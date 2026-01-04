"""
Phase 11: \u6570\u636e\u5c42\u5347\u7ea7 - \u6570\u636e\u6e90\u670d\u52a1

\u652f\u6301\u7684\u6570\u636e\u6e90:
- Polygon.io: \u5b9e\u65f6 + \u5386\u53f2\u6570\u636e
- Alpaca: \u5b9e\u65f6 + \u5386\u53f2\u6570\u636e (\u514d\u8d39)
- IEX Cloud: \u5386\u53f2\u6570\u636e
- Yahoo Finance: \u5386\u53f2\u6570\u636e (\u5907\u7528)
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any

import httpx
import structlog

from app.core.config import settings
from app.schemas.market_data import (
    DataSource,
    DataFrequency,
    DataSourceStatus,
    DataSourceInfo,
    OHLCVBar,
    MinuteBar,
    Quote,
    MarketSnapshot,
)

logger = structlog.get_logger()


class BaseDataSource(ABC):
    """\u6570\u636e\u6e90\u57fa\u7c7b"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.status = DataSourceStatus.DISCONNECTED
        self.requests_today = 0
        self.last_request_time: datetime | None = None
        self.latency_ms = 0.0
        self._client: httpx.AsyncClient | None = None

    @property
    @abstractmethod
    def source(self) -> DataSource:
        """数据源标识"""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """API 基础 URL"""
        pass

    @property
    @abstractmethod
    def rate_limit(self) -> int:
        """每分钟请求限制"""
        pass

    async def connect(self) -> None:
        """建立连接"""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers=self._get_headers()
        )
        self.status = DataSourceStatus.CONNECTED
        logger.info(f"{self.source} 数据源已连接")

    async def disconnect(self) -> None:
        """断开连接"""
        if self._client:
            await self._client.aclose()
            self._client = None
        self.status = DataSourceStatus.DISCONNECTED

    def _get_headers(self) -> dict[str, str]:
        """获取请求头"""
        return {}

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        **kwargs
    ) -> dict[str, Any]:
        """发送请求"""
        if not self._client:
            await self.connect()

        start_time = datetime.now()
        try:
            response = await self._client.request(method, path, params=params, **kwargs)
            self.latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            self.requests_today += 1
            self.last_request_time = datetime.now()

            if response.status_code == 429:
                self.status = DataSourceStatus.RATE_LIMITED
                raise Exception("Rate limit exceeded")

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            self.status = DataSourceStatus.ERROR
            logger.error(f"{self.source} 请求失败", error=str(e))
            raise
        except Exception as e:
            self.status = DataSourceStatus.ERROR
            raise

    def get_info(self) -> DataSourceInfo:
        """获取数据源信息"""
        return DataSourceInfo(
            source=self.source,
            status=self.status,
            last_sync=self.last_request_time,
            requests_today=self.requests_today,
            requests_limit=self.rate_limit,
            latency_ms=self.latency_ms,
        )

    @abstractmethod
    async def get_bars(
        self,
        symbol: str,
        frequency: DataFrequency,
        start_date: str,
        end_date: str,
        adjusted: bool = True,
    ) -> list[OHLCVBar]:
        """获取K线数据"""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote | None:
        """获取实时报价"""
        pass

    @abstractmethod
    async def get_snapshot(self, symbol: str) -> MarketSnapshot | None:
        """获取市场快照"""
        pass


