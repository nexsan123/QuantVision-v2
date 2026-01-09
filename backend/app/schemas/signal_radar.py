"""
信号雷达 Pydantic Schema

PRD 4.16.2: 信号雷达功能
- 实时买入/卖出信号
- 接近触发检测
- 信号强度分级
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SignalType(str, Enum):
    """信号类型"""
    BUY = "buy"      # 买入信号
    SELL = "sell"    # 卖出信号
    HOLD = "hold"    # 持有


class SignalStrength(str, Enum):
    """信号强度"""
    STRONG = "strong"    # 强信号 (score >= 80)
    MEDIUM = "medium"    # 中等信号 (60 <= score < 80)
    WEAK = "weak"        # 弱信号 (score < 60)


class SignalStatus(str, Enum):
    """信号状态 (PRD 4.16.2)"""
    HOLDING = "holding"           # 已持仓
    BUY_SIGNAL = "buy_signal"     # 买入信号已触发
    SELL_SIGNAL = "sell_signal"   # 卖出信号已触发
    NEAR_TRIGGER = "near_trigger" # 接近触发 (>=80%)
    MONITORING = "monitoring"     # 监控中
    EXCLUDED = "excluded"         # 不符合条件


# ============ 因子触发信息 ============

class FactorTrigger(BaseModel):
    """因子触发信息"""
    factor_id: str
    factor_name: str
    current_value: float
    threshold: float
    direction: str  # 'above' 或 'below'
    near_trigger_pct: float = Field(0, ge=0, le=100, description="接近触发程度%")
    is_satisfied: bool = False


# ============ 信号模型 ============

class Signal(BaseModel):
    """信号实体"""
    signal_id: str
    strategy_id: str
    symbol: str
    company_name: str
    signal_type: SignalType
    signal_strength: SignalStrength
    signal_score: float = Field(..., ge=0, le=100, description="信号分数 0-100")
    status: SignalStatus = SignalStatus.MONITORING
    triggered_factors: list[FactorTrigger] = Field(default_factory=list)
    current_price: Decimal
    target_price: Optional[Decimal] = None
    stop_loss_price: Optional[Decimal] = None
    expected_return_pct: Optional[float] = None
    signal_time: datetime
    expires_at: Optional[datetime] = None
    is_holding: bool = False

    class Config:
        from_attributes = True


class SignalSummary(BaseModel):
    """信号摘要"""
    signal_id: str
    symbol: str
    company_name: str
    signal_type: SignalType
    signal_strength: SignalStrength
    signal_score: float
    current_price: float
    signal_time: datetime


# ============ API 请求/响应 ============

class SignalListRequest(BaseModel):
    """信号列表请求"""
    strategy_id: str
    signal_type: Optional[SignalType] = None
    signal_strength: Optional[SignalStrength] = None
    status: Optional[SignalStatus] = None
    search: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class SignalListResponse(BaseModel):
    """信号列表响应"""
    total: int
    signals: list[Signal]
    summary: dict[str, int]  # 各类型信号数量


class SignalHistoryRequest(BaseModel):
    """历史信号请求"""
    strategy_id: str
    symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=500)


class SignalHistoryResponse(BaseModel):
    """历史信号响应"""
    total: int
    signals: list[Signal]


class StockSearchRequest(BaseModel):
    """股票搜索请求"""
    query: str = Field(..., min_length=1, max_length=20)
    strategy_id: Optional[str] = None
    limit: int = Field(20, ge=1, le=50)


class StockSearchResult(BaseModel):
    """股票搜索结果"""
    symbol: str
    company_name: str
    sector: Optional[str] = None
    current_price: float
    signal_status: Optional[SignalStatus] = None
    signal_score: Optional[float] = None


class StockSearchResponse(BaseModel):
    """股票搜索响应"""
    results: list[StockSearchResult]


class StatusSummary(BaseModel):
    """状态分布统计"""
    holding: int = 0
    buy_signal: int = 0
    sell_signal: int = 0
    near_trigger: int = 0
    monitoring: int = 0
    excluded: int = 0


class StatusSummaryResponse(BaseModel):
    """状态分布响应"""
    strategy_id: str
    summary: StatusSummary
    updated_at: datetime


# ============ 信号状态缓存 ============

class SignalStatusCache(BaseModel):
    """信号状态缓存 (用于快速查询)"""
    strategy_id: str
    symbol: str
    status: SignalStatus
    signal_strength: float = 0  # 0-100
    factor_values: dict[str, float] = Field(default_factory=dict)
    updated_at: datetime

    class Config:
        from_attributes = True
