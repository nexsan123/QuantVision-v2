"""
Phase 10: 风险因子模型服务

简化版 Barra 风险模型实现:
- 8个风格因子
- 11个行业因子
- 风险分解
- 因子协方差矩阵
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy import stats

logger = structlog.get_logger()


# ============ 风格因子定义 ============

STYLE_FACTORS = [
    "size",       # 市值因子 - ln(市值)
    "value",      # 价值因子 - BP, EP
    "momentum",   # 动量因子 - 12-1个月收益率
    "volatility", # 波动因子 - 252日波动率
    "quality",    # 质量因子 - ROE, 资产周转率
    "growth",     # 成长因子 - 营收增长率
    "liquidity",  # 流动因子 - 换手率
    "leverage",   # 杠杆因子 - 资产负债率
]

# GICS 一级行业
INDUSTRY_FACTORS = [
    "communication_services",
    "consumer_discretionary",
    "consumer_staples",
    "energy",
    "financials",
    "healthcare",
    "industrials",
    "information_technology",
    "materials",
    "real_estate",
    "utilities",
]

# 行业中文标签
INDUSTRY_LABELS = {
    "communication_services": "通讯服务",
    "consumer_discretionary": "非必需消费",
    "consumer_staples": "必需消费",
    "energy": "能源",
    "financials": "金融",
    "healthcare": "医疗",
    "industrials": "工业",
    "information_technology": "信息技术",
    "materials": "材料",
    "real_estate": "房地产",
    "utilities": "公用事业",
}

# 风格因子中文标签
STYLE_LABELS = {
    "size": "市值",
    "value": "价值",
    "momentum": "动量",
    "volatility": "波动",
    "quality": "质量",
    "growth": "成长",
    "liquidity": "流动性",
    "leverage": "杠杆",
}


@dataclass
class FactorReturn:
    """因子收益"""
    factor: str
    mean_return: float      # 平均收益 (日)
    volatility: float       # 波动率 (年化)
    sharpe: float           # 夏普比率
    t_stat: float           # t统计量


@dataclass
class RiskDecomposition:
    """风险分解结果"""
    total_risk: float                           # 总风险 (年化)
    market_risk: float = 0.0                    # 市场风险
    style_risk: float = 0.0                     # 风格风险
    industry_risk: float = 0.0                  # 行业风险
    specific_risk: float = 0.0                  # 特质风险

    # 贡献比例
    market_contribution: float = 0.0
    style_contribution: float = 0.0
    industry_contribution: float = 0.0
    specific_contribution: float = 0.0

    # 详细分解
    style_details: dict[str, float] = field(default_factory=dict)
    industry_details: dict[str, float] = field(default_factory=dict)

    # 因子暴露
    market_beta: float = 1.0
    style_exposures: dict[str, float] = field(default_factory=dict)
    industry_exposures: dict[str, float] = field(default_factory=dict)

    # 模型统计
    r_squared: float = 0.0
    tracking_error: float = 0.0


class RiskFactorModel:
    """
    简化版 Barra 风险因子模型

    股票收益 = 市场因子 + 风格因子 + 行业因子 + 特质收益
    Ri = β_mkt * R_mkt + Σ(β_style * R_style) + Σ(β_ind * R_ind) + εi

    使用示例:
    ```python
    model = RiskFactorModel()

    # 计算风险分解
    decomposition = model.decompose_risk(
        holdings={"AAPL": 0.3, "GOOGL": 0.3, "JPM": 0.4},
        asset_returns=returns_df,
        factor_returns=factor_df,
    )

    print(f"总风险: {decomposition.total_risk:.2%}")
    print(f"市场贡献: {decomposition.market_contribution:.1%}")
    ```
    """

    def __init__(
        self,
        risk_free_rate: float = 0.02,
        min_history: int = 60,
    ):
        """
        Args:
            risk_free_rate: 无风险利率 (年化)
            min_history: 最小历史数据天数
        """
        self.risk_free_rate = risk_free_rate / 252  # 日化
        self.min_history = min_history

        # 因子协方差矩阵 (模拟数据)
        self._factor_cov = None

    def decompose_risk(
        self,
        holdings: dict[str, float],
        asset_returns: pd.DataFrame | None = None,
        factor_returns: pd.DataFrame | None = None,
        asset_betas: dict[str, float] | None = None,
        asset_industries: dict[str, str] | None = None,
        asset_style_exposures: dict[str, dict[str, float]] | None = None,
    ) -> RiskDecomposition:
        """
        计算组合风险分解

        Args:
            holdings: 持仓权重 {symbol: weight}
            asset_returns: 资产收益率 DataFrame
            factor_returns: 因子收益率 DataFrame
            asset_betas: 资产 Beta {symbol: beta}
            asset_industries: 资产行业 {symbol: industry}
            asset_style_exposures: 资产风格暴露 {symbol: {factor: exposure}}

        Returns:
            风险分解结果
        """
        # 使用模拟数据或真实数据
        if asset_returns is not None and len(asset_returns) >= self.min_history:
            return self._decompose_with_data(
                holdings, asset_returns, factor_returns
            )
        else:
            return self._decompose_with_exposures(
                holdings, asset_betas, asset_industries, asset_style_exposures
            )

    def _decompose_with_exposures(
        self,
        holdings: dict[str, float],
        asset_betas: dict[str, float] | None = None,
        asset_industries: dict[str, str] | None = None,
        asset_style_exposures: dict[str, dict[str, float]] | None = None,
    ) -> RiskDecomposition:
        """使用暴露数据进行风险分解 (模拟)"""
        asset_betas = asset_betas or {}
        asset_industries = asset_industries or {}
        asset_style_exposures = asset_style_exposures or {}

        # 计算组合 Beta
        portfolio_beta = sum(
            weight * asset_betas.get(symbol, 1.0)
            for symbol, weight in holdings.items()
        )

        # 计算行业暴露
        industry_exposures = {}
        for symbol, weight in holdings.items():
            industry = asset_industries.get(symbol, "information_technology")
            industry_exposures[industry] = industry_exposures.get(industry, 0) + weight

        # 计算风格暴露 (简化: 使用模拟数据)
        style_exposures = {f: 0.0 for f in STYLE_FACTORS}
        for symbol, weight in holdings.items():
            if symbol in asset_style_exposures:
                for factor, exp in asset_style_exposures[symbol].items():
                    if factor in style_exposures:
                        style_exposures[factor] += weight * exp
            else:
                # 模拟暴露
                style_exposures["size"] += weight * np.random.uniform(-0.5, 0.5)
                style_exposures["momentum"] += weight * np.random.uniform(-0.3, 0.3)

        # 模拟风险分解
        base_vol = 0.18  # 基准波动率

        market_var = (portfolio_beta ** 2) * (0.16 ** 2)  # 市场波动约 16%
        style_var = sum(exp ** 2 * 0.02 for exp in style_exposures.values())
        industry_var = sum(exp ** 2 * 0.08 for exp in industry_exposures.values())
        specific_var = 0.12 ** 2 * (1 - max(holdings.values()) ** 2)  # 特质风险

        total_var = market_var + style_var + industry_var + specific_var
        total_risk = np.sqrt(total_var) * np.sqrt(252)

        # 风格风险详情
        style_details = {
            f: (style_exposures[f] ** 2 * 0.02 / total_var * 100) if total_var > 0 else 0
            for f in STYLE_FACTORS
        }

        # 行业风险详情
        industry_details = {
            ind: (exp ** 2 * 0.08 / total_var * 100) if total_var > 0 else 0
            for ind, exp in industry_exposures.items()
        }

        return RiskDecomposition(
            total_risk=total_risk,
            market_risk=np.sqrt(market_var) * np.sqrt(252),
            style_risk=np.sqrt(style_var) * np.sqrt(252),
            industry_risk=np.sqrt(industry_var) * np.sqrt(252),
            specific_risk=np.sqrt(specific_var) * np.sqrt(252),
            market_contribution=market_var / total_var * 100 if total_var > 0 else 0,
            style_contribution=style_var / total_var * 100 if total_var > 0 else 0,
            industry_contribution=industry_var / total_var * 100 if total_var > 0 else 0,
            specific_contribution=specific_var / total_var * 100 if total_var > 0 else 0,
            style_details=style_details,
            industry_details=industry_details,
            market_beta=portfolio_beta,
            style_exposures=style_exposures,
            industry_exposures=industry_exposures,
            r_squared=0.85,  # 模拟
            tracking_error=0.05,
        )

    def _decompose_with_data(
        self,
        holdings: dict[str, float],
        asset_returns: pd.DataFrame,
        factor_returns: pd.DataFrame | None = None,
    ) -> RiskDecomposition:
        """使用历史数据进行风险分解"""
        # 计算组合收益
        portfolio_returns = pd.Series(0.0, index=asset_returns.index)
        for symbol, weight in holdings.items():
            if symbol in asset_returns.columns:
                portfolio_returns += weight * asset_returns[symbol]

        if factor_returns is None:
            # 生成模拟因子收益
            factor_returns = self._generate_mock_factor_returns(len(portfolio_returns))
            factor_returns.index = portfolio_returns.index

        # 回归分析
        common_idx = portfolio_returns.index.intersection(factor_returns.index)
        y = portfolio_returns.loc[common_idx].values
        X = factor_returns.loc[common_idx].values

        # 添加常数项
        X_with_const = np.column_stack([np.ones(len(X)), X])

        try:
            beta, residuals, rank, s = np.linalg.lstsq(X_with_const, y, rcond=None)
        except np.linalg.LinAlgError:
            return self._decompose_with_exposures(holdings)

        # 计算 R²
        y_hat = X_with_const @ beta
        ss_res = np.sum((y - y_hat) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # 残差风险
        residuals = y - y_hat
        specific_risk = np.std(residuals) * np.sqrt(252)

        # 总风险
        total_risk = np.std(y) * np.sqrt(252)

        # 因子风险
        factor_risk = np.sqrt(max(0, total_risk ** 2 - specific_risk ** 2))

        # 简化分解
        market_beta = beta[1] if len(beta) > 1 else 1.0
        market_risk = abs(market_beta) * 0.16  # 假设市场波动 16%

        return RiskDecomposition(
            total_risk=total_risk,
            market_risk=market_risk,
            style_risk=factor_risk * 0.3,
            industry_risk=factor_risk * 0.2,
            specific_risk=specific_risk,
            market_contribution=45,
            style_contribution=20,
            industry_contribution=15,
            specific_contribution=20,
            market_beta=market_beta,
            r_squared=r_squared,
            tracking_error=np.std(y - X[:, 0] if X.shape[1] > 0 else y) * np.sqrt(252),
        )

    def _generate_mock_factor_returns(self, n_days: int) -> pd.DataFrame:
        """生成模拟因子收益"""
        np.random.seed(42)

        factors = ["market"] + STYLE_FACTORS[:4]  # 简化: 使用部分因子

        # 因子相关性矩阵
        n_factors = len(factors)
        corr = np.eye(n_factors)
        corr[0, 1:] = 0.3  # 市场与其他因子相关
        corr[1:, 0] = 0.3

        # 生成相关因子收益
        cov = np.outer(np.ones(n_factors) * 0.01, np.ones(n_factors) * 0.01) * corr
        returns = np.random.multivariate_normal(
            mean=np.zeros(n_factors),
            cov=cov,
            size=n_days,
        )

        return pd.DataFrame(returns, columns=factors)

    def calculate_factor_covariance(
        self,
        factor_returns: pd.DataFrame,
        method: str = "sample",
        shrinkage: float = 0.2,
    ) -> pd.DataFrame:
        """
        计算因子协方差矩阵

        Args:
            factor_returns: 因子收益
            method: 计算方法 (sample, shrinkage, ewma)
            shrinkage: 收缩系数

        Returns:
            协方差矩阵
        """
        if method == "sample":
            return factor_returns.cov() * 252

        elif method == "shrinkage":
            sample_cov = factor_returns.cov()
            # Ledoit-Wolf 收缩
            target = np.diag(np.diag(sample_cov))
            shrunk = (1 - shrinkage) * sample_cov + shrinkage * target
            return pd.DataFrame(
                shrunk * 252,
                index=sample_cov.index,
                columns=sample_cov.columns,
            )

        elif method == "ewma":
            # 指数加权
            lambda_param = 0.94
            n = len(factor_returns)
            weights = np.array([(1 - lambda_param) * lambda_param ** i for i in range(n)])
            weights = weights[::-1] / weights.sum()

            centered = factor_returns - factor_returns.mean()
            cov = np.zeros((factor_returns.shape[1], factor_returns.shape[1]))
            for i in range(n):
                cov += weights[i] * np.outer(centered.iloc[i], centered.iloc[i])

            return pd.DataFrame(
                cov * 252,
                index=factor_returns.columns,
                columns=factor_returns.columns,
            )

        else:
            raise ValueError(f"Unknown method: {method}")

    def calculate_marginal_risk(
        self,
        holdings: dict[str, float],
        asset_cov: pd.DataFrame,
    ) -> dict[str, float]:
        """
        计算边际风险贡献

        Args:
            holdings: 持仓权重
            asset_cov: 资产协方差矩阵

        Returns:
            各资产的边际风险贡献
        """
        symbols = list(holdings.keys())
        weights = np.array([holdings[s] for s in symbols])

        # 提取协方差子矩阵
        cov = asset_cov.loc[symbols, symbols].values

        # 组合方差
        portfolio_var = weights @ cov @ weights
        portfolio_vol = np.sqrt(portfolio_var)

        # 边际风险贡献
        marginal = cov @ weights / portfolio_vol

        # 风险贡献
        risk_contributions = weights * marginal / portfolio_vol

        return {
            symbols[i]: float(risk_contributions[i])
            for i in range(len(symbols))
        }


class RiskMonitorService:
    """
    实时风险监控服务
    """

    def __init__(self):
        self.alerts: list[dict] = []
        self.risk_limits = {
            "max_drawdown": 0.15,
            "max_var": 0.03,
            "max_volatility": 0.25,
            "max_industry_exposure": 0.25,
            "max_style_exposure": 0.5,
            "max_beta": 1.5,
        }

    def check_limits(
        self,
        current_metrics: dict[str, float],
        factor_exposures: dict[str, float] | None = None,
    ) -> list[dict]:
        """
        检查风险限制

        Returns:
            触发的警报列表
        """
        alerts = []

        # 检查回撤
        if current_metrics.get("drawdown", 0) > self.risk_limits["max_drawdown"]:
            alerts.append({
                "level": "critical",
                "type": "drawdown",
                "message": f"回撤超限: {current_metrics['drawdown']:.1%} > {self.risk_limits['max_drawdown']:.1%}",
                "current_value": current_metrics["drawdown"],
                "threshold": self.risk_limits["max_drawdown"],
            })
        elif current_metrics.get("drawdown", 0) > self.risk_limits["max_drawdown"] * 0.8:
            alerts.append({
                "level": "warning",
                "type": "drawdown",
                "message": f"回撤接近限制: {current_metrics['drawdown']:.1%}",
                "current_value": current_metrics["drawdown"],
                "threshold": self.risk_limits["max_drawdown"],
            })

        # 检查 VaR
        if current_metrics.get("var", 0) > self.risk_limits["max_var"]:
            alerts.append({
                "level": "critical",
                "type": "var",
                "message": f"VaR超限: {current_metrics['var']:.2%} > {self.risk_limits['max_var']:.2%}",
                "current_value": current_metrics["var"],
                "threshold": self.risk_limits["max_var"],
            })

        # 检查波动率
        if current_metrics.get("volatility", 0) > self.risk_limits["max_volatility"]:
            alerts.append({
                "level": "warning",
                "type": "volatility",
                "message": f"波动率过高: {current_metrics['volatility']:.1%}",
                "current_value": current_metrics["volatility"],
                "threshold": self.risk_limits["max_volatility"],
            })

        # 检查因子暴露
        if factor_exposures:
            for factor, exposure in factor_exposures.items():
                if abs(exposure) > self.risk_limits["max_style_exposure"]:
                    alerts.append({
                        "level": "warning",
                        "type": "factor_exposure",
                        "message": f"{STYLE_LABELS.get(factor, factor)}因子暴露过高: {exposure:.2f}",
                        "current_value": abs(exposure),
                        "threshold": self.risk_limits["max_style_exposure"],
                    })

        return alerts

    def calculate_risk_score(
        self,
        current_metrics: dict[str, float],
        alerts: list[dict],
    ) -> tuple[float, str]:
        """
        计算综合风险评分

        Returns:
            (risk_score, risk_level)
        """
        score = 0.0

        # 回撤贡献 (0-40分)
        dd = current_metrics.get("drawdown", 0)
        dd_pct = dd / self.risk_limits["max_drawdown"]
        score += min(40, dd_pct * 40)

        # VaR 贡献 (0-30分)
        var = current_metrics.get("var", 0)
        var_pct = var / self.risk_limits["max_var"]
        score += min(30, var_pct * 30)

        # 波动率贡献 (0-20分)
        vol = current_metrics.get("volatility", 0)
        vol_pct = vol / self.risk_limits["max_volatility"]
        score += min(20, vol_pct * 20)

        # 警报贡献 (0-10分)
        critical_count = sum(1 for a in alerts if a["level"] == "critical")
        warning_count = sum(1 for a in alerts if a["level"] == "warning")
        score += min(10, critical_count * 5 + warning_count * 2)

        # 确定风险等级
        if score >= 70:
            level = "critical"
        elif score >= 50:
            level = "high"
        elif score >= 30:
            level = "medium"
        else:
            level = "low"

        return min(100, score), level

    def update_limits(self, new_limits: dict[str, float]) -> None:
        """更新风险限制"""
        self.risk_limits.update(new_limits)
        logger.info("风险限制已更新", limits=self.risk_limits)
