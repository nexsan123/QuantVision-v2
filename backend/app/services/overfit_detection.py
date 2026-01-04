"""
Phase 9: 过拟合检测服务

实现多种过拟合检测方法:
- 参数敏感性分析
- 样本内外对比
- Deflated Sharpe Ratio (DSR)
- 夏普比率上限检验
"""

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import stats
import structlog

logger = structlog.get_logger()


@dataclass
class ParameterSensitivityResult:
    """参数敏感性分析结果"""
    parameter: str
    parameter_label: str
    sensitivity_score: float  # 0-1
    optimal_range: tuple[float, float]
    current_value: float
    curve: list[dict]  # [{param_value, sharpe, returns}]
    verdict: str  # stable, moderate, sensitive


@dataclass
class InOutSampleComparison:
    """样本内外对比"""
    in_sample_sharpe: float
    out_sample_sharpe: float
    in_sample_returns: float
    out_sample_returns: float
    stability_ratio: float
    verdict: str  # robust, moderate, likely_overfit


@dataclass
class DeflatedSharpeResult:
    """Deflated Sharpe Ratio 结果"""
    original_sharpe: float
    deflated_sharpe: float
    trials_count: int
    adjustment_factor: float
    p_value: float
    significant: bool


@dataclass
class SharpeUpperBoundResult:
    """夏普比率上限检验结果"""
    observed_sharpe: float
    theoretical_upper_bound: float
    exceeds_probability: float
    verdict: str  # acceptable, suspicious, likely_overfit


