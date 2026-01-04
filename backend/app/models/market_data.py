"""
市场数据模型

Phase 11 升级:
- StockOHLCV: 股票日线 OHLCV 数据
- StockMinuteBar: 分钟级 K 线数据 (TimescaleDB 超表)
- IntradayFactor: 日内因子数据
- DataSyncLog: 数据同步日志
- MacroData: 宏观经济数据
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    Numeric,
    String,
    Text,
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


# ============ Phase 11: 分钟级数据模型 ============

class StockMinuteBar(Base):
    """
    分钟级 K 线数据

    设计用于 TimescaleDB 超表:
    - 按时间分区
    - 高效压缩存储
    - 支持时间序列查询优化
    """

    __tablename__ = "stock_minute_bar"

    # === 主键 (复合) ===
    symbol: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        comment="股票代码",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="时间戳 (带时区)",
    )
    frequency: Mapped[str] = mapped_column(
        String(10),
        primary_key=True,
        default="1min",
        comment="频率 (1min, 5min, 15min, 30min, 1hour)",
    )

    # === OHLCV ===
    open: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="开盘价",
    )
    high: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="最高价",
    )
    low: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="最低价",
    )
    close: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="收盘价",
    )
    volume: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="成交量",
    )

    # === 扩展字段 ===
    vwap: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="VWAP",
    )
    trade_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="成交笔数",
    )

    # === 日内统计 ===
    day_open: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="当日开盘价",
    )
    day_high: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="当日最高",
    )
    day_low: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="当日最低",
    )
    day_volume: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        comment="当日累计成交量",
    )

    # === 元数据 ===
    pre_market: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否盘前交易",
    )
    after_hours: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否盘后交易",
    )
    source: Mapped[str] = mapped_column(
        String(20),
        default="alpaca",
        comment="数据来源",
    )

    __table_args__ = (
        Index("ix_minute_bar_symbol_time", "symbol", "timestamp"),
        Index("ix_minute_bar_time", "timestamp"),
        {
            "comment": "分钟级K线数据 (TimescaleDB超表)",
            # TimescaleDB 超表创建需要单独执行:
            # SELECT create_hypertable('stock_minute_bar', 'timestamp',
            #        chunk_time_interval => interval '1 day');
        },
    )


class IntradayFactor(Base):
    """
    日内因子数据

    存储实时计算的日内因子值:
    - 相对成交量
    - VWAP偏离
    - 买卖压力
    - 价格动量
    """

    __tablename__ = "intraday_factor"

    # === 主键 ===
    symbol: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        comment="股票代码",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        comment="时间戳",
    )
    factor_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="因子ID",
    )

    # === 因子值 ===
    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="因子值",
    )
    zscore: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="标准化值",
    )
    percentile: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="百分位",
    )

    __table_args__ = (
        Index("ix_intraday_factor_symbol_time", "symbol", "timestamp"),
        Index("ix_intraday_factor_factor_time", "factor_id", "timestamp"),
        {"comment": "日内因子数据 (TimescaleDB超表)"},
    )


class DataSyncLog(Base, UUIDMixin, TimestampMixin):
    """
    数据同步日志

    追踪数据同步状态和历史
    """

    __tablename__ = "data_sync_log"

    # === 同步信息 ===
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="股票代码",
    )
    frequency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="1day",
        comment="数据频率",
    )
    data_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="alpaca",
        comment="数据源",
    )

    # === 时间范围 ===
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="同步起始时间",
    )
    end_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="同步结束时间",
    )

    # === 同步结果 ===
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        comment="状态 (pending, syncing, completed, failed)",
    )
    bars_synced: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="同步的K线数量",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="同步耗时(秒)",
    )

    __table_args__ = (
        Index("ix_sync_log_symbol_freq", "symbol", "frequency"),
        Index("ix_sync_log_status", "status"),
        {"comment": "数据同步日志"},
    )


class DataQualityIssue(Base, UUIDMixin, TimestampMixin):
    """
    数据质量问题记录

    追踪和管理数据质量问题
    """

    __tablename__ = "data_quality_issue"

    # === 问题信息 ===
    symbol: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="股票代码",
    )
    issue_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="问题发生时间",
    )
    issue_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="问题类型 (missing_data, outlier, stale_data, etc.)",
    )
    severity: Mapped[str] = mapped_column(
        String(10),
        default="medium",
        comment="严重程度 (low, medium, high)",
    )

    # === 详情 ===
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="问题描述",
    )
    affected_fields: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="受影响字段 (逗号分隔)",
    )
    expected_value: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="期望值",
    )
    actual_value: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="实际值",
    )

    # === 解决状态 ===
    resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否已解决",
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="解决时间",
    )
    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="解决备注",
    )

    __table_args__ = (
        Index("ix_dq_issue_symbol", "symbol"),
        Index("ix_dq_issue_type", "issue_type"),
        Index("ix_dq_issue_resolved", "resolved"),
        {"comment": "数据质量问题记录"},
    )
