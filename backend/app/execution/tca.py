"""
TCA (Transaction Cost Analysis) 交易成本分析

分析交易执行质量:
- 滑点分析
- 实现差额 (Implementation Shortfall)
- 执行基准比较
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog

from app.execution.order_manager import Fill, Order, OrderSide

logger = structlog.get_logger()


class ExecutionQuality(str, Enum):
    """执行质量评级"""
    EXCELLENT = "excellent"     # 优秀: < -5 bps
    GOOD = "good"               # 良好: -5 to 5 bps
    FAIR = "fair"               # 一般: 5 to 15 bps
    POOR = "poor"               # 较差: 15 to 30 bps
    BAD = "bad"                 # 糟糕: > 30 bps


class Benchmark(str, Enum):
    """执行基准"""
    ARRIVAL = "arrival"         # 到达价
    CLOSE = "close"             # 收盘价
    OPEN = "open"               # 开盘价
    VWAP = "vwap"               # 成交量加权平均价
    TWAP = "twap"               # 时间加权平均价
    MIDPOINT = "midpoint"       # 中间价


@dataclass
class TCAMetrics:
    """TCA 指标"""
    # 价格基准
    arrival_price: float = 0.0          # 到达价 (决策时价格)
    execution_price: float = 0.0        # 执行均价
    vwap: float = 0.0                   # 期间 VWAP
    twap: float = 0.0                   # 期间 TWAP
    close_price: float = 0.0            # 收盘价

    # 滑点 (基点)
    slippage_vs_arrival: float = 0.0    # 相对到达价
    slippage_vs_vwap: float = 0.0       # 相对 VWAP
    slippage_vs_twap: float = 0.0       # 相对 TWAP

    # 实现差额分解
    implementation_shortfall: float = 0.0  # 总实现差额 (bps)
    timing_cost: float = 0.0            # 时机成本 (bps)
    market_impact: float = 0.0          # 市场冲击 (bps)
    spread_cost: float = 0.0            # 价差成本 (bps)
    opportunity_cost: float = 0.0       # 机会成本 (bps)

    # 执行效率
    fill_rate: float = 0.0              # 成交率
    participation_rate: float = 0.0      # 市场参与率
    avg_spread_bps: float = 0.0         # 平均价差

    # 质量评级
    quality: ExecutionQuality = ExecutionQuality.FAIR


@dataclass
class TCAReport:
    """TCA 报告"""
    order_id: str
    symbol: str
    side: str
    total_quantity: float
    filled_quantity: float
    metrics: TCAMetrics = field(default_factory=TCAMetrics)

    # 执行时间
    decision_time: datetime | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_seconds: float = 0.0

    # 成交明细
    fills: list[dict[str, Any]] = field(default_factory=list)

    # 建议
    recommendations: list[str] = field(default_factory=list)


class TCAAnalyzer:
    """
    TCA 分析器

    分析订单执行质量

    使用示例:
    ```python
    analyzer = TCAAnalyzer()

    report = analyzer.analyze(
        order=order,
        fills=fills,
        market_data=market_df,
        arrival_price=150.0,
    )

    print(f"滑点: {report.metrics.slippage_vs_arrival:.1f} bps")
    print(f"质量: {report.metrics.quality.value}")
    ```
    """

    def __init__(self):
        pass

    def analyze(
        self,
        order: Order,
        fills: list[Fill],
        market_data: pd.DataFrame | None = None,
        arrival_price: float | None = None,
        vwap: float | None = None,
        twap: float | None = None,
    ) -> TCAReport:
        """
        分析订单执行

        Args:
            order: 订单
            fills: 成交列表
            market_data: 市场数据 (columns: time, price, volume)
            arrival_price: 到达价格
            vwap: 期间 VWAP
            twap: 期间 TWAP

        Returns:
            TCA 报告
        """
        metrics = TCAMetrics()

        # 计算执行均价
        if fills:
            total_cost = sum(f.quantity * f.price for f in fills)
            total_qty = sum(f.quantity for f in fills)
            metrics.execution_price = total_cost / total_qty if total_qty > 0 else 0

            # 成交率
            metrics.fill_rate = total_qty / order.quantity if order.quantity > 0 else 0

        # 设置基准价格
        if arrival_price:
            metrics.arrival_price = arrival_price
        elif order.created_at and market_data is not None:
            metrics.arrival_price = self._get_price_at_time(market_data, order.created_at)

        if vwap:
            metrics.vwap = vwap
        elif market_data is not None:
            metrics.vwap = self._calculate_vwap(market_data)

        if twap:
            metrics.twap = twap
        elif market_data is not None:
            metrics.twap = self._calculate_twap(market_data)

        # 计算滑点
        side_multiplier = 1 if order.side == OrderSide.BUY else -1

        if metrics.arrival_price > 0 and metrics.execution_price > 0:
            metrics.slippage_vs_arrival = (
                (metrics.execution_price - metrics.arrival_price)
                / metrics.arrival_price * 10000 * side_multiplier
            )

        if metrics.vwap > 0 and metrics.execution_price > 0:
            metrics.slippage_vs_vwap = (
                (metrics.execution_price - metrics.vwap)
                / metrics.vwap * 10000 * side_multiplier
            )

        if metrics.twap > 0 and metrics.execution_price > 0:
            metrics.slippage_vs_twap = (
                (metrics.execution_price - metrics.twap)
                / metrics.twap * 10000 * side_multiplier
            )

        # 实现差额分解
        metrics.implementation_shortfall = metrics.slippage_vs_arrival

        # 简化的成本分解
        # 市场冲击: 执行价 vs VWAP 的差异
        if metrics.vwap > 0:
            metrics.market_impact = abs(
                (metrics.execution_price - metrics.vwap) / metrics.vwap * 10000
            )

        # 时机成本: 到达价 vs TWAP 的差异
        if metrics.arrival_price > 0 and metrics.twap > 0:
            metrics.timing_cost = abs(
                (metrics.twap - metrics.arrival_price) / metrics.arrival_price * 10000
            ) * side_multiplier

        # 价差成本 (估计)
        if market_data is not None and "bid" in market_data.columns and "ask" in market_data.columns:
            avg_spread = (market_data["ask"] - market_data["bid"]).mean()
            mid = (market_data["ask"] + market_data["bid"]).mean() / 2
            metrics.spread_cost = avg_spread / mid * 5000  # 假设承担一半价差

        # 执行质量评级
        metrics.quality = self._rate_quality(metrics.slippage_vs_arrival)

        # 生成报告
        report = TCAReport(
            order_id=str(order.order_id),
            symbol=order.symbol,
            side=order.side.value,
            total_quantity=order.quantity,
            filled_quantity=order.filled_quantity,
            metrics=metrics,
            decision_time=order.created_at,
            fills=[
                {
                    "fill_id": f.fill_id,
                    "quantity": f.quantity,
                    "price": f.price,
                    "timestamp": f.timestamp.isoformat(),
                }
                for f in fills
            ],
        )

        # 计算执行时间
        if fills:
            report.start_time = min(f.timestamp for f in fills)
            report.end_time = max(f.timestamp for f in fills)
            report.duration_seconds = (report.end_time - report.start_time).total_seconds()

        # 生成建议
        report.recommendations = self._generate_recommendations(metrics)

        logger.info(
            "TCA分析完成",
            order_id=report.order_id[:8],
            slippage=f"{metrics.slippage_vs_arrival:.1f} bps",
            quality=metrics.quality.value,
        )

        return report

    def _calculate_vwap(self, market_data: pd.DataFrame) -> float:
        """计算 VWAP"""
        if "price" not in market_data.columns or "volume" not in market_data.columns:
            return 0.0

        total_value = (market_data["price"] * market_data["volume"]).sum()
        total_volume = market_data["volume"].sum()

        return total_value / total_volume if total_volume > 0 else 0.0

    def _calculate_twap(self, market_data: pd.DataFrame) -> float:
        """计算 TWAP"""
        if "price" not in market_data.columns:
            return 0.0

        return market_data["price"].mean()

    def _get_price_at_time(
        self, market_data: pd.DataFrame, target_time: datetime
    ) -> float:
        """获取指定时间的价格"""
        if "time" not in market_data.columns or "price" not in market_data.columns:
            return 0.0

        # 找到最接近的时间点
        market_data = market_data.copy()
        market_data["time_diff"] = abs(
            pd.to_datetime(market_data["time"]) - target_time
        )
        closest = market_data.loc[market_data["time_diff"].idxmin()]

        return float(closest["price"])

    def _rate_quality(self, slippage_bps: float) -> ExecutionQuality:
        """评价执行质量"""
        if slippage_bps < -5:
            return ExecutionQuality.EXCELLENT
        elif slippage_bps < 5:
            return ExecutionQuality.GOOD
        elif slippage_bps < 15:
            return ExecutionQuality.FAIR
        elif slippage_bps < 30:
            return ExecutionQuality.POOR
        else:
            return ExecutionQuality.BAD

    def _generate_recommendations(self, metrics: TCAMetrics) -> list[str]:
        """生成建议"""
        recommendations = []

        if metrics.market_impact > 10:
            recommendations.append("市场冲击较大，考虑降低参与率或使用更长的执行时间")

        if metrics.timing_cost > 10:
            recommendations.append("时机成本较高，考虑更快执行或调整决策时机")

        if metrics.spread_cost > 5:
            recommendations.append("价差成本较高，考虑使用限价单或在流动性较好时段执行")

        if metrics.fill_rate < 0.95:
            recommendations.append("成交率较低，考虑更激进的限价或使用市价单")

        if metrics.quality == ExecutionQuality.EXCELLENT:
            recommendations.append("执行质量优秀，保持当前策略")

        return recommendations


def calculate_slippage(
    execution_price: float,
    benchmark_price: float,
    side: OrderSide,
) -> float:
    """
    快速计算滑点 (基点)

    Args:
        execution_price: 执行价格
        benchmark_price: 基准价格
        side: 方向

    Returns:
        滑点 (基点, 正数表示不利)
    """
    if benchmark_price <= 0:
        return 0.0

    slippage = (execution_price - benchmark_price) / benchmark_price * 10000

    if side == OrderSide.SELL:
        slippage = -slippage

    return float(slippage)


def calculate_implementation_shortfall(
    decision_price: float,
    execution_price: float,
    quantity: float,
    side: OrderSide,
) -> dict[str, float]:
    """
    计算实现差额

    Args:
        decision_price: 决策时价格
        execution_price: 执行均价
        quantity: 数量
        side: 方向

    Returns:
        实现差额分解
    """
    if decision_price <= 0:
        return {"total_bps": 0, "dollar_cost": 0}

    price_diff = execution_price - decision_price
    if side == OrderSide.SELL:
        price_diff = -price_diff

    shortfall_bps = price_diff / decision_price * 10000
    dollar_cost = price_diff * quantity

    return {
        "total_bps": float(shortfall_bps),
        "dollar_cost": float(dollar_cost),
        "pct_of_trade": float(shortfall_bps / 10000),
    }


def aggregate_tca_reports(reports: list[TCAReport]) -> dict[str, Any]:
    """
    聚合多个 TCA 报告

    Args:
        reports: TCA 报告列表

    Returns:
        聚合统计
    """
    if not reports:
        return {}

    slippages = [r.metrics.slippage_vs_arrival for r in reports]
    quantities = [r.filled_quantity for r in reports]

    total_quantity = sum(quantities)
    weighted_slippage = sum(s * q for s, q in zip(slippages, quantities)) / total_quantity if total_quantity > 0 else 0

    quality_counts = {}
    for r in reports:
        q = r.metrics.quality.value
        quality_counts[q] = quality_counts.get(q, 0) + 1

    return {
        "n_orders": len(reports),
        "total_quantity": total_quantity,
        "avg_slippage_bps": float(np.mean(slippages)),
        "weighted_slippage_bps": float(weighted_slippage),
        "median_slippage_bps": float(np.median(slippages)),
        "std_slippage_bps": float(np.std(slippages)),
        "min_slippage_bps": float(min(slippages)),
        "max_slippage_bps": float(max(slippages)),
        "quality_distribution": quality_counts,
        "avg_fill_rate": float(np.mean([r.metrics.fill_rate for r in reports])),
        "avg_duration_seconds": float(np.mean([r.duration_seconds for r in reports])),
    }
