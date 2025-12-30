"""
交易信号生成器

提供:
- 因子信号生成
- 信号组合
- 信号平滑
- 信号转换为权重
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pandas as pd
import structlog

from app.strategy.constraints import PortfolioConstraints, apply_constraints

logger = structlog.get_logger()


class SignalType(str, Enum):
    """信号类型"""
    LONG_ONLY = "long_only"         # 只做多
    LONG_SHORT = "long_short"       # 多空
    DOLLAR_NEUTRAL = "dollar_neutral"  # 美元中性
    BETA_NEUTRAL = "beta_neutral"   # Beta 中性
    SECTOR_NEUTRAL = "sector_neutral"  # 行业中性


class SignalScaling(str, Enum):
    """信号缩放方法"""
    RANK = "rank"                   # 排名
    ZSCORE = "zscore"               # Z-score
    PERCENTILE = "percentile"       # 百分位
    MINMAX = "minmax"               # Min-Max 归一化
    WINSORIZE = "winsorize"         # 截尾
    RAW = "raw"                     # 原始值


@dataclass
class SignalConfig:
    """信号配置"""
    signal_type: SignalType = SignalType.LONG_ONLY
    scaling: SignalScaling = SignalScaling.RANK
    top_n: int | None = None            # 选取前 N 名
    top_pct: float | None = None        # 选取前 N%
    bottom_n: int | None = None         # 选取后 N 名 (做空)
    bottom_pct: float | None = None     # 选取后 N%
    min_signal: float = 0.0             # 信号阈值
    decay: float = 0.0                  # 信号衰减 (0-1)
    smooth_window: int = 1              # 平滑窗口


@dataclass
class SignalOutput:
    """信号输出"""
    weights: pd.DataFrame               # 目标权重 (index=date, columns=symbols)
    signals: pd.DataFrame               # 原始信号
    long_count: pd.Series = field(default_factory=pd.Series)   # 多头数量
    short_count: pd.Series = field(default_factory=pd.Series)  # 空头数量
    turnover: pd.Series = field(default_factory=pd.Series)     # 换手率
    metadata: dict[str, Any] = field(default_factory=dict)


class SignalGenerator:
    """
    信号生成器

    将因子值转换为交易信号/权重:
    1. 标准化/缩放因子值
    2. 筛选信号 (Top N / 阈值)
    3. 计算权重
    4. 应用约束
    """

    def __init__(
        self,
        config: SignalConfig | None = None,
        constraints: PortfolioConstraints | None = None,
    ):
        """
        Args:
            config: 信号配置
            constraints: 组合约束
        """
        self.config = config or SignalConfig()
        self.constraints = constraints or PortfolioConstraints()

    def generate(
        self,
        factor_data: pd.DataFrame,
        sector_map: dict[str, str] | None = None,
        betas: pd.DataFrame | None = None,
    ) -> SignalOutput:
        """
        生成交易信号

        Args:
            factor_data: 因子数据 (index=date, columns=symbols)
            sector_map: 资产-行业映射
            betas: 资产 Beta 值 (index=date, columns=symbols)

        Returns:
            信号输出
        """
        # 1. 缩放因子值
        scaled = self._scale_signals(factor_data)

        # 2. 筛选信号
        selected = self._select_signals(scaled)

        # 3. 转换为权重
        weights = self._signals_to_weights(selected, sector_map, betas)

        # 4. 应用约束
        constrained = self._apply_constraints(weights)

        # 5. 平滑处理
        if self.config.smooth_window > 1:
            constrained = constrained.rolling(
                self.config.smooth_window, min_periods=1
            ).mean()

        # 6. 计算元数据
        long_count = (constrained > 0).sum(axis=1)
        short_count = (constrained < 0).sum(axis=1)
        turnover = constrained.diff().abs().sum(axis=1) / 2

        logger.info(
            "信号生成完成",
            signal_type=self.config.signal_type.value,
            dates=len(constrained),
            avg_long=long_count.mean(),
            avg_short=short_count.mean(),
            avg_turnover=turnover.mean(),
        )

        return SignalOutput(
            weights=constrained,
            signals=scaled,
            long_count=long_count,
            short_count=short_count,
            turnover=turnover,
        )

    def _scale_signals(self, factor_data: pd.DataFrame) -> pd.DataFrame:
        """缩放信号"""
        if self.config.scaling == SignalScaling.RANK:
            # 截面排名 (0-1)
            return factor_data.rank(axis=1, pct=True)

        elif self.config.scaling == SignalScaling.ZSCORE:
            # 截面 Z-score
            mean = factor_data.mean(axis=1)
            std = factor_data.std(axis=1)
            return factor_data.sub(mean, axis=0).div(std, axis=0)

        elif self.config.scaling == SignalScaling.PERCENTILE:
            # 百分位
            return factor_data.rank(axis=1, pct=True) * 100

        elif self.config.scaling == SignalScaling.MINMAX:
            # Min-Max 归一化
            min_val = factor_data.min(axis=1)
            max_val = factor_data.max(axis=1)
            range_val = max_val - min_val
            return factor_data.sub(min_val, axis=0).div(range_val, axis=0)

        elif self.config.scaling == SignalScaling.WINSORIZE:
            # 截尾 (1%, 99%)
            lower = factor_data.quantile(0.01, axis=1)
            upper = factor_data.quantile(0.99, axis=1)
            return factor_data.clip(lower, upper, axis=0)

        else:  # RAW
            return factor_data.copy()

    def _select_signals(self, scaled: pd.DataFrame) -> pd.DataFrame:
        """筛选信号"""
        result = pd.DataFrame(0.0, index=scaled.index, columns=scaled.columns)

        for dt in scaled.index:
            row = scaled.loc[dt].dropna()
            if row.empty:
                continue

            # 选择多头
            if self.config.top_n:
                top_assets = row.nlargest(self.config.top_n).index
                result.loc[dt, top_assets] = 1.0
            elif self.config.top_pct:
                n = max(1, int(len(row) * self.config.top_pct))
                top_assets = row.nlargest(n).index
                result.loc[dt, top_assets] = 1.0
            else:
                # 使用阈值或全部
                above_threshold = row[row >= self.config.min_signal].index
                result.loc[dt, above_threshold] = row[above_threshold]

            # 选择空头 (多空策略)
            if self.config.signal_type in [
                SignalType.LONG_SHORT,
                SignalType.DOLLAR_NEUTRAL,
            ]:
                if self.config.bottom_n:
                    bottom_assets = row.nsmallest(self.config.bottom_n).index
                    result.loc[dt, bottom_assets] = -1.0
                elif self.config.bottom_pct:
                    n = max(1, int(len(row) * self.config.bottom_pct))
                    bottom_assets = row.nsmallest(n).index
                    result.loc[dt, bottom_assets] = -1.0

        return result

    def _signals_to_weights(
        self,
        signals: pd.DataFrame,
        sector_map: dict[str, str] | None,
        betas: pd.DataFrame | None,
    ) -> pd.DataFrame:
        """信号转换为权重"""
        weights = signals.copy()

        if self.config.signal_type == SignalType.LONG_ONLY:
            # 只做多: 归一化正信号
            weights = weights.clip(lower=0)
            row_sum = weights.sum(axis=1).replace(0, 1)
            weights = weights.div(row_sum, axis=0)

        elif self.config.signal_type == SignalType.LONG_SHORT:
            # 多空: 多头 50%, 空头 50%
            long_weights = weights.clip(lower=0)
            short_weights = weights.clip(upper=0).abs()

            long_sum = long_weights.sum(axis=1).replace(0, 1)
            short_sum = short_weights.sum(axis=1).replace(0, 1)

            long_weights = long_weights.div(long_sum, axis=0) * 0.5
            short_weights = short_weights.div(short_sum, axis=0) * 0.5

            weights = long_weights - short_weights

        elif self.config.signal_type == SignalType.DOLLAR_NEUTRAL:
            # 美元中性: 多头总权重 = 空头总权重
            long_weights = weights.clip(lower=0)
            short_weights = weights.clip(upper=0).abs()

            long_sum = long_weights.sum(axis=1).replace(0, 1)
            short_sum = short_weights.sum(axis=1).replace(0, 1)

            # 多空各 50%
            long_weights = long_weights.div(long_sum, axis=0) * 0.5
            short_weights = short_weights.div(short_sum, axis=0) * 0.5

            weights = long_weights - short_weights

        elif self.config.signal_type == SignalType.BETA_NEUTRAL:
            # Beta 中性: 调整权重使组合 Beta = 0
            if betas is None:
                logger.warning("未提供 Beta 数据，使用美元中性")
                return self._signals_to_weights(
                    signals,
                    sector_map,
                    None,
                )

            for dt in weights.index:
                row = weights.loc[dt]
                beta_row = betas.loc[dt] if dt in betas.index else pd.Series(1.0, index=row.index)

                # 计算需要的空头 Beta 以对冲多头
                long_mask = row > 0
                short_mask = row < 0

                long_beta = (row[long_mask] * beta_row[long_mask]).sum()

                if short_mask.any():
                    short_beta = beta_row[short_mask].mean()
                    if short_beta != 0:
                        # 调整空头权重
                        short_scale = long_beta / short_beta
                        weights.loc[dt, short_mask] *= short_scale

        elif self.config.signal_type == SignalType.SECTOR_NEUTRAL:
            # 行业中性: 每个行业多空对冲
            if sector_map is None:
                logger.warning("未提供行业映射，使用美元中性")
                return self._signals_to_weights(
                    signals,
                    None,
                    betas,
                )

            for dt in weights.index:
                row = weights.loc[dt]
                sectors = pd.Series({a: sector_map.get(a, "Unknown") for a in row.index})

                for sector in sectors.unique():
                    sector_mask = sectors == sector
                    sector_weights = row[sector_mask]

                    # 行业内做多空对冲
                    long_w = sector_weights.clip(lower=0)
                    short_w = sector_weights.clip(upper=0).abs()

                    if long_w.sum() > 0 and short_w.sum() > 0:
                        # 归一化使多空相等
                        scale = min(long_w.sum(), short_w.sum())
                        long_w = long_w / long_w.sum() * scale
                        short_w = short_w / short_w.sum() * scale
                        weights.loc[dt, sector_mask] = long_w - short_w

        return weights

    def _apply_constraints(self, weights: pd.DataFrame) -> pd.DataFrame:
        """应用组合约束"""
        result = weights.copy()

        for dt in result.index:
            row = result.loc[dt]
            adjusted = apply_constraints(row, self.constraints)
            result.loc[dt] = adjusted

        return result


# === 便捷函数 ===

def generate_equal_weight_signals(
    universe: list[str],
    dates: pd.DatetimeIndex,
) -> pd.DataFrame:
    """生成等权重信号"""
    n = len(universe)
    weight = 1.0 / n if n > 0 else 0.0
    return pd.DataFrame(
        weight,
        index=dates,
        columns=universe,
    )


def generate_top_n_signals(
    factor_data: pd.DataFrame,
    n: int = 50,
    long_only: bool = True,
) -> pd.DataFrame:
    """生成 Top N 信号"""
    config = SignalConfig(
        signal_type=SignalType.LONG_ONLY if long_only else SignalType.LONG_SHORT,
        scaling=SignalScaling.RANK,
        top_n=n,
        bottom_n=n if not long_only else None,
    )
    generator = SignalGenerator(config=config)
    output = generator.generate(factor_data)
    return output.weights


def generate_quantile_signals(
    factor_data: pd.DataFrame,
    long_quantile: float = 0.2,
    short_quantile: float = 0.2,
) -> pd.DataFrame:
    """生成分位数信号"""
    config = SignalConfig(
        signal_type=SignalType.LONG_SHORT,
        scaling=SignalScaling.RANK,
        top_pct=long_quantile,
        bottom_pct=short_quantile,
    )
    generator = SignalGenerator(config=config)
    output = generator.generate(factor_data)
    return output.weights


def combine_signals(
    signals: list[pd.DataFrame],
    weights: list[float] | None = None,
) -> pd.DataFrame:
    """
    组合多个信号

    Args:
        signals: 信号列表
        weights: 信号权重 (默认等权)

    Returns:
        组合信号
    """
    if not signals:
        return pd.DataFrame()

    if weights is None:
        weights = [1.0 / len(signals)] * len(signals)

    # 对齐所有信号
    combined = signals[0] * weights[0]
    for sig, w in zip(signals[1:], weights[1:]):
        combined = combined.add(sig * w, fill_value=0)

    return combined
