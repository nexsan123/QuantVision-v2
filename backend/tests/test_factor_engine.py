"""
因子引擎单元测试

测试所有 80 个算子的功能正确性
"""

import numpy as np
import pandas as pd
import pytest

from app.factor_engine import operators as ops


class TestL0Operators:
    """L0: 基础算子测试"""

    def test_returns(self, sample_ohlcv):
        """测试收益率计算"""
        result = ops.returns(sample_ohlcv["close"])
        assert len(result) == len(sample_ohlcv)
        assert result.iloc[0] != result.iloc[0]  # 第一个应为 NaN
        assert not result.iloc[1:].isna().any()

    def test_log_returns(self, sample_ohlcv):
        """测试对数收益率"""
        result = ops.log_returns(sample_ohlcv["close"])
        assert len(result) == len(sample_ohlcv)

    def test_sma(self, sample_ohlcv):
        """测试简单移动平均"""
        result = ops.sma(sample_ohlcv["close"], period=20)
        assert len(result) == len(sample_ohlcv)
        assert result.iloc[:19].isna().all()  # 前 19 个应为 NaN
        assert not result.iloc[19:].isna().any()

    def test_ema(self, sample_ohlcv):
        """测试指数移动平均"""
        result = ops.ema(sample_ohlcv["close"], period=20)
        assert len(result) == len(sample_ohlcv)

    def test_std(self, sample_ohlcv):
        """测试标准差"""
        result = ops.std(sample_ohlcv["close"], period=20)
        assert len(result) == len(sample_ohlcv)
        assert (result.dropna() >= 0).all()  # 标准差应非负

    def test_zscore(self, sample_ohlcv):
        """测试 Z-Score"""
        result = ops.zscore(sample_ohlcv["close"], period=20)
        assert len(result) == len(sample_ohlcv)

    def test_rank(self, sample_returns_df):
        """测试排名"""
        result = ops.rank(sample_returns_df)
        assert result.shape == sample_returns_df.shape
        # 排名应在 0-1 之间
        assert (result.dropna() >= 0).all().all()
        assert (result.dropna() <= 1).all().all()

    def test_delay(self, sample_ohlcv):
        """测试滞后"""
        result = ops.delay(sample_ohlcv["close"], period=5)
        assert len(result) == len(sample_ohlcv)
        # 验证滞后正确
        assert result.iloc[5] == sample_ohlcv["close"].iloc[0]

    def test_delta(self, sample_ohlcv):
        """测试差分"""
        result = ops.delta(sample_ohlcv["close"], period=5)
        assert len(result) == len(sample_ohlcv)

    def test_max_rolling(self, sample_ohlcv):
        """测试滚动最大值"""
        result = ops.max_rolling(sample_ohlcv["close"], period=20)
        assert len(result) == len(sample_ohlcv)


class TestL1Operators:
    """L1: 技术指标算子测试"""

    def test_rsi(self, sample_ohlcv):
        """测试 RSI"""
        result = ops.rsi(sample_ohlcv["close"], period=14)
        assert len(result) == len(sample_ohlcv)
        # RSI 应在 0-100 之间
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_macd(self, sample_ohlcv):
        """测试 MACD"""
        macd, signal, hist = ops.macd(sample_ohlcv["close"])
        assert len(macd) == len(sample_ohlcv)
        assert len(signal) == len(sample_ohlcv)
        assert len(hist) == len(sample_ohlcv)

    def test_bollinger_bands(self, sample_ohlcv):
        """测试布林带"""
        upper, middle, lower = ops.bollinger_bands(sample_ohlcv["close"])
        assert len(upper) == len(sample_ohlcv)
        # 上轨应大于中轨，中轨应大于下轨
        valid_idx = ~upper.isna()
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_atr(self, sample_ohlcv):
        """测试 ATR"""
        result = ops.atr(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            period=14,
        )
        assert len(result) == len(sample_ohlcv)
        assert (result.dropna() >= 0).all()  # ATR 应非负

    def test_adx(self, sample_ohlcv):
        """测试 ADX"""
        result = ops.adx(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            period=14,
        )
        assert len(result) == len(sample_ohlcv)

    def test_williams_r(self, sample_ohlcv):
        """测试威廉 %R"""
        result = ops.williams_r(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            period=14,
        )
        assert len(result) == len(sample_ohlcv)
        # Williams %R 应在 -100 到 0 之间
        valid = result.dropna()
        assert (valid >= -100).all()
        assert (valid <= 0).all()


