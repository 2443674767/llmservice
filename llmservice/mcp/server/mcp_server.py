import logging

from mcp.server.fastmcp import FastMCP

from common import settings
from common.log_utils import init_root_logger
from common.settings import MCP_HOST, MCP_PORT


def main():
    settings.init_settings()
    logging.info(
        r"""
            __  __  ____ ____       ____  _____ ______     _______ ____
            |  \/  |/ ___|  _ \     / ___|| ____|  _ \ \   / / ____|  _ \
            | |\/| | |   | |_) |    \___ \|  _| | |_) \ \ / /|  _| | |_) |
            | |  | | |___|  __/      ___) | |___|  _ < \ V / | |___|  _ <
            |_|  |_|\____|_|        |____/|_____|_| \_\ \_/  |_____|_| \_\
        """
    )

    logging.info("MCP host: {MCP_HOST}")
    logging.info("MCP port: {MCP_PORT}")

    mcp = FastMCP("FCManager", host=MCP_HOST, port=MCP_PORT)

    mcp.run(transport="sse")


if __name__ == '__main__':
    init_root_logger("mcp_service")
    logging.info("启动 MCP  服务器，监听 http://0.0.0.0:8000")
    main()
