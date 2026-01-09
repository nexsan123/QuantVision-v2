"""
交易成本配置 API
PRD 4.4 交易成本配置
"""

from fastapi import APIRouter, Query

from app.schemas.trading_cost import (
    TradingCostConfig,
    CostEstimateRequest,
    CostEstimateResult,
    CostConfigUpdate,
)
from app.services.cost_service import cost_service

router = APIRouter(prefix="/trading-cost", tags=["交易成本"])


@router.get("/config", response_model=TradingCostConfig)
async def get_cost_config(
    user_id: str = Query("default", description="用户ID"),
):
    """
    获取成本配置

    返回用户的交易成本配置，包括:
    - 成本模式 (简单/专业)
    - 佣金设置
    - 滑点配置
    - 市场冲击配置
    - 成本缓冲
    """
    return await cost_service.get_config(user_id)


@router.put("/config", response_model=TradingCostConfig)
async def update_cost_config(
    update: CostConfigUpdate,
    user_id: str = Query("default", description="用户ID"),
):
    """
    更新成本配置

    注意:
    - 佣金最低 $0.003/股
    - 滑点有最低限制 (大盘0.02%, 中盘0.05%, 小盘0.15%)
    - 超出限制的值会自动调整为最低值
    """
    return await cost_service.update_config(user_id, update)


@router.post("/config/reset", response_model=TradingCostConfig)
async def reset_cost_config(
    user_id: str = Query("default", description="用户ID"),
):
    """
    重置为默认配置

    将所有成本参数恢复为系统默认值
    """
    return await cost_service.reset_to_default(user_id)


@router.post("/estimate", response_model=CostEstimateResult)
async def estimate_trading_cost(
    request: CostEstimateRequest,
    user_id: str = Query("default", description="用户ID"),
):
    """
    估算交易成本

    根据用户配置估算单笔交易的成本，包括:
    - 佣金
    - SEC费用 (仅卖出)
    - TAF费用
    - 滑点成本
    - 市场冲击成本 (专业模式)

    返回总成本及各项明细
    """
    return await cost_service.estimate_cost(request, user_id)


@router.get("/defaults")
async def get_default_configs():
    """
    获取默认配置

    返回系统默认的成本配置和最低限制:
    - 简单模式默认值
    - 专业模式默认值
    - 各项最低限制
    """
    return cost_service.get_defaults()


@router.get("/estimate/quick")
async def quick_estimate(
    symbol: str = Query(..., description="股票代码"),
    quantity: int = Query(..., gt=0, description="交易数量"),
    price: float = Query(..., gt=0, description="交易价格"),
    side: str = Query("buy", description="交易方向 (buy/sell)"),
    user_id: str = Query("default", description="用户ID"),
):
    """
    快速估算交易成本

    简化的成本估算接口，适用于快速查询
    """
    request = CostEstimateRequest(
        symbol=symbol,
        quantity=quantity,
        price=price,
        side=side,
    )
    return await cost_service.estimate_cost(request, user_id)
