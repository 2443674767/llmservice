"""MCP Agent 微服务主启动文件"""
from datetime import date

import dotenv
import logging
from langchain_ollama import ChatOllama

from common.log_utils import init_root_logger
from config.settings import settings, init_setting
from agents.sql_agent.agent import SQLAgent
from agents.weather_agent.agent import WeatherAgent
from agents.go_mcp_agent.agent import GoMCPAgent
from graphmcp.core import LangsmithManager, LangGraphManager
from graphmcp.core.mcp_server import MCPServerBase

# 加载环境变量
dotenv.load_dotenv()


def create_llm():
    """
    创建语言模型实例

    :return: ChatOllama 实例
    """
    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        validate_model_on_init=True,
        reasoning=False,
        base_url=settings.OLLAMA_BASE_URL,
    )
    # 启用LangSmith 添加回调管理
    # if settings.LANGSMITH_MANAGER and settings.LANGSMITH_MANAGER.is_enabled():
    #     callback_manager = settings.LANGSMITH_MANAGER.get_callback_manager()
    #     if callback_manager:
    #         llm.callbacks = callback_manager
    #         logging.info("LangSmith 追踪应用语言模型")

    return llm


def main():
    """主函数"""
    today = date.today()
    log_path = today.strftime("graph_mcp%Y-%m-%d")
    init_root_logger(log_path)
    logging.info("初始化 MCP Agent 微服务...")
    logging.info(r"""
           ____   ____       _      ____    _   _   __  __    ____   ____  
          / ___| |  _ \     / \    |  _ \  | | | | |  \/  |  / ___| |  _ \ 
         | |  _  | |_) |   / _ \   | |_) | | |_| | | |\/| | | |     | |_) |
         | |_| | |  _ <   / ___ \  |  __/  |  _  | | |  | | | |___  |  __/ 
          \____| |_| \_\ /_/   \_\ |_|     |_| |_| |_|  |_|  \____| |_|    
    """)

    init_setting()

    # 创建语言模型
    llm = create_llm()
    logging.info(f"语言模型初始化成功: {settings.OLLAMA_MODEL}")

    # 初始化 LangGraph 管理器
    # if settings.LANGGRAPH_ENABLED:
    #     settings.LANGGRAPH_MANAGER = LangGraphManager(llm=llm)
    #     logging.info("LangGraph 管理器已初始化")
    # else:
    #     logging.info("LangGraph 已禁用")

    # 创建 MCP 服务器
    mcp_server = MCPServerBase(
        name="MCPAgentServer",
        host=settings.MCP_HOST,
        port=settings.MCP_PORT
    )

    # # 注册 SQL Agent
    # if settings.SQLITE_DB_PATH:
    #     sql_agent = SQLAgent(
    #         llm=llm,
    #         db_type="sqlite",
    #         db_path=settings.SQLITE_DB_PATH
    #     )
    #     mcp_server.register_agent(sql_agent)
    #     logging.info("SQL Agent 注册成功")
    # else:
    #     logging.warning("未配置 SQLITE_DB_PATH，跳过 SQL Agent 注册")
    #
    # # 注册 Weather Agent
    # weather_agent = WeatherAgent(llm=llm)
    # mcp_server.register_agent(weather_agent)
    # logging.info("Weather Agent 注册成功")

    # 注册 Go MCP Agent
    go_mcp_agent = GoMCPAgent(llm=llm)
    mcp_server.register_agent(go_mcp_agent)
    logging.info("fcPro MCP Agent 注册成功")

    # 启动 MCP 服务器
    mcp_server.run(transport="sse")


if __name__ == "__main__":
    main()

