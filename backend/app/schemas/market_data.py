"""
Phase 11: \u6570\u636e\u5c42\u5347\u7ea7 - \u5e02\u573a\u6570\u636e Pydantic Schema

\u5305\u542b:
- \u5206\u949f\u7ea7 K \u7ebf\u6570\u636e\u6a21\u578b
- \u5b9e\u65f6\u884c\u60c5\u6a21\u578b
- \u65e5\u5185\u56e0\u5b50\u6a21\u578b
- \u6570\u636e\u8d28\u91cf\u6a21\u578b
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============ \u679a\u4e3e\u7c7b\u578b ============

class DataSource(str, Enum):
    """\u6570\u636e\u6e90"""
    POLYGON = "polygon"
    ALPACA = "alpaca"
    IEX = "iex"
    YAHOO = "yahoo"


class DataFrequency(str, Enum):
    """\u6570\u636e\u9891\u7387"""
    MIN_1 = "1min"
    MIN_5 = "5min"
    MIN_15 = "15min"
    MIN_30 = "30min"
    HOUR_1 = "1hour"
    DAY_1 = "1day"


class DataSourceStatus(str, Enum):
    """\u6570\u636e\u6e90\u72b6\u6001"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class DataSyncStatus(str, Enum):
    """\u6570\u636e\u540c\u6b65\u72b6\u6001"""
    SYNCED = "synced"
    SYNCING = "syncing"
    ERROR = "error"
    STALE = "stale"


class DataQualityIssueType(str, Enum):
    """\u6570\u636e\u8d28\u91cf\u95ee\u9898\u7c7b\u578b"""
    MISSING_DATA = "missing_data"
    OUTLIER = "outlier"
    STALE_DATA = "stale_data"
    INVALID_OHLC = "invalid_ohlc"
    ZERO_VOLUME = "zero_volume"
    PRICE_GAP = "price_gap"
    DUPLICATE = "duplicate"


class IntradayFactorType(str, Enum):
    """\u65e5\u5185\u56e0\u5b50\u7c7b\u578b"""
    RELATIVE_VOLUME = "relative_volume"
    VWAP_DEVIATION = "vwap_deviation"
    BUY_PRESSURE = "buy_pressure"
    PRICE_MOMENTUM_5MIN = "price_momentum_5min"
    PRICE_MOMENTUM_15MIN = "price_momentum_15min"
    INTRADAY_VOLATILITY = "intraday_volatility"
    SPREAD_RATIO = "spread_ratio"
    ORDER_IMBALANCE = "order_imbalance"


# ============ K\u7ebf\u6570\u636e\u6a21\u578b ============

