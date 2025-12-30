"""
Redis 连接模块

提供:
- 异步 Redis 客户端
- 连接池管理
- 缓存工具函数
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings


class RedisClient:
    """
    Redis 客户端封装

    提供连接池管理和常用缓存操作的封装
    """

    _pool: ConnectionPool | None = None
    _client: Redis | None = None

    @classmethod
    async def connect(cls) -> None:
        """
        初始化 Redis 连接池

        应用启动时调用
        """
        if cls._pool is None:
            cls._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,
                decode_responses=True,
            )
            cls._client = Redis(connection_pool=cls._pool)

    @classmethod
    async def disconnect(cls) -> None:
        """
        关闭 Redis 连接

        应用关闭时调用
        """
        if cls._client:
            await cls._client.close()
            cls._client = None
        if cls._pool:
            await cls._pool.disconnect()
            cls._pool = None

    @classmethod
    def get_client(cls) -> Redis:
        """
        获取 Redis 客户端实例

        Raises:
            RuntimeError: 如果连接未初始化
        """
        if cls._client is None:
            raise RuntimeError("Redis 未连接，请先调用 RedisClient.connect()")
        return cls._client

    # === 缓存工具方法 ===

    @classmethod
    async def get(cls, key: str) -> str | None:
        """获取缓存值"""
        client = cls.get_client()
        return await client.get(key)

    @classmethod
    async def set(
        cls,
        key: str,
        value: str,
        expire: int | None = None,
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒），None 表示永不过期
        """
        client = cls.get_client()
        return await client.set(key, value, ex=expire)

    @classmethod
    async def delete(cls, *keys: str) -> int:
        """删除缓存键"""
        client = cls.get_client()
        return await client.delete(*keys)

    @classmethod
    async def exists(cls, key: str) -> bool:
        """检查键是否存在"""
        client = cls.get_client()
        return await client.exists(key) > 0

    @classmethod
    async def hget(cls, name: str, key: str) -> str | None:
        """获取哈希表字段"""
        client = cls.get_client()
        return await client.hget(name, key)

    @classmethod
    async def hset(cls, name: str, key: str, value: str) -> int:
        """设置哈希表字段"""
        client = cls.get_client()
        return await client.hset(name, key, value)

    @classmethod
    async def hgetall(cls, name: str) -> dict[str, str]:
        """获取哈希表所有字段"""
        client = cls.get_client()
        return await client.hgetall(name)


# 全局 Redis 客户端实例
redis_client = RedisClient


async def get_redis() -> Redis:
    """
    Redis 依赖注入

    用法:
        @app.get("/cached")
        async def get_cached(redis: Redis = Depends(get_redis)):
            ...
    """
    return RedisClient.get_client()


@asynccontextmanager
async def get_redis_context() -> AsyncGenerator[Redis, None]:
    """
    Redis 上下文管理器

    用于非 FastAPI 依赖注入场景:
        async with get_redis_context() as redis:
            await redis.set("key", "value")
    """
    yield RedisClient.get_client()
