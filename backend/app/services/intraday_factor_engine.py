"""
Phase 11: \u6570\u636e\u5c42\u5347\u7ea7 - \u65e5\u5185\u56e0\u5b50\u8ba1\u7b97\u5f15\u64ce

\u652f\u6301\u7684\u65e5\u5185\u56e0\u5b50:
- relative_volume: \u76f8\u5bf9\u6210\u4ea4\u91cf
- vwap_deviation: VWAP\u504f\u79bb
- buy_pressure: \u4e70\u5356\u538b\u529b
- price_momentum_5min: 5\u5206\u949f\u52a8\u91cf
- price_momentum_15min: 15\u5206\u949f\u52a8\u91cf
- intraday_volatility: \u65e5\u5185\u6ce2\u52a8
- spread_ratio: \u4e70\u5356\u4ef7\u5dee\u6bd4
- order_imbalance: \u8ba2\u5355\u4e0d\u5e73\u8861
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.market_data import StockMinuteBar, IntradayFactor
from app.schemas.market_data import (
    IntradayFactorType,
    IntradayFactorValue,
    IntradayFactorSnapshot,
    DataFrequency,
)

logger = structlog.get_logger()


class IntradayFactorEngine:
    """\u65e5\u5185\u56e0\u5b50\u8ba1\u7b97\u5f15\u64ce"""

    def __init__(self):
        # \u5386\u53f2\u6570\u636e\u7f13\u5b58 (\u7528\u4e8e\u8ba1\u7b97\u6eda\u52a8\u7edf\u8ba1)
        self._volume_history: dict[str, pd.DataFrame] = {}
        self._price_history: dict[str, pd.DataFrame] = {}

    async def calculate_factors(
        self,
        symbol: str,
        timestamp: datetime | None = None,
    ) -> IntradayFactorSnapshot:
        """
        \u8ba1\u7b97\u5355\u53ea\u80a1\u7968\u7684\u6240\u6709\u65e5\u5185\u56e0\u5b50

        Args:
            symbol: \u80a1\u7968\u4ee3\u7801
            timestamp: \u65f6\u95f4\u6233 (\u9ed8\u8ba4\u4e3a\u5f53\u524d\u65f6\u95f4)

        Returns:
            \u56e0\u5b50\u5feb\u7167
        """
        if timestamp is None:
            timestamp = datetime.now()

        # \u83b7\u53d6\u6240\u9700\u6570\u636e
        async with get_async_session() as session:
            bars = await self._get_intraday_bars(session, symbol, timestamp)

        if len(bars) < 2:
            return IntradayFactorSnapshot(
                symbol=symbol,
                timestamp=timestamp,
                factors={},
            )

        df = pd.DataFrame(bars)

        # \u8ba1\u7b97\u5404\u56e0\u5b50
        factors = {}

        # \u76f8\u5bf9\u6210\u4ea4\u91cf
        rv = self._calc_relative_volume(df)
        if rv is not None:
            factors[IntradayFactorType.RELATIVE_VOLUME.value] = rv

        # VWAP \u504f\u79bb
        vwap_dev = self._calc_vwap_deviation(df)
        if vwap_dev is not None:
            factors[IntradayFactorType.VWAP_DEVIATION.value] = vwap_dev

        # 5\u5206\u949f\u52a8\u91cf
        mom_5 = self._calc_price_momentum(df, 5)
        if mom_5 is not None:
            factors[IntradayFactorType.PRICE_MOMENTUM_5MIN.value] = mom_5

        # 15\u5206\u949f\u52a8\u91cf
        mom_15 = self._calc_price_momentum(df, 15)
        if mom_15 is not None:
            factors[IntradayFactorType.PRICE_MOMENTUM_15MIN.value] = mom_15

        # \u65e5\u5185\u6ce2\u52a8\u7387
        vol = self._calc_intraday_volatility(df)
        if vol is not None:
            factors[IntradayFactorType.INTRADAY_VOLATILITY.value] = vol

        # \u4e70\u5356\u4ef7\u5dee\u6bd4 (\u9700\u8981 quote \u6570\u636e)
        spread = self._calc_spread_ratio(df)
        if spread is not None:
            factors[IntradayFactorType.SPREAD_RATIO.value] = spread

        return IntradayFactorSnapshot(
            symbol=symbol,
            timestamp=timestamp,
            factors=factors,
        )

    async def calculate_batch(
        self,
        symbols: list[str],
        timestamp: datetime | None = None,
    ) -> list[IntradayFactorSnapshot]:
        """\u6279\u91cf\u8ba1\u7b97\u591a\u53ea\u80a1\u7968\u7684\u56e0\u5b50"""
        results = []
        for symbol in symbols:
            try:
                snapshot = await self.calculate_factors(symbol, timestamp)
                results.append(snapshot)
            except Exception as e:
                logger.warning(f"\u8ba1\u7b97\u56e0\u5b50\u5931\u8d25: {symbol}", error=str(e))

        return results

    async def _get_intraday_bars(
        self,
        session: AsyncSession,
        symbol: str,
        timestamp: datetime,
    ) -> list[dict]:
        """\u83b7\u53d6\u5f53\u65e5\u5206\u949f\u6570\u636e"""
        # \u83b7\u53d6\u5f53\u65e5\u5f00\u76d8\u65f6\u95f4
        today_open = timestamp.replace(hour=9, minute=30, second=0, microsecond=0)

        query = select(StockMinuteBar).where(
            StockMinuteBar.symbol == symbol,
            StockMinuteBar.frequency == "1min",
            StockMinuteBar.timestamp >= today_open,
            StockMinuteBar.timestamp <= timestamp,
        ).order_by(StockMinuteBar.timestamp)

        result = await session.execute(query)
        bars = result.scalars().all()

        return [
            {
                "timestamp": bar.timestamp,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
                "vwap": bar.vwap,
            }
            for bar in bars
        ]

    def _calc_relative_volume(self, df: pd.DataFrame) -> float | None:
        """
        \u8ba1\u7b97\u76f8\u5bf9\u6210\u4ea4\u91cf

        \u5f53\u524d10\u5206\u949f\u6210\u4ea4\u91cf / \u5386\u53f220\u5929\u540c\u65f6\u6bb5\u5e73\u5747\u6210\u4ea4\u91cf
        """
        if len(df) < 10:
            return None

        # \u6700\u8fd110\u5206\u949f\u6210\u4ea4\u91cf
        recent_volume = df["volume"].tail(10).sum()

        # \u7b80\u5316\u5904\u7406\uff1a\u4f7f\u7528\u5f53\u65e5\u5e73\u5747\u4f5c\u4e3a\u57fa\u51c6
        # \u5b9e\u9645\u5e94\u8be5\u7528\u5386\u53f2\u540c\u65f6\u6bb5\u6570\u636e
        avg_volume = df["volume"].mean() * 10

        if avg_volume == 0:
            return None

        return recent_volume / avg_volume

    def _calc_vwap_deviation(self, df: pd.DataFrame) -> float | None:
        """
        \u8ba1\u7b97 VWAP \u504f\u79bb

        (\u5f53\u524d\u4ef7 - VWAP) / VWAP
        """
        if len(df) == 0:
            return None

        current_close = df["close"].iloc[-1]

        # \u8ba1\u7b97 VWAP
        if "vwap" in df.columns and df["vwap"].iloc[-1] is not None:
            vwap = df["vwap"].iloc[-1]
        else:
            # \u81ea\u5df1\u8ba1\u7b97
            typical_price = (df["high"] + df["low"] + df["close"]) / 3
            vwap = (typical_price * df["volume"]).sum() / df["volume"].sum()

        if vwap == 0:
            return None

        return (current_close - vwap) / vwap

    def _calc_price_momentum(
        self,
        df: pd.DataFrame,
        minutes: int,
    ) -> float | None:
        """
        \u8ba1\u7b97\u4ef7\u683c\u52a8\u91cf

        close / delay(close, N) - 1
        """
        if len(df) < minutes + 1:
            return None

        current_close = df["close"].iloc[-1]
        past_close = df["close"].iloc[-minutes - 1]

        if past_close == 0:
            return None

        return (current_close / past_close) - 1

    def _calc_intraday_volatility(self, df: pd.DataFrame) -> float | None:
        """
        \u8ba1\u7b97\u65e5\u5185\u6ce2\u52a8\u7387

        std(returns) * sqrt(390) \u5e74\u5316
        """
        if len(df) < 10:
            return None

        returns = df["close"].pct_change().dropna()

        if len(returns) < 5:
            return None

        # \u5e74\u5316 (\u5047\u8bbe\u6bcf\u5929 390 \u5206\u949f)
        return returns.std() * np.sqrt(390 * 252)

    def _calc_spread_ratio(self, df: pd.DataFrame) -> float | None:
        """
        \u8ba1\u7b97\u4e70\u5356\u4ef7\u5dee\u6bd4

        (high - low) / ((high + low) / 2)

        \u4f7f\u7528 high-low \u4f5c\u4e3a spread \u7684\u8fd1\u4f3c
        """
        if len(df) == 0:
            return None

        last_bar = df.iloc[-1]
        mid = (last_bar["high"] + last_bar["low"]) / 2

        if mid == 0:
            return None

        return (last_bar["high"] - last_bar["low"]) / mid

    async def save_factors(
        self,
        snapshots: list[IntradayFactorSnapshot],
    ) -> int:
        """\u4fdd\u5b58\u56e0\u5b50\u5230\u6570\u636e\u5e93"""
        saved_count = 0

        async with get_async_session() as session:
            for snapshot in snapshots:
                for factor_id, value in snapshot.factors.items():
                    factor = IntradayFactor(
                        symbol=snapshot.symbol,
                        timestamp=snapshot.timestamp,
                        factor_id=factor_id,
                        value=value,
                    )
                    session.add(factor)
                    saved_count += 1

            await session.commit()

        return saved_count

    async def get_factor_history(
        self,
        symbol: str,
        factor_id: IntradayFactorType,
        start_time: datetime,
        end_time: datetime,
    ) -> list[IntradayFactorValue]:
        """\u83b7\u53d6\u56e0\u5b50\u5386\u53f2\u6570\u636e"""
        async with get_async_session() as session:
            query = select(IntradayFactor).where(
                IntradayFactor.symbol == symbol,
                IntradayFactor.factor_id == factor_id.value,
                IntradayFactor.timestamp >= start_time,
                IntradayFactor.timestamp <= end_time,
            ).order_by(IntradayFactor.timestamp)

            result = await session.execute(query)
            factors = result.scalars().all()

            return [
                IntradayFactorValue(
                    symbol=f.symbol,
                    timestamp=f.timestamp,
                    factor_id=IntradayFactorType(f.factor_id),
                    value=f.value,
                    zscore=f.zscore,
                    percentile=f.percentile,
                )
                for f in factors
            ]

    async def get_latest_factors(
        self,
        symbols: list[str],
    ) -> dict[str, IntradayFactorSnapshot]:
        """\u83b7\u53d6\u591a\u53ea\u80a1\u7968\u7684\u6700\u65b0\u56e0\u5b50"""
        async with get_async_session() as session:
            results = {}

            for symbol in symbols:
                # \u83b7\u53d6\u6700\u65b0\u65f6\u95f4\u6233
                subquery = select(func.max(IntradayFactor.timestamp)).where(
                    IntradayFactor.symbol == symbol
                )
                result = await session.execute(subquery)
                latest_time = result.scalar()

                if latest_time is None:
                    continue

                # \u83b7\u53d6\u8be5\u65f6\u95f4\u6233\u7684\u6240\u6709\u56e0\u5b50
                query = select(IntradayFactor).where(
                    IntradayFactor.symbol == symbol,
                    IntradayFactor.timestamp == latest_time,
                )
                result = await session.execute(query)
                factors = result.scalars().all()

                if factors:
                    results[symbol] = IntradayFactorSnapshot(
                        symbol=symbol,
                        timestamp=latest_time,
                        factors={f.factor_id: f.value for f in factors},
                    )

            return results


class IntradayFactorScheduler:
    """\u65e5\u5185\u56e0\u5b50\u8ba1\u7b97\u8c03\u5ea6\u5668"""

    def __init__(self, engine: IntradayFactorEngine):
        self.engine = engine
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(
        self,
        symbols: list[str],
        interval_seconds: int = 60,
    ):
        """\u542f\u52a8\u5b9a\u65f6\u8ba1\u7b97"""
        self._running = True

        while self._running:
            try:
                # \u68c0\u67e5\u662f\u5426\u5728\u4ea4\u6613\u65f6\u95f4
                now = datetime.now()
                if self._is_market_hours(now):
                    snapshots = await self.engine.calculate_batch(symbols, now)
                    await self.engine.save_factors(snapshots)
                    logger.info(
                        f"\u56e0\u5b50\u8ba1\u7b97\u5b8c\u6210",
                        symbols=len(symbols),
                        factors=sum(len(s.factors) for s in snapshots),
                    )

                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error("\u56e0\u5b50\u8ba1\u7b97\u8c03\u5ea6\u5668\u9519\u8bef", error=str(e))
                await asyncio.sleep(interval_seconds)

    def stop(self):
        """\u505c\u6b62\u8c03\u5ea6\u5668"""
        self._running = False

    def _is_market_hours(self, dt: datetime) -> bool:
        """\u68c0\u67e5\u662f\u5426\u5728\u4ea4\u6613\u65f6\u95f4"""
        # \u7b80\u5316\uff1a\u5468\u4e00\u81f3\u5468\u4e94 9:30-16:00 (\u7f8e\u4e1c\u65f6\u95f4)
        if dt.weekday() >= 5:  # \u5468\u672b
            return False

        market_open = dt.replace(hour=9, minute=30)
        market_close = dt.replace(hour=16, minute=0)

        return market_open <= dt <= market_close


# \u5168\u5c40\u5b9e\u4f8b
intraday_factor_engine = IntradayFactorEngine()
