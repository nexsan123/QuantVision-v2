"""
过拟合检测器

检测策略可能存在的过拟合问题:
- 样本内外表现差异
- 参数敏感性
- 复杂度过高
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy import stats

logger = structlog.get_logger()


class OverfitIndicator(str, Enum):
    """过拟合指标"""
    IS_OOS_RATIO = "is_oos_ratio"           # 样本内/外收益比
    PARAMETER_SENSITIVITY = "param_sens"    # 参数敏感性
    COMPLEXITY_RATIO = "complexity"         # 复杂度比率
    SHARPE_DECAY = "sharpe_decay"           # 夏普衰减
    RETURN_AUTOCORR = "return_autocorr"     # 收益自相关
    STABILITY_SCORE = "stability"           # 稳定性分数


@dataclass
class OverfitWarning:
    """过拟合警告"""
    indicator: OverfitIndicator
    severity: str                           # "low", "medium", "high"
    description: str
    value: float
    threshold: float
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class OverfitReport:
    """过拟合检测报告"""
    overfit_probability: float = 0.0        # 过拟合概率 (0-1)
    risk_level: str = "low"                 # "low", "medium", "high"
    warnings: list[OverfitWarning] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    def add_warning(self, warning: OverfitWarning) -> None:
        """添加警告"""
        self.warnings.append(warning)

        # 更新风险级别
        if warning.severity == "high":
            self.risk_level = "high"
        elif warning.severity == "medium" and self.risk_level != "high":
            self.risk_level = "medium"


class OverfittingDetector:
    """
    过拟合检测器

    使用多种方法检测过拟合:
    1. 样本内/外表现比较
    2. 参数敏感性分析
    3. 策略复杂度评估
    4. 时间稳定性检验
    """

    def __init__(
        self,
        oos_ratio: float = 0.3,
        n_bootstrap: int = 100,
    ):
        """
        Args:
            oos_ratio: 样本外数据比例
            n_bootstrap: Bootstrap 采样次数
        """
        self.oos_ratio = oos_ratio
        self.n_bootstrap = n_bootstrap
        self.report = OverfitReport()

    def detect(
        self,
        returns: pd.Series,
        signals: pd.DataFrame | None = None,
        strategy_params: dict[str, Any] | None = None,
        param_variations: list[dict[str, Any]] | None = None,
        variation_returns: list[pd.Series] | None = None,
    ) -> OverfitReport:
        """
        执行过拟合检测

        Args:
            returns: 策略收益序列
            signals: 交易信号
            strategy_params: 策略参数
            param_variations: 参数变化列表
            variation_returns: 参数变化后的收益列表

        Returns:
            过拟合检测报告
        """
        self.report = OverfitReport()

        if len(returns) < 100:
            logger.warning("收益序列过短，无法进行可靠的过拟合检测")
            return self.report

        # 1. 样本内/外比较
        self._check_is_oos_performance(returns)

        # 2. 夏普比率稳定性
        self._check_sharpe_stability(returns)

        # 3. 收益自相关性
        self._check_return_autocorrelation(returns)

        # 4. 参数敏感性
        if param_variations and variation_returns:
            self._check_parameter_sensitivity(returns, variation_returns)

        # 5. 计算综合过拟合概率
        self._calculate_overfit_probability()

        logger.info(
            "过拟合检测完成",
            probability=f"{self.report.overfit_probability:.1%}",
            risk_level=self.report.risk_level,
            warnings=len(self.report.warnings),
        )

        return self.report

    def _check_is_oos_performance(self, returns: pd.Series) -> None:
        """检查样本内外表现差异"""
        n = len(returns)
        split_idx = int(n * (1 - self.oos_ratio))

        is_returns = returns.iloc[:split_idx]
        oos_returns = returns.iloc[split_idx:]

        # 计算夏普比率
        is_sharpe = self._calculate_sharpe(is_returns)
        oos_sharpe = self._calculate_sharpe(oos_returns)

        self.report.metrics["is_sharpe"] = is_sharpe
        self.report.metrics["oos_sharpe"] = oos_sharpe

        # 计算比率
        if oos_sharpe != 0:
            ratio = is_sharpe / oos_sharpe
        else:
            ratio = float("inf") if is_sharpe > 0 else 0.0

        self.report.metrics["is_oos_ratio"] = float(ratio)

        # 判断是否过拟合
        if ratio > 2.0:
            self.report.add_warning(
                OverfitWarning(
                    indicator=OverfitIndicator.IS_OOS_RATIO,
                    severity="high" if ratio > 3.0 else "medium",
                    description=f"样本内夏普 ({is_sharpe:.2f}) 远高于样本外 ({oos_sharpe:.2f})",
                    value=float(ratio),
                    threshold=2.0,
                    evidence={
                        "is_sharpe": float(is_sharpe),
                        "oos_sharpe": float(oos_sharpe),
                        "is_return": float(is_returns.sum()),
                        "oos_return": float(oos_returns.sum()),
                    },
                )
            )

        # 检查收益是否有显著下降
        is_annual = is_returns.mean() * 252
        oos_annual = oos_returns.mean() * 252

        if is_annual > 0 and oos_annual < is_annual * 0.5:
            self.report.add_warning(
                OverfitWarning(
                    indicator=OverfitIndicator.IS_OOS_RATIO,
                    severity="medium",
                    description=f"样本外年化收益 ({oos_annual:.1%}) 低于样本内 ({is_annual:.1%}) 的一半",
                    value=float(oos_annual / is_annual) if is_annual != 0 else 0,
                    threshold=0.5,
                )
            )

    def _check_sharpe_stability(self, returns: pd.Series) -> None:
        """检查滚动夏普比率稳定性"""
        # 计算滚动夏普 (60天窗口)
        window = min(60, len(returns) // 4)
        if window < 20:
            return

        rolling_mean = returns.rolling(window).mean()
        rolling_std = returns.rolling(window).std()
        rolling_sharpe = (rolling_mean / rolling_std * np.sqrt(252)).dropna()

        if len(rolling_sharpe) < 10:
            return

        # 计算夏普比率的变异系数
        sharpe_cv = rolling_sharpe.std() / abs(rolling_sharpe.mean()) if rolling_sharpe.mean() != 0 else float("inf")
        self.report.metrics["sharpe_cv"] = float(sharpe_cv)

        # 计算夏普衰减 (前半段 vs 后半段)
        mid = len(rolling_sharpe) // 2
        first_half_sharpe = rolling_sharpe.iloc[:mid].mean()
        second_half_sharpe = rolling_sharpe.iloc[mid:].mean()

        if first_half_sharpe > 0:
            decay = 1 - second_half_sharpe / first_half_sharpe
            self.report.metrics["sharpe_decay"] = float(decay)

            if decay > 0.5:
                self.report.add_warning(
                    OverfitWarning(
                        indicator=OverfitIndicator.SHARPE_DECAY,
                        severity="high" if decay > 0.7 else "medium",
                        description=f"夏普比率在后期下降了 {decay:.0%}",
                        value=float(decay),
                        threshold=0.5,
                        evidence={
                            "first_half_sharpe": float(first_half_sharpe),
                            "second_half_sharpe": float(second_half_sharpe),
                        },
                    )
                )

        # 高变异系数表明不稳定
        if sharpe_cv > 1.5:
            self.report.add_warning(
                OverfitWarning(
                    indicator=OverfitIndicator.STABILITY_SCORE,
                    severity="medium",
                    description=f"滚动夏普比率变异系数过高 ({sharpe_cv:.2f})",
                    value=float(sharpe_cv),
                    threshold=1.5,
                )
            )

    def _check_return_autocorrelation(self, returns: pd.Series) -> None:
        """检查收益自相关性"""
        # 计算多个滞后期的自相关
        autocorrs = []
        for lag in range(1, 11):
            ac = returns.autocorr(lag)
            if not np.isnan(ac):
                autocorrs.append((lag, ac))

        if not autocorrs:
            return

        # 检查是否有显著的负自相关 (可能是过度交易)
        negative_autocorr = [ac for lag, ac in autocorrs if ac < -0.1]
        self.report.metrics["avg_autocorr"] = float(np.mean([ac for _, ac in autocorrs]))

        if len(negative_autocorr) > 3:
            self.report.add_warning(
                OverfitWarning(
                    indicator=OverfitIndicator.RETURN_AUTOCORR,
                    severity="low",
                    description="收益存在显著负自相关，可能过度交易",
                    value=float(np.mean(negative_autocorr)),
                    threshold=-0.1,
                    evidence={
                        "autocorrelations": dict(autocorrs[:5]),
                    },
                )
            )

    def _check_parameter_sensitivity(
        self,
        base_returns: pd.Series,
        variation_returns: list[pd.Series],
    ) -> None:
        """检查参数敏感性"""
        base_sharpe = self._calculate_sharpe(base_returns)

        variation_sharpes = []
        for var_ret in variation_returns:
            if len(var_ret) > 0:
                variation_sharpes.append(self._calculate_sharpe(var_ret))

        if not variation_sharpes:
            return

        # 计算相对变化
        relative_changes = []
        for vs in variation_sharpes:
            if base_sharpe != 0:
                change = abs(vs - base_sharpe) / abs(base_sharpe)
                relative_changes.append(change)

        if not relative_changes:
            return

        avg_sensitivity = np.mean(relative_changes)
        max_sensitivity = np.max(relative_changes)

        self.report.metrics["param_sensitivity_avg"] = float(avg_sensitivity)
        self.report.metrics["param_sensitivity_max"] = float(max_sensitivity)

        if avg_sensitivity > 0.3:
            self.report.add_warning(
                OverfitWarning(
                    indicator=OverfitIndicator.PARAMETER_SENSITIVITY,
                    severity="high" if avg_sensitivity > 0.5 else "medium",
                    description=f"策略对参数变化高度敏感 (平均变化 {avg_sensitivity:.0%})",
                    value=float(avg_sensitivity),
                    threshold=0.3,
                    evidence={
                        "base_sharpe": float(base_sharpe),
                        "variation_sharpes": variation_sharpes[:5],
                        "max_sensitivity": float(max_sensitivity),
                    },
                )
            )

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """计算夏普比率"""
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
        return float(returns.mean() / returns.std() * np.sqrt(252))

    def _calculate_overfit_probability(self) -> None:
        """计算综合过拟合概率"""
        # 基于多个指标计算综合概率
        probability = 0.0
        weights = {
            "is_oos_ratio": 0.35,
            "sharpe_decay": 0.25,
            "param_sensitivity_avg": 0.25,
            "sharpe_cv": 0.15,
        }

        for metric, weight in weights.items():
            value = self.report.metrics.get(metric, 0)

            if metric == "is_oos_ratio":
                # 比率越高，过拟合概率越高
                prob = min(1.0, max(0.0, (value - 1) / 3))
            elif metric == "sharpe_decay":
                # 衰减越大，过拟合概率越高
                prob = min(1.0, max(0.0, value))
            elif metric == "param_sensitivity_avg":
                # 敏感性越高，过拟合概率越高
                prob = min(1.0, max(0.0, value / 0.5))
            elif metric == "sharpe_cv":
                # 变异越大，过拟合概率越高
                prob = min(1.0, max(0.0, (value - 0.5) / 1.5))
            else:
                prob = 0.0

            probability += prob * weight

        self.report.overfit_probability = probability

        # 更新风险级别
        if probability > 0.6:
            self.report.risk_level = "high"
        elif probability > 0.3:
            self.report.risk_level = "medium"


def quick_overfit_check(
    in_sample_sharpe: float,
    out_sample_sharpe: float,
) -> str:
    """
    快速过拟合检查

    Args:
        in_sample_sharpe: 样本内夏普
        out_sample_sharpe: 样本外夏普

    Returns:
        风险级别 ("low", "medium", "high")
    """
    if out_sample_sharpe <= 0:
        return "high"

    ratio = in_sample_sharpe / out_sample_sharpe

    if ratio > 3.0:
        return "high"
    elif ratio > 2.0:
        return "medium"
    else:
        return "low"


def deflated_sharpe_ratio(
    sharpe: float,
    n_trials: int,
    sample_length: int,
    skewness: float = 0,
    kurtosis: float = 3,
) -> float:
    """
    计算 Deflated Sharpe Ratio

    根据尝试次数调整夏普比率，解决多重比较问题

    Args:
        sharpe: 原始夏普比率
        n_trials: 尝试的策略/参数数量
        sample_length: 样本长度
        skewness: 收益偏度
        kurtosis: 收益峰度

    Returns:
        调整后的夏普比率
    """
    if n_trials <= 1:
        return sharpe

    # 计算期望的最大夏普 (基于多重试验)
    from scipy.special import erfinv

    # 期望最大值 (假设正态分布)
    expected_max = np.sqrt(2) * erfinv(1 - 1 / n_trials)

    # 计算调整后夏普: 原始夏普减去基于试验次数的期望最大值
    deflated = sharpe - expected_max

    return float(max(0, deflated))
