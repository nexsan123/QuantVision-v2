"""
因子缓存服务

提供因子值缓存、版本控制、增量计算等功能
目标: 提升 90% 计算效率
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import pandas as pd
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factor_cache import (
    FactorAnalysisCache,
    FactorComputeLog,
    FactorDefinition,
    FactorValue,
    IncrementalSchedule,
)

logger = logging.getLogger(__name__)


class FactorCacheService:
    """
    因子缓存服务

    功能:
    1. 因子定义管理 (CRUD + 版本控制)
    2. 因子值缓存 (读写 + 批量操作)
    3. 分析结果缓存 (IC分析、分组回测等)
    4. 缓存失效管理
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # 因子定义管理
    # =========================================================================

    async def create_factor(
        self,
        name: str,
        expression: str,
        category: str = "custom",
        description: str = "",
        lookback_period: int = 252,
        frequency: str = "daily",
    ) -> FactorDefinition:
        """
        创建因子定义

        Args:
            name: 因子名称 (唯一)
            expression: 因子表达式
            category: 因子类别
            description: 描述
            lookback_period: 回望周期
            frequency: 计算频率

        Returns:
            创建的因子定义对象
        """
        code_hash = FactorDefinition.compute_code_hash(expression)

        factor = FactorDefinition(
            name=name,
            expression=expression,
            code_hash=code_hash,
            category=category,
            description=description,
            lookback_period=lookback_period,
            frequency=frequency,
        )

        self.db.add(factor)
        await self.db.commit()
        await self.db.refresh(factor)

        logger.info(f"创建因子: {name}, hash: {code_hash[:8]}...")
        return factor

    async def get_factor_by_name(self, name: str) -> Optional[FactorDefinition]:
        """根据名称获取因子定义"""
        result = await self.db.execute(
            select(FactorDefinition).where(FactorDefinition.name == name)
        )
        return result.scalar_one_or_none()

    async def get_factor_by_id(self, factor_id: str) -> Optional[FactorDefinition]:
        """根据 ID 获取因子定义"""
        result = await self.db.execute(
            select(FactorDefinition).where(FactorDefinition.id == factor_id)
        )
        return result.scalar_one_or_none()

    async def update_factor_expression(
        self,
        factor_id: str,
        new_expression: str,
    ) -> tuple[FactorDefinition, bool]:
        """
        更新因子表达式

        Args:
            factor_id: 因子 ID
            new_expression: 新表达式

        Returns:
            (更新后的因子, 是否版本变化)
        """
        factor = await self.get_factor_by_id(factor_id)
        if not factor:
            raise ValueError(f"因子不存在: {factor_id}")

        factor.expression = new_expression
        version_changed = factor.update_hash()

        if version_changed:
            # 版本变化，需要失效缓存
            await self._invalidate_factor_cache(factor_id)
            logger.info(f"因子 {factor.name} 版本更新: v{factor.version}")

        await self.db.commit()
        return factor, version_changed

    async def _invalidate_factor_cache(self, factor_id: str) -> int:
        """
        失效因子相关缓存

        Returns:
            删除的缓存数量
        """
        # 删除因子值缓存
        result = await self.db.execute(
            delete(FactorValue).where(FactorValue.factor_id == factor_id)
        )
        values_deleted = result.rowcount

        # 失效分析缓存
        await self.db.execute(
            select(FactorAnalysisCache)
            .where(FactorAnalysisCache.factor_id == factor_id)
            .execution_options(synchronize_session="fetch")
        )
        result = await self.db.execute(
            delete(FactorAnalysisCache).where(
                FactorAnalysisCache.factor_id == factor_id
            )
        )
        analysis_deleted = result.rowcount

        logger.info(
            f"因子缓存失效: 因子值 {values_deleted} 条, 分析结果 {analysis_deleted} 条"
        )
        return values_deleted + analysis_deleted

    # =========================================================================
    # 因子值缓存
    # =========================================================================

    async def get_cached_values(
        self,
        factor_id: str,
        start_date: str,
        end_date: str,
        symbols: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        获取缓存的因子值

        Args:
            factor_id: 因子 ID
            start_date: 开始日期
            end_date: 结束日期
            symbols: 股票列表 (可选)

        Returns:
            因子值 DataFrame (index=date, columns=symbol)
        """
        query = select(FactorValue).where(
            and_(
                FactorValue.factor_id == factor_id,
                FactorValue.trade_date >= start_date,
                FactorValue.trade_date <= end_date,
            )
        )

        if symbols:
            query = query.where(FactorValue.symbol.in_(symbols))

        result = await self.db.execute(query)
        rows = result.scalars().all()

        if not rows:
            return pd.DataFrame()

        # 转换为 DataFrame
        data = [
            {"date": r.trade_date, "symbol": r.symbol, "value": r.value}
            for r in rows
        ]
        df = pd.DataFrame(data)
        return df.pivot(index="date", columns="symbol", values="value")

    async def get_missing_dates(
        self,
        factor_id: str,
        required_dates: list[str],
        symbols: Optional[list[str]] = None,
    ) -> list[str]:
        """
        获取缺失的日期 (需要计算的日期)

        Args:
            factor_id: 因子 ID
            required_dates: 需要的日期列表
            symbols: 股票列表

        Returns:
            缺失日期列表
        """
        # 查询已有日期
        query = (
            select(FactorValue.trade_date)
            .where(FactorValue.factor_id == factor_id)
            .where(FactorValue.trade_date.in_(required_dates))
            .distinct()
        )

        result = await self.db.execute(query)
        cached_dates = set(r[0] for r in result.all())

        missing = [d for d in required_dates if d not in cached_dates]
        return missing

    async def save_factor_values(
        self,
        factor_id: str,
        df: pd.DataFrame,
        compute_zscore: bool = True,
    ) -> int:
        """
        保存因子值到缓存

        Args:
            factor_id: 因子 ID
            df: 因子值 DataFrame (index=date, columns=symbol)
            compute_zscore: 是否计算横截面标准化

        Returns:
            保存的行数
        """
        if df.empty:
            return 0

        rows_to_insert = []

        for date in df.index:
            row_data = df.loc[date]
            valid_data = row_data.dropna()

            if valid_data.empty:
                continue

            # 计算横截面统计
            if compute_zscore:
                mean = valid_data.mean()
                std = valid_data.std()
                zscore_data = (valid_data - mean) / (std + 1e-8)
                percentile_data = valid_data.rank(pct=True)
            else:
                zscore_data = pd.Series(index=valid_data.index)
                percentile_data = pd.Series(index=valid_data.index)

            for symbol in valid_data.index:
                rows_to_insert.append(
                    FactorValue(
                        factor_id=factor_id,
                        trade_date=str(date),
                        symbol=symbol,
                        value=float(valid_data[symbol]),
                        zscore=float(zscore_data.get(symbol, 0)),
                        percentile=float(percentile_data.get(symbol, 0.5)),
                    )
                )

        # 批量插入
        if rows_to_insert:
            self.db.add_all(rows_to_insert)
            await self.db.commit()

        logger.info(f"保存因子值: {len(rows_to_insert)} 条")
        return len(rows_to_insert)

    # =========================================================================
    # 分析结果缓存
    # =========================================================================

    async def get_analysis_cache(
        self,
        factor_id: str,
        analysis_type: str,
        start_date: str,
        end_date: str,
        parameters: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        获取分析结果缓存

        Args:
            factor_id: 因子 ID
            analysis_type: 分析类型
            start_date: 开始日期
            end_date: 结束日期
            parameters: 其他参数

        Returns:
            缓存的分析结果 (如果存在且有效)
        """
        # 获取因子当前版本
        factor = await self.get_factor_by_id(factor_id)
        if not factor:
            return None

        query = select(FactorAnalysisCache).where(
            and_(
                FactorAnalysisCache.factor_id == factor_id,
                FactorAnalysisCache.analysis_type == analysis_type,
                FactorAnalysisCache.start_date == start_date,
                FactorAnalysisCache.end_date == end_date,
                FactorAnalysisCache.factor_version == factor.version,
                FactorAnalysisCache.is_valid == True,  # noqa: E712
            )
        )

        result = await self.db.execute(query)
        cache = result.scalar_one_or_none()

        if cache and not cache.is_expired():
            logger.debug(f"分析缓存命中: {analysis_type}")
            return cache.result

        return None

    async def save_analysis_cache(
        self,
        factor_id: str,
        analysis_type: str,
        start_date: str,
        end_date: str,
        result: dict,
        parameters: Optional[dict] = None,
        ttl_hours: int = 24,
    ) -> FactorAnalysisCache:
        """
        保存分析结果缓存

        Args:
            factor_id: 因子 ID
            analysis_type: 分析类型
            start_date: 开始日期
            end_date: 结束日期
            result: 分析结果
            parameters: 其他参数
            ttl_hours: 缓存有效期 (小时)

        Returns:
            创建的缓存对象
        """
        factor = await self.get_factor_by_id(factor_id)
        if not factor:
            raise ValueError(f"因子不存在: {factor_id}")

        # 删除旧缓存
        await self.db.execute(
            delete(FactorAnalysisCache).where(
                and_(
                    FactorAnalysisCache.factor_id == factor_id,
                    FactorAnalysisCache.analysis_type == analysis_type,
                    FactorAnalysisCache.start_date == start_date,
                    FactorAnalysisCache.end_date == end_date,
                )
            )
        )

        cache = FactorAnalysisCache(
            factor_id=factor_id,
            analysis_type=analysis_type,
            start_date=start_date,
            end_date=end_date,
            result=result,
            parameters=parameters or {},
            factor_version=factor.version,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
        )

        self.db.add(cache)
        await self.db.commit()

        logger.info(f"保存分析缓存: {analysis_type}, TTL={ttl_hours}h")
        return cache

    # =========================================================================
    # 计算日志
    # =========================================================================

    async def create_compute_log(
        self,
        factor_id: str,
        start_date: str,
        end_date: str,
        symbol_count: int,
    ) -> FactorComputeLog:
        """创建计算日志"""
        log = FactorComputeLog(
            factor_id=factor_id,
            start_date=start_date,
            end_date=end_date,
            symbol_count=symbol_count,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(log)
        await self.db.commit()
        return log

    async def complete_compute_log(
        self,
        log: FactorComputeLog,
        rows_computed: int,
        rows_cached: int,
        error: Optional[str] = None,
    ) -> None:
        """完成计算日志"""
        log.completed_at = datetime.utcnow()
        log.duration_seconds = (
            log.completed_at - log.started_at
        ).total_seconds()
        log.rows_computed = rows_computed
        log.rows_cached = rows_cached

        if error:
            log.status = "failed"
            log.error_message = error
        else:
            log.status = "completed"

        await self.db.commit()

    # =========================================================================
    # 统计信息
    # =========================================================================

    async def get_cache_stats(self, factor_id: str) -> dict[str, Any]:
        """
        获取因子缓存统计信息

        Returns:
            包含缓存命中率、数据量等统计
        """
        # 统计因子值数量
        result = await self.db.execute(
            select(FactorValue)
            .where(FactorValue.factor_id == factor_id)
        )
        values_count = len(result.scalars().all())

        # 统计分析缓存数量
        result = await self.db.execute(
            select(FactorAnalysisCache)
            .where(FactorAnalysisCache.factor_id == factor_id)
            .where(FactorAnalysisCache.is_valid == True)  # noqa: E712
        )
        analysis_count = len(result.scalars().all())

        # 获取计算日志统计
        result = await self.db.execute(
            select(FactorComputeLog)
            .where(FactorComputeLog.factor_id == factor_id)
            .order_by(FactorComputeLog.started_at.desc())
            .limit(10)
        )
        recent_logs = result.scalars().all()

        total_computed = sum(l.rows_computed or 0 for l in recent_logs)
        total_cached = sum(l.rows_cached or 0 for l in recent_logs)
        cache_hit_rate = (
            total_cached / (total_computed + total_cached) * 100
            if (total_computed + total_cached) > 0
            else 0
        )

        return {
            "factor_id": factor_id,
            "values_count": values_count,
            "analysis_cache_count": analysis_count,
            "recent_compute_count": len(recent_logs),
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
        }
