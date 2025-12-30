"""
因子暴露计算器

计算组合对各类风险因子的暴露:
- 市场因子 (Beta)
- Fama-French 因子
- 行业因子
- 风格因子
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy import stats

logger = structlog.get_logger()


class FactorType(str, Enum):
    """因子类型"""
    MARKET = "market"           # 市场因子
    SIZE = "size"               # 规模因子 (SMB)
    VALUE = "value"             # 价值因子 (HML)
    MOMENTUM = "momentum"       # 动量因子
    VOLATILITY = "volatility"   # 波动率因子
    QUALITY = "quality"         # 质量因子
    LIQUIDITY = "liquidity"     # 流动性因子
    INDUSTRY = "industry"       # 行业因子


@dataclass
class FactorExposure:
    """单个因子暴露"""
    factor: str
    factor_type: FactorType
    exposure: float             # 暴露系数 (Beta)
    t_stat: float               # t 统计量
    p_value: float              # p 值
    is_significant: bool        # 是否显著 (p < 0.05)
    contribution: float = 0.0   # 对组合收益的贡献


@dataclass
class ExposureReport:
    """因子暴露报告"""
    exposures: list[FactorExposure] = field(default_factory=list)
    r_squared: float = 0.0                  # R² (解释力度)
    adj_r_squared: float = 0.0              # 调整后 R²
    alpha: float = 0.0                      # Alpha (超额收益)
    alpha_t_stat: float = 0.0
    alpha_p_value: float = 1.0
    residual_risk: float = 0.0              # 残差风险 (特异性风险)
    factor_risk: float = 0.0                # 因子风险 (系统性风险)
    total_risk: float = 0.0                 # 总风险


class FactorExposureCalculator:
    """
    因子暴露计算器

    使用回归分析计算组合对各因子的暴露

    使用示例:
    ```python
    calculator = FactorExposureCalculator()
    report = calculator.calculate(
        portfolio_returns=returns,
        factor_returns=factor_df,  # columns: ['market', 'size', 'value', ...]
    )
    for exp in report.exposures:
        print(f"{exp.factor}: beta={exp.exposure:.2f}, t={exp.t_stat:.2f}")
    ```
    """

    def __init__(
        self,
        risk_free_rate: float = 0.0,
        min_observations: int = 60,
    ):
        """
        Args:
            risk_free_rate: 无风险利率 (日)
            min_observations: 最小观测数
        """
        self.risk_free_rate = risk_free_rate
        self.min_observations = min_observations

    def calculate(
        self,
        portfolio_returns: pd.Series,
        factor_returns: pd.DataFrame,
        factor_types: dict[str, FactorType] | None = None,
    ) -> ExposureReport:
        """
        计算因子暴露

        Args:
            portfolio_returns: 组合收益
            factor_returns: 因子收益矩阵
            factor_types: 因子类型映射

        Returns:
            因子暴露报告
        """
        # 对齐数据
        common_idx = portfolio_returns.index.intersection(factor_returns.index)
        if len(common_idx) < self.min_observations:
            logger.warning(
                "观测数不足",
                n_obs=len(common_idx),
                min_required=self.min_observations,
            )
            return ExposureReport()

        y = portfolio_returns.loc[common_idx] - self.risk_free_rate
        X = factor_returns.loc[common_idx]

        # 添加常数项
        X_with_const = np.column_stack([np.ones(len(X)), X.values])

        # OLS 回归
        try:
            beta, residuals, rank, s = np.linalg.lstsq(X_with_const, y.values, rcond=None)
        except np.linalg.LinAlgError:
            logger.error("回归计算失败")
            return ExposureReport()

        # 计算统计量
        n = len(y)
        k = X.shape[1] + 1  # 包含常数项

        y_hat = X_with_const @ beta
        ss_res = np.sum((y.values - y_hat) ** 2)
        ss_tot = np.sum((y.values - y.mean()) ** 2)

        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k) if n > k else 0

        # 残差标准误
        mse = ss_res / (n - k) if n > k else ss_res
        se_beta = np.sqrt(np.diag(mse * np.linalg.inv(X_with_const.T @ X_with_const)))

        # t 统计量和 p 值
        t_stats = beta / se_beta
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), n - k))

        # 构建报告
        report = ExposureReport(
            r_squared=float(r_squared),
            adj_r_squared=float(adj_r_squared),
            alpha=float(beta[0] * 252),  # 年化 Alpha
            alpha_t_stat=float(t_stats[0]),
            alpha_p_value=float(p_values[0]),
        )

        # 添加因子暴露
        factor_names = list(X.columns)
        for i, name in enumerate(factor_names):
            idx = i + 1  # 跳过常数项

            factor_type = FactorType.MARKET
            if factor_types and name in factor_types:
                factor_type = factor_types[name]

            exposure = FactorExposure(
                factor=name,
                factor_type=factor_type,
                exposure=float(beta[idx]),
                t_stat=float(t_stats[idx]),
                p_value=float(p_values[idx]),
                is_significant=p_values[idx] < 0.05,
            )
            report.exposures.append(exposure)

        # 计算风险分解
        residuals = y.values - y_hat
        report.residual_risk = float(np.std(residuals) * np.sqrt(252))
        report.total_risk = float(np.std(y) * np.sqrt(252))
        report.factor_risk = float(
            np.sqrt(max(0, report.total_risk ** 2 - report.residual_risk ** 2))
        )

        # 计算因子贡献
        factor_vars = X.var()
        for i, exp in enumerate(report.exposures):
            if i < len(factor_vars):
                exp.contribution = float(
                    exp.exposure ** 2 * factor_vars.iloc[i] / (y.var() if y.var() > 0 else 1)
                )

        logger.info(
            "因子暴露计算完成",
            n_factors=len(report.exposures),
            r_squared=f"{r_squared:.2%}",
            alpha=f"{report.alpha:.2%}",
        )

        return report

    def calculate_rolling_exposure(
        self,
        portfolio_returns: pd.Series,
        factor_returns: pd.DataFrame,
        window: int = 60,
    ) -> pd.DataFrame:
        """
        计算滚动因子暴露

        Args:
            portfolio_returns: 组合收益
            factor_returns: 因子收益矩阵
            window: 滚动窗口大小

        Returns:
            滚动暴露 DataFrame
        """
        common_idx = portfolio_returns.index.intersection(factor_returns.index)
        y = portfolio_returns.loc[common_idx]
        X = factor_returns.loc[common_idx]

        factor_names = list(X.columns)
        results = {name: [] for name in ["date", "alpha"] + factor_names}

        for i in range(window, len(y) + 1):
            y_window = y.iloc[i - window : i]
            X_window = X.iloc[i - window : i]

            X_with_const = np.column_stack([np.ones(window), X_window.values])

            try:
                beta, _, _, _ = np.linalg.lstsq(X_with_const, y_window.values, rcond=None)

                results["date"].append(y.index[i - 1])
                results["alpha"].append(beta[0])
                for j, name in enumerate(factor_names):
                    results[name].append(beta[j + 1])
            except Exception:
                results["date"].append(y.index[i - 1])
                results["alpha"].append(np.nan)
                for name in factor_names:
                    results[name].append(np.nan)

        return pd.DataFrame(results).set_index("date")


class IndustryExposureCalculator:
    """
    行业暴露计算器

    计算组合对各行业的暴露
    """

    def __init__(
        self,
        industry_mapping: dict[str, str] | None = None,
    ):
        """
        Args:
            industry_mapping: 股票 -> 行业映射
        """
        self.industry_mapping = industry_mapping or {}

    def calculate(
        self,
        holdings: dict[str, float],
        benchmark_weights: dict[str, float] | None = None,
    ) -> pd.DataFrame:
        """
        计算行业暴露

        Args:
            holdings: 持仓 {symbol: weight}
            benchmark_weights: 基准权重

        Returns:
            行业暴露 DataFrame
        """
        # 计算组合行业权重
        portfolio_industry = {}
        for symbol, weight in holdings.items():
            industry = self.industry_mapping.get(symbol, "其他")
            portfolio_industry[industry] = portfolio_industry.get(industry, 0) + weight

        # 计算基准行业权重
        benchmark_industry = {}
        if benchmark_weights:
            for symbol, weight in benchmark_weights.items():
                industry = self.industry_mapping.get(symbol, "其他")
                benchmark_industry[industry] = benchmark_industry.get(industry, 0) + weight

        # 合并所有行业
        all_industries = set(portfolio_industry.keys()) | set(benchmark_industry.keys())

        results = []
        for industry in sorted(all_industries):
            port_weight = portfolio_industry.get(industry, 0)
            bench_weight = benchmark_industry.get(industry, 0)

            results.append({
                "industry": industry,
                "portfolio_weight": port_weight,
                "benchmark_weight": bench_weight,
                "active_weight": port_weight - bench_weight,
                "relative_weight": port_weight / bench_weight if bench_weight > 0 else np.inf,
            })

        return pd.DataFrame(results).set_index("industry")


def calculate_beta(
    returns: pd.Series,
    market_returns: pd.Series,
) -> float:
    """
    快速计算 Beta

    Args:
        returns: 资产收益
        market_returns: 市场收益

    Returns:
        Beta 值
    """
    common_idx = returns.index.intersection(market_returns.index)
    if len(common_idx) < 30:
        return 1.0

    r = returns.loc[common_idx]
    m = market_returns.loc[common_idx]

    cov = np.cov(r, m)[0, 1]
    var = m.var()

    return float(cov / var) if var > 0 else 1.0


def calculate_tracking_error(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    annualize: bool = True,
) -> float:
    """
    计算跟踪误差

    Args:
        portfolio_returns: 组合收益
        benchmark_returns: 基准收益
        annualize: 是否年化

    Returns:
        跟踪误差
    """
    common_idx = portfolio_returns.index.intersection(benchmark_returns.index)
    if len(common_idx) < 2:
        return 0.0

    active_returns = portfolio_returns.loc[common_idx] - benchmark_returns.loc[common_idx]
    te = active_returns.std()

    if annualize:
        te *= np.sqrt(252)

    return float(te)
