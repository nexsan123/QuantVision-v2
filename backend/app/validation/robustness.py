"""
稳健性检验

提供:
- 参数稳健性分析
- 时间稳健性分析
- 市场环境稳健性
- Monte Carlo 模拟
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


class RobustnessTestType(str, Enum):
    """稳健性测试类型"""
    PARAMETER = "parameter"           # 参数敏感性
    TEMPORAL = "temporal"             # 时间稳定性
    MARKET_REGIME = "market_regime"   # 市场环境
    MONTE_CARLO = "monte_carlo"       # Monte Carlo
    BOOTSTRAP = "bootstrap"           # Bootstrap


@dataclass
class RobustnessMetric:
    """稳健性指标"""
    name: str
    value: float
    is_robust: bool
    threshold: float
    description: str = ""


@dataclass
class RobustnessReport:
    """稳健性检验报告"""
    overall_score: float = 0.0          # 综合稳健性分数 (0-1)
    is_robust: bool = False
    metrics: list[RobustnessMetric] = field(default_factory=list)
    parameter_sensitivity: dict[str, float] = field(default_factory=dict)
    temporal_stability: dict[str, float] = field(default_factory=dict)
    regime_performance: dict[str, dict[str, float]] = field(default_factory=dict)
    monte_carlo_results: dict[str, float] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)


class RobustnessTester:
    """
    稳健性测试器

    执行多维度稳健性检验:
    1. 参数稳健性: 参数小幅变化是否导致大幅性能变化
    2. 时间稳健性: 不同时间段表现是否一致
    3. 市场环境稳健性: 不同市场环境表现
    4. Monte Carlo: 随机模拟统计显著性
    """

    def __init__(
        self,
        n_simulations: int = 1000,
        confidence_level: float = 0.95,
    ):
        """
        Args:
            n_simulations: Monte Carlo 模拟次数
            confidence_level: 置信水平
        """
        self.n_simulations = n_simulations
        self.confidence_level = confidence_level
        self.report = RobustnessReport()

    def run_all_tests(
        self,
        returns: pd.Series,
        strategy_func: Callable | None = None,
        params: dict[str, Any] | None = None,
        market_data: pd.DataFrame | None = None,
    ) -> RobustnessReport:
        """
        执行所有稳健性测试

        Args:
            returns: 策略收益序列
            strategy_func: 策略函数 (可选，用于参数敏感性)
            params: 策略参数
            market_data: 市场数据 (用于市场环境分析)

        Returns:
            稳健性报告
        """
        self.report = RobustnessReport()

        # 1. 时间稳健性
        self._test_temporal_stability(returns)

        # 2. 参数稳健性 (如果提供策略函数)
        if strategy_func and params:
            self._test_parameter_sensitivity(strategy_func, params, returns)

        # 3. 市场环境稳健性
        if market_data is not None:
            self._test_market_regime(returns, market_data)

        # 4. Monte Carlo
        self._test_monte_carlo(returns)

        # 5. Bootstrap 置信区间
        self._test_bootstrap(returns)

        # 计算综合分数
        self._calculate_overall_score()

        logger.info(
            "稳健性检验完成",
            overall_score=f"{self.report.overall_score:.2f}",
            is_robust=self.report.is_robust,
            n_metrics=len(self.report.metrics),
        )

        return self.report

    def _test_temporal_stability(self, returns: pd.Series) -> None:
        """测试时间稳定性"""
        n = len(returns)
        if n < 100:
            return

        # 将数据分成多个时期
        n_periods = min(5, n // 50)
        period_size = n // n_periods

        period_sharpes = []
        period_returns = []

        for i in range(n_periods):
            start = i * period_size
            end = start + period_size if i < n_periods - 1 else n
            period_data = returns.iloc[start:end]

            sharpe = self._calculate_sharpe(period_data)
            total_return = period_data.sum()

            period_sharpes.append(sharpe)
            period_returns.append(total_return)

            self.report.temporal_stability[f"period_{i+1}_sharpe"] = sharpe
            self.report.temporal_stability[f"period_{i+1}_return"] = float(total_return)

        # 计算稳定性指标
        sharpe_cv = np.std(period_sharpes) / abs(np.mean(period_sharpes)) if np.mean(period_sharpes) != 0 else float("inf")
        n_positive = sum(1 for s in period_sharpes if s > 0)

        self.report.temporal_stability["sharpe_cv"] = float(sharpe_cv)
        self.report.temporal_stability["positive_periods_ratio"] = n_positive / n_periods

        # 添加指标
        is_stable = sharpe_cv < 1.0 and n_positive >= n_periods * 0.6

        self.report.metrics.append(
            RobustnessMetric(
                name="temporal_stability",
                value=float(1 - min(sharpe_cv, 2) / 2),  # 转换为 0-1 分数
                is_robust=is_stable,
                threshold=0.5,
                description=f"夏普比率变异系数: {sharpe_cv:.2f}, {n_positive}/{n_periods} 期为正",
            )
        )

    def _test_parameter_sensitivity(
        self,
        strategy_func: Callable,
        params: dict[str, Any],
        base_returns: pd.Series,
    ) -> None:
        """测试参数敏感性"""
        base_sharpe = self._calculate_sharpe(base_returns)
        sensitivities = {}

        for param_name, param_value in params.items():
            if not isinstance(param_value, (int, float)):
                continue

            # 测试 ±10% 变化
            variations = []
            for pct in [-0.1, 0.1]:
                new_value = param_value * (1 + pct)
                new_params = params.copy()
                new_params[param_name] = new_value

                try:
                    new_returns = strategy_func(**new_params)
                    new_sharpe = self._calculate_sharpe(new_returns)
                    if base_sharpe != 0:
                        change = abs(new_sharpe - base_sharpe) / abs(base_sharpe)
                        variations.append(change)
                except Exception:
                    pass

            if variations:
                sensitivity = np.mean(variations)
                sensitivities[param_name] = float(sensitivity)

        self.report.parameter_sensitivity = sensitivities

        if sensitivities:
            avg_sensitivity = np.mean(list(sensitivities.values()))
            max_sensitivity = max(sensitivities.values())

            is_robust = avg_sensitivity < 0.3 and max_sensitivity < 0.5

            self.report.metrics.append(
                RobustnessMetric(
                    name="parameter_sensitivity",
                    value=float(1 - min(avg_sensitivity, 1)),
                    is_robust=is_robust,
                    threshold=0.7,
                    description=f"平均敏感性: {avg_sensitivity:.2%}, 最大: {max_sensitivity:.2%}",
                )
            )

    def _test_market_regime(
        self,
        returns: pd.Series,
        market_data: pd.DataFrame,
    ) -> None:
        """测试市场环境稳健性"""
        # 使用市场收益识别环境
        if "market_return" in market_data.columns:
            market_returns = market_data["market_return"]
        elif "close" in market_data.columns:
            market_returns = market_data["close"].pct_change()
        else:
            return

        # 对齐数据
        common_idx = returns.index.intersection(market_returns.index)
        if len(common_idx) < 50:
            return

        aligned_returns = returns.loc[common_idx]
        aligned_market = market_returns.loc[common_idx]

        # 识别市场环境
        # 牛市: 滚动收益 > 0, 熊市: < 0, 震荡: 介于两者
        rolling_market = aligned_market.rolling(60).mean()

        bull_mask = rolling_market > 0.0005  # 约年化 12%
        bear_mask = rolling_market < -0.0005
        sideways_mask = ~bull_mask & ~bear_mask

        regimes = {
            "bull": aligned_returns[bull_mask],
            "bear": aligned_returns[bear_mask],
            "sideways": aligned_returns[sideways_mask],
        }

        for regime_name, regime_returns in regimes.items():
            if len(regime_returns) > 20:
                sharpe = self._calculate_sharpe(regime_returns)
                total_ret = regime_returns.sum()
                self.report.regime_performance[regime_name] = {
                    "sharpe": float(sharpe),
                    "return": float(total_ret),
                    "n_days": len(regime_returns),
                }

        # 评估环境稳健性
        regime_sharpes = [
            r["sharpe"] for r in self.report.regime_performance.values()
            if r.get("n_days", 0) > 20
        ]

        if len(regime_sharpes) >= 2:
            min_sharpe = min(regime_sharpes)
            max_sharpe = max(regime_sharpes)
            regime_spread = max_sharpe - min_sharpe if max_sharpe > 0 else float("inf")

            is_robust = min_sharpe > 0 or regime_spread < 1.5

            self.report.metrics.append(
                RobustnessMetric(
                    name="market_regime",
                    value=float(min(1, max(0, 1 - regime_spread / 3))),
                    is_robust=is_robust,
                    threshold=0.5,
                    description=f"环境夏普范围: {min_sharpe:.2f} - {max_sharpe:.2f}",
                )
            )

    def _test_monte_carlo(self, returns: pd.Series) -> None:
        """Monte Carlo 模拟"""
        n = len(returns)
        if n < 50:
            return

        actual_sharpe = self._calculate_sharpe(returns)
        actual_return = returns.sum()

        # 生成随机策略收益
        random_sharpes = []
        random_returns = []

        for _ in range(self.n_simulations):
            # 随机打乱收益
            shuffled = np.random.permutation(returns.values)
            shuffled_series = pd.Series(shuffled, index=returns.index)

            random_sharpes.append(self._calculate_sharpe(shuffled_series))
            random_returns.append(shuffled_series.sum())

        # 计算 p 值
        p_sharpe = (np.array(random_sharpes) >= actual_sharpe).mean()
        p_return = (np.array(random_returns) >= actual_return).mean()

        self.report.monte_carlo_results = {
            "actual_sharpe": float(actual_sharpe),
            "random_mean_sharpe": float(np.mean(random_sharpes)),
            "p_value_sharpe": float(p_sharpe),
            "p_value_return": float(p_return),
            "percentile_sharpe": float(1 - p_sharpe) * 100,
        }

        is_significant = p_sharpe < (1 - self.confidence_level)

        self.report.metrics.append(
            RobustnessMetric(
                name="monte_carlo",
                value=float(1 - p_sharpe),
                is_robust=is_significant,
                threshold=self.confidence_level,
                description=f"夏普比率 p-value: {p_sharpe:.4f}",
            )
        )

    def _test_bootstrap(self, returns: pd.Series) -> None:
        """Bootstrap 置信区间"""
        n = len(returns)
        if n < 50:
            return

        bootstrap_sharpes = []

        for _ in range(self.n_simulations):
            # 有放回抽样
            sample_idx = np.random.choice(n, size=n, replace=True)
            sample = returns.iloc[sample_idx]
            bootstrap_sharpes.append(self._calculate_sharpe(sample))

        # 计算置信区间
        alpha = 1 - self.confidence_level
        lower = np.percentile(bootstrap_sharpes, alpha / 2 * 100)
        upper = np.percentile(bootstrap_sharpes, (1 - alpha / 2) * 100)
        median = np.median(bootstrap_sharpes)

        self.report.monte_carlo_results["bootstrap_lower"] = float(lower)
        self.report.monte_carlo_results["bootstrap_upper"] = float(upper)
        self.report.monte_carlo_results["bootstrap_median"] = float(median)

        # 如果置信区间下界 > 0，则稳健
        is_robust = lower > 0

        self.report.metrics.append(
            RobustnessMetric(
                name="bootstrap_ci",
                value=float(lower) if lower > 0 else 0.0,
                is_robust=is_robust,
                threshold=0.0,
                description=f"{self.confidence_level:.0%} CI: [{lower:.2f}, {upper:.2f}]",
            )
        )

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """计算夏普比率"""
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        return float(returns.mean() / returns.std() * np.sqrt(252))

    def _calculate_overall_score(self) -> None:
        """计算综合稳健性分数"""
        if not self.report.metrics:
            return

        # 加权平均
        weights = {
            "temporal_stability": 0.25,
            "parameter_sensitivity": 0.20,
            "market_regime": 0.20,
            "monte_carlo": 0.20,
            "bootstrap_ci": 0.15,
        }

        total_score = 0.0
        total_weight = 0.0
        robust_count = 0

        for metric in self.report.metrics:
            weight = weights.get(metric.name, 0.1)
            total_score += metric.value * weight
            total_weight += weight
            if metric.is_robust:
                robust_count += 1

        if total_weight > 0:
            self.report.overall_score = total_score / total_weight

        # 如果大多数指标通过，则整体稳健
        self.report.is_robust = robust_count >= len(self.report.metrics) * 0.6

        # 生成建议
        for metric in self.report.metrics:
            if not metric.is_robust:
                if metric.name == "temporal_stability":
                    self.report.recommendations.append("策略表现随时间波动较大，建议检查是否存在过拟合")
                elif metric.name == "parameter_sensitivity":
                    self.report.recommendations.append("策略对参数敏感，建议使用更稳健的参数设置")
                elif metric.name == "market_regime":
                    self.report.recommendations.append("策略在某些市场环境下表现不佳，考虑增加环境自适应")
                elif metric.name == "monte_carlo":
                    self.report.recommendations.append("策略收益可能来自随机性，统计显著性不足")
                elif metric.name == "bootstrap_ci":
                    self.report.recommendations.append("夏普比率置信区间包含负值，风险较高")


def stress_test(
    returns: pd.Series,
    scenarios: dict[str, dict[str, float]],
) -> dict[str, dict[str, float]]:
    """
    压力测试

    Args:
        returns: 策略收益
        scenarios: 压力情景 {"scenario_name": {"return_shock": -0.1, "vol_shock": 2.0}}

    Returns:
        各情景下的表现
    """
    results = {}
    base_mean = returns.mean()

    for scenario_name, shocks in scenarios.items():
        return_shock = shocks.get("return_shock", 0)
        vol_shock = shocks.get("vol_shock", 1)

        # 应用冲击
        stressed_returns = (returns - base_mean) * vol_shock + base_mean + return_shock

        # 计算指标
        stressed_sharpe = stressed_returns.mean() / stressed_returns.std() * np.sqrt(252) if stressed_returns.std() > 0 else 0
        max_dd = (stressed_returns.cumsum().cummax() - stressed_returns.cumsum()).max()

        results[scenario_name] = {
            "sharpe": float(stressed_sharpe),
            "total_return": float(stressed_returns.sum()),
            "max_drawdown": float(max_dd),
            "volatility": float(stressed_returns.std() * np.sqrt(252)),
        }

    return results
