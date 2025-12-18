from mcp_project.agent_service.agent import AgentService
from mcp_project.database_service.database import DatabaseService


class QueryService:
    def __init__(self, db_uri: str, model_name: str):
        self.agent_service = AgentService(db_uri, model_name)
        self.database_service = DatabaseService(db_uri)

    def process_query(self, query: str):
        # 使用 AgentService 来生成查询
        result = self.agent_service.handle_query(query)
        return result
