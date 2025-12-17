import logging
import uuid
from datetime import datetime
from flask_login import login_user

from api.common.base64 import encode_to_base64
from common import settings
from common.connection_utils import sync_construct_response
from common.constants import ActiveEnum, StatusEnum
from api.common.exceptions import UserNotFoundError, AdminException
from api.db.services import UserService
from api.utils.crypt import decrypt
from common.misc_utils import get_uuid
from common.time_utils import current_timestamp, datetime_format, get_format_time
# 生成和验证安全的签名
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer


def setup_auth(login_manager):
    @login_manager.request_loader
    def load_user(web_request):
        jwt = Serializer(secret_key=settings.SECRET_KEY)
        authorization = web_request.headers.get("Authorization")
        if authorization:
            try:
                access_token = str(jwt.loads(authorization))

                if not access_token or not access_token.strip():
                    logging.warning("Authentication attempt with empty access token")
                    return None

                # Access tokens should be UUIDs (32 hex characters)
                if len(access_token.strip()) < 32:
                    logging.warning(f"Authentication attempt with invalid token format: {len(access_token)} chars")
                    return None

                user = UserService.query(
                    access_token=access_token, status=StatusEnum.VALID.value
                )
                if user:
                    if not user[0].access_token or not user[0].access_token.strip():
                        logging.warning(f"User {user[0].email} has empty access_token in database")
                        return None
                    return user[0]
                else:
                    return None
            except Exception as e:
                logging.warning(f"load_user got exception {e}")
                return None
        else:
            return None


def init_default_admin():
    # Verify that at least one active admin user exists. If not, create a default one.
    users = UserService.query(is_superuser=True)
    if not users:
        default_admin = {
            "id": uuid.uuid1().hex,
            "password": encode_to_base64("admin"),
            "nickname": "admin",
            "is_superuser": True,
            "email": "admin@ragflow.io",
            "creator": "system",
            "status": "1",
        }
        if not UserService.save(**default_admin):
            raise AdminException("Can't init admin.", 500)
    elif not any([u.is_active == ActiveEnum.ACTIVE.value for u in users]):
        raise AdminException("No active admin. Please update 'is_active' in db manually.", 500)


def login_admin(email: str, password: str):
    """
    :param email: admin 的邮箱
    :param password: 解密前字符串
    """
    users = UserService.query(email=email)
    if not users:
        raise UserNotFoundError(email)
    psw = decrypt(password)
    user = UserService.query_user(email, psw)
    if not user:
        raise AdminException("Email and password do not match!")
    # if not user.is_superuser:
    #     raise AdminException("Not admin", 403)
    if user.is_active == ActiveEnum.INACTIVE.value:
        raise AdminException(f"User {email} inactive", 403)

    resp = user.to_json()
    user.access_token = get_uuid()
    login_user(user)
    user.update_time = (current_timestamp(),)
    user.update_date = (datetime_format(datetime.now()),)
    user.last_login_time = get_format_time()
    user.save()
    msg = "Welcome back!"
    return sync_construct_response(data=resp, auth=user.get_id(), message=msg)