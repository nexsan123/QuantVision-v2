"""
盘前扫描服务
PRD 4.18.0 盘前扫描器

数据源: Polygon API (行情) + Mock (降级)
"""
import random
import uuid
from datetime import date, datetime
from typing import Optional

import httpx
import structlog

from app.core.config import settings
from app.schemas.pre_market import (
    CreateWatchlistRequest,
    IntradayWatchlist,
    PreMarketScanFilter,
    PreMarketScanResult,
    PreMarketStock,
    ScoreBreakdown,
)

logger = structlog.get_logger()


# ============ 数据源状态 ============

class PreMarketDataSourceStatus:
    """盘前服务数据源状态"""
    def __init__(self):
        self.is_mock = True
        self.source = "mock"
        self.error_message: Optional[str] = "Using mock data - Polygon API not connected"
        self.last_sync: Optional[datetime] = None

    def to_dict(self):
        return {
            "is_mock": self.is_mock,
            "source": self.source,
            "error_message": self.error_message,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }


_data_source_status = PreMarketDataSourceStatus()


# ============ Polygon API 客户端 ============

class PolygonPreMarketClient:
    """Polygon API 盘前数据客户端"""

    BASE_URL = "https://api.polygon.io"

    def __init__(self):
        self.api_key = getattr(settings, "POLYGON_API_KEY", None)

    async def _request(self, endpoint: str, params: dict = None) -> Optional[dict]:
        """发送API请求"""
        if not self.api_key:
            return None

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                url = f"{self.BASE_URL}{endpoint}"
                params = params or {}
                params["apiKey"] = self.api_key

                response = await client.get(url, params=params)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning("polygon_premarket_error", status=response.status_code, endpoint=endpoint)
                    return None
        except Exception as e:
            logger.warning("polygon_premarket_connection_error", error=str(e))
            return None

    async def get_gainers_losers(self, direction: str = "gainers") -> list[dict]:
        """获取盘前涨跌榜"""
        data = await self._request(f"/v2/snapshot/locale/us/markets/stocks/{direction}")
        if data and "tickers" in data:
            return data["tickers"]
        return []

    async def get_snapshot(self, symbol: str) -> Optional[dict]:
        """获取单个股票快照"""
        data = await self._request(f"/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}")
        if data and "ticker" in data:
            return data["ticker"]
        return None

    async def get_snapshots(self, symbols: list[str]) -> list[dict]:
        """获取多个股票快照"""
        if not symbols:
            return []

        tickers_param = ",".join(symbols)
        data = await self._request(
            "/v2/snapshot/locale/us/markets/stocks/tickers",
            {"tickers": tickers_param}
        )
        if data and "tickers" in data:
            return data["tickers"]
        return []


_polygon_client = PolygonPreMarketClient()


