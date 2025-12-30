"""
健康检查 API

提供:
- 应用健康状态
- 组件状态检查
- 版本信息
"""

from datetime import datetime

import structlog
from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DBSession, RedisConn
from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: DBSession,
    redis: RedisConn,
) -> HealthResponse:
    """
    健康检查

    检查各组件状态:
    - 数据库连接
    - Redis 连接
    - 应用版本
    """
    components = {}

    # 检查数据库
    try:
        await db.execute(text("SELECT 1"))
        components["database"] = "healthy"
    except Exception as e:
        logger.error("数据库检查失败", error=str(e))
        components["database"] = "unhealthy"

    # 检查 Redis
    try:
        await redis.ping()
        components["redis"] = "healthy"
    except Exception as e:
        logger.error("Redis 检查失败", error=str(e))
        components["redis"] = "unhealthy"

    # 整体状态
    all_healthy = all(v == "healthy" for v in components.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        timestamp=datetime.now(),
        components=components,
    )


@router.get("/health/live")
async def liveness_probe() -> dict[str, str]:
    """
    存活探针

    Kubernetes 存活检查使用
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe(
    db: DBSession,
    redis: RedisConn,
) -> dict[str, str]:
    """
    就绪探针

    Kubernetes 就绪检查使用
    """
    # 检查数据库
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        return {"status": "not_ready", "reason": "database_unavailable"}

    # 检查 Redis
    try:
        await redis.ping()
    except Exception:
        return {"status": "not_ready", "reason": "redis_unavailable"}

    return {"status": "ready"}
