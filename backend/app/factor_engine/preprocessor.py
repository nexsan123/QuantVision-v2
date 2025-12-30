"""
因子预处理模块

提供因子数据预处理:
- 缺失值处理
- 异常值处理
- 标准化
- 中性化
"""

from enum import Enum

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


class FillMethod(str, Enum):
    """缺失值填充方法"""
    NONE = "none"           # 不填充
    ZERO = "zero"           # 填充 0
    MEAN = "mean"           # 横截面均值
    MEDIAN = "median"       # 横截面中位数
    FFILL = "ffill"         # 前向填充
    BFILL = "bfill"         # 后向填充


class OutlierMethod(str, Enum):
    """异常值处理方法"""
    NONE = "none"           # 不处理
    WINSORIZE = "winsorize" # 缩尾
    MAD = "mad"             # MAD 方法
    ZSCORE = "zscore"       # Z-score 截断


class NormalizeMethod(str, Enum):
    """标准化方法"""
    NONE = "none"           # 不标准化
    ZSCORE = "zscore"       # Z-score 标准化
    RANK = "rank"           # 排名标准化
    MINMAX = "minmax"       # 最小最大标准化


class FactorPreprocessor:
    """
    因子预处理器

    处理流程:
    1. 缺失值处理
    2. 异常值处理
    3. 标准化
    4. (可选) 行业/市值中性化
    """

    def __init__(
        self,
        fill_method: FillMethod = FillMethod.MEDIAN,
        outlier_method: OutlierMethod = OutlierMethod.WINSORIZE,
        normalize_method: NormalizeMethod = NormalizeMethod.ZSCORE,
        winsorize_bounds: tuple[float, float] = (0.01, 0.99),
        zscore_threshold: float = 3.0,
        mad_threshold: float = 5.0,
    ):
        self.fill_method = fill_method
        self.outlier_method = outlier_method
        self.normalize_method = normalize_method
        self.winsorize_bounds = winsorize_bounds
        self.zscore_threshold = zscore_threshold
        self.mad_threshold = mad_threshold

    def process(
        self,
        factor: pd.DataFrame,
        industry: pd.DataFrame | None = None,
        market_cap: pd.Series | None = None,
    ) -> pd.DataFrame:
        """
        完整预处理流程

        Args:
            factor: 因子值 DataFrame (index=date, columns=symbols)
            industry: 行业分类 (用于行业中性化)
            market_cap: 市值 (用于市值中性化)

        Returns:
            预处理后的因子值
        """
        result = factor.copy()

        # 1. 缺失值处理
        result = self.handle_missing(result)

        # 2. 异常值处理
        result = self.handle_outliers(result)

        # 3. 标准化
        result = self.normalize(result)

        # 4. 中性化 (如果提供了行业/市值)
        if industry is not None:
            result = self.neutralize_industry(result, industry)

        if market_cap is not None:
            result = self.neutralize_market_cap(result, market_cap)

        logger.info(
            "因子预处理完成",
            fill=self.fill_method.value,
            outlier=self.outlier_method.value,
            normalize=self.normalize_method.value,
        )

        return result

    def handle_missing(self, factor: pd.DataFrame) -> pd.DataFrame:
        """
        处理缺失值

        Args:
            factor: 因子值 DataFrame

        Returns:
            处理后的 DataFrame
        """
        if self.fill_method == FillMethod.NONE:
            return factor

        result = factor.copy()

        if self.fill_method == FillMethod.ZERO:
            result = result.fillna(0)

        elif self.fill_method == FillMethod.MEAN:
            # 横截面均值填充
            row_mean = result.mean(axis=1)
            result = result.T.fillna(row_mean).T

        elif self.fill_method == FillMethod.MEDIAN:
            # 横截面中位数填充
            row_median = result.median(axis=1)
            result = result.T.fillna(row_median).T

        elif self.fill_method == FillMethod.FFILL:
            result = result.ffill()

        elif self.fill_method == FillMethod.BFILL:
            result = result.bfill()

        return result

    def handle_outliers(self, factor: pd.DataFrame) -> pd.DataFrame:
        """
        处理异常值

        Args:
            factor: 因子值 DataFrame

        Returns:
            处理后的 DataFrame
        """
        if self.outlier_method == OutlierMethod.NONE:
            return factor

        result = factor.copy()

        if self.outlier_method == OutlierMethod.WINSORIZE:
            # 缩尾处理
            lower, upper = self.winsorize_bounds
            for dt in result.index:
                row = result.loc[dt]
                lower_bound = row.quantile(lower)
                upper_bound = row.quantile(upper)
                result.loc[dt] = row.clip(lower_bound, upper_bound)

        elif self.outlier_method == OutlierMethod.MAD:
            # MAD (Median Absolute Deviation) 方法
            for dt in result.index:
                row = result.loc[dt]
                median = row.median()
                mad = (row - median).abs().median()
                if mad > 0:
                    threshold = self.mad_threshold * mad
                    result.loc[dt] = row.clip(
                        median - threshold,
                        median + threshold,
                    )

        elif self.outlier_method == OutlierMethod.ZSCORE:
            # Z-score 截断
            for dt in result.index:
                row = result.loc[dt]
                mean = row.mean()
                std = row.std()
                if std > 0:
                    threshold = self.zscore_threshold * std
                    result.loc[dt] = row.clip(
                        mean - threshold,
                        mean + threshold,
                    )

        return result

    def normalize(self, factor: pd.DataFrame) -> pd.DataFrame:
        """
        标准化

        Args:
            factor: 因子值 DataFrame

        Returns:
            标准化后的 DataFrame
        """
        if self.normalize_method == NormalizeMethod.NONE:
            return factor

        result = factor.copy()

        if self.normalize_method == NormalizeMethod.ZSCORE:
            # Z-score 标准化
            row_mean = result.mean(axis=1)
            row_std = result.std(axis=1)
            result = result.sub(row_mean, axis=0).div(row_std, axis=0)

        elif self.normalize_method == NormalizeMethod.RANK:
            # 排名标准化 (0-1)
            result = result.rank(axis=1, pct=True)

        elif self.normalize_method == NormalizeMethod.MINMAX:
            # 最小最大标准化 (0-1)
            row_min = result.min(axis=1)
            row_max = result.max(axis=1)
            row_range = row_max - row_min
            result = result.sub(row_min, axis=0).div(row_range, axis=0)

        return result

    def neutralize_industry(
        self,
        factor: pd.DataFrame,
        industry: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        行业中性化

        减去行业均值，消除行业因素影响

        Args:
            factor: 因子值 DataFrame
            industry: 行业分类 DataFrame (one-hot 编码或行业代码)

        Returns:
            中性化后的 DataFrame
        """
        result = factor.copy()

        for dt in result.index:
            if dt not in industry.index:
                continue

            row = result.loc[dt]
            ind = industry.loc[dt]

            # 如果是 one-hot 编码
            if isinstance(ind, pd.DataFrame):
                for col in ind.columns:
                    mask = ind[col] == 1
                    if mask.sum() > 0:
                        ind_mean = row[mask].mean()
                        result.loc[dt, mask] = row[mask] - ind_mean
            else:
                # 如果是行业代码
                for ind_code in ind.unique():
                    if pd.isna(ind_code):
                        continue
                    mask = ind == ind_code
                    if mask.sum() > 0:
                        ind_mean = row[mask].mean()
                        result.loc[dt, mask] = row[mask] - ind_mean

        return result

    def neutralize_market_cap(
        self,
        factor: pd.DataFrame,
        market_cap: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        市值中性化

        使用线性回归去除市值因素

        Args:
            factor: 因子值 DataFrame
            market_cap: 市值 DataFrame (对数值)

        Returns:
            中性化后的 DataFrame
        """
        result = factor.copy()

        for dt in result.index:
            if dt not in market_cap.index:
                continue

            f = result.loc[dt].dropna()
            mc = market_cap.loc[dt].dropna()

            common = f.index.intersection(mc.index)
            if len(common) < 10:
                continue

            f = f[common]
            mc = mc[common]

            # 对数市值
            log_mc = np.log(mc)

            # 线性回归
            X = np.column_stack([np.ones(len(log_mc)), log_mc])
            beta = np.linalg.lstsq(X, f.values, rcond=None)[0]

            # 残差
            residual = f - (beta[0] + beta[1] * log_mc)
            result.loc[dt, common] = residual

        return result
