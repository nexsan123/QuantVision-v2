"""
策略冲突检测 API
PRD 4.6 策略冲突检测
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.schemas.conflict import (
    ConflictDetail,
    ConflictCheckRequest,
    ConflictCheckResult,
    ResolveConflictRequest,
    ConflictListResponse,
    ConflictStatus,
)
from app.services.conflict_service import conflict_service

router = APIRouter(prefix="/conflicts", tags=["策略冲突检测"])


@router.post("/check", response_model=ConflictCheckResult)
async def check_conflicts(request: ConflictCheckRequest):
    """
    检测策略冲突

    检测类型:
    - 逻辑冲突: 同一股票相反信号
    - 执行冲突: 资金/仓位限制
    - 超时冲突: 信号过期
    - 重复冲突: 重复买入信号
    """
    result = await conflict_service.check_conflicts(
        strategy_ids=request.strategy_ids,
        symbol=request.symbol,
        check_execution=request.check_execution,
        check_timeout=request.check_timeout,
    )
    return result


@router.get("/pending", response_model=ConflictListResponse)
async def get_pending_conflicts(
    strategy_id: Optional[str] = Query(None, description="策略ID"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    获取待处理冲突列表

    按严重程度排序:
    1. 严重 (必须处理)
    2. 警告 (建议处理)
    3. 提示 (仅供参考)
    """
    conflicts = await conflict_service.get_pending_conflicts(
        strategy_id=strategy_id,
        limit=limit,
    )
    pending_count = await conflict_service.get_conflict_count(
        strategy_id=strategy_id,
        status=ConflictStatus.PENDING,
    )
    return ConflictListResponse(
        total=len(conflicts),
        pending_count=pending_count,
        conflicts=conflicts,
    )


@router.get("/{conflict_id}", response_model=ConflictDetail)
async def get_conflict_detail(conflict_id: str):
    """
    获取冲突详情

    包含:
    - 冲突双方信号
    - 冲突原因和影响
    - 建议解决方案
    """
    conflict = await conflict_service.get_conflict_by_id(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="冲突不存在")
    return conflict


@router.post("/resolve", response_model=ConflictDetail)
async def resolve_conflict(request: ResolveConflictRequest):
    """
    解决冲突

    解决方案:
    - execute_strategy_a: 执行策略A
    - execute_strategy_b: 执行策略B
    - execute_both: 同时执行
    - cancel_both: 全部取消
    - reduce_position: 减仓执行
    - delay_execution: 延迟执行
    - ignore: 忽略冲突
    """
    conflict = await conflict_service.resolve_conflict(
        conflict_id=request.conflict_id,
        resolution=request.resolution,
        reason=request.reason,
    )
    if not conflict:
        raise HTTPException(status_code=404, detail="冲突不存在")
    return conflict


@router.post("/{conflict_id}/ignore", response_model=ConflictDetail)
async def ignore_conflict(conflict_id: str):
    """
    忽略冲突

    将冲突标记为已忽略状态
    """
    conflict = await conflict_service.ignore_conflict(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="冲突不存在")
    return conflict


@router.get("/count/pending")
async def get_pending_conflict_count(
    strategy_id: Optional[str] = Query(None, description="策略ID"),
):
    """
    获取待处理冲突数量

    用于显示通知角标
    """
    count = await conflict_service.get_conflict_count(
        strategy_id=strategy_id,
        status=ConflictStatus.PENDING,
    )
    critical_count = 0
    warning_count = 0

    conflicts = await conflict_service.get_pending_conflicts(strategy_id=strategy_id)
    from app.schemas.conflict import ConflictSeverity
    for c in conflicts:
        if c.severity == ConflictSeverity.CRITICAL:
            critical_count += 1
        elif c.severity == ConflictSeverity.WARNING:
            warning_count += 1

    return {
        "total": count,
        "critical": critical_count,
        "warning": warning_count,
    }


@router.get("/strategies/{strategy_id}/summary")
async def get_strategy_conflict_summary(strategy_id: str):
    """
    获取策略冲突摘要

    快速概览策略的冲突状态
    """
    pending = await conflict_service.get_pending_conflicts(strategy_id=strategy_id)
    total_count = await conflict_service.get_conflict_count(strategy_id=strategy_id)
    pending_count = await conflict_service.get_conflict_count(
        strategy_id=strategy_id,
        status=ConflictStatus.PENDING,
    )

    from app.schemas.conflict import ConflictSeverity, ConflictType
    critical_count = sum(1 for c in pending if c.severity == ConflictSeverity.CRITICAL)
    warning_count = sum(1 for c in pending if c.severity == ConflictSeverity.WARNING)

    type_counts = {}
    for c in pending:
        type_counts[c.conflict_type.value] = type_counts.get(c.conflict_type.value, 0) + 1

    return {
        "strategy_id": strategy_id,
        "total_conflicts": total_count,
        "pending_conflicts": pending_count,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "type_breakdown": type_counts,
        "needs_attention": critical_count > 0,
        "latest_conflicts": [
            {
                "conflict_id": c.conflict_id,
                "type": c.conflict_type.value,
                "severity": c.severity.value,
                "symbol": c.signal_a.symbol,
                "description": c.description,
            }
            for c in pending[:3]
        ],
    }
