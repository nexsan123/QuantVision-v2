"""
配置验证模块
Sprint 14: T37 - 环境配置管理

提供:
- 生产环境配置验证
- 密钥强度检查
- 必需配置检查
"""

import os
import secrets
import string
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ==================== 配置验证 ====================

class ConfigValidationError(Exception):
    """配置验证错误"""
    pass


def validate_production_config() -> list[str]:
    """
    验证生产环境配置

    Returns:
        list[str]: 警告消息列表
    """
    warnings: list[str] = []
    environment = os.getenv("ENVIRONMENT", "development")

    if environment != "production":
        return warnings

    # 检查必需的生产配置
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "APP_SECRET_KEY",
        "JWT_SECRET_KEY",
    ]

    for var in required_vars:
        if not os.getenv(var):
            warnings.append(f"[CRITICAL] 缺少必需配置: {var}")

    # 检查 DEBUG 模式
    if os.getenv("DEBUG", "").lower() == "true":
        warnings.append("[CRITICAL] 生产环境不应开启 DEBUG 模式")

    # 检查密钥强度
    app_secret = os.getenv("APP_SECRET_KEY", "")
    if len(app_secret) < 32:
        warnings.append("[WARNING] APP_SECRET_KEY 长度不足 (建议 >= 32 字符)")

    jwt_secret = os.getenv("JWT_SECRET_KEY", "")
    if len(jwt_secret) < 32:
        warnings.append("[WARNING] JWT_SECRET_KEY 长度不足 (建议 >= 32 字符)")

    # 检查默认密码
    db_password = os.getenv("DB_PASSWORD", "")
    if db_password in ["postgres", "quantvision123", "password", ""]:
        warnings.append("[CRITICAL] 数据库使用了默认/弱密码")

    # 检查 CORS
    cors_origins = os.getenv("CORS_ORIGINS", "")
    if "*" in cors_origins:
        warnings.append("[WARNING] CORS 允许所有来源 (不安全)")

    # 检查日志格式
    log_format = os.getenv("LOG_FORMAT", "console")
    if log_format != "json":
        warnings.append("[INFO] 生产环境建议使用 JSON 日志格式")

    # 记录验证结果
    if warnings:
        logger.warning(
            "production_config_validation",
            warnings=warnings,
            warning_count=len(warnings),
        )
    else:
        logger.info("production_config_validation", status="passed")

    return warnings


def generate_secret_key(length: int = 64) -> str:
    """
    生成安全的随机密钥

    Args:
        length: 密钥长度

    Returns:
        str: 随机密钥
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def check_environment_completeness() -> dict[str, Any]:
    """
    检查环境配置完整性

    Returns:
        dict: 配置状态
    """
    config_groups = {
        "database": {
            "required": ["DATABASE_URL"],
            "optional": ["DB_POOL_SIZE", "DB_MAX_OVERFLOW"],
        },
        "redis": {
            "required": ["REDIS_URL"],
            "optional": ["REDIS_PASSWORD"],
        },
        "alpaca": {
            "required": ["ALPACA_API_KEY", "ALPACA_SECRET_KEY"],
            "optional": ["ALPACA_BASE_URL"],
        },
        "security": {
            "required": ["APP_SECRET_KEY", "JWT_SECRET_KEY"],
            "optional": ["CORS_ORIGINS"],
        },
        "s3": {
            "required": [],
            "optional": ["S3_ENDPOINT", "S3_ACCESS_KEY", "S3_SECRET_KEY", "S3_BUCKET"],
        },
        "monitoring": {
            "required": [],
            "optional": ["SENTRY_DSN", "LOG_LEVEL", "LOG_FORMAT"],
        },
    }

    result: dict[str, Any] = {
        "complete": True,
        "groups": {},
    }

    for group_name, vars_config in config_groups.items():
        group_status = {
            "required_present": [],
            "required_missing": [],
            "optional_present": [],
            "optional_missing": [],
        }

        for var in vars_config["required"]:
            if os.getenv(var):
                group_status["required_present"].append(var)
            else:
                group_status["required_missing"].append(var)
                result["complete"] = False

        for var in vars_config["optional"]:
            if os.getenv(var):
                group_status["optional_present"].append(var)
            else:
                group_status["optional_missing"].append(var)

        result["groups"][group_name] = group_status

    return result


# ==================== 启动检查 ====================

def run_startup_checks() -> None:
    """
    运行启动时配置检查
    """
    environment = os.getenv("ENVIRONMENT", "development")

    logger.info(
        "startup_check_started",
        environment=environment,
    )

    # 生产环境验证
    if environment == "production":
        warnings = validate_production_config()
        critical_warnings = [w for w in warnings if "[CRITICAL]" in w]

        if critical_warnings:
            logger.error(
                "startup_check_failed",
                critical_issues=len(critical_warnings),
            )
            raise ConfigValidationError(
                f"生产环境配置验证失败: {len(critical_warnings)} 个严重问题"
            )

    # 配置完整性检查
    completeness = check_environment_completeness()

    if not completeness["complete"]:
        missing_required = []
        for group, status in completeness["groups"].items():
            missing_required.extend(status["required_missing"])

        logger.warning(
            "config_incomplete",
            missing_vars=missing_required,
        )

    logger.info("startup_check_completed")
