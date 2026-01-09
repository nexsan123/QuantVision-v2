"""
因子有效性验证 API
PRD 4.3 因子有效性验证
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import date

from app.services.factor_validation_service import factor_validation_service
from app.schemas.factor_validation import (
    FactorValidationResult,
    FactorValidationRequest,
    FactorCompareRequest,
    FactorCompareResult,
    FactorSuggestion,
    EFFECTIVENESS_LEVEL_CONFIG,
    FACTOR_CATEGORY_CONFIG,
)

router = APIRouter(prefix="/factors", tags=["因子验证"])


@router.get("/{factor_id}/validation", response_model=FactorValidationResult)
async def get_factor_validation(factor_id: str):
    """
    获取因子验证结果

    返回指定因子的有效性验证结果，包含IC统计、分组收益、使用建议等

    - **factor_id**: 因子ID (如 PE_TTM, ROE, MOMENTUM_3M)
    """
    result = await factor_validation_service.get_validation_result(factor_id)
    if not result:
        # 如果没有缓存，先执行验证
        result = await factor_validation_service.validate_factor(factor_id)
    return result


@router.post("/{factor_id}/validate", response_model=FactorValidationResult)
async def validate_factor(
    factor_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    universe: str = "全A",
):
    """
    触发因子验证

    重新计算因子的有效性指标

    - **factor_id**: 因子ID
    - **start_date**: 开始日期 (可选)
    - **end_date**: 结束日期 (可选)
    - **universe**: 股票池 (默认: 全A)
    """
    result = await factor_validation_service.validate_factor(
        factor_id=factor_id,
        start_date=start_date,
        end_date=end_date,
        universe=universe,
    )
    return result


@router.post("/compare", response_model=FactorCompareResult)
async def compare_factors(request: FactorCompareRequest):
    """
    因子对比分析

    对比多个因子的有效性，返回相关性矩阵和最佳组合建议

    - **factor_ids**: 因子ID列表 (2-5个)
    - **start_date**: 开始日期 (可选)
    - **end_date**: 结束日期 (可选)
    """
    result = await factor_validation_service.compare_factors(request.factor_ids)
    return result


@router.get("/{factor_id}/suggestions", response_model=list[FactorSuggestion])
async def get_factor_suggestions(factor_id: str):
    """
    获取因子组合建议

    返回与指定因子互补的因子建议

    - **factor_id**: 因子ID
    """
    suggestions = await factor_validation_service.get_suggestions(factor_id)
    return suggestions


@router.get("/categories")
async def get_factor_categories():
    """
    获取因子类别配置

    返回所有因子类别及其示例因子
    """
    return FACTOR_CATEGORY_CONFIG


@router.get("/effectiveness-levels")
async def get_effectiveness_levels():
    """
    获取有效性等级配置

    返回有效性等级定义及其说明
    """
    return {
        level.value: config
        for level, config in EFFECTIVENESS_LEVEL_CONFIG.items()
    }


@router.get("/available")
async def get_available_factors():
    """
    获取可用因子列表

    返回系统支持验证的因子列表
    """
    from app.services.factor_validation_service import FactorValidationService

    factors = []
    for factor_id, metadata in FactorValidationService.FACTOR_METADATA.items():
        factors.append({
            "factor_id": factor_id,
            "factor_name": metadata["name"],
            "category": metadata["category"],
            "description": metadata["plain_description"][:50] + "...",
        })
    return factors
