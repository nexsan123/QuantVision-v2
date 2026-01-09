"""
策略漂移监控服务
PRD 4.8 实盘vs回测差异监控
"""

from datetime import datetime, date, timedelta
from typing import Optional
import uuid

from app.schemas.drift import (
    StrategyDriftReport,
    DriftMetric,
    DriftMetricType,
    DriftSeverity,
    DriftThresholds,
)
from app.schemas.alert import AlertType, AlertSeverity


class StrategyDriftService:
    """策略漂移监控服务"""

    # PRD 附录C 定义的默认阈值
    DEFAULT_THRESHOLDS = DriftThresholds()

    # 模拟数据存储
    _drift_reports: dict[str, StrategyDriftReport] = {}
    _strategy_reports: dict[str, list[str]] = {}  # strategy_id -> [report_ids]

    def __init__(self):
        """初始化服务"""
        pass

    async def check_drift(
        self,
        strategy_id: str,
        deployment_id: str,
        period_days: int = 30,
        user_id: str = "demo",
    ) -> StrategyDriftReport:
        """
        检查策略漂移

        Args:
            strategy_id: 策略ID
            deployment_id: 部署ID
            period_days: 比较周期 (天)
            user_id: 用户ID

        Returns:
            漂移报告
        """
        # 1. 获取回测数据 (模拟)
        backtest_stats = await self._get_backtest_stats(strategy_id)

        # 2. 获取实盘/模拟盘数据 (模拟)
        live_stats = await self._get_live_stats(deployment_id, period_days)

        # 3. 计算各指标漂移
        metrics = self._calculate_drift_metrics(backtest_stats, live_stats)

        # 4. 计算整体漂移评分
        overall_severity, drift_score = self._calculate_overall_drift(metrics)

        # 5. 生成建议
        recommendations, should_pause = self._generate_recommendations(
            metrics, overall_severity
        )

        # 6. 创建报告
        report = StrategyDriftReport(
            report_id=str(uuid.uuid4()),
            strategy_id=strategy_id,
            strategy_name=await self._get_strategy_name(strategy_id),
            deployment_id=deployment_id,
            environment=live_stats.get("environment", "paper"),
            period_start=date.today() - timedelta(days=period_days),
            period_end=date.today(),
            days_compared=period_days,
            overall_severity=overall_severity,
            drift_score=drift_score,
            metrics=metrics,
            recommendations=recommendations,
            should_pause=should_pause,
            created_at=datetime.now(),
        )

        # 7. 保存报告
        await self._save_report(report)

        # 8. 触发预警 (如果严重)
        if overall_severity in [DriftSeverity.WARNING, DriftSeverity.CRITICAL]:
            await self._trigger_drift_alert(report, user_id)

        return report

    def _calculate_drift_metrics(
        self, backtest: dict, live: dict
    ) -> list[DriftMetric]:
        """计算各指标漂移"""

        thresholds = self.DEFAULT_THRESHOLDS
        metrics = []

        # 定义指标映射
        metric_configs = [
            (
                DriftMetricType.RETURN,
                "total_return",
                "收益率",
                thresholds.return_warning,
                thresholds.return_critical,
            ),
            (
                DriftMetricType.WIN_RATE,
                "win_rate",
                "胜率",
                thresholds.win_rate_warning,
                thresholds.win_rate_critical,
            ),
            (
                DriftMetricType.TURNOVER,
                "turnover_rate",
                "换手率",
                thresholds.turnover_warning,
                thresholds.turnover_critical,
            ),
            (
                DriftMetricType.SLIPPAGE,
                "avg_slippage",
                "平均滑点",
                thresholds.slippage_warning,
                thresholds.slippage_critical,
            ),
            (
                DriftMetricType.MAX_DRAWDOWN,
                "max_drawdown",
                "最大回撤",
                thresholds.max_drawdown_warning,
                thresholds.max_drawdown_critical,
            ),
            (
                DriftMetricType.HOLD_PERIOD,
                "avg_hold_days",
                "平均持仓天数",
                thresholds.hold_period_warning,
                thresholds.hold_period_critical,
            ),
        ]

        for metric_type, key, name, warn_thresh, crit_thresh in metric_configs:
            bt_value = backtest.get(key, 0)
            live_value = live.get(key, 0)

            # 计算差异
            if bt_value != 0:
                diff_pct = abs(live_value - bt_value) / abs(bt_value)
            else:
                diff_pct = 0 if live_value == 0 else 1.0

            # 判断严重程度
            if diff_pct >= crit_thresh:
                severity = DriftSeverity.CRITICAL
            elif diff_pct >= warn_thresh:
                severity = DriftSeverity.WARNING
            else:
                severity = DriftSeverity.NORMAL

            # 生成描述
            description = self._generate_metric_description(
                name, bt_value, live_value, diff_pct, severity
            )

            metrics.append(
                DriftMetric(
                    metric_type=metric_type,
                    backtest_value=bt_value,
                    live_value=live_value,
                    difference=abs(live_value - bt_value),
                    difference_pct=diff_pct,
                    warning_threshold=warn_thresh,
                    critical_threshold=crit_thresh,
                    severity=severity,
                    description=description,
                )
            )

        return metrics

    def _calculate_overall_drift(
        self, metrics: list[DriftMetric]
    ) -> tuple[DriftSeverity, float]:
        """计算整体漂移程度"""

        # 统计各级别数量
        critical_count = sum(
            1 for m in metrics if m.severity == DriftSeverity.CRITICAL
        )
        warning_count = sum(
            1 for m in metrics if m.severity == DriftSeverity.WARNING
        )

        # 计算漂移评分 (0-100)
        # 权重: 收益最重要, 其次是胜率和回撤
        weights = {
            DriftMetricType.RETURN: 0.30,
            DriftMetricType.WIN_RATE: 0.20,
            DriftMetricType.MAX_DRAWDOWN: 0.20,
            DriftMetricType.TURNOVER: 0.10,
            DriftMetricType.SLIPPAGE: 0.10,
            DriftMetricType.HOLD_PERIOD: 0.10,
        }

        drift_score = 0
        for metric in metrics:
            weight = weights.get(metric.metric_type, 0.1)
            # 相对于critical阈值的比例
            if metric.critical_threshold > 0:
                relative = metric.difference_pct / metric.critical_threshold
            else:
                relative = 0
            drift_score += min(relative, 2.0) * weight * 50  # 最高100分

        # 确定整体严重程度
        if critical_count >= 2 or drift_score >= 70:
            overall = DriftSeverity.CRITICAL
        elif critical_count >= 1 or warning_count >= 3 or drift_score >= 40:
            overall = DriftSeverity.WARNING
        else:
            overall = DriftSeverity.NORMAL

        return overall, min(drift_score, 100)

    def _generate_recommendations(
        self, metrics: list[DriftMetric], overall: DriftSeverity
    ) -> tuple[list[str], bool]:
        """生成建议"""

        recommendations = []
        should_pause = False

        for metric in metrics:
            if metric.severity == DriftSeverity.CRITICAL:
                if metric.metric_type == DriftMetricType.RETURN:
                    recommendations.append(
                        "收益差异严重，建议检查因子有效性是否发生变化"
                    )
                elif metric.metric_type == DriftMetricType.SLIPPAGE:
                    recommendations.append(
                        "滑点差异过大，考虑调整交易频率或选择流动性更好的股票"
                    )
                elif metric.metric_type == DriftMetricType.MAX_DRAWDOWN:
                    recommendations.append(
                        "实盘回撤显著高于回测，建议检查风控参数是否合理"
                    )
                elif metric.metric_type == DriftMetricType.WIN_RATE:
                    recommendations.append(
                        "胜率下降明显，建议分析近期失败交易的原因"
                    )
                elif metric.metric_type == DriftMetricType.TURNOVER:
                    recommendations.append(
                        "换手率差异大，检查是否有信号执行延迟或遗漏"
                    )
            elif metric.severity == DriftSeverity.WARNING:
                if metric.metric_type == DriftMetricType.RETURN:
                    recommendations.append(
                        "收益略有偏差，持续观察"
                    )

        if overall == DriftSeverity.CRITICAL:
            recommendations.insert(
                0,
                "⚠️ 策略实盘表现与回测差异过大，强烈建议暂停策略并进行深入分析",
            )
            should_pause = True
        elif overall == DriftSeverity.WARNING:
            recommendations.insert(0, "策略出现漂移迹象，建议密切关注并考虑调整")

        if not recommendations:
            recommendations.append("策略运行正常，实盘表现与回测基本一致")

        return recommendations, should_pause

    def _generate_metric_description(
        self,
        name: str,
        bt_value: float,
        live_value: float,
        diff_pct: float,
        severity: DriftSeverity,
    ) -> str:
        """生成指标描述"""

        direction = "高于" if live_value > bt_value else "低于"

        # 格式化数值
        if name in ["收益率", "胜率", "换手率", "最大回撤", "平均滑点"]:
            bt_str = f"{bt_value * 100:.1f}%"
            live_str = f"{live_value * 100:.1f}%"
        else:
            bt_str = f"{bt_value:.1f}"
            live_str = f"{live_value:.1f}"

        status = {
            DriftSeverity.NORMAL: "正常",
            DriftSeverity.WARNING: "需关注",
            DriftSeverity.CRITICAL: "异常",
        }[severity]

        return f"{name}: 实盘{live_str} {direction}回测{bt_str}, 差异{diff_pct * 100:.1f}% [{status}]"

    async def _trigger_drift_alert(
        self, report: StrategyDriftReport, user_id: str
    ):
        """触发漂移预警"""
        # 创建预警 (实际应调用 alert_service)
        print(
            f"[Drift Alert] 策略 {report.strategy_name} 漂移评分: {report.drift_score:.0f}"
        )

    async def _get_backtest_stats(self, strategy_id: str) -> dict:
        """获取回测统计数据 (模拟)"""
        # 模拟回测数据
        return {
            "total_return": 0.25,        # 25% 收益
            "win_rate": 0.58,            # 58% 胜率
            "turnover_rate": 0.15,       # 15% 换手率
            "avg_slippage": 0.001,       # 0.1% 滑点
            "max_drawdown": 0.12,        # 12% 最大回撤
            "avg_hold_days": 5.2,        # 平均持仓5.2天
        }

    async def _get_live_stats(self, deployment_id: str, period_days: int) -> dict:
        """获取实盘统计数据 (模拟)"""
        # 模拟实盘数据 - 有一定偏差
        import random

        # 模拟不同程度的漂移
        drift_level = random.choice(["normal", "warning", "critical"])

        if drift_level == "normal":
            return {
                "environment": "paper",
                "total_return": 0.23,        # 略低于回测
                "win_rate": 0.56,            # 略低于回测
                "turnover_rate": 0.14,
                "avg_slippage": 0.0012,
                "max_drawdown": 0.13,
                "avg_hold_days": 5.5,
            }
        elif drift_level == "warning":
            return {
                "environment": "paper",
                "total_return": 0.18,        # 明显低于回测
                "win_rate": 0.52,            # 明显低于回测
                "turnover_rate": 0.20,       # 换手率偏高
                "avg_slippage": 0.0018,      # 滑点偏大
                "max_drawdown": 0.15,
                "avg_hold_days": 4.2,
            }
        else:  # critical
            return {
                "environment": "paper",
                "total_return": 0.10,        # 严重低于回测
                "win_rate": 0.45,            # 严重低于回测
                "turnover_rate": 0.25,
                "avg_slippage": 0.003,       # 滑点严重
                "max_drawdown": 0.22,        # 回撤严重
                "avg_hold_days": 3.0,
            }

    async def _get_strategy_name(self, strategy_id: str) -> str:
        """获取策略名称 (模拟)"""
        return f"动量突破策略-{strategy_id[:8]}"

    async def _get_strategy_owner(self, strategy_id: str) -> str:
        """获取策略所有者 (模拟)"""
        return "demo"

    async def _save_report(self, report: StrategyDriftReport):
        """保存漂移报告"""
        self._drift_reports[report.report_id] = report

        if report.strategy_id not in self._strategy_reports:
            self._strategy_reports[report.strategy_id] = []
        self._strategy_reports[report.strategy_id].insert(0, report.report_id)

        # 保留最近50条
        if len(self._strategy_reports[report.strategy_id]) > 50:
            old_id = self._strategy_reports[report.strategy_id].pop()
            self._drift_reports.pop(old_id, None)

    async def get_drift_history(
        self, strategy_id: str, limit: int = 10
    ) -> list[StrategyDriftReport]:
        """获取漂移历史报告"""
        report_ids = self._strategy_reports.get(strategy_id, [])[:limit]
        return [
            self._drift_reports[rid]
            for rid in report_ids
            if rid in self._drift_reports
        ]

    async def get_report_by_id(self, report_id: str) -> Optional[StrategyDriftReport]:
        """根据ID获取报告"""
        return self._drift_reports.get(report_id)

    async def acknowledge_report(self, report_id: str, user_id: str) -> bool:
        """确认漂移报告"""
        report = self._drift_reports.get(report_id)
        if not report:
            return False

        # 更新为已确认
        self._drift_reports[report_id] = report.model_copy(
            update={"is_acknowledged": True}
        )
        return True

    async def get_latest_report(
        self, strategy_id: str
    ) -> Optional[StrategyDriftReport]:
        """获取策略最新的漂移报告"""
        report_ids = self._strategy_reports.get(strategy_id, [])
        if not report_ids:
            return None
        return self._drift_reports.get(report_ids[0])


# 单例服务实例
drift_service = StrategyDriftService()
