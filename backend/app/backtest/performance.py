"""
绩效分析模块

提供:
- 收益分析
- 风险指标
- 归因分析
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy import stats

logger = structlog.get_logger()


@dataclass
class PerformanceMetrics:
    """绩效指标"""

    # 收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    monthly_return_avg: float = 0.0
    daily_return_avg: float = 0.0

    # 风险指标
    volatility: float = 0.0          # 年化波动率
    max_drawdown: float = 0.0        # 最大回撤
    avg_drawdown: float = 0.0        # 平均回撤
    drawdown_duration: int = 0       # 最大回撤持续天数

    # 风险调整收益
    sharpe_ratio: float = 0.0        # 夏普比率
    sortino_ratio: float = 0.0       # 索提诺比率
    calmar_ratio: float = 0.0        # 卡尔马比率
    information_ratio: float = 0.0   # 信息比率

    # 交易统计
    win_rate: float = 0.0            # 胜率
    profit_factor: float = 0.0       # 盈亏比
    avg_win: float = 0.0             # 平均盈利
    avg_loss: float = 0.0            # 平均亏损
    max_consecutive_wins: int = 0    # 最大连胜
    max_consecutive_losses: int = 0  # 最大连亏

    # 其他
    beta: float = 0.0                # 贝塔
    alpha: float = 0.0               # 阿尔法
    r_squared: float = 0.0           # R 平方

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "volatility": self.volatility,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "calmar_ratio": self.calmar_ratio,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "beta": self.beta,
            "alpha": self.alpha,
        }


class PerformanceAnalyzer:
    """
    绩效分析器

    计算各类绩效指标:
    - 收益分析
    - 风险分析
    - 归因分析
    """

    def __init__(
        self,
        risk_free_rate: float = 0.0,
        trading_days: int = 252,
    ):
        """
        Args:
            risk_free_rate: 无风险利率 (年化)
            trading_days: 每年交易日数
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days = trading_days

    def analyze(
        self,
        equity_curve: pd.Series,
        benchmark: pd.Series | None = None,
        trades: list[dict[str, Any]] | None = None,
    ) -> PerformanceMetrics:
        """
        完整绩效分析

        Args:
            equity_curve: 权益曲线
            benchmark: 基准曲线
            trades: 交易列表

        Returns:
            绩效指标
        """
        metrics = PerformanceMetrics()

        if len(equity_curve) < 2:
            return metrics

        # 收益率序列
        returns = equity_curve.pct_change().dropna()

        # 收益指标
        self._calculate_return_metrics(equity_curve, returns, metrics)

        # 风险指标
        self._calculate_risk_metrics(equity_curve, returns, metrics)

        # 风险调整收益
        self._calculate_risk_adjusted_metrics(returns, metrics)

        # 基准相关
        if benchmark is not None:
            self._calculate_benchmark_metrics(returns, benchmark, metrics)

        # 交易统计
        if trades:
            self._calculate_trade_metrics(trades, metrics)

        return metrics

    def _calculate_return_metrics(
        self,
        equity: pd.Series,
        returns: pd.Series,
        metrics: PerformanceMetrics,
    ) -> None:
        """计算收益指标"""
        # 总收益
        metrics.total_return = equity.iloc[-1] / equity.iloc[0] - 1

        # 年化收益
        days = (equity.index[-1] - equity.index[0]).days
        if days > 0:
            metrics.annual_return = (1 + metrics.total_return) ** (365 / days) - 1

        # 平均收益
        metrics.daily_return_avg = returns.mean()
        metrics.monthly_return_avg = equity.resample("M").last().pct_change().mean()

    def _calculate_risk_metrics(
        self,
        equity: pd.Series,
        returns: pd.Series,
        metrics: PerformanceMetrics,
    ) -> None:
        """计算风险指标"""
        # 年化波动率
        metrics.volatility = returns.std() * np.sqrt(self.trading_days)

        # 回撤分析
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax

        metrics.max_drawdown = abs(drawdown.min())
        metrics.avg_drawdown = abs(drawdown.mean())

        # 最大回撤持续时间
        in_drawdown = drawdown < 0
        if in_drawdown.any():
            drawdown_groups = (~in_drawdown).cumsum()
            drawdown_lengths = in_drawdown.groupby(drawdown_groups).sum()
            metrics.drawdown_duration = int(drawdown_lengths.max())

    def _calculate_risk_adjusted_metrics(
        self,
        returns: pd.Series,
        metrics: PerformanceMetrics,
    ) -> None:
        """计算风险调整收益"""
        daily_rf = self.risk_free_rate / self.trading_days
        excess_returns = returns - daily_rf

        # 夏普比率
        if returns.std() > 0:
            metrics.sharpe_ratio = (
                excess_returns.mean() / returns.std() * np.sqrt(self.trading_days)
            )

        # 索提诺比率 (只考虑下行风险)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            metrics.sortino_ratio = (
                excess_returns.mean() / downside_returns.std() * np.sqrt(self.trading_days)
            )

        # 卡尔马比率
        if metrics.max_drawdown > 0:
            metrics.calmar_ratio = metrics.annual_return / metrics.max_drawdown

    def _calculate_benchmark_metrics(
        self,
        returns: pd.Series,
        benchmark: pd.Series,
        metrics: PerformanceMetrics,
    ) -> None:
        """计算基准相关指标"""
        # 对齐数据
        benchmark_returns = benchmark.pct_change().dropna()
        common_idx = returns.index.intersection(benchmark_returns.index)

        if len(common_idx) < 10:
            return

        r = returns.loc[common_idx]
        b = benchmark_returns.loc[common_idx]

        # 回归分析
        slope, intercept, r_value, p_value, std_err = stats.linregress(b, r)

        metrics.beta = slope
        metrics.alpha = intercept * self.trading_days  # 年化
        metrics.r_squared = r_value ** 2

        # 信息比率
        tracking_error = (r - b).std() * np.sqrt(self.trading_days)
        if tracking_error > 0:
            excess_return = metrics.annual_return - (benchmark.iloc[-1] / benchmark.iloc[0] - 1)
            metrics.information_ratio = excess_return / tracking_error

    def _calculate_trade_metrics(
        self,
        trades: list[dict[str, Any]],
        metrics: PerformanceMetrics,
    ) -> None:
        """计算交易统计"""
        if not trades:
            return

        # 提取盈亏
        pnls = [t.get("pnl", 0) for t in trades if "pnl" in t]

        if not pnls:
            return

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]

        # 胜率
        metrics.win_rate = len(wins) / len(pnls) if pnls else 0

        # 盈亏比
        total_wins = sum(wins)
        total_losses = abs(sum(losses))
        if total_losses > 0:
            metrics.profit_factor = total_wins / total_losses

        # 平均盈亏
        metrics.avg_win = np.mean(wins) if wins else 0
        metrics.avg_loss = np.mean(losses) if losses else 0

        # 连续统计
        metrics.max_consecutive_wins = self._max_consecutive(pnls, lambda x: x > 0)
        metrics.max_consecutive_losses = self._max_consecutive(pnls, lambda x: x < 0)

    @staticmethod
    def _max_consecutive(values: list, condition) -> int:
        """计算最大连续满足条件的次数"""
        max_count = 0
        current_count = 0

        for v in values:
            if condition(v):
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        return max_count

    def calculate_monthly_returns(self, equity_curve: pd.Series) -> pd.DataFrame:
        """
        计算月度收益矩阵

        Returns:
            月度收益 DataFrame (行=年, 列=月)
        """
        monthly = equity_curve.resample("M").last().pct_change()

        # 创建年-月矩阵
        df = pd.DataFrame({
            "year": monthly.index.year,
            "month": monthly.index.month,
            "return": monthly.values,
        })

        pivot = df.pivot(index="year", columns="month", values="return")
        pivot.columns = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        return pivot

    def calculate_rolling_metrics(
        self,
        returns: pd.Series,
        window: int = 60,
    ) -> pd.DataFrame:
        """
        计算滚动指标

        Args:
            returns: 收益率序列
            window: 滚动窗口

        Returns:
            滚动指标 DataFrame
        """
        rolling_mean = returns.rolling(window).mean() * self.trading_days
        rolling_std = returns.rolling(window).std() * np.sqrt(self.trading_days)
        rolling_sharpe = rolling_mean / rolling_std

        # 滚动回撤
        cumret = (1 + returns).cumprod()
        rolling_max = cumret.rolling(window).max()
        rolling_dd = (cumret - rolling_max) / rolling_max

        return pd.DataFrame({
            "annual_return": rolling_mean,
            "volatility": rolling_std,
            "sharpe_ratio": rolling_sharpe,
            "max_drawdown": rolling_dd.rolling(window).min().abs(),
        })
