"""
告警通知服务
Sprint 13: T35 - 告警通知系统

提供:
- 多渠道通知 (WebSocket, Email, Webhook)
- 通知规则引擎
- 通知历史记录
- 通知限流
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from collections import defaultdict

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ==================== 枚举类型 ====================

class NotificationChannel(str, Enum):
    WEBSOCKET = "websocket"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationCategory(str, Enum):
    TRADE = "trade"
    RISK = "risk"
    SYSTEM = "system"
    STRATEGY = "strategy"
    MARKET = "market"


# ==================== 数据模型 ====================

class NotificationPayload(BaseModel):
    """通知内容"""
    title: str
    message: str
    category: NotificationCategory
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: dict[str, Any] | None = None
    action_url: str | None = None


class NotificationRule(BaseModel):
    """通知规则"""
    id: str
    name: str
    enabled: bool = True
    category: NotificationCategory
    min_priority: NotificationPriority = NotificationPriority.LOW
    channels: list[NotificationChannel] = [NotificationChannel.WEBSOCKET]
    rate_limit: int = 10  # 每分钟最大通知数
    quiet_hours: tuple[int, int] | None = None  # 静默时段 (开始小时, 结束小时)


class NotificationRecord(BaseModel):
    """通知记录"""
    id: str
    payload: NotificationPayload
    channels: list[NotificationChannel]
    sent_at: datetime
    success: bool
    error: str | None = None


# ==================== 通知服务 ====================

class NotificationService:
    """通知服务"""

    def __init__(self):
        self.rules: dict[str, NotificationRule] = {}
        self.history: list[NotificationRecord] = []
        self.rate_limits: dict[str, list[datetime]] = defaultdict(list)
        self.ws_clients: list[Any] = []  # WebSocket 客户端列表

        # 初始化默认规则
        self._init_default_rules()

    def _init_default_rules(self) -> None:
        """初始化默认通知规则"""
        default_rules = [
            NotificationRule(
                id="trade_executed",
                name="交易执行通知",
                category=NotificationCategory.TRADE,
                min_priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.WEBSOCKET],
            ),
            NotificationRule(
                id="risk_alert",
                name="风险预警",
                category=NotificationCategory.RISK,
                min_priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.WEBSOCKET, NotificationChannel.EMAIL],
            ),
            NotificationRule(
                id="system_alert",
                name="系统告警",
                category=NotificationCategory.SYSTEM,
                min_priority=NotificationPriority.HIGH,
                channels=[NotificationChannel.WEBSOCKET],
            ),
            NotificationRule(
                id="strategy_status",
                name="策略状态变更",
                category=NotificationCategory.STRATEGY,
                min_priority=NotificationPriority.MEDIUM,
                channels=[NotificationChannel.WEBSOCKET],
            ),
            NotificationRule(
                id="market_event",
                name="市场事件",
                category=NotificationCategory.MARKET,
                min_priority=NotificationPriority.LOW,
                channels=[NotificationChannel.WEBSOCKET],
            ),
        ]

        for rule in default_rules:
            self.rules[rule.id] = rule

    # ==================== 规则管理 ====================

    def add_rule(self, rule: NotificationRule) -> None:
        """添加通知规则"""
        self.rules[rule.id] = rule
        logger.info("notification_rule_added", rule_id=rule.id, name=rule.name)

    def update_rule(self, rule_id: str, updates: dict[str, Any]) -> NotificationRule | None:
        """更新通知规则"""
        if rule_id not in self.rules:
            return None

        rule = self.rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        logger.info("notification_rule_updated", rule_id=rule_id)
        return rule

    def delete_rule(self, rule_id: str) -> bool:
        """删除通知规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info("notification_rule_deleted", rule_id=rule_id)
            return True
        return False

    def get_rules(self) -> list[NotificationRule]:
        """获取所有规则"""
        return list(self.rules.values())

    # ==================== 限流检查 ====================

    def _check_rate_limit(self, rule_id: str, rate_limit: int) -> bool:
        """检查是否超过限流"""
        now = datetime.now()
        window_start = now - timedelta(minutes=1)

        # 清理过期记录
        self.rate_limits[rule_id] = [
            t for t in self.rate_limits[rule_id]
            if t > window_start
        ]

        # 检查是否超限
        if len(self.rate_limits[rule_id]) >= rate_limit:
            return False

        self.rate_limits[rule_id].append(now)
        return True

    def _is_quiet_hours(self, quiet_hours: tuple[int, int] | None) -> bool:
        """检查是否在静默时段"""
        if not quiet_hours:
            return False

        current_hour = datetime.now().hour
        start, end = quiet_hours

        if start <= end:
            return start <= current_hour < end
        else:
            # 跨午夜的情况
            return current_hour >= start or current_hour < end

    # ==================== 发送通知 ====================

    async def send(self, payload: NotificationPayload) -> NotificationRecord:
        """发送通知"""
        # 查找匹配的规则
        matching_rules = [
            rule for rule in self.rules.values()
            if rule.enabled
            and rule.category == payload.category
            and self._priority_matches(payload.priority, rule.min_priority)
            and not self._is_quiet_hours(rule.quiet_hours)
        ]

        if not matching_rules:
            logger.debug("no_matching_rules", category=payload.category)
            return self._create_record(payload, [], False, "No matching rules")

        # 收集所有渠道
        channels: set[NotificationChannel] = set()
        for rule in matching_rules:
            if self._check_rate_limit(rule.id, rule.rate_limit):
                channels.update(rule.channels)

        if not channels:
            logger.warning("rate_limited", category=payload.category)
            return self._create_record(payload, [], False, "Rate limited")

        # 发送到各渠道
        errors = []
        for channel in channels:
            try:
                await self._send_to_channel(channel, payload)
            except Exception as e:
                errors.append(f"{channel}: {str(e)}")
                logger.error("notification_failed", channel=channel, error=str(e))

        success = len(errors) == 0
        record = self._create_record(
            payload,
            list(channels),
            success,
            "; ".join(errors) if errors else None,
        )

        self.history.append(record)
        # 保留最近 1000 条记录
        if len(self.history) > 1000:
            self.history = self.history[-1000:]

        return record

    def _priority_matches(
        self,
        actual: NotificationPriority,
        minimum: NotificationPriority,
    ) -> bool:
        """检查优先级是否匹配"""
        priority_order = {
            NotificationPriority.LOW: 0,
            NotificationPriority.MEDIUM: 1,
            NotificationPriority.HIGH: 2,
            NotificationPriority.CRITICAL: 3,
        }
        return priority_order[actual] >= priority_order[minimum]

    async def _send_to_channel(
        self,
        channel: NotificationChannel,
        payload: NotificationPayload,
    ) -> None:
        """发送到指定渠道"""
        if channel == NotificationChannel.WEBSOCKET:
            await self._send_websocket(payload)
        elif channel == NotificationChannel.EMAIL:
            await self._send_email(payload)
        elif channel == NotificationChannel.WEBHOOK:
            await self._send_webhook(payload)
        elif channel == NotificationChannel.SMS:
            await self._send_sms(payload)

    async def _send_websocket(self, payload: NotificationPayload) -> None:
        """发送 WebSocket 通知"""
        message = {
            "type": "notification",
            "data": {
                "title": payload.title,
                "message": payload.message,
                "category": payload.category,
                "priority": payload.priority,
                "data": payload.data,
                "action_url": payload.action_url,
                "timestamp": datetime.now().isoformat(),
            }
        }

        # 广播到所有 WebSocket 客户端
        for client in self.ws_clients:
            try:
                await client.send_json(message)
            except Exception:
                pass  # 忽略发送失败

        logger.debug("websocket_notification_sent", title=payload.title)

    async def _send_email(self, payload: NotificationPayload) -> None:
        """发送邮件通知 (占位实现)"""
        # TODO: 实现邮件发送
        logger.info("email_notification", title=payload.title, message=payload.message)

    async def _send_webhook(self, payload: NotificationPayload) -> None:
        """发送 Webhook 通知 (占位实现)"""
        # TODO: 实现 Webhook 调用
        logger.info("webhook_notification", title=payload.title)

    async def _send_sms(self, payload: NotificationPayload) -> None:
        """发送短信通知 (占位实现)"""
        # TODO: 实现短信发送
        logger.info("sms_notification", title=payload.title)

    def _create_record(
        self,
        payload: NotificationPayload,
        channels: list[NotificationChannel],
        success: bool,
        error: str | None,
    ) -> NotificationRecord:
        """创建通知记录"""
        import uuid
        return NotificationRecord(
            id=str(uuid.uuid4()),
            payload=payload,
            channels=channels,
            sent_at=datetime.now(),
            success=success,
            error=error,
        )

    # ==================== WebSocket 客户端管理 ====================

    def register_client(self, client: Any) -> None:
        """注册 WebSocket 客户端"""
        self.ws_clients.append(client)
        logger.debug("ws_client_registered", total=len(self.ws_clients))

    def unregister_client(self, client: Any) -> None:
        """注销 WebSocket 客户端"""
        if client in self.ws_clients:
            self.ws_clients.remove(client)
        logger.debug("ws_client_unregistered", total=len(self.ws_clients))

    # ==================== 历史查询 ====================

    def get_history(
        self,
        category: NotificationCategory | None = None,
        limit: int = 50,
    ) -> list[NotificationRecord]:
        """获取通知历史"""
        records = self.history
        if category:
            records = [r for r in records if r.payload.category == category]
        return records[-limit:]


# ==================== 全局实例 ====================

notification_service = NotificationService()


# ==================== 便捷函数 ====================

async def notify_trade(
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
) -> NotificationRecord:
    """发送交易通知"""
    return await notification_service.send(NotificationPayload(
        title=title,
        message=message,
        category=NotificationCategory.TRADE,
        priority=priority,
        data=data,
    ))


async def notify_risk(
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
    priority: NotificationPriority = NotificationPriority.HIGH,
) -> NotificationRecord:
    """发送风险通知"""
    return await notification_service.send(NotificationPayload(
        title=title,
        message=message,
        category=NotificationCategory.RISK,
        priority=priority,
        data=data,
    ))


async def notify_system(
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
) -> NotificationRecord:
    """发送系统通知"""
    return await notification_service.send(NotificationPayload(
        title=title,
        message=message,
        category=NotificationCategory.SYSTEM,
        priority=priority,
        data=data,
    ))


async def notify_strategy(
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
) -> NotificationRecord:
    """发送策略通知"""
    return await notification_service.send(NotificationPayload(
        title=title,
        message=message,
        category=NotificationCategory.STRATEGY,
        priority=priority,
        data=data,
    ))
