"""
回测 API

提供:
- 回测创建
- 状态查询
- 结果获取
"""

from datetime import datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import DBSession, Pagination
from app.schemas.backtest import (
    BacktestCreateRequest,
    BacktestListResponse,
    BacktestMetrics,
    BacktestResponse,
    BacktestResultResponse,
    BacktestStatusRequest,
    BacktestStatusResponse,
)
from app.schemas.common import ResponseBase
from app.tasks.backtest_task import BacktestTaskManager

router = APIRouter(prefix="/backtests")
logger = structlog.get_logger()


@router.get("", response_model=BacktestListResponse)
async def list_backtests(
    db: DBSession,
    pagination: Pagination,
    status_filter: str | None = Query(None, alias="status", description="状态过滤"),
) -> BacktestListResponse:
    """
    获取回测列表

    支持状态过滤和分页
    """
    # TODO: 从数据库查询

    backtests = [
        BacktestResponse(
            id="bt_001",
            name="动量策略回测",
            status="completed",
            progress=100,
            created_at=datetime.now(),
            completed_at=datetime.now(),
        ),
        BacktestResponse(
            id="bt_002",
            name="价值策略回测",
            status="running",
            progress=45,
            created_at=datetime.now(),
        ),
    ]

    return BacktestListResponse(backtests=backtests, total=len(backtests))


@router.post("", response_model=ResponseBase[BacktestResponse])
async def create_backtest(
    db: DBSession,
    request: BacktestCreateRequest,
) -> ResponseBase[BacktestResponse]:
    """
    创建回测

    提交回测任务到 Celery 队列
    """
    # 验证参数
    if request.start_date > request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始日期不能大于结束日期",
        )

    if not request.universe and not request.universe_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须指定股票池",
        )

    # TODO: 获取价格和信号数据，提交到 Celery

    # 示例返回
    backtest = BacktestResponse(
        id="bt_new",
        name=request.name,
        status="pending",
        progress=0,
        created_at=datetime.now(),
    )

    logger.info(
        "创建回测",
        name=request.name,
        start=request.start_date,
        end=request.end_date,
    )

    return ResponseBase(data=backtest, message="回测任务已提交")


@router.get("/{backtest_id}", response_model=ResponseBase[BacktestResultResponse])
async def get_backtest(
    db: DBSession,
    backtest_id: str,
) -> ResponseBase[BacktestResultResponse]:
    """
    获取回测详情

    返回回测配置和结果
    """
    # TODO: 从数据库查询

    # 检查 Celery 任务状态
    task_status = BacktestTaskManager.get_status(backtest_id)

    if task_status["status"] == "pending":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={"status": "pending", "progress": 0},
        )

    if task_status["status"] == "running":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail={
                "status": "running",
                "progress": task_status.get("progress", 0),
            },
        )

    # 获取结果
    result = BacktestTaskManager.get_result(backtest_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="回测不存在",
        )

    # 示例返回
    backtest_result = BacktestResultResponse(
        id=backtest_id,
        name="示例回测",
        status="completed",
        config={
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 1000000,
        },
        metrics=BacktestMetrics(
            total_return=0.25,
            annual_return=0.25,
            volatility=0.15,
            max_drawdown=0.12,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            calmar_ratio=2.1,
            win_rate=0.55,
            profit_factor=1.8,
            beta=0.8,
            alpha=0.1,
        ),
        trades_count=150,
    )

    return ResponseBase(data=backtest_result)


@router.get("/{backtest_id}/status")
async def get_backtest_status(
    backtest_id: str,
) -> dict[str, Any]:
    """
    获取回测状态

    用于轮询任务进度
    """
    status_info = BacktestTaskManager.get_status(backtest_id)

    return {
        "id": backtest_id,
        **status_info,
    }


@router.post("/status", response_model=BacktestStatusResponse)
async def get_backtests_status(
    request: BacktestStatusRequest,
) -> BacktestStatusResponse:
    """
    批量获取回测状态

    一次查询多个回测的状态
    """
    statuses = {}
    for backtest_id in request.ids:
        statuses[backtest_id] = BacktestTaskManager.get_status(backtest_id)

    return BacktestStatusResponse(statuses=statuses)


@router.delete("/{backtest_id}", response_model=ResponseBase)
async def delete_backtest(
    db: DBSession,
    backtest_id: str,
) -> ResponseBase:
    """删除回测"""
    # 取消运行中的任务
    BacktestTaskManager.cancel(backtest_id)

    # TODO: 从数据库删除

    logger.info("删除回测", backtest_id=backtest_id)

    return ResponseBase(message="回测删除成功")


@router.post("/{backtest_id}/cancel", response_model=ResponseBase)
async def cancel_backtest(
    backtest_id: str,
) -> ResponseBase:
    """取消回测"""
    success = BacktestTaskManager.cancel(backtest_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="取消失败",
        )

    logger.info("取消回测", backtest_id=backtest_id)

    return ResponseBase(message="回测已取消")


@router.get("/{backtest_id}/trades")
async def get_backtest_trades(
    db: DBSession,
    backtest_id: str,
    pagination: Pagination,
) -> dict[str, Any]:
    """
    获取回测交易记录

    分页返回交易详情
    """
    # TODO: 从结果中提取交易记录

    return {
        "trades": [
            {
                "timestamp": "2023-06-15T09:30:00",
                "symbol": "AAPL",
                "side": "buy",
                "quantity": 100,
                "price": 185.50,
                "commission": 18.55,
            },
        ],
        "total": 150,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
    }


@router.get("/{backtest_id}/positions")
async def get_backtest_positions(
    db: DBSession,
    backtest_id: str,
    as_of: str | None = Query(None, description="截至日期"),
) -> dict[str, Any]:
    """
    获取回测持仓

    返回指定日期的持仓详情
    """
    # TODO: 从结果中提取持仓

    return {
        "as_of": as_of or "2023-12-31",
        "positions": [
            {
                "symbol": "AAPL",
                "quantity": 100,
                "market_value": 19250.00,
                "weight": 0.08,
                "pnl": 1250.00,
                "pnl_pct": 0.07,
            },
        ],
        "cash": 50000.00,
        "total_value": 1050000.00,
    }
