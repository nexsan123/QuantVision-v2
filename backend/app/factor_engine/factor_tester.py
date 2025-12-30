"""
因子检验模块

提供因子有效性检验:
- IC 分析 (信息系数)
- 分组回测
- 因子衰减分析
"""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy import stats

logger = structlog.get_logger()


@dataclass
class ICAnalysisResult:
    """IC 分析结果"""

    # 基础统计
    ic_mean: float = 0.0           # IC 均值
    ic_std: float = 0.0            # IC 标准差
    ic_ir: float = 0.0             # IC 信息比率 (IC_mean / IC_std)
    rank_ic_mean: float = 0.0      # Rank IC 均值
    rank_ic_std: float = 0.0       # Rank IC 标准差
    rank_ic_ir: float = 0.0        # Rank IC 信息比率

    # 显著性检验
    t_statistic: float = 0.0       # t 统计量
    p_value: float = 1.0           # p 值

    # 稳定性指标
    ic_positive_ratio: float = 0.0 # IC > 0 的比例
    ic_abs_gt_2_ratio: float = 0.0 # |IC| > 0.02 的比例

    # 时间序列
    ic_series: pd.Series = field(default_factory=pd.Series)
    rank_ic_series: pd.Series = field(default_factory=pd.Series)

    # 衰减分析
    ic_decay: list[float] = field(default_factory=list)  # 不同持有期的 IC

    def is_significant(self, alpha: float = 0.05) -> bool:
        """判断因子是否统计显著"""
        return self.p_value < alpha

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "ic_mean": self.ic_mean,
            "ic_std": self.ic_std,
            "ic_ir": self.ic_ir,
            "rank_ic_mean": self.rank_ic_mean,
            "rank_ic_std": self.rank_ic_std,
            "rank_ic_ir": self.rank_ic_ir,
            "t_statistic": self.t_statistic,
            "p_value": self.p_value,
            "ic_positive_ratio": self.ic_positive_ratio,
            "ic_abs_gt_2_ratio": self.ic_abs_gt_2_ratio,
            "is_significant": self.is_significant(),
        }


@dataclass
class GroupBacktestResult:
    """分组回测结果"""

    # 分组收益
    group_returns: pd.DataFrame = field(default_factory=pd.DataFrame)
    cumulative_returns: pd.DataFrame = field(default_factory=pd.DataFrame)

    # 单调性
    monotonicity: float = 0.0      # 收益单调性 (-1 到 1)
    long_short_return: float = 0.0 # 多空组合年化收益
    long_short_sharpe: float = 0.0 # 多空组合夏普比率

    # 各分组统计
    group_stats: dict[str, dict[str, float]] = field(default_factory=dict)


