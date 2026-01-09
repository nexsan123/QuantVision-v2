"""
风险预警服务

PRD 4.14: 风险预警通知
- 预警触发检测
- 预警创建和管理
- 通知发送
"""

from datetime import datetime
from typing import Optional
import uuid

import structlog

from app.schemas.alert import (
    RiskAlert,
    AlertType,
    AlertSeverity,
    AlertChannel,
    AlertConfig,
)
from app.services.email_service import email_service

logger = structlog.get_logger()


class AlertService:
    """风险预警服务"""

    # 默认预警阈值
    DEFAULT_THRESHOLDS = {
        AlertType.DAILY_LOSS: 0.03,       # 单日亏损 > 3%
        AlertType.MAX_DRAWDOWN: 0.10,     # 最大回撤 > 10%
        AlertType.CONCENTRATION: 0.30,    # 单股持仓 > 30%
        AlertType.VIX_HIGH: 30.0,         # VIX > 30
    }

    # 模拟数据存储
    _alerts: dict[str, list[RiskAlert]] = {}
    _configs: dict[str, AlertConfig] = {}

    def __init__(self):
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化模拟数据"""
        now = datetime.now()

        # 模拟一些预警
        self._alerts["demo-user"] = [
            RiskAlert(
                alert_id=str(uuid.uuid4()),
                user_id="demo-user",
                strategy_id="strategy-001",
                alert_type=AlertType.DAILY_LOSS,
                severity=AlertSeverity.WARNING,
                title="单日亏损预警: 3.5%",
                message="您的策略今日亏损已达 3.5%，超过预设阈值 3%。建议检查持仓风险。",
                details={"current_value": -0.035, "threshold": 0.03},
                is_read=False,
                created_at=now,
            ),
            RiskAlert(
                alert_id=str(uuid.uuid4()),
                user_id="demo-user",
                alert_type=AlertType.VIX_HIGH,
                severity=AlertSeverity.INFO,
                title="市场波动率预警: VIX=28.5",
                message="VIX指数接近预警阈值，市场波动可能加剧。",
                details={"current_value": 28.5, "threshold": 30.0},
                is_read=True,
                created_at=now,
            ),
        ]

        # 模拟用户配置
        self._configs["demo-user"] = AlertConfig(
            user_id="demo-user",
            enabled=True,
            daily_loss_threshold=0.03,
            max_drawdown_threshold=0.10,
            concentration_threshold=0.30,
            vix_threshold=30.0,
            email_enabled=True,
            email_address="user@example.com",
        )

    async def check_and_alert(
        self,
        user_id: str,
        alert_type: AlertType,
        current_value: float,
        strategy_id: Optional[str] = None,
        extra_details: Optional[dict] = None,
    ) -> Optional[RiskAlert]:
        """检查是否需要触发预警"""
        logger.info(
            "check_and_alert",
            user_id=user_id,
            alert_type=alert_type,
            current_value=current_value,
        )

        # 获取用户配置
        config = await self.get_user_config(user_id)
        if not config.enabled:
            return None

        # 获取阈值
        threshold = self._get_threshold(config, alert_type)

        # 判断是否触发
        should_alert = self._should_trigger(alert_type, current_value, threshold)
        if not should_alert:
            return None

        # 创建预警
        alert = await self._create_alert(
            user_id=user_id,
            strategy_id=strategy_id,
            alert_type=alert_type,
            current_value=current_value,
            threshold=threshold,
            extra_details=extra_details,
        )

        # 发送通知
        await self._send_notification(alert, config)

        return alert

    async def create_manual_alert(
        self,
        user_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        strategy_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> RiskAlert:
        """手动创建预警 (用于冲突、系统错误等)"""
        alert = RiskAlert(
            alert_id=str(uuid.uuid4()),
            user_id=user_id,
            strategy_id=strategy_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details=details,
            created_at=datetime.now(),
        )

        await self._save_alert(alert)

        # 获取用户配置并发送
        config = await self.get_user_config(user_id)
        await self._send_notification(alert, config)

        return alert

    async def get_user_alerts(
        self,
        user_id: str,
        unread_only: bool = False,
        alert_type: Optional[AlertType] = None,
        limit: int = 50,
    ) -> list[RiskAlert]:
        """获取用户的预警列表"""
        alerts = self._alerts.get(user_id, [])

        # 筛选
        if unread_only:
            alerts = [a for a in alerts if not a.is_read]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        # 按时间倒序
        alerts = sorted(alerts, key=lambda a: a.created_at, reverse=True)

        return alerts[:limit]

    async def get_unread_count(self, user_id: str) -> int:
        """获取未读预警数量"""
        alerts = self._alerts.get(user_id, [])
        return sum(1 for a in alerts if not a.is_read)

    async def mark_as_read(self, alert_id: str, user_id: str) -> bool:
        """标记预警为已读"""
        alerts = self._alerts.get(user_id, [])
        for alert in alerts:
            if alert.alert_id == alert_id:
                alert.is_read = True
                return True
        return False

    async def mark_all_as_read(self, user_id: str) -> int:
        """标记所有预警为已读"""
        alerts = self._alerts.get(user_id, [])
        count = 0
        for alert in alerts:
            if not alert.is_read:
                alert.is_read = True
                count += 1
        return count

    async def get_user_config(self, user_id: str) -> AlertConfig:
        """获取用户预警配置"""
        if user_id not in self._configs:
            self._configs[user_id] = AlertConfig(user_id=user_id)
        return self._configs[user_id]

    async def update_user_config(self, config: AlertConfig) -> AlertConfig:
        """更新用户预警配置"""
        self._configs[config.user_id] = config
        return config

    async def send_test_email(self, user_id: str) -> bool:
        """发送测试邮件"""
        config = await self.get_user_config(user_id)
        if not config.email_address:
            return False

        return await email_service.send_test_email(config.email_address)

    def _get_threshold(self, config: AlertConfig, alert_type: AlertType) -> float:
        """获取阈值"""
        thresholds = {
            AlertType.DAILY_LOSS: config.daily_loss_threshold,
            AlertType.MAX_DRAWDOWN: config.max_drawdown_threshold,
            AlertType.CONCENTRATION: config.concentration_threshold,
            AlertType.VIX_HIGH: config.vix_threshold,
        }
        return thresholds.get(alert_type, self.DEFAULT_THRESHOLDS.get(alert_type, 0))

    def _should_trigger(
        self,
        alert_type: AlertType,
        value: float,
        threshold: float,
    ) -> bool:
        """判断是否应该触发预警"""
        if alert_type in [AlertType.DAILY_LOSS, AlertType.MAX_DRAWDOWN]:
            return abs(value) >= threshold  # 亏损用绝对值
        elif alert_type == AlertType.VIX_HIGH:
            return value >= threshold
        elif alert_type == AlertType.CONCENTRATION:
            return value >= threshold
        return False

    def _get_severity(
        self,
        alert_type: AlertType,
        value: float,
        threshold: float,
    ) -> AlertSeverity:
        """根据超出程度确定严重级别"""
        ratio = abs(value) / threshold if threshold > 0 else 1

        if ratio >= 2.0:  # 超出2倍
            return AlertSeverity.CRITICAL
        elif ratio >= 1.0:  # 刚达到阈值
            return AlertSeverity.WARNING
        return AlertSeverity.INFO

    async def _create_alert(
        self,
        user_id: str,
        strategy_id: Optional[str],
        alert_type: AlertType,
        current_value: float,
        threshold: float,
        extra_details: Optional[dict],
    ) -> RiskAlert:
        """创建预警对象"""
        severity = self._get_severity(alert_type, current_value, threshold)
        title, message = self._generate_alert_message(alert_type, current_value, threshold)

        alert = RiskAlert(
            alert_id=str(uuid.uuid4()),
            user_id=user_id,
            strategy_id=strategy_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details={
                "current_value": current_value,
                "threshold": threshold,
                **(extra_details or {}),
            },
            created_at=datetime.now(),
        )

        await self._save_alert(alert)
        return alert

    def _generate_alert_message(
        self,
        alert_type: AlertType,
        value: float,
        threshold: float,
    ) -> tuple[str, str]:
        """生成预警标题和消息"""
        messages = {
            AlertType.DAILY_LOSS: (
                f"单日亏损预警: {abs(value) * 100:.1f}%",
                f"您的账户今日亏损已达 {abs(value) * 100:.1f}%，超过预设阈值 {threshold * 100:.1f}%。建议检查持仓风险。",
            ),
            AlertType.MAX_DRAWDOWN: (
                f"最大回撤预警: {abs(value) * 100:.1f}%",
                f"策略最大回撤已达 {abs(value) * 100:.1f}%，触及预警阈值 {threshold * 100:.1f}%。建议评估是否暂停策略。",
            ),
            AlertType.CONCENTRATION: (
                "持仓集中度预警",
                f"单只股票持仓占比达 {value * 100:.1f}%，超过安全阈值 {threshold * 100:.1f}%。建议分散投资。",
            ),
            AlertType.VIX_HIGH: (
                f"市场波动率预警: VIX={value:.1f}",
                f"VIX指数已达 {value:.1f}，市场波动加剧。建议谨慎操作，注意风险控制。",
            ),
        }

        return messages.get(alert_type, ("风险预警", "请检查您的账户"))

    async def _save_alert(self, alert: RiskAlert):
        """保存预警"""
        if alert.user_id not in self._alerts:
            self._alerts[alert.user_id] = []
        self._alerts[alert.user_id].append(alert)

    async def _send_notification(self, alert: RiskAlert, config: AlertConfig):
        """发送通知"""
        # 检查静默时段
        if self._is_quiet_hours(config):
            logger.info("notification_skipped_quiet_hours", alert_id=alert.alert_id)
            return

        # 发送邮件 (Phase 1)
        if config.email_enabled and config.email_address:
            try:
                success = await email_service.send_alert_email(
                    to_email=config.email_address,
                    alert=alert,
                )
                if success:
                    alert.sent_channels.append(AlertChannel.EMAIL)
                    alert.is_sent = True
                    alert.sent_at = datetime.now()
            except Exception as e:
                logger.error("email_notification_failed", error=str(e))

    def _is_quiet_hours(self, config: AlertConfig) -> bool:
        """检查是否在静默时段"""
        if config.quiet_hours_start is None or config.quiet_hours_end is None:
            return False

        current_hour = datetime.now().hour
        start, end = config.quiet_hours_start, config.quiet_hours_end

        if start <= end:
            return start <= current_hour < end
        else:  # 跨午夜
            return current_hour >= start or current_hour < end


# 全局服务实例
alert_service = AlertService()
