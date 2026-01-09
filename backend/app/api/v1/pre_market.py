"""
盘前扫描 API
PRD 4.18.0 盘前扫描器
"""
from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.pre_market import (
    CreateWatchlistRequest,
    IntradayWatchlist,
    PreMarketScanFilter,
    PreMarketScanResult,
)
from app.services.pre_market_service import get_pre_market_service

router = APIRouter(prefix="/intraday", tags=["日内交易"])

# 模拟用户信息
MOCK_USER_ID = "user_001"


@router.get(
    "/pre-market-scanner",
    response_model=PreMarketScanResult,
    summary="盘前扫描",
)
async def scan_pre_market(
    strategy_id: str = Query(..., description="策略ID"),
    min_gap: float = Query(0.02, description="最小Gap (默认2%)"),
    min_premarket_volume: float = Query(2.0, description="盘前成交量倍数"),
    min_volatility: float = Query(0.03, description="最小波动率"),
    min_liquidity: float = Query(5000000, description="最小流动性 ($)"),
    has_news: Optional[bool] = Query(None, description="是否有新闻"),
    is_earnings_day: Optional[bool] = Query(None, description="是否财报日"),
) -> PreMarketScanResult:
    """
    盘前扫描

    可用时间: 美东时间 4:00-9:30 AM
    刷新频率: 建议每5分钟刷新一次

    返回符合条件的股票列表，按评分排序
    """
    service = get_pre_market_service()

    filters = PreMarketScanFilter(
        min_gap=min_gap,
        min_premarket_volume=min_premarket_volume,
        min_volatility=min_volatility,
        min_liquidity=min_liquidity,
        has_news=has_news,
        is_earnings_day=is_earnings_day,
    )

    return await service.scan(strategy_id, filters)


@router.post(
    "/watchlist",
    response_model=IntradayWatchlist,
    summary="确认监控列表",
)
async def create_watchlist(
    request: CreateWatchlistRequest,
) -> IntradayWatchlist:
    """
    确认今日监控列表

    建议: 5-15只股票，不超过20只
    """
    service = get_pre_market_service()

    return await service.create_watchlist(
        user_id=MOCK_USER_ID,
        request=request,
    )


@router.get(
    "/watchlist",
    response_model=Optional[IntradayWatchlist],
    summary="获取今日监控列表",
)
async def get_today_watchlist(
    strategy_id: str = Query(..., description="策略ID"),
) -> Optional[IntradayWatchlist]:
    """获取今日监控列表"""
    service = get_pre_market_service()

    return await service.get_today_watchlist(
        user_id=MOCK_USER_ID,
        strategy_id=strategy_id,
    )


@router.get(
    "/watchlist/history",
    response_model=list[IntradayWatchlist],
    summary="获取监控列表历史",
)
async def get_watchlist_history(
    strategy_id: str = Query(..., description="策略ID"),
    limit: int = Query(10, ge=1, le=30, description="返回数量"),
) -> list[IntradayWatchlist]:
    """获取监控列表历史"""
    service = get_pre_market_service()

    return await service.get_watchlist_history(
        user_id=MOCK_USER_ID,
        strategy_id=strategy_id,
        limit=limit,
    )


@router.get(
    "/market-status",
    summary="获取市场状态",
)
async def get_market_status() -> dict:
    """
    获取当前市场状态

    返回盘前/盘中/盘后状态
    """
    from datetime import datetime

    now = datetime.now()
    hour = now.hour
    minute = now.minute

    # 简化的市场时间判断 (实际需要考虑时区和假日)
    if 4 <= hour < 9 or (hour == 9 and minute < 30):
        status = "pre_market"
        status_text = "盘前交易"
    elif (hour == 9 and minute >= 30) or (9 < hour < 16):
        status = "market_open"
        status_text = "盘中"
    elif 16 <= hour < 20:
        status = "after_hours"
        status_text = "盘后交易"
    else:
        status = "market_closed"
        status_text = "休市"

    return {
        "status": status,
        "status_text": status_text,
        "current_time": now.isoformat(),
        "next_open": "09:30 ET",
        "next_close": "16:00 ET",
    }
