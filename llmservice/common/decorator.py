import os


def singleton(cls, *args, **kw):
    """
        进程内单例
    :param cls:
    :param args:
    :param kw:
    :return:
    """
    instances = {}

    def _singleton():
        key = str(cls) + str(os.getpid())
        if key not in instances:
            instances[key] = cls(*args, **kw)
        return instances[key]

    return _singleton
