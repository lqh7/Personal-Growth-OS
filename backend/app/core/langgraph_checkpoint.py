"""
LangGraph PostgreSQL Checkpointer配置（异步版本）
用于持久化agent对话状态和历史消息

基于LangGraph 1.0官方文档最佳实践
"""

from typing import Optional
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# 全局Checkpointer实例和连接池
_checkpointer: Optional[AsyncPostgresSaver] = None
_pool: Optional[AsyncConnectionPool] = None


async def init_checkpointer() -> AsyncPostgresSaver:
    """
    初始化PostgreSQL Checkpointer (应用启动时调用)

    使用AsyncPostgresSaver + AsyncConnectionPool
    避免使用from_conn_string()上下文管理器导致的连接关闭问题

    Returns:
        AsyncPostgresSaver实例

    Raises:
        Exception: 如果数据库连接失败或表创建失败
    """
    global _checkpointer, _pool

    if _checkpointer is None:
        try:
            logger.info("初始化 LangGraph PostgreSQL Checkpointer (Async)...")

            # 创建异步连接池 (不自动打开，手动调用open)
            _pool = AsyncConnectionPool(
                conninfo=settings.DATABASE_URL,
                max_size=10,
                min_size=2,
                timeout=30,
                open=False,  # 不自动打开，避免警告
            )

            # 手动打开连接池
            await _pool.open()

            # 使用连接池创建 AsyncPostgresSaver
            _checkpointer = AsyncPostgresSaver(_pool)

            # 初始化数据库表
            await _checkpointer.setup()

            logger.info("LangGraph Checkpointer 初始化成功 (Async)")

        except Exception as e:
            logger.error(f"初始化 Checkpointer 失败: {str(e)}", exc_info=True)
            raise

    return _checkpointer


def get_checkpointer() -> Optional[AsyncPostgresSaver]:
    """
    获取全局Checkpointer实例

    Returns:
        AsyncPostgresSaver实例,如果未初始化则返回None
    """
    if _checkpointer is None:
        logger.warning("Checkpointer 未初始化,请先调用 init_checkpointer()")

    return _checkpointer


async def shutdown_checkpointer():
    """
    关闭Checkpointer和连接池 (应用关闭时调用)
    """
    global _checkpointer, _pool

    if _pool is not None:
        try:
            logger.info("关闭 LangGraph Checkpointer 连接池...")
            await _pool.close()
            _pool = None
            _checkpointer = None
            logger.info("LangGraph Checkpointer 连接池已关闭")
        except Exception as e:
            logger.error(f"关闭连接池失败: {str(e)}", exc_info=True)
