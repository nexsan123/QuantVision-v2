"""
数据加载服务

提供 Point-in-Time (PIT) 数据加载:
- 行情数据加载
- 财务数据加载
- 宏观数据加载
"""

from collections.abc import AsyncGenerator
from datetime import date

import pandas as pd
import structlog
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.models.financial_data import FinancialStatement
from app.models.market_data import MacroData, StockOHLCV
from app.models.universe import Universe, UniverseSnapshot

logger = structlog.get_logger()


class DataLoader:
    """
    PIT 数据加载器

    确保回测时数据无前视偏差:
    - 行情数据: 使用 trade_date
    - 财务数据: 使用 release_date (非 report_date)
    - 宏观数据: 使用 release_date
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # === 行情数据 ===

    async def load_ohlcv(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        """
        加载股票 OHLCV 数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            MultiIndex DataFrame (symbol, trade_date)
        """
        query = select(StockOHLCV).where(
            and_(
                StockOHLCV.symbol.in_(symbols),
                StockOHLCV.trade_date >= start_date,
                StockOHLCV.trade_date <= end_date,
            )
        ).order_by(StockOHLCV.symbol, StockOHLCV.trade_date)

        result = await self.db.execute(query)
        rows = result.scalars().all()

        if not rows:
            logger.warning("未找到行情数据", symbols=symbols, start=start_date, end=end_date)
            return pd.DataFrame()

        data = []
        for row in rows:
            data.append({
                "symbol": row.symbol,
                "trade_date": row.trade_date,
                "open": float(row.open),
                "high": float(row.high),
                "low": float(row.low),
                "close": float(row.close),
                "volume": row.volume,
                "adj_close": float(row.adj_close) if row.adj_close else float(row.close),
                "vwap": float(row.vwap) if row.vwap else None,
            })

        df = pd.DataFrame(data)
        df["trade_date"] = pd.to_datetime(df["trade_date"])
        df = df.set_index(["symbol", "trade_date"]).sort_index()

        logger.info(
            "加载行情数据完成",
            symbols=len(symbols),
            rows=len(df),
        )

        return df

    async def load_returns(
        self,
        symbols: list[str],
        start_date: date,
        end_date: date,
        periods: int = 1,
    ) -> pd.DataFrame:
        """
        加载收益率数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            periods: 收益率周期 (1=日收益, 5=周收益, 20=月收益)

        Returns:
            收益率 DataFrame
        """
        df = await self.load_ohlcv(symbols, start_date, end_date)
        if df.empty:
            return pd.DataFrame()

        # 计算收益率
        returns = df["adj_close"].unstack("symbol").pct_change(periods)
        returns = returns.stack("symbol").to_frame("returns")

        return returns

    # === 财务数据 (PIT) ===

    async def load_financials_pit(
        self,
        symbols: list[str],
        as_of_date: date,
        lookback_quarters: int = 4,
    ) -> pd.DataFrame:
        """
        加载 PIT 财务数据

        使用 release_date 确保无前视偏差:
        只返回在 as_of_date 之前已发布的财报

        Args:
            symbols: 股票代码列表
            as_of_date: 观察日期
            lookback_quarters: 回望季度数

        Returns:
            最近 N 个季度的财务数据
        """
        # 查询在 as_of_date 之前已发布的财报
        query = select(FinancialStatement).where(
            and_(
                FinancialStatement.symbol.in_(symbols),
                FinancialStatement.release_date <= as_of_date,
            )
        ).order_by(
            FinancialStatement.symbol,
            FinancialStatement.release_date.desc(),
        )

        result = await self.db.execute(query)
        rows = result.scalars().all()

        if not rows:
            logger.warning("未找到财务数据 (PIT)", symbols=symbols, as_of=as_of_date)
            return pd.DataFrame()

        # 每个股票保留最近 N 个季度
        data = []
        symbol_counts: dict[str, int] = {}

        for row in rows:
            count = symbol_counts.get(row.symbol, 0)
            if count >= lookback_quarters:
                continue

            data.append({
                "symbol": row.symbol,
                "report_date": row.report_date,
                "release_date": row.release_date,
                "fiscal_year": row.fiscal_year,
                "fiscal_period": row.fiscal_period.value,
                # 利润表
                "revenue": float(row.revenue) if row.revenue else None,
                "net_income": float(row.net_income) if row.net_income else None,
                "eps": float(row.eps) if row.eps else None,
                # 资产负债表
                "total_assets": float(row.total_assets) if row.total_assets else None,
                "total_equity": float(row.total_equity) if row.total_equity else None,
                # 现金流
                "operating_cash_flow": float(row.operating_cash_flow) if row.operating_cash_flow else None,
                "free_cash_flow": float(row.free_cash_flow) if row.free_cash_flow else None,
            })

            symbol_counts[row.symbol] = count + 1

        df = pd.DataFrame(data)
        df["report_date"] = pd.to_datetime(df["report_date"])
        df["release_date"] = pd.to_datetime(df["release_date"])

        logger.info(
            "加载 PIT 财务数据完成",
            symbols=len(symbols),
            as_of=as_of_date,
            rows=len(df),
        )

        return df

    # === 宏观数据 (PIT) ===

    async def load_macro_pit(
        self,
        indicators: list[str],
        as_of_date: date,
    ) -> pd.DataFrame:
        """
        加载 PIT 宏观数据

        Args:
            indicators: 指标代码列表
            as_of_date: 观察日期

        Returns:
            最新可用的宏观数据
        """
        # 对每个指标，获取在 as_of_date 之前最新发布的数据
        data = []

        for indicator in indicators:
            query = select(MacroData).where(
                and_(
                    MacroData.indicator == indicator,
                    MacroData.release_date <= as_of_date,
                )
            ).order_by(MacroData.release_date.desc()).limit(1)

            result = await self.db.execute(query)
            row = result.scalar_one_or_none()

            if row:
                data.append({
                    "indicator": row.indicator,
                    "report_date": row.report_date,
                    "release_date": row.release_date,
                    "value": float(row.value),
                    "unit": row.unit,
                })

        if not data:
            logger.warning("未找到宏观数据 (PIT)", indicators=indicators, as_of=as_of_date)
            return pd.DataFrame()

        df = pd.DataFrame(data)

        logger.info(
            "加载 PIT 宏观数据完成",
            indicators=len(indicators),
            as_of=as_of_date,
            rows=len(df),
        )

        return df

    # === 股票池 ===

    async def load_universe_pit(
        self,
        universe_name: str,
        as_of_date: date,
    ) -> list[str]:
        """
        加载 PIT 股票池成分股

        Args:
            universe_name: 股票池名称
            as_of_date: 观察日期

        Returns:
            成分股列表
        """
        # 先查找股票池
        universe_query = select(Universe).where(Universe.name == universe_name)
        result = await self.db.execute(universe_query)
        universe = result.scalar_one_or_none()

        if not universe:
            logger.warning("未找到股票池", name=universe_name)
            return []

        # 获取最近的快照
        snapshot_query = select(UniverseSnapshot).where(
            and_(
                UniverseSnapshot.universe_id == universe.id,
                UniverseSnapshot.snapshot_date <= as_of_date,
            )
        ).order_by(UniverseSnapshot.snapshot_date.desc()).limit(1)

        result = await self.db.execute(snapshot_query)
        snapshot: UniverseSnapshot | None = result.scalar_one_or_none()  # type: ignore[assignment]

        if not snapshot:
            logger.warning(
                "未找到股票池快照",
                name=universe_name,
                as_of=as_of_date,
            )
            return []

        logger.info(
            "加载 PIT 股票池完成",
            name=universe_name,
            as_of=as_of_date,
            symbols=len(snapshot.symbols),
        )

        return snapshot.symbols


async def get_data_loader() -> AsyncGenerator[DataLoader, None]:
    """获取数据加载器实例"""
    async with get_db_context() as db:
        yield DataLoader(db)
