"""
数据质量服务

提供:
- 缺失值检测
- 异常值检测
- 数据一致性检查
- 质量评分
"""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import structlog

logger = structlog.get_logger()


@dataclass
class QualityReport:
    """数据质量报告"""

    # 基本统计
    total_records: int = 0
    missing_count: int = 0
    anomaly_count: int = 0

    # 缺失详情
    missing_by_column: dict[str, int] = field(default_factory=dict)
    missing_by_symbol: dict[str, int] = field(default_factory=dict)

    # 异常详情
    anomalies: list[dict[str, Any]] = field(default_factory=list)

    # 质量评分
    completeness_score: float = 0.0  # 完整性 (0-100)
    validity_score: float = 0.0       # 有效性 (0-100)
    consistency_score: float = 0.0    # 一致性 (0-100)
    overall_score: float = 0.0        # 综合评分 (0-100)

    @property
    def missing_rate(self) -> float:
        """缺失率"""
        if self.total_records == 0:
            return 0.0
        return self.missing_count / self.total_records * 100

    @property
    def anomaly_rate(self) -> float:
        """异常率"""
        if self.total_records == 0:
            return 0.0
        return self.anomaly_count / self.total_records * 100


class DataQualityService:
    """
    数据质量检测服务

    检测规则:
    1. 缺失值: NULL, NaN, 空字符串
    2. 异常值: 基于统计方法 (IQR, Z-score)
    3. 逻辑一致性: 业务规则校验
    """

    def __init__(
        self,
        z_score_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
    ):
        self.z_score_threshold = z_score_threshold
        self.iqr_multiplier = iqr_multiplier

    def check_ohlcv(self, df: pd.DataFrame) -> QualityReport:
        """
        检查 OHLCV 数据质量

        Args:
            df: OHLCV DataFrame

        Returns:
            质量报告
        """
        report = QualityReport(total_records=len(df))

        # 1. 缺失值检测
        self._check_missing(df, report)

        # 2. 价格有效性检测
        self._check_price_validity(df, report)

        # 3. 逻辑一致性检测
        self._check_ohlcv_consistency(df, report)

        # 4. 异常值检测 (基于收益率)
        self._check_return_anomalies(df, report)

        # 计算评分
        self._calculate_scores(report)

        logger.info(
            "OHLCV 数据质量检查完成",
            total=report.total_records,
            missing_rate=f"{report.missing_rate:.2f}%",
            anomaly_rate=f"{report.anomaly_rate:.2f}%",
            score=f"{report.overall_score:.1f}",
        )

        return report

    def check_financials(self, df: pd.DataFrame) -> QualityReport:
        """
        检查财务数据质量

        Args:
            df: 财务数据 DataFrame

        Returns:
            质量报告
        """
        report = QualityReport(total_records=len(df))

        # 1. 缺失值检测
        self._check_missing(df, report)

        # 2. 财务指标有效性
        self._check_financial_validity(df, report)

        # 3. 计算评分
        self._calculate_scores(report)

        logger.info(
            "财务数据质量检查完成",
            total=report.total_records,
            missing_rate=f"{report.missing_rate:.2f}%",
            score=f"{report.overall_score:.1f}",
        )

        return report

    def _check_missing(self, df: pd.DataFrame, report: QualityReport) -> None:
        """检查缺失值"""
        # 按列统计
        for col in df.columns:
            missing = df[col].isna().sum()
            if missing > 0:
                report.missing_by_column[col] = int(missing)
                report.missing_count += int(missing)

        # 如果有 symbol 列，按股票统计
        if "symbol" in df.index.names:
            for symbol in df.index.get_level_values("symbol").unique():
                symbol_df = df.xs(symbol, level="symbol")
                missing = symbol_df.isna().sum().sum()
                if missing > 0:
                    report.missing_by_symbol[symbol] = int(missing)

    def _check_price_validity(self, df: pd.DataFrame, report: QualityReport) -> None:
        """检查价格有效性"""
        price_cols = ["open", "high", "low", "close"]

        for col in price_cols:
            if col not in df.columns:
                continue

            # 负价格
            negative_mask = df[col] < 0
            if negative_mask.any():
                count = negative_mask.sum()
                report.anomaly_count += int(count)
                report.anomalies.append({
                    "type": "negative_price",
                    "column": col,
                    "count": int(count),
                })

            # 零价格
            zero_mask = df[col] == 0
            if zero_mask.any():
                count = zero_mask.sum()
                report.anomaly_count += int(count)
                report.anomalies.append({
                    "type": "zero_price",
                    "column": col,
                    "count": int(count),
                })

    def _check_ohlcv_consistency(self, df: pd.DataFrame, report: QualityReport) -> None:
        """检查 OHLCV 逻辑一致性"""
        if not all(c in df.columns for c in ["open", "high", "low", "close"]):
            return

        # High >= Low
        invalid_hl = df["high"] < df["low"]
        if invalid_hl.any():
            count = invalid_hl.sum()
            report.anomaly_count += int(count)
            report.anomalies.append({
                "type": "high_less_than_low",
                "count": int(count),
            })

        # High >= Open, Close
        invalid_ho = df["high"] < df["open"]
        invalid_hc = df["high"] < df["close"]
        if invalid_ho.any() or invalid_hc.any():
            count = (invalid_ho | invalid_hc).sum()
            report.anomaly_count += int(count)
            report.anomalies.append({
                "type": "high_not_highest",
                "count": int(count),
            })

        # Low <= Open, Close
        invalid_lo = df["low"] > df["open"]
        invalid_lc = df["low"] > df["close"]
        if invalid_lo.any() or invalid_lc.any():
            count = (invalid_lo | invalid_lc).sum()
            report.anomaly_count += int(count)
            report.anomalies.append({
                "type": "low_not_lowest",
                "count": int(count),
            })

        # 负成交量
        if "volume" in df.columns:
            invalid_vol = df["volume"] < 0
            if invalid_vol.any():
                count = invalid_vol.sum()
                report.anomaly_count += int(count)
                report.anomalies.append({
                    "type": "negative_volume",
                    "count": int(count),
                })

    def _check_return_anomalies(self, df: pd.DataFrame, report: QualityReport) -> None:
        """检查收益率异常"""
        if "close" not in df.columns:
            return

        # 计算日收益率
        if isinstance(df.index, pd.MultiIndex):
            returns = df["close"].unstack().pct_change().stack()
        else:
            returns = df["close"].pct_change()

        # 排除 NaN
        returns = returns.dropna()

        if len(returns) == 0:
            return

        # Z-score 异常检测
        mean = returns.mean()
        std = returns.std()

        if std > 0:
            z_scores = (returns - mean).abs() / std
            anomalies = z_scores > self.z_score_threshold

            if anomalies.any():
                count = anomalies.sum()
                report.anomaly_count += int(count)
                report.anomalies.append({
                    "type": "extreme_return",
                    "method": "z_score",
                    "threshold": self.z_score_threshold,
                    "count": int(count),
                })

    def _check_financial_validity(self, df: pd.DataFrame, report: QualityReport) -> None:
        """检查财务数据有效性"""
        # 总资产应该为正
        if "total_assets" in df.columns:
            invalid = df["total_assets"] <= 0
            if invalid.any():
                count = invalid.sum()
                report.anomaly_count += int(count)
                report.anomalies.append({
                    "type": "invalid_total_assets",
                    "count": int(count),
                })

        # 股东权益可以为负 (但需要标记)
        if "total_equity" in df.columns:
            negative_equity = df["total_equity"] < 0
            if negative_equity.any():
                report.anomalies.append({
                    "type": "negative_equity",
                    "count": int(negative_equity.sum()),
                    "severity": "warning",
                })

    def _calculate_scores(self, report: QualityReport) -> None:
        """计算质量评分"""
        # 完整性: 基于缺失率
        report.completeness_score = max(0, 100 - report.missing_rate)

        # 有效性: 基于异常率
        report.validity_score = max(0, 100 - report.anomaly_rate * 10)

        # 一致性: 基于逻辑检查
        logic_anomalies = sum(
            1 for a in report.anomalies
            if a.get("type") in ["high_less_than_low", "high_not_highest", "low_not_lowest"]
        )
        if report.total_records > 0:
            report.consistency_score = max(0, 100 - logic_anomalies / report.total_records * 100)
        else:
            report.consistency_score = 100

        # 综合评分 (加权平均)
        report.overall_score = (
            report.completeness_score * 0.4 +
            report.validity_score * 0.3 +
            report.consistency_score * 0.3
        )


# 单例服务
_data_quality_service: DataQualityService | None = None


def get_data_quality_service() -> DataQualityService:
    """获取数据质量服务单例"""
    global _data_quality_service
    if _data_quality_service is None:
        _data_quality_service = DataQualityService()
    return _data_quality_service