class PreMarketService:
    """盘前扫描服务"""

    # 模拟数据存储
    _watchlists: dict[str, IntradayWatchlist] = {}

    # 模拟股票池
    SAMPLE_UNIVERSE = [
        {"symbol": "AAPL", "name": "Apple Inc."},
        {"symbol": "MSFT", "name": "Microsoft Corp."},
        {"symbol": "GOOGL", "name": "Alphabet Inc."},
        {"symbol": "AMZN", "name": "Amazon.com Inc."},
        {"symbol": "NVDA", "name": "NVIDIA Corp."},
        {"symbol": "TSLA", "name": "Tesla Inc."},
        {"symbol": "META", "name": "Meta Platforms Inc."},
        {"symbol": "AMD", "name": "Advanced Micro Devices"},
        {"symbol": "NFLX", "name": "Netflix Inc."},
        {"symbol": "CRM", "name": "Salesforce Inc."},
        {"symbol": "PYPL", "name": "PayPal Holdings"},
        {"symbol": "INTC", "name": "Intel Corp."},
        {"symbol": "UBER", "name": "Uber Technologies"},
        {"symbol": "SQ", "name": "Block Inc."},
        {"symbol": "COIN", "name": "Coinbase Global"},
    ]

    async def scan(
        self,
        strategy_id: str,
        filters: PreMarketScanFilter,
    ) -> PreMarketScanResult:
        """
        执行盘前扫描

        数据源优先级:
        1. Polygon API (实时数据)
        2. Mock 数据 (降级)
        """
        logger.info("执行盘前扫描", strategy_id=strategy_id)

        # 尝试从 Polygon 获取实时数据
        real_data = await self._fetch_polygon_data()

        if real_data:
            matched_stocks = await self._process_polygon_data(real_data, filters)
            _data_source_status.is_mock = False
            _data_source_status.source = "polygon"
            _data_source_status.error_message = None
            _data_source_status.last_sync = datetime.now()
            logger.info("使用 Polygon 实时数据", count=len(matched_stocks))
        else:
            matched_stocks = self._process_mock_data(filters)
            _data_source_status.is_mock = True
            _data_source_status.source = "mock"
            _data_source_status.error_message = "Polygon API 不可用，使用演示数据"
            logger.info("降级到 Mock 数据", count=len(matched_stocks))

        # 按评分排序
        matched_stocks.sort(key=lambda x: x.score, reverse=True)

        # 生成AI建议
        ai_suggestion = self._generate_ai_suggestion(matched_stocks[:10])

        return PreMarketScanResult(
            scan_time=datetime.now(),
            strategy_id=strategy_id,
            strategy_name=f"策略-{strategy_id[:8]}",
            filters_applied=filters,
            total_matched=len(matched_stocks),
            stocks=matched_stocks,
            ai_suggestion=ai_suggestion,
        )

    async def _fetch_polygon_data(self) -> Optional[list[dict]]:
        """从 Polygon 获取盘前涨跌榜数据"""
        try:
            # 获取涨幅榜和跌幅榜
            gainers = await _polygon_client.get_gainers_losers("gainers")
            losers = await _polygon_client.get_gainers_losers("losers")

            if gainers or losers:
                return gainers + losers
            return None
        except Exception as e:
            logger.warning("fetch_polygon_data_error", error=str(e))
            return None

    async def _process_polygon_data(
        self,
        tickers: list[dict],
        filters: PreMarketScanFilter
    ) -> list[PreMarketStock]:
        """处理 Polygon 返回的数据"""
        matched_stocks = []

        for ticker in tickers:
            try:
                symbol = ticker.get("ticker", "")
                day = ticker.get("day", {})
                prevDay = ticker.get("prevDay", {})

                if not day or not prevDay:
                    continue

                # 提取数据
                current_price = day.get("c", 0) or day.get("vw", 0)
                prev_close = prevDay.get("c", 0)

                if prev_close == 0:
                    continue

                gap = (current_price - prev_close) / prev_close
                volume = day.get("v", 0)
                prev_volume = prevDay.get("v", 1)
                vol_ratio = volume / prev_volume if prev_volume > 0 else 0

                # 计算波动率 (简化: 使用日内波动)
                high = day.get("h", current_price)
                low = day.get("l", current_price)
                volatility = (high - low) / current_price if current_price > 0 else 0

                avg_daily_value = prev_close * prev_volume

                # 应用筛选
                if abs(gap) < filters.min_gap:
                    continue
                if vol_ratio < filters.min_premarket_volume:
                    continue
                if volatility < filters.min_volatility:
                    continue
                if avg_daily_value < filters.min_liquidity:
                    continue

                # 计算评分
                score, breakdown = self._calculate_score(
                    gap=gap,
                    vol_ratio=vol_ratio,
                    volatility=volatility,
                    has_news=False,  # Polygon 免费版不提供新闻
                )

                # 从股票池获取名称，如果没有则用 symbol
                stock_info = next(
                    (s for s in self.SAMPLE_UNIVERSE if s["symbol"] == symbol),
                    {"symbol": symbol, "name": symbol}
                )

                stock = PreMarketStock(
                    symbol=symbol,
                    name=stock_info.get("name", symbol),
                    gap=gap,
                    gap_direction="up" if gap > 0 else "down",
                    premarket_price=current_price,
                    premarket_volume=int(volume),
                    premarket_volume_ratio=vol_ratio,
                    prev_close=prev_close,
                    prev_volume=int(prev_volume),
                    volatility=volatility,
                    avg_daily_volume=int(prev_volume),
                    avg_daily_value=avg_daily_value,
                    has_news=False,
                    news_headline=None,
                    is_earnings_day=False,
                    score=score,
                    score_breakdown=breakdown,
                )

                matched_stocks.append(stock)
            except Exception as e:
                logger.warning("process_ticker_error", ticker=ticker.get("ticker"), error=str(e))
                continue

        return matched_stocks

    def _process_mock_data(self, filters: PreMarketScanFilter) -> list[PreMarketStock]:
        """处理 Mock 数据"""
        matched_stocks = []

        for stock_info in self.SAMPLE_UNIVERSE:
            pm_data = self._generate_premarket_data(stock_info["symbol"])

            # 应用筛选条件
            if abs(pm_data["gap"]) < filters.min_gap:
                continue
            if pm_data["vol_ratio"] < filters.min_premarket_volume:
                continue
            if pm_data["volatility"] < filters.min_volatility:
                continue
            if pm_data["avg_daily_value"] < filters.min_liquidity:
                continue
            if filters.has_news is not None and pm_data["has_news"] != filters.has_news:
                continue
            if filters.is_earnings_day is not None and pm_data["is_earnings_day"] != filters.is_earnings_day:
                continue

            score, breakdown = self._calculate_score(
                gap=pm_data["gap"],
                vol_ratio=pm_data["vol_ratio"],
                volatility=pm_data["volatility"],
                has_news=pm_data["has_news"],
            )

            stock = PreMarketStock(
                symbol=stock_info["symbol"],
                name=stock_info["name"],
                gap=pm_data["gap"],
                gap_direction="up" if pm_data["gap"] > 0 else "down",
                premarket_price=pm_data["premarket_price"],
                premarket_volume=pm_data["premarket_volume"],
                premarket_volume_ratio=pm_data["vol_ratio"],
                prev_close=pm_data["prev_close"],
                prev_volume=pm_data["prev_volume"],
                volatility=pm_data["volatility"],
                avg_daily_volume=pm_data["avg_daily_volume"],
                avg_daily_value=pm_data["avg_daily_value"],
                has_news=pm_data["has_news"],
                news_headline=pm_data.get("news_headline"),
                is_earnings_day=pm_data["is_earnings_day"],
                score=score,
                score_breakdown=breakdown,
            )

            matched_stocks.append(stock)

        return matched_stocks

    def _generate_premarket_data(self, symbol: str) -> dict:
        """生成模拟盘前数据"""
        # 根据 symbol 生成稳定的随机数据
        seed = sum(ord(c) for c in symbol)
        random.seed(seed + datetime.now().day)

        prev_close = 100 + (seed % 200)
        gap = random.uniform(-0.08, 0.08)
        premarket_price = prev_close * (1 + gap)

        avg_daily_volume = random.randint(5000000, 50000000)
        vol_ratio = random.uniform(1.0, 5.0)

        has_news = random.random() > 0.7
        is_earnings_day = random.random() > 0.9

        news_headlines = [
            f"{symbol} 宣布重大并购计划",
            f"{symbol} 获得分析师上调评级",
            f"{symbol} 发布超预期财报",
            f"{symbol} CEO 发表重要声明",
            f"{symbol} 签署重大合作协议",
        ]

        return {
            "prev_close": prev_close,
            "premarket_price": premarket_price,
            "gap": gap,
            "premarket_volume": int(avg_daily_volume * vol_ratio * 0.1),
            "prev_volume": avg_daily_volume,
            "vol_ratio": vol_ratio,
            "volatility": random.uniform(0.02, 0.08),
            "avg_daily_volume": avg_daily_volume,
            "avg_daily_value": avg_daily_volume * prev_close,
            "has_news": has_news,
            "news_headline": random.choice(news_headlines) if has_news else None,
            "is_earnings_day": is_earnings_day,
        }

    def _calculate_score(
        self,
        gap: float,
        vol_ratio: float,
        volatility: float,
        has_news: bool,
    ) -> tuple[float, ScoreBreakdown]:
        """
        计算策略评分 (PRD 4.18.0)

        评分 = w1×Gap得分 + w2×成交量得分 + w3×波动率得分 + w4×新闻加分
        """
        # Gap得分: |Gap%| × 10 (上限50分)
        gap_score = min(abs(gap) * 100 * 10, 50)

        # 成交量得分: min(盘前量%, 500) / 10 (上限50分)
        volume_score = min(vol_ratio * 100, 500) / 10

        # 波动率得分: 波动率% × 5 (上限25分)
        volatility_score = min(volatility * 100 * 5, 25)

        # 新闻加分: 有新闻+10分
        news_score = 10 if has_news else 0

        # 加权计算
        total = (
            gap_score * 0.3 +
            volume_score * 0.3 +
            volatility_score * 0.2 +
            news_score
        )

        breakdown = ScoreBreakdown(
            gap=round(gap_score, 1),
            volume=round(volume_score, 1),
            volatility=round(volatility_score, 1),
            news=news_score,
        )

        return round(total, 1), breakdown

    def _generate_ai_suggestion(self, top_stocks: list[PreMarketStock]) -> str:
        """生成AI建议"""
        if not top_stocks:
            return "暂无符合条件的股票"

        news_stocks = [s for s in top_stocks if s.has_news]
        high_gap_stocks = [s for s in top_stocks if abs(s.gap) > 0.03]

        suggestions = []

        if news_stocks:
            symbols = ", ".join(s.symbol for s in news_stocks[:3])
            suggestions.append(f"{symbols} 今日有重大新闻催化，建议重点关注")

        if high_gap_stocks:
            symbols = ", ".join(s.symbol for s in high_gap_stocks[:2])
            suggestions.append(f"{symbols} 跳空幅度较大，注意风险控制")

        if not suggestions:
            return "今日候选股票波动正常，请按策略执行"

        return "；".join(suggestions)

    async def create_watchlist(
        self,
        user_id: str,
        request: CreateWatchlistRequest,
    ) -> IntradayWatchlist:
        """创建今日监控列表"""
        watchlist_id = str(uuid.uuid4())

        watchlist = IntradayWatchlist(
            watchlist_id=watchlist_id,
            user_id=user_id,
            strategy_id=request.strategy_id,
            date=date.today(),
            symbols=request.symbols[:20],  # 最多20只
            created_at=datetime.now(),
            is_confirmed=True,
        )

        # 存储 (以 user_id + strategy_id + date 为 key)
        key = f"{user_id}_{request.strategy_id}_{date.today()}"
        self._watchlists[key] = watchlist

        logger.info(
            "创建监控列表",
            watchlist_id=watchlist_id,
            symbols=request.symbols,
        )

        return watchlist

    async def get_today_watchlist(
        self,
        user_id: str,
        strategy_id: str,
    ) -> Optional[IntradayWatchlist]:
        """获取今日监控列表"""
        key = f"{user_id}_{strategy_id}_{date.today()}"
        return self._watchlists.get(key)

    async def get_watchlist_history(
        self,
        user_id: str,
        strategy_id: str,
        limit: int = 10,
    ) -> list[IntradayWatchlist]:
        """获取监控列表历史"""
        result = []
        prefix = f"{user_id}_{strategy_id}_"

        for key, watchlist in self._watchlists.items():
            if key.startswith(prefix):
                result.append(watchlist)

        result.sort(key=lambda x: x.date, reverse=True)
        return result[:limit]


# 单例服务
_pre_market_service: Optional[PreMarketService] = None


def get_pre_market_service() -> PreMarketService:
    """获取盘前扫描服务实例"""
    global _pre_market_service
    if _pre_market_service is None:
        _pre_market_service = PreMarketService()
    return _pre_market_service


def get_premarket_data_source_status() -> dict:
    """获取盘前服务数据源状态"""
    return _data_source_status.to_dict()
