"""
Phase 12: \u6267\u884c\u5c42\u5347\u7ea7 - \u4ea4\u6613 Pydantic \u6a21\u578b

\u5305\u542b:
- \u5238\u5546\u63a5\u53e3\u6a21\u578b
- \u8ba2\u5355\u7ba1\u7406\u6a21\u578b
- \u6ed1\u70b9\u6a21\u578b
- \u6267\u884c\u7b97\u6cd5\u6a21\u578b
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ============ \u679a\u4e3e\u7c7b\u578b ============

class BrokerType(str, Enum):
    """\u5238\u5546\u7c7b\u578b"""
    ALPACA = "alpaca"
    INTERACTIVE_BROKERS = "interactive_brokers"
    PAPER = "paper"


class BrokerConnectionStatus(str, Enum):
    """\u5238\u5546\u8fde\u63a5\u72b6\u6001"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class OrderSide(str, Enum):
    """\u8ba2\u5355\u65b9\u5411"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """\u8ba2\u5355\u7c7b\u578b"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(str, Enum):
    """\u8ba2\u5355\u72b6\u6001"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(str, Enum):
    """\u8ba2\u5355\u6709\u6548\u671f"""
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"
    OPG = "opg"
    CLS = "cls"


class SlippageModelType(str, Enum):
    """\u6ed1\u70b9\u6a21\u578b\u7c7b\u578b"""
    FIXED = "fixed"
    VOLUME_BASED = "volume_based"
    SQRT = "sqrt"
    ALMGREN_CHRISS = "almgren_chriss"


class ExecutionAlgorithm(str, Enum):
    """\u6267\u884c\u7b97\u6cd5"""
    MARKET = "market"
    TWAP = "twap"
    VWAP = "vwap"
    POV = "pov"
    IS = "is"  # Implementation Shortfall


class MarketStatus(str, Enum):
    """\u5e02\u573a\u72b6\u6001"""
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"


# ============ \u5238\u5546\u6a21\u578b ============

class BrokerConfig(BaseModel):
    """\u5238\u5546\u914d\u7f6e"""
    broker: BrokerType
    api_key: str | None = None
    secret_key: str | None = None
    paper_trading: bool = True
    base_url: str | None = None


class BrokerAccount(BaseModel):
    """\u5238\u5546\u8d26\u6237"""
    id: str
    broker: BrokerType
    account_number: str
    status: str = "active"
    currency: str = "USD"
    buying_power: float
    cash: float
    portfolio_value: float
    equity: float
    last_equity: float = 0.0
    long_market_value: float = 0.0
    short_market_value: float = 0.0
    initial_margin: float = 0.0
    maintenance_margin: float = 0.0
    daytrade_count: int = 0
    pattern_day_trader: bool = False
    trading_blocked: bool = False
    transfers_blocked: bool = False
    account_blocked: bool = False
    created_at: datetime | None = None
    paper_trading: bool = True


class BrokerPosition(BaseModel):
    """\u5238\u5546\u6301\u4ed3"""
    symbol: str
    quantity: float
    side: str = "long"
    avg_entry_price: float
    market_value: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    cost_basis: float
    asset_class: str = "us_equity"
    exchange: str = ""


class BrokerStatusSummary(BaseModel):
    """\u5238\u5546\u72b6\u6001\u6458\u8981"""
    broker: BrokerType
    status: BrokerConnectionStatus
    paper_trading: bool
    account: dict[str, Any] | None = None
    market_status: MarketStatus = MarketStatus.CLOSED
    last_update: datetime


# ============ \u6ed1\u70b9\u6a21\u578b ============

class AlmgrenChrissParams(BaseModel):
    """Almgren-Chriss \u6ed1\u70b9\u6a21\u578b\u53c2\u6570"""
    eta: float = Field(0.3, ge=0.1, le=0.5, description="\u4e34\u65f6\u51b2\u51fb\u7cfb\u6570")
    gamma: float = Field(0.03, ge=0.01, le=0.1, description="\u6c38\u4e45\u51b2\u51fb\u7cfb\u6570")
    sigma: float = Field(0.02, ge=0.001, le=0.1, description="\u65e5\u6ce2\u52a8\u7387")
    spread_bps: float = Field(5.0, ge=0.0, description="\u4e70\u5356\u4ef7\u5dee (\u57fa\u70b9)")


class SlippageResult(BaseModel):
    """\u6ed1\u70b9\u8ba1\u7b97\u7ed3\u679c"""
    total_slippage: float = Field(..., description="\u603b\u6ed1\u70b9 (\u7edd\u5bf9\u503c)")
    fixed_cost: float = Field(..., description="\u56fa\u5b9a\u6210\u672c (spread/2)")
    temporary_impact: float = Field(..., description="\u4e34\u65f6\u51b2\u51fb")
    permanent_impact: float = Field(..., description="\u6c38\u4e45\u51b2\u51fb")
    slippage_bps: float = Field(..., description="\u6ed1\u70b9 (\u57fa\u70b9)")
    slippage_percent: float = Field(..., description="\u6ed1\u70b9 (\u767e\u5206\u6bd4)")


class SlippageConfig(BaseModel):
    """\u6ed1\u70b9\u914d\u7f6e"""
    model_type: SlippageModelType = SlippageModelType.ALMGREN_CHRISS
    fixed_rate: float = Field(0.001, ge=0.0, le=0.01)
    almgren_chriss: AlmgrenChrissParams | None = None


class SlippageEstimateRequest(BaseModel):
    """\u6ed1\u70b9\u4f30\u7b97\u8bf7\u6c42"""
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    daily_volume: float | None = None
    volatility: float | None = None
    config: SlippageConfig | None = None


# ============ \u6267\u884c\u7b97\u6cd5\u6a21\u578b ============

class TWAPParams(BaseModel):
    """TWAP \u53c2\u6570"""
    duration_minutes: int = Field(30, ge=1, le=480)
    interval_seconds: int = Field(60, ge=10, le=300)


class VWAPParams(BaseModel):
    """VWAP \u53c2\u6570"""
    start_time: str | None = None
    end_time: str | None = None
    participation_rate: float = Field(0.1, ge=0.01, le=0.5)


class POVParams(BaseModel):
    """POV \u53c2\u6570"""
    target_rate: float = Field(0.1, ge=0.01, le=0.3)
    max_rate: float = Field(0.25, ge=0.05, le=0.5)


class ExecutionConfig(BaseModel):
    """\u6267\u884c\u7b97\u6cd5\u914d\u7f6e"""
    algorithm: ExecutionAlgorithm = ExecutionAlgorithm.MARKET
    twap: TWAPParams | None = None
    vwap: VWAPParams | None = None
    pov: POVParams | None = None


# ============ \u8ba2\u5355\u6a21\u578b ============

class CreateOrderRequest(BaseModel):
    """\u521b\u5efa\u8ba2\u5355\u8bf7\u6c42"""
    symbol: str
    side: OrderSide
    quantity: float = Field(..., gt=0)
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = Field(None, gt=0)
    stop_price: float | None = Field(None, gt=0)
    time_in_force: TimeInForce = TimeInForce.DAY
    extended_hours: bool = False
    client_order_id: str | None = None
    execution: ExecutionConfig | None = None

    @field_validator("limit_price")
    @classmethod
    def validate_limit_price(cls, v: float | None, info) -> float | None:
        if info.data.get("order_type") == OrderType.LIMIT and v is None:
            raise ValueError("\u9650\u4ef7\u5355\u5fc5\u987b\u6307\u5b9a\u9650\u4ef7")
        return v

    @field_validator("stop_price")
    @classmethod
    def validate_stop_price(cls, v: float | None, info) -> float | None:
        order_type = info.data.get("order_type")
        if order_type in {OrderType.STOP, OrderType.STOP_LIMIT} and v is None:
            raise ValueError("\u6b62\u635f\u5355\u5fc5\u987b\u6307\u5b9a\u6b62\u635f\u4ef7")
        return v


class OrderResponse(BaseModel):
    """\u8ba2\u5355\u54cd\u5e94"""
    id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    quantity: float
    filled_quantity: float = 0.0
    order_type: OrderType
    status: OrderStatus
    limit_price: float | None = None
    stop_price: float | None = None
    filled_avg_price: float | None = None
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None = None
    filled_at: datetime | None = None
    cancelled_at: datetime | None = None
    expired_at: datetime | None = None
    broker: BrokerType
    broker_order_id: str | None = None
    commission: float = 0.0
    slippage: float = 0.0


class OrderUpdate(BaseModel):
    """\u8ba2\u5355\u66f4\u65b0"""
    order_id: str
    status: OrderStatus | None = None
    filled_quantity: float | None = None
    filled_avg_price: float | None = None


class CancelOrderRequest(BaseModel):
    """\u53d6\u6d88\u8ba2\u5355\u8bf7\u6c42"""
    order_id: str
    reason: str | None = None


# ============ \u4ea4\u6613\u7edf\u8ba1\u6a21\u578b ============

class TradingStats(BaseModel):
    """\u4ea4\u6613\u7edf\u8ba1"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_commission: float = 0.0
    total_slippage: float = 0.0
    avg_slippage_bps: float = 0.0
    avg_trade_size: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0


