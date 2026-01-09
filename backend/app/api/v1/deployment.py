"""
策略部署 API

端点:
- POST   /deployments              创建部署
- GET    /deployments              获取部署列表
- GET    /deployments/{id}         获取部署详情
- PUT    /deployments/{id}         更新部署
- DELETE /deployments/{id}         删除部署
- POST   /deployments/{id}/start   启动
- POST   /deployments/{id}/pause   暂停
- POST   /deployments/{id}/stop    停止
- POST   /deployments/{id}/switch-env  切换环境
- GET    /deployments/{id}/param-limits  获取参数范围
"""

from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from app.schemas.deployment import (
    Deployment, DeploymentCreate, DeploymentUpdate,
    DeploymentListResponse, DeploymentStatus, DeploymentEnvironment,
    ParamLimits
)
from app.services.deployment_service import deployment_service

router = APIRouter(prefix="/deployments", tags=["策略部署"])


@router.post("", response_model=Deployment, summary="创建部署")
async def create_deployment(data: DeploymentCreate):
    """
    创建新的策略部署

    - **config.strategy_id**: 要部署的策略ID
    - **config.deployment_name**: 部署名称
    - **config.environment**: 环境 (paper/live)
    - **auto_start**: 是否自动启动
    """
    try:
        return await deployment_service.create_deployment(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=DeploymentListResponse, summary="获取部署列表")
async def list_deployments(
    strategy_id: Optional[str] = Query(None, description="策略ID筛选"),
    status: Optional[DeploymentStatus] = Query(None, description="状态筛选"),
    environment: Optional[DeploymentEnvironment] = Query(None, description="环境筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    获取部署列表

    支持按策略ID、状态、环境筛选
    """
    deployments = await deployment_service.list_deployments(
        strategy_id=strategy_id,
        status=status,
        environment=environment
    )
    # 分页
    paginated = deployments[skip:skip + limit]
    return DeploymentListResponse(total=len(deployments), items=paginated)


@router.get("/{deployment_id}", response_model=Deployment, summary="获取部署详情")
async def get_deployment(deployment_id: str):
    """获取部署详情"""
    try:
        return await deployment_service.get_deployment(deployment_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="部署不存在")


@router.put("/{deployment_id}", response_model=Deployment, summary="更新部署")
async def update_deployment(deployment_id: str, data: DeploymentUpdate):
    """
    更新部署配置

    只能在非运行状态下修改
    """
    try:
        return await deployment_service.update_deployment(deployment_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{deployment_id}", summary="删除部署")
async def delete_deployment(deployment_id: str):
    """
    删除部署

    只能删除非运行状态的部署
    """
    try:
        await deployment_service.delete_deployment(deployment_id)
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{deployment_id}/start", response_model=Deployment, summary="启动部署")
async def start_deployment(deployment_id: str):
    """
    启动部署

    会验证配置是否满足要求
    """
    try:
        return await deployment_service.start_deployment(deployment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{deployment_id}/pause", response_model=Deployment, summary="暂停部署")
async def pause_deployment(deployment_id: str):
    """
    暂停部署

    只能暂停运行中的部署
    """
    try:
        return await deployment_service.pause_deployment(deployment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{deployment_id}/stop", response_model=Deployment, summary="停止部署")
async def stop_deployment(deployment_id: str):
    """停止部署"""
    try:
        return await deployment_service.stop_deployment(deployment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{deployment_id}/switch-env", response_model=Deployment, summary="切换环境")
async def switch_environment(
    deployment_id: str,
    target_env: DeploymentEnvironment = Query(..., description="目标环境")
):
    """
    切换部署环境 (模拟盘 <-> 实盘)

    切换到实盘需要满足以下条件:
    - 模拟盘运行满30天
    - 胜率 > 40%
    """
    try:
        return await deployment_service.switch_environment(deployment_id, target_env)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{deployment_id}/param-limits",
    response_model=ParamLimits,
    summary="获取参数范围"
)
async def get_param_limits(deployment_id: str):
    """
    获取部署的参数范围限制

    参数范围从策略回测结果继承
    """
    try:
        deployment = await deployment_service.get_deployment(deployment_id)
        return await deployment_service.get_param_limits(deployment.strategy_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="部署不存在")


@router.get(
    "/strategy/{strategy_id}/param-limits",
    response_model=ParamLimits,
    summary="获取策略参数范围"
)
async def get_strategy_param_limits(strategy_id: str):
    """
    获取策略的参数范围限制

    用于部署前获取可调整的参数范围
    """
    return await deployment_service.get_param_limits(strategy_id)