class PolygonDataSource(BaseDataSource):
    """Polygon.io 数据源"""

    @property
    def source(self) -> DataSource:
        return DataSource.POLYGON

    @property
    def base_url(self) -> str:
        return "https://api.polygon.io"

    @property
    def rate_limit(self) -> int:
        return 100  # 免费版每分钟5个，付费版100+

    def _get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _frequency_to_multiplier(self, frequency: DataFrequency) -> tuple[int, str]:
        """转换频率为 Polygon 格式"""
        mapping = {
            DataFrequency.MIN_1: (1, "minute"),
            DataFrequency.MIN_5: (5, "minute"),
            DataFrequency.MIN_15: (15, "minute"),
            DataFrequency.MIN_30: (30, "minute"),
            DataFrequency.HOUR_1: (1, "hour"),
            DataFrequency.DAY_1: (1, "day"),
        }
        return mapping.get(frequency, (1, "day"))

    async def get_bars(
        self,
        symbol: str,
        frequency: DataFrequency,
        start_date: str,
        end_date: str,
        adjusted: bool = True,
    ) -> list[OHLCVBar]:
        """获取K线数据"""
        multiplier, timespan = self._frequency_to_multiplier(frequency)

        params = {
            "adjusted": str(adjusted).lower(),
            "sort": "asc",
            "limit": 50000,
        }

        path = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date}/{end_date}"
        data = await self._request("GET", path, params=params)

        bars = []
        for result in data.get("results", []):
            bars.append(OHLCVBar(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(result["t"] / 1000),
                open=result["o"],
                high=result["h"],
                low=result["l"],
                close=result["c"],
                volume=result["v"],
                vwap=result.get("vw"),
                trades=result.get("n"),
            ))

        return bars

    async def get_quote(self, symbol: str) -> Quote | None:
        """获取实时报价"""
        try:
            data = await self._request("GET", f"/v2/last/nbbo/{symbol}")
            result = data.get("results", {})

            return Quote(
                symbol=symbol,
                timestamp=datetime.fromtimestamp(result.get("t", 0) / 1000000000),
                bid_price=result.get("p", 0),
                bid_size=result.get("s", 0),
                ask_price=result.get("P", 0),
                ask_size=result.get("S", 0),
                last_price=result.get("p", 0),
                last_size=0,
                volume=0,
            )
        except Exception as e:
            logger.warning(f"获取 {symbol} 报价失败", error=str(e))
            return None

    async def get_snapshot(self, symbol: str) -> MarketSnapshot | None:
        """获取市场快照"""
        try:
            data = await self._request("GET", f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}")
            ticker = data.get("ticker", {})
            day = ticker.get("day", {})
            prev_day = ticker.get("prevDay", {})

            return MarketSnapshot(
                symbol=symbol,
                timestamp=datetime.now(),
                last_price=ticker.get("lastTrade", {}).get("p", 0),
                change=day.get("c", 0) - prev_day.get("c", 0),
                change_percent=((day.get("c", 0) / prev_day.get("c", 1)) - 1) * 100 if prev_day.get("c") else 0,
                open=day.get("o", 0),
                high=day.get("h", 0),
                low=day.get("l", 0),
                close=day.get("c", 0),
                previous_close=prev_day.get("c", 0),
                volume=day.get("v", 0),
                bid_price=ticker.get("lastQuote", {}).get("p", 0),
                bid_size=ticker.get("lastQuote", {}).get("s", 0),
                ask_price=ticker.get("lastQuote", {}).get("P", 0),
                ask_size=ticker.get("lastQuote", {}).get("S", 0),
                vwap=day.get("vw"),
            )
        except Exception as e:
            logger.warning(f"获取 {symbol} 快照失败", error=str(e))
            return None


