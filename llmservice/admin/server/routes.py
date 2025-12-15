from flask import Blueprint, request
from responses import success_response, error_response
from auth import login_admin

# 管理后台的API蓝图对象，定义所有以 /api/v1/admin 开头的路由
admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


@admin_bp.route('/login', methods=['POST'])
def login():
    if not request.json:
        return error_response('Authorize admin failed.' ,400)
    try:
        email = request.json.get("email", "")
        password = request.json.get("password", "")
        return login_admin(email, password)
    except Exception as e:
        return error_response(str(e), 500)



