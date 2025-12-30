"""
增量计算调度器

管理因子的增量计算任务，实现:
1. 自动检测需要更新的因子
2. 优先级调度
3. 失败重试
4. 性能统计
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

import pandas as pd
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.factor_cache import (
    FactorDefinition,
    IncrementalSchedule,
)
from app.services.factor_cache_service import FactorCacheService

logger = logging.getLogger(__name__)


class IncrementalScheduler:
    """
    增量计算调度器

    核心功能:
    1. 识别需要增量计算的因子
    2. 按优先级执行计算任务
    3. 管理计算进度和失败重试
    4. 提供统计和监控接口
    """

    def __init__(
        self,
        db: AsyncSession,
        cache_service: FactorCacheService,
        compute_func: Optional[Callable] = None,
    ):
        """
        初始化调度器

        Args:
            db: 数据库会话
            cache_service: 缓存服务
            compute_func: 因子计算函数 (可选，用于实际计算)
        """
        self.db = db
        self.cache_service = cache_service
        self.compute_func = compute_func
        self._is_running = False
        self._current_task: Optional[str] = None

    # =========================================================================
    # 调度管理
    # =========================================================================

    async def register_factor(
        self,
        factor_id: str,
        priority: int = 0,
        enabled: bool = True,
    ) -> IncrementalSchedule:
        """
        注册因子到增量计算调度

        Args:
            factor_id: 因子 ID
            priority: 优先级 (越大越优先)
            enabled: 是否启用

        Returns:
            调度配置对象
        """
        # 检查是否已注册
        existing = await self._get_schedule(factor_id)
        if existing:
            existing.priority = priority
            existing.is_enabled = enabled
            await self.db.commit()
            return existing

        schedule = IncrementalSchedule(
            factor_id=factor_id,
            priority=priority,
            is_enabled=enabled,
        )
        self.db.add(schedule)
        await self.db.commit()

        logger.info(f"注册因子调度: {factor_id}, 优先级={priority}")
        return schedule

    async def unregister_factor(self, factor_id: str) -> bool:
        """取消因子的增量计算调度"""
        schedule = await self._get_schedule(factor_id)
        if schedule:
            await self.db.delete(schedule)
            await self.db.commit()
            return True
        return False

    async def _get_schedule(self, factor_id: str) -> Optional[IncrementalSchedule]:
        """获取因子调度配置"""
        result = await self.db.execute(
            select(IncrementalSchedule).where(
                IncrementalSchedule.factor_id == factor_id
            )
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # 增量计算核心
    # =========================================================================

    async def get_pending_factors(
        self,
        current_date: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        获取需要增量计算的因子列表

        Args:
            current_date: 当前日期 (YYYY-MM-DD)
            limit: 返回数量限制

        Returns:
            需要计算的因子列表，按优先级排序
        """
        query = (
            select(IncrementalSchedule, FactorDefinition)
            .join(
                FactorDefinition,
                IncrementalSchedule.factor_id == FactorDefinition.id,
            )
            .where(IncrementalSchedule.is_enabled == True)  # noqa: E712
            .where(
                # 从未计算或需要更新
                (IncrementalSchedule.last_success_date.is_(None))
                | (IncrementalSchedule.last_success_date < current_date)
            )
            .where(
                # 未超过重试限制
                IncrementalSchedule.consecutive_failures
                < IncrementalSchedule.max_retries
            )
            .order_by(
                IncrementalSchedule.priority.desc(),
                IncrementalSchedule.last_success_date.asc().nullsfirst(),
            )
            .limit(limit)
        )

        result = await self.db.execute(query)
        rows = result.all()

        pending = []
        for schedule, factor in rows:
            pending.append({
                "factor_id": factor.id,
                "factor_name": factor.name,
                "expression": factor.expression,
                "last_computed": schedule.last_success_date,
                "priority": schedule.priority,
                "failures": schedule.consecutive_failures,
            })

        return pending

    async def compute_incremental(
        self,
        factor_id: str,
        target_date: str,
        market_data: pd.DataFrame,
        force_full: bool = False,
    ) -> dict[str, Any]:
        """
        执行因子增量计算

        Args:
            factor_id: 因子 ID
            target_date: 目标日期
            market_data: 市场数据 DataFrame
            force_full: 强制全量计算

        Returns:
            计算结果统计
        """
        self._current_task = factor_id
        start_time = datetime.utcnow()

        try:
            factor = await self.cache_service.get_factor_by_id(factor_id)
            if not factor:
                raise ValueError(f"因子不存在: {factor_id}")

            # 确定计算日期范围
            if force_full or not factor.last_computed_date:
                # 全量计算
                start_date = (
                    datetime.strptime(target_date, "%Y-%m-%d")
                    - timedelta(days=factor.lookback_period + 252)
                ).strftime("%Y-%m-%d")
                dates_to_compute = self._get_trading_dates(start_date, target_date)
            else:
                # 增量计算
                last_date = factor.last_computed_date
                dates_to_compute = await self.cache_service.get_missing_dates(
                    factor_id,
                    self._get_trading_dates(last_date, target_date),
                )

            # 创建计算日志
            log = await self.cache_service.create_compute_log(
                factor_id=factor_id,
                start_date=dates_to_compute[0] if dates_to_compute else target_date,
                end_date=target_date,
                symbol_count=len(market_data.columns) if isinstance(market_data, pd.DataFrame) else 0,
            )

            rows_computed = 0
            rows_cached = 0

            if dates_to_compute:
                # 检查缓存命中
                cached_df = await self.cache_service.get_cached_values(
                    factor_id,
                    dates_to_compute[0],
                    dates_to_compute[-1],
                )

                if not cached_df.empty:
                    rows_cached = len(cached_df) * len(cached_df.columns)

                # 计算缺失的日期
                missing_dates = [
                    d for d in dates_to_compute
                    if d not in cached_df.index
                ]

                if missing_dates and self.compute_func:
                    # 执行实际计算
                    factor_values = await self._execute_compute(
                        factor.expression,
                        market_data,
                        missing_dates,
                    )

                    # 保存到缓存
                    rows_computed = await self.cache_service.save_factor_values(
                        factor_id,
                        factor_values,
                    )

            # 更新因子计算时间
            factor.last_computed_at = datetime.utcnow()
            factor.last_computed_date = target_date

            # 更新调度状态
            await self._update_schedule_success(factor_id, target_date)

            # 完成日志
            await self.cache_service.complete_compute_log(
                log,
                rows_computed=rows_computed,
                rows_cached=rows_cached,
            )

            duration = (datetime.utcnow() - start_time).total_seconds()

            result = {
                "factor_id": factor_id,
                "factor_name": factor.name,
                "dates_computed": len(dates_to_compute),
                "rows_computed": rows_computed,
                "rows_cached": rows_cached,
                "cache_hit_rate": (
                    rows_cached / (rows_computed + rows_cached) * 100
                    if (rows_computed + rows_cached) > 0
                    else 0
                ),
                "duration_seconds": round(duration, 2),
                "status": "success",
            }

            logger.info(
                f"增量计算完成: {factor.name}, "
                f"计算 {rows_computed} 条, 缓存命中 {rows_cached} 条, "
                f"耗时 {duration:.2f}s"
            )

            return result

        except Exception as e:
            # 记录失败
            await self._update_schedule_failure(factor_id, str(e))
            logger.error(f"增量计算失败: {factor_id}, 错误: {e}")

            return {
                "factor_id": factor_id,
                "status": "failed",
                "error": str(e),
            }

        finally:
            self._current_task = None

    async def _execute_compute(
        self,
        expression: str,
        market_data: pd.DataFrame,
        dates: list[str],
    ) -> pd.DataFrame:
        """
        执行因子计算

        这是一个模板方法，实际计算逻辑由 compute_func 提供
        """
        if self.compute_func:
            return await self.compute_func(expression, market_data, dates)

        # 默认返回空 DataFrame
        logger.warning("未设置计算函数，返回空结果")
        return pd.DataFrame()

    # =========================================================================
    # 调度状态更新
    # =========================================================================

    async def _update_schedule_success(
        self,
        factor_id: str,
        computed_date: str,
    ) -> None:
        """更新调度状态 (成功)"""
        await self.db.execute(
            update(IncrementalSchedule)
            .where(IncrementalSchedule.factor_id == factor_id)
            .values(
                last_success_date=computed_date,
                consecutive_failures=0,
                last_error=None,
            )
        )
        await self.db.commit()

    async def _update_schedule_failure(
        self,
        factor_id: str,
        error: str,
    ) -> None:
        """更新调度状态 (失败)"""
        schedule = await self._get_schedule(factor_id)
        if schedule:
            schedule.consecutive_failures += 1
            schedule.last_error = error
            await self.db.commit()

    # =========================================================================
    # 批量调度
    # =========================================================================

    async def run_batch(
        self,
        current_date: str,
        market_data: pd.DataFrame,
        batch_size: int = 5,
        max_concurrent: int = 3,
    ) -> list[dict[str, Any]]:
        """
        批量执行增量计算

        Args:
            current_date: 当前日期
            market_data: 市场数据
            batch_size: 批次大小
            max_concurrent: 最大并发数

        Returns:
            计算结果列表
        """
        self._is_running = True
        results = []

        try:
            pending = await self.get_pending_factors(current_date, batch_size)

            if not pending:
                logger.info("没有待计算的因子")
                return results

            logger.info(f"开始批量计算: {len(pending)} 个因子")

            # 并发执行
            semaphore = asyncio.Semaphore(max_concurrent)

            async def compute_with_limit(factor_info):
                async with semaphore:
                    return await self.compute_incremental(
                        factor_info["factor_id"],
                        current_date,
                        market_data,
                    )

            tasks = [compute_with_limit(f) for f in pending]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理异常
            results = [
                r if not isinstance(r, Exception) else {"status": "error", "error": str(r)}
                for r in results
            ]

            success_count = sum(1 for r in results if r.get("status") == "success")
            logger.info(f"批量计算完成: {success_count}/{len(pending)} 成功")

            return results

        finally:
            self._is_running = False

    # =========================================================================
    # 工具方法
    # =========================================================================

    def _get_trading_dates(
        self,
        start_date: str,
        end_date: str,
    ) -> list[str]:
        """
        获取交易日期列表

        简化实现，实际应该从交易日历获取
        """
        dates = pd.date_range(start=start_date, end=end_date, freq="B")
        return [d.strftime("%Y-%m-%d") for d in dates]

    # =========================================================================
    # 监控接口
    # =========================================================================

    async def get_scheduler_status(self) -> dict[str, Any]:
        """获取调度器状态"""
        # 统计各状态因子数量
        result = await self.db.execute(select(IncrementalSchedule))
        schedules = result.scalars().all()

        enabled_count = sum(1 for s in schedules if s.is_enabled)
        failed_count = sum(1 for s in schedules if s.consecutive_failures > 0)

        return {
            "is_running": self._is_running,
            "current_task": self._current_task,
            "total_factors": len(schedules),
            "enabled_factors": enabled_count,
            "failed_factors": failed_count,
        }

    async def get_factor_schedule_status(
        self,
        factor_id: str,
    ) -> Optional[dict[str, Any]]:
        """获取单个因子的调度状态"""
        schedule = await self._get_schedule(factor_id)
        if not schedule:
            return None

        return {
            "factor_id": factor_id,
            "is_enabled": schedule.is_enabled,
            "priority": schedule.priority,
            "last_success_date": schedule.last_success_date,
            "next_compute_date": schedule.next_compute_date,
            "consecutive_failures": schedule.consecutive_failures,
            "last_error": schedule.last_error,
        }

    async def reset_failures(self, factor_id: str) -> bool:
        """重置因子的失败计数"""
        schedule = await self._get_schedule(factor_id)
        if schedule:
            schedule.consecutive_failures = 0
            schedule.last_error = None
            await self.db.commit()
            logger.info(f"重置失败计数: {factor_id}")
            return True
        return False
