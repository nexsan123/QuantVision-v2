"""
实时监控 API
Sprint 10: 实时数据集成

端点:
- GET /realtime/status - 获取实时状态
- GET /realtime/positions - 获取持仓详情
- POST /realtime/monitor/start - 启动监控
- POST /realtime/monitor/stop - 停止监控
- GET /realtime/account - 获取账户信息
- GET /realtime/orders - 获取订单列表
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.services.realtime_monitor import realtime_monitor
from app.services.alpaca_client import get_alpaca_client, AlpacaOrderSide, AlpacaOrderType

router = APIRouter(prefix="/realtime", tags=["实时监控"])


@router.get("/status", summary="获取实时状态")
async def get_realtime_status():
    """
    获取实时监控状态

    返回:
    - 市场状态
    - 账户信息
    - 收益情况
    - 持仓统计
    """
    return await realtime_monitor.get_current_status()


@router.get("/positions", summary="获取持仓详情")
async def get_positions():
    """
    获取当前持仓详情

    返回每个持仓的:
    - 股票代码
    - 持仓方向
    - 数量和成本
    - 当前价格和市值
    - 未实现盈亏
    - 持仓权重
    """
    return await realtime_monitor.get_positions_detail()


@router.post("/monitor/start", summary="启动实时监控")
async def start_monitor():
    """启动实时风险监控"""
    await realtime_monitor.start()
    return {"success": True, "message": "监控已启动"}


@router.post("/monitor/stop", summary="停止实时监控")
async def stop_monitor():
    """停止实时风险监控"""
    await realtime_monitor.stop()
    return {"success": True, "message": "监控已停止"}


@router.get("/account", summary="获取账户信息")
async def get_account():
    """获取 Alpaca 账户信息"""
    try:
        alpaca = get_alpaca_client()
        account = await alpaca.get_account()
        return account
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", summary="获取订单列表")
async def get_orders(
    status: str = Query("all", description="状态过滤: open, closed, all"),
    limit: int = Query(50, ge=1, le=500),
):
    """获取订单列表"""
    try:
        alpaca = get_alpaca_client()
        orders = await alpaca.get_orders(status=status, limit=limit)

        return [
            {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "side": order.side.value,
                "type": order.order_type.value,
                "qty": float(order.qty),
                "filled_qty": float(order.filled_qty),
                "filled_avg_price": float(order.filled_avg_price) if order.filled_avg_price else None,
                "status": order.status.value,
                "time_in_force": order.time_in_force.value,
                "limit_price": float(order.limit_price) if order.limit_price else None,
                "stop_price": float(order.stop_price) if order.stop_price else None,
                "created_at": order.created_at.isoformat(),
                "filled_at": order.filled_at.isoformat() if order.filled_at else None,
            }
            for order in orders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clock", summary="获取市场时钟")
async def get_market_clock():
    """获取市场时钟状态"""
    try:
        alpaca = get_alpaca_client()
        return await alpaca.get_clock()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orders", summary="提交订单")
async def submit_order(
    symbol: str = Query(..., description="股票代码"),
    qty: float = Query(..., gt=0, description="数量"),
    side: str = Query(..., regex="^(buy|sell)$", description="方向: buy, sell"),
    order_type: str = Query("market", description="类型: market, limit, stop, stop_limit"),
    limit_price: Optional[float] = Query(None, description="限价"),
    stop_price: Optional[float] = Query(None, description="止损价"),
):
    """提交订单到 Alpaca"""
    try:
        alpaca = get_alpaca_client()

        alpaca_side = AlpacaOrderSide.BUY if side == "buy" else AlpacaOrderSide.SELL
        alpaca_type = AlpacaOrderType(order_type)

        order = await alpaca.submit_order(
            symbol=symbol,
            qty=qty,
            side=alpaca_side,
            order_type=alpaca_type,
            limit_price=limit_price,
            stop_price=stop_price,
        )

        return {
            "success": True,
            "order": {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side.value,
                "qty": float(order.qty),
                "status": order.status.value,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/orders/{order_id}", summary="取消订单")
async def cancel_order(order_id: str):
    """取消订单"""
    try:
        alpaca = get_alpaca_client()
        await alpaca.cancel_order(order_id)
        return {"success": True, "message": "订单已取消"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/positions/{symbol}", summary="平仓")
async def close_position(symbol: str):
    """平仓指定股票"""
    try:
        alpaca = get_alpaca_client()
        order = await alpaca.close_position(symbol)
        return {
            "success": True,
            "order": {
                "id": order.id,
                "symbol": order.symbol,
                "side": order.side.value,
                "qty": float(order.qty),
                "status": order.status.value,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/positions", summary="全部平仓")
async def close_all_positions():
    """平掉所有持仓"""
    try:
        alpaca = get_alpaca_client()
        orders = await alpaca.close_all_positions()
        return {
            "success": True,
            "orders_count": len(orders),
            "message": "已提交平仓订单",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
