"""Agent 基类，所有 Agent 服务都应继承此类"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from langchain_classic.agents import AgentExecutor
from langchain_core.language_models import BaseChatModel


class AgentBase(ABC):
    """Agent 基类"""

    def __init__(self, llm: BaseChatModel, name: str, description: str):
        """
        初始化 Agent

        :param llm: 语言模型实例
        :param name: Agent 名称
        :param description: Agent 描述
        """
        self.llm = llm
        self.name = name
        self.description = description
        self.agent_executor: AgentExecutor = None

    @abstractmethod
    def create_agent(self) -> AgentExecutor:
        """
        创建 Agent 执行器
        子类必须实现此方法

        :return: AgentExecutor 实例
        """
        pass

    @abstractmethod
    def get_tools(self) -> List[Any]:
        """
        获取 Agent 使用的工具列表
        子类必须实现此方法

        :return: 工具列表
        """
        pass

    def execute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        执行查询

        :param query: 用户查询
        :param kwargs: 其他参数
        :return: 执行结果
        """
        if self.agent_executor is None:
            self.agent_executor = self.create_agent()

        result = self.agent_executor.invoke(
            {"messages": [{"role": "user", "content": query}]},
            **kwargs
        )
        return result

    def stream(self, query: str, **kwargs):
        """
        流式执行查询

        :param query: 用户查询
        :param kwargs: 其他参数
        :return: 流式结果生成器
        """
        if self.agent_executor is None:
            self.agent_executor = self.create_agent()

        return self.agent_executor.stream(
            {"messages": [{"role": "user", "content": query}]},
            **kwargs
        )

    async def aexecute(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        异步执行查询

        :param query: 用户查询
        :param kwargs: 其他参数
        :return: 执行结果
        """
        if self.agent_executor is None:
            self.agent_executor = self.create_agent()

        result = await self.agent_executor.ainvoke(
            {"messages": [{"role": "user", "content": query}]},
            **kwargs
        )
        return result