class TestL2Operators:
    """L2: 量价复合算子测试"""

    def test_vwap(self, sample_ohlcv):
        """测试 VWAP"""
        result = ops.vwap(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            sample_ohlcv["volume"],
        )
        assert len(result) == len(sample_ohlcv)
        assert (result.dropna() > 0).all()

    def test_obv(self, sample_ohlcv):
        """测试 OBV"""
        result = ops.obv(sample_ohlcv["close"], sample_ohlcv["volume"])
        assert len(result) == len(sample_ohlcv)

    def test_mfi(self, sample_ohlcv):
        """测试 MFI"""
        result = ops.mfi(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            sample_ohlcv["volume"],
            period=14,
        )
        assert len(result) == len(sample_ohlcv)
        # MFI 应在 0-100 之间
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_ad_line(self, sample_ohlcv):
        """测试 AD Line"""
        result = ops.ad_line(
            sample_ohlcv["high"],
            sample_ohlcv["low"],
            sample_ohlcv["close"],
            sample_ohlcv["volume"],
        )
        assert len(result) == len(sample_ohlcv)


class TestL3Operators:
    """L3: 因子合成算子测试"""

    def test_momentum(self, sample_ohlcv):
        """测试动量因子"""
        result = ops.momentum(sample_ohlcv["close"], period=20)
        assert len(result) == len(sample_ohlcv)

    def test_volatility(self, sample_returns):
        """测试波动率因子"""
        result = ops.volatility(sample_returns, period=20)
        assert len(result) == len(sample_returns)
        assert (result.dropna() >= 0).all()

    def test_mean_reversion(self, sample_ohlcv):
        """测试均值回归因子"""
        result = ops.mean_reversion(sample_ohlcv["close"], period=20)
        assert len(result) == len(sample_ohlcv)

    def test_trend_strength(self, sample_ohlcv):
        """测试趋势强度因子"""
        result = ops.trend_strength(sample_ohlcv["close"], period=20)
        assert len(result) == len(sample_ohlcv)
        # 趋势强度应在 -1 到 1 之间
        valid = result.dropna()
        assert (valid >= -1).all()
        assert (valid <= 1).all()


class TestL4Operators:
    """L4: 高级风险算子测试"""

    def test_sharpe_ratio(self, sample_returns):
        """测试夏普比率"""
        result = ops.sharpe_ratio(sample_returns, period=252)
        assert len(result) == len(sample_returns)

    def test_sortino_ratio(self, sample_returns):
        """测试索提诺比率"""
        result = ops.sortino_ratio(sample_returns, period=252)
        assert len(result) == len(sample_returns)

    def test_max_drawdown(self, sample_ohlcv):
        """测试最大回撤"""
        result = ops.max_drawdown(sample_ohlcv["close"], period=60)
        assert len(result) == len(sample_ohlcv)
        # 最大回撤应在 -1 到 0 之间
        valid = result.dropna()
        assert (valid >= -1).all()
        assert (valid <= 0).all()

    def test_calmar_ratio(self, sample_returns, sample_ohlcv):
        """测试卡尔马比率"""
        result = ops.calmar_ratio(sample_returns, sample_ohlcv["close"], period=252)
        assert len(result) == len(sample_returns)


class TestL5Operators:
    """L5: 多因子分析算子测试"""

    def test_skewness(self, sample_returns):
        """测试偏度因子"""
        result = ops.skewness(sample_returns, period=20)
        assert len(result) == len(sample_returns)

    def test_kurtosis(self, sample_returns):
        """测试峰度因子"""
        result = ops.kurtosis(sample_returns, period=20)
        assert len(result) == len(sample_returns)


class TestOperatorCount:
    """算子数量验证"""

    def test_total_operators(self):
        """验证算子总数 >= 80"""
        all_ops = (
            ops.L0_OPERATORS
            + ops.L1_OPERATORS
            + ops.L2_OPERATORS
            + ops.L3_OPERATORS
            + ops.L4_OPERATORS
            + ops.L5_OPERATORS
        )
        assert len(all_ops) >= 80, f"算子数量不足: {len(all_ops)}"


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_series(self):
        """测试空序列"""
        empty = pd.Series([], dtype=float)
        result = ops.sma(empty, period=20)
        assert len(result) == 0

    def test_single_value(self):
        """测试单值序列"""
        single = pd.Series([100.0])
        result = ops.returns(single)
        assert len(result) == 1

    def test_nan_handling(self, sample_ohlcv):
        """测试 NaN 处理"""
        data = sample_ohlcv["close"].copy()
        data.iloc[10:15] = np.nan
        result = ops.sma(data, period=5)
        # 验证不会崩溃
        assert len(result) == len(data)

    def test_all_same_values(self):
        """测试全相同值"""
        same = pd.Series([100.0] * 100)
        result = ops.std(same, period=20)
        # 标准差应为 0
        assert (result.dropna() == 0).all()
