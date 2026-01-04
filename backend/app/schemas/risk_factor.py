"""
Phase 10: 风险系统升级 - Pydantic Schema

风险因子模型、风险分解、压力测试、实时监控的数据模型
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============ 枚举类型 ============

class StyleFactor(str, Enum):
    """风格因子"""
    SIZE = "size"
    VALUE = "value"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    QUALITY = "quality"
    GROWTH = "growth"
    LIQUIDITY = "liquidity"
    LEVERAGE = "leverage"


class IndustryFactor(str, Enum):
    """行业因子 (GICS一级)"""
    COMMUNICATION_SERVICES = "communication_services"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    ENERGY = "energy"
    FINANCIALS = "financials"
    HEALTHCARE = "healthcare"
    INDUSTRIALS = "industrials"
    INFORMATION_TECHNOLOGY = "information_technology"
    MATERIALS = "materials"
    REAL_ESTATE = "real_estate"
    UTILITIES = "utilities"


class ScenarioType(str, Enum):
    """压力情景类型"""
    HISTORICAL = "historical"
    HYPOTHETICAL = "hypothetical"
    CUSTOM = "custom"


class AlertLevel(str, Enum):
    """警报级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ExposureStatus(str, Enum):
    """暴露状态"""
    NORMAL = "normal"
    WARNING = "warning"
    BREACH = "breach"


# ============ 因子暴露模型 ============

class FactorExposureItem(BaseModel):
    """单个因子暴露"""
    factor: str
    exposure: float = Field(..., description="暴露系数")
    t_stat: float = Field(0.0, description="t统计量")
    p_value: float = Field(1.0, description="p值")
    is_significant: bool = Field(False, description="是否显著")
    risk_contribution: float = Field(0.0, description="风险贡献(%)")


class StyleFactorExposures(BaseModel):
    """风格因子暴露"""
    size: float = 0.0
    value: float = 0.0
    momentum: float = 0.0
    volatility: float = 0.0
    quality: float = 0.0
    growth: float = 0.0
    liquidity: float = 0.0
    leverage: float = 0.0


# ============ 风险分解模型 ============

class RiskContributions(BaseModel):
    """风险贡献分解"""
    market: float = Field(..., description="市场风险贡献(%)")
    style: float = Field(..., description="风格风险贡献(%)")
    industry: float = Field(..., description="行业风险贡献(%)")
    specific: float = Field(..., description="特质风险贡献(%)")


class FactorExposures(BaseModel):
    """因子暴露汇总"""
    market: float = Field(1.0, description="市场Beta")
    style: StyleFactorExposures = Field(default_factory=StyleFactorExposures)
    industry: dict[str, float] = Field(default_factory=dict)


class RiskDecompositionResult(BaseModel):
    """风险分解结果"""
    total_risk: float = Field(..., description="总风险(年化波动率)")
    risk_contributions: RiskContributions
    style_risk_details: dict[str, float] = Field(default_factory=dict)
    industry_risk_details: dict[str, float] = Field(default_factory=dict)
    factor_exposures: FactorExposures
    r_squared: float = Field(0.0, description="解释力度")
    tracking_error: float = Field(0.0, description="跟踪误差")
    active_risk: float = Field(0.0, description="主动风险")


class RiskDecompositionRequest(BaseModel):
    """风险分解请求"""
    portfolio_id: str | None = Field(None, description="组合ID")
    holdings: dict[str, float] = Field(..., description="持仓 {symbol: weight}")
    benchmark: str = Field("SPY", description="基准")
    lookback_days: int = Field(252, ge=60, le=756, description="回溯天数")


# ============ 压力测试模型 ============

class ScenarioShocks(BaseModel):
    """情景冲击参数"""
    market_return: float | None = Field(None, description="市场收益冲击")
    volatility_multiplier: float | None = Field(None, ge=0.5, le=10.0, description="波动率乘数")
    sector_shocks: dict[str, float] | None = Field(None, description="行业冲击")
    factor_shocks: dict[str, float] | None = Field(None, description="因子冲击")
    liquidity_shock: float | None = Field(None, ge=1.0, le=10.0, description="流动性冲击")


class HistoricalPeriod(BaseModel):
    """历史情景时间段"""
    start_date: str
    end_date: str
    spy_drawdown: float


class StressScenario(BaseModel):
    """压力测试情景"""
    id: str
    name: str
    type: ScenarioType
    description: str = ""
    shocks: ScenarioShocks
    historical_period: HistoricalPeriod | None = None


class PortfolioImpact(BaseModel):
    """组合影响"""
    expected_loss: float = Field(..., description="预期亏损金额")
    expected_loss_percent: float = Field(..., description="预期亏损百分比")
    var_impact: float = Field(0.0, description="VaR变化")
    max_drawdown: float = Field(0.0, description="最大回撤")
    recovery_days: int = Field(0, description="预计恢复天数")
    liquidation_risk: bool = Field(False, description="是否触发强平")


