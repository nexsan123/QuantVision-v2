"""
风险监控器

实时监控组合风险指标并生成警报
"""

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


class AlertLevel(str, Enum):
    """警报级别"""
    INFO = "info"           # 信息
    WARNING = "warning"     # 警告
    CRITICAL = "critical"   # 严重
    EMERGENCY = "emergency" # 紧急


class MetricType(str, Enum):
    """指标类型"""
    VAR = "var"                         # VaR
    VOLATILITY = "volatility"           # 波动率
    DRAWDOWN = "drawdown"               # 回撤
    SHARPE = "sharpe"                   # 夏普比率
    BETA = "beta"                       # Beta
    EXPOSURE = "exposure"               # 风险敞口
    CONCENTRATION = "concentration"     # 集中度
    LIQUIDITY = "liquidity"             # 流动性
    PNL = "pnl"                         # 盈亏
    TURNOVER = "turnover"               # 换手率


@dataclass
class RiskMetrics:
    """风险指标集"""
    timestamp: datetime = field(default_factory=datetime.now)

    # 收益风险
    daily_return: float = 0.0
    cumulative_return: float = 0.0
    volatility: float = 0.0
    sharpe: float = 0.0

    # VaR
    var_95: float = 0.0
    var_99: float = 0.0
    cvar_95: float = 0.0

    # 回撤
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0
    drawdown_duration: int = 0

    # 组合特征
    beta: float = 1.0
    tracking_error: float = 0.0
    information_ratio: float = 0.0

    # 集中度
    top1_weight: float = 0.0
    top5_weight: float = 0.0
    herfindahl_index: float = 0.0

    # 流动性
    liquidity_score: float = 1.0
    days_to_liquidate: float = 0.0

    # 杠杆
    gross_leverage: float = 1.0
    net_leverage: float = 1.0


@dataclass
class RiskAlert:
    """风险警报"""
    timestamp: datetime
    level: AlertLevel
    metric_type: MetricType
    message: str
    current_value: float
    threshold: float
    details: dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False


@dataclass
class AlertRule:
    """警报规则"""
    metric_type: MetricType
    level: AlertLevel
    condition: str                      # "gt", "lt", "gte", "lte"
    threshold: float
    message_template: str
    cooldown_minutes: int = 15          # 同类警报冷却时间


