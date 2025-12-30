"""
市场数据模型

包含:
- StockOHLCV: 股票日线 OHLCV 数据
- MacroData: 宏观经济数据
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class StockOHLCV(Base, UUIDMixin, TimestampMixin):
    """
    股票日线 OHLCV 数据

    存储每日股票行情数据，支持:
    - 复权价格 (adj_*)
    - 成交量/成交额
    - VWAP (成交量加权平均价)
    """

    __tablename__ = "stock_ohlcv"

    # === 标识字段 ===
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="股票代码 (如 AAPL, MSFT)",
    )
    trade_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="交易日期",
    )

    # === 原始价格 ===
    open: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        comment="开盘价",
    )
    high: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        comment="最高价",
    )
    low: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        comment="最低价",
    )
    close: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        comment="收盘价",
    )
    volume: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="成交量",
    )

    # === 复权价格 ===
    adj_open: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
        comment="复权开盘价",
    )
    adj_high: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
        comment="复权最高价",
    )
    adj_low: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
        comment="复权最低价",
    )
    adj_close: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
        comment="复权收盘价",
    )

    # === 衍生指标 ===
    vwap: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4),
        nullable=True,
        comment="成交量加权平均价",
    )
    turnover: Mapped[Decimal | None] = mapped_column(
        Numeric(22, 2),
        nullable=True,
        comment="成交额",
    )
    trade_count: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="成交笔数",
    )

    # === 数据来源 ===
    source: Mapped[str] = mapped_column(
        String(50),
        default="alpaca",
        comment="数据来源 (alpaca, yfinance, polygon)",
    )

    __table_args__ = (
        UniqueConstraint("symbol", "trade_date", name="uq_stock_ohlcv_symbol_date"),
        Index("ix_stock_ohlcv_symbol_date", "symbol", "trade_date"),
        Index("ix_stock_ohlcv_date", "trade_date"),
        {"comment": "股票日线 OHLCV 数据"},
    )


class MacroData(Base, UUIDMixin, TimestampMixin):
    """
    宏观经济数据

    存储 FRED 等数据源的宏观经济指标:
    - GDP, CPI, 失业率等
    - 利率曲线
    - 市场情绪指标
    """

    __tablename__ = "macro_data"

    # === 标识字段 ===
    indicator: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="指标代码 (如 GDP, CPI, UNRATE)",
    )
    report_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="报告日期 (数据所属日期)",
    )
    release_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="发布日期 (数据公开日期，用于 PIT)",
    )

    # === 数据值 ===
    value: Mapped[Decimal] = mapped_column(
        Numeric(22, 6),
        nullable=False,
        comment="指标值",
    )

    # === 元信息 ===
    unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="单位 (%, billions, index)",
    )
    frequency: Mapped[str] = mapped_column(
        String(20),
        default="monthly",
        comment="频率 (daily, weekly, monthly, quarterly)",
    )
    source: Mapped[str] = mapped_column(
        String(50),
        default="fred",
        comment="数据来源",
    )
    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="指标描述",
    )

    __table_args__ = (
        UniqueConstraint(
            "indicator", "report_date", "release_date",
            name="uq_macro_data_indicator_dates"
        ),
        Index("ix_macro_data_indicator_release", "indicator", "release_date"),
        {"comment": "宏观经济数据 (支持 PIT)"},
    )
