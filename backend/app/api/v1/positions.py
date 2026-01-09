"""
持仓管理 API
PRD 4.18 分策略持仓管理
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.position import (
    AccountPositionSummary,
    ConsolidatedPosition,
    SellPositionRequest,
    SellPositionResponse,
    StrategyPosition,
    UpdateStopLossRequest,
)
from app.services.position_service import get_position_service

router = APIRouter(prefix="/positions", tags=["持仓管理"])

# 模拟用户信息
MOCK_USER_ID = "user_001"
MOCK_ACCOUNT_ID = "account_001"


@router.get(
    "/summary",
    response_model=AccountPositionSummary,
    summary="获取持仓汇总",
)
async def get_position_summary() -> AccountPositionSummary:
    """
    获取账户持仓汇总

    返回:
    - 按策略分组的持仓视图
    - 按股票汇总的持仓视图
    - 集中度风险警告
    - 组合 Beta 值
    """
    service = get_position_service()

    return await service.get_account_positions(
        user_id=MOCK_USER_ID,
        account_id=MOCK_ACCOUNT_ID,
    )


@router.get(
    "/strategy/{strategy_id}",
    response_model=list[StrategyPosition],
    summary="获取策略持仓",
)
async def get_strategy_positions(strategy_id: str) -> list[StrategyPosition]:
    """获取特定策略的持仓列表"""
    service = get_position_service()

    return await service.get_positions_by_strategy(
        user_id=MOCK_USER_ID,
        strategy_id=strategy_id,
    )


@router.get(
    "/manual",
    response_model=list[StrategyPosition],
    summary="获取手动交易持仓",
)
async def get_manual_positions() -> list[StrategyPosition]:
    """获取手动交易的持仓列表"""
    service = get_position_service()

    return await service.get_positions_by_strategy(
        user_id=MOCK_USER_ID,
        strategy_id=None,
    )


@router.get(
    "/symbol/{symbol}",
    response_model=Optional[ConsolidatedPosition],
    summary="获取股票持仓详情",
)
async def get_symbol_positions(symbol: str) -> Optional[ConsolidatedPosition]:
    """
    获取特定股票的持仓详情

    返回该股票在所有策略中的持仓汇总和来源分解
    """
    service = get_position_service()

    summary = await service.get_account_positions(
        user_id=MOCK_USER_ID,
        account_id=MOCK_ACCOUNT_ID,
    )

    for pos in summary.consolidated:
        if pos.symbol.upper() == symbol.upper():
            return pos

    return None


@router.get(
    "/{position_id}",
    response_model=StrategyPosition,
    summary="获取持仓详情",
)
async def get_position(position_id: str) -> StrategyPosition:
    """获取单个持仓详情"""
    service = get_position_service()

    position = await service.get_position(position_id)

    if not position:
        raise HTTPException(status_code=404, detail="持仓不存在")

    if position.user_id != MOCK_USER_ID:
        raise HTTPException(status_code=403, detail="无权访问此持仓")

    return position


@router.post(
    "/sell",
    response_model=SellPositionResponse,
    summary="卖出持仓",
)
async def sell_position(request: SellPositionRequest) -> SellPositionResponse:
    """
    卖出特定策略的持仓

    可以部分卖出或全部卖出
    """
    service = get_position_service()

    result = await service.sell_position(
        user_id=MOCK_USER_ID,
        request=request,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.put(
    "/{position_id}/stop-loss",
    summary="更新止盈止损",
)
async def update_stop_loss(
    position_id: str,
    request: UpdateStopLossRequest,
) -> dict:
    """更新持仓的止盈止损价位"""
    service = get_position_service()

    success = await service.update_stop_loss(
        user_id=MOCK_USER_ID,
        position_id=position_id,
        request=request,
    )

    if not success:
        raise HTTPException(status_code=400, detail="更新失败")

    return {"success": True, "message": "止盈止损已更新"}


@router.get(
    "/risk/concentration",
    summary="获取集中度风险",
)
async def get_concentration_risk() -> dict:
    """获取持仓集中度风险分析"""
    service = get_position_service()

    summary = await service.get_account_positions(
        user_id=MOCK_USER_ID,
        account_id=MOCK_ACCOUNT_ID,
    )

    return {
        "warnings": summary.concentration_warnings,
        "portfolio_beta": summary.portfolio_beta,
        "positions": [
            {
                "symbol": pos.symbol,
                "concentration_pct": pos.concentration_pct,
                "market_value": pos.total_market_value,
            }
            for pos in summary.consolidated
        ],
    }
