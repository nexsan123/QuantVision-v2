"""
策略构建器 7步配置 Pydantic Schema
Phase 8: 策略构建增强

7步流程:
1. Universe (投资池) - 定义可交易的股票范围
2. Alpha (因子层) - 选择和配置选股因子
3. Signal (信号层) - 定义买入和卖出规则 [新增]
4. Risk (风险层) - 设置风险约束和限制 [新增]
5. Portfolio (组合层) - 仓位分配和权重优化
6. Execution (执行层) - 交易执行配置
7. Monitor (监控层) - 监控和告警配置
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from enum import Enum


# ==================== 枚举类型 ====================

class BasePool(str, Enum):
    SP500 = "SP500"
    NASDAQ100 = "NASDAQ100"
    DOW30 = "DOW30"
    RUSSELL1000 = "RUSSELL1000"
    RUSSELL2000 = "RUSSELL2000"
    CUSTOM = "CUSTOM"


class Sector(str, Enum):
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCIALS = "financials"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    INDUSTRIALS = "industrials"
    MATERIALS = "materials"
    ENERGY = "energy"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"
    COMMUNICATION_SERVICES = "communication_services"


class FactorCategory(str, Enum):
    MOMENTUM = "momentum"
    VALUE = "value"
    QUALITY = "quality"
    VOLATILITY = "volatility"
    SIZE = "size"
    GROWTH = "growth"
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    CUSTOM = "custom"


class NeutralizeType(str, Enum):
    SECTOR = "sector"
    MARKET_CAP = "market_cap"
    BOTH = "both"
    NONE = "none"


class NormalizeType(str, Enum):
    ZSCORE = "zscore"
    RANK = "rank"
    PERCENTILE = "percentile"
    MINMAX = "minmax"
    NONE = "none"


class CombineMethod(str, Enum):
    EQUAL_WEIGHT = "equal_weight"
    IC_WEIGHT = "ic_weight"
    IR_WEIGHT = "ir_weight"
    CUSTOM_WEIGHT = "custom_weight"


class SignalType(str, Enum):
    LONG_ONLY = "long_only"
    LONG_SHORT = "long_short"


class RuleOperator(str, Enum):
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"


class RuleField(str, Enum):
    FACTOR_RANK = "factor_rank"
    FACTOR_SCORE = "factor_score"
    HOLDING_PNL = "holding_pnl"
    HOLDING_DAYS = "holding_days"
    PRICE_CHANGE = "price_change"
    VOLUME_CHANGE = "volume_change"


class WeightOptimizer(str, Enum):
    EQUAL_WEIGHT = "equal_weight"
    MARKET_CAP = "market_cap"
    MIN_VARIANCE = "min_variance"
    MAX_SHARPE = "max_sharpe"
    RISK_PARITY = "risk_parity"
    FACTOR_SCORE = "factor_score"
    CUSTOM = "custom"


class RebalanceFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class SlippageModel(str, Enum):
    FIXED = "fixed"
    VOLUME_BASED = "volume_based"
    SQRT = "sqrt"


class ExecutionAlgorithm(str, Enum):
    MARKET = "market"
    TWAP = "twap"
    VWAP = "vwap"
    POV = "pov"


class AlertType(str, Enum):
    DRAWDOWN = "drawdown"
    DAILY_LOSS = "daily_loss"
    POSITION_DRIFT = "position_drift"
    FACTOR_DECAY = "factor_decay"
    EXECUTION_FAIL = "execution_fail"
    CIRCUIT_BREAKER = "circuit_breaker"


class NotifyChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"
    PAUSED = "paused"
    ARCHIVED = "archived"


# ==================== Step 1: Universe 投资池配置 ====================

class MarketCapRange(BaseModel):
    """市值范围"""
    min: Optional[float] = Field(None, description="最小市值(亿美元)")
    max: Optional[float] = Field(None, description="最大市值(亿美元)")


class UniverseConfig(BaseModel):
    """Step 1: 投资池配置"""
    base_pool: BasePool = Field(default=BasePool.SP500, description="基础股票池")
    market_cap: MarketCapRange = Field(default_factory=lambda: MarketCapRange(min=10, max=None))
    avg_volume: float = Field(default=500, description="日均成交额下限(万美元)")
    listing_age: int = Field(default=1, description="最短上市时间(年)")
    exclude_sectors: List[Sector] = Field(default_factory=list, description="排除的行业")
    custom_symbols: Optional[List[str]] = Field(None, description="自定义股票列表")


# ==================== Step 2: Alpha 因子层配置 ====================

class FactorSelection(BaseModel):
    """单个因子选择"""
    factor_id: str = Field(..., description="因子ID")
    expression: str = Field(..., description="因子表达式")
    weight: Optional[float] = Field(1.0, description="自定义权重")
    direction: Literal[1, -1] = Field(1, description="方向: 1正向, -1反向")
    lookback_period: int = Field(20, description="回望周期(天)")


class AlphaConfig(BaseModel):
    """Step 2: 因子层配置"""
    factors: List[FactorSelection] = Field(default_factory=list, description="已选因子列表")
    combine_method: CombineMethod = Field(default=CombineMethod.EQUAL_WEIGHT, description="组合方式")
    normalize: NormalizeType = Field(default=NormalizeType.ZSCORE, description="标准化方式")
    neutralize: NeutralizeType = Field(default=NeutralizeType.SECTOR, description="中性化处理")


# ==================== Step 3: Signal 信号层配置 (新增) ====================

class SignalRule(BaseModel):
    """信号规则"""
    id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    field: RuleField = Field(..., description="规则字段")
    operator: RuleOperator = Field(..., description="操作符")
    threshold: float = Field(..., description="阈值")
    enabled: bool = Field(True, description="是否启用")


class SignalConfig(BaseModel):
    """Step 3: 信号层配置"""
    signal_type: SignalType = Field(default=SignalType.LONG_ONLY, description="信号类型")
    target_positions: int = Field(default=20, ge=5, le=100, description="目标持仓数")
    entry_rules: List[SignalRule] = Field(default_factory=list, description="入场规则(AND逻辑)")
    exit_rules: List[SignalRule] = Field(default_factory=list, description="出场规则(OR逻辑)")
    stop_loss: float = Field(default=15, ge=5, le=50, description="止损阈值(%)")
    take_profit: Optional[float] = Field(None, ge=10, le=200, description="止盈阈值(%)")


# ==================== Step 4: Risk 风险层配置 (新增) ====================

class CircuitBreakerLevel(BaseModel):
    """熔断级别"""
    level: Literal[1, 2, 3] = Field(..., description="熔断级别")
    trigger_type: Literal["daily_loss", "drawdown"] = Field(..., description="触发类型")
    threshold: float = Field(..., description="触发阈值(%)")
    action: Literal["notify", "pause_new", "full_stop"] = Field(..., description="触发动作")


class RiskConfig(BaseModel):
    """Step 4: 风险层配置"""
    max_single_position: float = Field(default=5, ge=1, le=50, description="最大单股仓位(%)")
    max_industry_position: float = Field(default=20, ge=5, le=100, description="最大行业仓位(%)")
    max_drawdown: float = Field(default=15, ge=5, le=50, description="最大回撤(%)")
    max_volatility: Optional[float] = Field(None, ge=5, le=100, description="最大波动率(%)")
    max_var: Optional[float] = Field(None, ge=1, le=20, description="最大VaR(%)")
    circuit_breakers: List[CircuitBreakerLevel] = Field(
        default_factory=lambda: [
            CircuitBreakerLevel(level=1, trigger_type="daily_loss", threshold=3, action="notify"),
            CircuitBreakerLevel(level=2, trigger_type="daily_loss", threshold=5, action="pause_new"),
            CircuitBreakerLevel(level=3, trigger_type="drawdown", threshold=15, action="full_stop"),
        ],
        description="熔断规则(不可关闭)"
    )
    enable_risk_monitor: bool = Field(True, description="启用风险监控")


# ==================== Step 5: Portfolio 组合层配置 ====================

class PortfolioConfig(BaseModel):
    """Step 5: 组合层配置"""
    optimizer: WeightOptimizer = Field(default=WeightOptimizer.EQUAL_WEIGHT, description="优化方法")
    rebalance_frequency: RebalanceFrequency = Field(default=RebalanceFrequency.MONTHLY, description="调仓频率")
    min_holdings: int = Field(default=10, ge=5, description="最小持仓数")
    max_holdings: int = Field(default=50, le=200, description="最大持仓数")
    max_turnover: float = Field(default=100, ge=0, le=500, description="最大换手率(%)")
    long_only: bool = Field(True, description="仅做多")
    cash_ratio: float = Field(default=5, ge=0, le=50, description="现金比例(%)")


# ==================== Step 6: Execution 执行层配置 ====================

class BrokerConfig(BaseModel):
    """券商配置"""
    broker: Literal["alpaca", "interactive_brokers"] = Field(..., description="券商")
    api_key: Optional[str] = Field(None, description="API Key")
    secret_key: Optional[str] = Field(None, description="Secret Key")


class ExecutionConfig(BaseModel):
    """Step 6: 执行层配置"""
    commission_rate: float = Field(default=0.1, ge=0, le=1, description="手续费率(%)")
    slippage_model: SlippageModel = Field(default=SlippageModel.FIXED, description="滑点模型")
    slippage_rate: float = Field(default=0.1, ge=0, le=2, description="滑点率(%)")
    algorithm: ExecutionAlgorithm = Field(default=ExecutionAlgorithm.MARKET, description="执行算法")
    paper_trade: bool = Field(True, description="模拟交易")
    broker_config: Optional[BrokerConfig] = Field(None, description="券商配置")


# ==================== Step 7: Monitor 监控层配置 ====================

class AlertRule(BaseModel):
    """告警规则"""
    id: str = Field(..., description="规则ID")
    type: AlertType = Field(..., description="告警类型")
    threshold: float = Field(..., description="阈值")
    channels: List[NotifyChannel] = Field(default_factory=list, description="通知渠道")
    enabled: bool = Field(True, description="是否启用")


class MonitorMetric(BaseModel):
    """监控指标"""
    name: str = Field(..., description="指标名称")
    show_on_dashboard: bool = Field(True, description="是否显示在仪表盘")
    refresh_interval: int = Field(60, description="刷新间隔(秒)")


class MonitorConfig(BaseModel):
    """Step 7: 监控层配置"""
    alerts: List[AlertRule] = Field(default_factory=list, description="告警规则")
    metrics: List[MonitorMetric] = Field(default_factory=list, description="监控指标")
    enable_realtime: bool = Field(True, description="启用实时监控")
    report_frequency: Literal["daily", "weekly", "monthly"] = Field("weekly", description="报告频率")


# ==================== 完整策略配置 ====================

class StrategyConfigV2(BaseModel):
    """完整7步策略配置"""
    # 基本信息
    id: Optional[str] = Field(None, description="策略ID")
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    description: str = Field("", max_length=500, description="策略描述")
    status: StrategyStatus = Field(default=StrategyStatus.DRAFT, description="策略状态")

    # 7步配置
    universe: UniverseConfig = Field(default_factory=UniverseConfig, description="Step 1: 投资池")
    alpha: AlphaConfig = Field(default_factory=AlphaConfig, description="Step 2: 因子层")
    signal: SignalConfig = Field(default_factory=SignalConfig, description="Step 3: 信号层")
    risk: RiskConfig = Field(default_factory=RiskConfig, description="Step 4: 风险层")
    portfolio: PortfolioConfig = Field(default_factory=PortfolioConfig, description="Step 5: 组合层")
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig, description="Step 6: 执行层")
    monitor: MonitorConfig = Field(default_factory=MonitorConfig, description="Step 7: 监控层")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "动量价值双因子策略",
                "description": "结合动量和价值因子的多因子策略",
                "status": "draft",
                "universe": {
                    "base_pool": "SP500",
                    "market_cap": {"min": 10, "max": None},
                    "avg_volume": 500,
                    "listing_age": 1,
                    "exclude_sectors": ["utilities", "real_estate"]
                },
                "alpha": {
                    "factors": [
                        {"factor_id": "momentum_20d", "expression": "close / delay(close, 20) - 1", "direction": 1, "lookback_period": 20},
                        {"factor_id": "value_pb", "expression": "1 / pb_ratio", "direction": 1, "lookback_period": 1}
                    ],
                    "combine_method": "equal_weight",
                    "normalize": "zscore",
                    "neutralize": "sector"
                },
                "signal": {
                    "signal_type": "long_only",
                    "target_positions": 20,
                    "stop_loss": 15
                },
                "risk": {
                    "max_single_position": 5,
                    "max_industry_position": 20,
                    "max_drawdown": 15
                },
                "portfolio": {
                    "optimizer": "equal_weight",
                    "rebalance_frequency": "monthly",
                    "min_holdings": 15,
                    "max_holdings": 30
                },
                "execution": {
                    "commission_rate": 0.1,
                    "slippage_rate": 0.1,
                    "paper_trade": True
                },
                "monitor": {
                    "enable_realtime": True,
                    "report_frequency": "weekly"
                }
            }
        }


# ==================== API 请求/响应模型 ====================

class StrategyCreateRequest(BaseModel):
    """创建策略请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    config: StrategyConfigV2


class StrategyUpdateRequest(BaseModel):
    """更新策略请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[StrategyStatus] = None
    universe: Optional[UniverseConfig] = None
    alpha: Optional[AlphaConfig] = None
    signal: Optional[SignalConfig] = None
    risk: Optional[RiskConfig] = None
    portfolio: Optional[PortfolioConfig] = None
    execution: Optional[ExecutionConfig] = None
    monitor: Optional[MonitorConfig] = None


class StrategyResponse(BaseModel):
    """策略响应"""
    id: str
    name: str
    description: str
    status: StrategyStatus
    created_at: str
    updated_at: str
    config: StrategyConfigV2


class StrategyListResponse(BaseModel):
    """策略列表响应"""
    total: int
    strategies: List[StrategyResponse]
