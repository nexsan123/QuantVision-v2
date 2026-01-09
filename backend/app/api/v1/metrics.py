"""
性能指标 API
Sprint 13: T34 - 性能监控指标

提供:
- JSON 格式指标
- Prometheus 格式指标
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.metrics import metrics

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """
    获取所有指标 (JSON 格式)

    用于仪表盘展示
    """
    return metrics.get_all_metrics()


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics():
    """
    获取 Prometheus 格式指标

    用于 Prometheus 抓取
    """
    return metrics.get_prometheus_metrics()


@router.get("/metrics/summary")
async def get_metrics_summary():
    """
    获取指标摘要

    用于快速查看关键指标
    """
    all_metrics = metrics.get_all_metrics()

    return {
        "status": "ok",
        "uptime_hours": round(all_metrics["uptime_seconds"] / 3600, 2),
        "cpu_percent": all_metrics["system"]["cpu_percent"],
        "memory_percent": all_metrics["system"]["memory_percent"],
        "http_requests_total": all_metrics["http"]["requests_total"],
        "active_strategies": all_metrics["business"]["strategies_active"],
        "websocket_connections": all_metrics["websocket"]["connections_active"],
    }
