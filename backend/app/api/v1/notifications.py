"""
通知管理 API
Sprint 13: T35 - 告警通知系统

提供:
- 通知规则管理
- 通知历史查询
- 测试通知发送
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.notification_service import (
    notification_service,
    NotificationPayload,
    NotificationRule,
    NotificationCategory,
    NotificationPriority,
    NotificationChannel,
)

router = APIRouter()


# ==================== 请求模型 ====================

class RuleUpdate(BaseModel):
    enabled: bool | None = None
    min_priority: NotificationPriority | None = None
    channels: list[NotificationChannel] | None = None
    rate_limit: int | None = None
    quiet_hours: tuple[int, int] | None = None


class TestNotification(BaseModel):
    title: str
    message: str
    category: NotificationCategory = NotificationCategory.SYSTEM
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: dict[str, Any] | None = None


# ==================== 规则管理 ====================

@router.get("/notifications/rules")
async def list_rules():
    """获取所有通知规则"""
    rules = notification_service.get_rules()
    return {
        "rules": [
            {
                "id": rule.id,
                "name": rule.name,
                "enabled": rule.enabled,
                "category": rule.category,
                "min_priority": rule.min_priority,
                "channels": rule.channels,
                "rate_limit": rule.rate_limit,
                "quiet_hours": rule.quiet_hours,
            }
            for rule in rules
        ]
    }


@router.put("/notifications/rules/{rule_id}")
async def update_rule(rule_id: str, update: RuleUpdate):
    """更新通知规则"""
    updates = {k: v for k, v in update.model_dump().items() if v is not None}
    rule = notification_service.update_rule(rule_id, updates)

    if not rule:
        return {"error": "Rule not found"}

    return {
        "id": rule.id,
        "name": rule.name,
        "enabled": rule.enabled,
        "category": rule.category,
        "min_priority": rule.min_priority,
        "channels": rule.channels,
        "rate_limit": rule.rate_limit,
    }


@router.post("/notifications/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: str):
    """切换规则启用状态"""
    rules = notification_service.rules
    if rule_id not in rules:
        return {"error": "Rule not found"}

    rules[rule_id].enabled = not rules[rule_id].enabled
    return {"enabled": rules[rule_id].enabled}


# ==================== 通知历史 ====================

@router.get("/notifications/history")
async def get_history(
    category: NotificationCategory | None = None,
    limit: int = 50,
):
    """获取通知历史"""
    records = notification_service.get_history(category, limit)

    return {
        "records": [
            {
                "id": record.id,
                "title": record.payload.title,
                "message": record.payload.message,
                "category": record.payload.category,
                "priority": record.payload.priority,
                "channels": record.channels,
                "sent_at": record.sent_at.isoformat(),
                "success": record.success,
                "error": record.error,
            }
            for record in records
        ]
    }


# ==================== 测试通知 ====================

@router.post("/notifications/test")
async def send_test_notification(notification: TestNotification):
    """发送测试通知"""
    payload = NotificationPayload(
        title=notification.title,
        message=notification.message,
        category=notification.category,
        priority=notification.priority,
        data=notification.data,
    )

    record = await notification_service.send(payload)

    return {
        "id": record.id,
        "success": record.success,
        "channels": record.channels,
        "error": record.error,
    }


# ==================== 统计信息 ====================

@router.get("/notifications/stats")
async def get_stats():
    """获取通知统计"""
    history = notification_service.history

    total = len(history)
    successful = sum(1 for r in history if r.success)
    failed = total - successful

    by_category = {}
    by_priority = {}

    for record in history:
        cat = record.payload.category
        pri = record.payload.priority

        by_category[cat] = by_category.get(cat, 0) + 1
        by_priority[pri] = by_priority.get(pri, 0) + 1

    return {
        "total": total,
        "successful": successful,
        "failed": failed,
        "success_rate": round(successful / total * 100, 2) if total > 0 else 100,
        "by_category": by_category,
        "by_priority": by_priority,
        "active_rules": sum(1 for r in notification_service.rules.values() if r.enabled),
        "ws_clients": len(notification_service.ws_clients),
    }
