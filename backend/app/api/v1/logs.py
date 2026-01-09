"""
日志收集 API
Sprint 13: T33 - 前端日志收集

接收前端日志并转发到日志系统
"""

from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

router = APIRouter()
logger = structlog.get_logger("frontend")


# ==================== 模型定义 ====================

class ErrorInfo(BaseModel):
    name: str
    message: str
    stack: str | None = None


class PerformanceInfo(BaseModel):
    duration_ms: float
    operation: str


class UserInfo(BaseModel):
    id: str | None = None
    session_id: str | None = None


class PageInfo(BaseModel):
    url: str
    route: str | None = None


class LogEntry(BaseModel):
    level: str = Field(..., pattern="^(debug|info|warn|error)$")
    message: str
    timestamp: str
    context: dict[str, Any] | None = None
    error: ErrorInfo | None = None
    performance: PerformanceInfo | None = None
    user: UserInfo | None = None
    page: PageInfo | None = None


class LogBatch(BaseModel):
    logs: list[LogEntry]


# ==================== 日志处理 ====================

def process_log_entry(entry: LogEntry) -> None:
    """处理单条日志"""
    log_data: dict[str, Any] = {
        "source": "frontend",
        "client_timestamp": entry.timestamp,
        "page_url": entry.page.url if entry.page else None,
        "page_route": entry.page.route if entry.page else None,
        "session_id": entry.user.session_id if entry.user else None,
        "user_id": entry.user.id if entry.user else None,
    }

    # 添加上下文
    if entry.context:
        log_data["context"] = entry.context

    # 添加性能信息
    if entry.performance:
        log_data["duration_ms"] = entry.performance.duration_ms
        log_data["operation"] = entry.performance.operation

    # 添加错误信息
    if entry.error:
        log_data["error_name"] = entry.error.name
        log_data["error_message"] = entry.error.message
        log_data["error_stack"] = entry.error.stack

    # 根据级别记录日志
    if entry.level == "error":
        logger.error(entry.message, **log_data)
    elif entry.level == "warn":
        logger.warning(entry.message, **log_data)
    elif entry.level == "debug":
        logger.debug(entry.message, **log_data)
    else:
        logger.info(entry.message, **log_data)


# ==================== API 端点 ====================

@router.post("/logs")
async def receive_logs(
    batch: LogBatch,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """
    接收前端日志批量上报

    后台异步处理日志，立即返回响应
    """
    for entry in batch.logs:
        background_tasks.add_task(process_log_entry, entry)

    return {"status": "received", "count": str(len(batch.logs))}


@router.post("/logs/error")
async def receive_error(
    error: ErrorInfo,
    page: PageInfo | None = None,
    user: UserInfo | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, str]:
    """
    接收单条前端错误

    用于关键错误的即时上报
    """
    logger.error(
        "frontend_error",
        error_name=error.name,
        error_message=error.message,
        error_stack=error.stack,
        page_url=page.url if page else None,
        session_id=user.session_id if user else None,
        context=context,
    )

    return {"status": "received"}
