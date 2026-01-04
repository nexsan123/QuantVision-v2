"""
Phase 9: 偏差检测服务

实现多种偏差检测:
- 前视偏差 (Lookahead Bias)
- 幸存者偏差 (Survivorship Bias)
- 数据窥探偏差 (Data Snooping Bias)
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import numpy as np
from scipy import stats
import structlog

logger = structlog.get_logger()


@dataclass
class LookaheadBiasIssue:
    """前视偏差问题"""
    field: str
    description: str
    severity: str  # high, medium, low
    location: str
    suggestion: str


@dataclass
class LookaheadBiasResult:
    """前视偏差检测结果"""
    detected: bool
    issues: list[LookaheadBiasIssue] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class SurvivorshipBiasResult:
    """幸存者偏差检测结果"""
    detected: bool
    delisted_stocks_used: list[str] = field(default_factory=list)
    delisted_count: int = 0
    impact_estimate: float = 0.0
    recommendation: str = ""


@dataclass
class DataSnoopingResult:
    """数据窥探偏差结果"""
    trials_count: int
    original_p_value: float
    adjusted_p_value: float
    adjustment_method: str
    still_significant: bool


class BiasDetectionService:
    """
    偏差检测服务

    检测回测中可能存在的各种偏差
    """

    # 常见的前视偏差字段模式
    LOOKAHEAD_PATTERNS = {
        "future": {
            "pattern": ["future", "next", "tomorrow", "forward"],
            "severity": "high",
            "description": "直接使用未来数据",
        },
        "target": {
            "pattern": ["target_return", "future_return", "forward_return"],
            "severity": "high",
            "description": "使用未来收益作为特征",
        },
        "announcement": {
            "pattern": ["earnings", "announcement", "report_date"],
            "severity": "medium",
            "description": "可能在公告日期前使用公告数据",
        },
        "index_change": {
            "pattern": ["index_addition", "index_removal", "rebalance"],
            "severity": "medium",
            "description": "可能提前知道指数成分变化",
        },
    }

    # 已知的已退市股票 (示例)
    KNOWN_DELISTED = {
        "LEHMAN": {"delisted_date": "2008-09-15", "reason": "破产"},
        "ENRON": {"delisted_date": "2001-12-02", "reason": "破产"},
        "WAMU": {"delisted_date": "2008-09-25", "reason": "破产"},
        "BEARS": {"delisted_date": "2008-03-16", "reason": "收购"},
        "MER": {"delisted_date": "2008-09-14", "reason": "收购"},
    }

    def detect_lookahead_bias(
        self,
        strategy_config: dict[str, Any],
        factor_expressions: list[str] | None = None,
        signal_rules: list[dict] | None = None
    ) -> LookaheadBiasResult:
        """
        检测前视偏差

        Args:
            strategy_config: 策略配置
            factor_expressions: 因子表达式列表
            signal_rules: 信号规则列表

        Returns:
            前视偏差检测结果
        """
        issues = []

        # 检查策略配置
        config_str = str(strategy_config).lower()
        for bias_type, info in self.LOOKAHEAD_PATTERNS.items():
            for pattern in info["pattern"]:
                if pattern in config_str:
                    issues.append(LookaheadBiasIssue(
                        field=pattern,
                        description=info["description"],
                        severity=info["severity"],
                        location="strategy_config",
                        suggestion=f"请检查是否使用了包含 '{pattern}' 的字段，确保只使用历史数据"
                    ))

        # 检查因子表达式
        if factor_expressions:
            for i, expr in enumerate(factor_expressions):
                expr_lower = expr.lower()
                for bias_type, info in self.LOOKAHEAD_PATTERNS.items():
                    for pattern in info["pattern"]:
                        if pattern in expr_lower:
                            issues.append(LookaheadBiasIssue(
                                field=pattern,
                                description=f"因子表达式 #{i+1}: {info['description']}",
                                severity=info["severity"],
                                location=f"factor_expression[{i}]",
                                suggestion=f"因子表达式可能使用了未来数据: {expr[:50]}..."
                            ))

        # 检查信号规则
        if signal_rules:
            for i, rule in enumerate(signal_rules):
                rule_str = str(rule).lower()
                for bias_type, info in self.LOOKAHEAD_PATTERNS.items():
                    for pattern in info["pattern"]:
                        if pattern in rule_str:
                            issues.append(LookaheadBiasIssue(
                                field=pattern,
                                description=f"信号规则 #{i+1}: {info['description']}",
                                severity=info["severity"],
                                location=f"signal_rule[{i}]",
                                suggestion="检查信号规则是否依赖未来信息"
                            ))

        # 计算风险得分
        risk_score = self._calculate_lookahead_risk_score(issues)

        return LookaheadBiasResult(
            detected=len(issues) > 0,
            issues=issues,
            risk_score=risk_score
        )

    def _calculate_lookahead_risk_score(self, issues: list[LookaheadBiasIssue]) -> float:
        """计算前视偏差风险得分"""
        if not issues:
            return 0.0

        severity_scores = {
            "high": 40,
            "medium": 20,
            "low": 10
        }

        total_score = sum(severity_scores.get(issue.severity, 10) for issue in issues)
        return min(100.0, total_score)

    def detect_survivorship_bias(
        self,
        stock_universe: list[str],
        start_date: date,
        end_date: date,
        delisted_stocks: dict[str, dict] | None = None
    ) -> SurvivorshipBiasResult:
        """
        检测幸存者偏差

        Args:
            stock_universe: 股票池
            start_date: 回测开始日期
            end_date: 回测结束日期
            delisted_stocks: 已退市股票信息

        Returns:
            幸存者偏差检测结果
        """
        if delisted_stocks is None:
            delisted_stocks = self.KNOWN_DELISTED

        # 检查股票池中是否应包含已退市股票
        delisted_in_universe = []
        for symbol in stock_universe:
            symbol_upper = symbol.upper()
            if symbol_upper in delisted_stocks:
                delisted_info = delisted_stocks[symbol_upper]
                delisted_date = delisted_info.get("delisted_date", "")
                # 如果回测期间股票退市，应该被包含
                if delisted_date and delisted_date >= str(start_date):
                    delisted_in_universe.append(symbol_upper)

        # 检查是否有应包含但未包含的退市股票
        missing_delisted = []
        for symbol, info in delisted_stocks.items():
            delisted_date = info.get("delisted_date", "")
            if (delisted_date and
                str(start_date) <= delisted_date <= str(end_date) and
                symbol not in stock_universe):
                missing_delisted.append(symbol)

        # 估计影响
        impact_estimate = 0.0
        if missing_delisted:
            # 粗略估计: 每个遗漏的退市股票可能导致约 0.5-1% 的收益高估
            impact_estimate = len(missing_delisted) * 0.8  # 百分比

        # 生成建议
        recommendation = ""
        if missing_delisted:
            recommendation = (
                f"检测到可能的幸存者偏差: 回测期间有 {len(missing_delisted)} 只股票退市 "
                f"({', '.join(missing_delisted[:5])}{'...' if len(missing_delisted) > 5 else ''})，"
                "但未包含在股票池中。建议使用 Point-in-Time 数据或包含历史成分股。"
            )
        elif delisted_in_universe:
            recommendation = (
                f"股票池中包含了 {len(delisted_in_universe)} 只已退市股票，"
                "这是正确的做法，有助于避免幸存者偏差。"
            )
        else:
            recommendation = "未检测到明显的幸存者偏差问题。"

        return SurvivorshipBiasResult(
            detected=len(missing_delisted) > 0,
            delisted_stocks_used=delisted_in_universe,
            delisted_count=len(missing_delisted),
            impact_estimate=impact_estimate,
            recommendation=recommendation
        )

    def detect_data_snooping_bias(
        self,
        trials_count: int,
        original_sharpe: float,
        sample_length: int = 252 * 5,
        alpha: float = 0.05,
        method: str = "bonferroni"
    ) -> DataSnoopingResult:
        """
        检测数据窥探偏差

        当测试了多个策略/参数后，需要调整统计显著性

        Args:
            trials_count: 测试的策略/参数组合数量
            original_sharpe: 最佳策略的夏普比率
            sample_length: 样本长度 (天)
            alpha: 原始显著性水平
            method: 调整方法 (bonferroni, holm, fdr)

        Returns:
            数据窥探偏差结果
        """
        if trials_count <= 1:
            return DataSnoopingResult(
                trials_count=1,
                original_p_value=0.05,
                adjusted_p_value=0.05,
                adjustment_method=method,
                still_significant=original_sharpe > 0
            )

        # 计算夏普比率的 p 值 (H0: SR = 0)
        sr_std = np.sqrt((1 + 0.5 * original_sharpe ** 2) / sample_length)
        z_score = original_sharpe / sr_std if sr_std > 0 else 0
        original_p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))  # 双边检验

        # 多重检验调整
        if method == "bonferroni":
            # Bonferroni 校正 (最保守)
            adjusted_alpha = alpha / trials_count
            adjusted_p_value = min(1.0, original_p_value * trials_count)

        elif method == "holm":
            # Holm-Bonferroni 方法 (略微宽松)
            # 简化实现: 假设这是最显著的结果
            adjusted_p_value = min(1.0, original_p_value * trials_count)

        elif method == "fdr":
            # False Discovery Rate (Benjamini-Hochberg)
            # 假设这是排名第一的结果
            adjusted_p_value = min(1.0, original_p_value * trials_count / 1)

        else:
            adjusted_p_value = original_p_value

        # 判断调整后是否仍显著
        still_significant = adjusted_p_value < alpha

        return DataSnoopingResult(
            trials_count=trials_count,
            original_p_value=original_p_value,
            adjusted_p_value=adjusted_p_value,
            adjustment_method=method,
            still_significant=still_significant
        )

    def run_comprehensive_detection(
        self,
        strategy_config: dict[str, Any],
        stock_universe: list[str],
        start_date: date,
        end_date: date,
        trials_count: int = 1,
        observed_sharpe: float = 1.0,
        detection_types: list[str] | None = None
    ) -> dict[str, Any]:
        """
        运行综合偏差检测

        Args:
            strategy_config: 策略配置
            stock_universe: 股票池
            start_date: 开始日期
            end_date: 结束日期
            trials_count: 测试次数
            observed_sharpe: 观察到的夏普
            detection_types: 要运行的检测类型

        Returns:
            综合检测结果
        """
        if detection_types is None:
            detection_types = ["lookahead", "survivorship", "snooping"]

        results = {}

        # 前视偏差检测
        if "lookahead" in detection_types:
            lookahead = self.detect_lookahead_bias(
                strategy_config,
                factor_expressions=strategy_config.get("factor_expressions", []),
                signal_rules=strategy_config.get("signal_rules", [])
            )
            results["lookahead_bias"] = {
                "detected": lookahead.detected,
                "issues": [
                    {
                        "field": issue.field,
                        "description": issue.description,
                        "severity": issue.severity,
                        "location": issue.location,
                        "suggestion": issue.suggestion
                    }
                    for issue in lookahead.issues
                ],
                "risk_score": lookahead.risk_score
            }

        # 幸存者偏差检测
        if "survivorship" in detection_types:
            survivorship = self.detect_survivorship_bias(
                stock_universe,
                start_date,
                end_date
            )
            results["survivorship_bias"] = {
                "detected": survivorship.detected,
                "delisted_stocks_used": survivorship.delisted_stocks_used,
                "delisted_count": survivorship.delisted_count,
                "impact_estimate": survivorship.impact_estimate,
                "recommendation": survivorship.recommendation
            }

        # 数据窥探偏差检测
        if "snooping" in detection_types:
            snooping = self.detect_data_snooping_bias(
                trials_count,
                observed_sharpe
            )
            results["data_snooping_bias"] = {
                "trials_count": snooping.trials_count,
                "original_p_value": snooping.original_p_value,
                "adjusted_p_value": snooping.adjusted_p_value,
                "adjustment_method": snooping.adjustment_method,
                "still_significant": snooping.still_significant
            }

        # 综合评估
        overall = self._generate_overall_assessment(results)
        results["overall_assessment"] = overall

        return results

    def _generate_overall_assessment(self, results: dict[str, Any]) -> dict[str, Any]:
        """生成综合偏差评估"""
        total_issues = 0
        critical_issues = 0
        recommendations = []

        # 前视偏差
        if "lookahead_bias" in results:
            lb = results["lookahead_bias"]
            issues = lb.get("issues", [])
            total_issues += len(issues)
            critical_issues += sum(1 for i in issues if i.get("severity") == "high")
            if lb.get("detected"):
                recommendations.append("检测到前视偏差风险，请仔细检查标记的字段")

        # 幸存者偏差
        if "survivorship_bias" in results:
            sb = results["survivorship_bias"]
            if sb.get("detected"):
                total_issues += 1
                critical_issues += 1 if sb.get("delisted_count", 0) > 3 else 0
                recommendations.append(sb.get("recommendation", ""))

        # 数据窥探
        if "data_snooping_bias" in results:
            ds = results["data_snooping_bias"]
            if not ds.get("still_significant"):
                total_issues += 1
                recommendations.append(
                    f"警告: 考虑 {ds.get('trials_count')} 次测试后，"
                    "统计显著性消失，结果可能是偶然"
                )

        # 确定风险等级
        if critical_issues >= 2 or total_issues >= 5:
            risk_level = "severe"
        elif critical_issues >= 1 or total_issues >= 3:
            risk_level = "moderate"
        elif total_issues >= 1:
            risk_level = "minor"
        else:
            risk_level = "clean"

        return {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "risk_level": risk_level,
            "recommendations": [r for r in recommendations if r]
        }
