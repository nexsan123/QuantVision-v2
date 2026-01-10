"""
审计日志模型

机构级合规要求:
- 不可篡改的交易记录
- 操作追踪
- 时间戳签名
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Index, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDMixin


class AuditActionType(str, Enum):
    """审计操作类型"""
    # 策略相关
    STRATEGY_CREATE = "strategy.create"
    STRATEGY_UPDATE = "strategy.update"
    STRATEGY_DELETE = "strategy.delete"
    STRATEGY_DEPLOY = "strategy.deploy"

    # 交易相关
    ORDER_SUBMIT = "order.submit"
    ORDER_CANCEL = "order.cancel"
    ORDER_FILL = "order.fill"
    ORDER_REJECT = "order.reject"

    # 部署相关
    DEPLOYMENT_START = "deployment.start"
    DEPLOYMENT_STOP = "deployment.stop"
    DEPLOYMENT_PAUSE = "deployment.pause"

    # 风险相关
    CIRCUIT_BREAKER_TRIGGER = "risk.circuit_breaker.trigger"
    CIRCUIT_BREAKER_RESET = "risk.circuit_breaker.reset"
    RISK_LIMIT_BREACH = "risk.limit.breach"

    # 系统相关
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    CONFIG_CHANGE = "config.change"

    # 数据相关
    DATA_IMPORT = "data.import"
    DATA_EXPORT = "data.export"


class AuditLog(Base, UUIDMixin):
    """
    审计日志表

    设计原则:
    - 只能插入，不能更新或删除 (append-only)
    - 包含完整的操作上下文
    - 支持高效查询
    """

    __tablename__ = "audit_logs"

    # === 操作信息 ===
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="操作类型",
    )

    # === 操作者信息 ===
    user_id: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="操作用户ID",
    )
    user_name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="操作用户名",
    )
    ip_address: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        comment="客户端IP地址",
    )
    user_agent: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment="客户端User-Agent",
    )

    # === 资源信息 ===
    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="资源类型 (strategy/order/deployment等)",
    )
    resource_id: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="资源ID",
    )

    # === 操作详情 ===
    old_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="变更前的值 (JSON)",
    )
    new_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="变更后的值 (JSON)",
    )
    extra_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="附加元数据 (JSON)",
    )

    # === 结果信息 ===
    status: Mapped[str] = mapped_column(
        String(20),
        default="success",
        nullable=False,
        comment="操作状态 (success/failure/pending)",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息 (如果失败)",
    )

    # === 时间戳 ===
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="记录创建时间",
    )

    # === 索引 ===
    __table_args__ = (
        Index("ix_audit_logs_action_created", "action", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        {"comment": "审计日志表 - 不可篡改的操作记录"},
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id} at {self.created_at}>"


# === 审计日志服务函数 ===

async def log_audit_event(
    db_session,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    user_id: str = None,
    user_name: str = None,
    old_value: dict = None,
    new_value: dict = None,
    extra_data: dict = None,
    status: str = "success",
    error_message: str = None,
    ip_address: str = None,
    user_agent: str = None,
) -> AuditLog:
    """
    记录审计日志

    用法:
        await log_audit_event(
            db_session,
            action=AuditActionType.ORDER_SUBMIT,
            resource_type="order",
            resource_id="ord-123",
            user_id="user-001",
            new_value={"symbol": "AAPL", "qty": 100},
        )
    """
    log_entry = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        user_name=user_name,
        old_value=old_value,
        new_value=new_value,
        extra_data=extra_data,
        status=status,
        error_message=error_message,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db_session.add(log_entry)
    await db_session.commit()
    await db_session.refresh(log_entry)

    return log_entry
