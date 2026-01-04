"""
策略构建器 7步配置 API 端点
Phase 8: 策略构建增强

使用 PostgreSQL 数据库持久化存储
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.strategy_v2 import StrategyStatusEnum, StrategyV2
from app.schemas.strategy_v2 import (
    StrategyConfigV2,
    StrategyCreateRequest,
    StrategyListResponse,
    StrategyResponse,
    StrategyStatus,
    StrategyUpdateRequest,
)

router = APIRouter(prefix="/strategies/v2", tags=["Strategy V2 (7-Step)"])


def model_to_response(strategy: StrategyV2) -> StrategyResponse:
    """将数据库模型转换为响应模型"""
    # 构建配置对象
    config = StrategyConfigV2(
        universe=strategy.universe_config,
        alpha=strategy.alpha_config,
        signal=strategy.signal_config,
        risk=strategy.risk_config,
        portfolio=strategy.portfolio_config,
        execution=strategy.execution_config,
        monitor=strategy.monitor_config,
    )

    # 状态映射 (数据库枚举 -> API枚举)
    status_map = {
        StrategyStatusEnum.DRAFT: StrategyStatus.DRAFT,
        StrategyStatusEnum.BACKTEST: StrategyStatus.BACKTEST,
        StrategyStatusEnum.PAPER: StrategyStatus.PAPER,
        StrategyStatusEnum.LIVE: StrategyStatus.LIVE,
        StrategyStatusEnum.PAUSED: StrategyStatus.PAUSED,
        StrategyStatusEnum.ARCHIVED: StrategyStatus.ARCHIVED,
    }

    return StrategyResponse(
        id=strategy.id,
        name=strategy.name,
        description=strategy.description,
        status=status_map.get(strategy.status, StrategyStatus.DRAFT),
        created_at=strategy.created_at.isoformat() if strategy.created_at else "",
        updated_at=strategy.updated_at.isoformat() if strategy.updated_at else "",
        config=config,
    )


def api_status_to_db(status: StrategyStatus) -> StrategyStatusEnum:
    """API状态枚举转换为数据库枚举"""
    status_map = {
        StrategyStatus.DRAFT: StrategyStatusEnum.DRAFT,
        StrategyStatus.BACKTEST: StrategyStatusEnum.BACKTEST,
        StrategyStatus.PAPER: StrategyStatusEnum.PAPER,
        StrategyStatus.LIVE: StrategyStatusEnum.LIVE,
        StrategyStatus.PAUSED: StrategyStatusEnum.PAUSED,
        StrategyStatus.ARCHIVED: StrategyStatusEnum.ARCHIVED,
    }
    return status_map.get(status, StrategyStatusEnum.DRAFT)


@router.post("/", response_model=StrategyResponse, summary="创建策略")
async def create_strategy(
    request: StrategyCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的7步策略配置

    包含完整的策略定义：
    - 投资池配置
    - 因子层配置
    - 信号层配置 (新增)
    - 风险层配置 (新增)
    - 组合层配置
    - 执行层配置
    - 监控层配置
    """
    strategy_id = str(uuid4())
    config = request.config.model_dump()

    db_strategy = StrategyV2(
        id=strategy_id,
        name=request.name,
        description=request.description,
        status=StrategyStatusEnum.DRAFT,
        universe_config=config.get("universe", {}),
        alpha_config=config.get("alpha", {}),
        signal_config=config.get("signal", {}),
        risk_config=config.get("risk", {}),
        portfolio_config=config.get("portfolio", {}),
        execution_config=config.get("execution", {}),
        monitor_config=config.get("monitor", {}),
    )

    db.add(db_strategy)
    await db.commit()
    await db.refresh(db_strategy)

    return model_to_response(db_strategy)


