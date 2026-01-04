"""
Phase 11: \u6570\u636e\u5c42\u5347\u7ea7 - \u5e02\u573a\u6570\u636e API

\u63d0\u4f9b:
- \u5386\u53f2\u6570\u636e\u67e5\u8be2
- \u5b9e\u65f6\u884c\u60c5
- \u65e5\u5185\u56e0\u5b50
- \u6570\u636e\u540c\u6b65\u7ba1\u7406
- \u6570\u636e\u8d28\u91cf\u76d1\u63a7
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
import structlog

from app.schemas.market_data import (
    DataSource,
    DataFrequency,
    HistoricalDataRequest,
    HistoricalDataResponse,
    DataSourceListResponse,
    SyncStatusResponse,
    IntradayFactorsResponse,
    DataQualityReport,
    MarketSnapshot,
    IntradayFactorSnapshot,
    INTRADAY_FACTOR_DEFINITIONS,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/market-data", tags=["\u5e02\u573a\u6570\u636e"])


# === \u6570\u636e\u6e90\u7ba1\u7406 ===

@router.get("/sources", response_model=DataSourceListResponse)
async def list_data_sources() -> DataSourceListResponse:
    """\u83b7\u53d6\u53ef\u7528\u6570\u636e\u6e90\u5217\u8868"""
    from app.services.data_source import data_source_manager

    sources = data_source_manager.get_all_sources()

    return DataSourceListResponse(
        sources=sources,
        primary_source=data_source_manager._primary_source,
    )


@router.post("/sources/{source}/test")
async def test_data_source(source: DataSource) -> dict[str, Any]:
    """\u6d4b\u8bd5\u6570\u636e\u6e90\u8fde\u63a5"""
    from app.services.data_source import data_source_manager

    try:
        ds = data_source_manager.get_source(source)
        snapshot = await ds.get_snapshot("AAPL")

        return {
            "status": "ok",
            "source": source.value,
            "latency_ms": ds.latency_ms,
            "test_symbol": "AAPL",
            "test_price": snapshot.last_price if snapshot else None,
        }
    except Exception as e:
        return {
            "status": "error",
            "source": source.value,
            "error": str(e),
        }


# === \u5386\u53f2\u6570\u636e ===

@router.post("/historical", response_model=list[HistoricalDataResponse])
async def get_historical_data(
    request: HistoricalDataRequest,
) -> list[HistoricalDataResponse]:
    """
    \u83b7\u53d6\u5386\u53f2K\u7ebf\u6570\u636e

    \u652f\u6301\u9891\u7387: 1min, 5min, 15min, 30min, 1hour, 1day
    """
    from app.services.data_source import data_source_manager

    results = []

    for symbol in request.symbols:
        try:
            bars = await data_source_manager.get_bars(
                symbol=symbol,
                frequency=request.frequency,
                start_date=request.start_date,
                end_date=request.end_date,
                adjusted=request.adjusted_price,
                source=request.data_source,
            )

            results.append(HistoricalDataResponse(
                symbol=symbol,
                frequency=request.frequency,
                bars=bars,
                total_count=len(bars),
                data_source=request.data_source or DataSource.ALPACA,
            ))

        except Exception as e:
            logger.error(f"\u83b7\u53d6 {symbol} \u5386\u53f2\u6570\u636e\u5931\u8d25", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    return results


@router.get("/snapshot/{symbol}", response_model=MarketSnapshot)
async def get_market_snapshot(
    symbol: str,
    source: DataSource | None = Query(None),
) -> MarketSnapshot:
    """\u83b7\u53d6\u5e02\u573a\u5feb\u7167"""
    from app.services.data_source import data_source_manager

    snapshot = await data_source_manager.get_snapshot(symbol, source)

    if not snapshot:
        raise HTTPException(status_code=404, detail=f"\u65e0\u6cd5\u83b7\u53d6 {symbol} \u7684\u5e02\u573a\u6570\u636e")

    return snapshot


@router.post("/snapshots")
async def get_multiple_snapshots(
    symbols: list[str],
) -> dict[str, MarketSnapshot]:
    """\u6279\u91cf\u83b7\u53d6\u5e02\u573a\u5feb\u7167"""
    from app.services.data_source import data_source_manager

    return await data_source_manager.get_multiple_snapshots(symbols)


# === \u6570\u636e\u540c\u6b65 ===

@router.post("/sync")
async def sync_historical_data(
    symbols: list[str],
    frequency: DataFrequency = DataFrequency.DAY_1,
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    source: DataSource | None = None,
    background_tasks: BackgroundTasks = None,
) -> dict[str, Any]:
    """
    \u540c\u6b65\u5386\u53f2\u6570\u636e\u5230\u6570\u636e\u5e93

    \u53ef\u4ee5\u5728\u540e\u53f0\u8fd0\u884c
    """
    from app.services.data_etl import data_etl_service

    if len(symbols) > 10:
        # \u5927\u6279\u91cf\u540c\u6b65\u5728\u540e\u53f0\u8fd0\u884c
        background_tasks.add_task(
            data_etl_service.sync_historical_data,
            symbols, frequency, start_date, end_date, source
        )
        return {
            "status": "started",
            "message": f"\u540e\u53f0\u540c\u6b65\u5df2\u542f\u52a8\uff0c\u5171 {len(symbols)} \u53ea\u80a1\u7968",
        }

    # \u5c0f\u6279\u91cf\u76f4\u63a5\u540c\u6b65
    result = await data_etl_service.sync_historical_data(
        symbols, frequency, start_date, end_date, source
    )

    return result


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    symbols: list[str] | None = Query(None),
    frequency: DataFrequency = DataFrequency.DAY_1,
) -> SyncStatusResponse:
    """\u83b7\u53d6\u6570\u636e\u540c\u6b65\u72b6\u6001"""
    from app.services.data_etl import data_etl_service

    statuses = await data_etl_service.get_sync_status(symbols, frequency)

    return SyncStatusResponse(
        symbols=statuses,
        total_symbols=len(statuses),
        synced_count=sum(1 for s in statuses if s.status.value == "synced"),
        syncing_count=sum(1 for s in statuses if s.status.value == "syncing"),
        error_count=sum(1 for s in statuses if s.status.value == "error"),
    )


@router.post("/sync/fill-missing")
async def fill_missing_data(
    symbol: str,
    frequency: DataFrequency = DataFrequency.DAY_1,
    start_date: str = Query(...),
    end_date: str = Query(...),
) -> dict[str, Any]:
    """\u586b\u5145\u7f3a\u5931\u6570\u636e"""
    from app.services.data_etl import data_etl_service

    result = await data_etl_service.fill_missing_data(
        symbol, frequency, start_date, end_date
    )

    return result


# === \u65e5\u5185\u56e0\u5b50 ===

@router.get("/intraday-factors/definitions")
async def get_intraday_factor_definitions() -> list[dict[str, Any]]:
    """\u83b7\u53d6\u65e5\u5185\u56e0\u5b50\u5b9a\u4e49"""
    return [f.model_dump() for f in INTRADAY_FACTOR_DEFINITIONS]


@router.get("/intraday-factors/{symbol}", response_model=IntradayFactorSnapshot)
async def get_intraday_factors(
    symbol: str,
    timestamp: datetime | None = None,
) -> IntradayFactorSnapshot:
    """\u83b7\u53d6\u5355\u53ea\u80a1\u7968\u7684\u65e5\u5185\u56e0\u5b50"""
    from app.services.intraday_factor_engine import intraday_factor_engine

    snapshot = await intraday_factor_engine.calculate_factors(symbol, timestamp)

    return snapshot


@router.post("/intraday-factors/batch", response_model=IntradayFactorsResponse)
async def get_batch_intraday_factors(
    symbols: list[str],
    timestamp: datetime | None = None,
) -> IntradayFactorsResponse:
    """\u6279\u91cf\u83b7\u53d6\u65e5\u5185\u56e0\u5b50"""
    from app.services.intraday_factor_engine import intraday_factor_engine

    snapshots = await intraday_factor_engine.calculate_batch(symbols, timestamp)

    return IntradayFactorsResponse(
        snapshots=snapshots,
        timestamp=timestamp or datetime.now(),
        factors_calculated=[f.id.value for f in INTRADAY_FACTOR_DEFINITIONS],
    )


@router.get("/intraday-factors/latest")
async def get_latest_intraday_factors(
    symbols: list[str] = Query(...),
) -> dict[str, IntradayFactorSnapshot]:
    """\u83b7\u53d6\u6700\u65b0\u7684\u65e5\u5185\u56e0\u5b50"""
    from app.services.intraday_factor_engine import intraday_factor_engine

    return await intraday_factor_engine.get_latest_factors(symbols)


# === \u6570\u636e\u8d28\u91cf ===

@router.post("/quality/check")
async def check_data_quality(
    symbols: list[str],
    frequency: DataFrequency = DataFrequency.DAY_1,
    start_date: str = Query(...),
    end_date: str = Query(...),
) -> list[dict[str, Any]]:
    """\u68c0\u67e5\u6570\u636e\u8d28\u91cf"""
    from app.services.data_etl import data_etl_service

    issues = await data_etl_service.check_data_quality(
        symbols, frequency, start_date, end_date
    )

    return issues


@router.get("/quality/report")
async def get_quality_report(
    start_date: str = Query(...),
    end_date: str = Query(...),
) -> DataQualityReport:
    """\u83b7\u53d6\u6570\u636e\u8d28\u91cf\u62a5\u544a"""
    from sqlalchemy import select, func
    from app.core.database import get_async_session
    from app.models.market_data import DataQualityIssue

    async with get_async_session() as session:
        # \u7edf\u8ba1\u95ee\u9898
        query = select(DataQualityIssue).where(
            DataQualityIssue.issue_timestamp >= start_date,
            DataQualityIssue.issue_timestamp <= end_date,
        )
        result = await session.execute(query)
        issues = result.scalars().all()

        # \u6309\u7c7b\u578b\u7edf\u8ba1
        issues_by_type = {}
        issues_by_severity = {"low": 0, "medium": 0, "high": 0}

        for issue in issues:
            issues_by_type[issue.issue_type] = issues_by_type.get(issue.issue_type, 0) + 1
            issues_by_severity[issue.severity] = issues_by_severity.get(issue.severity, 0) + 1

        # \u8ba1\u7b97\u8bc4\u5206 (100 - \u95ee\u9898\u6570 * \u6743\u91cd)
        score = max(0, 100 - (
            issues_by_severity["low"] * 1 +
            issues_by_severity["medium"] * 5 +
            issues_by_severity["high"] * 10
        ))

        return DataQualityReport(
            report_date=datetime.now(),
            symbols_checked=len(set(i.symbol for i in issues)),
            bars_checked=0,  # \u9700\u8981\u989d\u5916\u67e5\u8be2
            issues_found=len(issues),
            issues_by_type=issues_by_type,
            issues_by_severity=issues_by_severity,
            overall_score=score,
            issues=[],  # \u7b80\u5316\uff0c\u4e0d\u8fd4\u56de\u5168\u90e8\u95ee\u9898
        )


@router.post("/quality/resolve/{issue_id}")
async def resolve_quality_issue(
    issue_id: str,
    resolution_notes: str | None = None,
) -> dict[str, str]:
    """\u6807\u8bb0\u6570\u636e\u8d28\u91cf\u95ee\u9898\u4e3a\u5df2\u89e3\u51b3"""
    from sqlalchemy import update
    from app.core.database import get_async_session
    from app.models.market_data import DataQualityIssue

    async with get_async_session() as session:
        stmt = update(DataQualityIssue).where(
            DataQualityIssue.id == issue_id
        ).values(
            resolved=True,
            resolved_at=datetime.now(),
            resolution_notes=resolution_notes,
        )
        await session.execute(stmt)
        await session.commit()

    return {"status": "resolved", "issue_id": issue_id}
