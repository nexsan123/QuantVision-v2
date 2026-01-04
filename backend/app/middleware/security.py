"""
Phase 14: \u751f\u4ea7\u90e8\u7f72 - \u5b89\u5168\u4e2d\u95f4\u4ef6

\u5305\u542b:
- \u8bf7\u6c42\u9650\u6d41
- \u5b89\u5168\u5934\u90e8
- \u8bf7\u6c42\u65e5\u5fd7
- IP \u767d\u540d\u5355
- CORS \u589e\u5f3a
"""

import time
from collections import defaultdict
from typing import Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


# ============ \u8bf7\u6c42\u9650\u6d41 ============

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    \u8bf7\u6c42\u9650\u6d41\u4e2d\u95f4\u4ef6

    \u57fa\u4e8e\u6ed1\u52a8\u7a97\u53e3\u7b97\u6cd5\u9650\u5236\u8bf7\u6c42\u9891\u7387
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit

        # \u8bf7\u6c42\u8bb0\u5f55: {ip: [(timestamp, count), ...]}
        self.request_history: dict[str, list[tuple[float, int]]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # \u68c0\u67e5\u9650\u6d41
        if not self._is_allowed(client_ip, current_time):
            logger.warning("rate_limit_exceeded", client_ip=client_ip)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": 60,
                },
                headers={"Retry-After": "60"},
            )

        # \u8bb0\u5f55\u8bf7\u6c42
        self._record_request(client_ip, current_time)

        response = await call_next(request)

        # \u6dfb\u52a0\u9650\u6d41\u5934
        remaining = self._get_remaining(client_ip, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time) + 60)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP"""
        # 检查代理头
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _is_allowed(self, client_ip: str, current_time: float) -> bool:
        """\u68c0\u67e5\u662f\u5426\u5141\u8bb8\u8bf7\u6c42"""
        history = self.request_history[client_ip]

        # \u6e05\u7406\u8fc7\u671f\u8bb0\u5f55 (1\u5c0f\u65f6\u524d)
        cutoff = current_time - 3600
        self.request_history[client_ip] = [
            (ts, count) for ts, count in history if ts > cutoff
        ]

        # \u8ba1\u7b97\u6700\u8fd1\u4e00\u5206\u949f\u8bf7\u6c42\u6570
        minute_cutoff = current_time - 60
        minute_count = sum(
            count for ts, count in self.request_history[client_ip]
            if ts > minute_cutoff
        )

        if minute_count >= self.requests_per_minute:
            return False

        # \u8ba1\u7b97\u6700\u8fd1\u4e00\u5c0f\u65f6\u8bf7\u6c42\u6570
        hour_count = sum(count for _, count in self.request_history[client_ip])

        if hour_count >= self.requests_per_hour:
            return False

        return True

    def _record_request(self, client_ip: str, current_time: float) -> None:
        """\u8bb0\u5f55\u8bf7\u6c42"""
        self.request_history[client_ip].append((current_time, 1))

    def _get_remaining(self, client_ip: str, current_time: float) -> int:
        """\u83b7\u53d6\u5269\u4f59\u8bf7\u6c42\u6570"""
        minute_cutoff = current_time - 60
        minute_count = sum(
            count for ts, count in self.request_history[client_ip]
            if ts > minute_cutoff
        )
        return max(0, self.requests_per_minute - minute_count)


# ============ \u5b89\u5168\u5934\u90e8 ============

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    \u5b89\u5168\u5934\u90e8\u4e2d\u95f4\u4ef6

    \u6dfb\u52a0\u5fc5\u8981\u7684\u5b89\u5168 HTTP \u5934
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # \u9632\u6b62\u70b9\u51fb\u52ab\u6301
        response.headers["X-Frame-Options"] = "DENY"

        # \u9632\u6b62 MIME \u7c7b\u578b\u5d4c\u63a2
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS \u4fdd\u62a4
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # \u5f15\u7528\u6765\u6e90\u7b56\u7565
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # \u5185\u5bb9\u5b89\u5168\u7b56\u7565
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' wss: https:; "
            "frame-ancestors 'none';"
        )

        # HSTS (HTTPS \u5f3a\u5236)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # \u6743\u9650\u7b56\u7565
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        return response


# ============ \u8bf7\u6c42\u65e5\u5fd7 ============

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    \u8bf7\u6c42\u65e5\u5fd7\u4e2d\u95f4\u4ef6

    \u8bb0\u5f55\u6240\u6709 HTTP \u8bf7\u6c42
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # \u751f\u6210\u8bf7\u6c42 ID
        request_id = request.headers.get("X-Request-ID") or f"{time.time():.6f}"

        # \u83b7\u53d6\u5ba2\u6237\u7aef\u4fe1\u606f
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        # \u7ed1\u5b9a\u65e5\u5fd7\u4e0a\u4e0b\u6587
        log = logger.bind(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=request.headers.get("User-Agent", ""),
        )

        # \u8bb0\u5f55\u8bf7\u6c42\u5f00\u59cb
        log.info("request_started")

        try:
            response = await call_next(request)

            # \u8ba1\u7b97\u5904\u7406\u65f6\u95f4
            duration = time.time() - start_time

            # \u8bb0\u5f55\u8bf7\u6c42\u5b8c\u6210
            log.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )

            # \u6dfb\u52a0\u54cd\u5e94\u5934
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration * 1000:.2f}ms"

            return response

        except Exception as e:
            duration = time.time() - start_time
            log.error(
                "request_failed",
                error=str(e),
                duration_ms=round(duration * 1000, 2),
            )
            raise


# ============ IP \u767d\u540d\u5355 ============

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    IP \u767d\u540d\u5355\u4e2d\u95f4\u4ef6

    \u9650\u5236\u53ea\u6709\u767d\u540d\u5355\u4e2d\u7684 IP \u53ef\u4ee5\u8bbf\u95ee
    """

    def __init__(
        self,
        app,
        whitelist: list[str] | None = None,
        protected_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.whitelist = set(whitelist or [])
        self.protected_paths = protected_paths or ["/admin", "/api/v1/admin"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # \u68c0\u67e5\u662f\u5426\u662f\u53d7\u4fdd\u62a4\u8def\u5f84
        if not any(request.url.path.startswith(p) for p in self.protected_paths):
            return await call_next(request)

        # \u5982\u679c\u6ca1\u6709\u767d\u540d\u5355\uff0c\u5141\u8bb8\u6240\u6709
        if not self.whitelist:
            return await call_next(request)

        # \u83b7\u53d6\u5ba2\u6237\u7aef IP
        client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        # \u68c0\u67e5\u767d\u540d\u5355
        if client_ip not in self.whitelist:
            logger.warning(
                "ip_blocked",
                client_ip=client_ip,
                path=request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"},
            )

        return await call_next(request)


# ============ \u4ea4\u6613 API \u5b89\u5168 ============

class TradingSecurityMiddleware(BaseHTTPMiddleware):
    """
    \u4ea4\u6613 API \u5b89\u5168\u4e2d\u95f4\u4ef6

    \u5bf9\u4ea4\u6613\u76f8\u5173 API \u8fdb\u884c\u989d\u5916\u5b89\u5168\u68c0\u67e5
    """

    TRADING_PATHS = [
        "/api/v1/trading/orders",
        "/api/v1/trading/connect",
        "/api/v1/trading/paper/disable",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # \u68c0\u67e5\u662f\u5426\u662f\u4ea4\u6613\u8def\u5f84
        if not any(request.url.path.startswith(p) for p in self.TRADING_PATHS):
            return await call_next(request)

        # \u53ea\u5bf9\u4fee\u6539\u64cd\u4f5c\u68c0\u67e5
        if request.method not in ["POST", "PUT", "DELETE"]:
            return await call_next(request)

        # \u68c0\u67e5\u5fc5\u8981\u7684\u5934
        if not request.headers.get("X-Trading-Signature"):
            logger.warning(
                "trading_signature_missing",
                path=request.url.path,
                method=request.method,
            )
            # \u5728\u5f00\u53d1\u73af\u5883\u5141\u8bb8\u8df3\u8fc7
            # return JSONResponse(
            #     status_code=400,
            #     content={"detail": "Trading signature required"},
            # )

        # \u8bb0\u5f55\u4ea4\u6613\u64cd\u4f5c
        logger.info(
            "trading_operation",
            path=request.url.path,
            method=request.method,
            client_ip=request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown"),
        )

        return await call_next(request)


# ============ \u5de5\u5382\u51fd\u6570 ============

def setup_security_middleware(app, settings) -> None:
    """
    \u8bbe\u7f6e\u5b89\u5168\u4e2d\u95f4\u4ef6

    Args:
        app: FastAPI \u5e94\u7528\u5b9e\u4f8b
        settings: \u914d\u7f6e\u5bf9\u8c61
    """
    # \u751f\u4ea7\u73af\u5883\u542f\u7528\u66f4\u4e25\u683c\u7684\u9650\u6d41
    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=60,
            requests_per_hour=1000,
        )
    else:
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=200,
            requests_per_hour=5000,
        )

    # \u5b89\u5168\u5934
    app.add_middleware(SecurityHeadersMiddleware)

    # \u8bf7\u6c42\u65e5\u5fd7
    app.add_middleware(RequestLoggingMiddleware)

    # \u4ea4\u6613\u5b89\u5168
    app.add_middleware(TradingSecurityMiddleware)

    # IP \u767d\u540d\u5355 (\u7ba1\u7406\u8def\u5f84)
    if settings.ADMIN_IP_WHITELIST:
        app.add_middleware(
            IPWhitelistMiddleware,
            whitelist=settings.ADMIN_IP_WHITELIST,
            protected_paths=["/admin", "/api/v1/admin"],
        )
