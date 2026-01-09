"""
手动交易 Schema
PRD 4.16 实时交易监控界面
"""
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class OrderSide(str, Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    PARTIAL = "partial"


class ManualTradeOrder(BaseModel):
    """手动交易订单"""
    order_id: str
    user_id: str
    account_id: str
    strategy_id: Optional[str] = None  # 可选归属策略

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None

    # 止盈止损 (买入时设置)
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None

    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[float] = None

    # 费用
    commission: float = 0.0
    total_cost: float = 0.0

    created_at: datetime
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class PlaceOrderRequest(BaseModel):
    """下单请求"""
    symbol: str = Field(..., description="股票代码")
    side: Literal["buy", "sell"] = Field(..., description="买/卖方向")
    order_type: Literal["market", "limit", "stop"] = Field(
        default="market", description="订单类型"
    )
    quantity: int = Field(..., ge=1, description="数量")
    strategy_id: Optional[str] = Field(None, description="归属策略ID")
    limit_price: Optional[float] = Field(None, ge=0, description="限价")
    stop_price: Optional[float] = Field(None, ge=0, description="止损价")
    take_profit: Optional[float] = Field(None, ge=0, description="止盈价")
    stop_loss: Optional[float] = Field(None, ge=0, description="止损价")


class PlaceOrderResponse(BaseModel):
    """下单响应"""
    success: bool
    order: Optional[ManualTradeOrder] = None
    error: Optional[str] = None
    pdt_warning: Optional[str] = None  # PDT 警告


class CancelOrderResponse(BaseModel):
    """取消订单响应"""
    success: bool
    message: str


class QuoteData(BaseModel):
    """报价数据"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: int
    change: float
    change_pct: float
    high: float
    low: float
    open: float
    prev_close: float
    timestamp: datetime


class OrderListRequest(BaseModel):
    """订单列表请求"""
    status: Optional[str] = None
    symbol: Optional[str] = None
    strategy_id: Optional[str] = None
    limit: int = Field(default=50, le=200)
    offset: int = Field(default=0, ge=0)


class OrderListResponse(BaseModel):
    """订单列表响应"""
    orders: list[ManualTradeOrder]
    total: int
    has_more: bool
