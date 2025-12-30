"""
生存偏差检测器

检测策略中可能存在的生存偏差 (Survivorship Bias):
- 只使用当前存在的股票
- 忽略退市股票
- 忽略被收购/合并的股票
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


class DelistReason(str, Enum):
    """退市原因"""
    BANKRUPTCY = "bankruptcy"           # 破产
    MERGER = "merger"                   # 合并
    ACQUISITION = "acquisition"         # 被收购
    PRIVATIZATION = "privatization"     # 私有化
    DELISTING = "delisting"             # 强制退市
    OTHER = "other"                     # 其他


@dataclass
class DelistedStock:
    """退市股票记录"""
    symbol: str
    delist_date: date
    reason: DelistReason
    last_price: float | None = None
    terminal_return: float | None = None  # 退市前最后收益


@dataclass
class SurvivorshipWarning:
    """生存偏差警告"""
    severity: str                       # "low", "medium", "high"
    description: str
    affected_period: tuple[date, date] | None = None
    missing_stocks: list[str] = field(default_factory=list)
    estimated_impact: float = 0.0       # 估计的收益影响
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class SurvivorshipReport:
    """生存偏差检测报告"""
    has_bias: bool = False
    bias_severity: str = "none"         # "none", "low", "medium", "high"
    warnings: list[SurvivorshipWarning] = field(default_factory=list)
    missing_delisted_count: int = 0
    estimated_return_impact: float = 0.0  # 估计的收益影响 (%)
    coverage_ratio: float = 1.0           # 数据覆盖率

    def add_warning(self, warning: SurvivorshipWarning) -> None:
        """添加警告"""
        self.warnings.append(warning)
        self.has_bias = True

        # 更新严重程度
        severity_order = ["none", "low", "medium", "high"]
        if severity_order.index(warning.severity) > severity_order.index(self.bias_severity):
            self.bias_severity = warning.severity


class SurvivorshipDetector:
    """
    生存偏差检测器

    检测方法:
    1. 股票池覆盖检查: 是否包含历史上存在但现已退市的股票
    2. 数据完整性检查: 是否有股票数据突然消失
    3. 退市影响估计: 估算忽略退市股票对收益的影响
    """

    def __init__(self, delisted_stocks: list[DelistedStock] | None = None):
        """
        Args:
            delisted_stocks: 已知的退市股票列表
        """
        self.delisted_stocks = delisted_stocks or []
        self.report = SurvivorshipReport()

    def detect(
        self,
        prices: pd.DataFrame,
        signals: pd.DataFrame,
        universe_history: dict[date, list[str]] | None = None,
    ) -> SurvivorshipReport:
        """
        执行生存偏差检测

        Args:
            prices: 价格数据 (index=date, columns=symbols)
            signals: 交易信号
            universe_history: 历史股票池快照

        Returns:
            检测报告
        """
        self.report = SurvivorshipReport()

        # 1. 检测数据中断
        self._detect_data_gaps(prices)

        # 2. 检查退市股票覆盖
        if self.delisted_stocks:
            self._check_delisted_coverage(prices, signals)

        # 3. 检查股票池一致性
        if universe_history:
            self._check_universe_consistency(signals, universe_history)

        # 4. 估算生存偏差影响
        self._estimate_bias_impact(prices, signals)

        logger.info(
            "生存偏差检测完成",
            has_bias=self.report.has_bias,
            severity=self.report.bias_severity,
            missing_stocks=self.report.missing_delisted_count,
            estimated_impact=f"{self.report.estimated_return_impact:.2%}",
        )

        return self.report

    def _detect_data_gaps(self, prices: pd.DataFrame) -> None:
        """检测数据中断 (可能是退市)"""
        gaps = []

        for symbol in prices.columns:
            series = prices[symbol].dropna()
            if len(series) < 10:
                continue

            # 检查最后交易日期
            last_date = series.index[-1]
            data_end = prices.index[-1]

            # 如果股票在数据期间消失且不是接近结束
            days_missing = (data_end - last_date).days
            if days_missing > 30:  # 超过30天没有数据
                gaps.append({
                    "symbol": symbol,
                    "last_date": last_date,
                    "days_missing": days_missing,
                    "last_price": float(series.iloc[-1]),
                })

        if gaps:
            # 检查这些是否是已知的退市
            known_delisted = {d.symbol for d in self.delisted_stocks}
            unknown_gaps = [g for g in gaps if g["symbol"] not in known_delisted]

            if unknown_gaps:
                self.report.add_warning(
                    SurvivorshipWarning(
                        severity="medium",
                        description=f"检测到 {len(unknown_gaps)} 只股票数据中断，可能是退市但未记录",
                        missing_stocks=[g["symbol"] for g in unknown_gaps[:20]],
                        evidence={
                            "total_gaps": len(unknown_gaps),
                            "examples": unknown_gaps[:5],
                        },
                    )
                )

    def _check_delisted_coverage(
        self,
        prices: pd.DataFrame,
        signals: pd.DataFrame,
    ) -> None:
        """检查退市股票是否被正确处理"""
        missing_in_prices = []
        missing_in_signals = []

        data_start = prices.index[0]
        data_end = prices.index[-1]

        for stock in self.delisted_stocks:
            # 检查退市日期是否在数据范围内
            delist_date_ts = pd.Timestamp(stock.delist_date)
            if delist_date_ts < data_start or delist_date_ts > data_end:
                continue

            # 检查价格数据
            if stock.symbol not in prices.columns:
                missing_in_prices.append(stock)
            else:
                # 检查退市前是否有数据
                stock_prices = prices[stock.symbol].dropna()
                if stock_prices.empty or stock_prices.index[-1] < delist_date_ts - pd.Timedelta(days=30):
                    missing_in_prices.append(stock)

            # 检查信号数据
            if stock.symbol not in signals.columns:
                missing_in_signals.append(stock)

        self.report.missing_delisted_count = len(missing_in_prices)

        if missing_in_prices:
            # 分类退市原因
            by_reason = {}
            for stock in missing_in_prices:
                reason = stock.reason.value
                if reason not in by_reason:
                    by_reason[reason] = []
                by_reason[reason].append(stock.symbol)

            self.report.add_warning(
                SurvivorshipWarning(
                    severity="high" if len(missing_in_prices) > 10 else "medium",
                    description=f"缺少 {len(missing_in_prices)} 只已退市股票的历史数据",
                    missing_stocks=[s.symbol for s in missing_in_prices[:20]],
                    evidence={
                        "by_reason": {k: len(v) for k, v in by_reason.items()},
                        "bankruptcy_count": len(by_reason.get("bankruptcy", [])),
                    },
                )
            )

    def _check_universe_consistency(
        self,
        signals: pd.DataFrame,
        universe_history: dict[date, list[str]],
    ) -> None:
        """检查股票池一致性"""
        inconsistencies = []

        sorted_dates = sorted(universe_history.keys())
        signal_dates = signals.index

        for sig_date in signal_dates:
            sig_date_val = sig_date.date() if hasattr(sig_date, "date") else sig_date

            # 找到适用的股票池
            applicable = [d for d in sorted_dates if d <= sig_date_val]
            if not applicable:
                continue

            historical_universe = set(universe_history[applicable[-1]])
            signal_symbols = set(signals.loc[sig_date][signals.loc[sig_date] != 0].index)

            # 检查信号中是否有不在历史股票池中的股票
            extra_symbols = signal_symbols - historical_universe

            if extra_symbols:
                inconsistencies.append({
                    "date": sig_date_val,
                    "extra_count": len(extra_symbols),
                    "examples": list(extra_symbols)[:5],
                })

        if inconsistencies:
            total_extra = sum(i["extra_count"] for i in inconsistencies)

            self.report.add_warning(
                SurvivorshipWarning(
                    severity="medium",
                    description=f"在 {len(inconsistencies)} 个日期使用了不在当时股票池中的股票",
                    evidence={
                        "total_extra_selections": total_extra,
                        "affected_dates": len(inconsistencies),
                        "examples": inconsistencies[:5],
                    },
                )
            )

    def _estimate_bias_impact(
        self,
        prices: pd.DataFrame,
        signals: pd.DataFrame,
    ) -> None:
        """估算生存偏差对收益的影响"""
        if not self.delisted_stocks:
            return

        # 计算退市股票的平均终端收益
        terminal_returns = []
        for stock in self.delisted_stocks:
            if stock.terminal_return is not None:
                terminal_returns.append(stock.terminal_return)
            elif stock.reason == DelistReason.BANKRUPTCY:
                # 破产通常损失大部分价值
                terminal_returns.append(-0.9)
            elif stock.reason in [DelistReason.ACQUISITION, DelistReason.MERGER]:
                # 收购/合并通常有溢价
                terminal_returns.append(0.2)
            elif stock.reason == DelistReason.PRIVATIZATION:
                terminal_returns.append(0.1)
            else:
                terminal_returns.append(-0.3)

        if terminal_returns:
            avg_terminal = np.mean(terminal_returns)
            # 估算影响: 假设退市股票占信号的一定比例
            missing_ratio = self.report.missing_delisted_count / max(len(signals.columns), 1)
            estimated_impact = avg_terminal * missing_ratio

            self.report.estimated_return_impact = float(estimated_impact)

            if abs(estimated_impact) > 0.02:  # 超过 2% 影响
                self.report.add_warning(
                    SurvivorshipWarning(
                        severity="high",
                        description=f"估计生存偏差对年化收益的影响约为 {estimated_impact:.2%}",
                        estimated_impact=float(estimated_impact),
                        evidence={
                            "avg_terminal_return": float(avg_terminal),
                            "missing_ratio": float(missing_ratio),
                        },
                    )
                )


def estimate_survivorship_bias(
    returns: pd.DataFrame,
    bankruptcy_rate: float = 0.02,
    avg_bankruptcy_loss: float = 0.9,
) -> float:
    """
    估算生存偏差的大致影响

    Args:
        returns: 收益率数据
        bankruptcy_rate: 估计的年化破产率
        avg_bankruptcy_loss: 破产平均损失比例

    Returns:
        估计的年化收益偏差 (正值表示高估)
    """
    # 简单估算: 破产率 * 平均损失 = 被高估的收益
    years = len(returns) / 252 if len(returns) > 0 else 1
    total_bankruptcy_prob = 1 - (1 - bankruptcy_rate) ** years
    estimated_bias = total_bankruptcy_prob * avg_bankruptcy_loss / years

    return float(estimated_bias)
