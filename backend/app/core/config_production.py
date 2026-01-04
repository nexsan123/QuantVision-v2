"""
Phase 14: \u751f\u4ea7\u90e8\u7f72 - \u751f\u4ea7\u73af\u5883\u914d\u7f6e

\u751f\u4ea7\u73af\u5883\u4e13\u7528\u914d\u7f6e\uff0c\u8986\u76d6\u9ed8\u8ba4\u914d\u7f6e
"""

from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProductionSettings(BaseSettings):
    """
    \u751f\u4ea7\u73af\u5883\u914d\u7f6e

    \u4ece\u73af\u5883\u53d8\u91cf\u548c AWS Secrets Manager \u52a0\u8f7d
    """

    model_config = SettingsConfigDict(
        env_file=".env.production",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ============ \u57fa\u7840\u914d\u7f6e ============
    APP_NAME: str = "QuantVision"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # ============ \u5b89\u5168\u914d\u7f6e ============
    SECRET_KEY: str  # \u5fc5\u987b\u4ece\u73af\u5883\u53d8\u91cf\u83b7\u53d6
    JWT_SECRET_KEY: str  # \u5fc5\u987b\u4ece\u73af\u5883\u53d8\u91cf\u83b7\u53d6
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    # API Key \u52a0\u5bc6
    API_KEY_ENCRYPTION_KEY: str = ""  # \u7528\u4e8e\u52a0\u5bc6\u5b58\u50a8\u7684 API Key

    # \u7ba1\u7406\u5458 IP \u767d\u540d\u5355
    ADMIN_IP_WHITELIST: list[str] = []

    # ============ \u6570\u636e\u5e93\u914d\u7f6e ============
    DATABASE_URL: str  # \u5fc5\u987b\u4ece\u73af\u5883\u53d8\u91cf\u83b7\u53d6
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_ECHO: bool = False

    # ============ Redis \u914d\u7f6e ============
    REDIS_URL: str  # \u5fc5\u987b\u4ece\u73af\u5883\u53d8\u91cf\u83b7\u53d6
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5

    # ============ \u65e5\u5fd7\u914d\u7f6e ============
    LOG_LEVEL: str = "WARNING"
    LOG_FORMAT: str = "json"
    LOG_FILE: str = "/app/logs/quantvision.log"
    LOG_MAX_SIZE: int = 104857600  # 100MB
    LOG_BACKUP_COUNT: int = 10

    # ============ CORS \u914d\u7f6e ============
    CORS_ORIGINS: list[str] = [
        "https://quantvision.io",
        "https://www.quantvision.io",
        "https://app.quantvision.io",
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # ============ \u9650\u6d41\u914d\u7f6e ============
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_BURST: int = 10

    # ============ \u5238\u5546 API ============
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    ALPACA_BASE_URL: str = "https://api.alpaca.markets"
    ALPACA_PAPER_TRADING: bool = False  # \u751f\u4ea7\u73af\u5883\u9ed8\u8ba4\u5173\u95ed Paper Trading

    # ============ \u5916\u90e8\u670d\u52a1 ============
    POLYGON_API_KEY: str = ""
    FRED_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # ============ Sentry (\u9519\u8bef\u8ddf\u8e2a) ============
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1

    # ============ \u90ae\u4ef6/\u901a\u77e5 ============
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@quantvision.io"

    SLACK_WEBHOOK_URL: str = ""
    PAGERDUTY_SERVICE_KEY: str = ""

    # ============ AWS ============
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "quantvision-production"

    # ============ \u7f13\u5b58\u914d\u7f6e ============
    CACHE_TTL_DEFAULT: int = 300  # 5\u5206\u949f
    CACHE_TTL_MARKET_DATA: int = 60  # 1\u5206\u949f
    CACHE_TTL_FACTOR_DATA: int = 3600  # 1\u5c0f\u65f6
    CACHE_TTL_BACKTEST: int = 86400  # 24\u5c0f\u65f6

    # ============ \u56de\u6d4b\u914d\u7f6e ============
    BACKTEST_MAX_CONCURRENT: int = 10
    BACKTEST_TIMEOUT_SECONDS: int = 3600
    BACKTEST_MAX_SYMBOLS: int = 500

    # ============ \u4ea4\u6613\u914d\u7f6e ============
    TRADING_MAX_POSITION_SIZE: float = 0.05  # 5%
    TRADING_MAX_ORDER_VALUE: float = 100000
    TRADING_REQUIRE_2FA: bool = True
    TRADING_IP_WHITELIST: list[str] = []

    # ============ \u5b9a\u65f6\u4efb\u52a1 ============
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_TIMEZONE: str = "America/New_York"

    # ============ \u5065\u5eb7\u68c0\u67e5 ============
    HEALTH_CHECK_INTERVAL: int = 30
    HEALTH_CHECK_TIMEOUT: int = 10

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("ADMIN_IP_WHITELIST", mode="before")
    @classmethod
    def parse_ip_whitelist(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if not v:
                return []
            return [ip.strip() for ip in v.split(",")]
        return v

    @field_validator("TRADING_IP_WHITELIST", mode="before")
    @classmethod
    def parse_trading_ip_whitelist(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if not v:
                return []
            return [ip.strip() for ip in v.split(",")]
        return v


class StagingSettings(ProductionSettings):
    """
    \u6d4b\u8bd5\u73af\u5883\u914d\u7f6e

    \u7ee7\u627f\u751f\u4ea7\u914d\u7f6e\uff0c\u4f46\u653e\u5bbd\u90e8\u5206\u9650\u5236
    """

    model_config = SettingsConfigDict(
        env_file=".env.staging",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "staging"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # \u653e\u5bbd\u9650\u6d41
    RATE_LIMIT_PER_MINUTE: int = 200
    RATE_LIMIT_PER_HOUR: int = 5000

    # \u5141\u8bb8 Paper Trading
    ALPACA_PAPER_TRADING: bool = True
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"

    # \u653e\u5bbd\u4ea4\u6613\u9650\u5236
    TRADING_REQUIRE_2FA: bool = False

    # Sentry \u91c7\u6837\u7387\u63d0\u9ad8
    SENTRY_TRACES_SAMPLE_RATE: float = 0.5
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.5


def get_settings():
    """
    \u6839\u636e\u73af\u5883\u53d8\u91cf\u83b7\u53d6\u914d\u7f6e

    ENVIRONMENT=production -> ProductionSettings
    ENVIRONMENT=staging -> StagingSettings
    """
    import os

    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return ProductionSettings()
    elif env == "staging":
        return StagingSettings()
    else:
        # \u5f00\u53d1\u73af\u5883\u4f7f\u7528\u9ed8\u8ba4\u914d\u7f6e
        from app.core.config import settings
        return settings
