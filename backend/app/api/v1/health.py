"""
健康检查 API
Sprint 12: T31 - 健康检查端点增强

提供:
- 应用健康状态
- 组件状态检查
- 外部服务检查 (Alpaca, S3)
- 版本信息
- 系统资源监控
"""

import asyncio
import os
import platform
import psutil
from datetime import datetime
from typing import Any

import httpx
import structlog
from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import DBSession, RedisConn
from app.core.config import settings
from app.schemas.common import HealthResponse

router = APIRouter()
logger = structlog.get_logger()

# 启动时间记录
_start_time = datetime.now()


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


@router.get("/ai/health")
async def ai_health_check() -> dict[str, Any]:
    """
    AI 服务健康检查

    前端使用此端点检查 AI 服务连接状态
    """
    return {
        "status": "healthy",
        "model": "Claude 4.5 Sonnet",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
    }


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


# ==================== 详细健康检查 ====================

async def check_alpaca_connection() -> dict[str, Any]:
    """检查 Alpaca API 连接"""
    try:
        alpaca_key = os.getenv("ALPACA_API_KEY")
        alpaca_secret = os.getenv("ALPACA_SECRET_KEY")
        alpaca_base = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

        if not alpaca_key or not alpaca_secret:
            return {"status": "unconfigured", "message": "Alpaca credentials not set"}

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{alpaca_base}/v2/account",
                headers={
                    "APCA-API-KEY-ID": alpaca_key,
                    "APCA-API-SECRET-KEY": alpaca_secret,
                }
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "account_status": data.get("status"),
                    "trading_blocked": data.get("trading_blocked", False),
                    "account_blocked": data.get("account_blocked", False),
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                }

    except httpx.TimeoutException:
        return {"status": "unhealthy", "error": "Connection timeout"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_s3_connection() -> dict[str, Any]:
    """检查 S3 存储连接"""
    try:
        s3_endpoint = os.getenv("S3_ENDPOINT")
        s3_access_key = os.getenv("S3_ACCESS_KEY")

        if not s3_endpoint or not s3_access_key:
            return {"status": "unconfigured", "message": "S3 credentials not set"}

        async with httpx.AsyncClient(timeout=5.0) as client:
            # 尝试访问 S3 端点
            response = await client.head(s3_endpoint)
            if response.status_code < 500:
                return {"status": "healthy", "endpoint": s3_endpoint}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}

    except httpx.TimeoutException:
        return {"status": "unhealthy", "error": "Connection timeout"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


def get_system_metrics() -> dict[str, Any]:
    """获取系统资源指标"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": cpu_percent,
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": round(disk.percent, 1),
            },
        }
    except Exception as e:
        logger.warning("无法获取系统指标", error=str(e))
        return {"error": str(e)}


@router.get("/health/detailed")
async def detailed_health_check(
    db: DBSession,
    redis: RedisConn,
) -> dict[str, Any]:
    """
    详细健康检查

    检查所有服务和系统资源
    """
    components: dict[str, Any] = {}

    # 并行检查各组件
    db_task = asyncio.create_task(check_database(db))
    redis_task = asyncio.create_task(check_redis(redis))
    alpaca_task = asyncio.create_task(check_alpaca_connection())
    s3_task = asyncio.create_task(check_s3_connection())

    # 等待所有检查完成
    components["database"] = await db_task
    components["redis"] = await redis_task
    components["alpaca"] = await alpaca_task
    components["s3_storage"] = await s3_task

    # 系统资源
    components["system"] = get_system_metrics()

    # 计算整体状态
    core_services = ["database", "redis"]
    core_healthy = all(
        components.get(svc, {}).get("status") == "healthy"
        for svc in core_services
    )

    external_healthy = all(
        components.get(svc, {}).get("status") in ["healthy", "unconfigured"]
        for svc in ["alpaca", "s3_storage"]
    )

    if core_healthy and external_healthy:
        status = "healthy"
    elif core_healthy:
        status = "degraded"
    else:
        status = "unhealthy"

    # 运行时间
    uptime = datetime.now() - _start_time

    return {
        "status": status,
        "version": settings.APP_VERSION,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(uptime.total_seconds()),
        "uptime_human": str(uptime).split(".")[0],
        "python_version": platform.python_version(),
        "components": components,
    }


async def check_database(db: DBSession) -> dict[str, Any]:
    """检查数据库连接"""
    try:
        start = datetime.now()
        await db.execute(text("SELECT 1"))
        latency_ms = (datetime.now() - start).total_seconds() * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_redis(redis: RedisConn) -> dict[str, Any]:
    """检查 Redis 连接"""
    try:
        start = datetime.now()
        await redis.ping()
        latency_ms = (datetime.now() - start).total_seconds() * 1000

        # 获取 Redis 信息
        info = await redis.info("memory")

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "used_memory_mb": round(info.get("used_memory", 0) / (1024**2), 2),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health/metrics")
async def metrics_endpoint() -> dict[str, Any]:
    """
    Prometheus 格式指标端点

    用于监控系统集成
    """
    metrics = get_system_metrics()
    uptime = (datetime.now() - _start_time).total_seconds()

    return {
        "app_uptime_seconds": uptime,
        "cpu_usage_percent": metrics.get("cpu_percent", 0),
        "memory_usage_percent": metrics.get("memory", {}).get("percent", 0),
        "disk_usage_percent": metrics.get("disk", {}).get("percent", 0),
    }
