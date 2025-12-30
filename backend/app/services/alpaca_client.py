"""
Alpaca 客户端

提供:
- 历史行情数据获取
- 实时行情订阅
- 交易执行接口
- 账户和持仓管理
- WebSocket 订单状态更新
"""

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable
from uuid import UUID

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger()


class AlpacaOrderSide(str, Enum):
    """Alpaca 订单方向"""
    BUY = "buy"
    SELL = "sell"


class AlpacaOrderType(str, Enum):
    """Alpaca 订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class AlpacaOrderStatus(str, Enum):
    """Alpaca 订单状态"""
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    DONE_FOR_DAY = "done_for_day"
    CANCELED = "canceled"
    EXPIRED = "expired"
    REPLACED = "replaced"
    PENDING_CANCEL = "pending_cancel"
    PENDING_REPLACE = "pending_replace"
    ACCEPTED = "accepted"
    PENDING_NEW = "pending_new"
    ACCEPTED_FOR_BIDDING = "accepted_for_bidding"
    STOPPED = "stopped"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    CALCULATED = "calculated"


class AlpacaTimeInForce(str, Enum):
    """Alpaca 订单有效期"""
    DAY = "day"
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"
    OPG = "opg"
    CLS = "cls"


@dataclass
class AlpacaPosition:
    """Alpaca 持仓"""
    symbol: str
    quantity: Decimal
    avg_entry_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pl: Decimal
    unrealized_plpc: Decimal  # 未实现盈亏百分比
    current_price: Decimal
    side: str  # "long" or "short"
    exchange: str


@dataclass
class AlpacaOrder:
    """Alpaca 订单"""
    id: str
    client_order_id: str
    symbol: str
    side: AlpacaOrderSide
    order_type: AlpacaOrderType
    qty: Decimal
    filled_qty: Decimal
    filled_avg_price: Decimal | None
    status: AlpacaOrderStatus
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    filled_at: datetime | None
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: AlpacaTimeInForce = AlpacaTimeInForce.DAY


class AlpacaClient:
    """
    Alpaca API 客户端

    封装 Alpaca REST API，提供:
    - 行情数据获取
    - 财务数据获取
    - 错误处理和重试
    """

    def __init__(self):
        self.api_key = settings.ALPACA_API_KEY
        self.secret_key = settings.ALPACA_SECRET_KEY
        self.base_url = settings.ALPACA_BASE_URL
        self.data_url = settings.ALPACA_DATA_URL

        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端实例"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "APCA-API-KEY-ID": self.api_key,
                    "APCA-API-SECRET-KEY": self.secret_key,
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """关闭客户端连接"""
        if self._client:
            await self._client.aclose()
            self._client = None

    # === 行情数据 ===

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_bars(
        self,
        symbols: list[str],
        start: date,
        end: date,
        timeframe: str = "1Day",
        adjustment: str = "all",
    ) -> dict[str, list[dict[str, Any]]]:
        """
        获取历史 K 线数据

        Args:
            symbols: 股票代码列表
            start: 开始日期
            end: 结束日期
            timeframe: 时间周期 (1Min, 5Min, 15Min, 1Hour, 1Day)
            adjustment: 复权类型 (raw, split, dividend, all)

        Returns:
            按股票代码分组的 K 线数据
        """
        client = await self._get_client()
        result: dict[str, list[dict[str, Any]]] = {s: [] for s in symbols}

        # Alpaca 限制每次最多 10000 条
        url = f"{self.data_url}/v2/stocks/bars"

        params = {
            "symbols": ",".join(symbols),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timeframe": timeframe,
            "adjustment": adjustment,
            "limit": 10000,
        }

        page_token = None
        while True:
            if page_token:
                params["page_token"] = page_token

            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                bars = data.get("bars", {})
                for symbol, symbol_bars in bars.items():
                    for bar in symbol_bars:
                        result[symbol].append({
                            "timestamp": bar["t"],
                            "open": Decimal(str(bar["o"])),
                            "high": Decimal(str(bar["h"])),
                            "low": Decimal(str(bar["l"])),
                            "close": Decimal(str(bar["c"])),
                            "volume": bar["v"],
                            "vwap": Decimal(str(bar.get("vw", 0))),
                            "trade_count": bar.get("n", 0),
                        })

                page_token = data.get("next_page_token")
                if not page_token:
                    break

            except httpx.HTTPStatusError as e:
                logger.error(
                    "Alpaca API 请求失败",
                    status_code=e.response.status_code,
                    symbols=symbols,
                )
                raise

        logger.info(
            "获取 K 线数据完成",
            symbols=len(symbols),
            total_bars=sum(len(v) for v in result.values()),
        )

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_latest_bars(
        self,
        symbols: list[str],
    ) -> dict[str, dict[str, Any]]:
        """
        获取最新 K 线数据

        Args:
            symbols: 股票代码列表

        Returns:
            按股票代码分组的最新 K 线
        """
        client = await self._get_client()
        url = f"{self.data_url}/v2/stocks/bars/latest"

        params = {"symbols": ",".join(symbols)}

        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        result = {}
        for symbol, bar in data.get("bars", {}).items():
            result[symbol] = {
                "timestamp": bar["t"],
                "open": Decimal(str(bar["o"])),
                "high": Decimal(str(bar["h"])),
                "low": Decimal(str(bar["l"])),
                "close": Decimal(str(bar["c"])),
                "volume": bar["v"],
                "vwap": Decimal(str(bar.get("vw", 0))),
            }

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def get_quotes(
        self,
        symbols: list[str],
    ) -> dict[str, dict[str, Any]]:
        """
        获取最新报价

        Args:
            symbols: 股票代码列表

        Returns:
            按股票代码分组的报价数据
        """
        client = await self._get_client()
        url = f"{self.data_url}/v2/stocks/quotes/latest"

        params = {"symbols": ",".join(symbols)}

        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        result = {}
        for symbol, quote in data.get("quotes", {}).items():
            result[symbol] = {
                "timestamp": quote["t"],
                "bid": Decimal(str(quote.get("bp", 0))),
                "bid_size": quote.get("bs", 0),
                "ask": Decimal(str(quote.get("ap", 0))),
                "ask_size": quote.get("as", 0),
            }

        return result

    # === 资产信息 ===

    async def get_assets(
        self,
        status: str = "active",
        asset_class: str = "us_equity",
    ) -> list[dict[str, Any]]:
        """
        获取可交易资产列表

        Args:
            status: 状态 (active, inactive)
            asset_class: 资产类别 (us_equity, crypto)

        Returns:
            资产列表
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/assets"

        params = {"status": status, "asset_class": asset_class}

        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return [
            {
                "symbol": asset["symbol"],
                "name": asset["name"],
                "exchange": asset["exchange"],
                "tradable": asset["tradable"],
                "shortable": asset["shortable"],
                "fractionable": asset["fractionable"],
            }
            for asset in data
        ]

    # === 账户信息 ===

    async def get_account(self) -> dict[str, Any]:
        """获取账户信息"""
        client = await self._get_client()
        url = f"{self.base_url}/v2/account"

        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

        return {
            "id": data["id"],
            "status": data["status"],
            "currency": data["currency"],
            "cash": Decimal(str(data["cash"])),
            "portfolio_value": Decimal(str(data["portfolio_value"])),
            "buying_power": Decimal(str(data["buying_power"])),
            "equity": Decimal(str(data["equity"])),
            "last_equity": Decimal(str(data["last_equity"])),
            "pattern_day_trader": data["pattern_day_trader"],
        }

    # === 持仓管理 ===

    async def get_positions(self) -> list[AlpacaPosition]:
        """
        获取所有持仓

        Returns:
            持仓列表
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/positions"

        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

        positions = []
        for pos in data:
            positions.append(AlpacaPosition(
                symbol=pos["symbol"],
                quantity=Decimal(str(pos["qty"])),
                avg_entry_price=Decimal(str(pos["avg_entry_price"])),
                market_value=Decimal(str(pos["market_value"])),
                cost_basis=Decimal(str(pos["cost_basis"])),
                unrealized_pl=Decimal(str(pos["unrealized_pl"])),
                unrealized_plpc=Decimal(str(pos["unrealized_plpc"])),
                current_price=Decimal(str(pos["current_price"])),
                side=pos["side"],
                exchange=pos["exchange"],
            ))

        logger.info("获取持仓完成", n_positions=len(positions))
        return positions

    async def get_position(self, symbol: str) -> AlpacaPosition | None:
        """
        获取单个持仓

        Args:
            symbol: 股票代码

        Returns:
            持仓信息 (无持仓返回 None)
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/positions/{symbol}"

        try:
            response = await client.get(url)
            response.raise_for_status()
            pos = response.json()

            return AlpacaPosition(
                symbol=pos["symbol"],
                quantity=Decimal(str(pos["qty"])),
                avg_entry_price=Decimal(str(pos["avg_entry_price"])),
                market_value=Decimal(str(pos["market_value"])),
                cost_basis=Decimal(str(pos["cost_basis"])),
                unrealized_pl=Decimal(str(pos["unrealized_pl"])),
                unrealized_plpc=Decimal(str(pos["unrealized_plpc"])),
                current_price=Decimal(str(pos["current_price"])),
                side=pos["side"],
                exchange=pos["exchange"],
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def close_position(self, symbol: str) -> AlpacaOrder:
        """
        平仓

        Args:
            symbol: 股票代码

        Returns:
            平仓订单
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/positions/{symbol}"

        response = await client.delete(url)
        response.raise_for_status()
        data = response.json()

        logger.info("平仓成功", symbol=symbol)
        return self._parse_order(data)

    async def close_all_positions(self) -> list[AlpacaOrder]:
        """
        平掉所有持仓

        Returns:
            平仓订单列表
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/positions"

        response = await client.delete(url)
        response.raise_for_status()
        data = response.json()

        orders = [self._parse_order(o) for o in data]
        logger.info("全部平仓完成", n_orders=len(orders))
        return orders

    # === 订单管理 ===

    async def submit_order(
        self,
        symbol: str,
        qty: float,
        side: AlpacaOrderSide,
        order_type: AlpacaOrderType = AlpacaOrderType.MARKET,
        time_in_force: AlpacaTimeInForce = AlpacaTimeInForce.DAY,
        limit_price: float | None = None,
        stop_price: float | None = None,
        client_order_id: str | None = None,
        extended_hours: bool = False,
    ) -> AlpacaOrder:
        """
        提交订单

        Args:
            symbol: 股票代码
            qty: 数量
            side: 方向
            order_type: 订单类型
            time_in_force: 有效期
            limit_price: 限价
            stop_price: 止损价
            client_order_id: 客户端订单ID
            extended_hours: 是否允许盘前盘后交易

        Returns:
            订单信息
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/orders"

        payload: dict[str, Any] = {
            "symbol": symbol,
            "qty": str(qty),
            "side": side.value,
            "type": order_type.value,
            "time_in_force": time_in_force.value,
            "extended_hours": extended_hours,
        }

        if limit_price is not None:
            payload["limit_price"] = str(limit_price)

        if stop_price is not None:
            payload["stop_price"] = str(stop_price)

        if client_order_id:
            payload["client_order_id"] = client_order_id

        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        order = self._parse_order(data)

        logger.info(
            "订单已提交",
            order_id=order.id,
            symbol=symbol,
            side=side.value,
            qty=qty,
            order_type=order_type.value,
        )

        return order

    async def get_order(self, order_id: str) -> AlpacaOrder:
        """
        获取订单信息

        Args:
            order_id: 订单ID

        Returns:
            订单信息
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/orders/{order_id}"

        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

        return self._parse_order(data)

    async def get_orders(
        self,
        status: str = "open",
        limit: int = 50,
        symbols: list[str] | None = None,
    ) -> list[AlpacaOrder]:
        """
        获取订单列表

        Args:
            status: 状态过滤 (open, closed, all)
            limit: 数量限制
            symbols: 股票过滤

        Returns:
            订单列表
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/orders"

        params: dict[str, Any] = {
            "status": status,
            "limit": limit,
        }

        if symbols:
            params["symbols"] = ",".join(symbols)

        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return [self._parse_order(o) for o in data]

    async def cancel_order(self, order_id: str) -> None:
        """
        取消订单

        Args:
            order_id: 订单ID
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/orders/{order_id}"

        response = await client.delete(url)
        response.raise_for_status()

        logger.info("订单已取消", order_id=order_id)

    async def cancel_all_orders(self) -> list[dict[str, Any]]:
        """
        取消所有订单

        Returns:
            取消结果列表
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/orders"

        response = await client.delete(url)
        response.raise_for_status()
        data = response.json()

        logger.info("取消所有订单完成", n_cancelled=len(data))
        return data

    async def replace_order(
        self,
        order_id: str,
        qty: float | None = None,
        limit_price: float | None = None,
        stop_price: float | None = None,
        time_in_force: AlpacaTimeInForce | None = None,
    ) -> AlpacaOrder:
        """
        修改订单

        Args:
            order_id: 订单ID
            qty: 新数量
            limit_price: 新限价
            stop_price: 新止损价
            time_in_force: 新有效期

        Returns:
            修改后的订单
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/orders/{order_id}"

        payload: dict[str, Any] = {}

        if qty is not None:
            payload["qty"] = str(qty)
        if limit_price is not None:
            payload["limit_price"] = str(limit_price)
        if stop_price is not None:
            payload["stop_price"] = str(stop_price)
        if time_in_force is not None:
            payload["time_in_force"] = time_in_force.value

        response = await client.patch(url, json=payload)
        response.raise_for_status()
        data = response.json()

        order = self._parse_order(data)
        logger.info("订单已修改", order_id=order_id)

        return order

    # === 活动和日历 ===

    async def get_clock(self) -> dict[str, Any]:
        """
        获取市场时钟

        Returns:
            市场时钟信息
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/clock"

        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

        return {
            "timestamp": data["timestamp"],
            "is_open": data["is_open"],
            "next_open": data["next_open"],
            "next_close": data["next_close"],
        }

    async def get_calendar(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> list[dict[str, Any]]:
        """
        获取交易日历

        Args:
            start: 开始日期
            end: 结束日期

        Returns:
            交易日列表
        """
        client = await self._get_client()
        url = f"{self.base_url}/v2/calendar"

        params: dict[str, str] = {}
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()

        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return [
            {
                "date": day["date"],
                "open": day["open"],
                "close": day["close"],
            }
            for day in data
        ]

    # === 辅助方法 ===

    def _parse_order(self, data: dict[str, Any]) -> AlpacaOrder:
        """解析订单数据"""
        return AlpacaOrder(
            id=data["id"],
            client_order_id=data["client_order_id"],
            symbol=data["symbol"],
            side=AlpacaOrderSide(data["side"]),
            order_type=AlpacaOrderType(data["type"]),
            qty=Decimal(str(data["qty"])),
            filled_qty=Decimal(str(data["filled_qty"])),
            filled_avg_price=Decimal(str(data["filled_avg_price"])) if data.get("filled_avg_price") else None,
            status=AlpacaOrderStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
            submitted_at=datetime.fromisoformat(data["submitted_at"].replace("Z", "+00:00")) if data.get("submitted_at") else None,
            filled_at=datetime.fromisoformat(data["filled_at"].replace("Z", "+00:00")) if data.get("filled_at") else None,
            limit_price=Decimal(str(data["limit_price"])) if data.get("limit_price") else None,
            stop_price=Decimal(str(data["stop_price"])) if data.get("stop_price") else None,
            time_in_force=AlpacaTimeInForce(data["time_in_force"]),
        )


# 单例客户端
_alpaca_client: AlpacaClient | None = None


def get_alpaca_client() -> AlpacaClient:
    """获取 Alpaca 客户端单例"""
    global _alpaca_client
    if _alpaca_client is None:
        _alpaca_client = AlpacaClient()
    return _alpaca_client