class FactorTester:
    """
    因子检验器

    提供:
    1. IC 分析: 因子值与未来收益的相关性
    2. 分组回测: 按因子值分组的收益表现
    3. 衰减分析: 因子在不同持有期的有效性
    """

    def __init__(
        self,
        n_groups: int = 10,
        holding_periods: list[int] | None = None,
    ):
        """
        Args:
            n_groups: 分组数量
            holding_periods: 衰减分析的持有期列表
        """
        self.n_groups = n_groups
        self.holding_periods = holding_periods or [1, 5, 10, 20]

    def analyze_ic(
        self,
        factor: pd.DataFrame,
        returns: pd.DataFrame,
        method: str = "pearson",
    ) -> ICAnalysisResult:
        """
        IC 分析

        计算因子值与未来收益的相关系数

        Args:
            factor: 因子值 DataFrame (index=date, columns=symbols)
            returns: 未来收益 DataFrame (同结构)
            method: 相关系数方法 ('pearson' 或 'spearman')

        Returns:
            IC 分析结果
        """
        result = ICAnalysisResult()

        # 对齐数据
        common_dates = factor.index.intersection(returns.index)
        common_symbols = factor.columns.intersection(returns.columns)

        factor = factor.loc[common_dates, common_symbols]
        returns = returns.loc[common_dates, common_symbols]

        # 计算每日 IC
        ic_list = []
        rank_ic_list = []

        for dt in common_dates:
            f = factor.loc[dt].dropna()
            r = returns.loc[dt].dropna()

            common = f.index.intersection(r.index)
            if len(common) < 10:
                continue

            f = f[common]
            r = r[common]

            # Pearson IC
            if method == "pearson":
                ic = f.corr(r)
            else:
                ic = f.corr(r, method="spearman")

            # Rank IC (Spearman)
            rank_ic = f.corr(r, method="spearman")

            if not np.isnan(ic):
                ic_list.append((dt, ic))
            if not np.isnan(rank_ic):
                rank_ic_list.append((dt, rank_ic))

        if not ic_list:
            logger.warning("IC 分析失败: 没有有效数据")
            return result

        # 转换为 Series
        result.ic_series = pd.Series(dict(ic_list))
        result.rank_ic_series = pd.Series(dict(rank_ic_list))

        # 基础统计
        result.ic_mean = result.ic_series.mean()
        result.ic_std = result.ic_series.std()
        result.ic_ir = result.ic_mean / result.ic_std if result.ic_std > 0 else 0

        result.rank_ic_mean = result.rank_ic_series.mean()
        result.rank_ic_std = result.rank_ic_series.std()
        result.rank_ic_ir = result.rank_ic_mean / result.rank_ic_std if result.rank_ic_std > 0 else 0

        # t 检验
        n = len(result.ic_series)
        if n > 1 and result.ic_std > 0:
            result.t_statistic = result.ic_mean / (result.ic_std / np.sqrt(n))
            result.p_value = 2 * (1 - stats.t.cdf(abs(result.t_statistic), n - 1))
        else:
            result.t_statistic = 0
            result.p_value = 1.0

        # 稳定性指标
        result.ic_positive_ratio = (result.ic_series > 0).mean()
        result.ic_abs_gt_2_ratio = (result.ic_series.abs() > 0.02).mean()

        # 衰减分析
        result.ic_decay = self._analyze_ic_decay(factor, returns)

        logger.info(
            "IC 分析完成",
            ic_mean=f"{result.ic_mean:.4f}",
            ic_ir=f"{result.ic_ir:.4f}",
            t_stat=f"{result.t_statistic:.2f}",
            p_value=f"{result.p_value:.4f}",
        )

        return result

    def _analyze_ic_decay(
        self,
        factor: pd.DataFrame,
        returns: pd.DataFrame,
    ) -> list[float]:
        """分析 IC 衰减"""
        decay = []

        for period in self.holding_periods:
            # 计算不同持有期的收益
            period_returns = returns.rolling(period).sum().shift(-period)

            ic_list = []
            for dt in factor.index:
                if dt not in period_returns.index:
                    continue

                f = factor.loc[dt].dropna()
                r = period_returns.loc[dt].dropna()

                common = f.index.intersection(r.index)
                if len(common) < 10:
                    continue

                ic = f[common].corr(r[common])
                if not np.isnan(ic):
                    ic_list.append(ic)

            if ic_list:
                decay.append(np.mean(ic_list))
            else:
                decay.append(0.0)

        return decay

    def group_backtest(
        self,
        factor: pd.DataFrame,
        returns: pd.DataFrame,
    ) -> GroupBacktestResult:
        """
        分组回测

        按因子值分组，计算各组收益表现

        Args:
            factor: 因子值 DataFrame
            returns: 未来收益 DataFrame

        Returns:
            分组回测结果
        """
        result = GroupBacktestResult()

        # 对齐数据
        common_dates = factor.index.intersection(returns.index)
        common_symbols = factor.columns.intersection(returns.columns)

        factor = factor.loc[common_dates, common_symbols]
        returns = returns.loc[common_dates, common_symbols]

        # 分组标签
        group_returns_list = []

        for dt in common_dates:
            f = factor.loc[dt].dropna()
            r = returns.loc[dt].dropna()

            common = f.index.intersection(r.index)
            if len(common) < self.n_groups:
                continue

            f = f[common]
            r = r[common]

            # 分组
            groups = pd.qcut(f, self.n_groups, labels=False, duplicates="drop")

            # 计算各组平均收益
            group_ret = {}
            for g in range(self.n_groups):
                mask = groups == g
                if mask.sum() > 0:
                    group_ret[f"G{g+1}"] = r[mask].mean()

            if group_ret:
                group_returns_list.append(pd.Series(group_ret, name=dt))

        if not group_returns_list:
            logger.warning("分组回测失败: 没有有效数据")
            return result

        # 汇总
        result.group_returns = pd.DataFrame(group_returns_list)
        result.cumulative_returns = (1 + result.group_returns).cumprod() - 1

        # 多空收益 (第一组 - 最后一组)
        if "G1" in result.group_returns.columns and f"G{self.n_groups}" in result.group_returns.columns:
            long_short = result.group_returns[f"G{self.n_groups}"] - result.group_returns["G1"]
            result.long_short_return = long_short.mean() * 252  # 年化
            result.long_short_sharpe = (
                long_short.mean() / long_short.std() * np.sqrt(252)
                if long_short.std() > 0 else 0
            )

        # 单调性 (用 Spearman 相关)
        avg_returns = result.group_returns.mean()
        group_idx = np.arange(len(avg_returns))
        result.monotonicity = stats.spearmanr(group_idx, avg_returns.values)[0]

        # 各组统计
        for col in result.group_returns.columns:
            g_ret = result.group_returns[col]
            result.group_stats[col] = {
                "mean": g_ret.mean() * 252,
                "std": g_ret.std() * np.sqrt(252),
                "sharpe": g_ret.mean() / g_ret.std() * np.sqrt(252) if g_ret.std() > 0 else 0,
                "win_rate": (g_ret > 0).mean(),
            }

        logger.info(
            "分组回测完成",
            monotonicity=f"{result.monotonicity:.4f}",
            long_short_return=f"{result.long_short_return:.2%}",
            long_short_sharpe=f"{result.long_short_sharpe:.2f}",
        )

        return result
