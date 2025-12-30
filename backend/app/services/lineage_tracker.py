"""
数据血缘追踪服务

提供:
- 数据获取记录
- 处理流程追踪
- 质量检测结果记录
- 血缘查询
"""

from datetime import date, datetime
from typing import Any
from uuid import uuid4

import structlog
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.models.data_lineage import DataLineage, DataSourceType, DataStatus

logger = structlog.get_logger()


class LineageTracker:
    """
    数据血缘追踪器

    记录数据的来源、处理过程和质量状态:
    - 开始任务: 创建血缘记录
    - 更新进度: 更新处理状态
    - 完成任务: 记录最终结果
    - 查询血缘: 追溯数据来源
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_task(
        self,
        task_type: str,
        source: DataSourceType,
        symbols: list[str] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        开始数据任务，创建血缘记录

        Args:
            task_type: 任务类型 (fetch_ohlcv, fetch_financials, etc.)
            source: 数据来源
            symbols: 处理的股票列表
            start_date: 数据起始日期
            end_date: 数据结束日期
            task_id: Celery 任务 ID (可选)
            metadata: 附加元数据

        Returns:
            血缘记录 ID
        """
        lineage = DataLineage(
            id=str(uuid4()),
            task_type=task_type,
            task_id=task_id,
            source=source,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            status=DataStatus.PENDING,
            started_at=datetime.now(),
            metadata_=metadata,
        )

        self.db.add(lineage)
        await self.db.commit()

        logger.info(
            "开始数据任务",
            lineage_id=lineage.id,
            task_type=task_type,
            source=source.value,
        )

        return lineage.id

    async def update_progress(
        self,
        lineage_id: str,
        records_fetched: int | None = None,
        records_inserted: int | None = None,
        records_updated: int | None = None,
        records_failed: int | None = None,
        status: DataStatus | None = None,
    ) -> None:
        """
        更新任务进度

        Args:
            lineage_id: 血缘记录 ID
            records_fetched: 已获取记录数
            records_inserted: 已插入记录数
            records_updated: 已更新记录数
            records_failed: 失败记录数
            status: 当前状态
        """
        update_values: dict[str, Any] = {}

        if records_fetched is not None:
            update_values["records_fetched"] = records_fetched
        if records_inserted is not None:
            update_values["records_inserted"] = records_inserted
        if records_updated is not None:
            update_values["records_updated"] = records_updated
        if records_failed is not None:
            update_values["records_failed"] = records_failed
        if status is not None:
            update_values["status"] = status

        if update_values:
            stmt = (
                update(DataLineage)
                .where(DataLineage.id == lineage_id)
                .values(**update_values)
            )
            await self.db.execute(stmt)
            await self.db.commit()

    async def complete_task(
        self,
        lineage_id: str,
        status: DataStatus,
        records_fetched: int = 0,
        records_inserted: int = 0,
        records_updated: int = 0,
        records_failed: int = 0,
        quality_score: float | None = None,
        missing_rate: float | None = None,
        anomaly_count: int = 0,
        error_message: str | None = None,
    ) -> None:
        """
        完成任务，记录最终结果

        Args:
            lineage_id: 血缘记录 ID
            status: 最终状态
            records_fetched: 获取记录数
            records_inserted: 插入记录数
            records_updated: 更新记录数
            records_failed: 失败记录数
            quality_score: 数据质量评分
            missing_rate: 缺失率
            anomaly_count: 异常值数量
            error_message: 错误信息
        """
        # 获取记录计算时长
        query = select(DataLineage).where(DataLineage.id == lineage_id)
        result = await self.db.execute(query)
        lineage = result.scalar_one_or_none()

        duration = None
        if lineage and lineage.started_at:
            duration = (datetime.now() - lineage.started_at).total_seconds()

        # 更新记录
        stmt = (
            update(DataLineage)
            .where(DataLineage.id == lineage_id)
            .values(
                status=status,
                completed_at=datetime.now(),
                duration_seconds=duration,
                records_fetched=records_fetched,
                records_inserted=records_inserted,
                records_updated=records_updated,
                records_failed=records_failed,
                quality_score=quality_score,
                missing_rate=missing_rate,
                anomaly_count=anomaly_count,
                error_message=error_message,
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

        logger.info(
            "数据任务完成",
            lineage_id=lineage_id,
            status=status.value,
            duration=f"{duration:.1f}s" if duration else None,
            fetched=records_fetched,
            inserted=records_inserted,
            failed=records_failed,
        )

    async def fail_task(
        self,
        lineage_id: str,
        error_message: str,
    ) -> None:
        """
        任务失败

        Args:
            lineage_id: 血缘记录 ID
            error_message: 错误信息
        """
        await self.complete_task(
            lineage_id=lineage_id,
            status=DataStatus.FAILED,
            error_message=error_message,
        )

        logger.error(
            "数据任务失败",
            lineage_id=lineage_id,
            error=error_message,
        )

    async def get_lineage(self, lineage_id: str) -> DataLineage | None:
        """
        获取血缘记录

        Args:
            lineage_id: 血缘记录 ID

        Returns:
            血缘记录
        """
        query = select(DataLineage).where(DataLineage.id == lineage_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_task_history(
        self,
        task_type: str | None = None,
        source: DataSourceType | None = None,
        status: DataStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
    ) -> list[DataLineage]:
        """
        查询任务历史

        Args:
            task_type: 任务类型过滤
            source: 数据来源过滤
            status: 状态过滤
            start_date: 开始日期过滤
            end_date: 结束日期过滤
            limit: 最大返回数量

        Returns:
            血缘记录列表
        """
        conditions = []

        if task_type:
            conditions.append(DataLineage.task_type == task_type)
        if source:
            conditions.append(DataLineage.source == source)
        if status:
            conditions.append(DataLineage.status == status)
        if start_date:
            conditions.append(DataLineage.created_at >= start_date)
        if end_date:
            conditions.append(DataLineage.created_at <= end_date)

        query = (
            select(DataLineage)
            .where(and_(*conditions) if conditions else True)
            .order_by(DataLineage.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_successful(
        self,
        task_type: str,
        source: DataSourceType | None = None,
    ) -> DataLineage | None:
        """
        获取最近成功的任务记录

        Args:
            task_type: 任务类型
            source: 数据来源

        Returns:
            最近的成功记录
        """
        conditions = [
            DataLineage.task_type == task_type,
            DataLineage.status == DataStatus.SUCCESS,
        ]

        if source:
            conditions.append(DataLineage.source == source)

        query = (
            select(DataLineage)
            .where(and_(*conditions))
            .order_by(DataLineage.completed_at.desc())
            .limit(1)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_statistics(
        self,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        获取血缘统计

        Args:
            days: 统计天数

        Returns:
            统计信息
        """
        cutoff = datetime.now().date()
        from datetime import timedelta
        start = cutoff - timedelta(days=days)

        query = select(DataLineage).where(
            DataLineage.created_at >= start
        )

        result = await self.db.execute(query)
        records = list(result.scalars().all())

        total = len(records)
        success = sum(1 for r in records if r.status == DataStatus.SUCCESS)
        failed = sum(1 for r in records if r.status == DataStatus.FAILED)
        partial = sum(1 for r in records if r.status == DataStatus.PARTIAL)

        total_fetched = sum(r.records_fetched for r in records)
        total_inserted = sum(r.records_inserted for r in records)
        total_failed_records = sum(r.records_failed for r in records)

        avg_quality = None
        quality_scores = [r.quality_score for r in records if r.quality_score is not None]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)

        return {
            "period_days": days,
            "total_tasks": total,
            "success_count": success,
            "failed_count": failed,
            "partial_count": partial,
            "success_rate": success / total if total > 0 else 0,
            "total_records_fetched": total_fetched,
            "total_records_inserted": total_inserted,
            "total_records_failed": total_failed_records,
            "average_quality_score": avg_quality,
        }


async def get_lineage_tracker() -> LineageTracker:
    """获取血缘追踪器实例"""
    async with get_db_context() as db:
        yield LineageTracker(db)
