"""
分策略持仓 Schema
PRD 4.18 分策略持仓管理
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class StrategyPosition(BaseModel):
    """策略持仓 (逻辑隔离)"""
    position_id: str
    user_id: str
    account_id: str
    strategy_id: Optional[str] = None  # None = 手动交易
    strategy_name: Optional[str] = None

    symbol: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float

    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl: float = 0  # 已实现盈亏

    # 止盈止损
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

    # 风险指标
    beta: Optional[float] = None
    volatility: Optional[float] = None

    created_at: datetime
    updated_at: datetime


class PositionSource(BaseModel):
    """持仓来源"""
    strategy_id: Optional[str] = None
    strategy_name: str
    quantity: int
    avg_cost: float
    pnl: float
    pnl_pct: float


class ConsolidatedPosition(BaseModel):
    """同股票汇总持仓"""
    symbol: str
    total_quantity: int
    weighted_avg_cost: float
    current_price: float
    total_market_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float

    # 来源策略
    sources: list[PositionSource]

    # 集中度
    concentration_pct: float = 0  # 占账户比例


class PositionGroup(BaseModel):
    """持仓分组 (按策略)"""
    strategy_id: Optional[str] = None
    strategy_name: str  # "手动交易" 或策略名
    positions: list[StrategyPosition]
    total_market_value: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    position_count: int = 0


class AccountPositionSummary(BaseModel):
    """账户持仓汇总"""
    account_id: str
    total_market_value: float
    total_cash: float
    total_equity: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float

    # 按策略分组
    groups: list[PositionGroup]

    # 同股票汇总视图
    consolidated: list[ConsolidatedPosition]

    # 风险指标
    concentration_warnings: list[str] = []  # 集中度警告
    portfolio_beta: Optional[float] = None

    updated_at: datetime


class SellPositionRequest(BaseModel):
    """卖出持仓请求"""
    position_id: str
    quantity: int = Field(..., ge=1)
    order_type: str = Field(default="market")
    limit_price: Optional[float] = None


class SellPositionResponse(BaseModel):
    """卖出持仓响应"""
    success: bool
    order_id: Optional[str] = None
    message: str


class UpdateStopLossRequest(BaseModel):
    """更新止损请求"""
    stop_loss: Optional[float] = Field(None, ge=0)
    take_profit: Optional[float] = Field(None, ge=0)


class PositionRiskMetrics(BaseModel):
    """持仓风险指标"""
    symbol: str
    beta: float
    volatility: float
    var_95: float  # 95% VaR
    max_loss: float
    correlation_to_spy: float
