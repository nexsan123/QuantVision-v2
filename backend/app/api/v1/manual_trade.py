"""
手动交易 API
PRD 4.16 实时交易监控界面
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.manual_trade import (
    CancelOrderResponse,
    ManualTradeOrder,
    OrderListResponse,
    PlaceOrderRequest,
    PlaceOrderResponse,
    QuoteData,
)
from app.services.manual_trade_service import get_manual_trade_service

router = APIRouter(prefix="/manual-trade", tags=["手动交易"])

# 模拟用户信息
MOCK_USER_ID = "user_001"
MOCK_ACCOUNT_ID = "account_001"


@router.post("/order", response_model=PlaceOrderResponse, summary="下单")
async def place_order(request: PlaceOrderRequest) -> PlaceOrderResponse:
    """
    创建手动交易订单

    - 支持市价单、限价单、止损单
    - 可设置止盈止损价位
    - 可关联到特定策略
    - 自动检查 PDT 规则
    """
    service = get_manual_trade_service()

    result = await service.place_order(
        user_id=MOCK_USER_ID,
        account_id=MOCK_ACCOUNT_ID,
        request=request,
    )

    return result


@router.delete(
    "/order/{order_id}",
    response_model=CancelOrderResponse,
    summary="取消订单",
)
async def cancel_order(order_id: str) -> CancelOrderResponse:
    """
    取消未成交的订单

    只有 pending 状态的订单可以取消
    """
    service = get_manual_trade_service()

    result = await service.cancel_order(
        order_id=order_id,
        user_id=MOCK_USER_ID,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)

    return result


@router.get("/orders", response_model=OrderListResponse, summary="获取订单列表")
async def get_orders(
    status: Optional[str] = Query(None, description="订单状态过滤"),
    symbol: Optional[str] = Query(None, description="股票代码过滤"),
    strategy_id: Optional[str] = Query(None, description="策略ID过滤"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> OrderListResponse:
    """
    获取订单列表

    支持按状态、股票代码、策略ID过滤
    """
    service = get_manual_trade_service()

    orders, total = await service.get_orders(
        user_id=MOCK_USER_ID,
        status=status,
        symbol=symbol,
        strategy_id=strategy_id,
        limit=limit,
        offset=offset,
    )

    return OrderListResponse(
        orders=orders,
        total=total,
        has_more=offset + len(orders) < total,
    )


@router.get(
    "/order/{order_id}",
    response_model=ManualTradeOrder,
    summary="获取订单详情",
)
async def get_order(order_id: str) -> ManualTradeOrder:
    """获取单个订单详情"""
    service = get_manual_trade_service()

    order = await service.get_order(order_id)

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.user_id != MOCK_USER_ID:
        raise HTTPException(status_code=403, detail="无权访问此订单")

    return order


@router.get("/quote/{symbol}", response_model=QuoteData, summary="获取实时报价")
async def get_quote(symbol: str) -> QuoteData:
    """
    获取股票实时报价

    返回买卖价、最新价、成交量等信息
    """
    service = get_manual_trade_service()

    quote = await service.get_quote(symbol)

    return quote


@router.get("/quotes", response_model=list[QuoteData], summary="批量获取报价")
async def get_quotes(
    symbols: str = Query(..., description="股票代码，逗号分隔"),
) -> list[QuoteData]:
    """
    批量获取多个股票的实时报价
    """
    service = get_manual_trade_service()

    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    quotes = []

    for symbol in symbol_list[:20]:  # 限制最多20个
        quote = await service.get_quote(symbol)
        quotes.append(quote)

    return quotes