@router.get("/", response_model=StrategyListResponse, summary="获取策略列表")
async def list_strategies(
    status: Optional[StrategyStatus] = Query(None, description="按状态筛选"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """获取策略列表，支持按状态筛选和分页"""
    # 构建查询
    query = select(StrategyV2).where(StrategyV2.is_deleted == False)

    # 按状态筛选
    if status:
        db_status = api_status_to_db(status)
        query = query.where(StrategyV2.status == db_status)

    # 按更新时间排序
    query = query.order_by(StrategyV2.updated_at.desc())

    # 获取总数
    count_query = select(StrategyV2).where(StrategyV2.is_deleted == False)
    if status:
        count_query = count_query.where(StrategyV2.status == api_status_to_db(status))
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    # 分页
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    strategies = result.scalars().all()

    return StrategyListResponse(
        total=total,
        strategies=[model_to_response(s) for s in strategies],
    )


@router.get("/{strategy_id}", response_model=StrategyResponse, summary="获取策略详情")
async def get_strategy(
    strategy_id: str,
    db: AsyncSession = Depends(get_db),
):
    """获取单个策略的详细配置"""
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return model_to_response(strategy)


@router.patch("/{strategy_id}", response_model=StrategyResponse, summary="更新策略")
async def update_strategy(
    strategy_id: str,
    request: StrategyUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    更新策略配置

    支持部分更新，只传入需要修改的字段
    """
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # 更新基本字段
    if request.name is not None:
        strategy.name = request.name
    if request.description is not None:
        strategy.description = request.description
    if request.status is not None:
        strategy.status = api_status_to_db(request.status)

    # 更新7步配置
    if request.universe is not None:
        strategy.universe_config = request.universe.model_dump()
    if request.alpha is not None:
        strategy.alpha_config = request.alpha.model_dump()
    if request.signal is not None:
        strategy.signal_config = request.signal.model_dump()
    if request.risk is not None:
        strategy.risk_config = request.risk.model_dump()
    if request.portfolio is not None:
        strategy.portfolio_config = request.portfolio.model_dump()
    if request.execution is not None:
        strategy.execution_config = request.execution.model_dump()
    if request.monitor is not None:
        strategy.monitor_config = request.monitor.model_dump()

    await db.commit()
    await db.refresh(strategy)

    return model_to_response(strategy)


@router.delete("/{strategy_id}", summary="删除策略")
async def delete_strategy(
    strategy_id: str,
    db: AsyncSession = Depends(get_db),
):
    """删除策略 (软删除)"""
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # 软删除
    strategy.is_deleted = True
    strategy.deleted_at = datetime.utcnow()

    await db.commit()

    return {"message": "Strategy deleted successfully"}


@router.post("/{strategy_id}/clone", response_model=StrategyResponse, summary="克隆策略")
async def clone_strategy(
    strategy_id: str,
    new_name: str = Query(..., description="新策略名称"),
    db: AsyncSession = Depends(get_db),
):
    """克隆现有策略"""
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    original = result.scalar_one_or_none()

    if not original:
        raise HTTPException(status_code=404, detail="Strategy not found")

    new_id = str(uuid4())

    cloned = StrategyV2(
        id=new_id,
        name=new_name,
        description=f"Cloned from: {original.name}",
        status=StrategyStatusEnum.DRAFT,
        universe_config=original.universe_config.copy() if original.universe_config else {},
        alpha_config=original.alpha_config.copy() if original.alpha_config else {},
        signal_config=original.signal_config.copy() if original.signal_config else {},
        risk_config=original.risk_config.copy() if original.risk_config else {},
        portfolio_config=original.portfolio_config.copy() if original.portfolio_config else {},
        execution_config=original.execution_config.copy() if original.execution_config else {},
        monitor_config=original.monitor_config.copy() if original.monitor_config else {},
        parent_id=strategy_id,
    )

    db.add(cloned)
    await db.commit()
    await db.refresh(cloned)

    return model_to_response(cloned)


@router.post("/{strategy_id}/validate", summary="验证策略配置")
async def validate_strategy(
    strategy_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    验证策略配置的完整性和合理性

    检查项:
    - 必填字段是否完整
    - 因子是否已选择
    - 止损是否设置
    - 风险参数是否合理
    """
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    errors = []
    warnings = []

    # 检查因子是否选择
    alpha_config = strategy.alpha_config or {}
    if not alpha_config.get("factors"):
        errors.append("未选择任何因子")

    # 检查止损
    signal_config = strategy.signal_config or {}
    if not signal_config.get("stop_loss"):
        errors.append("必须设置止损")
    elif signal_config.get("stop_loss", 0) > 30:
        warnings.append("止损阈值较高(>30%)，风险较大")

    # 检查风险配置
    risk_config = strategy.risk_config or {}
    if risk_config.get("max_single_position", 0) > 10:
        warnings.append("单股仓位限制较宽松(>10%)，建议收紧")

    # 检查组合配置
    portfolio_config = strategy.portfolio_config or {}
    if portfolio_config.get("min_holdings", 0) < 10:
        warnings.append("最小持仓数较少，分散化程度较低")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "can_backtest": len(errors) == 0,
        "can_go_live": len(errors) == 0 and len(warnings) == 0,
    }


@router.post("/{strategy_id}/run-backtest", summary="启动回测")
async def run_backtest(
    strategy_id: str,
    start_date: str = Query(..., description="回测开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="回测结束日期 YYYY-MM-DD"),
    initial_capital: float = Query(1000000, description="初始资金"),
    db: AsyncSession = Depends(get_db),
):
    """
    启动策略回测任务

    使用7步配置中的所有参数运行回测
    """
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # 更新状态为回测中
    strategy.status = StrategyStatusEnum.BACKTEST
    await db.commit()

    # 这里应该启动异步回测任务
    # 实际实现会调用回测引擎

    return {
        "task_id": str(uuid4()),
        "strategy_id": strategy_id,
        "status": "queued",
        "start_date": start_date,
        "end_date": end_date,
        "initial_capital": initial_capital,
        "message": "Backtest task queued successfully",
    }
