from typing import Optional, List, Dict

from datrie import BaseState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, add_messages


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


