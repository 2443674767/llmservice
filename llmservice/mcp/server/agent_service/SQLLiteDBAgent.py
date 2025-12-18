from langchain.agents import create_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_ollama import ChatOllama


class SQLLiteDBAgent:
    def __init__(self, db_uri: str, model_name: str, base_url: str):
        self.db = SQLDatabase.from_uri(db_uri)
        self.llm = ChatOllama(model=model_name, base_url=base_url)  # "http://localhost:12356"
        self.toolkit = SQLDatabaseToolkit(db=self.db, llm=self.llm)
        self.tools = self.toolkit.get_tools()

    def handle_query(self, question: str):
        system_prompt = '你是一个数据库查询助手, 【20240315_外特性_1】表是数据库中存储外特性数据的表'
        agent = create_agent(self.llm, self.tools, system_prompt=system_prompt)
        message = [{"role": "user", "content": question}]
        # agent.invoke({"message": message})  # , stream_mode="values"
        for step in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="values",
        ):
            step["messages"][-1].pretty_print()