class OHLCVBar(BaseModel):
    """OHLCV K\u7ebf\u6570\u636e"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float | None = None
    trades: int | None = None


class MinuteBar(OHLCVBar):
    """\u5206\u949f\u7ea7K\u7ebf"""
    frequency: DataFrequency = DataFrequency.MIN_1
    pre_market: bool = False
    after_hours: bool = False
    day_open: float | None = None
    day_high: float | None = None
    day_low: float | None = None
    day_volume: float | None = None


class DailyBar(OHLCVBar):
    """\u65e5\u7ebfK\u7ebf"""
    adj_close: float | None = None
    dividend: float | None = None
    split: float | None = None


# ============ \u5b9e\u65f6\u884c\u60c5\u6a21\u578b ============

class Quote(BaseModel):
    """\u5b9e\u65f6\u62a5\u4ef7"""
    symbol: str
    timestamp: datetime
    bid_price: float
    bid_size: int
    ask_price: float
    ask_size: int
    last_price: float
    last_size: int
    volume: float


class Trade(BaseModel):
    """\u5b9e\u65f6\u6210\u4ea4"""
    symbol: str
    timestamp: datetime
    price: float
    size: int
    exchange: str
    conditions: list[str] | None = None


class MarketSnapshot(BaseModel):
    """\u5e02\u573a\u5feb\u7167"""
    symbol: str
    timestamp: datetime

    # \u4ef7\u683c
    last_price: float
    change: float
    change_percent: float

    # \u5f53\u65e5\u7edf\u8ba1
    open: float
    high: float
    low: float
    close: float
    previous_close: float
    volume: float

    # \u62a5\u4ef7
    bid_price: float
    bid_size: int
    ask_price: float
    ask_size: int

    # \u884d\u751f\u6307\u6807
    vwap: float | None = None
    average_volume: float | None = None
    relative_volume: float | None = None


# ============ \u65e5\u5185\u56e0\u5b50\u6a21\u578b ============

class IntradayFactorDefinition(BaseModel):
    """\u65e5\u5185\u56e0\u5b50\u5b9a\u4e49"""
    id: IntradayFactorType
    name: str
    description: str
    expression: str
    interpretation: str
    lookback_period: int = Field(..., description="\u56de\u770b\u5468\u671f(\u5206\u949f)")
    update_frequency: DataFrequency


class IntradayFactorValue(BaseModel):
    """\u65e5\u5185\u56e0\u5b50\u503c"""
    symbol: str
    timestamp: datetime
    factor_id: IntradayFactorType
    value: float
    zscore: float | None = None
    percentile: float | None = None


class IntradayFactorSnapshot(BaseModel):
    """\u65e5\u5185\u56e0\u5b50\u5feb\u7167"""
    symbol: str
    timestamp: datetime
    factors: dict[str, float]


# ============ \u6570\u636e\u6e90\u6a21\u578b ============

class DataSourceCapabilities(BaseModel):
    """\u6570\u636e\u6e90\u80fd\u529b"""
    realtime: bool = False
    historical: bool = True
    intraday: bool = False
    fundamentals: bool = False


class DataSourceConfig(BaseModel):
    """\u6570\u636e\u6e90\u914d\u7f6e"""
    source: DataSource
    api_key: str | None = None
    base_url: str | None = None
    ws_url: str | None = None
    rate_limit: int = Field(100, description="\u6bcf\u5206\u949f\u8bf7\u6c42\u6570")
    priority: int = Field(1, description="\u4f18\u5148\u7ea7")
    capabilities: DataSourceCapabilities = Field(default_factory=DataSourceCapabilities)


class DataSourceInfo(BaseModel):
    """\u6570\u636e\u6e90\u72b6\u6001\u4fe1\u606f"""
    source: DataSource
    status: DataSourceStatus
    last_sync: datetime | None = None
    requests_today: int = 0
    requests_limit: int
    latency_ms: float = 0
    error_message: str | None = None


# ============ \u6570\u636e\u8bf7\u6c42/\u54cd\u5e94\u6a21\u578b ============

class HistoricalDataRequest(BaseModel):
    """\u5386\u53f2\u6570\u636e\u8bf7\u6c42"""
    symbols: list[str]
    frequency: DataFrequency = DataFrequency.DAY_1
    start_date: str
    end_date: str
    adjusted_price: bool = True
    include_pre_post: bool = False
    data_source: DataSource | None = None


class HistoricalDataResponse(BaseModel):
    """\u5386\u53f2\u6570\u636e\u54cd\u5e94"""
    symbol: str
    frequency: DataFrequency
    bars: list[OHLCVBar]
    total_count: int
    data_source: DataSource


class StreamSubscription(BaseModel):
    """\u5b9e\u65f6\u8ba2\u9605\u8bf7\u6c42"""
    symbols: list[str]
    data_types: list[str] = Field(default_factory=lambda: ["quotes", "trades"])
    frequency: DataFrequency | None = None


class SymbolSyncStatus(BaseModel):
    """\u5355\u4e2a\u80a1\u7968\u540c\u6b65\u72b6\u6001"""
    symbol: str
    last_sync_time: datetime | None
    oldest_data: datetime | None
    newest_data: datetime | None
    total_bars: int = 0
    frequency: DataFrequency
    status: DataSyncStatus
    progress: float | None = None


# ============ \u6570\u636e\u8d28\u91cf\u6a21\u578b ============

class DataQualityIssue(BaseModel):
    """\u6570\u636e\u8d28\u91cf\u95ee\u9898"""
    id: str
    symbol: str
    timestamp: datetime
    issue_type: DataQualityIssueType
    severity: str = Field(..., pattern="^(low|medium|high)$")
    description: str
    affected_fields: list[str] = Field(default_factory=list)
    resolved: bool = False
    resolved_at: datetime | None = None


class DataQualityReport(BaseModel):
    """\u6570\u636e\u8d28\u91cf\u62a5\u544a"""
    report_date: datetime
    symbols_checked: int
    bars_checked: int
    issues_found: int
    issues_by_type: dict[str, int] = Field(default_factory=dict)
    issues_by_severity: dict[str, int] = Field(default_factory=dict)
    overall_score: float = Field(..., ge=0, le=100)
    issues: list[DataQualityIssue] = Field(default_factory=list)


# ============ API \u54cd\u5e94\u6a21\u578b ============

class DataSourceListResponse(BaseModel):
    """\u6570\u636e\u6e90\u5217\u8868\u54cd\u5e94"""
    sources: list[DataSourceInfo]
    primary_source: DataSource


class SyncStatusResponse(BaseModel):
    """\u540c\u6b65\u72b6\u6001\u54cd\u5e94"""
    symbols: list[SymbolSyncStatus]
    total_symbols: int
    synced_count: int
    syncing_count: int
    error_count: int


class IntradayFactorsResponse(BaseModel):
    """\u65e5\u5185\u56e0\u5b50\u54cd\u5e94"""
    snapshots: list[IntradayFactorSnapshot]
    timestamp: datetime
    factors_calculated: list[str]


# ============ \u9884\u7f6e\u65e5\u5185\u56e0\u5b50 ============

INTRADAY_FACTOR_DEFINITIONS = [
    IntradayFactorDefinition(
        id=IntradayFactorType.RELATIVE_VOLUME,
        name="\u76f8\u5bf9\u6210\u4ea4\u91cf",
        description="\u5f53\u524d10\u5206\u949f\u6210\u4ea4\u91cf / \u8fc7\u53bb20\u5929\u540c\u65f6\u6bb5\u5e73\u5747",
        expression="volume_10min / avg(volume_10min, 20)",
        interpretation=">2.0 \u663e\u8457\u653e\u91cf, <0.5 \u663e\u8457\u7f29\u91cf",
        lookback_period=10,
        update_frequency=DataFrequency.MIN_1,
    ),
    IntradayFactorDefinition(
        id=IntradayFactorType.VWAP_DEVIATION,
        name="VWAP\u504f\u79bb",
        description="\u5f53\u524d\u4ef7\u683c\u76f8\u5bf9VWAP\u7684\u504f\u79bb\u7a0b\u5ea6",
        expression="(close - vwap) / vwap",
        interpretation=">0 \u4e70\u538b\u5f3a, <0 \u5356\u538b\u5f3a",
        lookback_period=0,
        update_frequency=DataFrequency.MIN_1,
    ),
    IntradayFactorDefinition(
        id=IntradayFactorType.BUY_PRESSURE,
        name="\u4e70\u5356\u538b\u529b",
        description="\u4e3b\u52a8\u4e70\u5165\u91cf\u5360\u6bd4",
        expression="buy_volume / (buy_volume + sell_volume)",
        interpretation=">0.6 \u4e70\u538b\u5f3a, <0.4 \u5356\u538b\u5f3a",
        lookback_period=10,
        update_frequency=DataFrequency.MIN_1,
    ),
    IntradayFactorDefinition(
        id=IntradayFactorType.PRICE_MOMENTUM_5MIN,
        name="5\u5206\u949f\u52a8\u91cf",
        description="5\u5206\u949f\u4ef7\u683c\u53d8\u5316\u7387",
        expression="close / delay(close, 5) - 1",
        interpretation="\u6b63\u503c\u8868\u793a\u4e0a\u6da8\u52a8\u91cf",
        lookback_period=5,
        update_frequency=DataFrequency.MIN_1,
    ),
    IntradayFactorDefinition(
        id=IntradayFactorType.PRICE_MOMENTUM_15MIN,
        name="15\u5206\u949f\u52a8\u91cf",
        description="15\u5206\u949f\u4ef7\u683c\u53d8\u5316\u7387",
        expression="close / delay(close, 15) - 1",
        interpretation="\u6b63\u503c\u8868\u793a\u4e0a\u6da8\u52a8\u91cf",
        lookback_period=15,
        update_frequency=DataFrequency.MIN_1,
    ),
    IntradayFactorDefinition(
        id=IntradayFactorType.INTRADAY_VOLATILITY,
        name="\u65e5\u5185\u6ce2\u52a8",
        description="\u5f53\u65e5\u4ef7\u683c\u6ce2\u52a8\u7387",
        expression="std(returns_1min, today) * sqrt(390)",
        interpretation="\u5e74\u5316\u65e5\u5185\u6ce2\u52a8\u7387",
        lookback_period=390,
        update_frequency=DataFrequency.MIN_5,
    ),
    IntradayFactorDefinition(
        id=IntradayFactorType.SPREAD_RATIO,
        name="\u4e70\u5356\u4ef7\u5dee\u6bd4",
        description="\u4e70\u5356\u4ef7\u5dee\u5360\u4e2d\u95f4\u4ef7\u6bd4\u4f8b",
        expression="(ask - bid) / ((ask + bid) / 2)",
        interpretation="\u8d8a\u5927\u8868\u793a\u6d41\u52a8\u6027\u8d8a\u5dee",
        lookback_period=0,
        update_frequency=DataFrequency.MIN_1,
    ),
    IntradayFactorDefinition(
        id=IntradayFactorType.ORDER_IMBALANCE,
        name="\u8ba2\u5355\u4e0d\u5e73\u8861",
        description="\u4e70\u5356\u76d8\u53e3\u4e0d\u5e73\u8861\u5ea6",
        expression="(bid_size - ask_size) / (bid_size + ask_size)",
        interpretation=">0 \u4e70\u76d8\u5f3a, <0 \u5356\u76d8\u5f3a",
        lookback_period=0,
        update_frequency=DataFrequency.MIN_1,
    ),
]