class OverfitDetectionService:
    """
    过拟合检测服务

    综合多种方法评估策略的过拟合风险
    """

    def __init__(self):
        self.parameter_labels = {
            "lookback_period": "回望周期",
            "holding_count": "持仓数量",
            "stop_loss": "止损阈值",
            "rebalance_freq": "调仓频率",
            "factor_weight": "因子权重",
        }

    def analyze_parameter_sensitivity(
        self,
        strategy_config: dict[str, Any],
        parameters: list[dict],
        run_backtest_fn: callable = None
    ) -> list[ParameterSensitivityResult]:
        """
        参数敏感性分析

        Args:
            strategy_config: 策略配置
            parameters: 要分析的参数列表 [{name, range, steps}]
            run_backtest_fn: 回测函数

        Returns:
            参数敏感性结果列表
        """
        results = []

        for param in parameters:
            name = param["name"]
            param_range = param["range"]
            steps = param.get("steps", 10)

            logger.info(f"Analyzing sensitivity for {name}", range=param_range, steps=steps)

            # 生成参数值序列
            values = np.linspace(param_range[0], param_range[1], steps)
            curve = []

            for value in values:
                if run_backtest_fn:
                    # 使用真实回测
                    test_config = strategy_config.copy()
                    test_config[name] = value
                    metrics = run_backtest_fn(test_config)
                    sharpe = metrics.get("sharpe_ratio", 0)
                    returns = metrics.get("annual_return", 0)
                else:
                    # 模拟数据
                    sharpe, returns = self._simulate_sensitivity(name, value, param_range)

                curve.append({
                    "param_value": float(value),
                    "sharpe": float(sharpe),
                    "returns": float(returns)
                })

            # 计算敏感度得分
            sharpes = [c["sharpe"] for c in curve]
            sensitivity_score = self._calculate_sensitivity_score(sharpes)

            # 找到最优范围
            optimal_range = self._find_optimal_range(curve)

            # 当前值
            current_value = strategy_config.get(name, (param_range[0] + param_range[1]) / 2)

            # 评估
            if sensitivity_score < 0.3:
                verdict = "stable"
            elif sensitivity_score < 0.6:
                verdict = "moderate"
            else:
                verdict = "sensitive"

            results.append(ParameterSensitivityResult(
                parameter=name,
                parameter_label=self.parameter_labels.get(name, name),
                sensitivity_score=sensitivity_score,
                optimal_range=optimal_range,
                current_value=current_value,
                curve=curve,
                verdict=verdict
            ))

        return results

    def _simulate_sensitivity(
        self,
        param_name: str,
        value: float,
        param_range: tuple
    ) -> tuple[float, float]:
        """模拟参数敏感性数据"""
        # 生成一个合理的曲线，中间值通常较优
        mid = (param_range[0] + param_range[1]) / 2
        normalized = (value - mid) / (param_range[1] - param_range[0])

        # 高斯型响应曲线
        np.random.seed(int(value * 1000) % 10000)
        base_sharpe = 1.2 * math.exp(-2 * normalized ** 2)
        noise = np.random.normal(0, 0.1)
        sharpe = max(0, base_sharpe + noise)

        returns = sharpe * 0.12 + np.random.normal(0, 0.02)

        return sharpe, returns

    def _calculate_sensitivity_score(self, sharpes: list[float]) -> float:
        """计算敏感度得分 (0-1)"""
        if len(sharpes) < 2:
            return 0.5

        sharpe_array = np.array(sharpes)
        mean_sharpe = np.mean(sharpe_array)
        std_sharpe = np.std(sharpe_array)

        if mean_sharpe == 0:
            return 1.0

        # 变异系数作为敏感度指标
        cv = std_sharpe / abs(mean_sharpe) if mean_sharpe != 0 else 1.0

        # 归一化到 0-1
        score = min(1.0, cv / 2.0)
        return float(score)

    def _find_optimal_range(self, curve: list[dict]) -> tuple[float, float]:
        """找到最优参数范围"""
        if not curve:
            return (0, 0)

        # 找到夏普最高的点
        max_sharpe = max(c["sharpe"] for c in curve)
        threshold = max_sharpe * 0.9  # 90% 阈值

        # 找到所有满足阈值的参数值
        valid_values = [c["param_value"] for c in curve if c["sharpe"] >= threshold]

        if not valid_values:
            return (curve[0]["param_value"], curve[-1]["param_value"])

        return (min(valid_values), max(valid_values))

    def compare_in_out_sample(
        self,
        in_sample_metrics: dict,
        out_sample_metrics: dict
    ) -> InOutSampleComparison:
        """
        样本内外对比分析
        """
        is_sharpe = in_sample_metrics.get("sharpe_ratio", 0)
        oos_sharpe = out_sample_metrics.get("sharpe_ratio", 0)
        is_returns = in_sample_metrics.get("annual_return", 0)
        oos_returns = out_sample_metrics.get("annual_return", 0)

        # 计算稳定性比率
        stability_ratio = oos_sharpe / is_sharpe if is_sharpe > 0 else 0

        # 评估
        if stability_ratio >= 0.7:
            verdict = "robust"
        elif stability_ratio >= 0.5:
            verdict = "moderate"
        else:
            verdict = "likely_overfit"

        return InOutSampleComparison(
            in_sample_sharpe=is_sharpe,
            out_sample_sharpe=oos_sharpe,
            in_sample_returns=is_returns,
            out_sample_returns=oos_returns,
            stability_ratio=stability_ratio,
            verdict=verdict
        )

    def calculate_deflated_sharpe_ratio(
        self,
        observed_sharpe: float,
        trials_count: int,
        sample_length: int = 252,
        skewness: float = 0.0,
        kurtosis: float = 3.0
    ) -> DeflatedSharpeResult:
        """
        计算 Deflated Sharpe Ratio

        调整多重检验偏差，反映真实的夏普比率

        Args:
            observed_sharpe: 观察到的夏普比率
            trials_count: 测试/优化的次数
            sample_length: 样本长度 (天)
            skewness: 收益偏度
            kurtosis: 收益峰度
        """
        if trials_count <= 1:
            return DeflatedSharpeResult(
                original_sharpe=observed_sharpe,
                deflated_sharpe=observed_sharpe,
                trials_count=trials_count,
                adjustment_factor=1.0,
                p_value=0.5,
                significant=observed_sharpe > 0
            )

        # 计算夏普比率的标准误
        sr_std = math.sqrt(
            (1 + 0.5 * observed_sharpe ** 2 -
             skewness * observed_sharpe +
             (kurtosis - 3) / 4 * observed_sharpe ** 2) / sample_length
        )

        # 预期最大夏普 (基于多重检验)
        expected_max_sr = sr_std * (
            (1 - 1.0 / (2 * math.log(trials_count))) * math.sqrt(2 * math.log(trials_count)) +
            1.0 / (2 * math.sqrt(math.pi * math.log(trials_count)))
        )

        # 调整系数
        adjustment_factor = observed_sharpe / expected_max_sr if expected_max_sr > 0 else 0

        # Deflated Sharpe Ratio
        deflated_sr = max(0, observed_sharpe - expected_max_sr)

        # 计算 p 值 (使用正态分布近似)
        z_score = deflated_sr / sr_std if sr_std > 0 else 0
        p_value = 1 - stats.norm.cdf(z_score)

        # 是否显著 (5% 水平)
        significant = p_value < 0.05 and deflated_sr > 0

        return DeflatedSharpeResult(
            original_sharpe=observed_sharpe,
            deflated_sharpe=deflated_sr,
            trials_count=trials_count,
            adjustment_factor=adjustment_factor,
            p_value=p_value,
            significant=significant
        )

    def check_sharpe_upper_bound(
        self,
        observed_sharpe: float,
        sample_years: float = 5.0,
        strategy_complexity: str = "moderate"
    ) -> SharpeUpperBoundResult:
        """
        夏普比率上限检验

        基于经验法则，高夏普比率可能意味着过拟合

        Args:
            observed_sharpe: 观察到的夏普比率
            sample_years: 样本年数
            strategy_complexity: 策略复杂度 (simple, moderate, complex)
        """
        # 根据复杂度设置理论上限
        complexity_bounds = {
            "simple": 2.5,
            "moderate": 2.0,
            "complex": 1.5,
        }
        base_upper_bound = complexity_bounds.get(strategy_complexity, 2.0)

        # 样本长度调整 (样本越短，越容易有高夏普)
        sample_adjustment = math.sqrt(5.0 / sample_years) if sample_years > 0 else 1.5
        theoretical_upper_bound = base_upper_bound * sample_adjustment

        # 计算超过概率
        if observed_sharpe <= theoretical_upper_bound * 0.8:
            exceeds_probability = 0.1
        elif observed_sharpe <= theoretical_upper_bound:
            exceeds_probability = 0.3
        elif observed_sharpe <= theoretical_upper_bound * 1.5:
            exceeds_probability = 0.6
        else:
            exceeds_probability = 0.9

        # 评估
        if exceeds_probability < 0.3:
            verdict = "acceptable"
        elif exceeds_probability < 0.6:
            verdict = "suspicious"
        else:
            verdict = "likely_overfit"

        return SharpeUpperBoundResult(
            observed_sharpe=observed_sharpe,
            theoretical_upper_bound=theoretical_upper_bound,
            exceeds_probability=exceeds_probability,
            verdict=verdict
        )

    def run_comprehensive_detection(
        self,
        strategy_config: dict[str, Any],
        in_sample_metrics: dict,
        out_sample_metrics: dict,
        trials_count: int = 1,
        sample_years: float = 5.0,
        parameters_to_analyze: list[dict] | None = None
    ) -> dict[str, Any]:
        """
        运行综合过拟合检测

        Returns:
            综合检测结果
        """
        results = {}

        # 1. 参数敏感性分析
        if parameters_to_analyze:
            sensitivity_results = self.analyze_parameter_sensitivity(
                strategy_config,
                parameters_to_analyze
            )
            results["parameter_sensitivity"] = [
                {
                    "parameter": r.parameter,
                    "parameter_label": r.parameter_label,
                    "sensitivity_score": r.sensitivity_score,
                    "optimal_range": list(r.optimal_range),
                    "current_value": r.current_value,
                    "curve": r.curve,
                    "verdict": r.verdict
                }
                for r in sensitivity_results
            ]

        # 2. 样本内外对比
        comparison = self.compare_in_out_sample(in_sample_metrics, out_sample_metrics)
        results["in_out_sample_comparison"] = {
            "in_sample_sharpe": comparison.in_sample_sharpe,
            "out_sample_sharpe": comparison.out_sample_sharpe,
            "in_sample_returns": comparison.in_sample_returns,
            "out_sample_returns": comparison.out_sample_returns,
            "stability_ratio": comparison.stability_ratio,
            "verdict": comparison.verdict
        }

        # 3. Deflated Sharpe Ratio
        observed_sharpe = in_sample_metrics.get("sharpe_ratio", 0)
        dsr = self.calculate_deflated_sharpe_ratio(
            observed_sharpe,
            trials_count
        )
        results["deflated_sharpe_ratio"] = {
            "original_sharpe": dsr.original_sharpe,
            "deflated_sharpe": dsr.deflated_sharpe,
            "trials_count": dsr.trials_count,
            "adjustment_factor": dsr.adjustment_factor,
            "p_value": dsr.p_value,
            "significant": dsr.significant
        }

        # 4. 夏普上限检验
        sharpe_bound = self.check_sharpe_upper_bound(
            observed_sharpe,
            sample_years
        )
        results["sharpe_upper_bound"] = {
            "observed_sharpe": sharpe_bound.observed_sharpe,
            "theoretical_upper_bound": sharpe_bound.theoretical_upper_bound,
            "exceeds_probability": sharpe_bound.exceeds_probability,
            "verdict": sharpe_bound.verdict
        }

        # 5. 综合评估
        overall = self._generate_overall_assessment(
            comparison,
            dsr,
            sharpe_bound,
            results.get("parameter_sensitivity", [])
        )
        results["overall_assessment"] = overall

        return results

    def _generate_overall_assessment(
        self,
        comparison: InOutSampleComparison,
        dsr: DeflatedSharpeResult,
        sharpe_bound: SharpeUpperBoundResult,
        sensitivity_results: list[dict]
    ) -> dict[str, Any]:
        """生成综合评估"""
        # 计算过拟合概率
        risk_scores = []

        # 稳定性比率贡献
        if comparison.stability_ratio >= 0.7:
            risk_scores.append(10)
        elif comparison.stability_ratio >= 0.5:
            risk_scores.append(40)
        else:
            risk_scores.append(80)

        # DSR 贡献
        if dsr.significant:
            risk_scores.append(20)
        else:
            risk_scores.append(60)

        # 夏普上限贡献
        if sharpe_bound.verdict == "acceptable":
            risk_scores.append(15)
        elif sharpe_bound.verdict == "suspicious":
            risk_scores.append(50)
        else:
            risk_scores.append(85)

        # 参数敏感性贡献
        if sensitivity_results:
            sensitive_count = sum(1 for s in sensitivity_results if s.get("verdict") == "sensitive")
            sensitivity_risk = sensitive_count / len(sensitivity_results) * 100
            risk_scores.append(sensitivity_risk)

        # 加权平均
        overfit_probability = np.mean(risk_scores)

        # 置信度
        if len(risk_scores) >= 4:
            confidence = "high"
        elif len(risk_scores) >= 2:
            confidence = "medium"
        else:
            confidence = "low"

        # 风险等级
        if overfit_probability < 25:
            risk_level = "low"
        elif overfit_probability < 50:
            risk_level = "moderate"
        elif overfit_probability < 75:
            risk_level = "high"
        else:
            risk_level = "critical"

        # 建议
        recommendations = []
        if comparison.verdict == "likely_overfit":
            recommendations.append("样本外表现显著低于样本内，建议简化策略")
        if not dsr.significant:
            recommendations.append("调整多重检验后夏普不显著，谨慎解读回测结果")
        if sharpe_bound.verdict != "acceptable":
            recommendations.append(f"夏普比率 {sharpe_bound.observed_sharpe:.2f} 可能过高，警惕过拟合")

        sensitive_params = [s["parameter_label"] for s in sensitivity_results if s.get("verdict") == "sensitive"]
        if sensitive_params:
            recommendations.append(f"参数 {', '.join(sensitive_params)} 敏感度较高，建议收窄范围")

        # 说明
        explanation = f"综合 {len(risk_scores)} 项检测指标，过拟合概率约 {overfit_probability:.0f}%。"
        if risk_level in ["high", "critical"]:
            explanation += " 建议重新审视策略设计，避免数据窥探。"
        elif risk_level == "moderate":
            explanation += " 建议增加样本外验证并简化参数。"
        else:
            explanation += " 策略表现相对稳健。"

        return {
            "overfit_probability": float(overfit_probability),
            "confidence": confidence,
            "risk_level": risk_level,
            "recommendations": recommendations,
            "explanation": explanation
        }
