"""MCP Agent 微服务主启动文件"""
import dotenv
import logging
from langchain_ollama import ChatOllama

from common.log_utils import init_root_logger
from config.settings import settings
from agents.sql_agent.agent import SQLAgent
from agents.weather_agent.agent import WeatherAgent
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
    return llm


def main():
    """主函数"""
    init_root_logger("graph_mcp")
    logging.info("初始化 MCP Agent 微服务...")
    logging.info(r"""
           ____   ____       _      ____    _   _   __  __    ____   ____  
          / ___| |  _ \     / \    |  _ \  | | | | |  \/  |  / ___| |  _ \ 
         | |  _  | |_) |   / _ \   | |_) | | |_| | | |\/| | | |     | |_) |
         | |_| | |  _ <   / ___ \  |  __/  |  _  | | |  | | | |___  |  __/ 
          \____| |_| \_\ /_/   \_\ |_|     |_| |_| |_|  |_|  \____| |_|    
    """)

    # 创建语言模型
    llm = create_llm()
    logging.info(f"语言模型初始化成功: {settings.OLLAMA_MODEL}")

    # 创建 MCP 服务器
    mcp_server = MCPServerBase(
        name="MCPAgentServer",
        host=settings.MCP_HOST,
        port=settings.MCP_PORT
    )

    # 注册 SQL Agent
    if settings.SQLITE_DB_PATH:
        sql_agent = SQLAgent(
            llm=llm,
            db_type="sqlite",
            db_path=settings.SQLITE_DB_PATH
        )
        mcp_server.register_agent(sql_agent)
        logging.info("SQL Agent 注册成功")
    else:
        logging.warning("未配置 SQLITE_DB_PATH，跳过 SQL Agent 注册")

    # 注册 Weather Agent
    weather_agent = WeatherAgent(llm=llm)
    mcp_server.register_agent(weather_agent)
    logging.info("Weather Agent 注册成功")

    # 启动 MCP 服务器
    mcp_server.run(transport="sse")


if __name__ == "__main__":
    main()

