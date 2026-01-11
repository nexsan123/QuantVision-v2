"""
FastAPI 应用入口
Sprint 13: 增强日志与监控

应用生命周期管理、路由注册、中间件配置
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis import RedisClient
from app.core.logging import configure_logging, get_logger, RequestLoggingMiddleware

# 配置结构化日志
configure_logging()

logger = get_logger(__name__)


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

    db_connected = False
    redis_connected = False

    try:
        # 初始化数据库 (可选，失败不阻止启动)
        if settings.DEBUG:
            try:
                await init_db()
                db_connected = True
                logger.info("数据库初始化完成")
            except Exception as e:
                logger.warning("数据库连接失败，部分功能不可用", error=str(e))

        # 初始化 Redis (可选，失败不阻止启动)
        try:
            await RedisClient.connect()
            redis_connected = True
            logger.info("Redis 连接成功")
        except Exception as e:
            logger.warning("Redis 连接失败，缓存功能不可用", error=str(e))

        logger.info("应用启动完成", environment=settings.ENVIRONMENT, db=db_connected, redis=redis_connected)
        yield

    finally:
        # 关闭
        logger.info("应用关闭中...")
        try:
            await close_db()
        except Exception:
            pass
        try:
            await RedisClient.disconnect()
        except Exception:
            pass
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

    # 请求日志中间件 (Sprint 13)
    app.add_middleware(
        RequestLoggingMiddleware,
        exclude_paths=["/api/v1/health", "/docs", "/openapi.json"],
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
    from app.api.v1 import account, ai_assistant, advanced_backtest, alerts, attribution, auth, backtests, conflict, deployment, drift, execution, factor_validation, factors, health, logs, metrics, notifications, manual_trade, market_data, pdt, positions, pre_market, realtime, replay, risk, risk_advanced, signal_radar, strategy, strategy_v2, templates, trade_attribution, trading, trading_cost, validation
    from app.websocket import trading_router, alpaca_router

    # WebSocket 路由 (根路径)
    app.include_router(
        trading_router,
        tags=["WebSocket"],
    )

    # Alpaca WebSocket 路由 (Sprint 10)
    app.include_router(
        alpaca_router,
        tags=["WebSocket - Alpaca"],
    )

    app.include_router(
        health.router,
        prefix=settings.API_V1_PREFIX,
        tags=["健康检查"],
    )
    # Phase 3: 认证与授权 API
    app.include_router(
        auth.router,
        prefix=settings.API_V1_PREFIX,
        tags=["认证"],
    )
    # 账户总览 API
    app.include_router(
        account.router,
        prefix=settings.API_V1_PREFIX,
        tags=["账户"],
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
    # v2.1 Sprint 1: 策略部署 API
    app.include_router(
        deployment.router,
        prefix=settings.API_V1_PREFIX,
        tags=["策略部署"],
    )
    # v2.1 Sprint 2: 信号雷达 API
    app.include_router(
        signal_radar.router,
        prefix=settings.API_V1_PREFIX,
        tags=["信号雷达"],
    )
    # v2.1 Sprint 3: PDT 规则 API
    app.include_router(
        pdt.router,
        prefix=settings.API_V1_PREFIX,
        tags=["PDT规则"],
    )
    # v2.1 Sprint 3: 风险预警 API
    app.include_router(
        alerts.router,
        prefix=settings.API_V1_PREFIX,
        tags=["风险预警"],
    )
    # v2.1 Sprint 4: 策略漂移监控 API
    app.include_router(
        drift.router,
        prefix=settings.API_V1_PREFIX,
        tags=["漂移监控"],
    )
    # v2.1 Sprint 5: 因子有效性验证 API (PRD 4.3)
    app.include_router(
        factor_validation.router,
        prefix=settings.API_V1_PREFIX,
        tags=["因子验证"],
    )
    # v2.1 Sprint 5: 交易归因 API (PRD 4.5)
    app.include_router(
        trade_attribution.router,
        prefix=settings.API_V1_PREFIX,
        tags=["交易归因"],
    )
    # v2.1 Sprint 5: 策略冲突检测 API (PRD 4.6)
    app.include_router(
        conflict.router,
        prefix=settings.API_V1_PREFIX,
        tags=["冲突检测"],
    )
    # v2.1 Sprint 6: 交易成本配置 API (PRD 4.4)
    app.include_router(
        trading_cost.router,
        prefix=settings.API_V1_PREFIX,
        tags=["交易成本"],
    )
    # v2.1 Sprint 6: 策略模板库 API (PRD 4.13)
    app.include_router(
        templates.router,
        prefix=settings.API_V1_PREFIX,
        tags=["策略模板"],
    )
    # v2.1 Sprint 7: 手动交易 API (PRD 4.16)
    app.include_router(
        manual_trade.router,
        prefix=settings.API_V1_PREFIX,
        tags=["手动交易"],
    )
    # v2.1 Sprint 7: 分策略持仓管理 API (PRD 4.18)
    app.include_router(
        positions.router,
        prefix=settings.API_V1_PREFIX,
        tags=["持仓管理"],
    )
    # v2.1 Sprint 8: 日内交易 API (PRD 4.18.0-4.18.1)
    app.include_router(
        pre_market.router,
        prefix=settings.API_V1_PREFIX,
        tags=["日内交易"],
    )
    # v2.1 Sprint 9: 策略回放 API (PRD 4.17)
    app.include_router(
        replay.router,
        prefix=settings.API_V1_PREFIX,
        tags=["策略回放"],
    )
    # v2.1 Sprint 10: 实时监控 API
    app.include_router(
        realtime.router,
        prefix=settings.API_V1_PREFIX,
        tags=["实时监控"],
    )
    # v2.1 Sprint 13: 日志收集 API
    app.include_router(
        logs.router,
        prefix=settings.API_V1_PREFIX,
        tags=["日志"],
    )
    # v2.1 Sprint 13: 性能指标 API
    app.include_router(
        metrics.router,
        prefix=settings.API_V1_PREFIX,
        tags=["指标"],
    )
    # v2.1 Sprint 13: 通知管理 API
    app.include_router(
        notifications.router,
        prefix=settings.API_V1_PREFIX,
        tags=["通知"],
    )


# 创建应用实例
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