class AlpacaDataSource(BaseDataSource):
    """Alpaca 数据源 (免费)"""

    @property
    def source(self) -> DataSource:
        return DataSource.ALPACA

    @property
    def base_url(self) -> str:
        return "https://data.alpaca.markets"

    @property
    def rate_limit(self) -> int:
        return 200

    def _get_headers(self) -> dict[str, str]:
        # Alpaca 使用 key ID 和 secret key
        key_id = self.api_key or ""
        secret_key = getattr(settings, "ALPACA_SECRET_KEY", "")
        return {
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret_key,
        }

    def _frequency_to_timeframe(self, frequency: DataFrequency) -> str:
        """转换频率为 Alpaca 格式"""
        mapping = {
            DataFrequency.MIN_1: "1Min",
            DataFrequency.MIN_5: "5Min",
            DataFrequency.MIN_15: "15Min",
            DataFrequency.MIN_30: "30Min",
            DataFrequency.HOUR_1: "1Hour",
            DataFrequency.DAY_1: "1Day",
        }
        return mapping.get(frequency, "1Day")

    async def get_bars(
        self,
        symbol: str,
        frequency: DataFrequency,
        start_date: str,
        end_date: str,
        adjusted: bool = True,
    ) -> list[OHLCVBar]:
        """获取K线数据"""
        timeframe = self._frequency_to_timeframe(frequency)

        params = {
            "start": start_date,
            "end": end_date,
            "timeframe": timeframe,
            "adjustment": "all" if adjusted else "raw",
            "limit": 10000,
        }

        path = f"/v2/stocks/{symbol}/bars"
        data = await self._request("GET", path, params=params)

        bars = []
        for bar in data.get("bars", []):
            bars.append(OHLCVBar(
                symbol=symbol,
                timestamp=datetime.fromisoformat(bar["t"].replace("Z", "+00:00")),
                open=bar["o"],
                high=bar["h"],
                low=bar["l"],
                close=bar["c"],
                volume=bar["v"],
                vwap=bar.get("vw"),
                trades=bar.get("n"),
            ))

        return bars

    async def get_quote(self, symbol: str) -> Quote | None:
        """获取实时报价"""
        try:
            data = await self._request("GET", f"/v2/stocks/{symbol}/quotes/latest")
            quote_data = data.get("quote", {})

            return Quote(
                symbol=symbol,
                timestamp=datetime.fromisoformat(quote_data.get("t", "").replace("Z", "+00:00")),
                bid_price=quote_data.get("bp", 0),
                bid_size=quote_data.get("bs", 0),
                ask_price=quote_data.get("ap", 0),
                ask_size=quote_data.get("as", 0),
                last_price=(quote_data.get("bp", 0) + quote_data.get("ap", 0)) / 2,
                last_size=0,
                volume=0,
            )
        except Exception as e:
            logger.warning(f"获取 {symbol} 报价失败", error=str(e))
            return None

    async def get_snapshot(self, symbol: str) -> MarketSnapshot | None:
        """获取市场快照"""
        try:
            data = await self._request("GET", f"/v2/stocks/{symbol}/snapshot")
            snapshot = data.get("snapshot", {})
            daily = snapshot.get("dailyBar", {})
            prev = snapshot.get("prevDailyBar", {})
            latest = snapshot.get("latestTrade", {})
            quote = snapshot.get("latestQuote", {})

            last_price = latest.get("p", daily.get("c", 0))
            prev_close = prev.get("c", 0)

            return MarketSnapshot(
                symbol=symbol,
                timestamp=datetime.now(),
                last_price=last_price,
                change=last_price - prev_close,
                change_percent=((last_price / prev_close) - 1) * 100 if prev_close else 0,
                open=daily.get("o", 0),
                high=daily.get("h", 0),
                low=daily.get("l", 0),
                close=daily.get("c", 0),
                previous_close=prev_close,
                volume=daily.get("v", 0),
                bid_price=quote.get("bp", 0),
                bid_size=quote.get("bs", 0),
                ask_price=quote.get("ap", 0),
                ask_size=quote.get("as", 0),
                vwap=daily.get("vw"),
            )
        except Exception as e:
            logger.warning(f"获取 {symbol} 快照失败", error=str(e))
            return None


class YahooDataSource(BaseDataSource):
    """Yahoo Finance 数据源 (备用)"""

    @property
    def source(self) -> DataSource:
        return DataSource.YAHOO

    @property
    def base_url(self) -> str:
        return "https://query1.finance.yahoo.com"

    @property
    def rate_limit(self) -> int:
        return 60

    async def get_bars(
        self,
        symbol: str,
        frequency: DataFrequency,
        start_date: str,
        end_date: str,
        adjusted: bool = True,
    ) -> list[OHLCVBar]:
        """获取K线数据 (使用 yfinance 库)"""
        # Yahoo Finance 主要用于日线数据备份
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        interval_map = {
            DataFrequency.MIN_1: "1m",
            DataFrequency.MIN_5: "5m",
            DataFrequency.MIN_15: "15m",
            DataFrequency.MIN_30: "30m",
            DataFrequency.HOUR_1: "1h",
            DataFrequency.DAY_1: "1d",
        }
        interval = interval_map.get(frequency, "1d")

        # yfinance 对分钟数据有限制
        df = ticker.history(start=start_date, end=end_date, interval=interval)

        bars = []
        for idx, row in df.iterrows():
            bars.append(OHLCVBar(
                symbol=symbol,
                timestamp=idx.to_pydatetime(),
                open=row["Open"],
                high=row["High"],
                low=row["Low"],
                close=row["Close"],
                volume=row["Volume"],
            ))

        return bars

    async def get_quote(self, symbol: str) -> Quote | None:
        """Yahoo 不支持实时报价"""
        return None

    async def get_snapshot(self, symbol: str) -> MarketSnapshot | None:
        """获取市场快照"""
        import yfinance as yf

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return MarketSnapshot(
                symbol=symbol,
                timestamp=datetime.now(),
                last_price=info.get("regularMarketPrice", 0),
                change=info.get("regularMarketChange", 0),
                change_percent=info.get("regularMarketChangePercent", 0),
                open=info.get("regularMarketOpen", 0),
                high=info.get("regularMarketDayHigh", 0),
                low=info.get("regularMarketDayLow", 0),
                close=info.get("regularMarketPrice", 0),
                previous_close=info.get("regularMarketPreviousClose", 0),
                volume=info.get("regularMarketVolume", 0),
                bid_price=info.get("bid", 0),
                bid_size=info.get("bidSize", 0),
                ask_price=info.get("ask", 0),
                ask_size=info.get("askSize", 0),
                average_volume=info.get("averageVolume", 0),
            )
        except Exception as e:
            logger.warning(f"获取 {symbol} 快照失败", error=str(e))
            return None


