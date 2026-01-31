"""Tool Router - 工具路由和筛选模块"""
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from graphmcp.config.settings import settings
from graphmcp.core.embedding_service import EmbeddingService
from graphmcp.core.intent_recognizer import Intent, IntentRecognizer
from graphmcp.core.vector_store import VectorStore


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    description: str
    domain: str  # 工具所属组 device / channel / communication 等
    object: str  # 操作对象 package / can / tcp / device 等
    action: str  # 操作类型 enable / disable / create / execute / list 等
    risk: str  # 操作风险等级 read / write / dangerous


class ToolRouter:
    """工具路由器 - 根据意图筛选3-5个最相关的工具 增加向量检索"""

    def __init__(self, max_tools: int = 5):
        """
        初始化工具路由器

        :param max_tools: 最大返回工具数量，默认5个
        """
        self.max_tools = max_tools
        self.intent_recognizer = IntentRecognizer()
        self.vector_store: Optional[VectorStore] = None
        self.embedding_service: Optional[EmbeddingService] = None
        self.use_vector_search = settings.PG_VECTOR_ENABLED

        if self.use_vector_search:
            try:
                self.vector_store = VectorStore()
                self.embedding_service = EmbeddingService()
                if not self.vector_store.is_enabled():
                    logging.warning("embedding 服务不可用  将使用规则匹配")
                    self.use_vector_search = False
                elif not self.embedding_service.is_available():
                    logging.warning("embedding 服务不可用，使用规则匹配")
                    self.use_vector_search = False
                else:
                    logging.info("tool router 已启用向量检索功能")
            except Exception as e:
                logging.warning(f"初始化向量检索失败, 将只使用规则匹配： {e}")
                self.use_vector_search = False

    def extract_tool_metadata(self, tool: Any) -> Optional[ToolMetadata]:
        """
        从工具对象中提取元数据

        :param tool: LangChain工具对象或MCP工具对象
        :return: 工具元数据，如果无法提取则返回None
        """
        try:
            # 获取工具名称和描述
            tool_name = ''
            tool_description = ''

            if hasattr(tool, 'name'):
                tool_name = tool.name
            elif hasattr(tool, '__name__'):
                tool_name = tool.__name__

            if hasattr(tool, 'description'):
                tool_description = tool.description
            elif hasattr(tool, '__doc__'):
                tool_description = tool.__doc__ or ''

            # 方法1: 尝试从工具的metadata属性中获取（MCP工具的标准方式）
            if hasattr(tool, 'metadata') and tool.metadata:
                metadata = tool.metadata
                if isinstance(metadata, dict):
                    # if hasattr(metadata, '_meta'):
                    #     _meta = metadata._meta
                    #     metadata = _meta
                    if '_meta' in metadata and isinstance(metadata['_meta'], dict):
                        metadata = metadata['_meta']

                    return ToolMetadata(
                        name=tool_name or metadata.get('name', ''),
                        description=tool_description or metadata.get('Desc', ''),
                        domain=metadata.get('Domain', ''),
                        object=metadata.get('Object', ''),
                        action=metadata.get('Action', ''),
                        risk=metadata.get('Risk', 'read')
                    )

            # 方法2: 尝试从工具名称中解析（格式：domain.action）
            if tool_name and '.' in tool_name:
                parts = tool_name.split('.')
                if len(parts) >= 2:
                    domain = parts[0]
                    action = parts[1]
                    # 尝试从action中推断object（简化处理）
                    object_name = domain  # 默认object与domain相同

                    return ToolMetadata(
                        name=tool_name,
                        description=tool_description,
                        domain=domain,
                        object=object_name,
                        action=action,
                        risk='read'  # 默认风险级别
                    )

            # 方法3: 如果没有元数据，返回基础信息（用于描述匹配）
            if tool_name or tool_description:
                return ToolMetadata(
                    name=tool_name,
                    description=tool_description,
                    domain='',
                    object='',
                    action='',
                    risk='read'
                )
        except Exception as e:
            logging.warning(f"提取工具元数据失败 {tool}: {e}")

        return None

    def filter_tools_by_intent(
            self,
            tools: List[Any],
            user_query: str,
            intent: Optional[Intent] = None
    ) -> List[Any]:
        """
        根据用户查询和意图筛选工具

        :param tools: 所有可用工具列表
        :param user_query: 用户查询
        :param intent: 意图对象，如果为None则自动识别
        :return: 筛选后的工具列表（最多max_tools个）
        """
        if not tools:
            return []

        # 如果没有提供意图，则自动识别
        if intent is None:
            intent = self.intent_recognizer.recognize(user_query)

        logging.info(f"识别到的意图: Domain={intent.domain}, Object={intent.object}, Action={intent.action}")

        # 提取所有工具的元数据
        tool_metadata_list = []
        # tool_name_to_tool = []
        for tool in tools:
            metadata = self.extract_tool_metadata(tool)
            if metadata:
                tool_metadata_list.append((tool, metadata))
                # tool_name_to_tool[metadata.name] = tool
            else:
                # 如果没有元数据，仍然保留但优先级较低
                tool_metadata_list.append((tool, None))

        # 计算每个工具的匹配分数(向量检索)
        vector_search_results = []
        if self.use_vector_search and self.vector_store and self.embedding_service:
            try:
                # 生成查询向量
                query_embedding = self.embedding_service.embed_text(user_query)
                if query_embedding is not None:
                    # 向量检索
                    vector_results = self.vector_store.search_similar_tools(
                        query_embedding=query_embedding,
                        top_k=self.max_tools * 2,   # 后续再筛选
                        domain=intent.domain,
                        object_filter=intent.object,
                        action_filter=intent.action,
                    )
                    vector_search_results = vector_results
                    logging.info(f"向量检索返回 {len(vector_results)} 个候选工具")
            except Exception as e:
                logging.warning(f"向量检索失败,回退到规则匹配: {e}")

        # 计算每个工具的匹配分数(规则匹配)
        scored_tools = []
        for tool, metadata in tool_metadata_list:
            score = self._calculate_match_score(metadata, intent, user_query)
            scored_tools.append((tool, score, metadata))

        # 二次过滤
        if vector_search_results:
            # 创建向量相似度映射
            vector_scores = {tool_name: sim_score for tool_name, sim_score in vector_search_results}

            for i, (tool, rule_score, metadata) in enumerate[Any](scored_tools):
                if metadata and metadata.name in vector_scores:
                    vector_score = vector_scores[metadata.name]
                    # 暂时规则匹配为主，后期需要测试
                    fused_score = rule_score * 0.6 + vector_score * 0.4
                    scored_tools[i] = (tool, fused_score, metadata)
                    logging.info(f"工具 {metadata.name}: 规则={rule_score:.3f},向量={vector_score:.3f}, 融合={fused_score:.3f}")
                else:
                    # 向量检索如果没有找到当前工具，那么降低规则匹配的分数
                    scored_tools[i] = (tool, rule_score * 0.8, metadata)

        # 按分数排序，优先返回高分的工具
        scored_tools.sort(key=lambda x: x[1], reverse=True)

        # 返回前max_tools个工具
        selected_tools = [tool for tool, score, _ in scored_tools[:self.max_tools]]

        logging.info(f"从 {len(tools)} 个工具中筛选出 {len(selected_tools)} 个工具")
        if selected_tools:
            selected_names = [self._get_tool_name(t) for t in selected_tools]
            logging.info(f"选中的工具: {selected_names}")

        return selected_tools

    def _calculate_match_score(
            self,
            metadata: Optional[ToolMetadata],
            intent: Intent,
            user_query: str
    ) -> float:
        """
        计算工具与意图的匹配分数

        :param metadata: 工具元数据
        :param intent: 用户意图
        :param user_query: 用户查询
        :return: 匹配分数（0-1之间）
        """
        if metadata is None:
            # 没有元数据的工具，使用描述匹配
            return 0.1

        score = 0.0

        # Domain匹配（权重：0.3）
        if intent.domain and metadata.domain:
            if intent.domain.lower() == metadata.domain.lower():
                score += 0.3
            elif intent.domain.lower() in metadata.domain.lower() or metadata.domain.lower() in intent.domain.lower():
                score += 0.15

        # Object匹配（权重：0.3）
        if intent.object and metadata.object:
            if intent.object.lower() == metadata.object.lower():
                score += 0.3
            elif intent.object.lower() in metadata.object.lower() or metadata.object.lower() in intent.object.lower():
                score += 0.15

        # Action匹配（权重：0.2）
        if intent.action and metadata.action:
            if intent.action.lower() == metadata.action.lower():
                score += 0.2
            elif intent.action.lower() in metadata.action.lower() or metadata.action.lower() in intent.action.lower():
                score += 0.1

        # 描述文本相似度（权重：0.2）
        if metadata.description:
            query_lower = user_query.lower()
            desc_lower = metadata.description.lower()

            # 简单的关键词匹配
            query_words = set(query_lower.split())
            desc_words = set(desc_lower.split())

            common_words = query_words.intersection(desc_words)
            if query_words:
                similarity = len(common_words) / len(query_words)
                score += 0.2 * similarity

        # 风险级别调整（只读操作优先级稍高）
        if metadata.risk == 'read':
            score += 0.05

        return min(score, 1.0)

    def _get_tool_name(self, tool: Any) -> str:
        """获取工具名称"""
        if hasattr(tool, 'name'):
            return tool.name
        return str(tool)
