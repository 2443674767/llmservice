import os
from typing import Dict, Any


class GoMCPAgentConfig:
    """Go MCP Agent 配置类"""

    def __init__(self):
        """初始化配置"""
        # Go MCP 服务地址
        self.go_mcp_server_url = os.getenv("GO_MCP_SERVER_URL", "http://192.168.1.128:9300/mcp")
        # Go MCP 服务器名称
        self.go_mcp_server_name = os.getenv("GO_MCP_SERVER_NAME", "fc-pro")
        # Go MCP 服务器版本
        self.go_mcp_server_version = os.getenv("GO_MCP_SERVER_VERSION", "1.0.0")

    def get_server_config(self) -> Dict[str, Any]:
        """
        获取Go MCP服务器配置

        :return: 服务器配置字典
        """
        return {
            self.go_mcp_server_name: {
                "url": self.go_mcp_server_url,
                "transport": "streamable_http"  # 对于Go MCP的StreamableHTTPServer，使用streamable_http
            }
        }