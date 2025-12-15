


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
    if not user.is_superuser:
        raise AdminException("Not admin", 403)
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