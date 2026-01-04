"""
FastAPI 应用入口

应用生命周期管理、路由注册、中间件配置
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis import RedisClient

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json"
        else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理

    启动时:
    - 初始化数据库连接
    - 初始化 Redis 连接

    关闭时:
    - 释放所有连接资源
    """
    # 启动
    logger.info("应用启动中...", version=settings.APP_VERSION)

    try:
        # 初始化数据库
        if settings.DEBUG:
            await init_db()
            logger.info("数据库初始化完成")

        # 初始化 Redis
        await RedisClient.connect()
        logger.info("Redis 连接成功")

        logger.info("应用启动完成", environment=settings.ENVIRONMENT)
        yield

    finally:
        # 关闭
        logger.info("应用关闭中...")
        await close_db()
        await RedisClient.disconnect()
        logger.info("应用已关闭")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例

    工厂函数模式，便于测试和多实例部署
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="量化投资平台 - 机构级因子研究与回测系统",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """
    注册 API 路由

    所有 v1 版本的路由都挂载在 /api/v1 前缀下
    WebSocket 路由挂载在根路径
    """
    from app.api.v1 import ai_assistant, advanced_backtest, attribution, backtests, execution, factors, health, market_data, risk, risk_advanced, strategy, strategy_v2, trading, validation
    from app.websocket import trading_router

    # WebSocket 路由 (根路径)
    app.include_router(
        trading_router,
        tags=["WebSocket"],
    )

    app.include_router(
        health.router,
        prefix=settings.API_V1_PREFIX,
        tags=["健康检查"],
    )
    app.include_router(
        factors.router,
        prefix=settings.API_V1_PREFIX,
        tags=["因子"],
    )
    app.include_router(
        backtests.router,
        prefix=settings.API_V1_PREFIX,
        tags=["回测"],
    )
    app.include_router(
        strategy.router,
        prefix=settings.API_V1_PREFIX,
        tags=["策略框架"],
    )
    app.include_router(
        validation.router,
        prefix=settings.API_V1_PREFIX,
        tags=["策略验证"],
    )
    app.include_router(
        risk.router,
        prefix=settings.API_V1_PREFIX,
        tags=["风险管理"],
    )
    app.include_router(
        execution.router,
        prefix=settings.API_V1_PREFIX,
        tags=["执行系统"],
    )
    # Phase 8: 7步策略构建器 V2 API
    app.include_router(
        strategy_v2.router,
        prefix=settings.API_V1_PREFIX,
        tags=["策略构建器V2"],
    )
    # Phase 8: AI助手 API
    app.include_router(
        ai_assistant.router,
        prefix=settings.API_V1_PREFIX,
        tags=["AI助手"],
    )
    # Phase 9: 高级回测 API
    app.include_router(
        advanced_backtest.router,
        prefix=settings.API_V1_PREFIX,
        tags=["高级回测"],
    )
    # Phase 10: 风险系统升级 API
    app.include_router(
        risk_advanced.router,
        prefix=settings.API_V1_PREFIX,
        tags=["风险系统升级"],
    )
    # Phase 11: \u6570\u636e\u5c42\u5347\u7ea7 API
    app.include_router(
        market_data.router,
        prefix=settings.API_V1_PREFIX,
        tags=["\u5e02\u573a\u6570\u636e"],
    )
    # Phase 12: \u6267\u884c\u5c42\u5347\u7ea7 API
    app.include_router(
        trading.router,
        prefix=settings.API_V1_PREFIX,
        tags=["\u4ea4\u6613"],
    )
    # Phase 13: \u5f52\u56e0\u4e0e\u62a5\u8868 API
    app.include_router(
        attribution.router,
        prefix=settings.API_V1_PREFIX,
        tags=["\u5f52\u56e0\u5206\u6790"],
    )


# \u521b\u5efa\u5e94\u7528\u5b9e\u4f8b
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
