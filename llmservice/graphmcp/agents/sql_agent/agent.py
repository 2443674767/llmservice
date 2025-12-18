"""SQL Agent 实现"""
from typing import List, Any

from langchain.agents import create_agent
from langchain_classic.agents import AgentExecutor
from langchain_core.language_models import BaseChatModel
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from loguru import logger

from graphmcp.agents.sql_agent.config import SQLAgentConfig
from graphmcp.core.agent_base import AgentBase


class SQLAgent(AgentBase):
    """SQL 查询 Agent"""

    def __init__(self, llm: BaseChatModel, db_type: str = "sqlite", db_path: str = None):
        """
        初始化 SQL Agent

        :param llm: 语言模型实例
        :param db_type: 数据库类型 (sqlite, mysql)
        :param db_path: 数据库路径（SQLite 使用）
        """
        super().__init__(
            llm=llm,
            name="sql_agent",
            description="SQL 数据库查询助手，支持 SQLite 和 MySQL 数据库查询"
        )

        self.config = SQLAgentConfig(db_type=db_type)
        if db_path:
            self.config.db_path = db_path

        # 初始化数据库连接
        self.db = None
        self._init_database()

    def _init_database(self):
        """初始化数据库连接"""
        try:
            db_uri = self.config.get_db_uri()
            logger.info(f"连接数据库: {db_uri}")
            self.db = SQLDatabase.from_uri(db_uri)
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def get_tools(self) -> List[Any]:
        """
        获取 SQL 工具列表

        :return: 工具列表
        """
        if self.db is None:
            self._init_database()

        toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        return toolkit.get_tools()

    def create_agent(self) -> AgentExecutor:
        """
        创建 SQL Agent 执行器

        :return: AgentExecutor 实例
        """
        tools = self.get_tools()
        system_prompt = self.config.get_system_prompt()

        agent = create_agent(
            self.llm,
            tools,
            system_prompt=system_prompt,
        )

        logger.info(f"SQL Agent 创建成功，数据库类型: {self.config.db_type}")
        return agent

    def execute(self, query: str, **kwargs):
        """
        执行 SQL 查询

        :param query: 用户查询
        :param kwargs: 其他参数
        :return: 执行结果
        """
        return super().execute(query, **kwargs)

    def stream(self, query: str, stream_mode: str = "values", **kwargs):
        """
        流式执行 SQL 查询

        :param query: 用户查询
        :param stream_mode: 流式模式
        :param kwargs: 其他参数
        :return: 流式结果生成器
        """
        if self.agent_executor is None:
            self.agent_executor = self.create_agent()

        return self.agent_executor.stream(
            {"messages": [{"role": "user", "content": query}]},
            stream_mode=stream_mode,
            **kwargs
        )

