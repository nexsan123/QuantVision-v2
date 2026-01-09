"""
策略回放 Pydantic Schema
PRD 4.17 策略回放功能
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReplaySpeed(str, Enum):
    """回放速度"""
    HALF = "0.5x"
    NORMAL = "1x"
    DOUBLE = "2x"
    FAST = "5x"


class ReplayStatus(str, Enum):
    """回放状态"""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"


# ============ 回放配置 ============


class ReplayConfig(BaseModel):
    """回放配置"""
    strategy_id: str = Field(..., description="策略ID")
    symbol: str = Field(..., description="股票代码")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    speed: ReplaySpeed = Field(default=ReplaySpeed.NORMAL, description="回放速度")


class ReplayState(BaseModel):
    """回放状态"""
    session_id: str = Field(..., description="会话ID")
    config: ReplayConfig
    status: ReplayStatus = ReplayStatus.IDLE
    current_time: datetime
    current_bar_index: int = 0
    total_bars: int = 0

    # 模拟持仓
    position_quantity: int = 0
    position_avg_cost: Decimal = Decimal("0")
    cash: Decimal = Decimal("100000")

    # 回放统计
    total_signals: int = 0
    executed_signals: int = 0
    total_return_pct: float = 0
    benchmark_return_pct: float = 0


# ============ 历史数据 ============


class HistoricalBar(BaseModel):
    """历史K线"""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class ThresholdConfig(BaseModel):
    """阈值配置"""
    value: float
    direction: str  # above/below
    passed: bool


class FactorSnapshot(BaseModel):
    """因子快照"""
    timestamp: datetime
    factor_values: dict[str, float] = Field(default_factory=dict)
    thresholds: dict[str, ThresholdConfig] = Field(default_factory=dict)
    overall_signal: str = "hold"  # buy/sell/hold
    conditions_met: int = 0
    conditions_total: int = 0


class SignalEvent(BaseModel):
    """信号事件"""
    event_id: str
    timestamp: datetime
    event_type: str  # buy_trigger, sell_trigger, condition_check
    symbol: str
    price: Decimal
    description: str
    factor_details: Optional[dict] = None


# ============ 回放响应 ============


class SignalMarker(BaseModel):
    """信号标记"""
    index: int
    time: str
    type: str  # buy/sell


class ReplayInitResponse(BaseModel):
    """回放初始化响应"""
    state: ReplayState
    total_bars: int
    signal_markers: list[SignalMarker] = Field(default_factory=list)


class ReplayTickResponse(BaseModel):
    """回放Tick响应"""
    state: ReplayState
    bar: HistoricalBar
    factor_snapshot: FactorSnapshot
    events: list[SignalEvent] = Field(default_factory=list)


class ReplayInsight(BaseModel):
    """回放洞察"""
    total_signals: int
    execution_rate: float
    win_rate: float
    alpha: float

    # AI洞察
    ai_insights: list[str] = Field(default_factory=list)

    # 收益对比
    strategy_return: float
    benchmark_return: float


class ReplayExport(BaseModel):
    """回放导出"""
    events: list[SignalEvent]
    summary: ReplayInsight


# ============ 请求模型 ============


class SeekRequest(BaseModel):
    """跳转请求"""
    target_time: datetime


class SpeedRequest(BaseModel):
    """速度设置请求"""
    speed: ReplaySpeed
