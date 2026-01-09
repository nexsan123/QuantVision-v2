"""
策略模板 API
PRD 4.13 策略模板库
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.schemas.strategy_template import (
    TemplateCategory,
    DifficultyLevel,
    StrategyTemplate,
    TemplateDeployRequest,
    TemplateDeployResult,
    TemplateListResponse,
)
from app.services.template_service import template_service

router = APIRouter(prefix="/templates", tags=["策略模板"])


@router.get("", response_model=TemplateListResponse)
async def get_templates(
    category: Optional[TemplateCategory] = Query(None, description="模板分类"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="难度等级"),
    search: Optional[str] = Query(None, description="搜索关键词"),
):
    """
    获取模板列表

    支持筛选:
    - 按分类: value/momentum/dividend/multi_factor/timing/intraday
    - 按难度: beginner/intermediate/advanced
    - 按关键词搜索名称/描述/标签
    """
    templates = await template_service.get_templates(
        category=category,
        difficulty=difficulty,
        search=search,
    )
    return TemplateListResponse(total=len(templates), templates=templates)


@router.get("/categories")
async def get_categories():
    """
    获取模板分类列表

    返回所有分类及其模板数量
    """
    return await template_service.get_categories()


@router.get("/{template_id}", response_model=StrategyTemplate)
async def get_template_detail(template_id: str):
    """
    获取模板详情

    包含完整的策略配置信息
    """
    template = await template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.post("/{template_id}/deploy", response_model=TemplateDeployResult)
async def deploy_template(
    template_id: str,
    request: TemplateDeployRequest,
):
    """
    从模板部署策略

    一键部署:
    1. 复制模板配置
    2. 创建新策略
    3. 返回策略ID
    """
    if request.template_id != template_id:
        request.template_id = template_id

    try:
        result = await template_service.deploy_template(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{template_id}/preview")
async def preview_template(template_id: str):
    """
    预览模板配置

    返回策略配置的详细信息，不创建策略
    """
    template = await template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return {
        "template_id": template.template_id,
        "name": template.name,
        "config": template.strategy_config,
        "factors": template.strategy_config.get("factors", []),
        "universe": template.strategy_config.get("universe"),
        "rebalance_frequency": template.strategy_config.get("rebalance_frequency"),
        "position_count": template.strategy_config.get("position_count"),
    }
