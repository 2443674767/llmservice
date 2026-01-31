"""意图识别模块 - 从自然语言中提取用户意图"""
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict
import re


@dataclass
class Intent:
    """用户意图"""
    domain: Optional[str] = None  # 工具所属组 device / channel / communication 等
    object: Optional[str] = None  # 操作对象 package / can / tcp / device 等
    action: Optional[str] = None  # 操作类型 enable / disable / create / execute / list 等
    original_query: str = ""  # 原始查询


class IntentRecognizer:
    """意图识别器"""

    def __init__(self):
        """初始化意图识别器"""
        # Domain关键词映射
        self.domain_keywords = {
            'device': ['设备', 'device'],
            'channel': ['通道', 'channel', '信道'],
            'communication': ['通信', 'communication', '通讯', '网络'],
            'database': ['数据库', 'database', 'db', '数据'],
            'package': ['包', 'package', '程序包'],
        }

        # Object关键词映射
        self.object_keywords = {
            'device_config': ['设备配置', 'device_config'],
            'channel_config': ['通道配置', 'channel_config'],
            'can': ['can', 'CAN总线'],
            'tcp': ['tcp', 'TCP', '网络连接'],
            'package': ['包', 'package'],
            'database': ['数据库', 'database'],
        }

        # Action关键词映射
        self.action_keywords = {
            'list': ['列表', 'list', '查看', '显示', '列出', '查询', '获取'],
            # 'enable': ['启用', 'enable', '开启', '打开', '启动', '激活'],
            'disable': ['禁用', 'disable', '关闭', '停止', '停用'],
            'create': ['创建', 'create', '新建', '添加', '增加'],
            'delete': ['删除', 'delete', '移除', '去掉'],
            'execute': ['执行', 'execute', '运行', '运行'],
            'update': ['更新', 'update', '修改', '编辑'],
        }

    def recognize(self, query: str) -> Intent:
        """
        识别用户意图

        :param query: 用户查询文本
        :return: 意图对象
        """
        query_lower = query.lower()
        intent = Intent(original_query=query)

        # 识别Domain
        intent.domain = self._recognize_domain(query_lower)

        # 识别Object
        intent.object = self._recognize_object(query_lower)

        # 识别Action
        intent.action = self._recognize_action(query_lower)

        logging.info(f"意图识别结果: {intent}")
        return intent

    def _recognize_domain(self, query: str) -> Optional[str]:
        """识别Domain"""
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query:
                    return domain
        return None

    def _recognize_object(self, query: str) -> Optional[str]:
        """识别Object"""
        for obj, keywords in self.object_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query:
                    return obj
        return None

    def _recognize_action(self, query: str) -> Optional[str]:
        """识别Action"""
        # 按优先级排序，先匹配更具体的动作
        action_priority = ['list', 'enable', 'disable', 'create', 'delete', 'execute', 'update']

        for action in action_priority:
            keywords = self.action_keywords.get(action, [])
            for keyword in keywords:
                if keyword.lower() in query:
                    return action

        return None

    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """
        提取查询中的实体信息

        :param query: 用户查询
        :return: 实体字典
        """
        entities = {
            'domains': [],
            'objects': [],
            'actions': [],
        }

        query_lower = query.lower()

        # 提取Domain实体
        for domain, keywords in self.domain_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    entities['domains'].append(domain)
                    break

        # 提取Object实体
        for obj, keywords in self.object_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    entities['objects'].append(obj)
                    break

        # 提取Action实体
        for action, keywords in self.action_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    entities['actions'].append(action)
                    break

        return entities