class PositionImpact(BaseModel):
    """持仓影响"""
    symbol: str
    current_weight: float
    expected_loss: float
    loss_percent: float
    contribution: float = Field(..., description="对组合亏损的贡献")


class RiskMetricsChange(BaseModel):
    """风险指标变化"""
    volatility_before: float = 0.0
    volatility_after: float = 0.0
    var_before: float = 0.0
    var_after: float = 0.0
    beta_before: float = 1.0
    beta_after: float = 1.0


class StressTestResult(BaseModel):
    """压力测试结果"""
    scenario: StressScenario
    portfolio_impact: PortfolioImpact
    position_impacts: list[PositionImpact] = Field(default_factory=list)
    risk_metrics_change: RiskMetricsChange = Field(default_factory=RiskMetricsChange)
    recommendations: list[str] = Field(default_factory=list)


class StressTestRequest(BaseModel):
    """压力测试请求"""
    portfolio_id: str | None = None
    holdings: dict[str, float] = Field(..., description="持仓")
    portfolio_value: float = Field(1000000.0, gt=0, description="组合价值")
    scenario_id: str | None = Field(None, description="预置情景ID")
    custom_scenario: StressScenario | None = Field(None, description="自定义情景")
    asset_betas: dict[str, float] | None = None
    asset_sectors: dict[str, str] | None = None


class StressTestBatchRequest(BaseModel):
    """批量压力测试请求"""
    portfolio_id: str | None = None
    holdings: dict[str, float] = Field(..., description="持仓")
    portfolio_value: float = Field(1000000.0, gt=0)
    scenario_ids: list[str] = Field(default_factory=list, description="情景ID列表(空=全部)")
    asset_betas: dict[str, float] | None = None
    asset_sectors: dict[str, str] | None = None


# ============ 实时监控模型 ============

class CurrentMetrics(BaseModel):
    """当前风险指标"""
    drawdown: float = Field(0.0, description="当前回撤")
    drawdown_limit: float = Field(0.15, description="回撤限制")
    var_95: float = Field(0.0, description="95% VaR")
    var_limit: float = Field(0.03, description="VaR限制")
    volatility: float = Field(0.0, description="当前波动率")
    volatility_limit: float = Field(0.25, description="波动率限制")


class ExposureStatusDetail(BaseModel):
    """暴露状态详情"""
    current: float
    limit: float
    status: ExposureStatus


class IndustryExposureStatus(BaseModel):
    """行业暴露状态"""
    industry: str
    current: float
    limit: float
    status: ExposureStatus


class StyleExposureStatus(BaseModel):
    """风格暴露状态"""
    factor: str
    current: float
    limit: float
    status: ExposureStatus


class FactorExposureStatus(BaseModel):
    """因子暴露状态"""
    market: ExposureStatusDetail
    max_industry: IndustryExposureStatus
    max_style: StyleExposureStatus


class RiskAlert(BaseModel):
    """风险警报"""
    id: str
    timestamp: datetime
    level: AlertLevel
    type: str
    message: str
    current_value: float
    threshold: float
    acknowledged: bool = False


class RiskMonitorStatus(BaseModel):
    """风险监控状态"""
    current_metrics: CurrentMetrics
    factor_exposure_status: FactorExposureStatus
    active_alerts: list[RiskAlert] = Field(default_factory=list)
    risk_score: float = Field(0.0, ge=0, le=100, description="综合风险评分")
    risk_level: RiskLevel = Field(RiskLevel.LOW)
    last_updated: datetime


class RiskLimits(BaseModel):
    """风险限制配置"""
    max_drawdown: float = Field(0.15, ge=0.01, le=0.50, description="最大回撤")
    max_var: float = Field(0.03, ge=0.01, le=0.10, description="最大VaR")
    max_volatility: float = Field(0.25, ge=0.05, le=0.50, description="最大波动率")
    max_industry_exposure: float = Field(0.25, ge=0.10, le=0.50, description="最大行业暴露")
    max_style_exposure: float = Field(0.5, ge=0.1, le=2.0, description="最大风格暴露")
    max_single_position: float = Field(0.10, ge=0.01, le=0.30, description="最大单一持仓")
    max_beta: float = Field(1.5, ge=0.5, le=3.0, description="最大Beta")


class RiskLimitsUpdateRequest(BaseModel):
    """风险限制更新请求"""
    limits: RiskLimits


# ============ API 响应模型 ============

class ScenarioListResponse(BaseModel):
    """压力情景列表响应"""
    scenarios: list[StressScenario]
    total: int


class StressTestBatchResponse(BaseModel):
    """批量压力测试响应"""
    results: list[StressTestResult]
    summary: dict[str, Any] = Field(default_factory=dict)


class RiskDashboardResponse(BaseModel):
    """风险仪表盘响应"""
    monitor_status: RiskMonitorStatus
    risk_decomposition: RiskDecompositionResult | None = None
    recent_stress_tests: list[StressTestResult] = Field(default_factory=list)
