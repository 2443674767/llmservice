import logging
from typing import Optional, List, Any, Tuple
from dataclasses import dataclass

import numpy as np
import psycopg

from graphmcp.config.settings import settings


@dataclass
class ToolMetadata:
    """工具向量数据"""
    tool_name: str
    domain: str
    object: str
    action: str
    risk: str
    description: str
    embedding: np.ndarray
    updated_at: Optional[str] = None


class VectorStore:
    """向量存储服务 管理工具和知识库向量"""

    def __init__(self):
        self.conn = None
        self.enabled = settings.PG_VECTOR_ENABLED

        if not self.enabled:
            logging.info("pgvector 功能已禁止使用（PG_VECTOR_ENABLED）")
            return

        try:
            self._connect()
            self._ensure_extension()
            self._ensure_tables()

            logging.info("向量存储服务初始化成功")
        except Exception as e:
            logging.error(f"向量存储服务初始化失败:{e}")

    def _connect(self):
        """连接 PostgreSQL 数据库"""
        conn_str = (
            f"host={settings.PG_HOST} "
            f"port={settings.PG_PORT} "
            f"dbname={settings.PG_DATABASE} "
            f"user={settings.PG_USER} "
            f"password={settings.PG_PASSWORD} "
        )
        # autocommit = False 自动开启事务  =True 则不存在事务块
        self.conn = psycopg.connect(conn_str, autocommit=False)

    def _ensure_extension(self):
        """确保 pgvector 扩展已安装"""
        with self.conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            self.conn.commit()
            logging.info("pgvector 扩展启用")

    def _ensure_tables(self):
        """确保表已创建"""
        try:
            with self.conn.cursor() as cur:  # embedding vector,
                # # embedding 动态维度，根据实际 embedding 模型调整
                cur.execute("""
                CREATE TABLE IF NOT EXISTS tool_embeddings (
                        tool_name VARCHAR(255) PRIMARY KEY,
                        domain VARCHAR(100),
                        object VARCHAR(100),
                        action VARCHAR(100),
                        risk VARCHAR(20),
                        description TEXT,
                        embedding vector(4096),  
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # # 创建向量相似度搜索索引  ivfflat: 近似最近邻（ANN）」向量索引算法 = k-means
                # try:
                #     cur.execute("""
                #         CREATE INDEX IF NOT EXISTS tool_embeddings_embedding_idx
                #         ON tool_embeddings
                #         USING ivfflat (embedding vector_cosine_ops)
                #         WITH (lists = 100);
                #     """)
                # except Exception as e:
                #     logging.error(f"创建向量索引失败: {e}")

                self.conn.commit()
                logging.info("工具向量表已创建或者已存在")
        except Exception as e:
            logging.error("工具向量表创建失败")
            self.conn.rollback()

    def _ensure_index(self, embedding_dim: int):
        """
        确保向量索引已创建

        :param embedding_dim: 向量维度
        :return:
        """
        if not self.is_enabled():
            return

        try:
            with self.conn.cursor() as cur:
                # 检查索引是否已存在
                cur.execute("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = 'tool_embeddings' 
                    AND indexname = 'tool_embeddings_pkey';
                """)
                if cur.fetchone():
                    logging.debug("向量索引已存在")
                    return

                # 检查表中是否有数据（ivfflat 需要至少一些数据）
                cur.execute("SELECT COUNT(*) FROM tool_embeddings;")
                count = cur.fetchone()[0]

                if count == 0:
                    logging.debug("表中无数据，跳过索引创建（将在有数据后自动创建）")
                    return

                # 创建 ivfflat 索引
                lists = max(10, min(100, count // 1000))

                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS tool_embeddings_embedding_idx 
                    ON tool_embeddings 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {lists});
                """)
                self.conn.commit()
                logging.info(f"向量索引已创建（维度: {embedding_dim}, lists: {lists}）")
        except Exception as e:
            logging.warning(f"创建向量索引失败: {e}")
            self.conn.rollback()

    def is_enabled(self) -> bool:
        """查看向量存储是否启用"""
        return self.enabled and self.conn is not None

    def upsert_tool_embedding(
            self,
            tools: List[ToolMetadata],
            embeddings: List[np.ndarray]) -> bool:
        """
        批量更新或插入工具向量

        :param tools: 工具元数据列表
        :param embeddings: 对应的向量列表
        :return: 是否成功
        """
        if not self.is_enabled():
            logging.warning("向量存储未启用， 跳过工具向量更新")
            return False

        if len(tools) != len(embeddings):
            logging.error(f"工具数量 ({len(tools)}) 与向量数量 ({len(embeddings)}) 不匹配")
            return False

        try:
            # 获取第一个向量的维度（用于后续创建索引）
            embedding_dim = len(embeddings[0]) if embeddings else None
            with self.conn.cursor() as cur:
                for tool, embedding in zip(tools, embeddings):  # [tuple[ToolMetadata, Any]]
                    # 向量转换未 Pg 数据格式字符串
                    embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
                    cur.execute("""
                        INSERT INTO tool_embeddings 
                        (tool_name, domain, object, action, risk, description, embedding, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::vector, CURRENT_TIMESTAMP)
                        ON CONFLICT (tool_name) 
                        DO UPDATE SET
                            domain = EXCLUDED.domain,
                            object = EXCLUDED.object,
                            action = EXCLUDED.action,
                            risk = EXCLUDED.risk,
                            description = EXCLUDED.description,
                            embedding = EXCLUDED.embedding,
                            updated_at = CURRENT_TIMESTAMP;
                    """, (
                        tool.name, tool.domain, tool.object, tool.action, tool.risk, tool.description,
                        embedding_str))
                self.conn.commit()
                logging.info(f"成功更新 {len(tools)} 个工具的向量")

                if embedding_dim:
                    self._ensure_index(embedding_dim)
                return True
        except Exception as e:
            logging.error(f"更新工具向量失败:{e}")
            self.conn.rollback()
            return False

    def search_similar_tools(
            self,
            query_embedding: np.ndarray,
            top_k: int = 5,
            domain: Optional[str] = None,
            object_filter: Optional[str] = None,
            action_filter: Optional[str] = None,
            risk_filter: Optional[str] = None,
    ) -> List[Tuple[str, float]]:
        """
        根据查询向量搜索相似工具

        :param query_embedding: 查询向量
        :param top_k: 返回前k个结果
        :param domain: 可选的domain结果
        :param object_filter: 可选的操作对象
        :param action_filter: 可选的操作类型
        :param risk_filter: 可选的操作风险等级过滤
        :return: [(tool_name, similarity_score), ...]列表，按相似度降序
        """
        if not self.is_enabled():
            logging.warning("向量存储未启用，返回空结果")
            return []

        try:
            with self.conn.cursor() as cur:
                # 构建查询条件
                conditions = []
                params = [query_embedding, top_k]  # .tolist()

                if domain:
                    conditions.append("domain = %s")
                    params.insert(-1, domain)

                if object_filter:
                    conditions.append("object = %s")
                    params.insert(-1, object_filter)

                if action_filter:
                    conditions.append("action = %s")
                    params.insert(-1, action_filter)

                if risk_filter:
                    conditions.append("risk = %s")
                    params.insert(-1, risk_filter)

                where_clause = " AND ".join(conditions) if conditions else "1=1"

                # 使用余弦相似度搜索（1 - cosine_distance）
                # 将查询向量转换为字符串格式
                query_embedding_str = '[' + ','.join(str(x) for x in query_embedding) + ']'
                # 构建参数列表
                query_params = []
                param_index = 1

                query_params.append(query_embedding_str)

                # if domain:
                #     query_params.append(domain)
                # if object_filter:
                #     query_params.append(object_filter)
                # if action_filter:
                #     query_params.append(action_filter)
                # if risk_filter:
                #     query_params.append(risk_filter)

                query_params.append(query_embedding_str)
                query_params.append(top_k)

                # ::vector
                # query = f"""
                #     SELECT tool_name,
                #         1 - (embedding <=> %s) as similarity
                #         from tool_embeddings
                #         where {where_clause}
                #         order by embedding <=> %s
                #         LIMIT %s;
                # """
                # 暂时关闭条件过滤 只做向量检索  意图的字典不太准
                query = f"""
                    SELECT tool_name,
                        1 - (embedding <=> %s) as similarity
                        from tool_embeddings
                        order by embedding <=> %s
                        LIMIT %s;
                """

                cur.execute(query, query_params)
                results = cur.fetchall()
                logging.debug(f"向量检索返回 {len(results)} 个结果")
                return [(row[0], float(row[1])) for row in results]

        except Exception as e:
            logging.error(f"向量搜索失败: {e}")
            return []

    def get_tool_count(self) -> int:
        """获取工具向量总数"""
        if not self.is_enabled():
            return 0

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM tool_embeddings;")
                return cur.fetchone()[0]
        except Exception as e:
            logging.error(f"获取工具数量失败: {e}")

    def clear_all_tools(self):
        """清空所有工具向量"""
        if not self.is_enabled():
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE tool_embeddings;")
                self.conn.commit()
                logging.info("已清空所有工具向量")
                return True
        except Exception as e:
            logging.error(f"清空工具向量失败: {e}")
            self.conn.rollback()
            return False

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logging.info("向量存储连接已关闭")
