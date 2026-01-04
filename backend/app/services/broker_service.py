"""
Phase 12: \u6267\u884c\u5c42\u5347\u7ea7 - \u5238\u5546\u670d\u52a1

\u652f\u6301\u7684\u5238\u5546:
- Alpaca (\u9996\u9009, \u514d\u8d39 API)
- Interactive Brokers (\u5907\u9009, \u4e13\u4e1a\u7ea7)
- Paper Trading (\u6a21\u62df\u4ea4\u6613)

\u529f\u80fd:
- \u7edf\u4e00\u7684\u5238\u5546\u63a5\u53e3
- \u8d26\u6237\u7ba1\u7406
- \u8ba2\u5355\u7ba1\u7406
- \u6301\u4ed3\u67e5\u8be2
- \u81ea\u52a8\u6545\u969c\u8f6c\u79fb
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

import httpx
import structlog

from app.core.config import settings
from app.schemas.trading import (
    BrokerType,
    BrokerConnectionStatus,
    BrokerAccount,
    BrokerPosition,
    BrokerStatusSummary,
    OrderSide,
    OrderType,
    OrderStatus,
    TimeInForce,
    CreateOrderRequest,
    OrderResponse,
    MarketStatus,
)

logger = structlog.get_logger()


class BaseBroker(ABC):
    """\u5238\u5546\u63a5\u53e3\u57fa\u7c7b"""

    def __init__(self, paper_trading: bool = True):
        self.paper_trading = paper_trading
        self._status = BrokerConnectionStatus.DISCONNECTED
        self._last_error: str | None = None

    @property
    @abstractmethod
    def broker_type(self) -> BrokerType:
        """\u5238\u5546\u7c7b\u578b"""
        pass

    @property
    def status(self) -> BrokerConnectionStatus:
        """\u8fde\u63a5\u72b6\u6001"""
        return self._status

    @abstractmethod
    async def connect(self) -> bool:
        """\u8fde\u63a5\u5238\u5546"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """\u65ad\u5f00\u8fde\u63a5"""
        pass

    @abstractmethod
    async def get_account(self) -> BrokerAccount | None:
        """\u83b7\u53d6\u8d26\u6237\u4fe1\u606f"""
        pass

    @abstractmethod
    async def get_positions(self) -> list[BrokerPosition]:
        """\u83b7\u53d6\u6301\u4ed3"""
        pass

    @abstractmethod
    async def submit_order(self, order: CreateOrderRequest) -> OrderResponse | None:
        """\u63d0\u4ea4\u8ba2\u5355"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """\u53d6\u6d88\u8ba2\u5355"""
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> OrderResponse | None:
        """\u83b7\u53d6\u8ba2\u5355"""
        pass

    @abstractmethod
    async def get_orders(
        self,
        status: OrderStatus | None = None,
        limit: int = 100,
    ) -> list[OrderResponse]:
        """\u83b7\u53d6\u8ba2\u5355\u5217\u8868"""
        pass

    async def get_market_status(self) -> MarketStatus:
        """\u83b7\u53d6\u5e02\u573a\u72b6\u6001"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute

        # \u7b80\u5316\u7684\u5e02\u573a\u65f6\u95f4\u68c0\u67e5 (\u7f8e\u4e1c\u65f6\u95f4)
        if now.weekday() >= 5:
            return MarketStatus.CLOSED

        current_time = hour * 60 + minute

        if current_time < 4 * 60:  # 00:00 - 04:00
            return MarketStatus.CLOSED
        elif current_time < 9 * 60 + 30:  # 04:00 - 09:30
            return MarketStatus.PRE_MARKET
        elif current_time < 16 * 60:  # 09:30 - 16:00
            return MarketStatus.OPEN
        elif current_time < 20 * 60:  # 16:00 - 20:00
            return MarketStatus.AFTER_HOURS
        else:
            return MarketStatus.CLOSED

    def get_status_summary(self) -> BrokerStatusSummary:
        """\u83b7\u53d6\u72b6\u6001\u6458\u8981"""
        return BrokerStatusSummary(
            broker=self.broker_type,
            status=self._status,
            paper_trading=self.paper_trading,
            account=None,
            market_status=MarketStatus.CLOSED,
            last_update=datetime.now(),
        )


