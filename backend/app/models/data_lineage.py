"""
数据血缘模型

追踪数据的来源和处理过程:
- 数据获取记录
- 数据处理流水
- 质量检测结果
"""

from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class DataSourceType(str, Enum):
    """数据源类型"""
    ALPACA = "alpaca"
    YFINANCE = "yfinance"
    POLYGON = "polygon"
    FRED = "fred"
    MANUAL = "manual"


class DataStatus(str, Enum):
    """数据状态"""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    PENDING = "pending"


class DataLineage(Base, UUIDMixin, TimestampMixin):
    """
    数据血缘记录

    记录每次数据获取和处理的详细信息:
    - 来源和时间
    - 处理结果
    - 质量指标
    """

    __tablename__ = "data_lineage"

    # === 任务标识 ===
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="任务类型 (fetch_ohlcv, fetch_financials, etc.)",
    )
    task_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Celery 任务 ID",
    )

    # === 数据范围 ===
    source: Mapped[DataSourceType] = mapped_column(
        default=DataSourceType.ALPACA,
        comment="数据来源",
    )
    symbols: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="处理的股票列表",
    )
    start_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="数据起始日期",
    )
    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
        comment="数据结束日期",
    )

    # === 执行结果 ===
    status: Mapped[DataStatus] = mapped_column(
        default=DataStatus.PENDING,
        index=True,
        comment="执行状态",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="开始时间",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="完成时间",
    )
    duration_seconds: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="执行时长（秒）",
    )

    # === 统计信息 ===
    records_fetched: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="获取记录数",
    )
    records_inserted: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="插入记录数",
    )
    records_updated: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="更新记录数",
    )
    records_failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="失败记录数",
    )

    # === 质量指标 ===
    quality_score: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="数据质量评分 (0-100)",
    )
    missing_rate: Mapped[float | None] = mapped_column(
        nullable=True,
        comment="缺失率",
    )
    anomaly_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="异常值数量",
    )

    # === 详细信息 ===
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息",
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
        comment="附加元数据",
    )

    __table_args__ = (
        Index("ix_lineage_task_status", "task_type", "status"),
        Index("ix_lineage_created", "created_at"),
        {"comment": "数据血缘记录"},
    )

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.records_fetched or 0
        failed = self.records_failed or 0
        if total == 0:
            return 0.0
        return (total - failed) / total * 100
