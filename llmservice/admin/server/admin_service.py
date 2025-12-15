import faulthandler
import logging

from flask import Flask




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
    app.register_blueprint()
