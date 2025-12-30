"""
因子权重优化器

提供:
- 等权重分配
- IC 加权
- 风险平价
- 最小方差
- 最大夏普
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy.optimize import minimize

logger = structlog.get_logger()


class OptimizationMethod(str, Enum):
    """优化方法"""
    EQUAL = "equal"                 # 等权重
    IC_WEIGHTED = "ic_weighted"     # IC 加权
    RISK_PARITY = "risk_parity"     # 风险平价
    MIN_VARIANCE = "min_variance"   # 最小方差
    MAX_SHARPE = "max_sharpe"       # 最大夏普
    MAX_DIVERSIFICATION = "max_div" # 最大分散化
    CUSTOM = "custom"               # 自定义


@dataclass
class OptimizationResult:
    """优化结果"""
    weights: dict[str, float]       # 资产权重
    method: OptimizationMethod      # 优化方法
    expected_return: float = 0.0    # 预期收益
    expected_risk: float = 0.0      # 预期风险
    sharpe_ratio: float = 0.0       # 夏普比率
    diversification_ratio: float = 0.0  # 分散化比率
    metadata: dict[str, Any] | None = None


class WeightOptimizer:
    """
    权重优化器

    支持多种优化方法:
    - 等权: 简单均分
    - IC加权: 根据因子 IC 值分配
    - 风险平价: 每资产贡献相等风险
    - 最小方差: 最小化组合方差
    - 最大夏普: 最大化风险调整收益
    """

    def __init__(
        self,
        method: OptimizationMethod = OptimizationMethod.EQUAL,
        risk_free_rate: float = 0.0,
    ):
        """
        Args:
            method: 优化方法
            risk_free_rate: 无风险利率 (年化)
        """
        self.method = method
        self.risk_free_rate = risk_free_rate

    def optimize(
        self,
        returns: pd.DataFrame,
        ic_values: pd.Series | None = None,
        constraints: dict[str, Any] | None = None,
    ) -> OptimizationResult:
        """
        执行权重优化

        Args:
            returns: 资产收益率 DataFrame (index=date, columns=assets)
            ic_values: 因子 IC 值 (用于 IC 加权)
            constraints: 约束条件

        Returns:
            优化结果
        """
        assets = returns.columns.tolist()
        n_assets = len(assets)

        if n_assets == 0:
            return OptimizationResult(weights={}, method=self.method)

        # 计算预期收益和协方差矩阵
        expected_returns = returns.mean() * 252  # 年化
        cov_matrix = returns.cov() * 252         # 年化

        # 根据方法选择优化器
        if self.method == OptimizationMethod.EQUAL:
            weights = self._equal_weight(assets)
        elif self.method == OptimizationMethod.IC_WEIGHTED:
            weights = self._ic_weighted(assets, ic_values)
        elif self.method == OptimizationMethod.RISK_PARITY:
            weights = self._risk_parity(assets, cov_matrix)
        elif self.method == OptimizationMethod.MIN_VARIANCE:
            weights = self._min_variance(assets, cov_matrix, constraints)
        elif self.method == OptimizationMethod.MAX_SHARPE:
            weights = self._max_sharpe(assets, expected_returns, cov_matrix, constraints)
        elif self.method == OptimizationMethod.MAX_DIVERSIFICATION:
            weights = self._max_diversification(assets, cov_matrix, constraints)
        else:
            weights = self._equal_weight(assets)

        # 计算组合指标
        w = np.array([weights[a] for a in assets])
        port_return = float(np.dot(w, expected_returns))
        port_risk = float(np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))))
        sharpe = (port_return - self.risk_free_rate) / port_risk if port_risk > 0 else 0.0

        # 分散化比率
        asset_vols = np.sqrt(np.diag(cov_matrix))
        weighted_vol_sum = float(np.dot(w, asset_vols))
        div_ratio = weighted_vol_sum / port_risk if port_risk > 0 else 1.0

        logger.info(
            "权重优化完成",
            method=self.method.value,
            n_assets=n_assets,
            expected_return=f"{port_return:.2%}",
            expected_risk=f"{port_risk:.2%}",
            sharpe=f"{sharpe:.2f}",
        )

        return OptimizationResult(
            weights=weights,
            method=self.method,
            expected_return=port_return,
            expected_risk=port_risk,
            sharpe_ratio=sharpe,
            diversification_ratio=div_ratio,
        )

    def _equal_weight(self, assets: list[str]) -> dict[str, float]:
        """等权重"""
        n = len(assets)
        weight = 1.0 / n if n > 0 else 0.0
        return dict.fromkeys(assets, weight)

    def _ic_weighted(
        self,
        assets: list[str],
        ic_values: pd.Series | None,
    ) -> dict[str, float]:
        """
        IC 加权

        权重与因子 IC 成正比
        """
        if ic_values is None or ic_values.empty:
            logger.warning("未提供 IC 值，使用等权重")
            return self._equal_weight(assets)

        # 取绝对值 (支持正负因子)
        abs_ic = ic_values.abs()

        # 只保留有 IC 的资产
        valid_ic = abs_ic.reindex(assets).dropna()

        if valid_ic.empty or valid_ic.sum() == 0:
            return self._equal_weight(assets)

        # 归一化
        weights = valid_ic / valid_ic.sum()

        # 补充缺失资产
        result = dict.fromkeys(assets, 0.0)
        for asset, w in weights.items():
            result[asset] = float(w)

        return result

    def _risk_parity(
        self,
        assets: list[str],
        cov_matrix: pd.DataFrame,
    ) -> dict[str, float]:
        """
        风险平价

        目标: 每个资产对组合风险的贡献相等
        """
        n = len(assets)
        cov = cov_matrix.values

        def risk_budget_objective(weights: np.ndarray) -> float:
            """风险预算目标函数"""
            port_var = np.dot(weights.T, np.dot(cov, weights))
            port_vol = np.sqrt(port_var)

            # 边际风险贡献
            marginal_contrib = np.dot(cov, weights) / port_vol
            risk_contrib = weights * marginal_contrib

            # 目标: 所有风险贡献相等
            target_contrib = port_vol / n
            diff = risk_contrib - target_contrib

            return float(np.sum(diff ** 2))

        # 初始权重
        x0 = np.ones(n) / n

        # 约束
        constraints_list = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1},  # 权重和为1
        ]
        bounds = [(0.0, 1.0) for _ in range(n)]

        # 优化
        result = minimize(
            risk_budget_objective,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
        )

        if result.success:
            weights = result.x
        else:
            logger.warning("风险平价优化失败，使用等权重")
            weights = x0

        return {asset: float(w) for asset, w in zip(assets, weights)}

    def _min_variance(
        self,
        assets: list[str],
        cov_matrix: pd.DataFrame,
        constraints: dict[str, Any] | None,
    ) -> dict[str, float]:
        """
        最小方差组合

        目标: 最小化组合方差
        """
        n = len(assets)
        cov = cov_matrix.values

        def portfolio_variance(weights: np.ndarray) -> float:
            return float(np.dot(weights.T, np.dot(cov, weights)))

        # 初始权重
        x0 = np.ones(n) / n

        # 约束
        constraints_list = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1},
        ]

        # 边界
        bounds = self._get_bounds(n, constraints)

        # 优化
        result = minimize(
            portfolio_variance,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
        )

        if result.success:
            weights = result.x
        else:
            logger.warning("最小方差优化失败，使用等权重")
            weights = x0

        return {asset: float(w) for asset, w in zip(assets, weights)}

    def _max_sharpe(
        self,
        assets: list[str],
        expected_returns: pd.Series,
        cov_matrix: pd.DataFrame,
        constraints: dict[str, Any] | None,
    ) -> dict[str, float]:
        """
        最大夏普比率组合

        目标: 最大化 (预期收益 - 无风险利率) / 波动率
        """
        n = len(assets)
        mu = expected_returns.values
        cov = cov_matrix.values

        def neg_sharpe(weights: np.ndarray) -> float:
            port_return = np.dot(weights, mu)
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
            if port_vol == 0:
                return 0.0
            return -float((port_return - self.risk_free_rate) / port_vol)

        # 初始权重
        x0 = np.ones(n) / n

        # 约束
        constraints_list = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1},
        ]

        # 边界
        bounds = self._get_bounds(n, constraints)

        # 优化
        result = minimize(
            neg_sharpe,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
        )

        if result.success:
            weights = result.x
        else:
            logger.warning("最大夏普优化失败，使用等权重")
            weights = x0

        return {asset: float(w) for asset, w in zip(assets, weights)}

    def _max_diversification(
        self,
        assets: list[str],
        cov_matrix: pd.DataFrame,
        constraints: dict[str, Any] | None,
    ) -> dict[str, float]:
        """
        最大分散化组合

        目标: 最大化分散化比率 = 加权平均波动率 / 组合波动率
        """
        n = len(assets)
        cov = cov_matrix.values
        asset_vols = np.sqrt(np.diag(cov))

        def neg_diversification_ratio(weights: np.ndarray) -> float:
            port_vol = np.sqrt(np.dot(weights.T, np.dot(cov, weights)))
            weighted_vol_sum = np.dot(weights, asset_vols)
            if port_vol == 0:
                return 0.0
            return -float(weighted_vol_sum / port_vol)

        # 初始权重
        x0 = np.ones(n) / n

        # 约束
        constraints_list = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1},
        ]

        # 边界
        bounds = self._get_bounds(n, constraints)

        # 优化
        result = minimize(
            neg_diversification_ratio,
            x0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints_list,
        )

        if result.success:
            weights = result.x
        else:
            logger.warning("最大分散化优化失败，使用等权重")
            weights = x0

        return {asset: float(w) for asset, w in zip(assets, weights)}

    def _get_bounds(
        self,
        n: int,
        constraints: dict[str, Any] | None,
    ) -> list[tuple[float, float]]:
        """获取权重边界"""
        if constraints is None:
            return [(0.0, 1.0) for _ in range(n)]

        min_weight = constraints.get("min_weight", 0.0)
        max_weight = constraints.get("max_weight", 1.0)

        return [(min_weight, max_weight) for _ in range(n)]


# === 便捷函数 ===

def equal_weight(returns: pd.DataFrame) -> dict[str, float]:
    """等权重分配"""
    optimizer = WeightOptimizer(method=OptimizationMethod.EQUAL)
    result = optimizer.optimize(returns)
    return result.weights


def risk_parity(returns: pd.DataFrame) -> dict[str, float]:
    """风险平价分配"""
    optimizer = WeightOptimizer(method=OptimizationMethod.RISK_PARITY)
    result = optimizer.optimize(returns)
    return result.weights


def min_variance(
    returns: pd.DataFrame,
    max_weight: float = 0.1,
) -> dict[str, float]:
    """最小方差组合"""
    optimizer = WeightOptimizer(method=OptimizationMethod.MIN_VARIANCE)
    result = optimizer.optimize(returns, constraints={"max_weight": max_weight})
    return result.weights


def max_sharpe(
    returns: pd.DataFrame,
    risk_free_rate: float = 0.0,
    max_weight: float = 0.1,
) -> dict[str, float]:
    """最大夏普组合"""
    optimizer = WeightOptimizer(
        method=OptimizationMethod.MAX_SHARPE,
        risk_free_rate=risk_free_rate,
    )
    result = optimizer.optimize(returns, constraints={"max_weight": max_weight})
    return result.weights
