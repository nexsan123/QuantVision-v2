"""
Phase 9: Walk-Forward 验证引擎

实现滚动窗口样本外测试，检测策略过拟合风险
"""

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger()


@dataclass
class BacktestMetrics:
    """回测指标"""
    total_return: float = 0.0
    annual_return: float = 0.0
    volatility: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0


@dataclass
class WalkForwardRound:
    """Walk-Forward 单轮结果"""
    round_number: int
    train_start: date
    train_end: date
    test_start: date
    test_end: date
    optimized_params: dict[str, float]
    in_sample_metrics: BacktestMetrics
    out_of_sample_metrics: BacktestMetrics
    stability_ratio: float = 0.0


@dataclass
class WalkForwardConfig:
    """Walk-Forward 配置"""
    train_period: int = 36  # 训练期 (月)
    test_period: int = 12   # 测试期 (月)
    step_size: int = 12     # 滚动步长 (月)
    optimize_target: str = "sharpe"
    parameter_ranges: dict[str, list[float]] | None = None
    min_train_samples: int = 252
    expanding_window: bool = False


class WalkForwardEngine:
    """
    Walk-Forward 验证引擎

    实现滚动窗口验证，评估策略的真实样本外表现
    """

    def __init__(self, config: WalkForwardConfig):
        self.config = config
        self.rounds: list[WalkForwardRound] = []

    def calculate_windows(
        self,
        start_date: date,
        end_date: date
    ) -> list[tuple[date, date, date, date]]:
        """
        计算所有 Walk-Forward 窗口

        Returns:
            list of (train_start, train_end, test_start, test_end)
        """
        windows = []
        train_months = self.config.train_period
        test_months = self.config.test_period
        step_months = self.config.step_size

        current_date = start_date
        round_num = 0

        while True:
            # 计算训练期
            if self.config.expanding_window:
                train_start = start_date
            else:
                train_start = current_date

            train_end = self._add_months(train_start, train_months) - timedelta(days=1)

            # 计算测试期
            test_start = train_end + timedelta(days=1)
            test_end = self._add_months(test_start, test_months) - timedelta(days=1)

            # 检查是否超出范围
            if test_end > end_date:
                break

            windows.append((train_start, train_end, test_start, test_end))
            round_num += 1

            # 滚动到下一个窗口
            current_date = self._add_months(current_date, step_months)

            # 安全检查，防止无限循环
            if round_num > 100:
                logger.warning("Walk-Forward rounds exceeded 100, stopping")
                break

        return windows

    def _add_months(self, d: date, months: int) -> date:
        """日期加月份"""
        month = d.month - 1 + months
        year = d.year + month // 12
        month = month % 12 + 1
        day = min(d.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30,
                          31, 31, 30, 31, 30, 31][month - 1])
        return date(year, month, day)

    def run_validation(
        self,
        strategy_config: dict[str, Any],
        start_date: date,
        end_date: date,
        run_backtest_fn: callable = None
    ) -> dict[str, Any]:
        """
        运行 Walk-Forward 验证

        Args:
            strategy_config: 策略配置
            start_date: 开始日期
            end_date: 结束日期
            run_backtest_fn: 回测函数 (可选，用于实际回测)

        Returns:
            验证结果
        """
        windows = self.calculate_windows(start_date, end_date)

        if not windows:
            return {
                "error": "日期范围不足以进行 Walk-Forward 验证",
                "min_required_months": self.config.train_period + self.config.test_period
            }

        logger.info(
            "Starting Walk-Forward validation",
            rounds=len(windows),
            train_period=self.config.train_period,
            test_period=self.config.test_period
        )

        self.rounds = []
        oos_returns = []
        oos_sharpes = []

        for i, (train_start, train_end, test_start, test_end) in enumerate(windows):
            round_result = self._run_single_round(
                round_number=i + 1,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
                strategy_config=strategy_config,
                run_backtest_fn=run_backtest_fn
            )
            self.rounds.append(round_result)
            oos_returns.append(round_result.out_of_sample_metrics.annual_return)
            oos_sharpes.append(round_result.out_of_sample_metrics.sharpe_ratio)

        # 计算汇总指标
        aggregated = self._calculate_aggregated_metrics()

        # 计算过拟合概率
        overfit_prob = self._calculate_overfit_probability()

        # 生成评估和建议
        assessment = self._generate_assessment(aggregated, overfit_prob)

        # 构建权益曲线
        equity_curve = self._build_oos_equity_curve()

        return {
            "config": {
                "train_period": self.config.train_period,
                "test_period": self.config.test_period,
                "step_size": self.config.step_size,
                "optimize_target": self.config.optimize_target,
                "expanding_window": self.config.expanding_window,
            },
            "rounds": [self._round_to_dict(r) for r in self.rounds],
            "aggregated_metrics": aggregated,
            "overfit_probability": overfit_prob,
            "assessment": assessment["assessment"],
            "recommendations": assessment["recommendations"],
            "oos_equity_curve": equity_curve,
        }

    def _run_single_round(
        self,
        round_number: int,
        train_start: date,
        train_end: date,
        test_start: date,
        test_end: date,
        strategy_config: dict[str, Any],
        run_backtest_fn: callable = None
    ) -> WalkForwardRound:
        """运行单轮 Walk-Forward"""
        logger.info(
            f"Running round {round_number}",
            train=f"{train_start} to {train_end}",
            test=f"{test_start} to {test_end}"
        )

        # 如果提供了回测函数，使用它；否则使用模拟数据
        if run_backtest_fn:
            # 训练期回测
            is_metrics = run_backtest_fn(strategy_config, train_start, train_end)
            # 测试期回测
            oos_metrics = run_backtest_fn(strategy_config, test_start, test_end)
            optimized_params = strategy_config.get("optimized_params", {})
        else:
            # 模拟数据 (用于演示)
            is_metrics, oos_metrics, optimized_params = self._simulate_round(
                round_number, train_start, train_end, test_start, test_end
            )

        # 计算稳定性比率
        stability_ratio = 0.0
        if is_metrics.sharpe_ratio > 0:
            stability_ratio = oos_metrics.sharpe_ratio / is_metrics.sharpe_ratio

        return WalkForwardRound(
            round_number=round_number,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            optimized_params=optimized_params,
            in_sample_metrics=is_metrics,
            out_of_sample_metrics=oos_metrics,
            stability_ratio=stability_ratio
        )

    def _simulate_round(
        self,
        round_number: int,
        train_start: date,
        train_end: date,
        test_start: date,
        test_end: date
    ) -> tuple[BacktestMetrics, BacktestMetrics, dict]:
        """模拟单轮结果 (用于演示)"""
        # 模拟样本内表现 (通常较好)
        np.random.seed(round_number * 100)
        is_sharpe = 1.2 + np.random.normal(0, 0.3)
        is_return = 0.15 + np.random.normal(0, 0.05)

        is_metrics = BacktestMetrics(
            total_return=is_return * 3,
            annual_return=is_return,
            volatility=0.18,
            max_drawdown=-0.12 - np.random.uniform(0, 0.08),
            sharpe_ratio=is_sharpe,
            sortino_ratio=is_sharpe * 1.2,
            calmar_ratio=is_return / 0.15,
            win_rate=0.55 + np.random.uniform(-0.05, 0.05),
            profit_factor=1.5 + np.random.uniform(-0.3, 0.3),
        )

        # 模拟样本外表现 (通常较差，反映真实情况)
        degradation = 0.6 + np.random.uniform(0, 0.3)  # 60-90% 保留
        oos_sharpe = is_sharpe * degradation
        oos_return = is_return * degradation

        oos_metrics = BacktestMetrics(
            total_return=oos_return,
            annual_return=oos_return,
            volatility=0.20,
            max_drawdown=-0.15 - np.random.uniform(0, 0.10),
            sharpe_ratio=oos_sharpe,
            sortino_ratio=oos_sharpe * 1.1,
            calmar_ratio=oos_return / 0.18,
            win_rate=0.52 + np.random.uniform(-0.05, 0.05),
            profit_factor=1.3 + np.random.uniform(-0.3, 0.3),
        )

        optimized_params = {
            "lookback_period": 20 + round_number * 5,
            "holding_count": 30,
            "stop_loss": 15.0,
        }

        return is_metrics, oos_metrics, optimized_params

    def _calculate_aggregated_metrics(self) -> dict[str, float]:
        """计算汇总指标"""
        if not self.rounds:
            return {}

        oos_sharpes = [r.out_of_sample_metrics.sharpe_ratio for r in self.rounds]
        oos_returns = [r.out_of_sample_metrics.annual_return for r in self.rounds]
        oos_drawdowns = [r.out_of_sample_metrics.max_drawdown for r in self.rounds]
        stability_ratios = [r.stability_ratio for r in self.rounds]
        oos_win_rates = [r.out_of_sample_metrics.win_rate for r in self.rounds]

        return {
            "oos_sharpe": float(np.mean(oos_sharpes)),
            "oos_returns": float(np.mean(oos_returns)),
            "oos_max_drawdown": float(np.min(oos_drawdowns)),
            "stability_ratio": float(np.mean(stability_ratios)),
            "oos_win_rate": float(np.mean(oos_win_rates)),
        }

    def _calculate_overfit_probability(self) -> float:
        """计算过拟合概率"""
        if not self.rounds:
            return 50.0

        # 基于稳定性比率计算
        stability_ratios = [r.stability_ratio for r in self.rounds]
        avg_stability = np.mean(stability_ratios)

        # 稳定性比率越低，过拟合概率越高
        if avg_stability >= 0.8:
            base_prob = 10
        elif avg_stability >= 0.6:
            base_prob = 30
        elif avg_stability >= 0.4:
            base_prob = 55
        else:
            base_prob = 80

        # 考虑样本外夏普的一致性
        oos_sharpes = [r.out_of_sample_metrics.sharpe_ratio for r in self.rounds]
        sharpe_std = np.std(oos_sharpes)

        # 如果样本外表现波动大，增加过拟合概率
        if sharpe_std > 0.5:
            base_prob += 15
        elif sharpe_std > 0.3:
            base_prob += 8

        return min(max(base_prob, 0), 100)

    def _generate_assessment(
        self,
        aggregated: dict,
        overfit_prob: float
    ) -> dict[str, Any]:
        """生成评估和建议"""
        recommendations = []

        # 根据过拟合概率评估
        if overfit_prob < 20:
            assessment = "excellent"
            recommendations.append("策略表现稳健，样本外验证结果优秀")
        elif overfit_prob < 40:
            assessment = "good"
            recommendations.append("策略表现良好，建议继续监控样本外表现")
        elif overfit_prob < 60:
            assessment = "moderate"
            recommendations.append("策略存在一定过拟合风险，建议简化参数")
            recommendations.append("考虑增加训练期长度以提高稳健性")
        elif overfit_prob < 80:
            assessment = "poor"
            recommendations.append("策略可能过拟合，建议重新审视因子选择")
            recommendations.append("减少参数数量，避免过度优化")
            recommendations.append("考虑使用更简单的规则")
        else:
            assessment = "overfit"
            recommendations.append("警告: 策略严重过拟合")
            recommendations.append("样本内外表现差距过大，不建议实盘使用")
            recommendations.append("建议从头设计策略，避免数据窥探")

        # 根据稳定性比率添加建议
        if aggregated.get("stability_ratio", 0) < 0.5:
            recommendations.append("稳定性比率较低，策略在不同时期表现不一致")

        # 根据样本外夏普添加建议
        if aggregated.get("oos_sharpe", 0) < 0.5:
            recommendations.append("样本外夏普较低，策略预期收益/风险比不佳")

        return {
            "assessment": assessment,
            "recommendations": recommendations
        }

    def _build_oos_equity_curve(self) -> list[dict]:
        """构建样本外权益曲线"""
        curve = []
        cumulative_return = 1.0

        for r in self.rounds:
            # 简化处理: 假设每个测试期的收益均匀分布
            period_return = r.out_of_sample_metrics.annual_return
            months = self.config.test_period
            monthly_return = (1 + period_return) ** (1/12) - 1

            current_date = r.test_start
            while current_date <= r.test_end:
                cumulative_return *= (1 + monthly_return)
                curve.append({
                    "date": current_date.isoformat(),
                    "value": cumulative_return
                })
                current_date = self._add_months(current_date, 1)

        return curve

    def _round_to_dict(self, r: WalkForwardRound) -> dict:
        """将轮次结果转换为字典"""
        return {
            "round_number": r.round_number,
            "train_start": r.train_start.isoformat(),
            "train_end": r.train_end.isoformat(),
            "test_start": r.test_start.isoformat(),
            "test_end": r.test_end.isoformat(),
            "optimized_params": r.optimized_params,
            "in_sample_metrics": {
                "total_return": r.in_sample_metrics.total_return,
                "annual_return": r.in_sample_metrics.annual_return,
                "volatility": r.in_sample_metrics.volatility,
                "max_drawdown": r.in_sample_metrics.max_drawdown,
                "sharpe_ratio": r.in_sample_metrics.sharpe_ratio,
                "sortino_ratio": r.in_sample_metrics.sortino_ratio,
                "calmar_ratio": r.in_sample_metrics.calmar_ratio,
                "win_rate": r.in_sample_metrics.win_rate,
                "profit_factor": r.in_sample_metrics.profit_factor,
                "beta": r.in_sample_metrics.beta,
                "alpha": r.in_sample_metrics.alpha,
            },
            "out_of_sample_metrics": {
                "total_return": r.out_of_sample_metrics.total_return,
                "annual_return": r.out_of_sample_metrics.annual_return,
                "volatility": r.out_of_sample_metrics.volatility,
                "max_drawdown": r.out_of_sample_metrics.max_drawdown,
                "sharpe_ratio": r.out_of_sample_metrics.sharpe_ratio,
                "sortino_ratio": r.out_of_sample_metrics.sortino_ratio,
                "calmar_ratio": r.out_of_sample_metrics.calmar_ratio,
                "win_rate": r.out_of_sample_metrics.win_rate,
                "profit_factor": r.out_of_sample_metrics.profit_factor,
                "beta": r.out_of_sample_metrics.beta,
                "alpha": r.out_of_sample_metrics.alpha,
            },
            "stability_ratio": r.stability_ratio,
        }


def estimate_walk_forward_rounds(
    start_date: date,
    end_date: date,
    train_period: int = 36,
    test_period: int = 12,
    step_size: int = 12
) -> int:
    """估算 Walk-Forward 验证轮数"""
    total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    available_for_test = total_months - train_period

    if available_for_test < test_period:
        return 0

    rounds = 1 + (available_for_test - test_period) // step_size
    return max(0, rounds)
