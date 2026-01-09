"""
历史数据服务
PRD 4.17 策略回放功能

提供回放所需的K线和因子数据
"""

import random
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import AsyncGenerator, Optional

from app.schemas.replay import FactorSnapshot, HistoricalBar, ThresholdConfig


class HistoricalDataService:
    """历史数据服务"""

    def __init__(self):
        self._cache: dict[str, list[HistoricalBar]] = {}

    async def get_historical_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "5m",
    ) -> list[HistoricalBar]:
        """
        获取历史K线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            interval: K线周期 (1m, 5m, 15m, 1H, 1D)

        Returns:
            K线数据列表
        """
        cache_key = f"{symbol}_{start_date}_{end_date}_{interval}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # 模拟生成历史数据
        bars = self._generate_mock_bars(symbol, start_date, end_date, interval)
        self._cache[cache_key] = bars

        return bars

    async def get_factor_snapshots(
        self,
        strategy_id: str,
        symbol: str,
        start_date: date,
        end_date: date,
    ) -> dict[datetime, FactorSnapshot]:
        """
        获取历史因子快照

        Args:
            strategy_id: 策略ID
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            按时间索引的因子快照字典
        """
        # 获取K线数据
        bars = await self.get_historical_bars(symbol, start_date, end_date)

        # 为每个K线生成因子快照
        snapshots: dict[datetime, FactorSnapshot] = {}

        for i, bar in enumerate(bars):
            snapshot = self._calculate_factors(bar, bars[: i + 1])
            snapshots[bar.timestamp] = snapshot

        return snapshots

    async def stream_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        speed: float = 1.0,
    ) -> AsyncGenerator[HistoricalBar, None]:
        """
        流式返回K线 (用于实时回放)

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            speed: 播放速度倍数

        Yields:
            历史K线数据
        """
        import asyncio

        bars = await self.get_historical_bars(symbol, start_date, end_date)

        # 根据速度计算间隔
        base_interval = 1.0  # 基础1秒
        interval = base_interval / speed

        for bar in bars:
            yield bar
            await asyncio.sleep(interval)

    def _generate_mock_bars(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        interval: str = "5m",
    ) -> list[HistoricalBar]:
        """生成模拟K线数据"""
        bars = []

        # 根据股票设置基础价格
        base_prices = {
            "NVDA": 520.0,
            "TSLA": 250.0,
            "AAPL": 185.0,
            "MSFT": 420.0,
            "AMD": 145.0,
            "META": 510.0,
            "GOOGL": 175.0,
            "AMZN": 185.0,
        }
        base_price = base_prices.get(symbol, 100.0)

        # 计算K线数量
        interval_minutes = {"1m": 1, "5m": 5, "15m": 15, "1H": 60, "1D": 390}.get(
            interval, 5
        )
        trading_minutes_per_day = 390  # 6.5小时

        current_date = start_date
        current_price = base_price

        while current_date <= end_date:
            # 跳过周末
            if current_date.weekday() < 5:
                # 生成当天的K线
                market_open = datetime.combine(
                    current_date, datetime.strptime("09:30", "%H:%M").time()
                )

                bars_per_day = trading_minutes_per_day // interval_minutes

                for i in range(bars_per_day):
                    timestamp = market_open + timedelta(minutes=i * interval_minutes)

                    # 生成价格波动
                    volatility = 0.002  # 0.2%波动
                    change = random.gauss(0, volatility)

                    open_price = current_price
                    close_price = open_price * (1 + change)
                    high_price = max(open_price, close_price) * (
                        1 + abs(random.gauss(0, volatility / 2))
                    )
                    low_price = min(open_price, close_price) * (
                        1 - abs(random.gauss(0, volatility / 2))
                    )

                    # 生成成交量
                    base_volume = 100000
                    volume = int(base_volume * (1 + random.gauss(0, 0.5)))

                    bar = HistoricalBar(
                        timestamp=timestamp,
                        open=Decimal(str(round(open_price, 2))),
                        high=Decimal(str(round(high_price, 2))),
                        low=Decimal(str(round(low_price, 2))),
                        close=Decimal(str(round(close_price, 2))),
                        volume=max(volume, 1000),
                    )
                    bars.append(bar)

                    current_price = close_price

            current_date += timedelta(days=1)

        return bars

    def _calculate_factors(
        self, bar: HistoricalBar, historical_bars: list[HistoricalBar]
    ) -> FactorSnapshot:
        """计算因子值"""
        close_prices = [float(b.close) for b in historical_bars]
        current_close = float(bar.close)

        # RSI计算 (简化版)
        rsi = self._calculate_rsi(close_prices, 14)

        # MACD计算 (简化版)
        macd, signal = self._calculate_macd(close_prices)

        # 波动率计算
        volatility = self._calculate_volatility(close_prices, 20)

        # 成交量比率
        volumes = [b.volume for b in historical_bars]
        volume_ratio = (
            bar.volume / (sum(volumes[-20:]) / min(len(volumes), 20))
            if len(volumes) > 0
            else 1.0
        )

        # 因子值
        factor_values = {
            "RSI": rsi,
            "MACD": macd,
            "MACD_Signal": signal,
            "Volatility": volatility,
            "Volume_Ratio": volume_ratio,
            "close": current_close,
        }

        # 阈值检查
        thresholds = {
            "RSI": ThresholdConfig(value=30, direction="below", passed=rsi < 30),
            "MACD": ThresholdConfig(
                value=0, direction="above", passed=macd > signal
            ),
            "Volatility": ThresholdConfig(
                value=0.03, direction="above", passed=volatility > 0.03
            ),
            "Volume_Ratio": ThresholdConfig(
                value=1.5, direction="above", passed=volume_ratio > 1.5
            ),
        }

        # 计算满足条件数
        conditions_met = sum(1 for t in thresholds.values() if t.passed)
        conditions_total = len(thresholds)

        # 综合信号
        if conditions_met >= 3:
            overall_signal = "buy"
        elif conditions_met <= 1:
            overall_signal = "sell"
        else:
            overall_signal = "hold"

        return FactorSnapshot(
            timestamp=bar.timestamp,
            factor_values=factor_values,
            thresholds=thresholds,
            overall_signal=overall_signal,
            conditions_met=conditions_met,
            conditions_total=conditions_total,
        )

    def _calculate_rsi(self, prices: list[float], period: int = 14) -> float:
        """计算RSI"""
        if len(prices) < period + 1:
            return 50.0

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def _calculate_macd(
        self, prices: list[float], fast: int = 12, slow: int = 26, signal: int = 9
    ) -> tuple[float, float]:
        """计算MACD"""
        if len(prices) < slow:
            return 0.0, 0.0

        # 简化EMA计算
        def ema(data: list[float], period: int) -> float:
            if len(data) < period:
                return sum(data) / len(data)
            multiplier = 2 / (period + 1)
            ema_val = sum(data[:period]) / period
            for price in data[period:]:
                ema_val = (price - ema_val) * multiplier + ema_val
            return ema_val

        ema_fast = ema(prices, fast)
        ema_slow = ema(prices, slow)
        macd = ema_fast - ema_slow

        # 简化signal计算
        signal_val = macd * 0.8  # 简化

        return round(macd, 4), round(signal_val, 4)

    def _calculate_volatility(self, prices: list[float], period: int = 20) -> float:
        """计算波动率"""
        if len(prices) < 2:
            return 0.0

        returns = [
            (prices[i] - prices[i - 1]) / prices[i - 1]
            for i in range(1, min(len(prices), period + 1))
        ]

        if len(returns) == 0:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance**0.5

        return round(volatility, 4)


# 单例
_service: Optional[HistoricalDataService] = None


def get_historical_data_service() -> HistoricalDataService:
    """获取历史数据服务单例"""
    global _service
    if _service is None:
        _service = HistoricalDataService()
    return _service
