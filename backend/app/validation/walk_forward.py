"""
Walk-Forward 分析器

提供:
- 滚动窗口优化
- 样本内/外划分
- Walk-Forward 效率评估
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


class WindowType(str, Enum):
    """窗口类型"""
    ROLLING = "rolling"         # 滚动窗口 (固定长度)
    EXPANDING = "expanding"     # 扩展窗口 (累积)
    ANCHORED = "anchored"       # 锚定窗口 (固定起点)


@dataclass
class WalkForwardWindow:
    """Walk-Forward 窗口"""
    window_id: int
    is_start: date
    is_end: date                    # 样本内结束
    oos_start: date                 # 样本外开始
    oos_end: date
    is_size: int                    # 样本内天数
    oos_size: int                   # 样本外天数


@dataclass
class WalkForwardFold:
    """单个 Fold 结果"""
    window: WalkForwardWindow
    is_sharpe: float = 0.0          # 样本内夏普
    oos_sharpe: float = 0.0         # 样本外夏普
    is_return: float = 0.0          # 样本内收益
    oos_return: float = 0.0         # 样本外收益
    efficiency: float = 0.0         # WF 效率
    optimal_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class WalkForwardResult:
    """Walk-Forward 分析结果"""
    folds: list[WalkForwardFold] = field(default_factory=list)
    avg_is_sharpe: float = 0.0
    avg_oos_sharpe: float = 0.0
    wf_efficiency: float = 0.0      # Walk-Forward 效率
    total_oos_return: float = 0.0
    total_oos_sharpe: float = 0.0
    is_oos_correlation: float = 0.0 # 样本内外相关性
    stability_score: float = 0.0    # 稳定性分数
    n_profitable_folds: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class WalkForwardAnalyzer:
    """
    Walk-Forward 分析器

    执行滚动优化和样本外验证:
    1. 将数据分成多个训练/测试窗口
    2. 在每个训练窗口优化参数
    3. 在测试窗口评估性能
    4. 汇总分析结果
    """

    def __init__(
        self,
        window_type: WindowType = WindowType.ROLLING,
        is_periods: int = 252,      # 样本内期数 (1年)
        oos_periods: int = 63,      # 样本外期数 (1季度)
        step_size: int | None = None,  # 步长 (默认等于 oos_periods)
        min_is_periods: int = 126,  # 最小样本内期数
    ):
        """
        Args:
            window_type: 窗口类型
            is_periods: 样本内期数
            oos_periods: 样本外期数
            step_size: 窗口移动步长
            min_is_periods: 最小样本内期数 (用于 expanding)
        """
        self.window_type = window_type
        self.is_periods = is_periods
        self.oos_periods = oos_periods
        self.step_size = step_size or oos_periods
        self.min_is_periods = min_is_periods

    def create_windows(
        self,
        dates: pd.DatetimeIndex,
    ) -> list[WalkForwardWindow]:
        """
        创建 Walk-Forward 窗口

        Args:
            dates: 日期索引

        Returns:
            窗口列表
        """
        n = len(dates)
        windows = []
        window_id = 0

        if self.window_type == WindowType.ROLLING:
            # 滚动窗口
            start = 0
            while start + self.is_periods + self.oos_periods <= n:
                is_end = start + self.is_periods
                oos_end = is_end + self.oos_periods

                window = WalkForwardWindow(
                    window_id=window_id,
                    is_start=dates[start].date(),
                    is_end=dates[is_end - 1].date(),
                    oos_start=dates[is_end].date(),
                    oos_end=dates[oos_end - 1].date(),
                    is_size=self.is_periods,
                    oos_size=self.oos_periods,
                )
                windows.append(window)
                window_id += 1
                start += self.step_size

        elif self.window_type == WindowType.EXPANDING:
            # 扩展窗口
            start = 0
            is_end = self.min_is_periods
            while is_end + self.oos_periods <= n:
                oos_end = is_end + self.oos_periods

                window = WalkForwardWindow(
                    window_id=window_id,
                    is_start=dates[start].date(),
                    is_end=dates[is_end - 1].date(),
                    oos_start=dates[is_end].date(),
                    oos_end=dates[oos_end - 1].date(),
                    is_size=is_end,
                    oos_size=self.oos_periods,
                )
                windows.append(window)
                window_id += 1
                is_end += self.step_size

        elif self.window_type == WindowType.ANCHORED:
            # 锚定窗口 (固定起点，扩展训练集)
            start = 0
            is_end = self.is_periods
            while is_end + self.oos_periods <= n:
                oos_end = is_end + self.oos_periods

                window = WalkForwardWindow(
                    window_id=window_id,
                    is_start=dates[start].date(),
                    is_end=dates[is_end - 1].date(),
                    oos_start=dates[is_end].date(),
                    oos_end=dates[oos_end - 1].date(),
                    is_size=is_end - start,
                    oos_size=self.oos_periods,
                )
                windows.append(window)
                window_id += 1
                is_end += self.step_size

        logger.info(
            "创建 Walk-Forward 窗口",
            window_type=self.window_type.value,
            n_windows=len(windows),
            total_periods=n,
        )

        return windows

    def run(
        self,
        returns: pd.Series | pd.DataFrame,
        optimize_func: Callable[[pd.DataFrame, dict], dict] | None = None,
        evaluate_func: Callable[[pd.DataFrame, dict], float] | None = None,
        param_grid: dict[str, list] | None = None,
    ) -> WalkForwardResult:
        """
        运行 Walk-Forward 分析

        Args:
            returns: 收益数据
            optimize_func: 优化函数 (训练数据, 参数) -> 最优参数
            evaluate_func: 评估函数 (测试数据, 参数) -> 夏普比率
            param_grid: 参数网格

        Returns:
            分析结果
        """
        if isinstance(returns, pd.Series):
            returns = returns.to_frame("returns")

        dates = returns.index
        windows = self.create_windows(dates)

        if not windows:
            logger.warning("无法创建足够的 Walk-Forward 窗口")
            return WalkForwardResult()

        result = WalkForwardResult()
        is_sharpes = []
        oos_sharpes = []
        oos_returns_list = []

        for window in windows:
            # 提取样本内/外数据
            is_mask = (dates >= pd.Timestamp(window.is_start)) & (dates <= pd.Timestamp(window.is_end))
            oos_mask = (dates >= pd.Timestamp(window.oos_start)) & (dates <= pd.Timestamp(window.oos_end))

            is_data = returns[is_mask]
            oos_data = returns[oos_mask]

            # 优化
            if optimize_func and param_grid:
                optimal_params = optimize_func(is_data, param_grid)
            else:
                optimal_params = {}

            # 评估样本内
            is_sharpe = self._calculate_sharpe(is_data)

            # 评估样本外
            if evaluate_func:
                oos_sharpe = evaluate_func(oos_data, optimal_params)
            else:
                oos_sharpe = self._calculate_sharpe(oos_data)

            is_return = float(is_data.sum().iloc[0]) if not is_data.empty else 0.0
            oos_return = float(oos_data.sum().iloc[0]) if not oos_data.empty else 0.0

            # 计算效率
            efficiency = oos_sharpe / is_sharpe if is_sharpe > 0 else 0.0

            fold = WalkForwardFold(
                window=window,
                is_sharpe=is_sharpe,
                oos_sharpe=oos_sharpe,
                is_return=is_return,
                oos_return=oos_return,
                efficiency=efficiency,
                optimal_params=optimal_params,
            )
            result.folds.append(fold)

            is_sharpes.append(is_sharpe)
            oos_sharpes.append(oos_sharpe)
            oos_returns_list.append(oos_return)

            if oos_return > 0:
                result.n_profitable_folds += 1

        # 汇总统计
        if is_sharpes:
            result.avg_is_sharpe = float(np.mean(is_sharpes))
            result.avg_oos_sharpe = float(np.mean(oos_sharpes))
            result.wf_efficiency = result.avg_oos_sharpe / result.avg_is_sharpe if result.avg_is_sharpe > 0 else 0.0
            result.total_oos_return = float(sum(oos_returns_list))

            # 计算样本内外相关性
            if len(is_sharpes) > 2:
                corr = np.corrcoef(is_sharpes, oos_sharpes)[0, 1]
                result.is_oos_correlation = float(corr) if not np.isnan(corr) else 0.0

            # 稳定性分数 (基于 OOS 夏普的变异系数)
            if np.mean(oos_sharpes) != 0:
                cv = np.std(oos_sharpes) / abs(np.mean(oos_sharpes))
                result.stability_score = max(0, 1 - cv)

            # 计算总体 OOS 夏普
            all_oos_returns = []
            for fold in result.folds:
                window = fold.window
                oos_mask = (dates >= pd.Timestamp(window.oos_start)) & (dates <= pd.Timestamp(window.oos_end))
                all_oos_returns.extend(returns[oos_mask].values.flatten())

            if all_oos_returns:
                oos_series = pd.Series(all_oos_returns)
                result.total_oos_sharpe = self._calculate_sharpe(oos_series.to_frame())

        logger.info(
            "Walk-Forward 分析完成",
            n_folds=len(result.folds),
            avg_is_sharpe=f"{result.avg_is_sharpe:.2f}",
            avg_oos_sharpe=f"{result.avg_oos_sharpe:.2f}",
            wf_efficiency=f"{result.wf_efficiency:.1%}",
            profitable_folds=f"{result.n_profitable_folds}/{len(result.folds)}",
        )

        return result

    def _calculate_sharpe(self, returns: pd.DataFrame) -> float:
        """计算夏普比率"""
        if returns.empty:
            return 0.0

        ret = returns.iloc[:, 0] if isinstance(returns, pd.DataFrame) else returns
        if len(ret) < 2 or ret.std() == 0:
            return 0.0

        return float(ret.mean() / ret.std() * np.sqrt(252))


class SampleSplitter:
    """
    样本划分器

    提供多种样本内/外划分方法
    """

    @staticmethod
    def holdout_split(
        data: pd.DataFrame,
        test_ratio: float = 0.3,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        简单 Holdout 划分

        Args:
            data: 数据
            test_ratio: 测试集比例

        Returns:
            (训练集, 测试集)
        """
        n = len(data)
        split_idx = int(n * (1 - test_ratio))

        train = data.iloc[:split_idx]
        test = data.iloc[split_idx:]

        return train, test

    @staticmethod
    def purged_kfold(
        data: pd.DataFrame,
        n_folds: int = 5,
        embargo_periods: int = 5,
    ) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Purged K-Fold 划分

        使用 embargo 期避免信息泄露

        Args:
            data: 数据
            n_folds: 折数
            embargo_periods: 禁运期

        Returns:
            (训练集, 测试集) 列表
        """
        n = len(data)
        fold_size = n // n_folds
        folds = []

        for i in range(n_folds):
            test_start = i * fold_size
            test_end = test_start + fold_size if i < n_folds - 1 else n

            # 训练集: 排除测试集和 embargo 期
            train_end = max(0, test_start - embargo_periods)
            train_start_after = min(n, test_end + embargo_periods)

            train_indices = list(range(0, train_end)) + list(range(train_start_after, n))
            test_indices = list(range(test_start, test_end))

            if train_indices and test_indices:
                train = data.iloc[train_indices]
                test = data.iloc[test_indices]
                folds.append((train, test))

        return folds

    @staticmethod
    def combinatorial_purged_cv(
        data: pd.DataFrame,
        n_splits: int = 6,
        n_test_splits: int = 2,
        embargo_periods: int = 5,
    ) -> list[tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Combinatorial Purged Cross-Validation

        Lopez de Prado 的 CPCV 方法

        Args:
            data: 数据
            n_splits: 总分割数
            n_test_splits: 每次测试使用的分割数
            embargo_periods: 禁运期

        Returns:
            (训练集, 测试集) 列表
        """
        from itertools import combinations

        n = len(data)
        split_size = n // n_splits
        folds = []

        # 生成所有可能的测试分割组合
        test_combos = list(combinations(range(n_splits), n_test_splits))

        for test_splits in test_combos:
            test_indices = []
            for split_idx in test_splits:
                start = split_idx * split_size
                end = start + split_size if split_idx < n_splits - 1 else n
                test_indices.extend(range(start, end))

            # 排除测试索引和 embargo 期
            excluded = set(test_indices)
            for idx in test_indices:
                for e in range(1, embargo_periods + 1):
                    excluded.add(idx - e)
                    excluded.add(idx + e)

            train_indices = [i for i in range(n) if i not in excluded]

            if train_indices and test_indices:
                train = data.iloc[train_indices]
                test = data.iloc[test_indices]
                folds.append((train, test))

        return folds


def walk_forward_efficiency(is_sharpe: float, oos_sharpe: float) -> float:
    """
    计算 Walk-Forward 效率

    效率 = OOS Sharpe / IS Sharpe
    效率 > 0.5 通常认为是可接受的

    Args:
        is_sharpe: 样本内夏普
        oos_sharpe: 样本外夏普

    Returns:
        效率值
    """
    if is_sharpe <= 0:
        return 0.0
    return float(oos_sharpe / is_sharpe)
