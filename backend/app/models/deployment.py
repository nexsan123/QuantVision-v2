"""
部署数据模型

存储策略部署实例的配置和运行状态
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime,
    Enum as SQLEnum, JSON, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin, SoftDeleteMixin


class DeploymentStatusEnum(str, Enum):
    """部署状态"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class DeploymentEnvironmentEnum(str, Enum):
    """部署环境"""
    PAPER = "paper"
    LIVE = "live"


class StrategyTypeEnum(str, Enum):
    """策略类型"""
    LONG_TERM = "long_term"
    MEDIUM_TERM = "medium_term"
    SHORT_TERM = "short_term"
    INTRADAY = "intraday"


class Deployment(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """策略部署模型"""

    __tablename__ = "deployments"

    # 基本信息
    strategy_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    strategy_name: Mapped[str] = mapped_column(String(200), nullable=False)
    deployment_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # 状态
    environment: Mapped[DeploymentEnvironmentEnum] = mapped_column(
        SQLEnum(DeploymentEnvironmentEnum),
        default=DeploymentEnvironmentEnum.PAPER,
        nullable=False
    )
    status: Mapped[DeploymentStatusEnum] = mapped_column(
        SQLEnum(DeploymentStatusEnum),
        default=DeploymentStatusEnum.DRAFT,
        nullable=False
    )
    strategy_type: Mapped[StrategyTypeEnum] = mapped_column(
        SQLEnum(StrategyTypeEnum),
        default=StrategyTypeEnum.MEDIUM_TERM,
        nullable=False
    )

    # 配置 (JSON)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    # 运行时指标
    current_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    current_pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)

    # 时间戳
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 关系
    trades = relationship("IntradayTrade", back_populates="deployment", lazy="dynamic")

    __table_args__ = (
        Index("ix_deployments_strategy_status", "strategy_id", "status"),
        Index("ix_deployments_environment", "environment"),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "deployment_id": self.id,
            "strategy_id": self.strategy_id,
            "strategy_name": self.strategy_name,
            "deployment_name": self.deployment_name,
            "environment": self.environment.value,
            "status": self.status.value,
            "strategy_type": self.strategy_type.value,
            "config": self.config,
            "current_pnl": self.current_pnl,
            "current_pnl_pct": self.current_pnl_pct,
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class IntradayTrade(Base, UUIDMixin, TimestampMixin):
    """日内交易记录模型"""

    __tablename__ = "intraday_trades"

    # 关联
    deployment_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("deployments.id"),
        nullable=True,
        index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # 交易信息
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # buy/sell
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), default="market")  # market/limit

    # 风控参数
    stop_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    take_profit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 状态
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    exit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exit_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 盈亏
    pnl: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pnl_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Alpaca订单信息
    alpaca_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    alpaca_fill_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 关系
    deployment = relationship("Deployment", back_populates="trades")

    __table_args__ = (
        Index("ix_intraday_trades_user_symbol", "user_id", "symbol"),
        Index("ix_intraday_trades_date", "created_at"),
    )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "deployment_id": self.deployment_id,
            "user_id": self.user_id,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "order_type": self.order_type,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "is_open": self.is_open,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
            "alpaca_order_id": self.alpaca_order_id,
            "time": self.created_at.isoformat() if self.created_at else None,
        }


class PDTStatus(Base, UUIDMixin, TimestampMixin):
    """PDT规则状态模型"""

    __tablename__ = "pdt_status"

    user_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)

    # 账户信息
    account_equity: Mapped[float] = mapped_column(Float, default=0.0)
    is_pdt_account: Mapped[bool] = mapped_column(Boolean, default=False)  # 账户是否标记为PDT

    # 交易计数
    day_trades_count: Mapped[int] = mapped_column(Integer, default=0)  # 5个交易日内的日内交易次数
    remaining_day_trades: Mapped[int] = mapped_column(Integer, default=3)

    # 重置时间
    reset_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 警告状态
    is_warning: Mapped[bool] = mapped_column(Boolean, default=False)

    # 最后同步时间
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "account_equity": self.account_equity,
            "is_pdt_account": self.is_pdt_account,
            "day_trades_count": self.day_trades_count,
            "remaining_day_trades": self.remaining_day_trades,
            "reset_date": self.reset_date.isoformat() if self.reset_date else None,
            "is_warning": self.is_warning,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
        }
