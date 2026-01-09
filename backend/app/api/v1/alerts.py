"""
风险预警 API

PRD 4.14: 风险预警通知
端点:
- GET /alerts - 获取预警列表
- GET /alerts/unread-count - 获取未读数量
- POST /alerts/{id}/read - 标记为已读
- POST /alerts/mark-all-read - 全部标记已读
- GET /alerts/config - 获取预警配置
- PUT /alerts/config - 更新预警配置
- POST /alerts/test-email - 发送测试邮件
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.alert import (
    RiskAlert,
    AlertConfig,
    AlertType,
    AlertListResponse,
    UpdateAlertConfigRequest,
)
from app.services.alert_service import alert_service

router = APIRouter(prefix="/alerts", tags=["风险预警"])

# 模拟当前用户ID
DEMO_USER_ID = "demo-user"


@router.get("/", response_model=AlertListResponse, summary="获取预警列表")
async def get_alerts(
    unread_only: bool = Query(False, description="只显示未读"),
    alert_type: Optional[AlertType] = Query(None, description="预警类型筛选"),
    limit: int = Query(50, le=100, description="返回数量限制"),
):
    """
    获取预警列表

    - 支持只显示未读
    - 支持按预警类型筛选
    - 按时间倒序返回
    """
    alerts = await alert_service.get_user_alerts(
        user_id=DEMO_USER_ID,
        unread_only=unread_only,
        alert_type=alert_type,
        limit=limit,
    )

    unread_count = await alert_service.get_unread_count(DEMO_USER_ID)

    return AlertListResponse(
        total=len(alerts),
        alerts=alerts,
        unread_count=unread_count,
    )


@router.get("/unread-count", summary="获取未读数量")
async def get_unread_count():
    """获取未读预警数量"""
    count = await alert_service.get_unread_count(DEMO_USER_ID)
    return {"count": count}


@router.post("/{alert_id}/read", summary="标记为已读")
async def mark_alert_read(alert_id: str):
    """标记单个预警为已读"""
    success = await alert_service.mark_as_read(alert_id, DEMO_USER_ID)
    if not success:
        raise HTTPException(status_code=404, detail="预警不存在")
    return {"success": True}


@router.post("/mark-all-read", summary="全部标记已读")
async def mark_all_read():
    """标记所有预警为已读"""
    count = await alert_service.mark_all_as_read(DEMO_USER_ID)
    return {"success": True, "count": count}


@router.get("/config", response_model=AlertConfig, summary="获取预警配置")
async def get_alert_config():
    """获取用户的预警配置"""
    return await alert_service.get_user_config(DEMO_USER_ID)


@router.put("/config", response_model=AlertConfig, summary="更新预警配置")
async def update_alert_config(request: UpdateAlertConfigRequest):
    """
    更新预警配置

    可更新项:
    - 启用/禁用预警
    - 各类预警阈值
    - 邮件通知设置
    - 静默时段
    """
    # 获取当前配置
    config = await alert_service.get_user_config(DEMO_USER_ID)

    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(config, key) and value is not None:
            setattr(config, key, value)

    # 保存
    return await alert_service.update_user_config(config)


@router.post("/test-email", summary="发送测试邮件")
async def test_email_notification():
    """
    发送测试邮件

    验证邮件配置是否正确
    """
    config = await alert_service.get_user_config(DEMO_USER_ID)

    if not config.email_enabled:
        raise HTTPException(status_code=400, detail="邮件通知未启用")

    if not config.email_address:
        raise HTTPException(status_code=400, detail="未配置邮箱地址")

    success = await alert_service.send_test_email(DEMO_USER_ID)

    if success:
        return {"success": True, "message": "测试邮件已发送"}
    else:
        raise HTTPException(status_code=500, detail="邮件发送失败")
