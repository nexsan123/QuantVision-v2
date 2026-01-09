"""
生产安全配置
Sprint 14: T40 - 生产安全加固

提供:
- 安全 HTTP 头
- CORS 配置
- 速率限制
- 请求验证
"""

import time
from collections import defaultdict
from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


# ==================== 安全 HTTP 头 ====================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    添加安全 HTTP 头

    包括:
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security
    - Content-Security-Policy
    - Referrer-Policy
    - Permissions-Policy
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 防止 MIME 类型嗅探
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 防止点击劫持
        response.headers["X-Frame-Options"] = "DENY"

        # XSS 保护 (现代浏览器不再需要，但保留兼容性)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 仅在生产环境添加 HSTS
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # 内容安全策略
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' wss: https:; "
            "frame-ancestors 'none';"
        )

        # 引用策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 权限策略
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )

        # 移除敏感服务器信息
        if "Server" in response.headers:
            del response.headers["Server"]

        return response


# ==================== 速率限制 ====================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    请求速率限制

    基于 IP 的滑动窗口限制
    """

    def __init__(
        self,
        app: Any,
        requests_per_minute: int = 100,
        burst_limit: int = 20,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_limit = burst_limit
        self.request_counts: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 检查代理头
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> tuple[bool, int]:
        """检查是否超过限制"""
        now = time.time()
        window_start = now - 60  # 1 分钟窗口

        # 清理过期请求
        self.request_counts[client_ip] = [
            ts for ts in self.request_counts[client_ip]
            if ts > window_start
        ]

        request_count = len(self.request_counts[client_ip])

        # 检查爆发限制 (最近 1 秒)
        recent_count = sum(
            1 for ts in self.request_counts[client_ip]
            if ts > now - 1
        )
        if recent_count >= self.burst_limit:
            return True, self.requests_per_minute - request_count

        # 检查分钟限制
        if request_count >= self.requests_per_minute:
            return True, 0

        return False, self.requests_per_minute - request_count

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 跳过健康检查
        if request.url.path.startswith("/api/v1/health"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        is_limited, remaining = self._is_rate_limited(client_ip)

        if is_limited:
            return Response(
                content='{"detail": "Too many requests"}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )

        # 记录请求
        self.request_counts[client_ip].append(time.time())

        response = await call_next(request)

        # 添加限流头
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)

        return response


# ==================== 请求验证 ====================

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    请求验证中间件

    验证:
    - Content-Type
    - Content-Length
    - 敏感参数过滤
    """

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查请求大小
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            return Response(
                content='{"detail": "Request too large"}',
                status_code=413,
                media_type="application/json",
            )

        # 验证 Content-Type (对于 POST/PUT/PATCH)
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not any(ct in content_type for ct in [
                "application/json",
                "multipart/form-data",
                "application/x-www-form-urlencoded",
            ]):
                # 允许空 body 的请求
                if content_length and int(content_length) > 0:
                    return Response(
                        content='{"detail": "Invalid content type"}',
                        status_code=415,
                        media_type="application/json",
                    )

        return await call_next(request)


# ==================== 配置应用安全 ====================

def configure_security(app: FastAPI) -> None:
    """
    配置应用安全中间件

    Args:
        app: FastAPI 应用实例
    """
    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=[
            "X-Correlation-ID",
            "X-Response-Time",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
        ],
    )

    # 生产环境添加额外安全中间件
    if settings.ENVIRONMENT == "production":
        # 安全 HTTP 头
        app.add_middleware(SecurityHeadersMiddleware)

        # 速率限制
        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=100,
            burst_limit=20,
        )

        # 请求验证
        app.add_middleware(RequestValidationMiddleware)


# ==================== 密钥生成工具 ====================

def generate_api_key(length: int = 32) -> str:
    """生成 API 密钥"""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_password(password: str) -> str:
    """哈希密码"""
    import hashlib
    import os
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return salt.hex() + key.hex()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    import hashlib
    salt = bytes.fromhex(hashed[:64])
    stored_key = bytes.fromhex(hashed[64:])
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return key == stored_key
