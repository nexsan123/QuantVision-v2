"""
用户模型

机构级用户管理:
- 用户认证
- 角色权限 (RBAC)
- 会话管理
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, DateTime, String, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"           # 管理员 - 完全访问
    TRADER = "trader"         # 交易员 - 交易和策略
    ANALYST = "analyst"       # 分析师 - 只读分析
    VIEWER = "viewer"         # 观察者 - 只读


class UserStatus(str, Enum):
    """用户状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base, UUIDMixin, TimestampMixin):
    """
    用户表

    机构级用户管理，支持:
    - 多角色权限
    - 登录追踪
    - 会话管理
    """

    __tablename__ = "users"

    # === 基本信息 ===
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="邮箱 (唯一)",
    )
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="用户名 (唯一)",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="哈希密码",
    )

    # === 个人信息 ===
    full_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="全名",
    )
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="电话",
    )

    # === 角色与权限 ===
    role: Mapped[str] = mapped_column(
        String(20),
        default=UserRole.VIEWER.value,
        nullable=False,
        index=True,
        comment="用户角色",
    )
    permissions: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="自定义权限 (覆盖角色默认)",
    )

    # === 状态 ===
    status: Mapped[str] = mapped_column(
        String(20),
        default=UserStatus.ACTIVE.value,
        nullable=False,
        index=True,
        comment="用户状态",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否超级用户",
    )

    # === 登录追踪 ===
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="最后登录时间",
    )
    last_login_ip: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="最后登录IP",
    )
    login_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="登录次数",
    )
    failed_login_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="失败登录次数",
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="锁定截止时间",
    )

    # === 索引 ===
    __table_args__ = (
        Index("ix_users_role_status", "role", "status"),
        {"comment": "用户表 - 机构级用户管理"},
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"

    @property
    def is_active(self) -> bool:
        """是否活跃"""
        return self.status == UserStatus.ACTIVE.value

    @property
    def is_locked(self) -> bool:
        """是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until


# === 角色权限矩阵 ===
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "users": ["create", "read", "update", "delete"],
        "strategies": ["create", "read", "update", "delete", "deploy"],
        "trading": ["submit", "cancel", "view"],
        "reports": ["create", "read", "export"],
        "settings": ["read", "update"],
        "audit": ["read"],
    },
    UserRole.TRADER: {
        "users": [],
        "strategies": ["create", "read", "update", "deploy"],
        "trading": ["submit", "cancel", "view"],
        "reports": ["read", "export"],
        "settings": ["read"],
        "audit": [],
    },
    UserRole.ANALYST: {
        "users": [],
        "strategies": ["read"],
        "trading": ["view"],
        "reports": ["read", "export"],
        "settings": ["read"],
        "audit": [],
    },
    UserRole.VIEWER: {
        "users": [],
        "strategies": ["read"],
        "trading": ["view"],
        "reports": ["read"],
        "settings": [],
        "audit": [],
    },
}


def check_permission(user: User, resource: str, action: str) -> bool:
    """
    检查用户权限

    Args:
        user: 用户对象
        resource: 资源类型 (users/strategies/trading/reports/settings/audit)
        action: 操作类型 (create/read/update/delete/deploy/submit/cancel/view/export)

    Returns:
        是否有权限
    """
    # 超级用户拥有所有权限
    if user.is_superuser:
        return True

    # 获取角色权限
    role = UserRole(user.role)
    role_perms = ROLE_PERMISSIONS.get(role, {})

    # 检查资源权限
    resource_perms = role_perms.get(resource, [])
    if action in resource_perms:
        return True

    # 检查自定义权限覆盖
    if user.permissions:
        custom_perms = user.permissions.get(resource, [])
        if action in custom_perms:
            return True

    return False
