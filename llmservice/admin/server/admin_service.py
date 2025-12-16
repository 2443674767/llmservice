import faulthandler
import logging
import os
import signal
import threading
import time
import traceback

from flask import Flask
from flask_login import LoginManager
from werkzeug.serving import run_simple

from admin.server.auth import init_default_admin   # setup_auth
from admin.server.config import SERVICE_CONFIGS, load_configurations
from common import settings
from common.config_utils import show_configs
from common.constants import SERVICE_CONF
from common.versions import get_ragflow_version
from routes import admin_bp

from flask_session import Session

stop_event = threading.Event()


if __name__ == '__main__':
    # 启用 Python 的 faulthandler 模块，以便在程序崩溃时自动打印当前线程或所有线程的栈追踪（traceback），帮助定位和调试进程中的崩溃、死锁等问题
    faulthandler.enable()
    logging.info("admin_service")
    logging.info(r"""
         __   ____     _______   _____ _      _      __  __ 
         \ \ / /\ \   / /  __ \ / ____| |    | |    |  \/  |
          \ V /  \ \_/ /| |  | | |    | |    | |    | \  / |
           > <    \   / | |  | | |    | |    | |    | |\/| |
          / . \    | |  | |__| | |____| |____| |____| |  | |
         /_/ \_\   |_|  |_____/ \_____|______|______|_|  |_|
    """)
    app = Flask(__name__)
    app.register_blueprint(admin_bp)
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["MAX_CONTENT_LENGTH"] = int(
        os.environ.get("MAX_CONTENT_LENGTH", 1024 * 1024 * 1024)
    )
    Session(app)
    logging.info(f'LLM version: {get_ragflow_version()}')
    # 脱敏
    show_configs()
    login_manager = LoginManager()
    login_manager.init_app(app)
    settings.init_settings()
    # setup_auth(login_manager)
    init_default_admin()
    SERVICE_CONFIGS.configs = load_configurations(SERVICE_CONF)

    try:
        logging.info("llm service start...")
        # 启动一个轻量级的 WSGI 开发服务器
        run_simple(
            hostname="0.0.0.0",
            port=9381,
            application=app,
            threaded=True,
            use_reloader=False,
            use_debugger=True,
        )
    except Exception:
        traceback.print_exc()
        stop_event.set()
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGKILL)

