"""
股票池模型

提供:
- Universe: 股票池定义
- UniverseSnapshot: 股票池历史快照 (支持 PIT)
"""

from datetime import date
from enum import Enum

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UniverseType(str, Enum):
    """股票池类型"""
    INDEX = "index"           # 指数成分股 (如 SPY, QQQ)
    SECTOR = "sector"         # 行业股票池
    CUSTOM = "custom"         # 自定义股票池
    SCREEN = "screen"         # 筛选规则生成


class Universe(Base, UUIDMixin, TimestampMixin):
    """
    股票池定义

    存储股票池的基本信息和筛选规则
    """

    __tablename__ = "universes"

    # === 基本信息 ===
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="股票池名称",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="描述",
    )
    universe_type: Mapped[UniverseType] = mapped_column(
        default=UniverseType.CUSTOM,
        comment="股票池类型",
    )

    # === 配置 ===
    base_index: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="基准指数 (如 SPY, QQQ)",
    )
    filter_rules: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="筛选规则 (JSON 格式)",
    )
    is_active: Mapped[bool] = mapped_column(
        default=True,
        comment="是否启用",
    )

    # === 关系 ===
    snapshots: Mapped[list["UniverseSnapshot"]] = relationship(
        "UniverseSnapshot",
        back_populates="universe",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        {"comment": "股票池定义"},
    )


class UniverseSnapshot(Base, UUIDMixin, TimestampMixin):
    """
    股票池快照

    记录股票池在特定日期的成分股列表，支持:
    - 历史成分股查询
    - Point-in-Time 回测
    - 成分股变动追踪
    """

    __tablename__ = "universe_snapshots"

    # === 关联 ===
    universe_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("universes.id", ondelete="CASCADE"),
        nullable=False,
        comment="股票池 ID",
    )

    # === 快照信息 ===
    snapshot_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="快照日期",
    )
    symbols: Mapped[list[str]] = mapped_column(
        ARRAY(String(20)),
        nullable=False,
        comment="成分股列表",
    )
    count: Mapped[int] = mapped_column(
        nullable=False,
        comment="成分股数量",
    )

    # === 变动信息 ===
    added_symbols: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(20)),
        nullable=True,
        comment="新增成分股",
    )
    removed_symbols: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(20)),
        nullable=True,
        comment="移除成分股",
    )

    # === 关系 ===
    universe: Mapped["Universe"] = relationship(
        "Universe",
        back_populates="snapshots",
    )

    __table_args__ = (
        UniqueConstraint("universe_id", "snapshot_date", name="uq_universe_snapshot"),
        Index("ix_universe_snapshot_date", "universe_id", "snapshot_date"),
        {"comment": "股票池历史快照"},
    )
