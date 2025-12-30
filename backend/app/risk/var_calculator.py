"""
VaR (Value at Risk) 计算器

支持三种方法:
1. 历史模拟法 (Historical Simulation)
2. 参数法 (Parametric/Variance-Covariance)
3. 蒙特卡洛模拟 (Monte Carlo)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy import stats

logger = structlog.get_logger()


class VaRMethod(str, Enum):
    """VaR 计算方法"""
    HISTORICAL = "historical"           # 历史模拟法
    PARAMETRIC = "parametric"           # 参数法 (正态分布)
    MONTE_CARLO = "monte_carlo"         # 蒙特卡洛模拟
    CORNISH_FISHER = "cornish_fisher"   # Cornish-Fisher 展开 (非正态)
    EWMA = "ewma"                       # 指数加权移动平均


@dataclass
class VaRResult:
    """VaR 计算结果"""
    var: float                          # VaR 值 (正数表示损失)
    cvar: float                         # CVaR / Expected Shortfall
    confidence_level: float             # 置信水平
    horizon_days: int                   # 持有期 (天)
    method: VaRMethod
    portfolio_value: float = 0.0        # 组合价值
    var_pct: float = 0.0                # VaR 占组合比例
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.portfolio_value > 0:
            self.var_pct = self.var / self.portfolio_value


class VaRCalculator:
    """
    VaR 计算器

    使用示例:
    ```python
    calculator = VaRCalculator(confidence_level=0.95, horizon_days=1)
    result = calculator.calculate(returns, method=VaRMethod.HISTORICAL)
    print(f"1日 95% VaR: {result.var_pct:.2%}")
    ```
    """

    def __init__(
        self,
        confidence_level: float = 0.95,
        horizon_days: int = 1,
        n_simulations: int = 10000,
        ewma_lambda: float = 0.94,
    ):
        """
        Args:
            confidence_level: 置信水平 (0.95 = 95%)
            horizon_days: 持有期天数
            n_simulations: 蒙特卡洛模拟次数
            ewma_lambda: EWMA 衰减因子
        """
        if not 0 < confidence_level < 1:
            raise ValueError("置信水平必须在 0 到 1 之间")

        self.confidence_level = confidence_level
        self.horizon_days = horizon_days
        self.n_simulations = n_simulations
        self.ewma_lambda = ewma_lambda

    def calculate(
        self,
        returns: pd.Series | pd.DataFrame,
        method: VaRMethod = VaRMethod.HISTORICAL,
        portfolio_value: float = 1.0,
        weights: np.ndarray | None = None,
    ) -> VaRResult:
        """
        计算 VaR

        Args:
            returns: 收益率序列或矩阵 (多资产)
            method: 计算方法
            portfolio_value: 组合价值
            weights: 资产权重 (多资产时)

        Returns:
            VaR 计算结果
        """
        # 处理多资产情况
        if isinstance(returns, pd.DataFrame):
            if weights is None:
                weights = np.ones(len(returns.columns)) / len(returns.columns)
            portfolio_returns = returns.values @ weights
            returns = pd.Series(portfolio_returns, index=returns.index)

        returns = returns.dropna()
        if len(returns) < 30:
            logger.warning("收益率样本过少，VaR 计算可能不可靠", n_samples=len(returns))

        # 根据方法计算
        if method == VaRMethod.HISTORICAL:
            var, cvar, details = self._historical_var(returns)
        elif method == VaRMethod.PARAMETRIC:
            var, cvar, details = self._parametric_var(returns)
        elif method == VaRMethod.MONTE_CARLO:
            var, cvar, details = self._monte_carlo_var(returns)
        elif method == VaRMethod.CORNISH_FISHER:
            var, cvar, details = self._cornish_fisher_var(returns)
        elif method == VaRMethod.EWMA:
            var, cvar, details = self._ewma_var(returns)
        else:
            raise ValueError(f"不支持的 VaR 方法: {method}")

        # 调整持有期 (时间平方根法则)
        if self.horizon_days > 1:
            var *= np.sqrt(self.horizon_days)
            cvar *= np.sqrt(self.horizon_days)

        # 转换为绝对金额
        var_amount = var * portfolio_value
        cvar_amount = cvar * portfolio_value

        return VaRResult(
            var=var_amount,
            cvar=cvar_amount,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days,
            method=method,
            portfolio_value=portfolio_value,
            details=details,
        )

    def _historical_var(
        self, returns: pd.Series
    ) -> tuple[float, float, dict[str, Any]]:
        """历史模拟法"""
        alpha = 1 - self.confidence_level

        # VaR: 分位数
        var = -np.percentile(returns, alpha * 100)

        # CVaR: 尾部平均
        threshold = np.percentile(returns, alpha * 100)
        tail_returns = returns[returns <= threshold]
        cvar = -tail_returns.mean() if len(tail_returns) > 0 else var

        details = {
            "method": "历史模拟法",
            "n_samples": len(returns),
            "percentile": alpha * 100,
            "min_return": float(returns.min()),
            "max_return": float(returns.max()),
        }

        return float(var), float(cvar), details

    def _parametric_var(
        self, returns: pd.Series
    ) -> tuple[float, float, dict[str, Any]]:
        """参数法 (正态分布假设)"""
        mu = returns.mean()
        sigma = returns.std()

        # 正态分布分位数
        z = stats.norm.ppf(1 - self.confidence_level)

        var = -(mu + z * sigma)

        # CVaR (正态分布解析解)
        pdf_z = stats.norm.pdf(z)
        cvar = -(mu - sigma * pdf_z / (1 - self.confidence_level))

        details = {
            "method": "参数法 (正态)",
            "mean": float(mu),
            "std": float(sigma),
            "z_score": float(z),
            "annualized_vol": float(sigma * np.sqrt(252)),
        }

        return float(var), float(cvar), details

    def _monte_carlo_var(
        self, returns: pd.Series
    ) -> tuple[float, float, dict[str, Any]]:
        """蒙特卡洛模拟"""
        mu = returns.mean()
        sigma = returns.std()
        skew = returns.skew()
        kurt = returns.kurtosis()

        # 生成模拟收益
        simulated = np.random.normal(mu, sigma, self.n_simulations)

        # 可选: 使用 Johnson SU 分布匹配偏度和峰度
        # 这里简化使用正态分布

        alpha = 1 - self.confidence_level
        var = -np.percentile(simulated, alpha * 100)

        threshold = np.percentile(simulated, alpha * 100)
        tail = simulated[simulated <= threshold]
        cvar = -tail.mean() if len(tail) > 0 else var

        details = {
            "method": "蒙特卡洛模拟",
            "n_simulations": self.n_simulations,
            "input_mean": float(mu),
            "input_std": float(sigma),
            "simulated_mean": float(simulated.mean()),
            "simulated_std": float(simulated.std()),
        }

        return float(var), float(cvar), details

    def _cornish_fisher_var(
        self, returns: pd.Series
    ) -> tuple[float, float, dict[str, Any]]:
        """Cornish-Fisher 展开 (考虑偏度和峰度)"""
        mu = returns.mean()
        sigma = returns.std()
        skew = returns.skew()
        excess_kurt = returns.kurtosis()  # pandas 返回超额峰度

        # 标准正态分位数
        z = stats.norm.ppf(1 - self.confidence_level)

        # Cornish-Fisher 调整
        z_cf = (
            z
            + (z**2 - 1) * skew / 6
            + (z**3 - 3 * z) * excess_kurt / 24
            - (2 * z**3 - 5 * z) * skew**2 / 36
        )

        var = -(mu + z_cf * sigma)

        # CVaR 近似 (使用调整后的正态分布)
        pdf_z = stats.norm.pdf(z_cf)
        cvar = -(mu - sigma * pdf_z / (1 - self.confidence_level))

        details = {
            "method": "Cornish-Fisher 展开",
            "skewness": float(skew),
            "excess_kurtosis": float(excess_kurt),
            "normal_z": float(z),
            "adjusted_z": float(z_cf),
        }

        return float(var), float(cvar), details

    def _ewma_var(
        self, returns: pd.Series
    ) -> tuple[float, float, dict[str, Any]]:
        """EWMA (指数加权移动平均) VaR"""
        mu = returns.mean()

        # EWMA 方差
        n = len(returns)
        weights = np.array([(1 - self.ewma_lambda) * self.ewma_lambda ** i for i in range(n)])
        weights = weights[::-1]  # 最新数据权重最高
        weights /= weights.sum()

        ewma_var = np.sum(weights * (returns.values - mu) ** 2)
        ewma_std = np.sqrt(ewma_var)

        z = stats.norm.ppf(1 - self.confidence_level)
        var = -(mu + z * ewma_std)

        pdf_z = stats.norm.pdf(z)
        cvar = -(mu - ewma_std * pdf_z / (1 - self.confidence_level))

        details = {
            "method": "EWMA",
            "lambda": self.ewma_lambda,
            "ewma_std": float(ewma_std),
            "simple_std": float(returns.std()),
            "half_life": float(np.log(0.5) / np.log(self.ewma_lambda)),
        }

        return float(var), float(cvar), details


def calculate_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    method: VaRMethod = VaRMethod.HISTORICAL,
) -> float:
    """
    快速计算 VaR

    Args:
        returns: 收益率序列
        confidence_level: 置信水平
        method: 计算方法

    Returns:
        VaR 值 (正数表示损失)
    """
    calculator = VaRCalculator(confidence_level=confidence_level)
    result = calculator.calculate(returns, method=method)
    return result.var_pct


def calculate_cvar(
    returns: pd.Series,
    confidence_level: float = 0.95,
    method: VaRMethod = VaRMethod.HISTORICAL,
) -> float:
    """
    快速计算 CVaR (Expected Shortfall)

    Args:
        returns: 收益率序列
        confidence_level: 置信水平
        method: 计算方法

    Returns:
        CVaR 值 (正数表示损失)
    """
    calculator = VaRCalculator(confidence_level=confidence_level)
    result = calculator.calculate(returns, method=method)
    return result.cvar / result.portfolio_value if result.portfolio_value > 0 else result.cvar


class PortfolioVaR:
    """
    组合 VaR 计算

    支持:
    - 多资产组合
    - 协方差矩阵估计
    - 成分 VaR 分解
    """

    def __init__(
        self,
        returns: pd.DataFrame,
        weights: np.ndarray,
        confidence_level: float = 0.95,
    ):
        """
        Args:
            returns: 资产收益率矩阵 (index=date, columns=assets)
            weights: 资产权重
            confidence_level: 置信水平
        """
        self.returns = returns
        self.weights = np.array(weights)
        self.confidence_level = confidence_level

        # 计算协方差矩阵
        self.cov_matrix = returns.cov()
        self.mean_returns = returns.mean()

    def calculate_portfolio_var(self) -> dict[str, Any]:
        """计算组合 VaR"""
        # 组合收益
        port_return = self.mean_returns.values @ self.weights
        port_var = self.weights @ self.cov_matrix.values @ self.weights
        port_std = np.sqrt(port_var)

        z = stats.norm.ppf(1 - self.confidence_level)
        var = -(port_return + z * port_std)

        return {
            "portfolio_var": float(var),
            "portfolio_std": float(port_std),
            "portfolio_return": float(port_return),
            "annualized_vol": float(port_std * np.sqrt(252)),
        }

    def calculate_component_var(self) -> pd.Series:
        """计算成分 VaR (各资产对组合 VaR 的贡献)"""
        port_var = self.weights @ self.cov_matrix.values @ self.weights
        port_std = np.sqrt(port_var)

        z = stats.norm.ppf(1 - self.confidence_level)

        # 边际 VaR
        marginal_var = (self.cov_matrix.values @ self.weights) / port_std * (-z)

        # 成分 VaR
        component_var = marginal_var * self.weights

        return pd.Series(component_var, index=self.returns.columns, name="component_var")

    def calculate_incremental_var(self, asset_idx: int, delta_weight: float = 0.01) -> float:
        """
        计算增量 VaR (增加某资产头寸对 VaR 的影响)

        Args:
            asset_idx: 资产索引
            delta_weight: 权重变化

        Returns:
            增量 VaR
        """
        base_var = self.calculate_portfolio_var()["portfolio_var"]

        new_weights = self.weights.copy()
        new_weights[asset_idx] += delta_weight
        new_weights /= new_weights.sum()  # 重新归一化

        new_port_var = new_weights @ self.cov_matrix.values @ new_weights
        new_port_std = np.sqrt(new_port_var)
        z = stats.norm.ppf(1 - self.confidence_level)
        new_var = -z * new_port_std

        return float(new_var - base_var)
