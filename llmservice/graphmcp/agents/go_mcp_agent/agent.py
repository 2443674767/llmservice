import asyncio
from typing import Any, List, Optional, Dict

from langchain_classic.agents import AgentExecutor
from loguru import logger
from langchain_mcp_adapters.client import MultiServerMCPClient

from graphmcp.agents.go_mcp_agent.config import GoMCPAgentConfig
from graphmcp.core.agent_base import AgentBase
from langchain_core.language_models import BaseChatModel

from graphmcp.core.intent_recognizer import Intent
from graphmcp.core.tool_router import ToolRouter


class GoMCPAgent(AgentBase):
    """fcPro MCP Agent 连接 FcPro MCP服务的Agent"""

    def __init__(self, llm: BaseChatModel, go_mcp_server_url: str = None):
        """
        初始化
        :param llm: 语言模型实例
        :param go_mcp_server_url: FcPro 后端服务URL
        """
        super().__init__(
            llm=llm,
            name="fcPro_mcp_agent",
            description="fcPro MCP服务代理，可以调用fcPro MCP服务器提供的所有工具"
        )
        self.config = GoMCPAgentConfig()

        if go_mcp_server_url:
            self.config.go_mcp_server_url = go_mcp_server_url

        self.mcp_client: MultiServerMCPClient = None
        self._all_tools: List[Any] = None   # 工具列表
        self.tool_router = ToolRouter(max_tools=5)  # # 工具路由器，最多返回5个工具

    async def _initialize_mcp_client(self):
        """
        异步初始化MCP客户端并获取工具

        这个方法需要在异步上下文中调用
        """
        if self.mcp_client is None:
            try:
                server_config = self.config.get_server_config()
                self.mcp_client = MultiServerMCPClient(server_config)
                self._all_tools = await self.mcp_client.get_tools()
                logger.info(
                    f" fcPro MCP Agent 已连接服务器，加载了 {len(self._all_tools)} 个工具：{[t.name for t in self._all_tools]}")
            except Exception as e:
                logger.error(f"fcPro MCP Agent 连接服务器失败: {e}")
                raise

    def _sync_initialize_mcp_client(self):
        """
        同步初始化MCP客户端（在异步环境中运行）
        """
        if self.mcp_client is None or self._all_tools is None:
            try:
                # 检查是否有运行中的事件循环
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # 如果循环正在运行，尝试使用nest_asyncio
                        try:
                            import nest_asyncio
                            nest_asyncio.apply()
                            loop.run_until_complete(self._initialize_mcp_client())
                        except ImportError:
                            logger.warning("nest_asyncio未安装，尝试创建新的事件循环")
                            # 如果没有nest_asyncio，创建新的事件循环
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            try:
                                new_loop.run_until_complete(self._initialize_mcp_client())
                            finally:
                                new_loop.close()
                    else:
                        loop.run_until_complete(self._initialize_mcp_client())
                except RuntimeError:
                    # 没有事件循环，创建一个新的
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self._initialize_mcp_client())
                    finally:
                        loop.close()
            except Exception as e:
                logger.error(f"fcPro MCP Agent 同步初始化失败: {e}")
                # 如果初始化失败，使用空工具列表
                self._all_tools = []

    def get_tools(self) -> List[Any]:

        return self.get_all_tools()

    def get_all_tools(self) -> List[Any]:
        """
        获取Go MCP服务提供的所有工具列表

        :return: 所有工具列表
        """
        if self._all_tools is None:
            self._sync_initialize_mcp_client()
        return self._all_tools or []

    def get_filtered_tools(self, user_query: str, intent: Optional[Intent] = None) -> List[Any]:
        """
        根据用户查询和意图筛选工具（只返回3-5个最相关的工具）

        :param user_query: 用户查询
        :param intent: 意图对象，如果为None则自动识别
        :return: 筛选后的工具列表
        """
        all_tools = self.get_all_tools()
        if not all_tools:
            return []

        # 使用Tool Router筛选工具
        filtered_tools = self.tool_router.filter_tools_by_intent(
            tools=all_tools,
            user_query=user_query,
            intent=intent
        )

        return filtered_tools

    def create_agent(self, tools: Optional[List[Any]] = None) -> AgentExecutor:
        """
        创建 Go MCP Agent 执行器

        :param tools: 工具列表，如果为None则使用所有工具（不推荐，应该使用筛选后的工具）
        :return: AgentExecutor 实例
        """
        from langchain.agents import create_agent

        if tools is None:
            tools = self.get_all_tools()
            logger.warning("未提供工具列表，使用所有工具。建议使用get_filtered_tools()获取筛选后的工具")

        if not tools:
            logger.warning("fcPro MCP Agent 没有可用的工具，请检查fcPro MCP服务是否正常运行")

        system_prompt = f"""你是一个智能助手，可以通过调用fcPro MCP服务器提供的工具来帮助用户完成任务。
    
    当前可用的工具（已根据你的查询筛选出最相关的工具）：
    {chr(10).join([f"- {tool.name}: {tool.description}" for tool in tools])}
    
    请根据用户的请求，判断是否需要调用这些工具。如果需要，请正确使用工具并返回结果。
    如果不需要调用工具，就直接回答用户的问题。"""

        agent = create_agent(
            self.llm,
            tools,
            system_prompt=system_prompt,
        )

        logger.info(f"fcPro MCP Agent 创建成功，使用 {len(tools)} 个工具")
        return agent

    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        执行查询（重写父类方法，集成Tool Router）

        :param query: 用户查询
        :param kwargs: 其他参数
        :return: 执行结果
        """
        # 根据查询筛选工具（只返回3-5个最相关的工具）
        filtered_tools = self.get_filtered_tools(query)

        # 使用筛选后的工具创建agent
        if self.agent_executor is None:
            # 每次查询都重新创建agent，使用筛选后的工具
            self.agent_executor = self.create_agent(tools=filtered_tools)
        else:
            # 如果agent已存在，需要更新工具（这里简化处理，重新创建）
            # 注意：实际应用中可能需要更智能的agent更新机制
            self.agent_executor = self.create_agent(tools=filtered_tools)

        result = self.agent_executor.invoke(
            {"messages": [{"role": "user", "content": query}]},
            **kwargs
        )
        return result

    async def aexecute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        异步执行查询（重写父类方法，集成Tool Router）

        :param query: 用户查询
        :param kwargs: 其他参数
        :return: 执行结果
        """
        # 根据查询筛选工具（只返回3-5个最相关的工具）
        filtered_tools = self.get_filtered_tools(query)

        # 使用筛选后的工具创建agent
        if self.agent_executor is None:
            # 每次查询都重新创建agent，使用筛选后的工具
            self.agent_executor = self.create_agent(tools=filtered_tools)
        else:
            # 如果agent已存在，需要更新工具（这里简化处理，重新创建）
            # 注意：实际应用中可能需要更智能的agent更新机制
            self.agent_executor = self.create_agent(tools=filtered_tools)

        result = await self.agent_executor.ainvoke(
            {"messages": [{"role": "user", "content": query}]},
            **kwargs
        )
        return result

    async def cleanup(self):
        """
        清理资源，关闭MCP客户端连接

        这个方法应该在agent不再使用时调用
        """
        if self.mcp_client:
            try:
                await self.mcp_client.close()
                logger.info("fcPro MCP Agent 客户端已关闭")
            except Exception as e:
                logger.error(f"关闭 fcPro MCP Agent客户端时出错: {e}")
