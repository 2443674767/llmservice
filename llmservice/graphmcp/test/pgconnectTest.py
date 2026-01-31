"""初始化向量数据库脚本"""
import sys
import os

# 添加项目根目录到路径
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graphmcp.core.vector_store import VectorStore
from graphmcp.config.settings import settings
from loguru import logger


def init_vector_database():
    """初始化向量数据库（创建扩展和表）"""
    logger.info("开始初始化向量数据库...")

    if not settings.PG_VECTOR_ENABLED:
        logger.warning("PG_VECTOR_ENABLED=false，跳过初始化")
        return

    try:
        vector_store = VectorStore()

        if not vector_store.is_enabled():
            logger.error("向量存储未启用，请检查 PostgreSQL 连接配置")
            return

        logger.info("✅ 向量数据库初始化成功")
        logger.info(f"   - 数据库: {settings.PG_DATABASE}")
        logger.info(f"   - 主机: {settings.PG_HOST}:{settings.PG_PORT}")
        logger.info(f"   - 工具向量表: tool_embeddings")

        # 显示当前工具数量
        count = vector_store.get_tool_count()
        logger.info(f"   - 当前工具向量数量: {count}")

        vector_store.close()

    except Exception as e:
        logger.error(f"初始化向量数据库失败: {e}")
        raise


if __name__ == "__main__":
    init_vector_database()