class RiskMonitor:
    """
    风险监控器

    实时监控风险指标，在触发阈值时生成警报

    使用示例:
    ```python
    monitor = RiskMonitor()

    # 添加自定义规则
    monitor.add_rule(AlertRule(
        metric_type=MetricType.DRAWDOWN,
        level=AlertLevel.WARNING,
        condition="gt",
        threshold=0.10,
        message_template="回撤超过 10%: {value:.2%}",
    ))

    # 更新指标
    monitor.update(RiskMetrics(
        current_drawdown=0.12,
        volatility=0.25,
    ))

    # 获取警报
    alerts = monitor.get_active_alerts()
    ```
    """

    def __init__(
        self,
        on_alert: Callable[[RiskAlert], None] | None = None,
        history_size: int = 1000,
    ):
        """
        Args:
            on_alert: 警报回调函数
            history_size: 历史数据保留数量
        """
        self.on_alert = on_alert
        self.history_size = history_size

        self._rules: list[AlertRule] = []
        self._alerts: list[RiskAlert] = []
        self._metrics_history: deque[RiskMetrics] = deque(maxlen=history_size)
        self._last_alert_time: dict[str, datetime] = {}

        # 添加默认规则
        self._setup_default_rules()

    def _setup_default_rules(self) -> None:
        """设置默认警报规则"""
        default_rules = [
            # 回撤警报
            AlertRule(
                metric_type=MetricType.DRAWDOWN,
                level=AlertLevel.WARNING,
                condition="gt",
                threshold=0.10,
                message_template="回撤达到 {value:.2%}，超过警戒线 10%",
            ),
            AlertRule(
                metric_type=MetricType.DRAWDOWN,
                level=AlertLevel.CRITICAL,
                condition="gt",
                threshold=0.20,
                message_template="回撤达到 {value:.2%}，超过严重线 20%",
            ),

            # 波动率警报
            AlertRule(
                metric_type=MetricType.VOLATILITY,
                level=AlertLevel.WARNING,
                condition="gt",
                threshold=0.30,
                message_template="波动率升至 {value:.2%}，超过警戒线 30%",
            ),

            # VaR 警报
            AlertRule(
                metric_type=MetricType.VAR,
                level=AlertLevel.WARNING,
                condition="gt",
                threshold=0.05,
                message_template="日 VaR 达到 {value:.2%}，风险偏高",
            ),

            # 集中度警报
            AlertRule(
                metric_type=MetricType.CONCENTRATION,
                level=AlertLevel.WARNING,
                condition="gt",
                threshold=0.25,
                message_template="单一持仓占比 {value:.2%}，超过 25%",
            ),

            # 流动性警报
            AlertRule(
                metric_type=MetricType.LIQUIDITY,
                level=AlertLevel.WARNING,
                condition="lt",
                threshold=0.5,
                message_template="流动性评分 {value:.2f}，低于警戒值",
            ),
        ]

        for rule in default_rules:
            self._rules.append(rule)

    def add_rule(self, rule: AlertRule) -> None:
        """添加警报规则"""
        self._rules.append(rule)

    def remove_rule(self, metric_type: MetricType, level: AlertLevel) -> None:
        """移除规则"""
        self._rules = [
            r for r in self._rules
            if not (r.metric_type == metric_type and r.level == level)
        ]

    def update(self, metrics: RiskMetrics) -> list[RiskAlert]:
        """
        更新风险指标并检查警报

        Args:
            metrics: 风险指标

        Returns:
            触发的警报列表
        """
        self._metrics_history.append(metrics)

        triggered_alerts = []

        for rule in self._rules:
            # 获取指标值
            value = self._get_metric_value(metrics, rule.metric_type)
            if value is None:
                continue

            # 检查条件
            is_triggered = self._check_condition(value, rule.condition, rule.threshold)
            if not is_triggered:
                continue

            # 检查冷却时间
            rule_key = f"{rule.metric_type.value}_{rule.level.value}"
            last_time = self._last_alert_time.get(rule_key)
            if last_time:
                elapsed = (datetime.now() - last_time).total_seconds() / 60
                if elapsed < rule.cooldown_minutes:
                    continue

            # 生成警报
            alert = RiskAlert(
                timestamp=datetime.now(),
                level=rule.level,
                metric_type=rule.metric_type,
                message=rule.message_template.format(value=value),
                current_value=value,
                threshold=rule.threshold,
            )

            self._alerts.append(alert)
            self._last_alert_time[rule_key] = datetime.now()
            triggered_alerts.append(alert)

            logger.warning(
                "风险警报触发",
                level=rule.level.value,
                metric=rule.metric_type.value,
                value=f"{value:.4f}",
                threshold=f"{rule.threshold:.4f}",
            )

            if self.on_alert:
                self.on_alert(alert)

        return triggered_alerts

    def _get_metric_value(
        self, metrics: RiskMetrics, metric_type: MetricType
    ) -> float | None:
        """获取指标值"""
        mapping = {
            MetricType.VAR: metrics.var_95,
            MetricType.VOLATILITY: metrics.volatility,
            MetricType.DRAWDOWN: metrics.current_drawdown,
            MetricType.SHARPE: metrics.sharpe,
            MetricType.BETA: metrics.beta,
            MetricType.CONCENTRATION: metrics.top1_weight,
            MetricType.LIQUIDITY: metrics.liquidity_score,
            MetricType.PNL: metrics.daily_return,
        }
        return mapping.get(metric_type)

    def _check_condition(
        self, value: float, condition: str, threshold: float
    ) -> bool:
        """检查条件"""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "gte":
            return value >= threshold
        elif condition == "lte":
            return value <= threshold
        return False

    def get_active_alerts(
        self,
        level: AlertLevel | None = None,
        since_hours: float = 24,
    ) -> list[RiskAlert]:
        """
        获取活跃警报

        Args:
            level: 筛选级别
            since_hours: 时间范围 (小时)

        Returns:
            警报列表
        """
        cutoff = datetime.now() - timedelta(hours=since_hours)

        alerts = [a for a in self._alerts if a.timestamp > cutoff]

        if level:
            alerts = [a for a in alerts if a.level == level]

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def acknowledge_alert(self, alert_idx: int) -> None:
        """确认警报"""
        if 0 <= alert_idx < len(self._alerts):
            self._alerts[alert_idx].acknowledged = True

    def get_current_metrics(self) -> RiskMetrics | None:
        """获取最新指标"""
        return self._metrics_history[-1] if self._metrics_history else None

    def get_metrics_history(self, n: int = 100) -> list[RiskMetrics]:
        """获取历史指标"""
        return list(self._metrics_history)[-n:]

    def calculate_risk_score(self, metrics: RiskMetrics | None = None) -> float:
        """
        计算综合风险评分 (0-100, 越高风险越大)

        Args:
            metrics: 风险指标 (默认使用最新)

        Returns:
            风险评分
        """
        if metrics is None:
            metrics = self.get_current_metrics()
            if metrics is None:
                return 0.0

        scores = []

        # 回撤分数 (0-30)
        dd_score = min(30, metrics.current_drawdown * 150)
        scores.append(dd_score)

        # 波动率分数 (0-25)
        vol_score = min(25, (metrics.volatility - 0.15) * 100) if metrics.volatility > 0.15 else 0
        scores.append(vol_score)

        # VaR 分数 (0-20)
        var_score = min(20, metrics.var_95 * 400)
        scores.append(var_score)

        # 集中度分数 (0-15)
        conc_score = min(15, metrics.top1_weight * 50)
        scores.append(conc_score)

        # 流动性分数 (0-10)
        liq_score = max(0, (1 - metrics.liquidity_score) * 10)
        scores.append(liq_score)

        return min(100, sum(scores))

    def get_status(self) -> dict[str, Any]:
        """获取监控状态"""
        current = self.get_current_metrics()
        active_alerts = self.get_active_alerts(since_hours=24)

        return {
            "last_update": current.timestamp.isoformat() if current else None,
            "risk_score": self.calculate_risk_score(),
            "active_alerts_count": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            "warning_alerts": len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
            "current_drawdown": current.current_drawdown if current else None,
            "current_volatility": current.volatility if current else None,
            "current_var": current.var_95 if current else None,
        }


class RiskDashboard:
    """
    风险仪表板

    聚合多个监控器的数据
    """

    def __init__(self):
        self.monitors: dict[str, RiskMonitor] = {}

    def add_monitor(self, name: str, monitor: RiskMonitor) -> None:
        """添加监控器"""
        self.monitors[name] = monitor

    def get_overview(self) -> dict[str, Any]:
        """获取全局概览"""
        overview = {
            "timestamp": datetime.now().isoformat(),
            "portfolios": {},
            "total_alerts": 0,
            "critical_count": 0,
            "max_risk_score": 0,
        }

        for name, monitor in self.monitors.items():
            status = monitor.get_status()
            overview["portfolios"][name] = status
            overview["total_alerts"] += status["active_alerts_count"]
            overview["critical_count"] += status["critical_alerts"]
            overview["max_risk_score"] = max(
                overview["max_risk_score"],
                status["risk_score"],
            )

        return overview

    def get_all_alerts(self) -> list[tuple[str, RiskAlert]]:
        """获取所有警报"""
        all_alerts = []
        for name, monitor in self.monitors.items():
            for alert in monitor.get_active_alerts():
                all_alerts.append((name, alert))

        return sorted(all_alerts, key=lambda x: x[1].timestamp, reverse=True)
