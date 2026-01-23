"""MCP 服务器基类"""
from typing import Dict, Type
from mcp.server.fastmcp import FastMCP
from loguru import logger

from graphmcp.core.agent_base import AgentBase


class MCPServerBase:
    """MCP 服务器基类，用于管理多个 Agent 服务"""

    def __init__(self, name: str, host: str = "0.0.0.0", port: int = 8000):
        """
        初始化 MCP 服务器

        :param name: 服务器名称
        :param host: 监听地址
        :param port: 监听端口
        """
        self.name = name
        self.host = host
        self.port = port
        self.mcp = FastMCP(name, host=host, port=port)
        self.agents: Dict[str, AgentBase] = {}

    def register_agent(self, agent: AgentBase):
        """
        注册 Agent 服务

        :param agent: Agent 实例
        """
        self.agents[agent.name] = agent
        logger.info(f"已注册 Agent: {agent.name}")

    def create_agent_tool(self, agent: AgentBase):
        """
        为 Agent 创建 MCP 工具

        :param agent: Agent 实例
        """
        import asyncio

        async def agent_query(query: str) -> str:
            """
            执行 Agent 查询（异步版本）

            :param query: 用户查询
            :return: Agent 执行结果
            """
            try:
                # 检查agent是否有异步execute方法
                if hasattr(agent, 'aexecute'):
                    result = await agent.aexecute(query)
                else:
                    # 如果没有异步方法，在事件循环中运行同步方法
                    result = agent.execute(query)

                # 提取最终答案
                if isinstance(result, dict) and "messages" in result:
                    messages = result["messages"]
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, "content"):
                            return str(last_message.content)
                        return str(last_message)
                return str(result)
            except Exception as e:
                logger.error(f"Agent {agent.name} 执行错误: {e}")
                import traceback
                logger.debug(f"详细错误:\n{traceback.format_exc()}")
                return f"错误: {str(e)}"

        # 设置工具名称和描述
        agent_query.__name__ = f"{agent.name}_query"
        agent_query.__doc__ = f"{agent.description}\n\n:param query: 用户查询\n:return: 执行结果"

        # 注册为 MCP 工具（FastMCP支持异步工具）
        self.mcp.tool()(agent_query)

        return agent_query

    def setup_agents(self):
        """设置所有注册的 Agent 工具"""
        for agent in self.agents.values():
            self.create_agent_tool(agent)
        logger.info(f"已设置 {len(self.agents)} 个 Agent 工具")

    def run(self, transport: str = "sse"):
        """
        启动 MCP 服务器

        :param transport: 传输协议 (sse, stdio)
        """
        self.setup_agents()
        logger.info(f"启动 MCP 服务器 {self.name}，监听 http://{self.host}:{self.port}/sse")
        self.mcp.run(transport=transport)
