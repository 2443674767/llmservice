from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field


class SQLLiteDBAgentService:
    def __init__(self, db_uri: str, model_name: str, base_url: str):
        self.db = SQLDatabase.from_uri(db_uri)
        self.llm = ChatOllama(model=model_name, base_url=base_url)      # "http://localhost:12356"
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = self.toolkit.get_tools()


# class TestDataQuery(BaseModel):
#     """
#
#     实验数据参数模型类，用于定义查询SQLLite数据库工具的输入参数结构。
#
#     :param qtable: 表名，字符串类型，表示在数据库中要查询的表名
#     """
#     qtable: str = Field(description="表名")
#
#
# @tool(args_schema=TestDataQuery)
# def get_testdata(qtable):
#     """
#     查询指定SQLLite的表中数据。
#
#     :param qtable: 必要参数，字符串类型，表示在数据库中要查询的表名。
#                  注意：查询表名在SQLLite必须使用[]。
#     :return: 返回 查询 的响应结果，
#
#     """
#     pass


db_path = "D:/zy/code/Testdata/LData.db"

db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

toolkit = SQLDatabaseToolkit(db=db, llm=llm)

tools = toolkit.get_tools()



