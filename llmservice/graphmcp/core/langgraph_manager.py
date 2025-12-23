import logging
from typing import Optional, List, Dict, Any

from datrie import BaseState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode


class LangGraphManager:
    """LangGraph 管理器，用于创建和管理状态图"""

    def __init__(self, llm: BaseChatModel, tools: Optional[List[BaseTool]] = None):
        """
        初始化 LangGraph 管理
        :param llm: 语言模型实例
        :param tools: 工具列表（可选）
        """
        self.llm = llm
        self.tools = tools or []
        self.graphs: Dict[str, StateGraph] = {}
        self.checkpointer = MemorySaver()

    def create_agent_graph(
            self,
            name: str,
            system_prompt:
            Optional[str] = None,
            tools: Optional[List[BaseTool]] = None
    ) -> StateGraph:
        """
        创建简单的 Agent 状态图

        :param name: 图名称
        :param system_prompt: 系统提示词
        :param tools: 工具列表（如果提供，将覆盖初始化时的工具）
        :return: StateGraph 实例
        """
        tools = tools or self.tools

        from typing import TypedDict, Annotated

        class AgentState(TypedDict):
            messages: Annotated[List[BaseMessage], add_messages]

        # LLM绑定工具
        if tools:
            llm_tools = self.llm.bind_tools(tools)
        else:
            llm_tools = self.llm

        # 状态图
        graph = StateGraph(AgentState)

        # 增加节点
        def call_model(state: AgentState) -> AgentState:
            """调用模型节点"""
            messages = state["messages"]
            if system_prompt and not any(
                    isinstance(msg, AIMessage) for msg in messages
            ):
                # 系统提示词作为第一条消息
                messages = [HumanMessage(content=system_prompt)] + messages
            response = llm_tools.invoke(messages)
            return {"message": [response]}

        def should_continue(state: AgentState) -> str:
            """工具执行判断"""
            message = state["message"]
            last_message = state["messages"][-1]
            # 判断最后一条是否有工具调用
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return "end"

        # 添加节点
        graph.add_node("agent", call_model)

        if tools:
            tool_node = ToolNode(tools)
            graph.add_node("tools", tool_node)
            graph.add_conditional_edges(
                "agent",
                should_continue,
                {
                    "tools": tools,
                    "end": END
                }
            )
            graph.add_edge("tools", "agent")
        else:
            graph.add_edge("agent", END)

        # 设置入口点
        graph.set_entry_point("agent")

        compiled_graph = graph.compile(checkpointer=self.checkpointer)

        self.graphs[name] = compiled_graph
        logging.info(f"LangGraph'{name}' 创建成功")

        return compiled_graph

    def get_graph(self, name: str) -> Optional[StateGraph]:
        """
        获取创建的图
        :param name: 图名称
        :return: StateGraph实例 或 None
        """
        return self.graphs.get(name)

    def invoke_graph(
            self,
            name: str,
            query: str,
            config: Optional[Dict[str, Any]] = None,
            thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行图
        :param name: 图名称
        :param query: 用户查询
        :param config: 配置字段
        :param thread_id: 线程ID（检查点恢复等等）
        :return: 执行结果
        """
        graph = self.get_graph(name)
        if graph is None:
            raise ValueError(f"图 '{name}' 不存在")

        config = config or {}
        if thread_id:
            config["configurable"] = {"thread_id": thread_id}

        return graph.stream(
            {"messages": [HumanMessage(content=query)]},
            config=config
        )

    def list_graphs(self) -> List[str]:
        """
        列出所有创建的图
        :return: 图名称
        """
        return list[str](self.graphs.keys())

    def remove_graph(self, name: str) -> bool:
        """
        删除图
        :param name: 图名称
        :return: 是否删除成功
        """
        if name in self.graphs:
            del self.graphs[name]
            logging.info(f"LangGraph '{name}' 已删除")
            return True
        return False