class AlpacaBroker(BaseBroker):
    """
    Alpaca \u5238\u5546\u5b9e\u73b0

    \u7279\u70b9:
    - \u514d\u8d39 API
    - \u652f\u6301 Paper Trading
    - REST + WebSocket
    - 0 \u4f63\u91d1

    API \u6587\u6863: https://alpaca.markets/docs/api-references/
    """

    LIVE_BASE_URL = "https://api.alpaca.markets"
    PAPER_BASE_URL = "https://paper-api.alpaca.markets"
    DATA_BASE_URL = "https://data.alpaca.markets"

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        paper_trading: bool = True,
    ):
        super().__init__(paper_trading)
        self.api_key = api_key or getattr(settings, "ALPACA_API_KEY", None)
        self.secret_key = secret_key or getattr(settings, "ALPACA_SECRET_KEY", None)

        self.base_url = self.PAPER_BASE_URL if paper_trading else self.LIVE_BASE_URL
        self._client: httpx.AsyncClient | None = None

    @property
    def broker_type(self) -> BrokerType:
        return BrokerType.ALPACA

    def _get_headers(self) -> dict[str, str]:
        """\u83b7\u53d6\u8bf7\u6c42\u5934"""
        return {
            "APCA-API-KEY-ID": self.api_key or "",
            "APCA-API-SECRET-KEY": self.secret_key or "",
            "Content-Type": "application/json",
        }

    async def connect(self) -> bool:
        """\u8fde\u63a5 Alpaca"""
        if not self.api_key or not self.secret_key:
            self._status = BrokerConnectionStatus.ERROR
            self._last_error = "API \u5bc6\u94a5\u672a\u914d\u7f6e"
            logger.warning("Alpaca API \u5bc6\u94a5\u672a\u914d\u7f6e")
            return False

        try:
            self._status = BrokerConnectionStatus.CONNECTING
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._get_headers(),
                timeout=30.0,
            )

            # \u9a8c\u8bc1\u8fde\u63a5
            response = await self._client.get("/v2/account")
            if response.status_code == 200:
                self._status = BrokerConnectionStatus.CONNECTED
                logger.info(
                    "Alpaca \u8fde\u63a5\u6210\u529f",
                    paper_trading=self.paper_trading,
                )
                return True
            else:
                self._status = BrokerConnectionStatus.ERROR
                self._last_error = f"API \u9519\u8bef: {response.status_code}"
                return False

        except Exception as e:
            self._status = BrokerConnectionStatus.ERROR
            self._last_error = str(e)
            logger.error("Alpaca \u8fde\u63a5\u5931\u8d25", error=str(e))
            return False

    async def disconnect(self) -> None:
        """\u65ad\u5f00\u8fde\u63a5"""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._status = BrokerConnectionStatus.DISCONNECTED

    async def get_account(self) -> BrokerAccount | None:
        """\u83b7\u53d6\u8d26\u6237\u4fe1\u606f"""
        if not self._client or self._status != BrokerConnectionStatus.CONNECTED:
            return None

        try:
            response = await self._client.get("/v2/account")
            if response.status_code != 200:
                return None

            data = response.json()
            return BrokerAccount(
                id=data.get("id", ""),
                broker=BrokerType.ALPACA,
                account_number=data.get("account_number", ""),
                status=data.get("status", "active"),
                currency=data.get("currency", "USD"),
                buying_power=float(data.get("buying_power", 0)),
                cash=float(data.get("cash", 0)),
                portfolio_value=float(data.get("portfolio_value", 0)),
                equity=float(data.get("equity", 0)),
                last_equity=float(data.get("last_equity", 0)),
                long_market_value=float(data.get("long_market_value", 0)),
                short_market_value=float(data.get("short_market_value", 0)),
                initial_margin=float(data.get("initial_margin", 0)),
                maintenance_margin=float(data.get("maintenance_margin", 0)),
                daytrade_count=int(data.get("daytrade_count", 0)),
                pattern_day_trader=data.get("pattern_day_trader", False),
                trading_blocked=data.get("trading_blocked", False),
                transfers_blocked=data.get("transfers_blocked", False),
                account_blocked=data.get("account_blocked", False),
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                if data.get("created_at")
                else None,
                paper_trading=self.paper_trading,
            )

        except Exception as e:
            logger.error("\u83b7\u53d6\u8d26\u6237\u5931\u8d25", error=str(e))
            return None

    async def get_positions(self) -> list[BrokerPosition]:
        """\u83b7\u53d6\u6301\u4ed3"""
        if not self._client or self._status != BrokerConnectionStatus.CONNECTED:
            return []

        try:
            response = await self._client.get("/v2/positions")
            if response.status_code != 200:
                return []

            positions = []
            for data in response.json():
                qty = float(data.get("qty", 0))
                positions.append(
                    BrokerPosition(
                        symbol=data.get("symbol", ""),
                        quantity=abs(qty),
                        side="long" if qty > 0 else "short",
                        avg_entry_price=float(data.get("avg_entry_price", 0)),
                        market_value=float(data.get("market_value", 0)),
                        current_price=float(data.get("current_price", 0)),
                        unrealized_pnl=float(data.get("unrealized_pl", 0)),
                        unrealized_pnl_percent=float(data.get("unrealized_plpc", 0)) * 100,
                        cost_basis=float(data.get("cost_basis", 0)),
                        asset_class=data.get("asset_class", "us_equity"),
                        exchange=data.get("exchange", ""),
                    )
                )
            return positions

        except Exception as e:
            logger.error("\u83b7\u53d6\u6301\u4ed3\u5931\u8d25", error=str(e))
            return []

    async def submit_order(self, order: CreateOrderRequest) -> OrderResponse | None:
        """\u63d0\u4ea4\u8ba2\u5355"""
        if not self._client or self._status != BrokerConnectionStatus.CONNECTED:
            return None

        try:
            # \u6784\u5efa\u8ba2\u5355\u8bf7\u6c42
            payload: dict[str, Any] = {
                "symbol": order.symbol,
                "qty": order.quantity,
                "side": order.side.value,
                "type": order.order_type.value,
                "time_in_force": order.time_in_force.value,
            }

            if order.limit_price:
                payload["limit_price"] = str(order.limit_price)
            if order.stop_price:
                payload["stop_price"] = str(order.stop_price)
            if order.extended_hours:
                payload["extended_hours"] = True
            if order.client_order_id:
                payload["client_order_id"] = order.client_order_id

            response = await self._client.post("/v2/orders", json=payload)

            if response.status_code not in (200, 201):
                logger.error(
                    "\u63d0\u4ea4\u8ba2\u5355\u5931\u8d25",
                    status=response.status_code,
                    body=response.text,
                )
                return None

            data = response.json()
            return self._parse_order(data)

        except Exception as e:
            logger.error("\u63d0\u4ea4\u8ba2\u5355\u5f02\u5e38", error=str(e))
            return None

    async def cancel_order(self, order_id: str) -> bool:
        """\u53d6\u6d88\u8ba2\u5355"""
        if not self._client or self._status != BrokerConnectionStatus.CONNECTED:
            return False

        try:
            response = await self._client.delete(f"/v2/orders/{order_id}")
            return response.status_code in (200, 204)
        except Exception as e:
            logger.error("\u53d6\u6d88\u8ba2\u5355\u5931\u8d25", error=str(e))
            return False

    async def get_order(self, order_id: str) -> OrderResponse | None:
        """\u83b7\u53d6\u8ba2\u5355"""
        if not self._client or self._status != BrokerConnectionStatus.CONNECTED:
            return None

        try:
            response = await self._client.get(f"/v2/orders/{order_id}")
            if response.status_code != 200:
                return None
            return self._parse_order(response.json())
        except Exception as e:
            logger.error("\u83b7\u53d6\u8ba2\u5355\u5931\u8d25", error=str(e))
            return None

    async def get_orders(
        self,
        status: OrderStatus | None = None,
        limit: int = 100,
    ) -> list[OrderResponse]:
        """\u83b7\u53d6\u8ba2\u5355\u5217\u8868"""
        if not self._client or self._status != BrokerConnectionStatus.CONNECTED:
            return []

        try:
            params: dict[str, Any] = {"limit": limit}
            if status:
                params["status"] = status.value

            response = await self._client.get("/v2/orders", params=params)
            if response.status_code != 200:
                return []

            return [self._parse_order(data) for data in response.json()]

        except Exception as e:
            logger.error("\u83b7\u53d6\u8ba2\u5355\u5217\u8868\u5931\u8d25", error=str(e))
            return []

    def _parse_order(self, data: dict[str, Any]) -> OrderResponse:
        """\u89e3\u6790\u8ba2\u5355\u6570\u636e"""
        def parse_datetime(s: str | None) -> datetime | None:
            if not s:
                return None
            return datetime.fromisoformat(s.replace("Z", "+00:00"))

        return OrderResponse(
            id=data.get("id", ""),
            client_order_id=data.get("client_order_id", ""),
            symbol=data.get("symbol", ""),
            side=OrderSide(data.get("side", "buy")),
            quantity=float(data.get("qty", 0)),
            filled_quantity=float(data.get("filled_qty", 0)),
            order_type=OrderType(data.get("type", "market")),
            status=self._map_alpaca_status(data.get("status", "")),
            limit_price=float(data["limit_price"]) if data.get("limit_price") else None,
            stop_price=float(data["stop_price"]) if data.get("stop_price") else None,
            filled_avg_price=float(data["filled_avg_price"])
            if data.get("filled_avg_price")
            else None,
            created_at=parse_datetime(data.get("created_at")) or datetime.now(),
            updated_at=parse_datetime(data.get("updated_at")) or datetime.now(),
            submitted_at=parse_datetime(data.get("submitted_at")),
            filled_at=parse_datetime(data.get("filled_at")),
            cancelled_at=parse_datetime(data.get("canceled_at")),
            expired_at=parse_datetime(data.get("expired_at")),
            broker=BrokerType.ALPACA,
            broker_order_id=data.get("id"),
            commission=0.0,  # Alpaca \u96f6\u4f63\u91d1
            slippage=0.0,
        )

    def _map_alpaca_status(self, status: str) -> OrderStatus:
        """\u6620\u5c04 Alpaca \u8ba2\u5355\u72b6\u6001"""
        mapping = {
            "new": OrderStatus.SUBMITTED,
            "accepted": OrderStatus.ACCEPTED,
            "pending_new": OrderStatus.PENDING,
            "accepted_for_bidding": OrderStatus.ACCEPTED,
            "partially_filled": OrderStatus.PARTIAL,
            "filled": OrderStatus.FILLED,
            "done_for_day": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "expired": OrderStatus.EXPIRED,
            "replaced": OrderStatus.CANCELLED,
            "pending_cancel": OrderStatus.SUBMITTED,
            "pending_replace": OrderStatus.SUBMITTED,
            "stopped": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
            "suspended": OrderStatus.REJECTED,
            "calculated": OrderStatus.SUBMITTED,
        }
        return mapping.get(status, OrderStatus.PENDING)


