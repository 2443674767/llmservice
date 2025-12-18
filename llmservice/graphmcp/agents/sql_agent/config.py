"""SQL Agent 配置"""
from graphmcp.config.settings import settings


class SQLAgentConfig:
    """SQL Agent 配置类"""

    # 数据库类型
    DB_TYPE_SQLITE = "sqlite"
    DB_TYPE_MYSQL = "mysql"

    def __init__(self, db_type: str = DB_TYPE_SQLITE):
        """
        初始化配置

        :param db_type: 数据库类型 (sqlite, mysql)
        """
        self.db_type = db_type
        self.db_path = settings.SQLITE_DB_PATH
        self.mysql_config = {
            "host": settings.MYSQL_HOST,
            "port": settings.MYSQL_PORT,
            "user": settings.MYSQL_USER,
            "password": settings.MYSQL_PASSWORD,
            "database": settings.MYSQL_DATABASE,
        }

    def get_db_uri(self) -> str:
        """
        获取数据库 URI

        :return: 数据库连接 URI
        """
        if self.db_type == self.DB_TYPE_SQLITE:
            return f"sqlite:///{self.db_path}"
        elif self.db_type == self.DB_TYPE_MYSQL:
            return f"mysql+pymysql://{self.mysql_config['user']}:{self.mysql_config['password']}@{self.mysql_config['host']}:{self.mysql_config['port']}/{self.mysql_config['database']}"
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")

    def get_system_prompt(self) -> str:
        """
        获取系统提示词

        :return: 系统提示词
        """
        base_prompt = "你是一个数据库查询助手"

        if self.db_type == self.DB_TYPE_SQLITE:
            base_prompt += "。注意：SQLite 的表名需要使用 [] 括起来进行查询。"

        # 可以在这里添加表说明
        # base_prompt += "【20240315_外特性_1】表是数据库中存储外特性数据的表"

        return base_prompt

