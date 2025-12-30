"""
因子缓存数据模型

包含因子定义、因子值缓存、分析结果缓存三个核心表
支持增量计算和版本控制
"""

import hashlib
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class FactorDefinition(Base, UUIDMixin, TimestampMixin):
    """
    因子定义表

    存储因子的元信息和代码哈希，用于版本控制
    """

    __tablename__ = "factor_definitions"

    # 基本信息
    name = Column(String(100), nullable=False, unique=True, comment="因子名称")
    display_name = Column(String(200), comment="显示名称")
    description = Column(Text, comment="因子描述")
    category = Column(String(50), comment="因子类别: momentum/value/quality/volatility/liquidity")

    # 因子表达式
    expression = Column(Text, nullable=False, comment="因子表达式/代码")
    code_hash = Column(String(64), nullable=False, comment="表达式 SHA256 哈希")

    # 计算参数
    lookback_period = Column(Integer, default=252, comment="回望周期 (天)")
    frequency = Column(String(20), default="daily", comment="计算频率: daily/weekly/monthly")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    last_computed_at = Column(DateTime, comment="最后计算时间")
    last_computed_date = Column(String(10), comment="最后计算日期 YYYY-MM-DD")

    # 版本控制
    version = Column(Integer, default=1, comment="版本号")

    # 关系
    factor_values = relationship("FactorValue", back_populates="factor_definition")
    analysis_cache = relationship("FactorAnalysisCache", back_populates="factor_definition")

    # 索引
    __table_args__ = (
        Index("ix_factor_definitions_code_hash", "code_hash"),
        Index("ix_factor_definitions_category", "category"),
    )

    @classmethod
    def compute_code_hash(cls, expression: str) -> str:
        """计算表达式的 SHA256 哈希"""
        # 标准化表达式 (去除空白)
        normalized = "".join(expression.split())
        return hashlib.sha256(normalized.encode()).hexdigest()

    def update_hash(self) -> bool:
        """
        更新代码哈希，返回是否发生变化

        Returns:
            True 如果哈希值变化 (代码有更新)
        """
        new_hash = self.compute_code_hash(self.expression)
        if new_hash != self.code_hash:
            self.code_hash = new_hash
            self.version += 1
            return True
        return False


class FactorValue(Base, UUIDMixin):
    """
    因子值表

    存储计算后的因子值，支持按日期和股票查询
    设计用于 TimescaleDB 时序优化
    """

    __tablename__ = "factor_values"

    # 外键
    factor_id = Column(
        String(36),
        ForeignKey("factor_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="因子ID",
    )

    # 数据维度
    trade_date = Column(String(10), nullable=False, comment="交易日期 YYYY-MM-DD")
    symbol = Column(String(20), nullable=False, comment="股票代码")

    # 因子值
    value = Column(Float, comment="原始因子值")
    zscore = Column(Float, comment="横截面 Z-Score 标准化值")
    percentile = Column(Float, comment="横截面百分位 (0-1)")

    # 元数据
    computed_at = Column(DateTime, default=datetime.utcnow, comment="计算时间")

    # 关系
    factor_definition = relationship("FactorDefinition", back_populates="factor_values")

    # 索引和约束
    __table_args__ = (
        UniqueConstraint("factor_id", "trade_date", "symbol", name="uq_factor_value"),
        Index("ix_factor_values_date", "trade_date"),
        Index("ix_factor_values_symbol", "symbol"),
        Index("ix_factor_values_factor_date", "factor_id", "trade_date"),
    )


class FactorAnalysisCache(Base, UUIDMixin, TimestampMixin):
    """
    因子分析结果缓存表

    存储 IC 分析、分组回测等计算结果
    """

    __tablename__ = "factor_analysis_cache"

    # 外键
    factor_id = Column(
        String(36),
        ForeignKey("factor_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="因子ID",
    )

    # 分析类型
    analysis_type = Column(
        String(50),
        nullable=False,
        comment="分析类型: ic_analysis/group_return/turnover/decay",
    )

    # 分析参数
    start_date = Column(String(10), nullable=False, comment="开始日期")
    end_date = Column(String(10), nullable=False, comment="结束日期")
    parameters = Column(JSONB, default={}, comment="其他参数 JSON")

    # 分析结果
    result = Column(JSONB, nullable=False, comment="分析结果 JSON")

    # 版本控制 (关联因子版本)
    factor_version = Column(Integer, nullable=False, comment="因子版本号")

    # 有效性
    is_valid = Column(Boolean, default=True, comment="是否有效")
    expires_at = Column(DateTime, comment="过期时间")

    # 关系
    factor_definition = relationship("FactorDefinition", back_populates="analysis_cache")

    # 索引
    __table_args__ = (
        Index("ix_analysis_cache_factor_type", "factor_id", "analysis_type"),
        Index("ix_analysis_cache_dates", "start_date", "end_date"),
    )

    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        if not self.is_valid:
            return True
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False


class FactorComputeLog(Base, UUIDMixin):
    """
    因子计算日志表

    记录每次因子计算的状态和性能
    """

    __tablename__ = "factor_compute_logs"

    # 外键
    factor_id = Column(
        String(36),
        ForeignKey("factor_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="因子ID",
    )

    # 计算范围
    start_date = Column(String(10), nullable=False, comment="计算开始日期")
    end_date = Column(String(10), nullable=False, comment="计算结束日期")
    symbol_count = Column(Integer, comment="股票数量")

    # 计算状态
    status = Column(
        String(20),
        default="pending",
        comment="状态: pending/running/completed/failed",
    )
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")

    # 性能统计
    duration_seconds = Column(Float, comment="耗时 (秒)")
    rows_computed = Column(Integer, comment="计算行数")
    rows_cached = Column(Integer, comment="缓存命中行数")

    # 错误信息
    error_message = Column(Text, comment="错误信息")

    # 索引
    __table_args__ = (
        Index("ix_compute_log_factor", "factor_id"),
        Index("ix_compute_log_status", "status"),
    )


class IncrementalSchedule(Base, UUIDMixin, TimestampMixin):
    """
    增量计算调度表

    管理因子的增量计算任务
    """

    __tablename__ = "incremental_schedules"

    # 外键
    factor_id = Column(
        String(36),
        ForeignKey("factor_definitions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="因子ID",
    )

    # 调度配置
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=0, comment="优先级 (数字越大优先级越高)")

    # 计算状态
    last_success_date = Column(String(10), comment="最后成功计算日期")
    next_compute_date = Column(String(10), comment="下次计算日期")

    # 失败处理
    consecutive_failures = Column(Integer, default=0, comment="连续失败次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    last_error = Column(Text, comment="最后错误信息")

    # 索引
    __table_args__ = (
        Index("ix_schedule_enabled", "is_enabled"),
        Index("ix_schedule_next_date", "next_compute_date"),
    )
