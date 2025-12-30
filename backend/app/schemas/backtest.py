"""
回测相关 Schema

提供:
- 回测创建请求
- 回测响应
- 回测结果响应
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class BacktestCreateRequest(BaseModel):
    """
    回测创建请求
    """
    name: str = Field(..., min_length=1, max_length=100, description="回测名称")

    # 策略配置
    strategy_id: str | None = Field(None, description="策略 ID")
    strategy_config: dict[str, Any] | None = Field(None, description="策略配置")

    # 时间范围
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")

    # 资金配置
    initial_capital: float = Field(
        1_000_000.0,
        ge=10000,
        description="初始资金",
    )
    commission_rate: float = Field(
        0.001,
        ge=0,
        le=0.01,
        description="手续费率",
    )
    slippage_rate: float = Field(
        0.001,
        ge=0,
        le=0.01,
        description="滑点率",
    )
    slippage_model: str = Field(
        "fixed",
        description="滑点模型 (fixed, volume_based, sqrt)",
    )

    # 仓位限制
    max_position_pct: float = Field(
        0.1,
        ge=0.01,
        le=1.0,
        description="单只股票最大仓位",
    )
    max_leverage: float = Field(
        1.0,
        ge=0.1,
        le=3.0,
        description="最大杠杆",
    )

    # 调仓
    rebalance_freq: str = Field(
        "daily",
        description="调仓频率 (daily, weekly, monthly)",
    )

    # 股票池
    universe: list[str] | None = Field(None, description="股票列表")
    universe_id: str | None = Field(None, description="股票池 ID")

    # 基准
    benchmark: str = Field("SPY", description="基准代码")


class BacktestResponse(BaseModel):
    """回测响应 (任务信息)"""
    id: str = Field(..., description="回测 ID")
    name: str = Field(..., description="回测名称")
    status: str = Field(..., description="状态")
    progress: int = Field(0, ge=0, le=100, description="进度")
    created_at: datetime
    completed_at: datetime | None = None
    error: str | None = None


class BacktestMetrics(BaseModel):
    """回测绩效指标"""
    total_return: float = Field(..., description="总收益")
    annual_return: float = Field(..., description="年化收益")
    volatility: float = Field(0.0, description="年化波动率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: float = Field(0.0, description="索提诺比率")
    calmar_ratio: float = Field(..., description="卡尔马比率")
    win_rate: float = Field(..., description="胜率")
    profit_factor: float = Field(0.0, description="盈亏比")
    beta: float = Field(0.0, description="贝塔")
    alpha: float = Field(0.0, description="阿尔法")


class BacktestResultResponse(BaseModel):
    """回测结果响应"""
    id: str = Field(..., description="回测 ID")
    name: str = Field(..., description="回测名称")
    status: str = Field(..., description="状态")

    # 配置摘要
    config: dict[str, Any] = Field(..., description="回测配置")

    # 绩效指标
    metrics: BacktestMetrics

    # 时间序列数据
    equity_curve: dict[str, float] | None = Field(None, description="权益曲线")
    benchmark_curve: dict[str, float] | None = Field(None, description="基准曲线")
    drawdown_series: dict[str, float] | None = Field(None, description="回撤序列")
    monthly_returns: dict[str, float] | None = Field(None, description="月度收益")

    # 交易统计
    trades_count: int = Field(0, description="交易次数")
    trades_summary: dict[str, Any] | None = Field(None, description="交易统计")


class BacktestListResponse(BaseModel):
    """回测列表响应"""
    backtests: list[BacktestResponse]
    total: int


class BacktestStatusRequest(BaseModel):
    """回测状态查询"""
    ids: list[str] = Field(..., min_length=1, max_length=100, description="回测 ID 列表")


class BacktestStatusResponse(BaseModel):
    """回测状态响应"""
    statuses: dict[str, dict[str, Any]] = Field(..., description="各回测状态")
