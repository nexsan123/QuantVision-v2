"""
盘前扫描 Schema
PRD 4.18.0 盘前扫描器
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class PreMarketScanFilter(BaseModel):
    """盘前扫描筛选条件"""
    min_gap: float = Field(default=0.02, description="最小Gap (默认2%)")
    min_premarket_volume: float = Field(default=2.0, description="盘前成交量倍数 (默认2倍日均)")
    min_volatility: float = Field(default=0.03, description="最小昨日波动率 (默认3%)")
    min_liquidity: float = Field(default=5000000, description="最小流动性 (默认$5M/日)")
    has_news: Optional[bool] = Field(None, description="是否有新闻")
    is_earnings_day: Optional[bool] = Field(None, description="是否财报日")


class ScoreBreakdown(BaseModel):
    """评分明细"""
    gap: float
    volume: float
    volatility: float
    news: float
    weights: dict = {"gap": 0.3, "volume": 0.3, "volatility": 0.2, "news": 1.0}


class PreMarketStock(BaseModel):
    """盘前扫描股票"""
    symbol: str
    name: str

    # 盘前数据
    gap: float  # 开盘跳空 (%)
    gap_direction: str  # 'up' | 'down'
    premarket_price: float  # 盘前价格
    premarket_volume: int  # 盘前成交量
    premarket_volume_ratio: float  # 相对日均量倍数

    # 昨日数据
    prev_close: float
    prev_volume: int
    volatility: float  # 昨日波动率 (ATR%)

    # 流动性
    avg_daily_volume: int
    avg_daily_value: float  # 日均成交额

    # 新闻/事件
    has_news: bool
    news_headline: Optional[str] = None
    is_earnings_day: bool = False

    # 评分
    score: float  # 策略评分 0-100
    score_breakdown: ScoreBreakdown


class PreMarketScanResult(BaseModel):
    """盘前扫描结果"""
    scan_time: datetime
    strategy_id: str
    strategy_name: str

    filters_applied: PreMarketScanFilter
    total_matched: int
    stocks: list[PreMarketStock]

    # AI建议
    ai_suggestion: Optional[str] = None


class IntradayWatchlist(BaseModel):
    """日内交易监控列表"""
    watchlist_id: str
    user_id: str
    strategy_id: str
    date: date
    symbols: list[str]
    created_at: datetime
    is_confirmed: bool = False


class CreateWatchlistRequest(BaseModel):
    """创建监控列表请求"""
    strategy_id: str
    symbols: list[str] = Field(..., max_length=20)


class TimeStopConfig(BaseModel):
    """时间止损配置"""
    enabled: bool = True
    time: str = "15:55"  # HH:mm format, 收盘前5分钟


class StopLossConfig(BaseModel):
    """止盈止损配置"""
    # 止损设置
    stop_loss_type: str = "atr"  # 'atr' | 'fixed' | 'percentage' | 'technical'
    stop_loss_value: float = 1.5

    # 止盈设置
    take_profit_type: str = "atr"
    take_profit_value: float = 2.5

    # 时间止损 (日内专属)
    time_stop_enabled: bool = True
    time_stop_time: str = "15:55"

    # 移动止损
    trailing_stop_enabled: bool = False
    trailing_trigger_pct: float = 0.5
    trailing_distance_pct: float = 0.3


class IntradayPosition(BaseModel):
    """日内持仓"""
    position_id: str
    user_id: str
    account_id: str
    strategy_id: str

    symbol: str
    quantity: int
    entry_price: float
    current_price: float
    avg_cost: float

    pnl: float
    pnl_pct: float

    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    time_stop_config: Optional[TimeStopConfig] = None

    entry_time: datetime
    is_intraday: bool = True
