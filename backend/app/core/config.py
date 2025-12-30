"""
应用配置模块

使用 pydantic-settings 管理环境变量，支持 .env 文件加载。
所有敏感配置通过环境变量注入，不硬编码在代码中。
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    应用全局配置

    配置优先级: 环境变量 > .env 文件 > 默认值
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # === 应用基础配置 ===
    APP_NAME: str = "QuantVision"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # === API 配置 ===
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # === 数据库配置 ===
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "quantvision"

    @property
    def DATABASE_URL(self) -> str:
        """构建 PostgreSQL 连接 URL (异步驱动)"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """构建 PostgreSQL 连接 URL (同步驱动，用于 Alembic)"""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # === Redis 配置 ===
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @property
    def REDIS_URL(self) -> str:
        """构建 Redis 连接 URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # === Celery 配置 ===
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    @property
    def celery_broker(self) -> str:
        """Celery Broker URL，默认使用 Redis"""
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        """Celery Result Backend URL，默认使用 Redis"""
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    # === 数据源配置 ===
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"
    ALPACA_DATA_URL: str = "https://data.alpaca.markets"

    # === 回测配置 ===
    BACKTEST_DEFAULT_CAPITAL: float = 1_000_000.0
    BACKTEST_DEFAULT_COMMISSION: float = 0.001  # 0.1%
    BACKTEST_DEFAULT_SLIPPAGE: float = 0.001    # 0.1%
    BACKTEST_MAX_YEARS: int = 20

    # === 因子配置 ===
    FACTOR_CACHE_TTL: int = 3600  # 因子缓存过期时间（秒）
    FACTOR_MAX_LOOKBACK: int = 252  # 最大回望期（交易日）

    # === 日志配置 ===
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "console"


@lru_cache
def get_settings() -> Settings:
    """
    获取配置单例

    使用 lru_cache 确保整个应用生命周期内只创建一个配置实例
    """
    return Settings()


# 全局配置实例
settings = get_settings()
