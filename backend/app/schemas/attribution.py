"""
Phase 13: \u5f52\u56e0\u4e0e\u62a5\u8868 - Pydantic \u6a21\u578b

\u5305\u542b:
- Brinson \u5f52\u56e0\u6a21\u578b
- \u56e0\u5b50\u5f52\u56e0\u6a21\u578b
- TCA \u4ea4\u6613\u6210\u672c\u5206\u6790
- \u62a5\u8868\u5bfc\u51fa
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============ \u679a\u4e3e\u7c7b\u578b ============

class SectorType(str, Enum):
    """\u884c\u4e1a\u7c7b\u578b"""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCIALS = "financials"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    INDUSTRIALS = "industrials"
    ENERGY = "energy"
    MATERIALS = "materials"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"
    COMMUNICATION_SERVICES = "communication_services"


class RiskFactorType(str, Enum):
    """\u98ce\u9669\u56e0\u5b50\u7c7b\u578b"""
    MARKET = "market"
    SIZE = "size"
    VALUE = "value"
    MOMENTUM = "momentum"
    QUALITY = "quality"
    VOLATILITY = "volatility"
    DIVIDEND = "dividend"
    GROWTH = "growth"


class AttributionReportType(str, Enum):
    """\u5f52\u56e0\u62a5\u544a\u7c7b\u578b"""
    BRINSON = "brinson"
    FACTOR = "factor"
    TCA = "tca"
    COMPREHENSIVE = "comprehensive"


class ReportFormat(str, Enum):
    """\u62a5\u544a\u683c\u5f0f"""
    PDF = "pdf"
    EXCEL = "excel"
    JSON = "json"


class TCABenchmark(str, Enum):
    """TCA \u57fa\u51c6"""
    VWAP = "vwap"
    TWAP = "twap"
    ARRIVAL = "arrival"


# ============ \u57fa\u7840\u6a21\u578b ============

class TimePeriod(BaseModel):
    """\u65f6\u95f4\u6bb5"""
    start: date
    end: date


# ============ Brinson \u5f52\u56e0 ============

class SectorAttribution(BaseModel):
    """\u884c\u4e1a\u5f52\u56e0\u660e\u7ec6"""
    sector: SectorType
    sector_name: str
    portfolio_weight: float = Field(..., description="\u7ec4\u5408\u6743\u91cd")
    benchmark_weight: float = Field(..., description="\u57fa\u51c6\u6743\u91cd")
    active_weight: float = Field(..., description="\u4e3b\u52a8\u6743\u91cd")
    portfolio_return: float = Field(..., description="\u7ec4\u5408\u6536\u76ca")
    benchmark_return: float = Field(..., description="\u57fa\u51c6\u6536\u76ca")
    active_return: float = Field(..., description="\u4e3b\u52a8\u6536\u76ca")
    allocation_effect: float = Field(..., description="\u914d\u7f6e\u6548\u5e94")
    selection_effect: float = Field(..., description="\u9009\u80a1\u6548\u5e94")
    interaction_effect: float = Field(..., description="\u4ea4\u4e92\u6548\u5e94")
    total_effect: float = Field(..., description="\u603b\u6548\u5e94")


class BrinsonAttribution(BaseModel):
    """Brinson \u5f52\u56e0\u7ed3\u679c"""
    period: TimePeriod
    portfolio_return: float = Field(..., description="\u7ec4\u5408\u603b\u6536\u76ca")
    benchmark_return: float = Field(..., description="\u57fa\u51c6\u603b\u6536\u76ca")
    excess_return: float = Field(..., description="\u8d85\u989d\u6536\u76ca")

    # \u603b\u6548\u5e94
    total_allocation_effect: float = Field(..., description="\u603b\u914d\u7f6e\u6548\u5e94")
    total_selection_effect: float = Field(..., description="\u603b\u9009\u80a1\u6548\u5e94")
    total_interaction_effect: float = Field(..., description="\u603b\u4ea4\u4e92\u6548\u5e94")

    # \u884c\u4e1a\u660e\u7ec6
    sector_details: list[SectorAttribution] = []

    # \u89e3\u8bfb
    interpretation: str = ""


class BrinsonAttributionRequest(BaseModel):
    """Brinson \u5f52\u56e0\u8bf7\u6c42"""
    portfolio_id: str
    benchmark_id: str = "SPY"
    start_date: date
    end_date: date
    frequency: str = "monthly"


# ============ \u56e0\u5b50\u5f52\u56e0 ============

class FactorExposure(BaseModel):
    """\u56e0\u5b50\u66b4\u9732"""
    factor: RiskFactorType
    factor_name: str
    exposure: float = Field(..., description="\u56e0\u5b50\u66b4\u9732")
    factor_return: float = Field(..., description="\u56e0\u5b50\u6536\u76ca")
    contribution: float = Field(..., description="\u6536\u76ca\u8d21\u732e")
    t_stat: float = Field(0.0, description="t\u7edf\u8ba1\u91cf")


class FactorAttribution(BaseModel):
    """\u56e0\u5b50\u5f52\u56e0\u7ed3\u679c"""
    period: TimePeriod
    total_return: float = Field(..., description="\u603b\u6536\u76ca")
    benchmark_return: float = Field(..., description="\u57fa\u51c6\u6536\u76ca")
    active_return: float = Field(..., description="\u8d85\u989d\u6536\u76ca")

    # \u56e0\u5b50\u8d21\u732e
    factor_contributions: list[FactorExposure] = []

    # \u6c47\u603b
    total_factor_return: float = Field(..., description="\u56e0\u5b50\u603b\u6536\u76ca")
    specific_return: float = Field(..., description="\u7279\u8d28\u6536\u76ca")

    # \u98ce\u9669\u6307\u6807
    information_ratio: float = Field(0.0, description="\u4fe1\u606f\u6bd4\u7387")
    tracking_error: float = Field(0.0, description="\u8ddf\u8e2a\u8bef\u5dee")
    active_risk: float = Field(0.0, description="\u4e3b\u52a8\u98ce\u9669")

    # \u89e3\u8bfb
    interpretation: str = ""


class FactorAttributionRequest(BaseModel):
    """\u56e0\u5b50\u5f52\u56e0\u8bf7\u6c42"""
    portfolio_id: str
    benchmark_id: str | None = None
    start_date: date
    end_date: date
    factors: list[RiskFactorType] | None = None


# ============ TCA \u4ea4\u6613\u6210\u672c\u5206\u6790 ============

class TradeCostBreakdown(BaseModel):
    """\u4ea4\u6613\u6210\u672c\u7ec4\u6210"""
    commission: float = Field(0.0, description="\u4f63\u91d1")
    slippage: float = Field(0.0, description="\u6ed1\u70b9")
    market_impact: float = Field(0.0, description="\u5e02\u573a\u51b2\u51fb")
    timing_cost: float = Field(0.0, description="\u65f6\u673a\u6210\u672c")
    opportunity_cost: float = Field(0.0, description="\u673a\u4f1a\u6210\u672c")
    total_cost: float = Field(0.0, description="\u603b\u6210\u672c")


class TradeTCA(BaseModel):
    """\u5355\u7b14\u4ea4\u6613 TCA"""
    trade_id: str
    symbol: str
    side: str
    quantity: float

    # \u4ef7\u683c
    decision_price: float = Field(..., description="\u51b3\u7b56\u4ef7\u683c")
    arrival_price: float = Field(..., description="\u5230\u8fbe\u4ef7\u683c")
    execution_price: float = Field(..., description="\u6267\u884c\u4ef7\u683c")
    benchmark_price: float = Field(..., description="\u57fa\u51c6\u4ef7\u683c")

    # \u6210\u672c
    implementation_shortfall: float = Field(..., description="\u6267\u884c\u7f3a\u53e3")
    implementation_shortfall_bps: float = Field(..., description="\u6267\u884c\u7f3a\u53e3(\u57fa\u70b9)")
    costs: TradeCostBreakdown

    # \u65f6\u95f4
    decision_time: datetime
    execution_time: datetime
    execution_duration: float = Field(..., description="\u6267\u884c\u65f6\u957f(\u79d2)")

    # \u5e02\u573a\u6761\u4ef6
    market_volatility: float = 0.0
    volume_participation: float = 0.0


class StrategyTCA(BaseModel):
    """\u7b56\u7565 TCA \u6c47\u603b"""
    period: TimePeriod
    total_trades: int = 0
    total_volume: float = 0.0
    total_notional: float = 0.0

    # \u6c47\u603b\u6210\u672c
    total_costs: TradeCostBreakdown
    avg_cost_bps: float = Field(0.0, description="\u5e73\u5747\u6210\u672c(\u57fa\u70b9)")

    # \u6309\u65b9\u5411
    buy_costs: TradeCostBreakdown | None = None
    sell_costs: TradeCostBreakdown | None = None

    # \u6309\u65f6\u6bb5
    by_time_of_day: list[dict[str, Any]] = []

    # \u6309\u80a1\u7968
    by_symbol: list[dict[str, Any]] = []

    # \u57fa\u51c6\u5bf9\u6bd4
    vs_benchmark: dict[str, float] = {}

    # \u4ea4\u6613\u660e\u7ec6
    trades: list[TradeTCA] = []


class TCARequest(BaseModel):
    """TCA \u8bf7\u6c42"""
    portfolio_id: str | None = None
    strategy_id: str | None = None
    start_date: date
    end_date: date
    symbols: list[str] | None = None
    benchmark: TCABenchmark = TCABenchmark.VWAP


# ============ \u7efc\u5408\u5f52\u56e0\u62a5\u544a ============

class AttributionSummary(BaseModel):
    """\u5f52\u56e0\u6458\u8981"""
    portfolio_return: float
    benchmark_return: float
    excess_return: float
    information_ratio: float
    tracking_error: float
    sharpe_ratio: float
    max_drawdown: float


class ComprehensiveAttribution(BaseModel):
    """\u7efc\u5408\u5f52\u56e0\u62a5\u544a"""
    period: TimePeriod
    portfolio_id: str
    portfolio_name: str
    benchmark_id: str
    benchmark_name: str

    # \u6536\u76ca\u6982\u89c8
    summary: AttributionSummary

    # Brinson \u5f52\u56e0
    brinson: BrinsonAttribution | None = None

    # \u56e0\u5b50\u5f52\u56e0
    factor: FactorAttribution | None = None

    # TCA
    tca: StrategyTCA | None = None

    # \u65f6\u5e8f\u6570\u636e
    time_series: dict[str, list[float]] = {}

    # \u62a5\u544a\u751f\u6210\u65f6\u95f4
    generated_at: datetime


class ExportReportRequest(BaseModel):
    """\u5bfc\u51fa\u62a5\u544a\u8bf7\u6c42"""
    report_type: AttributionReportType
    portfolio_id: str
    start_date: date
    end_date: date
    format: ReportFormat = ReportFormat.PDF
    include_charts: bool = True
    language: str = "zh"


# ============ API \u54cd\u5e94\u6a21\u578b ============

class BrinsonResponse(BaseModel):
    """Brinson \u5f52\u56e0\u54cd\u5e94"""
    success: bool
    data: BrinsonAttribution | None = None
    error: str | None = None


class FactorResponse(BaseModel):
    """\u56e0\u5b50\u5f52\u56e0\u54cd\u5e94"""
    success: bool
    data: FactorAttribution | None = None
    error: str | None = None


class TCAResponse(BaseModel):
    """TCA \u54cd\u5e94"""
    success: bool
    data: StrategyTCA | None = None
    error: str | None = None


class ComprehensiveResponse(BaseModel):
    """\u7efc\u5408\u5f52\u56e0\u54cd\u5e94"""
    success: bool
    data: ComprehensiveAttribution | None = None
    error: str | None = None
