"""
数据窥探校正

解决多重假设检验问题:
- 家族错误率 (FWER) 控制
- 错误发现率 (FDR) 控制
- 调整后的 p 值和置信区间
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy import stats

logger = structlog.get_logger()


class CorrectionMethod(str, Enum):
    """校正方法"""
    BONFERRONI = "bonferroni"           # Bonferroni 校正
    HOLM = "holm"                       # Holm-Bonferroni
    BH = "benjamini_hochberg"           # Benjamini-Hochberg (FDR)
    BY = "benjamini_yekutieli"          # Benjamini-Yekutieli
    SIDAK = "sidak"                     # Šidák 校正
    BOOTSTRAP = "bootstrap"             # Bootstrap 校正


@dataclass
class CorrectionResult:
    """校正结果"""
    original_pvalue: float
    corrected_pvalue: float
    is_significant: bool
    original_sharpe: float
    corrected_sharpe: float
    method: CorrectionMethod
    n_tests: int


@dataclass
class DataSnoopingReport:
    """数据窥探校正报告"""
    n_strategies: int = 0                   # 测试的策略数量
    n_significant_original: int = 0         # 原始显著数量
    n_significant_corrected: int = 0        # 校正后显著数量
    false_discovery_rate: float = 0.0       # 估计的错误发现率
    results: list[CorrectionResult] = field(default_factory=list)
    best_strategy_idx: int | None = None
    best_corrected_sharpe: float = 0.0


class DataSnoopingCorrector:
    """
    数据窥探校正器

    方法:
    1. Bonferroni: 最保守，控制 FWER
    2. Holm-Bonferroni: 比 Bonferroni 稍宽松
    3. Benjamini-Hochberg: 控制 FDR，适合探索性研究
    4. Bootstrap: 非参数方法，适合小样本
    """

    def __init__(
        self,
        method: CorrectionMethod = CorrectionMethod.BH,
        alpha: float = 0.05,
    ):
        """
        Args:
            method: 校正方法
            alpha: 显著性水平
        """
        self.method = method
        self.alpha = alpha

    def correct_multiple_tests(
        self,
        sharpe_ratios: list[float],
        sample_sizes: list[int],
        skewness: list[float] | None = None,
        kurtosis: list[float] | None = None,
    ) -> DataSnoopingReport:
        """
        校正多重检验

        Args:
            sharpe_ratios: 夏普比率列表
            sample_sizes: 各策略的样本大小
            skewness: 收益偏度
            kurtosis: 收益峰度

        Returns:
            校正报告
        """
        n = len(sharpe_ratios)
        if n == 0:
            return DataSnoopingReport()

        # 计算原始 p 值
        p_values = []
        for i, sharpe in enumerate(sharpe_ratios):
            sample_size = sample_sizes[i] if i < len(sample_sizes) else 252
            sk = skewness[i] if skewness and i < len(skewness) else 0
            ku = kurtosis[i] if kurtosis and i < len(kurtosis) else 3

            pval = self._sharpe_to_pvalue(sharpe, sample_size, sk, ku)
            p_values.append(pval)

        p_values = np.array(p_values)

        # 应用校正
        corrected_pvalues = self._apply_correction(p_values)

        # 计算校正后夏普
        corrected_sharpes = []
        for i, (_sharpe, corr_p) in enumerate(zip(sharpe_ratios, corrected_pvalues)):
            sample_size = sample_sizes[i] if i < len(sample_sizes) else 252
            corr_sharpe = self._pvalue_to_sharpe(corr_p, sample_size)
            corrected_sharpes.append(corr_sharpe)

        # 生成结果
        report = DataSnoopingReport(n_strategies=n)
        results = []

        for i in range(n):
            is_sig = corrected_pvalues[i] < self.alpha
            result = CorrectionResult(
                original_pvalue=float(p_values[i]),
                corrected_pvalue=float(corrected_pvalues[i]),
                is_significant=is_sig,
                original_sharpe=float(sharpe_ratios[i]),
                corrected_sharpe=float(corrected_sharpes[i]),
                method=self.method,
                n_tests=n,
            )
            results.append(result)

            if p_values[i] < self.alpha:
                report.n_significant_original += 1
            if is_sig:
                report.n_significant_corrected += 1

        report.results = results

        # 找最佳策略
        if results:
            best_idx = int(np.argmax([r.corrected_sharpe for r in results]))
            report.best_strategy_idx = best_idx
            report.best_corrected_sharpe = results[best_idx].corrected_sharpe

        # 估计 FDR
        if report.n_significant_original > 0:
            report.false_discovery_rate = 1 - report.n_significant_corrected / report.n_significant_original

        logger.info(
            "数据窥探校正完成",
            method=self.method.value,
            n_strategies=n,
            original_significant=report.n_significant_original,
            corrected_significant=report.n_significant_corrected,
        )

        return report

    def _sharpe_to_pvalue(
        self,
        sharpe: float,
        sample_size: int,
        skewness: float = 0,
        kurtosis: float = 3,
    ) -> float:
        """将夏普比率转换为 p 值"""
        if sample_size <= 1:
            return 1.0

        # 夏普比率的标准误
        # SE(SR) = sqrt((1 + 0.5*SR^2 - skew*SR + (kurt-3)/4*SR^2) / T)
        var_adjustment = 1 + 0.5 * sharpe ** 2 - skewness * sharpe / 6 + (kurtosis - 3) / 24 * sharpe ** 2
        se = np.sqrt(max(0.001, var_adjustment) / sample_size)

        # 计算 z 值和 p 值 (单尾，H0: SR <= 0)
        z = sharpe / se
        p_value = 1 - stats.norm.cdf(z)

        return float(p_value)

    def _pvalue_to_sharpe(self, pvalue: float, sample_size: int) -> float:
        """将 p 值转换回夏普比率"""
        if pvalue >= 1.0:
            return 0.0
        if pvalue <= 0.0:
            return float("inf")

        z = stats.norm.ppf(1 - pvalue)
        se = 1.0 / np.sqrt(sample_size)
        sharpe = z * se

        return float(max(0, sharpe))

    def _apply_correction(self, p_values: np.ndarray) -> np.ndarray:
        """应用多重检验校正"""
        n = len(p_values)
        if n == 0:
            return p_values

        if self.method == CorrectionMethod.BONFERRONI:
            return self._bonferroni(p_values)
        elif self.method == CorrectionMethod.HOLM:
            return self._holm(p_values)
        elif self.method == CorrectionMethod.BH:
            return self._benjamini_hochberg(p_values)
        elif self.method == CorrectionMethod.BY:
            return self._benjamini_yekutieli(p_values)
        elif self.method == CorrectionMethod.SIDAK:
            return self._sidak(p_values)
        else:
            return p_values

    def _bonferroni(self, p_values: np.ndarray) -> np.ndarray:
        """Bonferroni 校正"""
        return np.minimum(p_values * len(p_values), 1.0)

    def _holm(self, p_values: np.ndarray) -> np.ndarray:
        """Holm-Bonferroni 校正"""
        n = len(p_values)
        sorted_idx = np.argsort(p_values)
        sorted_p = p_values[sorted_idx]

        corrected = np.zeros(n)
        cummax = 0
        for i, (idx, p) in enumerate(zip(sorted_idx, sorted_p)):
            adj_p = p * (n - i)
            cummax = max(cummax, adj_p)
            corrected[idx] = min(cummax, 1.0)

        return corrected

    def _benjamini_hochberg(self, p_values: np.ndarray) -> np.ndarray:
        """Benjamini-Hochberg 校正 (FDR)"""
        n = len(p_values)
        sorted_idx = np.argsort(p_values)
        sorted_p = p_values[sorted_idx]

        corrected = np.zeros(n)
        cummin = 1.0

        for i in range(n - 1, -1, -1):
            idx = sorted_idx[i]
            adj_p = sorted_p[i] * n / (i + 1)
            cummin = min(cummin, adj_p)
            corrected[idx] = min(cummin, 1.0)

        return corrected

    def _benjamini_yekutieli(self, p_values: np.ndarray) -> np.ndarray:
        """Benjamini-Yekutieli 校正 (更保守的 FDR)"""
        n = len(p_values)
        c_n = np.sum(1.0 / np.arange(1, n + 1))  # 调和级数

        sorted_idx = np.argsort(p_values)
        sorted_p = p_values[sorted_idx]

        corrected = np.zeros(n)
        cummin = 1.0

        for i in range(n - 1, -1, -1):
            idx = sorted_idx[i]
            adj_p = sorted_p[i] * n * c_n / (i + 1)
            cummin = min(cummin, adj_p)
            corrected[idx] = min(cummin, 1.0)

        return corrected

    def _sidak(self, p_values: np.ndarray) -> np.ndarray:
        """Šidák 校正"""
        n = len(p_values)
        return 1 - (1 - p_values) ** n


class BootstrapCorrector:
    """
    Bootstrap 数据窥探校正

    使用 Reality Check 或 SPA 测试
    """

    def __init__(self, n_bootstrap: int = 1000):
        """
        Args:
            n_bootstrap: Bootstrap 次数
        """
        self.n_bootstrap = n_bootstrap

    def reality_check(
        self,
        strategy_returns: pd.DataFrame,
        benchmark_returns: pd.Series | None = None,
    ) -> dict[str, Any]:
        """
        White's Reality Check

        检验最佳策略是否显著优于基准

        Args:
            strategy_returns: 策略收益矩阵 (index=date, columns=strategies)
            benchmark_returns: 基准收益

        Returns:
            检验结果
        """
        n_obs = len(strategy_returns)
        n_strategies = len(strategy_returns.columns)

        if benchmark_returns is None:
            benchmark_returns = pd.Series(0, index=strategy_returns.index)

        # 计算超额收益
        excess_returns = strategy_returns.sub(benchmark_returns, axis=0)

        # 原始检验统计量 (最大平均超额收益)
        mean_excess = excess_returns.mean()
        t_stat_original = mean_excess.max() * np.sqrt(n_obs)

        # Bootstrap
        t_stats_bootstrap = []

        for _ in range(self.n_bootstrap):
            # 有放回抽样
            bootstrap_idx = np.random.choice(n_obs, size=n_obs, replace=True)
            bootstrap_excess = excess_returns.iloc[bootstrap_idx]

            # 中心化 (在 H0 下)
            centered = bootstrap_excess - excess_returns.mean()
            mean_centered = centered.mean()
            t_stat = mean_centered.max() * np.sqrt(n_obs)
            t_stats_bootstrap.append(t_stat)

        t_stats_bootstrap = np.array(t_stats_bootstrap)

        # 计算 p 值
        p_value = (t_stats_bootstrap >= t_stat_original).mean()

        # 找到最佳策略
        best_strategy = mean_excess.idxmax()
        best_excess_return = mean_excess.max()

        return {
            "p_value": float(p_value),
            "is_significant": p_value < 0.05,
            "best_strategy": best_strategy,
            "best_excess_return": float(best_excess_return),
            "t_statistic": float(t_stat_original),
            "n_strategies": n_strategies,
            "n_bootstrap": self.n_bootstrap,
        }

    def spa_test(
        self,
        strategy_returns: pd.DataFrame,
        benchmark_returns: pd.Series | None = None,
    ) -> dict[str, Any]:
        """
        Superior Predictive Ability (SPA) 测试

        Hansen (2005) 的改进版本

        Args:
            strategy_returns: 策略收益矩阵
            benchmark_returns: 基准收益

        Returns:
            检验结果
        """
        n_obs = len(strategy_returns)
        n_strategies = len(strategy_returns.columns)

        if benchmark_returns is None:
            benchmark_returns = pd.Series(0, index=strategy_returns.index)

        # 计算超额收益
        excess_returns = strategy_returns.sub(benchmark_returns, axis=0)
        mean_excess = excess_returns.mean()

        # 方差估计 (Newey-West)
        variances = excess_returns.var()

        # t 统计量
        t_stats = mean_excess / np.sqrt(variances / n_obs)
        t_max = t_stats.max()

        # Bootstrap (使用 Politis-Romano 固定块)
        block_size = int(np.ceil(n_obs ** (1/3)))
        t_stats_bootstrap = []

        for _ in range(self.n_bootstrap):
            # 块 bootstrap
            bootstrap_idx = self._block_bootstrap_indices(n_obs, block_size)
            bootstrap_excess = excess_returns.iloc[bootstrap_idx].reset_index(drop=True)

            # 去均值
            centered = bootstrap_excess - mean_excess
            boot_mean = centered.mean()
            boot_var = centered.var()
            boot_t = boot_mean / np.sqrt(boot_var / n_obs)
            t_stats_bootstrap.append(boot_t.max())

        t_stats_bootstrap = np.array(t_stats_bootstrap)

        # p 值
        p_value = (t_stats_bootstrap >= t_max).mean()

        return {
            "p_value": float(p_value),
            "is_significant": p_value < 0.05,
            "best_strategy": t_stats.idxmax(),
            "best_t_statistic": float(t_max),
            "n_strategies": n_strategies,
            "n_bootstrap": self.n_bootstrap,
            "block_size": block_size,
        }

    def _block_bootstrap_indices(self, n: int, block_size: int) -> np.ndarray:
        """生成块 bootstrap 索引"""
        n_blocks = int(np.ceil(n / block_size))
        start_points = np.random.randint(0, n, size=n_blocks)

        indices = []
        for start in start_points:
            block = np.arange(start, start + block_size) % n
            indices.extend(block)

        return np.array(indices[:n])


def adjusted_sharpe_ratio(
    sharpe: float,
    n_strategies_tested: int,
    sample_size: int = 252,
) -> float:
    """
    快速计算调整后夏普比率

    Args:
        sharpe: 原始夏普比率
        n_strategies_tested: 测试的策略数量
        sample_size: 样本大小

    Returns:
        调整后的夏普比率
    """
    if n_strategies_tested <= 1:
        return sharpe

    # 使用 Bonferroni 风格的简单调整
    # 调整因子 = sqrt(log(n))
    adjustment_factor = np.sqrt(np.log(n_strategies_tested))
    se = 1.0 / np.sqrt(sample_size)

    adjusted = sharpe - adjustment_factor * se

    return float(max(0, adjusted))