class TradeCostAnalysis(BaseModel):
    """\u4ea4\u6613\u6210\u672c\u5206\u6790 (TCA)"""
    symbol: str
    execution_price: float
    arrival_price: float
    benchmark_price: float
    implementation_shortfall: float
    implementation_shortfall_bps: float
    commission: float
    slippage: float
    market_impact: float
    timing_cost: float
    opportunity_cost: float


# ============ Paper Trading \u6a21\u578b ============

class PaperTradingConfig(BaseModel):
    """Paper Trading \u914d\u7f6e"""
    initial_capital: float = Field(100000.0, gt=0)
    commission_rate: float = Field(0.0, ge=0.0, le=0.01)
    slippage_config: SlippageConfig = SlippageConfig()
    allow_shorting: bool = False
    margin_rate: float = Field(0.5, ge=0.25, le=1.0)


class PaperTradingState(BaseModel):
    """Paper Trading \u72b6\u6001"""
    enabled: bool = False
    config: PaperTradingConfig
    account: BrokerAccount | None = None
    positions: list[BrokerPosition] = []
    orders: list[OrderResponse] = []
    trades_today: int = 0


# ============ API \u54cd\u5e94\u6a21\u578b ============

class BrokerListResponse(BaseModel):
    """\u5238\u5546\u5217\u8868\u54cd\u5e94"""
    brokers: list[dict[str, Any]]
    connected_broker: BrokerType | None = None


class AccountResponse(BaseModel):
    """\u8d26\u6237\u54cd\u5e94"""
    success: bool
    account: BrokerAccount | None = None
    error: str | None = None


class PositionsResponse(BaseModel):
    """\u6301\u4ed3\u54cd\u5e94"""
    success: bool
    positions: list[BrokerPosition] = []
    total_value: float = 0.0
    unrealized_pnl: float = 0.0


class OrdersResponse(BaseModel):
    """\u8ba2\u5355\u5217\u8868\u54cd\u5e94"""
    success: bool
    orders: list[OrderResponse] = []
    total: int = 0


class SubmitOrderResponse(BaseModel):
    """\u63d0\u4ea4\u8ba2\u5355\u54cd\u5e94"""
    success: bool
    order: OrderResponse | None = None
    estimated_slippage: SlippageResult | None = None
    error: str | None = None


class CancelOrderResponse(BaseModel):
    """\u53d6\u6d88\u8ba2\u5355\u54cd\u5e94"""
    success: bool
    order_id: str
    error: str | None = None