class DataSourceManager:
    """数据源管理器"""

    def __init__(self):
        self._sources: dict[DataSource, BaseDataSource] = {}
        self._primary_source: DataSource = DataSource.ALPACA

    async def initialize(self):
        """初始化数据源"""
        # Alpaca (免费, 优先)
        alpaca_key = getattr(settings, "ALPACA_API_KEY", None)
        if alpaca_key:
            self._sources[DataSource.ALPACA] = AlpacaDataSource(alpaca_key)
            await self._sources[DataSource.ALPACA].connect()

        # Polygon (付费)
        polygon_key = getattr(settings, "POLYGON_API_KEY", None)
        if polygon_key:
            self._sources[DataSource.POLYGON] = PolygonDataSource(polygon_key)
            await self._sources[DataSource.POLYGON].connect()
            self._primary_source = DataSource.POLYGON  # 如果有 Polygon，优先使用

        # Yahoo (备用，无需 key)
        self._sources[DataSource.YAHOO] = YahooDataSource()

        logger.info(f"数据源初始化完成，主数据源: {self._primary_source}")

    async def shutdown(self):
        """关闭所有数据源"""
        for source in self._sources.values():
            await source.disconnect()

    def get_source(self, source: DataSource | None = None) -> BaseDataSource:
        """获取数据源"""
        if source and source in self._sources:
            return self._sources[source]
        return self._sources.get(self._primary_source) or self._sources[DataSource.YAHOO]

    def get_all_sources(self) -> list[DataSourceInfo]:
        """获取所有数据源信息"""
        return [s.get_info() for s in self._sources.values()]

    async def get_bars(
        self,
        symbol: str,
        frequency: DataFrequency,
        start_date: str,
        end_date: str,
        adjusted: bool = True,
        source: DataSource | None = None,
    ) -> list[OHLCVBar]:
        """获取K线数据 (自动故障转移)"""
        sources_to_try = []

        if source:
            sources_to_try.append(source)
        else:
            # 按优先级排序
            sources_to_try = [self._primary_source, DataSource.ALPACA, DataSource.YAHOO]

        for src in sources_to_try:
            if src not in self._sources:
                continue

            try:
                return await self._sources[src].get_bars(
                    symbol, frequency, start_date, end_date, adjusted
                )
            except Exception as e:
                logger.warning(f"{src} 获取数据失败，尝试下一个数据源", error=str(e))
                continue

        raise Exception(f"所有数据源都无法获取 {symbol} 的数据")

    async def get_snapshot(
        self,
        symbol: str,
        source: DataSource | None = None,
    ) -> MarketSnapshot | None:
        """获取市场快照"""
        src = self.get_source(source)
        return await src.get_snapshot(symbol)

    async def get_multiple_snapshots(
        self,
        symbols: list[str],
    ) -> dict[str, MarketSnapshot]:
        """批量获取市场快照"""
        results = {}
        tasks = [self.get_snapshot(symbol) for symbol in symbols]
        snapshots = await asyncio.gather(*tasks, return_exceptions=True)

        for symbol, snapshot in zip(symbols, snapshots):
            if isinstance(snapshot, MarketSnapshot):
                results[symbol] = snapshot

        return results


# 全局数据源管理器实例
data_source_manager = DataSourceManager()
