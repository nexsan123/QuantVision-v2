"""
Phase 11: \u6570\u636e\u5c42\u5347\u7ea7 - \u6570\u636e ETL \u670d\u52a1

\u529f\u80fd:
- \u5386\u53f2\u6570\u636e\u540c\u6b65
- \u589e\u91cf\u6570\u636e\u66f4\u65b0
- \u6570\u636e\u8d28\u91cf\u68c0\u67e5
- \u7f3a\u5931\u6570\u636e\u586b\u5145
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.core.database import get_async_session
from app.models.market_data import (
    StockOHLCV,
    StockMinuteBar,
    DataSyncLog,
    DataQualityIssue,
)
from app.schemas.market_data import (
    DataSource,
    DataFrequency,
    DataSyncStatus,
    OHLCVBar,
    SymbolSyncStatus,
    DataQualityIssueType,
)
from app.services.data_source import data_source_manager

logger = structlog.get_logger()


class DataETLService:
    """数据 ETL 服务"""

    def __init__(self):
        self._sync_tasks: dict[str, asyncio.Task] = {}

    async def sync_historical_data(
        self,
        symbols: list[str],
        frequency: DataFrequency,
        start_date: str,
        end_date: str,
        source: DataSource | None = None,
    ) -> dict[str, Any]:
        """
        同步历史数据

        Args:
            symbols: 股票代码列表
            frequency: 数据频率
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            source: 数据源 (可选)

        Returns:
            同步结果摘要
        """
        results = {
            "total_symbols": len(symbols),
            "success_count": 0,
            "failed_count": 0,
            "total_bars": 0,
            "errors": [],
        }

        async with get_async_session() as session:
            for symbol in symbols:
                try:
                    # 创建同步日志
                    sync_log = DataSyncLog(
                        symbol=symbol,
                        frequency=frequency.value,
                        data_source=source.value if source else "auto",
                        start_date=datetime.fromisoformat(start_date),
                        end_date=datetime.fromisoformat(end_date),
                        status="syncing",
                    )
                    session.add(sync_log)
                    await session.flush()

                    start_time = datetime.now()

                    # 获取数据
                    bars = await data_source_manager.get_bars(
                        symbol=symbol,
                        frequency=frequency,
                        start_date=start_date,
                        end_date=end_date,
                        source=source,
                    )

                    # 保存到数据库
                    bars_saved = await self._save_bars(
                        session, symbol, frequency, bars
                    )

                    # 更新同步日志
                    sync_log.status = "completed"
                    sync_log.bars_synced = bars_saved
                    sync_log.duration_seconds = (
                        datetime.now() - start_time
                    ).total_seconds()

                    results["success_count"] += 1
                    results["total_bars"] += bars_saved

                    logger.info(
                        f"同步完成: {symbol}",
                        bars=bars_saved,
                        duration=sync_log.duration_seconds,
                    )

                except Exception as e:
                    sync_log.status = "failed"
                    sync_log.error_message = str(e)
                    results["failed_count"] += 1
                    results["errors"].append({"symbol": symbol, "error": str(e)})
                    logger.error(f"同步失败: {symbol}", error=str(e))

            await session.commit()

        return results

    async def _save_bars(
        self,
        session: AsyncSession,
        symbol: str,
        frequency: DataFrequency,
        bars: list[OHLCVBar],
    ) -> int:
        """保存 K 线数据"""
        if not bars:
            return 0

        if frequency == DataFrequency.DAY_1:
            # 日线数据
            for bar in bars:
                stmt = insert(StockOHLCV).values(
                    symbol=bar.symbol,
                    trade_date=bar.timestamp.date(),
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    vwap=bar.vwap,
                    trade_count=bar.trades,
                    source="etl",
                ).on_conflict_do_update(
                    constraint="uq_stock_ohlcv_symbol_date",
                    set_={
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                        "vwap": bar.vwap,
                    },
                )
                await session.execute(stmt)
        else:
            # 分钟数据
            for bar in bars:
                stmt = insert(StockMinuteBar).values(
                    symbol=bar.symbol,
                    timestamp=bar.timestamp,
                    frequency=frequency.value,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    vwap=bar.vwap,
                    trade_count=bar.trades,
                    source="etl",
                ).on_conflict_do_update(
                    index_elements=["symbol", "timestamp", "frequency"],
                    set_={
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                    },
                )
                await session.execute(stmt)

        return len(bars)

    async def get_sync_status(
        self,
        symbols: list[str] | None = None,
        frequency: DataFrequency = DataFrequency.DAY_1,
    ) -> list[SymbolSyncStatus]:
        """获取同步状态"""
        async with get_async_session() as session:
            # 查询最近的同步日志
            query = select(DataSyncLog).where(
                DataSyncLog.frequency == frequency.value
            ).order_by(DataSyncLog.created_at.desc())

            if symbols:
                query = query.where(DataSyncLog.symbol.in_(symbols))

            result = await session.execute(query)
            logs = result.scalars().all()

            # 按 symbol 分组，取最新
            latest_by_symbol = {}
            for log in logs:
                if log.symbol not in latest_by_symbol:
                    latest_by_symbol[log.symbol] = log

            # 构建状态列表
            statuses = []
            for symbol, log in latest_by_symbol.items():
                statuses.append(SymbolSyncStatus(
                    symbol=symbol,
                    last_sync_time=log.updated_at,
                    oldest_data=log.start_date,
                    newest_data=log.end_date,
                    total_bars=log.bars_synced,
                    frequency=frequency,
                    status=DataSyncStatus(log.status) if log.status in ["synced", "syncing", "error", "stale"] else DataSyncStatus.SYNCED,
                ))

            return statuses

    async def fill_missing_data(
        self,
        symbol: str,
        frequency: DataFrequency,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """
        填充缺失数据

        检测并填充时间序列中的缺口
        """
        async with get_async_session() as session:
            # 获取现有数据时间戳
            if frequency == DataFrequency.DAY_1:
                query = select(StockOHLCV.trade_date).where(
                    StockOHLCV.symbol == symbol,
                    StockOHLCV.trade_date >= start_date,
                    StockOHLCV.trade_date <= end_date,
                ).order_by(StockOHLCV.trade_date)
            else:
                query = select(StockMinuteBar.timestamp).where(
                    StockMinuteBar.symbol == symbol,
                    StockMinuteBar.frequency == frequency.value,
                    StockMinuteBar.timestamp >= start_date,
                    StockMinuteBar.timestamp <= end_date,
                ).order_by(StockMinuteBar.timestamp)

            result = await session.execute(query)
            existing_dates = set(row[0] for row in result.fetchall())

            # 生成预期的交易日/时间序列
            expected_dates = self._generate_expected_timestamps(
                frequency, start_date, end_date
            )

            # 找出缺失的日期
            missing_dates = expected_dates - existing_dates

            if not missing_dates:
                return {
                    "symbol": symbol,
                    "missing_count": 0,
                    "filled_count": 0,
                }

            # 尝试从数据源获取缺失数据
            filled_count = 0
            for missing_date in sorted(missing_dates):
                try:
                    date_str = missing_date.strftime("%Y-%m-%d") if isinstance(missing_date, datetime) else str(missing_date)
                    bars = await data_source_manager.get_bars(
                        symbol=symbol,
                        frequency=frequency,
                        start_date=date_str,
                        end_date=date_str,
                    )
                    if bars:
                        await self._save_bars(session, symbol, frequency, bars)
                        filled_count += len(bars)
                except Exception as e:
                    logger.warning(f"填充数据失败: {symbol} {missing_date}", error=str(e))

            await session.commit()

            return {
                "symbol": symbol,
                "missing_count": len(missing_dates),
                "filled_count": filled_count,
            }

    def _generate_expected_timestamps(
        self,
        frequency: DataFrequency,
        start_date: str,
        end_date: str,
    ) -> set:
        """生成预期的时间戳序列"""
        from pandas.tseries.offsets import BDay

        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)

        if frequency == DataFrequency.DAY_1:
            # 工作日序列
            dates = pd.date_range(start, end, freq=BDay())
            return set(d.date() for d in dates)
        else:
            # 分钟级别 (9:30 - 16:00 美东时间)
            dates = []
            current = start
            while current <= end:
                if current.weekday() < 5:  # 工作日
                    market_open = current.replace(hour=9, minute=30)
                    market_close = current.replace(hour=16, minute=0)

                    freq_map = {
                        DataFrequency.MIN_1: "1T",
                        DataFrequency.MIN_5: "5T",
                        DataFrequency.MIN_15: "15T",
                        DataFrequency.MIN_30: "30T",
                        DataFrequency.HOUR_1: "1H",
                    }
                    intraday = pd.date_range(
                        market_open, market_close,
                        freq=freq_map.get(frequency, "1T")
                    )
                    dates.extend(intraday.to_pydatetime())

                current += timedelta(days=1)

            return set(dates)

    async def check_data_quality(
        self,
        symbols: list[str],
        frequency: DataFrequency,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """
        数据质量检查

        检测:
        - 缺失数据
        - 异常值
        - 无效 OHLC
        - 零成交量
        - 价格跳空
        """
        issues = []

        async with get_async_session() as session:
            for symbol in symbols:
                # 获取数据
                if frequency == DataFrequency.DAY_1:
                    query = select(StockOHLCV).where(
                        StockOHLCV.symbol == symbol,
                        StockOHLCV.trade_date >= start_date,
                        StockOHLCV.trade_date <= end_date,
                    ).order_by(StockOHLCV.trade_date)
                else:
                    query = select(StockMinuteBar).where(
                        StockMinuteBar.symbol == symbol,
                        StockMinuteBar.frequency == frequency.value,
                        StockMinuteBar.timestamp >= start_date,
                        StockMinuteBar.timestamp <= end_date,
                    ).order_by(StockMinuteBar.timestamp)

                result = await session.execute(query)
                bars = result.scalars().all()

                if not bars:
                    continue

                # 转换为 DataFrame
                df = pd.DataFrame([{
                    "timestamp": getattr(b, "trade_date", None) or b.timestamp,
                    "open": float(b.open),
                    "high": float(b.high),
                    "low": float(b.low),
                    "close": float(b.close),
                    "volume": int(b.volume),
                } for b in bars])

                # 检查无效 OHLC
                invalid_ohlc = df[
                    (df["high"] < df["low"]) |
                    (df["open"] > df["high"]) |
                    (df["open"] < df["low"]) |
                    (df["close"] > df["high"]) |
                    (df["close"] < df["low"])
                ]
                for _, row in invalid_ohlc.iterrows():
                    issues.append({
                        "symbol": symbol,
                        "timestamp": row["timestamp"],
                        "issue_type": "invalid_ohlc",
                        "severity": "high",
                        "description": f"无效 OHLC: O={row['open']}, H={row['high']}, L={row['low']}, C={row['close']}",
                    })

                # 检查零成交量
                zero_volume = df[df["volume"] == 0]
                for _, row in zero_volume.iterrows():
                    issues.append({
                        "symbol": symbol,
                        "timestamp": row["timestamp"],
                        "issue_type": "zero_volume",
                        "severity": "medium",
                        "description": "成交量为零",
                    })

                # 检查价格跳空 (>10%)
                df["return"] = df["close"].pct_change()
                large_gaps = df[abs(df["return"]) > 0.10]
                for _, row in large_gaps.iterrows():
                    if pd.notna(row["return"]):
                        issues.append({
                            "symbol": symbol,
                            "timestamp": row["timestamp"],
                            "issue_type": "price_gap",
                            "severity": "medium",
                            "description": f"价格跳空 {row['return']:.2%}",
                        })

                # 检查异常值 (超过 5 倍标准差)
                df["zscore"] = (df["close"] - df["close"].mean()) / df["close"].std()
                outliers = df[abs(df["zscore"]) > 5]
                for _, row in outliers.iterrows():
                    issues.append({
                        "symbol": symbol,
                        "timestamp": row["timestamp"],
                        "issue_type": "outlier",
                        "severity": "high",
                        "description": f"异常值: 价格 {row['close']}, Z-score={row['zscore']:.2f}",
                    })

            # 保存问题到数据库
            for issue in issues:
                dq_issue = DataQualityIssue(
                    symbol=issue["symbol"],
                    issue_timestamp=issue["timestamp"],
                    issue_type=issue["issue_type"],
                    severity=issue["severity"],
                    description=issue["description"],
                )
                session.add(dq_issue)

            await session.commit()

        return issues


# 全局 ETL 服务实例
data_etl_service = DataETLService()
