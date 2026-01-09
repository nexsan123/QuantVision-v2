"""
交易记录和归因 Schema 定义
PRD 4.5 交易归因系统
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, date
from enum import Enum


class TradeSide(str, Enum):
    """交易方向"""
    BUY = "buy"
    SELL = "sell"


class TradeOutcome(str, Enum):
    """交易结果"""
    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    OPEN = "open"  # 未平仓


class StrategyType(str, Enum):
    """策略类型"""
    INTRADAY = "intraday"   # 日内交易
    SHORT_TERM = "short_term"  # 短线 (1-5天)
    MEDIUM_TERM = "medium_term"  # 中线 (5-30天)
    LONG_TERM = "long_term"  # 长线 (>30天)


class FactorSnapshot(BaseModel):
    """入场时因子快照"""
    factor_id: str
    factor_name: str
    factor_value: float
    factor_rank: float = Field(description="因子在同期所有股票中的排名百分位")
    signal_contribution: float = Field(description="该因子对信号的贡献度")


class MarketSnapshot(BaseModel):
    """入场时市场环境快照"""
    market_index: float = Field(description="大盘指数")
    market_change_1d: float = Field(description="大盘1日涨跌幅")
    market_change_5d: float = Field(description="大盘5日涨跌幅")
    vix: float = Field(description="VIX恐慌指数")
    sector_rank: int = Field(description="所属板块强弱排名")
    market_sentiment: Literal["bullish", "neutral", "bearish"] = Field(description="市场情绪")


class TradeRecord(BaseModel):
    """交易记录"""
    trade_id: str
    strategy_id: str
    strategy_name: str
    deployment_id: str

    # 交易基本信息
    symbol: str
    side: TradeSide
    quantity: int
    entry_price: float
    entry_time: datetime

    # 平仓信息 (如果已平仓)
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None

    # 盈亏
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    outcome: TradeOutcome = TradeOutcome.OPEN

    # 快照
    factor_snapshot: list[FactorSnapshot] = Field(default=[], description="入场时因子快照")
    market_snapshot: Optional[MarketSnapshot] = None

    # 持仓时间
    hold_days: Optional[int] = None

    # 元数据
    created_at: datetime
    updated_at: datetime


class AttributionFactor(BaseModel):
    """归因因子"""
    factor_name: str
    contribution: float = Field(description="收益贡献")
    contribution_pct: float = Field(description="贡献占比")
    is_positive: bool = Field(description="是否正贡献")


class AttributionReport(BaseModel):
    """归因报告"""
    report_id: str
    strategy_id: str
    strategy_name: str

    # 报告周期
    period_start: date
    period_end: date

    # 交易统计
    total_trades: int
    win_trades: int
    loss_trades: int
    win_rate: float

    # 收益统计
    total_pnl: float
    total_pnl_pct: float
    avg_win: float
    avg_loss: float
    profit_factor: float = Field(description="盈亏比")

    # 归因分析
    factor_attributions: list[AttributionFactor]
    market_attribution: float = Field(description="市场因素贡献")
    alpha_attribution: float = Field(description="Alpha贡献")

    # 模式识别
    best_market_condition: str = Field(description="最佳市场环境")
    worst_market_condition: str = Field(description="最差市场环境")
    patterns: list[str] = Field(description="识别到的交易模式")

    # 元数据
    created_at: datetime
    trigger_reason: str = Field(description="触发原因")


class AIDiagnosis(BaseModel):
    """AI诊断"""
    diagnosis_id: str
    report_id: str

    summary: str = Field(description="诊断摘要")
    strengths: list[str] = Field(description="优势")
    weaknesses: list[str] = Field(description="劣势")
    suggestions: list[str] = Field(description="改进建议")
    risk_alerts: list[str] = Field(description="风险提示")

    confidence: float = Field(ge=0, le=1, description="诊断置信度")
    created_at: datetime


class AttributionTriggerConfig(BaseModel):
    """归因触发配置"""
    strategy_type: StrategyType
    trade_count_trigger: int = Field(description="交易次数触发")
    time_trigger: str = Field(description="时间触发周期")
    loss_trigger_pct: float = Field(description="亏损触发阈值")
    consecutive_loss_trigger: int = Field(description="连续亏损触发")


# 归因触发条件配置 (PRD 4.5)
ATTRIBUTION_TRIGGER_CONFIG = {
    StrategyType.INTRADAY: AttributionTriggerConfig(
        strategy_type=StrategyType.INTRADAY,
        trade_count_trigger=50,
        time_trigger="daily",
        loss_trigger_pct=0.02,
        consecutive_loss_trigger=5,
    ),
    StrategyType.SHORT_TERM: AttributionTriggerConfig(
        strategy_type=StrategyType.SHORT_TERM,
        trade_count_trigger=20,
        time_trigger="weekly",
        loss_trigger_pct=0.03,
        consecutive_loss_trigger=3,
    ),
    StrategyType.MEDIUM_TERM: AttributionTriggerConfig(
        strategy_type=StrategyType.MEDIUM_TERM,
        trade_count_trigger=10,
        time_trigger="monthly",
        loss_trigger_pct=0.05,
        consecutive_loss_trigger=3,
    ),
    StrategyType.LONG_TERM: AttributionTriggerConfig(
        strategy_type=StrategyType.LONG_TERM,
        trade_count_trigger=5,
        time_trigger="quarterly",
        loss_trigger_pct=0.03,
        consecutive_loss_trigger=2,
    ),
}


class GenerateAttributionRequest(BaseModel):
    """生成归因请求"""
    strategy_id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    force: bool = Field(default=False, description="强制生成，忽略触发条件")


class TradeListResponse(BaseModel):
    """交易列表响应"""
    total: int
    trades: list[TradeRecord]


class AttributionListResponse(BaseModel):
    """归因报告列表响应"""
    total: int
    reports: list[AttributionReport]
