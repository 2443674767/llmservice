import logging

from mcp.server.fastmcp import FastMCP

from common.log_utils import init_root_logger


mcp = FastMCP("FCManager", host="0.0.0.0", port=8000)


def start_server():
    mcp.run(transport="sse")


if __name__ == '__main__':
    init_root_logger("admin_service")
    logging.info("启动 MCP  服务器，监听 http://0.0.0.0:8000")

    logging.info(r"""
        XYDCMCP
    """)
    start_server()