class PaperBroker(BaseBroker):
    """
    Paper Trading \u5238\u5546\u5b9e\u73b0

    \u5b8c\u5168\u672c\u5730\u6a21\u62df:
    - \u65e0\u9700 API \u5bc6\u94a5
    - \u652f\u6301\u6240\u6709\u8ba2\u5355\u7c7b\u578b
    - \u53ef\u914d\u7f6e\u521d\u59cb\u8d44\u91d1
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_rate: float = 0.0,
    ):
        super().__init__(paper_trading=True)
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate

        # \u8d26\u6237\u72b6\u6001
        self._cash = initial_capital
        self._positions: dict[str, dict] = {}
        self._orders: dict[str, OrderResponse] = {}
        self._order_counter = 0

    @property
    def broker_type(self) -> BrokerType:
        return BrokerType.PAPER

    async def connect(self) -> bool:
        """\u8fde\u63a5 (\u59cb\u7ec8\u6210\u529f)"""
        self._status = BrokerConnectionStatus.CONNECTED
        logger.info("Paper Trading \u5df2\u542f\u7528", capital=self.initial_capital)
        return True

    async def disconnect(self) -> None:
        """\u65ad\u5f00\u8fde\u63a5"""
        self._status = BrokerConnectionStatus.DISCONNECTED

    async def get_account(self) -> BrokerAccount | None:
        """\u83b7\u53d6\u8d26\u6237\u4fe1\u606f"""
        # \u8ba1\u7b97\u6301\u4ed3\u5e02\u503c
        market_value = sum(
            pos["quantity"] * pos.get("current_price", pos["avg_price"])
            for pos in self._positions.values()
        )
        equity = self._cash + market_value

        return BrokerAccount(
            id="paper_account",
            broker=BrokerType.PAPER,
            account_number="PAPER-001",
            status="active",
            currency="USD",
            buying_power=self._cash,
            cash=self._cash,
            portfolio_value=equity,
            equity=equity,
            last_equity=self.initial_capital,
            long_market_value=market_value,
            paper_trading=True,
        )

    async def get_positions(self) -> list[BrokerPosition]:
        """\u83b7\u53d6\u6301\u4ed3"""
        positions = []
        for symbol, pos in self._positions.items():
            current_price = pos.get("current_price", pos["avg_price"])
            unrealized_pnl = (current_price - pos["avg_price"]) * pos["quantity"]
            unrealized_pnl_pct = (
                (current_price / pos["avg_price"] - 1) * 100
                if pos["avg_price"] > 0
                else 0
            )

            positions.append(
                BrokerPosition(
                    symbol=symbol,
                    quantity=pos["quantity"],
                    side="long" if pos["quantity"] > 0 else "short",
                    avg_entry_price=pos["avg_price"],
                    market_value=current_price * pos["quantity"],
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pnl_pct,
                    cost_basis=pos["avg_price"] * pos["quantity"],
                    asset_class="us_equity",
                )
            )
        return positions

    async def submit_order(self, order: CreateOrderRequest) -> OrderResponse | None:
        """\u63d0\u4ea4\u8ba2\u5355 (\u7acb\u5373\u6210\u4ea4)"""
        self._order_counter += 1
        order_id = f"PAPER-{self._order_counter:06d}"
        now = datetime.now()

        # \u5047\u8bbe\u4ee5\u5f53\u524d\u4ef7\u683c\u6210\u4ea4 (\u5b9e\u9645\u5e94\u8be5\u4ece\u5e02\u573a\u6570\u636e\u83b7\u53d6)
        fill_price = order.limit_price or 100.0  # \u9ed8\u8ba4\u4ef7\u683c

        # \u8ba1\u7b97\u4f63\u91d1
        commission = fill_price * order.quantity * self.commission_rate

        # \u66f4\u65b0\u6301\u4ed3
        if order.side == OrderSide.BUY:
            cost = fill_price * order.quantity + commission
            if cost > self._cash:
                logger.warning("\u8d44\u91d1\u4e0d\u8db3", required=cost, available=self._cash)
                return OrderResponse(
                    id=order_id,
                    client_order_id=order.client_order_id or order_id,
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.quantity,
                    filled_quantity=0,
                    order_type=order.order_type,
                    status=OrderStatus.REJECTED,
                    created_at=now,
                    updated_at=now,
                    broker=BrokerType.PAPER,
                )

            self._cash -= cost
            if order.symbol in self._positions:
                pos = self._positions[order.symbol]
                total_qty = pos["quantity"] + order.quantity
                pos["avg_price"] = (
                    (pos["avg_price"] * pos["quantity"] + fill_price * order.quantity)
                    / total_qty
                )
                pos["quantity"] = total_qty
            else:
                self._positions[order.symbol] = {
                    "quantity": order.quantity,
                    "avg_price": fill_price,
                    "current_price": fill_price,
                }
        else:  # SELL
            if order.symbol not in self._positions:
                return None
            pos = self._positions[order.symbol]
            if pos["quantity"] < order.quantity:
                return None

            proceeds = fill_price * order.quantity - commission
            self._cash += proceeds
            pos["quantity"] -= order.quantity
            if pos["quantity"] == 0:
                del self._positions[order.symbol]

        # \u521b\u5efa\u8ba2\u5355\u54cd\u5e94
        order_response = OrderResponse(
            id=order_id,
            client_order_id=order.client_order_id or order_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            filled_quantity=order.quantity,
            order_type=order.order_type,
            status=OrderStatus.FILLED,
            limit_price=order.limit_price,
            stop_price=order.stop_price,
            filled_avg_price=fill_price,
            created_at=now,
            updated_at=now,
            submitted_at=now,
            filled_at=now,
            broker=BrokerType.PAPER,
            broker_order_id=order_id,
            commission=commission,
        )

        self._orders[order_id] = order_response
        return order_response

    async def cancel_order(self, order_id: str) -> bool:
        """\u53d6\u6d88\u8ba2\u5355"""
        if order_id in self._orders:
            order = self._orders[order_id]
            if order.status not in {OrderStatus.FILLED, OrderStatus.CANCELLED}:
                order.status = OrderStatus.CANCELLED
                order.cancelled_at = datetime.now()
                return True
        return False

    async def get_order(self, order_id: str) -> OrderResponse | None:
        """\u83b7\u53d6\u8ba2\u5355"""
        return self._orders.get(order_id)

    async def get_orders(
        self,
        status: OrderStatus | None = None,
        limit: int = 100,
    ) -> list[OrderResponse]:
        """\u83b7\u53d6\u8ba2\u5355\u5217\u8868"""
        orders = list(self._orders.values())
        if status:
            orders = [o for o in orders if o.status == status]
        return orders[:limit]

    def update_prices(self, prices: dict[str, float]) -> None:
        """\u66f4\u65b0\u4ef7\u683c (\u7528\u4e8e\u8ba1\u7b97\u672a\u5b9e\u73b0\u76c8\u4e8f)"""
        for symbol, price in prices.items():
            if symbol in self._positions:
                self._positions[symbol]["current_price"] = price


class BrokerManager:
    """
    \u5238\u5546\u7ba1\u7406\u5668

    \u7ba1\u7406\u591a\u4e2a\u5238\u5546\u8fde\u63a5:
    - \u81ea\u52a8\u6545\u969c\u8f6c\u79fb
    - \u7edf\u4e00\u63a5\u53e3
    """

    def __init__(self):
        self._brokers: dict[BrokerType, BaseBroker] = {}
        self._primary_broker: BrokerType | None = None

    async def initialize(self) -> None:
        """\u521d\u59cb\u5316\u5238\u5546"""
        # \u521d\u59cb\u5316 Paper Broker (\u59cb\u7ec8\u53ef\u7528)
        paper = PaperBroker()
        await paper.connect()
        self._brokers[BrokerType.PAPER] = paper

        # \u5c1d\u8bd5\u8fde\u63a5 Alpaca
        if getattr(settings, "ALPACA_API_KEY", None):
            alpaca = AlpacaBroker()
            if await alpaca.connect():
                self._brokers[BrokerType.ALPACA] = alpaca
                self._primary_broker = BrokerType.ALPACA
                return

        # \u9ed8\u8ba4\u4f7f\u7528 Paper Trading
        self._primary_broker = BrokerType.PAPER

    async def shutdown(self) -> None:
        """\u5173\u95ed\u6240\u6709\u8fde\u63a5"""
        for broker in self._brokers.values():
            await broker.disconnect()
        self._brokers.clear()

    def get_broker(self, broker_type: BrokerType | None = None) -> BaseBroker | None:
        """\u83b7\u53d6\u5238\u5546"""
        if broker_type:
            return self._brokers.get(broker_type)
        if self._primary_broker:
            return self._brokers.get(self._primary_broker)
        return None

    @property
    def primary_broker(self) -> BaseBroker | None:
        """\u4e3b\u8981\u5238\u5546"""
        return self.get_broker()

    def get_available_brokers(self) -> list[BrokerType]:
        """\u83b7\u53d6\u53ef\u7528\u5238\u5546\u5217\u8868"""
        return [
            broker_type
            for broker_type, broker in self._brokers.items()
            if broker.status == BrokerConnectionStatus.CONNECTED
        ]

    async def switch_broker(self, broker_type: BrokerType) -> bool:
        """\u5207\u6362\u4e3b\u8981\u5238\u5546"""
        if broker_type in self._brokers:
            broker = self._brokers[broker_type]
            if broker.status == BrokerConnectionStatus.CONNECTED:
                self._primary_broker = broker_type
                logger.info("\u5207\u6362\u5238\u5546", broker=broker_type.value)
                return True
        return False


# \u5168\u5c40\u5b9e\u4f8b
broker_manager = BrokerManager()
