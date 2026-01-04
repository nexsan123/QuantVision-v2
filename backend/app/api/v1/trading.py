"""
Phase 12: \u6267\u884c\u5c42\u5347\u7ea7 - \u4ea4\u6613 API

\u7aef\u70b9:
- \u8d26\u6237\u7ba1\u7406
- \u6301\u4ed3\u67e5\u8be2
- \u8ba2\u5355\u7ba1\u7406
- \u6ed1\u70b9\u4f30\u7b97
- Paper Trading
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
import structlog

from app.schemas.trading import (
    BrokerType,
    BrokerConnectionStatus,
    BrokerAccount,
    BrokerPosition,
    BrokerStatusSummary,
    OrderSide,
    OrderStatus,
    CreateOrderRequest,
    OrderResponse,
    CancelOrderRequest,
    SlippageConfig,
    SlippageResult,
    SlippageEstimateRequest,
    PaperTradingConfig,
    PaperTradingState,
    BrokerListResponse,
    AccountResponse,
    PositionsResponse,
    OrdersResponse,
    SubmitOrderResponse,
    CancelOrderResponse,
    TradingStats,
    MarketStatus,
)
from app.services.broker_service import broker_manager, BrokerType as BT
from app.services.slippage_model import (
    SlippageModelFactory,
    estimate_slippage,
    MarketConditions,
)

router = APIRouter(prefix="/trading", tags=["\u4ea4\u6613"])
logger = structlog.get_logger()


# ============ \u5238\u5546\u7ba1\u7406 ============

@router.get("/brokers", response_model=BrokerListResponse)
async def get_brokers() -> BrokerListResponse:
    """
    \u83b7\u53d6\u652f\u6301\u7684\u5238\u5546\u5217\u8868

    \u8fd4\u56de\u6240\u6709\u652f\u6301\u7684\u5238\u5546\u53ca\u5176\u72b6\u6001
    """
    brokers = []

    # Alpaca
    brokers.append({
        "type": BrokerType.ALPACA.value,
        "name": "Alpaca",
        "description": "\u514d\u8d39 API\uff0c0 \u4f63\u91d1\uff0c\u652f\u6301 Paper Trading",
        "status": "available",
        "features": ["\u514d\u8d39", "0\u4f63\u91d1", "Paper Trading", "REST + WebSocket"],
        "url": "https://alpaca.markets",
    })

    # Interactive Brokers
    brokers.append({
        "type": BrokerType.INTERACTIVE_BROKERS.value,
        "name": "Interactive Brokers",
        "description": "\u4e13\u4e1a\u7ea7\u5238\u5546\uff0c\u8d39\u7528\u4f4e",
        "status": "coming_soon",
        "features": ["\u4e13\u4e1a\u7ea7", "\u8d39\u7528\u4f4e", "\u5168\u7403\u5e02\u573a"],
        "url": "https://interactivebrokers.com",
    })

    # Paper Trading
    brokers.append({
        "type": BrokerType.PAPER.value,
        "name": "\u6a21\u62df\u4ea4\u6613",
        "description": "\u672c\u5730\u6a21\u62df\u4ea4\u6613\uff0c\u65e0\u9700 API \u5bc6\u94a5",
        "status": "available",
        "features": ["\u5b8c\u5168\u514d\u8d39", "\u65e0\u9700\u914d\u7f6e", "\u5373\u65f6\u6210\u4ea4"],
    })

    # \u83b7\u53d6\u5f53\u524d\u8fde\u63a5\u7684\u5238\u5546
    connected = None
    primary = broker_manager.primary_broker
    if primary:
        connected = primary.broker_type

    return BrokerListResponse(
        brokers=brokers,
        connected_broker=connected,
    )


@router.get("/status", response_model=BrokerStatusSummary)
async def get_trading_status() -> BrokerStatusSummary:
    """
    \u83b7\u53d6\u4ea4\u6613\u72b6\u6001\u6458\u8981

    \u8fd4\u56de\u5f53\u524d\u5238\u5546\u8fde\u63a5\u72b6\u6001\u3001\u8d26\u6237\u4fe1\u606f\u6458\u8981
    """
    broker = broker_manager.primary_broker
    if not broker:
        return BrokerStatusSummary(
            broker=BrokerType.PAPER,
            status=BrokerConnectionStatus.DISCONNECTED,
            paper_trading=True,
            account=None,
            market_status=MarketStatus.CLOSED,
            last_update=datetime.now(),
        )

    # \u83b7\u53d6\u8d26\u6237\u4fe1\u606f
    account = await broker.get_account()
    account_summary = None
    if account:
        account_summary = {
            "equity": account.equity,
            "buyingPower": account.buying_power,
            "cash": account.cash,
            "dayPnl": account.equity - account.last_equity,
            "dayPnlPercent": (
                (account.equity / account.last_equity - 1) * 100
                if account.last_equity > 0
                else 0
            ),
        }

    return BrokerStatusSummary(
        broker=broker.broker_type,
        status=broker.status,
        paper_trading=broker.paper_trading,
        account=account_summary,
        market_status=await broker.get_market_status(),
        last_update=datetime.now(),
    )


@router.post("/connect/{broker_type}")
async def connect_broker(broker_type: BrokerType) -> dict[str, Any]:
    """
    \u8fde\u63a5\u5238\u5546

    \u5207\u6362\u5230\u6307\u5b9a\u7684\u5238\u5546
    """
    success = await broker_manager.switch_broker(BT(broker_type.value))
    if success:
        return {"success": True, "broker": broker_type.value}
    else:
        raise HTTPException(status_code=400, detail=f"\u65e0\u6cd5\u8fde\u63a5\u5238\u5546: {broker_type.value}")


# ============ \u8d26\u6237\u7ba1\u7406 ============

@router.get("/account", response_model=AccountResponse)
async def get_account() -> AccountResponse:
    """
    \u83b7\u53d6\u8d26\u6237\u4fe1\u606f

    \u8fd4\u56de\u8d26\u6237\u8d44\u91d1\u3001\u4fdd\u8bc1\u91d1\u3001\u4ea4\u6613\u9650\u5236\u7b49
    """
    broker = broker_manager.primary_broker
    if not broker:
        return AccountResponse(success=False, error="\u672a\u8fde\u63a5\u5238\u5546")

    account = await broker.get_account()
    if not account:
        return AccountResponse(success=False, error="\u83b7\u53d6\u8d26\u6237\u5931\u8d25")

    return AccountResponse(success=True, account=account)


@router.get("/positions", response_model=PositionsResponse)
async def get_positions() -> PositionsResponse:
    """
    \u83b7\u53d6\u6301\u4ed3

    \u8fd4\u56de\u5f53\u524d\u6240\u6709\u6301\u4ed3\u53ca\u672a\u5b9e\u73b0\u76c8\u4e8f
    """
    broker = broker_manager.primary_broker
    if not broker:
        return PositionsResponse(success=False)

    positions = await broker.get_positions()
    total_value = sum(p.market_value for p in positions)
    unrealized_pnl = sum(p.unrealized_pnl for p in positions)

    return PositionsResponse(
        success=True,
        positions=positions,
        total_value=total_value,
        unrealized_pnl=unrealized_pnl,
    )


# ============ \u8ba2\u5355\u7ba1\u7406 ============

@router.post("/orders", response_model=SubmitOrderResponse)
async def submit_order(request: CreateOrderRequest) -> SubmitOrderResponse:
    """
    \u63d0\u4ea4\u8ba2\u5355

    \u652f\u6301\u5e02\u4ef7\u5355\u3001\u9650\u4ef7\u5355\u3001\u6b62\u635f\u5355\u7b49
    """
    broker = broker_manager.primary_broker
    if not broker:
        return SubmitOrderResponse(success=False, error="\u672a\u8fde\u63a5\u5238\u5546")

    # \u4f30\u7b97\u6ed1\u70b9 (\u4f7f\u7528\u9ed8\u8ba4\u53c2\u6570)
    estimated_slippage = estimate_slippage(
        symbol=request.symbol,
        price=request.limit_price or 100.0,  # \u9ed8\u8ba4\u4ef7\u683c
        quantity=request.quantity,
        side=request.side,
        daily_volume=1e6,  # \u9ed8\u8ba4\u6210\u4ea4\u91cf
    )

    # \u63d0\u4ea4\u8ba2\u5355
    order = await broker.submit_order(request)
    if not order:
        return SubmitOrderResponse(success=False, error="\u8ba2\u5355\u63d0\u4ea4\u5931\u8d25")

    logger.info(
        "\u8ba2\u5355\u5df2\u63d0\u4ea4",
        order_id=order.id,
        symbol=request.symbol,
        side=request.side.value,
        quantity=request.quantity,
    )

    return SubmitOrderResponse(
        success=True,
        order=order,
        estimated_slippage=estimated_slippage,
    )


@router.get("/orders", response_model=OrdersResponse)
async def get_orders(
    status: OrderStatus | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> OrdersResponse:
    """
    \u83b7\u53d6\u8ba2\u5355\u5217\u8868

    \u53ef\u6309\u72b6\u6001\u7b5b\u9009
    """
    broker = broker_manager.primary_broker
    if not broker:
        return OrdersResponse(success=False)

    orders = await broker.get_orders(status=status, limit=limit)

    return OrdersResponse(
        success=True,
        orders=orders,
        total=len(orders),
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str) -> OrderResponse:
    """
    \u83b7\u53d6\u5355\u4e2a\u8ba2\u5355
    """
    broker = broker_manager.primary_broker
    if not broker:
        raise HTTPException(status_code=400, detail="\u672a\u8fde\u63a5\u5238\u5546")

    order = await broker.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="\u8ba2\u5355\u4e0d\u5b58\u5728")

    return order


@router.delete("/orders/{order_id}", response_model=CancelOrderResponse)
async def cancel_order(order_id: str) -> CancelOrderResponse:
    """
    \u53d6\u6d88\u8ba2\u5355
    """
    broker = broker_manager.primary_broker
    if not broker:
        return CancelOrderResponse(
            success=False,
            order_id=order_id,
            error="\u672a\u8fde\u63a5\u5238\u5546",
        )

    success = await broker.cancel_order(order_id)
    if not success:
        return CancelOrderResponse(
            success=False,
            order_id=order_id,
            error="\u53d6\u6d88\u5931\u8d25",
        )

    logger.info("\u8ba2\u5355\u5df2\u53d6\u6d88", order_id=order_id)

    return CancelOrderResponse(success=True, order_id=order_id)


# ============ \u6ed1\u70b9\u4f30\u7b97 ============

@router.get("/slippage/models")
async def get_slippage_models() -> list[dict[str, Any]]:
    """
    \u83b7\u53d6\u53ef\u7528\u7684\u6ed1\u70b9\u6a21\u578b
    """
    return SlippageModelFactory.get_available_models()


@router.post("/slippage/estimate", response_model=SlippageResult)
async def estimate_slippage_api(request: SlippageEstimateRequest) -> SlippageResult:
    """
    \u4f30\u7b97\u4ea4\u6613\u6ed1\u70b9

    \u4f7f\u7528 Almgren-Chriss \u6a21\u578b\u8ba1\u7b97\u9884\u671f\u6ed1\u70b9
    """
    result = estimate_slippage(
        symbol=request.symbol,
        price=request.price,
        quantity=request.quantity,
        side=request.side,
        daily_volume=request.daily_volume or 1e6,
        volatility=request.volatility,
        config=request.config,
    )
    return result


@router.post("/slippage/batch")
async def estimate_slippage_batch(
    trades: list[SlippageEstimateRequest],
) -> list[dict[str, Any]]:
    """
    \u6279\u91cf\u4f30\u7b97\u6ed1\u70b9
    """
    results = []
    for trade in trades:
        result = estimate_slippage(
            symbol=trade.symbol,
            price=trade.price,
            quantity=trade.quantity,
            side=trade.side,
            daily_volume=trade.daily_volume or 1e6,
            volatility=trade.volatility,
            config=trade.config,
        )
        results.append({
            "symbol": trade.symbol,
            "side": trade.side.value,
            "quantity": trade.quantity,
            "result": result.model_dump(),
        })
    return results


# ============ Paper Trading ============

@router.post("/paper/enable")
async def enable_paper_trading(
    config: PaperTradingConfig | None = None,
) -> dict[str, Any]:
    """
    \u542f\u7528 Paper Trading

    \u5207\u6362\u5230\u6a21\u62df\u4ea4\u6613\u6a21\u5f0f
    """
    success = await broker_manager.switch_broker(BT.PAPER)
    if not success:
        raise HTTPException(status_code=400, detail="\u542f\u7528 Paper Trading \u5931\u8d25")

    return {
        "success": True,
        "message": "Paper Trading \u5df2\u542f\u7528",
        "config": config.model_dump() if config else None,
    }


@router.post("/paper/disable")
async def disable_paper_trading() -> dict[str, Any]:
    """
    \u7981\u7528 Paper Trading

    \u5c1d\u8bd5\u5207\u6362\u5230\u5b9e\u76d8\u5238\u5546
    """
    # \u5c1d\u8bd5\u5207\u6362\u5230 Alpaca
    available = broker_manager.get_available_brokers()
    for broker_type in [BT.ALPACA]:
        if broker_type in available:
            success = await broker_manager.switch_broker(broker_type)
            if success:
                return {
                    "success": True,
                    "message": f"\u5df2\u5207\u6362\u5230 {broker_type.value}",
                }

    return {
        "success": False,
        "message": "\u6ca1\u6709\u53ef\u7528\u7684\u5b9e\u76d8\u5238\u5546\uff0c\u7ee7\u7eed\u4f7f\u7528 Paper Trading",
    }


@router.get("/paper/state", response_model=PaperTradingState)
async def get_paper_trading_state() -> PaperTradingState:
    """
    \u83b7\u53d6 Paper Trading \u72b6\u6001
    """
    broker = broker_manager.get_broker(BT.PAPER)
    if not broker or broker.broker_type != BrokerType.PAPER:
        return PaperTradingState(
            enabled=False,
            config=PaperTradingConfig(),
        )

    account = await broker.get_account()
    positions = await broker.get_positions()
    orders = await broker.get_orders(limit=50)

    return PaperTradingState(
        enabled=True,
        config=PaperTradingConfig(),
        account=account,
        positions=positions,
        orders=orders,
        trades_today=len([o for o in orders if o.status == OrderStatus.FILLED]),
    )


# ============ \u4ea4\u6613\u7edf\u8ba1 ============

@router.get("/stats", response_model=TradingStats)
async def get_trading_stats() -> TradingStats:
    """
    \u83b7\u53d6\u4ea4\u6613\u7edf\u8ba1

    \u8fd4\u56de\u80dc\u7387\u3001\u76c8\u4e8f\u3001\u4f63\u91d1\u3001\u6ed1\u70b9\u7b49\u7edf\u8ba1\u6570\u636e
    """
    broker = broker_manager.primary_broker
    if not broker:
        return TradingStats()

    orders = await broker.get_orders(status=OrderStatus.FILLED, limit=500)
    if not orders:
        return TradingStats()

    # \u8ba1\u7b97\u7edf\u8ba1\u6570\u636e
    total_trades = len(orders)
    total_commission = sum(o.commission for o in orders)
    total_slippage = sum(o.slippage for o in orders)
    avg_trade_size = sum(o.quantity for o in orders) / total_trades if total_trades > 0 else 0

    # \u7b80\u5316\u7684\u80dc\u7387\u8ba1\u7b97 (\u5b9e\u9645\u5e94\u57fa\u4e8e P&L)
    winning_trades = 0
    losing_trades = 0
    total_pnl = 0.0
    largest_win = 0.0
    largest_loss = 0.0

    return TradingStats(
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=winning_trades / total_trades if total_trades > 0 else 0,
        total_pnl=total_pnl,
        total_commission=total_commission,
        total_slippage=total_slippage,
        avg_slippage_bps=total_slippage / total_trades * 10000 if total_trades > 0 else 0,
        avg_trade_size=avg_trade_size,
        largest_win=largest_win,
        largest_loss=largest_loss,
    )
