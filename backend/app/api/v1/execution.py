"""
执行系统 API 端点

提供:
- 订单管理
- 执行算法 (TWAP, VWAP, POV)
- TCA 分析
- 持仓管理
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/execution", tags=["执行系统"])


# === Pydantic 模型 ===

class OrderRequest(BaseModel):
    """订单请求"""
    symbol: str = Field(..., description="股票代码")
    side: str = Field(..., description="方向: buy, sell")
    quantity: float = Field(..., gt=0)
    order_type: str = Field("market", description="订单类型: market, limit, stop, stop_limit")
    limit_price: float | None = Field(None, gt=0)
    stop_price: float | None = Field(None, gt=0)
    time_in_force: str = Field("day", description="有效期: day, gtc, ioc, fok")


class OrderResponse(BaseModel):
    """订单响应"""
    order_id: str
    symbol: str
    side: str
    quantity: float
    order_type: str
    status: str
    filled_quantity: float
    filled_avg_price: float | None
    created_at: str


class TWAPRequest(BaseModel):
    """TWAP 执行请求"""
    symbol: str
    side: str
    total_quantity: float = Field(..., gt=0)
    duration_minutes: int = Field(60, ge=5, le=480)
    n_slices: int = Field(10, ge=2, le=100)
    use_limit_orders: bool = Field(False)
    limit_offset_bps: float = Field(5.0, ge=0, le=50)


class VWAPRequest(BaseModel):
    """VWAP 执行请求"""
    symbol: str
    side: str
    total_quantity: float = Field(..., gt=0)
    duration_minutes: int = Field(120, ge=30, le=480)
    max_participation_rate: float = Field(0.10, ge=0.01, le=0.30)
    use_limit_orders: bool = Field(True)


class POVRequest(BaseModel):
    """POV 执行请求"""
    symbol: str
    side: str
    total_quantity: float = Field(..., gt=0)
    target_rate: float = Field(0.05, ge=0.01, le=0.20)
    max_duration_minutes: int = Field(240, ge=30, le=480)


class ExecutionProgressResponse(BaseModel):
    """执行进度响应"""
    total_quantity: float
    filled_quantity: float
    remaining_quantity: float
    fill_rate: float
    avg_fill_price: float
    is_complete: bool
    elapsed_seconds: float


class PositionResponse(BaseModel):
    """持仓响应"""
    symbol: str
    quantity: float
    avg_entry_price: float
    market_value: float
    unrealized_pl: float
    unrealized_plpc: float
    side: str


class TCARequest(BaseModel):
    """TCA 分析请求"""
    order_id: str
    arrival_price: float | None = None
    vwap: float | None = None
    twap: float | None = None


class TCAResponse(BaseModel):
    """TCA 响应"""
    order_id: str
    symbol: str
    side: str
    slippage_vs_arrival: float
    slippage_vs_vwap: float
    market_impact: float
    execution_quality: str
    recommendations: list[str]


# === 全局状态 ===

_order_manager = None
_execution_tasks: dict[str, Any] = {}


def _get_order_manager():
    """获取订单管理器"""
    global _order_manager
    if _order_manager is None:
        from app.execution.order_manager import OrderManager
        _order_manager = OrderManager()
    return _order_manager


# === 订单管理 API ===

@router.post("/orders", response_model=OrderResponse)
async def create_order(request: OrderRequest) -> OrderResponse:
    """创建订单"""
    from app.execution.order_manager import OrderSide, OrderType, TimeInForce

    try:
        side_map = {"buy": OrderSide.BUY, "sell": OrderSide.SELL}
        type_map = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "stop": OrderType.STOP,
            "stop_limit": OrderType.STOP_LIMIT,
        }
        tif_map = {
            "day": TimeInForce.DAY,
            "gtc": TimeInForce.GTC,
            "ioc": TimeInForce.IOC,
            "fok": TimeInForce.FOK,
        }

        manager = _get_order_manager()

        order = manager.create_order(
            symbol=request.symbol,
            side=side_map[request.side],
            quantity=request.quantity,
            order_type=type_map.get(request.order_type, OrderType.MARKET),
            limit_price=request.limit_price,
            stop_price=request.stop_price,
            time_in_force=tif_map.get(request.time_in_force, TimeInForce.DAY),
        )

        return OrderResponse(
            order_id=str(order.order_id),
            symbol=order.symbol,
            side=order.side.value,
            quantity=order.quantity,
            order_type=order.order_type.value,
            status=order.status.value,
            filled_quantity=order.filled_quantity,
            filled_avg_price=order.filled_avg_price if order.filled_avg_price else None,
            created_at=order.created_at.isoformat(),
        )

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"无效参数: {e}")
    except Exception as e:
        logger.error("创建订单失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str) -> OrderResponse:
    """获取订单"""
    manager = _get_order_manager()

    try:
        order = manager.get_order(UUID(order_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的订单ID格式")

    if order is None:
        raise HTTPException(status_code=404, detail="订单不存在")

    return OrderResponse(
        order_id=str(order.order_id),
        symbol=order.symbol,
        side=order.side.value,
        quantity=order.quantity,
        order_type=order.order_type.value,
        status=order.status.value,
        filled_quantity=order.filled_quantity,
        filled_avg_price=order.filled_avg_price if order.filled_avg_price else None,
        created_at=order.created_at.isoformat(),
    )


@router.get("/orders", response_model=list[OrderResponse])
async def list_orders(
    symbol: str | None = Query(None),
    active_only: bool = Query(True),
) -> list[OrderResponse]:
    """列出订单"""
    manager = _get_order_manager()

    if active_only:
        orders = manager.get_active_orders(symbol=symbol)
    else:
        orders = manager.get_orders_by_symbol(symbol) if symbol else list(manager._orders.values())

    return [
        OrderResponse(
            order_id=str(o.order_id),
            symbol=o.symbol,
            side=o.side.value,
            quantity=o.quantity,
            order_type=o.order_type.value,
            status=o.status.value,
            filled_quantity=o.filled_quantity,
            filled_avg_price=o.filled_avg_price if o.filled_avg_price else None,
            created_at=o.created_at.isoformat(),
        )
        for o in orders
    ]


@router.post("/orders/{order_id}/submit")
async def submit_order(order_id: str) -> dict[str, Any]:
    """提交订单"""
    manager = _get_order_manager()

    try:
        success = await manager.submit_order(UUID(order_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的订单ID格式")

    if not success:
        raise HTTPException(status_code=400, detail="订单提交失败")

    return {"status": "submitted", "order_id": order_id}


@router.delete("/orders/{order_id}")
async def cancel_order(order_id: str) -> dict[str, Any]:
    """取消订单"""
    manager = _get_order_manager()

    try:
        success = await manager.cancel_order(UUID(order_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的订单ID格式")

    if not success:
        raise HTTPException(status_code=400, detail="订单取消失败")

    return {"status": "cancelled", "order_id": order_id}


# === 执行算法 API ===

@router.post("/algorithms/twap")
async def start_twap(
    request: TWAPRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """启动 TWAP 执行"""
    from app.execution.order_manager import OrderSide
    from app.execution.twap import TWAPExecutor, TWAPConfig

    task_id = f"twap_{request.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    config = TWAPConfig(
        duration_minutes=request.duration_minutes,
        n_slices=request.n_slices,
        use_limit_orders=request.use_limit_orders,
        limit_offset_bps=request.limit_offset_bps,
    )

    manager = _get_order_manager()
    executor = TWAPExecutor(order_manager=manager)

    side = OrderSide.BUY if request.side == "buy" else OrderSide.SELL

    async def run_twap():
        result = await executor.execute(
            symbol=request.symbol,
            side=side,
            total_quantity=request.total_quantity,
            config=config,
        )
        _execution_tasks[task_id]["result"] = result
        _execution_tasks[task_id]["status"] = "completed"

    _execution_tasks[task_id] = {
        "type": "twap",
        "symbol": request.symbol,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "executor": executor,
    }

    background_tasks.add_task(run_twap)

    return {
        "task_id": task_id,
        "status": "started",
        "algorithm": "twap",
        "symbol": request.symbol,
        "total_quantity": request.total_quantity,
    }


@router.post("/algorithms/vwap")
async def start_vwap(
    request: VWAPRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """启动 VWAP 执行"""
    from app.execution.order_manager import OrderSide
    from app.execution.vwap import VWAPExecutor, VWAPConfig

    task_id = f"vwap_{request.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    config = VWAPConfig(
        duration_minutes=request.duration_minutes,
        max_participation_rate=request.max_participation_rate,
        use_limit_orders=request.use_limit_orders,
    )

    manager = _get_order_manager()
    executor = VWAPExecutor(order_manager=manager)

    side = OrderSide.BUY if request.side == "buy" else OrderSide.SELL

    async def run_vwap():
        result = await executor.execute(
            symbol=request.symbol,
            side=side,
            total_quantity=request.total_quantity,
            config=config,
        )
        _execution_tasks[task_id]["result"] = result
        _execution_tasks[task_id]["status"] = "completed"

    _execution_tasks[task_id] = {
        "type": "vwap",
        "symbol": request.symbol,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "executor": executor,
    }

    background_tasks.add_task(run_vwap)

    return {
        "task_id": task_id,
        "status": "started",
        "algorithm": "vwap",
        "symbol": request.symbol,
    }


@router.post("/algorithms/pov")
async def start_pov(
    request: POVRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """启动 POV 执行"""
    from app.execution.order_manager import OrderSide
    from app.execution.pov import POVExecutor, POVConfig

    task_id = f"pov_{request.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    config = POVConfig(
        target_rate=request.target_rate,
        max_duration_minutes=request.max_duration_minutes,
    )

    manager = _get_order_manager()
    executor = POVExecutor(order_manager=manager)

    side = OrderSide.BUY if request.side == "buy" else OrderSide.SELL

    async def run_pov():
        result = await executor.execute(
            symbol=request.symbol,
            side=side,
            total_quantity=request.total_quantity,
            config=config,
        )
        _execution_tasks[task_id]["result"] = result
        _execution_tasks[task_id]["status"] = "completed"

    _execution_tasks[task_id] = {
        "type": "pov",
        "symbol": request.symbol,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "executor": executor,
    }

    background_tasks.add_task(run_pov)

    return {
        "task_id": task_id,
        "status": "started",
        "algorithm": "pov",
        "symbol": request.symbol,
    }


@router.get("/algorithms/{task_id}")
async def get_execution_status(task_id: str) -> dict[str, Any]:
    """获取执行任务状态"""
    if task_id not in _execution_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = _execution_tasks[task_id]

    response = {
        "task_id": task_id,
        "type": task["type"],
        "symbol": task["symbol"],
        "status": task["status"],
        "started_at": task["started_at"],
    }

    if "result" in task:
        result = task["result"]
        response["result"] = {
            "total_quantity": result.total_quantity,
            "filled_quantity": result.filled_quantity,
            "avg_fill_price": result.avg_fill_price,
            "is_complete": result.is_complete,
        }

    return response


@router.post("/algorithms/{task_id}/cancel")
async def cancel_execution(task_id: str) -> dict[str, Any]:
    """取消执行任务"""
    if task_id not in _execution_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = _execution_tasks[task_id]

    if "executor" in task:
        task["executor"].cancel()

    task["status"] = "cancelled"

    return {"task_id": task_id, "status": "cancelled"}


# === 持仓管理 API ===

@router.get("/positions", response_model=list[PositionResponse])
async def list_positions() -> list[PositionResponse]:
    """获取所有持仓"""
    from app.services.alpaca_client import get_alpaca_client

    try:
        client = get_alpaca_client()
        positions = await client.get_positions()

        return [
            PositionResponse(
                symbol=p.symbol,
                quantity=float(p.quantity),
                avg_entry_price=float(p.avg_entry_price),
                market_value=float(p.market_value),
                unrealized_pl=float(p.unrealized_pl),
                unrealized_plpc=float(p.unrealized_plpc),
                side=p.side,
            )
            for p in positions
        ]

    except Exception as e:
        logger.error("获取持仓失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/{symbol}", response_model=PositionResponse)
async def get_position(symbol: str) -> PositionResponse:
    """获取单个持仓"""
    from app.services.alpaca_client import get_alpaca_client

    try:
        client = get_alpaca_client()
        position = await client.get_position(symbol)

        if position is None:
            raise HTTPException(status_code=404, detail="无持仓")

        return PositionResponse(
            symbol=position.symbol,
            quantity=float(position.quantity),
            avg_entry_price=float(position.avg_entry_price),
            market_value=float(position.market_value),
            unrealized_pl=float(position.unrealized_pl),
            unrealized_plpc=float(position.unrealized_plpc),
            side=position.side,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取持仓失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/sync/status")
async def get_sync_status() -> dict[str, Any]:
    """获取持仓同步状态"""
    from app.services.position_sync import get_position_sync_service

    service = get_position_sync_service()
    return service.get_status()


@router.post("/positions/sync")
async def sync_positions() -> dict[str, Any]:
    """同步持仓"""
    from app.services.position_sync import get_position_sync_service

    try:
        service = get_position_sync_service()
        result = await service.sync_to_local()

        return {
            "is_synced": result.is_synced,
            "total_positions": result.total_positions,
            "synced_count": result.synced_count,
            "drifted_count": result.drifted_count,
        }

    except Exception as e:
        logger.error("持仓同步失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
