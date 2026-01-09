"""
数据库连接模块

使用 SQLAlchemy 2.0 异步引擎，支持:
- 连接池管理
- 会话生命周期管理
- 异步上下文管理器
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    """
    SQLAlchemy 声明式基类

    所有模型继承此基类，自动获得:
    - 表名映射
    - 元数据管理
    - 类型注解支持
    """
    pass


def create_engine_instance() -> AsyncEngine:
    """
    创建异步数据库引擎

    根据环境配置不同的连接池策略:
    - 开发环境: 使用 NullPool 避免连接泄漏
    - 生产环境: 使用默认连接池，配置合理的 pool_size
    """
    # 开发环境使用 NullPool，不需要 pool_size/max_overflow
    if settings.DEBUG:
        return create_async_engine(
            settings.DATABASE_URL,
            echo=True,
            poolclass=NullPool,
        )

    # 生产环境使用连接池
    return create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


# 全局引擎实例
engine = create_engine_instance()

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话依赖注入

    用法:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...

    会话会在请求结束后自动关闭
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话上下文管理器

    用于非 FastAPI 依赖注入场景（如 Celery 任务）:
        async with get_db_context() as db:
            result = await db.execute(query)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化数据库

    创建所有表结构。仅用于开发环境快速初始化，
    生产环境应使用 Alembic 迁移。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    关闭数据库连接

    应用关闭时调用，释放所有连接池资源
    """
    await engine.dispose()
