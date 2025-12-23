import logging
from typing import Optional, Any, Dict

from langchain_core.callbacks import CallbackManager
from langchain_core.runnables import RunnableConfig
from langchain_core.tracers import LangChainTracer


class LangsmithManager:
    """LangSmith管理器， 配置和管理 LangSmith追踪 Agent执行"""
    def __init__(
            self,
            api_key: Optional[str] = None,
            project_name: Optional[str] = None,
            api_url: Optional[str] = None,
            enabled: bool = True
    ):
        """
        初始化LangSmith管理器
        :param api_key: LangSmith API密钥
        :param project_name: 项目名称
        :param api_url: LangSmith API URL
        :param enabled: 是否启用LangSmith追踪
        """
        self.api_key = api_key
        self.project_name = project_name
        self.api_url = api_url
        self.enabled = enabled
        self.tracer: Optional[LangChainTracer] = None

        if self.enabled:
            self._init_tracer()

    def _init_tracer(self):
        """
        初始化 LangChain Tracer 自动记录以下信息
        请求与响应：发送给模型（如 OpenAI GPT）的提示词（Prompt）和返回的结果。
        耗时：每个步骤（如调用 LLM、执行工具）花费的时间。
        步骤关系：复杂的链或代理中，各步骤之间的父子调用关系。
        工具使用：代理（Agent）执行时，具体调用了哪个工具，输入输出是什么。
        令牌用量与成本：消耗的 Token 数量和估算费用（如果后端支持）。
        :return:
        """
        if not self.api_key:
            logging.warning(
                "LangSmith API 密钥未设置，LangSmith 追踪将被禁用。"
                "请设置 LANGCHAIN_API_KEY 环境变量。"
            )
            self.enabled = False
            return

        try:
            self.tracer = LangChainTracer(
                project_name=self.project_name,
                api_url=self.api_url
            )
            logging.info(f"LangSmith 追踪已启用，项目: {self.project_name}")
        except Exception as e:
            logging.error(f"LangSmith 追踪初始化失败: {e}")
            self.enabled = False

    def get_callback_manager(self) -> Optional[CallbackManager]:
        """
        回调管理器 （LangChain调用）
        :return: CallbackManager实例或None
        """
        if not self.enabled or self.tracer is None:
            return None

        return CallbackManager(self.tracer)

    def get_runnable_config(
            self,
            tags: Optional[list] = None,
            metadata: Optional[Dict[str, Any]] = None,
            run_name: Optional[str] = None,
    ) -> Optional[RunnableConfig]:
        """
        获取 Runnable 配置
        RunnableConfig:在 LangChain 的各种可运行对象（Runnable）之间统一、安全地传递执行参数和上下文信息。
        :param tags: 标签列表
        :param metadata: 元数据字典
        :param run_name: 运行名称
        :return: RunnableConfig 实例或None
        """
        if not self.enabled:
            return None

        config = {}
        if tags:
            config['tags'] = tags
        if metadata:
            config['metadata'] = metadata
        if run_name:
            config['run_name'] = run_name

        return config if config else None

    def update_project_name(self, project_name: str):
        """
        更新项目名称
        :param project_name: 新的项目名称
        :return:
        """
        self.project_name = project_name
        if self.enabled:
            self._init_tracer()
            logging.info(f"LangSmith 项目名称已更新: {project_name}")

    def enable(self):
        """启用 LangSmith 追踪"""
        if not self.enabled:
            self.enabled = True
            self._init_tracer()

    def disable(self):
        """禁用LangSmith追踪"""
        self.enabled = False
        self.tracer = None
        logging.info("LangSmith 追踪已禁用")

    def is_enabled(self) -> bool:
        """检查LangSmith是否已启用"""
        return self.enabled and self.tracer is not None

    def get_tracer(self) -> Optional[LangChainTracer]:
        """
        获取 LangSmith 是否启用
        :return: LangChainTracer实例或None
        """
        return self.tracer if self.is_enabled() else None
