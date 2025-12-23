"""全局配置管理"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """应用配置类"""

    # LLM 配置
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:12356")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    # 数据库配置
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "")

    # MCP 服务器配置
    MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
    MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

    # LangSmith 配置
    # LANGSMITH_MANAGER = os.getenv("LANGSMITH_MANAGER", "")


settings = Settings()

