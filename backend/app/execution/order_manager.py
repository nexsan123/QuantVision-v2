"""
订单管理器

管理订单生命周期:
创建 -> 验证 -> 发送 -> 成交/取消
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger()


class OrderSide(str, Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """订单类型"""
    MARKET = "market"           # 市价单
    LIMIT = "limit"             # 限价单
    STOP = "stop"               # 止损单
    STOP_LIMIT = "stop_limit"   # 止损限价单
    TRAILING_STOP = "trailing_stop"  # 追踪止损


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"         # 待发送
    SUBMITTED = "submitted"     # 已提交
    ACCEPTED = "accepted"       # 已接受
    PARTIAL = "partial"         # 部分成交
    FILLED = "filled"           # 全部成交
    CANCELLED = "cancelled"     # 已取消
    REJECTED = "rejected"       # 被拒绝
    EXPIRED = "expired"         # 已过期


class TimeInForce(str, Enum):
    """订单有效期"""
    DAY = "day"                 # 当日有效
    GTC = "gtc"                 # 撤销前有效
    IOC = "ioc"                 # 立即成交或取消
    FOK = "fok"                 # 全部成交或取消
    OPG = "opg"                 # 开盘集合竞价
    CLS = "cls"                 # 收盘集合竞价


@dataclass
class Order:
    """订单"""
    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None
    stop_price: float | None = None
    time_in_force: TimeInForce = TimeInForce.DAY

    # 自动生成
    order_id: UUID = field(default_factory=uuid4)
    client_order_id: str = ""
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # 成交信息
    filled_quantity: float = 0.0
    filled_avg_price: float = 0.0
    filled_at: datetime | None = None

    # 执行信息
    broker_order_id: str | None = None
    execution_algo: str | None = None
    parent_order_id: UUID | None = None

    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.client_order_id:
            self.client_order_id = f"CLT_{self.order_id.hex[:8]}"

    @property
    def is_active(self) -> bool:
        """是否活跃"""
        return self.status in {
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIAL,
        }

    @property
    def is_done(self) -> bool:
        """是否完成"""
        return self.status in {
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED,
        }

    @property
    def remaining_quantity(self) -> float:
        """剩余数量"""
        return self.quantity - self.filled_quantity

    @property
    def fill_rate(self) -> float:
        """成交率"""
        return self.filled_quantity / self.quantity if self.quantity > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "order_id": str(self.order_id),
            "client_order_id": self.client_order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "limit_price": self.limit_price,
            "stop_price": self.stop_price,
            "time_in_force": self.time_in_force.value,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "filled_avg_price": self.filled_avg_price,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class OrderEvent:
    """订单事件"""
    order_id: UUID
    event_type: str             # "submitted", "filled", "cancelled", etc.
    timestamp: datetime = field(default_factory=datetime.now)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Fill:
    """成交"""
    order_id: UUID
    fill_id: str
    quantity: float
    price: float
    timestamp: datetime
    commission: float = 0.0
    exchange: str = ""


class OrderManager:
    """
    订单管理器

    管理订单的完整生命周期

    使用示例:
    ```python
    manager = OrderManager()

    # 创建订单
    order = manager.create_order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=100,
        order_type=OrderType.LIMIT,
        limit_price=150.0,
    )

    # 提交订单
    await manager.submit_order(order.order_id)

    # 监听事件
    manager.on_event = lambda e: print(f"Event: {e.event_type}")
    ```
    """

    def __init__(
        self,
        broker_client: Any = None,
        on_event: Callable[[OrderEvent], None] | None = None,
    ):
        """
        Args:
            broker_client: 券商客户端
            on_event: 事件回调
        """
        self.broker_client = broker_client
        self.on_event = on_event

        self._orders: dict[UUID, Order] = {}
        self._fills: list[Fill] = []
        self._events: list[OrderEvent] = []

    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: float | None = None,
        stop_price: float | None = None,
        time_in_force: TimeInForce = TimeInForce.DAY,
        metadata: dict[str, Any] | None = None,
    ) -> Order:
        """
        创建订单

        Args:
            symbol: 标的代码
            side: 方向
            quantity: 数量
            order_type: 订单类型
            limit_price: 限价
            stop_price: 止损价
            time_in_force: 有效期
            metadata: 元数据

        Returns:
            订单对象
        """
        if quantity <= 0:
            raise ValueError("数量必须大于 0")

        if order_type == OrderType.LIMIT and limit_price is None:
            raise ValueError("限价单必须指定限价")

        if order_type in {OrderType.STOP, OrderType.STOP_LIMIT} and stop_price is None:
            raise ValueError("止损单必须指定止损价")

        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            metadata=metadata or {},
        )

        self._orders[order.order_id] = order
        self._emit_event(order.order_id, "created")

        logger.info(
            "订单已创建",
            order_id=str(order.order_id)[:8],
            symbol=symbol,
            side=side.value,
            quantity=quantity,
            order_type=order_type.value,
        )

        return order

    async def submit_order(self, order_id: UUID) -> bool:
        """
        提交订单

        Args:
            order_id: 订单ID

        Returns:
            是否成功
        """
        order = self._orders.get(order_id)
        if order is None:
            logger.error("订单不存在", order_id=str(order_id))
            return False

        if order.status != OrderStatus.PENDING:
            logger.warning("订单状态不允许提交", status=order.status.value)
            return False

        try:
            if self.broker_client:
                # 实际提交到券商
                result = await self._submit_to_broker(order)
                if result:
                    order.broker_order_id = result.get("order_id")
            else:
                # 模拟模式
                await asyncio.sleep(0.01)

            order.status = OrderStatus.SUBMITTED
            order.updated_at = datetime.now()
            self._emit_event(order_id, "submitted")

            logger.info("订单已提交", order_id=str(order_id)[:8])
            return True

        except Exception as e:
            order.status = OrderStatus.REJECTED
            order.updated_at = datetime.now()
            order.metadata["reject_reason"] = str(e)
            self._emit_event(order_id, "rejected", {"reason": str(e)})

            logger.error("订单提交失败", order_id=str(order_id)[:8], error=str(e))
            return False

    async def cancel_order(self, order_id: UUID) -> bool:
        """
        取消订单

        Args:
            order_id: 订单ID

        Returns:
            是否成功
        """
        order = self._orders.get(order_id)
        if order is None:
            return False

        if not order.is_active:
            logger.warning("订单无法取消", status=order.status.value)
            return False

        try:
            if self.broker_client and order.broker_order_id:
                await self._cancel_from_broker(order)

            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.now()
            self._emit_event(order_id, "cancelled")

            logger.info("订单已取消", order_id=str(order_id)[:8])
            return True

        except Exception as e:
            logger.error("订单取消失败", order_id=str(order_id)[:8], error=str(e))
            return False

    def update_fill(
        self,
        order_id: UUID,
        fill_quantity: float,
        fill_price: float,
        fill_id: str = "",
        commission: float = 0.0,
    ) -> None:
        """
        更新成交

        Args:
            order_id: 订单ID
            fill_quantity: 成交数量
            fill_price: 成交价格
            fill_id: 成交ID
            commission: 佣金
        """
        order = self._orders.get(order_id)
        if order is None:
            return

        # 记录成交
        fill = Fill(
            order_id=order_id,
            fill_id=fill_id or f"FILL_{len(self._fills)}",
            quantity=fill_quantity,
            price=fill_price,
            timestamp=datetime.now(),
            commission=commission,
        )
        self._fills.append(fill)

        # 更新订单
        old_filled = order.filled_quantity
        order.filled_quantity += fill_quantity
        order.filled_avg_price = (
            (old_filled * order.filled_avg_price + fill_quantity * fill_price)
            / order.filled_quantity
        )
        order.updated_at = datetime.now()

        if order.filled_quantity >= order.quantity:
            order.status = OrderStatus.FILLED
            order.filled_at = datetime.now()
            self._emit_event(order_id, "filled")
        else:
            order.status = OrderStatus.PARTIAL
            self._emit_event(order_id, "partial_fill", {
                "fill_quantity": fill_quantity,
                "fill_price": fill_price,
            })

        logger.info(
            "订单成交更新",
            order_id=str(order_id)[:8],
            filled=f"{order.filled_quantity}/{order.quantity}",
            avg_price=f"{order.filled_avg_price:.2f}",
        )

    def get_order(self, order_id: UUID) -> Order | None:
        """获取订单"""
        return self._orders.get(order_id)

    def get_active_orders(self, symbol: str | None = None) -> list[Order]:
        """获取活跃订单"""
        orders = [o for o in self._orders.values() if o.is_active]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders

    def get_orders_by_symbol(self, symbol: str) -> list[Order]:
        """获取标的的所有订单"""
        return [o for o in self._orders.values() if o.symbol == symbol]

    def get_fills(self, order_id: UUID | None = None) -> list[Fill]:
        """获取成交"""
        if order_id:
            return [f for f in self._fills if f.order_id == order_id]
        return self._fills

    def _emit_event(
        self,
        order_id: UUID,
        event_type: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """发送事件"""
        event = OrderEvent(
            order_id=order_id,
            event_type=event_type,
            details=details or {},
        )
        self._events.append(event)

        if self.on_event:
            self.on_event(event)

    async def _submit_to_broker(self, order: Order) -> dict[str, Any]:
        """提交到券商 (需要实现)"""
        # 这里应该调用实际的券商 API
        raise NotImplementedError("需要实现券商接口")

    async def _cancel_from_broker(self, order: Order) -> None:
        """从券商取消 (需要实现)"""
        raise NotImplementedError("需要实现券商接口")


class OrderBook:
    """
    订单簿

    模拟订单簿用于回测
    """

    def __init__(self):
        self.bids: list[tuple[float, float]] = []  # [(price, quantity), ...]
        self.asks: list[tuple[float, float]] = []

    def update(
        self,
        bid_prices: list[float],
        bid_sizes: list[float],
        ask_prices: list[float],
        ask_sizes: list[float],
    ) -> None:
        """更新订单簿"""
        self.bids = list(zip(bid_prices, bid_sizes))
        self.asks = list(zip(ask_prices, ask_sizes))

    @property
    def best_bid(self) -> float | None:
        """最优买价"""
        return self.bids[0][0] if self.bids else None

    @property
    def best_ask(self) -> float | None:
        """最优卖价"""
        return self.asks[0][0] if self.asks else None

    @property
    def mid_price(self) -> float | None:
        """中间价"""
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None

    @property
    def spread(self) -> float | None:
        """买卖价差"""
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None

    @property
    def spread_bps(self) -> float | None:
        """买卖价差 (基点)"""
        if self.spread and self.mid_price:
            return self.spread / self.mid_price * 10000
        return None

    def get_market_impact(self, side: OrderSide, quantity: float) -> float:
        """
        估算市场冲击

        Args:
            side: 方向
            quantity: 数量

        Returns:
            预计成交均价
        """
        book = self.asks if side == OrderSide.BUY else self.bids
        if not book:
            return 0.0

        remaining = quantity
        total_cost = 0.0

        for price, size in book:
            fill = min(remaining, size)
            total_cost += fill * price
            remaining -= fill
            if remaining <= 0:
                break

        filled = quantity - remaining
        return total_cost / filled if filled > 0 else book[0][0]
