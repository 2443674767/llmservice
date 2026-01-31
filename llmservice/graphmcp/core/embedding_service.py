import logging
from typing import Optional, List

import numpy as np

from graphmcp.config.settings import settings


class EmbeddingService:
    """Embedding Service, 支持不同的 embedding 模型或者不同服务商"""

    def __init__(self):
        self.embedding_model = None
        self.embedding_dim = 4096   # 默认维度( ollama -> qwen3-embedding:8b)
        self._initialize_embedding_model()

    def _initialize_embedding_model(self):
        """初始化 embedding 模型"""
        try:
            from langchain_ollama import OllamaEmbeddings
            self.embedding_model = OllamaEmbeddings(
                model = settings.OLLAMA_MODEL,
                base_url = settings.OLLAMA_BASE_URL,
            )
            logging.info(f"使用Ollama Embeddings: {settings.OLLAMA_MODEL}")
        except ImportError:
            logging.warning(f"langchain_ollama 没有安装")
        except Exception as e:
            logging.warning(f"初始化 Ollama Embeddings失败: {e}")

        # 之后再考虑其他模型 或者联网情况下的API
        if self.embedding_model is None:
            pass

        if self.embedding_model is None:
            try:
                from langchain_openai import OpenAIEmbeddings
                self.embedding_model = OpenAIEmbeddings(
                    openai_api_key = settings.OPENAI_API_KEY,
                )
                self.embedding_dim = 1536
                logging.info("使用 OpenAI Embeddings")
            except ImportError:
                logging.warning("langchain_openai 未安装")
            except Exception as e:
                logging.warning(f"初始化 OpenAI Embeddings失败: {e}")

    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """
        生成单个文本的向量

        :param text: 输入文本
        :return: 向量数组 ， 如果失败返回 None
        """
        if self.embedding_model is None:
            logging.error("Embedding 模型未初始化")
            return None

        try:
            # 根据嵌入模型服务商属性判断
            if hasattr(self.embedding_model, 'embed_query'):
                # langchain
                return self.embedding_model.embed_query(text)
            elif hasattr(self.embedding_model, 'encode'):
                embedding = self.embedding_model.encode(text).tolist()
            else:
                logging.error(f"不支持的 embedding 模型类型: {type(self.embedding_model)}")
                return None
            return np.array(embedding, dtype=np.float32)
        except Exception as e:
            logging.error(f"生成 embedding失败:{e}")
            return None

    def embed_texts(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        批量生成文本向量

        :param texts: 文本列表
        :return: 向量列表，失败返回None
        """

        if self.embedding_model is None:
            logging.error("Embedding 模型没有初始化")
            return [None] * len(texts)

        try:
            # 根据模板类型调用不同的方法
            if hasattr(self.embedding_model, 'embed_documents'):
                embeddings = self.embedding_model.embed_documents(texts)
                return [np.array(emb, dtype=np.float32) for emb in embeddings]
            elif hasattr(self.embedding_model, 'encode'):
                embeddings = self.embedding_model.encode(texts)
                return [np.array(emb, dtype=np.float32) for emb in embeddings]
            else:
                logging.error(f"不支持的 embedding 模型类型： {type(self.embedding_model)}")
                return [None] * len(texts)
        except Exception as e:
            logging.error(f"批量生成 embedding 失败： {e}")
            return [None] * len(texts)

    def get_embedding_dim(self) -> int:
        """获取 embedding 维度"""
        return self.embedding_dim

    def is_available(self) -> bool:
        """检查 embedding 服务是否可用"""
        return self.embedding_model is not None


