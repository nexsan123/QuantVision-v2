"""
策略V2模型

提供:
- StrategyV2: 7步策略构建器的数据库模型
- StrategyStatusEnum: 策略状态枚举
"""

from enum import Enum
from typing import Any

from sqlalchemy import Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDMixin


class StrategyStatusEnum(str, Enum):
    """策略状态枚举"""
    DRAFT = "draft"          # 草稿状态，可编辑
    BACKTEST = "backtest"    # 回测中
    PAPER = "paper"          # 模拟交易中
    LIVE = "live"            # 实盘交易中
    PAUSED = "paused"        # 已暂停
    ARCHIVED = "archived"    # 已归档


class StrategyV2(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    策略V2模型

    存储7步策略构建器生成的策略配置:
    - Step 1: 投资池 (Universe)
    - Step 2: 因子层 (Alpha)
    - Step 3: 信号层 (Signal)
    - Step 4: 风险层 (Risk)
    - Step 5: 组合层 (Portfolio)
    - Step 6: 执行层 (Execution)
    - Step 7: 监控层 (Monitor)
    """

    __tablename__ = "strategies_v2"

    # === 基本信息 ===
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="策略名称",
    )
    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
        comment="策略描述",
    )
    status: Mapped[StrategyStatusEnum] = mapped_column(
        default=StrategyStatusEnum.DRAFT,
        nullable=False,
        comment="策略状态",
    )

    # === 7步配置 (JSON格式存储) ===
    universe_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Step 1: 投资池配置",
    )
    alpha_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Step 2: 因子层配置",
    )
    signal_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Step 3: 信号层配置",
    )
    risk_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Step 4: 风险层配置",
    )
    portfolio_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Step 5: 组合层配置",
    )
    execution_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Step 6: 执行层配置",
    )
    monitor_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Step 7: 监控层配置",
    )

    # === 元数据 ===
    version: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
        comment="策略版本号",
    )
    tags: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="策略标签",
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="父策略ID (克隆来源)",
    )

    __table_args__ = (
        Index("ix_strategies_v2_name", "name"),
        Index("ix_strategies_v2_status", "status"),
        Index("ix_strategies_v2_created_at", "created_at"),
        {"comment": "策略V2 - 7步策略构建器"},
    )

    def __repr__(self) -> str:
        return f"<StrategyV2(id={self.id}, name='{self.name}', status={self.status.value})>"
