"""全局配置管理"""
import logging
import os
from dotenv import load_dotenv

from graphmcp.core import LangsmithManager, LangGraphManager

load_dotenv()

LANGSMITH_MANAGER: LangsmithManager
LANGGRAPH_MANAGER: LangGraphManager
LANGSMITH_ENABLED = None
LANGCHAIN_API_KEY = None
LANGCHAIN_PROJECT = None
LANGCHAIN_API_URL = None
LANGGRAPH_ENABLED = None


def init_setting():
    global LANGCHAIN_API_KEY, LANGCHAIN_PROJECT, LANGCHAIN_API_URL, LANGGRAPH_ENABLED
    LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
    LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "mcp-agent-platform")
    LANGCHAIN_API_URL = os.getenv("LANGCHAIN_API_URL", "https://api.smith.langchain.com")
    # LangGraph 配置
    LANGGRAPH_ENABLED = os.getenv("LANGGRAPH_ENABLED", "true").lower() == "true"

    # LangSmith 配置
    global LANGSMITH_MANAGER, LANGGRAPH_MANAGER, LANGSMITH_ENABLED
    LANGSMITH_ENABLED = os.getenv("LANGSMITH_ENABLED", "true")
    LANGSMITH_MANAGER = None
    LANGGRAPH_MANAGER = None
    # 初始化管理器
    if LANGSMITH_ENABLED:
        LANGSMITH_MANAGER = LangsmithManager(
            api_key=LANGCHAIN_API_KEY,
            project_name=LANGCHAIN_PROJECT,
            api_url=LANGCHAIN_API_URL,
            enabled=LANGGRAPH_ENABLED
        )
        if LANGSMITH_MANAGER.is_enabled():
            logging.info(f"LangSmith 追踪已启用，项目: {LANGCHAIN_PROJECT}")
        else:
            logging.warning("LangSmith 追踪未启用（请检查 LANGCHAIN_API_KEY 环境变量）")
    else:
        logging.info("LangSmith 追踪已禁用")


class Settings:
    """应用配置类"""

    # LLM 配置
    OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:12356")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    # 数据库配置
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "")

    PG_HOST = os.getenv("PG_HOST", "localhost")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_USER = os.getenv("PG_USER", "myuser")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "mypassword")
    PG_DATABASE = os.getenv("PG_DATABASE", "mydb")
    PG_VECTOR_ENABLED = os.getenv("PG_VECTOR_ENABLED", "true").lower() == "true"

    # MCP 服务器配置
    MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("MCP_PORT", "8000"))


settings = Settings()

