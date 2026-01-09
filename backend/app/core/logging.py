"""
结构化日志系统
Sprint 13: T32 - 日志与监控

提供:
- 结构化日志配置
- 请求追踪 (Correlation ID)
- 性能日志
- 日志上下文管理
"""

import logging
import sys
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

# ==================== 上下文变量 ====================

# 请求追踪 ID
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
# 用户 ID
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
# 请求路径
request_path_var: ContextVar[str] = ContextVar("request_path", default="")


# ==================== 处理器 ====================

def add_correlation_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """添加 correlation_id 到日志"""
    correlation_id = correlation_id_var.get()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_user_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """添加用户上下文"""
    user_id = user_id_var.get()
    if user_id:
        event_dict["user_id"] = user_id
    return event_dict


def add_service_info(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """添加服务信息"""
    event_dict["service"] = settings.APP_NAME
    event_dict["version"] = settings.APP_VERSION
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


# ==================== 日志配置 ====================

def configure_logging() -> None:
    """配置结构化日志"""

    # 设置标准库日志级别
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    # 处理器链
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_correlation_id,
        add_user_context,
        add_service_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # 根据环境选择渲染器
    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        ))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """获取日志记录器"""
    return structlog.get_logger(name)


# ==================== 请求日志中间件 ====================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件

    记录:
    - 请求开始/结束
    - 响应时间
    - 状态码
    - 错误信息
    """

    def __init__(self, app: Any, exclude_paths: list[str] | None = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]
        self.logger = get_logger("http")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过排除的路径
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)

        # 生成 correlation_id
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        correlation_id_var.set(correlation_id)
        request_path_var.set(request.url.path)

        # 记录请求开始
        start_time = time.perf_counter()

        self.logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params) if request.query_params else None,
            client_ip=request.client.host if request.client else None,
        )

        # 处理请求
        try:
            response = await call_next(request)

            # 计算响应时间
            duration_ms = (time.perf_counter() - start_time) * 1000

            # 添加追踪头
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

            # 记录请求完成
            log_method = self.logger.info if response.status_code < 400 else self.logger.warning
            log_method(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            return response

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000

            self.logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise


# ==================== 性能日志装饰器 ====================

def log_performance(
    operation: str | None = None,
    log_args: bool = False,
    log_result: bool = False,
    warn_threshold_ms: float = 1000,
):
    """
    性能日志装饰器

    Args:
        operation: 操作名称
        log_args: 是否记录参数
        log_result: 是否记录结果
        warn_threshold_ms: 警告阈值 (毫秒)
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        op_name = operation or func.__name__

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()

            extra: dict[str, Any] = {"operation": op_name}
            if log_args:
                extra["args"] = str(args)[:200]
                extra["kwargs"] = str(kwargs)[:200]

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                if log_result:
                    extra["result"] = str(result)[:200]

                log_method = logger.warning if duration_ms > warn_threshold_ms else logger.debug
                log_method(
                    "operation_completed",
                    duration_ms=round(duration_ms, 2),
                    **extra,
                )

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    "operation_failed",
                    duration_ms=round(duration_ms, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    **extra,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()

            extra: dict[str, Any] = {"operation": op_name}
            if log_args:
                extra["args"] = str(args)[:200]
                extra["kwargs"] = str(kwargs)[:200]

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                if log_result:
                    extra["result"] = str(result)[:200]

                log_method = logger.warning if duration_ms > warn_threshold_ms else logger.debug
                log_method(
                    "operation_completed",
                    duration_ms=round(duration_ms, 2),
                    **extra,
                )

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    "operation_failed",
                    duration_ms=round(duration_ms, 2),
                    error=str(e),
                    error_type=type(e).__name__,
                    **extra,
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ==================== 业务日志类 ====================

class AuditLogger:
    """审计日志记录器"""

    def __init__(self):
        self.logger = get_logger("audit")

    def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        success: bool = True,
    ) -> None:
        """记录审计操作"""
        log_method = self.logger.info if success else self.logger.warning

        log_method(
            "audit_action",
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            success=success,
            details=details,
        )

    def log_trade(
        self,
        action: str,  # BUY, SELL, CANCEL
        symbol: str,
        quantity: float,
        price: float | None = None,
        order_id: str | None = None,
        strategy_id: str | None = None,
    ) -> None:
        """记录交易操作"""
        self.logger.info(
            "trade_action",
            action=action,
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_id=order_id,
            strategy_id=strategy_id,
        )

    def log_strategy_event(
        self,
        event: str,  # DEPLOYED, STOPPED, PAUSED, ERROR
        strategy_id: str,
        strategy_name: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """记录策略事件"""
        self.logger.info(
            "strategy_event",
            event=event,
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            details=details,
        )


# 全局审计日志实例
audit_logger = AuditLogger()


# ==================== 导出 ====================

__all__ = [
    "configure_logging",
    "get_logger",
    "RequestLoggingMiddleware",
    "log_performance",
    "audit_logger",
    "correlation_id_var",
    "user_id_var",
]
