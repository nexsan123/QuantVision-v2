"""
模型基类与 Mixin

提供通用的模型功能:
- UUID 主键
- 时间戳字段
- 软删除支持
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class UUIDMixin:
    """
    UUID 主键 Mixin

    使用 UUID 作为主键，确保分布式环境下的唯一性
    """

    @declared_attr
    def id(cls) -> Mapped[str]:
        return mapped_column(
            UUID(as_uuid=False),
            primary_key=True,
            default=lambda: str(uuid4()),
            comment="主键 UUID",
        )


class TimestampMixin:
    """
    时间戳 Mixin

    自动记录创建时间和更新时间
    """

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
            comment="创建时间",
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
            comment="更新时间",
        )


class SoftDeleteMixin:
    """
    软删除 Mixin

    标记删除而非物理删除，保留数据完整性
    """

    @declared_attr
    def is_deleted(cls) -> Mapped[bool]:
        return mapped_column(
            default=False,
            nullable=False,
            comment="是否已删除",
        )

    @declared_attr
    def deleted_at(cls) -> Mapped[datetime | None]:
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="删除时间",
        )
