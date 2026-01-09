"""
信号雷达 API

PRD 4.16.2: 信号雷达功能
端点:
- GET /signal-radar/{strategy_id} - 获取策略信号
- GET /signal-radar/stocks/search - 搜索股票
- GET /signal-radar/{strategy_id}/history - 历史信号
- GET /signal-radar/{strategy_id}/status-summary - 状态分布统计
- POST /signal-radar/{strategy_id}/refresh - 刷新信号
"""

from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.schemas.signal_radar import (
    SignalType,
    SignalStrength,
    SignalStatus,
    SignalListResponse,
    SignalHistoryResponse,
    StockSearchResponse,
    StatusSummaryResponse,
)
from app.services.signal_service import signal_service

router = APIRouter(prefix="/signal-radar", tags=["信号雷达"])


@router.get("/{strategy_id}", response_model=SignalListResponse, summary="获取策略信号")
async def get_signals(
    strategy_id: str,
    signal_type: Optional[SignalType] = Query(None, description="信号类型筛选"),
    signal_strength: Optional[SignalStrength] = Query(None, description="信号强度筛选"),
    status: Optional[SignalStatus] = Query(None, description="状态筛选"),
    search: Optional[str] = Query(None, description="股票搜索"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    获取策略的实时信号列表

    - 支持按信号类型筛选 (买入/卖出/持有)
    - 支持按信号强度筛选 (强/中/弱)
    - 支持按状态筛选
    - 支持股票代码/名称搜索
    """
    try:
        return await signal_service.get_signals(
            strategy_id=strategy_id,
            signal_type=signal_type,
            signal_strength=signal_strength,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocks/search", response_model=StockSearchResponse, summary="搜索股票")
async def search_stocks(
    query: str = Query(..., min_length=1, max_length=20, description="搜索关键词"),
    strategy_id: Optional[str] = Query(None, description="策略ID (可选)"),
    limit: int = Query(20, ge=1, le=50),
):
    """
    搜索股票

    - 支持股票代码和公司名称搜索
    - 返回股票的当前信号状态
    """
    return await signal_service.search_stocks(
        query=query,
        strategy_id=strategy_id,
        limit=limit,
    )


@router.get(
    "/{strategy_id}/history",
    response_model=SignalHistoryResponse,
    summary="获取历史信号"
)
async def get_signal_history(
    strategy_id: str,
    symbol: Optional[str] = Query(None, description="股票代码筛选"),
    limit: int = Query(100, ge=1, le=500),
):
    """
    获取策略的历史信号

    - 支持按股票代码筛选
    - 按时间倒序返回
    """
    return await signal_service.get_signal_history(
        strategy_id=strategy_id,
        symbol=symbol,
        limit=limit,
    )


@router.get(
    "/{strategy_id}/status-summary",
    response_model=StatusSummaryResponse,
    summary="获取状态分布"
)
async def get_status_summary(strategy_id: str):
    """
    获取策略的信号状态分布统计

    返回各状态的股票数量:
    - holding: 已持仓
    - buy_signal: 买入信号
    - sell_signal: 卖出信号
    - near_trigger: 接近触发
    - monitoring: 监控中
    - excluded: 不符合条件
    """
    return await signal_service.get_status_summary(strategy_id)


@router.post("/{strategy_id}/refresh", summary="刷新信号")
async def refresh_signals(strategy_id: str):
    """
    刷新策略信号

    强制重新计算所有信号状态
    """
    success = await signal_service.refresh_signals(strategy_id)
    return {"success": success, "message": "信号已刷新"}
