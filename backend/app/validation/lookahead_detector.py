"""
前视偏差检测器

检测策略中可能存在的前视偏差 (Lookahead Bias):
- 使用未来数据计算因子
- 使用未发布的财报数据
- 使用未来价格信息
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


class LookaheadType(str, Enum):
    """前视偏差类型"""
    PRICE_LOOKAHEAD = "price_lookahead"           # 价格前视
    FUNDAMENTAL_LOOKAHEAD = "fundamental_lookahead"  # 财务前视
    SIGNAL_LOOKAHEAD = "signal_lookahead"         # 信号前视
    UNIVERSE_LOOKAHEAD = "universe_lookahead"     # 股票池前视
    CALENDAR_LOOKAHEAD = "calendar_lookahead"     # 日历前视


@dataclass
class LookaheadWarning:
    """前视偏差警告"""
    type: LookaheadType
    severity: str               # "low", "medium", "high", "critical"
    description: str
    affected_dates: list[date] = field(default_factory=list)
    affected_symbols: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class LookaheadReport:
    """前视偏差检测报告"""
    is_clean: bool                              # 是否无前视偏差
    warnings: list[LookaheadWarning] = field(default_factory=list)
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0

    def add_warning(self, warning: LookaheadWarning) -> None:
        """添加警告"""
        self.warnings.append(warning)
        self.total_issues += 1

        if warning.severity == "critical":
            self.critical_issues += 1
            self.is_clean = False
        elif warning.severity == "high":
            self.high_issues += 1
            self.is_clean = False
        elif warning.severity == "medium":
            self.medium_issues += 1
        else:
            self.low_issues += 1


class LookaheadDetector:
    """
    前视偏差检测器

    检测方法:
    1. 价格前视: 检查信号是否与未来收益相关
    2. 财务前视: 检查财报使用是否基于 release_date
    3. 信号前视: 检查信号生成时间
    4. 股票池前视: 检查股票池成分是否使用历史快照
    """

    def __init__(self):
        self.report = LookaheadReport(is_clean=True)

    def detect_all(
        self,
        signals: pd.DataFrame,
        returns: pd.DataFrame,
        financial_data: pd.DataFrame | None = None,
        universe_snapshots: dict[date, list[str]] | None = None,
    ) -> LookaheadReport:
        """
        执行全部前视偏差检测

        Args:
            signals: 交易信号 (index=date, columns=symbols)
            returns: 收益率数据
            financial_data: 财务数据 (包含 report_date 和 release_date)
            universe_snapshots: 股票池历史快照

        Returns:
            检测报告
        """
        self.report = LookaheadReport(is_clean=True)

        # 1. 检测价格前视
        self._detect_price_lookahead(signals, returns)

        # 2. 检测信号时序
        self._detect_signal_timing(signals, returns)

        # 3. 检测财务前视
        if financial_data is not None:
            self._detect_fundamental_lookahead(signals, financial_data)

        # 4. 检测股票池前视
        if universe_snapshots is not None:
            self._detect_universe_lookahead(signals, universe_snapshots)

        # 记录结果
        logger.info(
            "前视偏差检测完成",
            is_clean=self.report.is_clean,
            total_issues=self.report.total_issues,
            critical=self.report.critical_issues,
            high=self.report.high_issues,
        )

        return self.report

    def _detect_price_lookahead(
        self,
        signals: pd.DataFrame,
        returns: pd.DataFrame,
    ) -> None:
        """
        检测价格前视偏差

        方法: 如果信号与同期收益相关性过高，可能存在前视
        正常情况: 信号应该与下期收益相关，而非当期
        """
        # 计算信号与同期收益的相关性
        common_dates = signals.index.intersection(returns.index)
        common_symbols = signals.columns.intersection(returns.columns)

        if len(common_dates) < 10 or len(common_symbols) < 5:
            return

        sig = signals.loc[common_dates, common_symbols]
        ret = returns.loc[common_dates, common_symbols]

        # 截面相关性
        correlations = []
        for dt in common_dates:
            sig_row = sig.loc[dt].dropna()
            ret_row = ret.loc[dt].dropna()
            common = sig_row.index.intersection(ret_row.index)

            if len(common) > 10:
                corr = sig_row[common].corr(ret_row[common])
                if not np.isnan(corr):
                    correlations.append((dt, corr))

        if not correlations:
            return

        # 分析相关性分布
        corr_values = [c[1] for c in correlations]
        avg_corr = np.mean(corr_values)
        suspicious_dates = [dt for dt, c in correlations if abs(c) > 0.5]

        # 同期相关性过高是可疑的
        if abs(avg_corr) > 0.3:
            self.report.add_warning(
                LookaheadWarning(
                    type=LookaheadType.PRICE_LOOKAHEAD,
                    severity="high" if abs(avg_corr) > 0.5 else "medium",
                    description=f"信号与同期收益相关性异常高 (avg={avg_corr:.2f})，可能存在价格前视",
                    affected_dates=suspicious_dates[:10],
                    evidence={
                        "avg_correlation": float(avg_corr),
                        "max_correlation": float(max(corr_values)),
                        "suspicious_date_count": len(suspicious_dates),
                    },
                )
            )

    def _detect_signal_timing(
        self,
        signals: pd.DataFrame,
        returns: pd.DataFrame,
    ) -> None:
        """
        检测信号时序问题

        方法: 信号应与下一期收益相关，而非当期
        """
        common_dates = signals.index.intersection(returns.index)
        common_symbols = signals.columns.intersection(returns.columns)

        if len(common_dates) < 20:
            return

        sig = signals.loc[common_dates, common_symbols]
        ret = returns.loc[common_dates, common_symbols]

        # 计算信号与 T+0 和 T+1 收益的相关性
        t0_corrs = []
        t1_corrs = []

        for i, dt in enumerate(common_dates[:-1]):
            next_dt = common_dates[i + 1]

            sig_row = sig.loc[dt].dropna()
            ret_t0 = ret.loc[dt].dropna()
            ret_t1 = ret.loc[next_dt].dropna()

            common_t0 = sig_row.index.intersection(ret_t0.index)
            common_t1 = sig_row.index.intersection(ret_t1.index)

            if len(common_t0) > 10:
                c0 = sig_row[common_t0].corr(ret_t0[common_t0])
                if not np.isnan(c0):
                    t0_corrs.append(c0)

            if len(common_t1) > 10:
                c1 = sig_row[common_t1].corr(ret_t1[common_t1])
                if not np.isnan(c1):
                    t1_corrs.append(c1)

        if not t0_corrs or not t1_corrs:
            return

        avg_t0 = np.mean(t0_corrs)
        avg_t1 = np.mean(t1_corrs)

        # T+0 相关性应该接近 0，T+1 应该为正
        if avg_t0 > avg_t1 and avg_t0 > 0.1:
            self.report.add_warning(
                LookaheadWarning(
                    type=LookaheadType.SIGNAL_LOOKAHEAD,
                    severity="critical" if avg_t0 > 0.3 else "high",
                    description=f"信号与 T+0 收益相关性 ({avg_t0:.3f}) 高于 T+1 ({avg_t1:.3f})，存在严重前视偏差",
                    evidence={
                        "t0_correlation": float(avg_t0),
                        "t1_correlation": float(avg_t1),
                        "ratio": float(avg_t0 / avg_t1) if avg_t1 != 0 else float("inf"),
                    },
                )
            )

    def _detect_fundamental_lookahead(
        self,
        signals: pd.DataFrame,
        financial_data: pd.DataFrame,
    ) -> None:
        """
        检测财务数据前视偏差

        方法: 检查是否使用了 report_date 而非 release_date
        """
        required_cols = {"report_date", "release_date", "symbol"}
        if not required_cols.issubset(financial_data.columns):
            logger.warning("财务数据缺少必要列，跳过财务前视检测")
            return

        # 检查是否有 release_date 晚于 report_date 的情况
        fin = financial_data.copy()
        fin["report_date"] = pd.to_datetime(fin["report_date"])
        fin["release_date"] = pd.to_datetime(fin["release_date"])

        # 计算发布延迟
        fin["delay_days"] = (fin["release_date"] - fin["report_date"]).dt.days

        # 检查信号日期是否在 release_date 之后
        issues = []
        for dt in signals.index:
            signal_date = pd.Timestamp(dt)
            active_symbols = signals.loc[dt][signals.loc[dt] != 0].index.tolist()

            for symbol in active_symbols:
                symbol_fin = fin[fin["symbol"] == symbol]
                if symbol_fin.empty:
                    continue

                # 查找在信号日期之后发布但报告日期在之前的数据
                lookahead = symbol_fin[
                    (symbol_fin["report_date"] <= signal_date) &
                    (symbol_fin["release_date"] > signal_date)
                ]

                if not lookahead.empty:
                    issues.append({
                        "date": dt,
                        "symbol": symbol,
                        "unreleased_reports": len(lookahead),
                    })

        if issues:
            affected_symbols = list(set(i["symbol"] for i in issues))
            affected_dates = list(set(i["date"] for i in issues))

            self.report.add_warning(
                LookaheadWarning(
                    type=LookaheadType.FUNDAMENTAL_LOOKAHEAD,
                    severity="critical",
                    description=f"检测到 {len(issues)} 处使用未发布财报数据的情况",
                    affected_dates=affected_dates[:20],
                    affected_symbols=affected_symbols[:20],
                    evidence={
                        "total_issues": len(issues),
                        "affected_symbols_count": len(affected_symbols),
                        "affected_dates_count": len(affected_dates),
                    },
                )
            )

    def _detect_universe_lookahead(
        self,
        signals: pd.DataFrame,
        universe_snapshots: dict[date, list[str]],
    ) -> None:
        """
        检测股票池前视偏差

        方法: 检查是否使用了当时不存在的股票池成分
        """
        issues = []

        snapshot_dates = sorted(universe_snapshots.keys())
        if not snapshot_dates:
            return

        for dt in signals.index:
            signal_date = dt.date() if hasattr(dt, "date") else dt
            active_symbols = signals.loc[dt][signals.loc[dt] != 0].index.tolist()

            # 找到该日期适用的股票池快照
            applicable_snapshots = [d for d in snapshot_dates if d <= signal_date]
            if not applicable_snapshots:
                continue

            valid_universe = set(universe_snapshots[applicable_snapshots[-1]])

            # 检查是否有不在当时股票池中的股票
            invalid_symbols = [s for s in active_symbols if s not in valid_universe]

            if invalid_symbols:
                issues.append({
                    "date": signal_date,
                    "invalid_symbols": invalid_symbols,
                    "valid_snapshot_date": applicable_snapshots[-1],
                })

        if issues:
            all_invalid = set()
            for i in issues:
                all_invalid.update(i["invalid_symbols"])

            self.report.add_warning(
                LookaheadWarning(
                    type=LookaheadType.UNIVERSE_LOOKAHEAD,
                    severity="high",
                    description=f"检测到 {len(issues)} 个日期使用了当时不在股票池中的股票",
                    affected_dates=[i["date"] for i in issues[:20]],
                    affected_symbols=list(all_invalid)[:20],
                    evidence={
                        "total_issues": len(issues),
                        "unique_invalid_symbols": len(all_invalid),
                    },
                )
            )


def quick_lookahead_check(
    signals: pd.DataFrame,
    returns: pd.DataFrame,
) -> bool:
    """
    快速前视偏差检查

    Args:
        signals: 交易信号
        returns: 收益率

    Returns:
        True 如果可能存在前视偏差
    """
    detector = LookaheadDetector()
    report = detector.detect_all(signals, returns)
    return not report.is_clean
