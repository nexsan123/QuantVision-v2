"""
因子算子库

提供 50+ 因子计算算子，分为三个层级:
- L0: 核心工具算子 (15个)
- L1: 时间序列算子 (20个)
- L2: 横截面算子 (10个)

所有算子设计遵循:
1. 输入输出一致性: 接受 Series/DataFrame，返回同类型
2. NaN 处理: 保留 NaN，不自动填充
3. 向量化计算: 使用 NumPy/Pandas 原生操作
"""

from typing import Union

import numpy as np
import pandas as pd

# 类型别名
SeriesOrFrame = Union[pd.Series, pd.DataFrame]


# ============================================================================
# Level 0: 核心工具算子 (15个)
# ============================================================================

def rd(x: SeriesOrFrame, decimals: int = 4) -> SeriesOrFrame:
    """
    ROUND: 四舍五入

    Args:
        x: 输入数据
        decimals: 保留小数位数

    Example:
        >>> rd(1.23456, 2)  # 返回 1.23
    """
    return np.round(x, decimals)


def ref(x: SeriesOrFrame, n: int = 1) -> SeriesOrFrame:
    """
    REF: 引用 n 期前的值

    Args:
        x: 输入数据
        n: 回望期数 (正数表示过去)

    Example:
        >>> ref(close, 1)  # 昨日收盘价
    """
    return x.shift(n)


def diff(x: SeriesOrFrame, n: int = 1) -> SeriesOrFrame:
    """
    DIFF: n 期差分

    Args:
        x: 输入数据
        n: 差分期数

    Example:
        >>> diff(close, 1)  # 收盘价日变化量
    """
    return x.diff(n)


def std(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    STD: n 期标准差

    Args:
        x: 输入数据
        n: 计算窗口

    Example:
        >>> std(returns, 20)  # 20日波动率
    """
    return x.rolling(window=n, min_periods=1).std()


def sum_(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    SUM: n 期求和

    Args:
        x: 输入数据
        n: 求和窗口

    Example:
        >>> sum_(volume, 5)  # 5日成交量总和
    """
    return x.rolling(window=n, min_periods=1).sum()


def hhv(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    HHV: n 期最高值

    Args:
        x: 输入数据
        n: 计算窗口

    Example:
        >>> hhv(high, 20)  # 20日最高价
    """
    return x.rolling(window=n, min_periods=1).max()


def llv(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    LLV: n 期最低值

    Args:
        x: 输入数据
        n: 计算窗口

    Example:
        >>> llv(low, 20)  # 20日最低价
    """
    return x.rolling(window=n, min_periods=1).min()


def ma(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    MA: 简单移动平均

    Args:
        x: 输入数据
        n: 平均窗口

    Example:
        >>> ma(close, 20)  # 20日均线
    """
    return x.rolling(window=n, min_periods=1).mean()


def ema(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    EMA: 指数移动平均

    使用 span 参数，衰减因子 = 2/(span+1)

    Args:
        x: 输入数据
        n: 平均窗口 (span)

    Example:
        >>> ema(close, 12)  # 12日 EMA
    """
    return x.ewm(span=n, adjust=False, min_periods=1).mean()


def sma(x: SeriesOrFrame, n: int, m: int = 1) -> SeriesOrFrame:
    """
    SMA: 加权移动平均 (通达信风格)

    公式: SMA(X,N,M) = (M*X + (N-M)*Y') / N
    其中 Y' 是上一期的 SMA 值

    Args:
        x: 输入数据
        n: 周期
        m: 权重

    Example:
        >>> sma(close, 5, 1)
    """
    alpha = m / n
    return x.ewm(alpha=alpha, adjust=False, min_periods=1).mean()


def wma(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    WMA: 加权移动平均 (线性权重)

    权重: [1, 2, 3, ..., n]，近期数据权重更高

    Args:
        x: 输入数据
        n: 平均窗口

    Example:
        >>> wma(close, 10)
    """
    weights = np.arange(1, n + 1)

    def weighted_mean(arr):
        if len(arr) < n:
            return np.nan
        return np.average(arr, weights=weights[-len(arr):])

    if isinstance(x, pd.DataFrame):
        return x.apply(lambda col: col.rolling(n).apply(weighted_mean, raw=True))
    return x.rolling(n).apply(weighted_mean, raw=True)


def slope(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    SLOPE: n 期线性回归斜率

    Args:
        x: 输入数据
        n: 回归窗口

    Example:
        >>> slope(close, 20)  # 价格趋势强度
    """
    def calc_slope(arr):
        if len(arr) < n or np.isnan(arr).any():
            return np.nan
        x_vals = np.arange(len(arr))
        return np.polyfit(x_vals, arr, 1)[0]

    if isinstance(x, pd.DataFrame):
        return x.apply(lambda col: col.rolling(n).apply(calc_slope, raw=True))
    return x.rolling(n).apply(calc_slope, raw=True)


def forcast(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    FORCAST: n 期线性回归预测值

    Args:
        x: 输入数据
        n: 回归窗口

    Example:
        >>> forcast(close, 20)  # 预测价格
    """
    def calc_forcast(arr):
        if len(arr) < n or np.isnan(arr).any():
            return np.nan
        x_vals = np.arange(len(arr))
        coeffs = np.polyfit(x_vals, arr, 1)
        return coeffs[0] * (len(arr) - 1) + coeffs[1]

    if isinstance(x, pd.DataFrame):
        return x.apply(lambda col: col.rolling(n).apply(calc_forcast, raw=True))
    return x.rolling(n).apply(calc_forcast, raw=True)


def sign(x: SeriesOrFrame) -> SeriesOrFrame:
    """
    SIGN: 取符号

    Returns:
        1 (正), -1 (负), 0 (零)

    Example:
        >>> sign(returns)  # 收益方向
    """
    return np.sign(x)


def abs_(x: SeriesOrFrame) -> SeriesOrFrame:
    """
    ABS: 取绝对值

    Example:
        >>> abs_(returns)  # 收益绝对值
    """
    return np.abs(x)


# ============================================================================
# Level 1: 时间序列算子 (20个)
# ============================================================================

def delay(x: SeriesOrFrame, n: int = 1) -> SeriesOrFrame:
    """
    DELAY: 延迟 n 期 (同 REF)

    Args:
        x: 输入数据
        n: 延迟期数

    Example:
        >>> delay(close, 5)  # 5天前的收盘价
    """
    return x.shift(n)


def delta(x: SeriesOrFrame, n: int = 1) -> SeriesOrFrame:
    """
    DELTA: n 期变化量 (同 DIFF)

    Args:
        x: 输入数据
        n: 计算周期

    Example:
        >>> delta(close, 5)  # 5日价格变化
    """
    return x - x.shift(n)


def ts_rank(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    TS_RANK: 时间序列排名百分位

    当前值在过去 n 期中的排名百分位 (0-1)

    Args:
        x: 输入数据
        n: 回望窗口

    Example:
        >>> ts_rank(close, 20)  # 价格在20日内的相对位置
    """
    def rank_pct(arr):
        if len(arr) < 2 or np.isnan(arr).any():
            return np.nan
        return (arr[-1] > arr[:-1]).sum() / (len(arr) - 1)

    if isinstance(x, pd.DataFrame):
        return x.apply(lambda col: col.rolling(n).apply(rank_pct, raw=True))
    return x.rolling(n).apply(rank_pct, raw=True)


def ts_min(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    TS_MIN: n 期最小值

    Args:
        x: 输入数据
        n: 回望窗口

    Example:
        >>> ts_min(low, 20)
    """
    return x.rolling(window=n, min_periods=1).min()


def ts_max(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    TS_MAX: n 期最大值

    Args:
        x: 输入数据
        n: 回望窗口

    Example:
        >>> ts_max(high, 20)
    """
    return x.rolling(window=n, min_periods=1).max()


def ts_argmax(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    TS_ARGMAX: n 期内最大值位置

    返回最大值距今天数 (0 = 今天是最大值)

    Args:
        x: 输入数据
        n: 回望窗口

    Example:
        >>> ts_argmax(high, 20)  # 最高点距今天数
    """
    def argmax_dist(arr):
        if len(arr) < 1 or np.isnan(arr).any():
            return np.nan
        return len(arr) - 1 - np.argmax(arr)

    if isinstance(x, pd.DataFrame):
        return x.apply(lambda col: col.rolling(n).apply(argmax_dist, raw=True))
    return x.rolling(n).apply(argmax_dist, raw=True)


def ts_argmin(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    TS_ARGMIN: n 期内最小值位置

    返回最小值距今天数 (0 = 今天是最小值)

    Args:
        x: 输入数据
        n: 回望窗口

    Example:
        >>> ts_argmin(low, 20)  # 最低点距今天数
    """
    def argmin_dist(arr):
        if len(arr) < 1 or np.isnan(arr).any():
            return np.nan
        return len(arr) - 1 - np.argmin(arr)

    if isinstance(x, pd.DataFrame):
        return x.apply(lambda col: col.rolling(n).apply(argmin_dist, raw=True))
    return x.rolling(n).apply(argmin_dist, raw=True)


def ts_mean(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    TS_MEAN: n 期均值 (同 MA)

    Args:
        x: 输入数据
        n: 计算窗口

    Example:
        >>> ts_mean(volume, 20)
    """
    return x.rolling(window=n, min_periods=1).mean()


def decay_linear(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    DECAY_LINEAR: 线性衰减加权平均

    权重: [n, n-1, ..., 2, 1]，远期数据权重更高

    Args:
        x: 输入数据
        n: 衰减窗口

    Example:
        >>> decay_linear(returns, 10)
    """
    weights = np.arange(n, 0, -1)
    weights = weights / weights.sum()

    def weighted_sum(arr):
        if len(arr) < n:
            return np.nan
        return np.dot(arr, weights[-len(arr):])

    if isinstance(x, pd.DataFrame):
        return x.apply(lambda col: col.rolling(n).apply(weighted_sum, raw=True))
    return x.rolling(n).apply(weighted_sum, raw=True)


def decay_exp(x: SeriesOrFrame, n: int, factor: float = 0.9) -> SeriesOrFrame:
    """
    DECAY_EXP: 指数衰减加权平均

    权重: [factor^(n-1), factor^(n-2), ..., factor, 1]
    近期数据权重更高

    Args:
        x: 输入数据
        n: 衰减窗口
        factor: 衰减因子 (0-1)

    Example:
        >>> decay_exp(returns, 10, 0.9)
    """
    weights = np.array([factor ** i for i in range(n - 1, -1, -1)])
    weights = weights / weights.sum()

    def weighted_sum(arr):
        if len(arr) < n:
            return np.nan
        return np.dot(arr, weights[-len(arr):])

    if isinstance(x, pd.DataFrame):
        return x.apply(lambda col: col.rolling(n).apply(weighted_sum, raw=True))
    return x.rolling(n).apply(weighted_sum, raw=True)


def product(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    PRODUCT: n 期连乘

    Args:
        x: 输入数据
        n: 计算窗口

    Example:
        >>> product(1 + returns, 20)  # 20日累计收益
    """
    return x.rolling(window=n, min_periods=1).apply(np.prod, raw=True)


def correlation(x: SeriesOrFrame, y: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    CORRELATION: n 期相关系数

    Args:
        x: 第一个序列
        y: 第二个序列
        n: 计算窗口

    Example:
        >>> correlation(returns_a, returns_b, 60)
    """
    return x.rolling(window=n, min_periods=1).corr(y)


def covariance(x: SeriesOrFrame, y: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    COVARIANCE: n 期协方差

    Args:
        x: 第一个序列
        y: 第二个序列
        n: 计算窗口

    Example:
        >>> covariance(returns_a, returns_b, 60)
    """
    return x.rolling(window=n, min_periods=1).cov(y)


def stddev(x: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    STDDEV: n 期标准差 (同 STD)

    Args:
        x: 输入数据
        n: 计算窗口

    Example:
        >>> stddev(returns, 20)
    """
    return x.rolling(window=n, min_periods=1).std()


def adv(volume: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    ADV: 平均日成交量

    Args:
        volume: 成交量序列
        n: 平均窗口

    Example:
        >>> adv(volume, 20)  # 20日平均成交量
    """
    return volume.rolling(window=n, min_periods=1).mean()


def returns(x: SeriesOrFrame, n: int = 1) -> SeriesOrFrame:
    """
    RETURNS: n 期收益率

    Args:
        x: 价格序列
        n: 计算周期

    Example:
        >>> returns(close, 1)  # 日收益率
        >>> returns(close, 20)  # 月收益率
    """
    return x.pct_change(n)


def future_returns(x: SeriesOrFrame, n: int = 1) -> SeriesOrFrame:
    """
    FUTURE_RETURNS: 未来 n 期收益率

    注意: 仅用于因子检验，回测中禁止使用

    Args:
        x: 价格序列
        n: 未来周期

    Example:
        >>> future_returns(close, 5)  # 未来5日收益
    """
    return x.pct_change(n).shift(-n)


def count(condition: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    COUNT: n 期内满足条件的次数

    Args:
        condition: 布尔条件序列
        n: 计算窗口

    Example:
        >>> count(close > ref(close, 1), 20)  # 20日内上涨天数
    """
    return condition.astype(int).rolling(window=n, min_periods=1).sum()


def sumif(x: SeriesOrFrame, condition: SeriesOrFrame, n: int) -> SeriesOrFrame:
    """
    SUMIF: n 期内满足条件的值求和

    Args:
        x: 输入数据
        condition: 布尔条件
        n: 计算窗口

    Example:
        >>> sumif(volume, close > ref(close, 1), 20)  # 20日上涨日成交量
    """
    masked = x.where(condition, 0)
    return masked.rolling(window=n, min_periods=1).sum()


def barslast(condition: SeriesOrFrame) -> SeriesOrFrame:
    """
    BARSLAST: 距离上次满足条件的周期数

    Args:
        condition: 布尔条件序列

    Example:
        >>> barslast(cross(ma5, ma20))  # 距上次金叉天数
    """
    def calc_barslast(arr):
        result = np.full_like(arr, np.nan, dtype=float)
        last_true = -1
        for i in range(len(arr)):
            if arr[i]:
                last_true = i
            if last_true >= 0:
                result[i] = i - last_true
        return result

    if isinstance(condition, pd.DataFrame):
        return condition.apply(lambda col: pd.Series(calc_barslast(col.values), index=col.index))
    return pd.Series(calc_barslast(condition.values), index=condition.index)


def cross(x: SeriesOrFrame, y: SeriesOrFrame) -> SeriesOrFrame:
    """
    CROSS: 上穿判断

    X 从下向上穿过 Y 时返回 True

    Args:
        x: 第一个序列
        y: 第二个序列

    Example:
        >>> cross(ma5, ma20)  # 5日线上穿20日线
    """
    return (x > y) & (x.shift(1) <= y.shift(1))


# ============================================================================
# Level 2: 横截面算子 (10个)
# ============================================================================

def rank(x: pd.DataFrame) -> pd.DataFrame:
    """
    RANK: 横截面排名百分位

    同一时间点，股票在所有股票中的排名百分位 (0-1)

    Args:
        x: 多股票 DataFrame (columns=symbols)

    Example:
        >>> rank(returns)  # 当日收益排名
    """
    return x.rank(axis=1, pct=True)


def scale(x: pd.DataFrame, target: float = 1.0) -> pd.DataFrame:
    """
    SCALE: 横截面缩放

    使横截面绝对值之和等于 target

    Args:
        x: 多股票 DataFrame
        target: 目标总和

    Example:
        >>> scale(factor, 1)  # 权重归一化
    """
    abs_sum = x.abs().sum(axis=1)
    return x.div(abs_sum, axis=0) * target


def industry_neutralize(
    x: pd.DataFrame,
    industry: pd.DataFrame,
) -> pd.DataFrame:
    """
    INDUSTRY_NEUTRALIZE: 行业中性化

    减去行业均值，消除行业因素影响

    Args:
        x: 因子值 DataFrame
        industry: 行业分类 DataFrame (one-hot 编码)

    Example:
        >>> industry_neutralize(pe_ratio, industry_dummies)
    """
    # 计算每个行业的均值
    industry_means = x.mul(industry).sum(axis=1) / industry.sum(axis=1)
    # 扩展回原始形状
    industry_effect = industry.mul(industry_means, axis=0).sum(axis=1)
    return x.sub(industry_effect, axis=0)


def zscore(x: pd.DataFrame) -> pd.DataFrame:
    """
    ZSCORE: 横截面标准化

    (x - mean) / std

    Args:
        x: 多股票 DataFrame

    Example:
        >>> zscore(pe_ratio)
    """
    mean = x.mean(axis=1)
    std = x.std(axis=1)
    return x.sub(mean, axis=0).div(std, axis=0)


def percentile(x: pd.DataFrame, pct: float) -> pd.Series:
    """
    PERCENTILE: 横截面百分位值

    Args:
        x: 多股票 DataFrame
        pct: 百分位 (0-100)

    Example:
        >>> percentile(returns, 90)  # 收益第90百分位
    """
    return x.quantile(pct / 100, axis=1)


def winsorize(
    x: pd.DataFrame,
    lower: float = 0.01,
    upper: float = 0.99,
) -> pd.DataFrame:
    """
    WINSORIZE: 横截面缩尾处理

    将极端值限制在指定百分位范围内

    Args:
        x: 多股票 DataFrame
        lower: 下限百分位 (0-1)
        upper: 上限百分位 (0-1)

    Example:
        >>> winsorize(pe_ratio, 0.01, 0.99)
    """
    lower_bound = x.quantile(lower, axis=1)
    upper_bound = x.quantile(upper, axis=1)

    result = x.copy()
    for col in result.columns:
        result[col] = result[col].clip(lower_bound, upper_bound)

    return result


def min_(x: SeriesOrFrame, y: SeriesOrFrame) -> SeriesOrFrame:
    """
    MIN: 逐元素取最小值

    Args:
        x: 第一个序列
        y: 第二个序列

    Example:
        >>> min_(close, open)
    """
    return np.minimum(x, y)


def max_(x: SeriesOrFrame, y: SeriesOrFrame) -> SeriesOrFrame:
    """
    MAX: 逐元素取最大值

    Args:
        x: 第一个序列
        y: 第二个序列

    Example:
        >>> max_(close, open)
    """
    return np.maximum(x, y)


def if_(
    condition: SeriesOrFrame,
    true_value: SeriesOrFrame,
    false_value: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    IF: 条件选择

    Args:
        condition: 布尔条件
        true_value: 条件为真时的值
        false_value: 条件为假时的值

    Example:
        >>> if_(close > open, 1, -1)
    """
    return np.where(condition, true_value, false_value)


def signedpower(x: SeriesOrFrame, exp: float) -> SeriesOrFrame:
    """
    SIGNEDPOWER: 带符号的幂运算

    sign(x) * |x|^exp

    Args:
        x: 输入数据
        exp: 指数

    Example:
        >>> signedpower(returns, 0.5)  # 开根号但保留符号
    """
    return np.sign(x) * np.power(np.abs(x), exp)


# ============================================================================
# Level 3: 技术指标算子 (5个)
# ============================================================================

def rsi(close: SeriesOrFrame, period: int = 14) -> SeriesOrFrame:
    """
    RSI: 相对强弱指标

    RSI = 100 - 100 / (1 + RS)
    RS = 平均上涨幅度 / 平均下跌幅度

    Args:
        close: 收盘价序列
        period: 计算周期 (默认14)

    Returns:
        RSI 值 (0-100)

    Example:
        >>> rsi(close, 14)  # 14日RSI
    """
    delta = close.diff()

    # 分离上涨和下跌
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)

    # 计算平均值 (使用 EMA)
    avg_gain = gain.ewm(span=period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(span=period, adjust=False, min_periods=period).mean()

    # 计算 RS 和 RSI
    rs = avg_gain / avg_loss
    rsi_value = 100 - (100 / (1 + rs))

    return rsi_value


def macd(
    close: SeriesOrFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[SeriesOrFrame, SeriesOrFrame, SeriesOrFrame]:
    """
    MACD: 移动平均收敛发散指标

    DIF = EMA(fast) - EMA(slow)
    DEA = EMA(DIF, signal)
    MACD柱 = (DIF - DEA) * 2

    Args:
        close: 收盘价序列
        fast: 快线周期 (默认12)
        slow: 慢线周期 (默认26)
        signal: 信号线周期 (默认9)

    Returns:
        (DIF, DEA, MACD柱) 三元组

    Example:
        >>> dif, dea, macd_bar = macd(close, 12, 26, 9)
    """
    ema_fast = close.ewm(span=fast, adjust=False, min_periods=fast).mean()
    ema_slow = close.ewm(span=slow, adjust=False, min_periods=slow).mean()

    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False, min_periods=signal).mean()
    macd_bar = (dif - dea) * 2

    return dif, dea, macd_bar


def boll(
    close: SeriesOrFrame,
    period: int = 20,
    std_dev: float = 2.0,
) -> tuple[SeriesOrFrame, SeriesOrFrame, SeriesOrFrame]:
    """
    BOLL: 布林带

    中轨 = MA(period)
    上轨 = 中轨 + std_dev * STD(period)
    下轨 = 中轨 - std_dev * STD(period)

    Args:
        close: 收盘价序列
        period: 计算周期 (默认20)
        std_dev: 标准差倍数 (默认2)

    Returns:
        (上轨, 中轨, 下轨) 三元组

    Example:
        >>> upper, mid, lower = boll(close, 20, 2)
    """
    mid = close.rolling(window=period, min_periods=period).mean()
    std = close.rolling(window=period, min_periods=period).std()

    upper = mid + std_dev * std
    lower = mid - std_dev * std

    return upper, mid, lower


def atr(
    close: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    period: int = 14,
) -> SeriesOrFrame:
    """
    ATR: 平均真实波幅

    TR = max(high-low, |high-prev_close|, |low-prev_close|)
    ATR = EMA(TR, period)

    Args:
        close: 收盘价序列
        high: 最高价序列
        low: 最低价序列
        period: 计算周期 (默认14)

    Returns:
        ATR 值

    Example:
        >>> atr(close, high, low, 14)
    """
    prev_close = close.shift(1)

    # 计算真实波幅的三个分量
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    # 真实波幅取最大值
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    if isinstance(close, pd.DataFrame):
        tr = tr.unstack()

    # ATR 是 TR 的 EMA
    atr_value = tr.ewm(span=period, adjust=False, min_periods=period).mean()

    return atr_value


def kdj(
    close: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    n: int = 9,
    m1: int = 3,
    m2: int = 3,
) -> tuple[SeriesOrFrame, SeriesOrFrame, SeriesOrFrame]:
    """
    KDJ: 随机指标

    RSV = (close - LLV(low, n)) / (HHV(high, n) - LLV(low, n)) * 100
    K = SMA(RSV, m1, 1)
    D = SMA(K, m2, 1)
    J = 3 * K - 2 * D

    Args:
        close: 收盘价序列
        high: 最高价序列
        low: 最低价序列
        n: RSV 周期 (默认9)
        m1: K 平滑周期 (默认3)
        m2: D 平滑周期 (默认3)

    Returns:
        (K, D, J) 三元组

    Example:
        >>> k, d, j = kdj(close, high, low, 9, 3, 3)
    """
    # 计算 n 日内最高价和最低价
    lowest_low = low.rolling(window=n, min_periods=1).min()
    highest_high = high.rolling(window=n, min_periods=1).max()

    # 计算 RSV
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100

    # 处理除零情况
    rsv = rsv.fillna(50)

    # 计算 K (SMA 平滑)
    alpha_k = 1 / m1
    k = rsv.ewm(alpha=alpha_k, adjust=False, min_periods=1).mean()

    # 计算 D (SMA 平滑)
    alpha_d = 1 / m2
    d = k.ewm(alpha=alpha_d, adjust=False, min_periods=1).mean()

    # 计算 J
    j = 3 * k - 2 * d

    return k, d, j


def emv(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    volume: SeriesOrFrame,
    period: int = 14,
) -> SeriesOrFrame:
    """
    EMV: 简易波动指标 (Ease of Movement)

    衡量价格与成交量之间的关系

    Args:
        high: 最高价序列
        low: 最低价序列
        volume: 成交量序列
        period: 平滑周期 (默认14)

    Returns:
        EMV 值

    Example:
        >>> emv(high, low, volume, 14)
    """
    # 中点移动
    midpoint_move = (high + low) / 2 - (high.shift(1) + low.shift(1)) / 2

    # 箱体比率
    box_ratio = (volume / 1e6) / (high - low)

    # 原始 EMV
    emv_raw = midpoint_move / box_ratio

    # 平滑
    return emv_raw.rolling(window=period, min_periods=1).mean()


def mass(
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    ema_period: int = 9,
    sum_period: int = 25,
) -> SeriesOrFrame:
    """
    MASS: 梅斯线 (Mass Index)

    用于识别趋势反转

    Args:
        high: 最高价序列
        low: 最低价序列
        ema_period: EMA 周期 (默认9)
        sum_period: 求和周期 (默认25)

    Returns:
        Mass Index 值

    Example:
        >>> mass(high, low, 9, 25)
    """
    hl_range = high - low

    # 单重 EMA
    ema1 = hl_range.ewm(span=ema_period, adjust=False, min_periods=ema_period).mean()

    # 双重 EMA
    ema2 = ema1.ewm(span=ema_period, adjust=False, min_periods=ema_period).mean()

    # EMA 比率
    ratio = ema1 / ema2

    # Mass Index 为比率之和
    return ratio.rolling(window=sum_period, min_periods=1).sum()


def dpo(
    close: SeriesOrFrame,
    period: int = 20,
) -> SeriesOrFrame:
    """
    DPO: 区间震荡线 (Detrended Price Oscillator)

    消除长期趋势，识别周期

    Args:
        close: 收盘价序列
        period: 计算周期 (默认20)

    Returns:
        DPO 值

    Example:
        >>> dpo(close, 20)
    """
    shift_period = period // 2 + 1
    ma_val = close.rolling(window=period, min_periods=period).mean()
    return close.shift(shift_period) - ma_val


def ktn(
    close: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    ema_period: int = 20,
    atr_period: int = 10,
    multiplier: float = 2.0,
) -> tuple[SeriesOrFrame, SeriesOrFrame, SeriesOrFrame]:
    """
    KTN: 肯特纳通道 (Keltner Channel)

    基于 ATR 的趋势通道

    Args:
        close: 收盘价序列
        high: 最高价序列
        low: 最低价序列
        ema_period: EMA 周期 (默认20)
        atr_period: ATR 周期 (默认10)
        multiplier: ATR 倍数 (默认2.0)

    Returns:
        (上轨, 中轨, 下轨) 三元组

    Example:
        >>> upper, mid, lower = ktn(close, high, low, 20, 10, 2)
    """
    # 中轨 = EMA
    mid = close.ewm(span=ema_period, adjust=False, min_periods=ema_period).mean()

    # 计算 ATR
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()

    if isinstance(close, pd.DataFrame):
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).unstack()
    else:
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr_val = tr.ewm(span=atr_period, adjust=False, min_periods=atr_period).mean()

    # 上下轨
    upper = mid + multiplier * atr_val
    lower = mid - multiplier * atr_val

    return upper, mid, lower


def brar(
    open_: SeriesOrFrame,
    close: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    period: int = 26,
) -> tuple[SeriesOrFrame, SeriesOrFrame]:
    """
    BRAR: 情绪指标 (买卖意愿指标)

    BR: 基于昨收的买卖强度
    AR: 基于今开的买卖强度

    Args:
        open_: 开盘价序列
        close: 收盘价序列
        high: 最高价序列
        low: 最低价序列
        period: 计算周期 (默认26)

    Returns:
        (BR, AR) 二元组

    Example:
        >>> br, ar = brar(open_, close, high, low, 26)
    """
    prev_close = close.shift(1)

    # BR = sum(max(0, high - prev_close)) / sum(max(0, prev_close - low)) * 100
    br_up = (high - prev_close).clip(lower=0).rolling(window=period, min_periods=1).sum()
    br_down = (prev_close - low).clip(lower=0).rolling(window=period, min_periods=1).sum()
    br = br_up / br_down.replace(0, np.nan) * 100

    # AR = sum(high - open) / sum(open - low) * 100
    ar_up = (high - open_).rolling(window=period, min_periods=1).sum()
    ar_down = (open_ - low).rolling(window=period, min_periods=1).sum()
    ar = ar_up / ar_down.replace(0, np.nan) * 100

    return br, ar


def dfma(
    close: SeriesOrFrame,
    short_period: int = 10,
    long_period: int = 50,
    signal_period: int = 10,
) -> tuple[SeriesOrFrame, SeriesOrFrame]:
    """
    DFMA: 平行线差 (DMA 指标)

    DMA = MA(short) - MA(long)
    AMA = MA(DMA, signal)

    Args:
        close: 收盘价序列
        short_period: 短期均线周期 (默认10)
        long_period: 长期均线周期 (默认50)
        signal_period: 信号线周期 (默认10)

    Returns:
        (DMA, AMA) 二元组

    Example:
        >>> dma, ama = dfma(close, 10, 50, 10)
    """
    ma_short = close.rolling(window=short_period, min_periods=1).mean()
    ma_long = close.rolling(window=long_period, min_periods=1).mean()

    dma = ma_short - ma_long
    ama = dma.rolling(window=signal_period, min_periods=1).mean()

    return dma, ama


# ============================================================================
# Level 4: 高阶复合算子 (WorldQuant Alpha + 自定义)
# ============================================================================

def alpha001(
    close: SeriesOrFrame,
    returns_: SeriesOrFrame,
    volume: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA001: WorldQuant Alpha #001

    (-1 * correlation(rank(delta(log(volume), 1)), rank(((close - open) / open)), 6))

    Args:
        close: 收盘价
        returns_: 收益率
        volume: 成交量

    Returns:
        Alpha 因子值

    Example:
        >>> alpha001(close, returns_, volume)
    """
    # 简化实现
    vol_delta = np.log(volume).diff(1)
    vol_rank = vol_delta.rank(axis=1, pct=True) if isinstance(vol_delta, pd.DataFrame) else vol_delta.rank(pct=True)

    ret_rank = returns_.rank(axis=1, pct=True) if isinstance(returns_, pd.DataFrame) else returns_.rank(pct=True)

    return -correlation(vol_rank, ret_rank, 6)


def alpha002(
    open_: SeriesOrFrame,
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA002: WorldQuant Alpha #002

    (-1 * correlation(rank(delta(log(volume), 2)), rank(((close - open) / open)), 6))

    Args:
        open_: 开盘价
        close: 收盘价
        volume: 成交量

    Returns:
        Alpha 因子值

    Example:
        >>> alpha002(open_, close, volume)
    """
    vol_delta = np.log(volume).diff(2)
    vol_rank = vol_delta.rank(axis=1, pct=True) if isinstance(vol_delta, pd.DataFrame) else vol_delta.rank(pct=True)

    ret = (close - open_) / open_
    ret_rank = ret.rank(axis=1, pct=True) if isinstance(ret, pd.DataFrame) else ret.rank(pct=True)

    return -correlation(vol_rank, ret_rank, 6)


def alpha003(
    open_: SeriesOrFrame,
    volume: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA003: WorldQuant Alpha #003

    (-1 * correlation(rank(open), rank(volume), 10))

    Args:
        open_: 开盘价
        volume: 成交量

    Returns:
        Alpha 因子值

    Example:
        >>> alpha003(open_, volume)
    """
    open_rank = open_.rank(axis=1, pct=True) if isinstance(open_, pd.DataFrame) else open_.rank(pct=True)
    vol_rank = volume.rank(axis=1, pct=True) if isinstance(volume, pd.DataFrame) else volume.rank(pct=True)

    return -correlation(open_rank, vol_rank, 10)


def alpha004(
    low: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA004: WorldQuant Alpha #004

    (-1 * ts_rank(rank(low), 9))

    Args:
        low: 最低价

    Returns:
        Alpha 因子值

    Example:
        >>> alpha004(low)
    """
    low_rank = low.rank(axis=1, pct=True) if isinstance(low, pd.DataFrame) else low.rank(pct=True)
    return -ts_rank(low_rank, 9)


def alpha005(
    open_: SeriesOrFrame,
    close: SeriesOrFrame,
    vwap: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA005: WorldQuant Alpha #005

    (rank(open - (sum(vwap, 10) / 10)) * (-1 * abs(rank(close - vwap))))

    Args:
        open_: 开盘价
        close: 收盘价
        vwap: 成交量加权平均价

    Returns:
        Alpha 因子值

    Example:
        >>> alpha005(open_, close, vwap)
    """
    vwap_ma = vwap.rolling(window=10, min_periods=1).mean()
    part1 = open_ - vwap_ma

    if isinstance(part1, pd.DataFrame):
        rank1 = part1.rank(axis=1, pct=True)
    else:
        rank1 = part1.rank(pct=True)

    diff = close - vwap
    if isinstance(diff, pd.DataFrame):
        rank2 = diff.rank(axis=1, pct=True)
    else:
        rank2 = diff.rank(pct=True)

    return rank1 * (-1 * np.abs(rank2))


def momentum_quality(
    close: SeriesOrFrame,
    high: SeriesOrFrame,
    low: SeriesOrFrame,
    volume: SeriesOrFrame,
    short_period: int = 20,
    long_period: int = 60,
) -> SeriesOrFrame:
    """
    MOMENTUM_QUALITY: 动量质量因子

    结合动量强度和动量质量 (稳定性)

    Args:
        close: 收盘价
        high: 最高价
        low: 最低价
        volume: 成交量
        short_period: 短期动量周期
        long_period: 长期动量周期

    Returns:
        动量质量因子值

    Example:
        >>> momentum_quality(close, high, low, volume, 20, 60)
    """
    # 动量强度
    mom_short = close.pct_change(short_period)
    mom_long = close.pct_change(long_period)

    # 动量稳定性 (日收益的波动率)
    daily_ret = close.pct_change(1)
    volatility = daily_ret.rolling(window=short_period).std()

    # 成交量确认
    vol_ma = volume.rolling(window=short_period).mean()
    vol_ratio = volume / vol_ma

    # 综合因子: 动量 / 波动率 * 成交量确认
    quality = (mom_short + mom_long) / (volatility + 1e-8) * vol_ratio.clip(0.5, 2)

    return quality


def value_composite(
    close: SeriesOrFrame,
    book_value: SeriesOrFrame,
    earnings: SeriesOrFrame,
    sales: SeriesOrFrame,
    cash_flow: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    VALUE_COMPOSITE: 复合价值因子

    结合多种估值指标

    Args:
        close: 收盘价 (市值)
        book_value: 账面价值
        earnings: 盈利
        sales: 销售收入
        cash_flow: 现金流

    Returns:
        复合价值因子值

    Example:
        >>> value_composite(close, book_value, earnings, sales, cash_flow)
    """
    # 各种价值指标
    bp = book_value / close  # 市净率倒数
    ep = earnings / close    # 市盈率倒数
    sp = sales / close       # 市销率倒数
    cfp = cash_flow / close  # 市现率倒数

    # 横截面标准化
    def cs_zscore(x):
        if isinstance(x, pd.DataFrame):
            return (x.sub(x.mean(axis=1), axis=0)).div(x.std(axis=1), axis=0)
        return (x - x.mean()) / x.std()

    # 等权综合
    composite = (cs_zscore(bp) + cs_zscore(ep) + cs_zscore(sp) + cs_zscore(cfp)) / 4

    return composite


def liquidity_risk(
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    period: int = 20,
) -> SeriesOrFrame:
    """
    LIQUIDITY_RISK: 流动性风险因子

    基于 Amihud 非流动性指标

    Args:
        close: 收盘价
        volume: 成交量 (金额)
        period: 计算周期

    Returns:
        流动性风险因子值 (越大流动性越差)

    Example:
        >>> liquidity_risk(close, volume, 20)
    """
    # 收益率绝对值
    abs_ret = close.pct_change(1).abs()

    # Amihud 非流动性: |收益率| / 成交金额
    amihud = abs_ret / (volume + 1e-8)

    # 平均非流动性
    illiq = amihud.rolling(window=period, min_periods=1).mean()

    return illiq


def volatility_regime(
    close: SeriesOrFrame,
    short_period: int = 10,
    long_period: int = 60,
) -> SeriesOrFrame:
    """
    VOLATILITY_REGIME: 波动率区制因子

    识别当前波动率状态 (高/低波动环境)

    Args:
        close: 收盘价
        short_period: 短期波动周期
        long_period: 长期波动周期

    Returns:
        波动率区制因子 (>1 高波动, <1 低波动)

    Example:
        >>> volatility_regime(close, 10, 60)
    """
    daily_ret = close.pct_change(1)

    vol_short = daily_ret.rolling(window=short_period).std()
    vol_long = daily_ret.rolling(window=long_period).std()

    # 短期/长期波动率比值
    regime = vol_short / (vol_long + 1e-8)

    return regime


def trend_strength(
    close: SeriesOrFrame,
    period: int = 20,
) -> SeriesOrFrame:
    """
    TREND_STRENGTH: 趋势强度因子

    基于线性回归 R² 衡量趋势强度

    Args:
        close: 收盘价
        period: 计算周期

    Returns:
        趋势强度因子 (0-1, 越大趋势越明显)

    Example:
        >>> trend_strength(close, 20)
    """
    def calc_r_squared(arr):
        if len(arr) < period or np.isnan(arr).any():
            return np.nan
        x = np.arange(len(arr))
        y = arr

        # 线性回归
        slope_val, intercept = np.polyfit(x, y, 1)
        y_pred = slope_val * x + intercept

        # R²
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)

        if ss_tot == 0:
            return 0

        return 1 - ss_res / ss_tot

    if isinstance(close, pd.DataFrame):
        return close.apply(lambda col: col.rolling(period).apply(calc_r_squared, raw=True))
    return close.rolling(period).apply(calc_r_squared, raw=True)


def alpha006(
    open_: SeriesOrFrame,
    volume: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA006: WorldQuant Alpha #006

    (-1 * correlation(open, volume, 10))

    Args:
        open_: 开盘价
        volume: 成交量

    Returns:
        Alpha 因子值
    """
    return -correlation(open_, volume, 10)


def alpha007(
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA007: WorldQuant Alpha #007

    根据成交量变化调整的动量因子

    Args:
        close: 收盘价
        volume: 成交量

    Returns:
        Alpha 因子值
    """
    adv_20 = volume.rolling(window=20, min_periods=1).mean()
    condition = adv_20 < volume

    delta_close = close.diff(7)
    if isinstance(delta_close, pd.DataFrame):
        ts_rank_val = delta_close.apply(lambda col: ts_rank(col, 60))
    else:
        ts_rank_val = ts_rank(delta_close, 60)

    return np.where(condition, -1 * ts_rank_val * np.sign(delta_close), -1)


def alpha008(
    open_: SeriesOrFrame,
    returns_: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA008: WorldQuant Alpha #008

    (-1 * rank(((sum(open, 5) * sum(returns, 5)) - delay((sum(open, 5) * sum(returns, 5)), 10))))

    Args:
        open_: 开盘价
        returns_: 收益率

    Returns:
        Alpha 因子值
    """
    sum_open = open_.rolling(window=5, min_periods=1).sum()
    sum_ret = returns_.rolling(window=5, min_periods=1).sum()

    prod = sum_open * sum_ret
    delta_prod = prod - prod.shift(10)

    if isinstance(delta_prod, pd.DataFrame):
        return -delta_prod.rank(axis=1, pct=True)
    return -delta_prod.rank(pct=True)


def alpha009(
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA009: WorldQuant Alpha #009

    条件动量因子

    Args:
        close: 收盘价

    Returns:
        Alpha 因子值
    """
    delta_close = close.diff(1)
    ts_min_delta = delta_close.rolling(window=5, min_periods=1).min()
    ts_max_delta = delta_close.rolling(window=5, min_periods=1).max()

    # 条件判断
    condition = ts_min_delta > 0
    result = np.where(condition, delta_close, np.nan)
    result = np.where(ts_max_delta < 0, delta_close, result)
    result = np.where(pd.isna(result), -delta_close, result)

    return result


def alpha010(
    close: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    ALPHA010: WorldQuant Alpha #010

    基于近期动量的因子

    Args:
        close: 收盘价

    Returns:
        Alpha 因子值
    """
    delta_close = close.diff(1)
    ts_min_delta = delta_close.rolling(window=4, min_periods=1).min()
    ts_max_delta = delta_close.rolling(window=4, min_periods=1).max()

    condition = ts_min_delta > 0

    if isinstance(delta_close, pd.DataFrame):
        rank_delta = delta_close.rank(axis=1, pct=True)
    else:
        rank_delta = delta_close.rank(pct=True)

    result = np.where(condition, delta_close, np.nan)
    result = np.where(ts_max_delta < 0, delta_close, result)
    result = np.where(pd.isna(result), -rank_delta, result)

    return result


def reversal_factor(
    close: SeriesOrFrame,
    period: int = 5,
) -> SeriesOrFrame:
    """
    REVERSAL_FACTOR: 短期反转因子

    短期收益的负值作为反转信号

    Args:
        close: 收盘价
        period: 计算周期

    Returns:
        反转因子值
    """
    return -close.pct_change(period)


def size_factor(
    market_cap: SeriesOrFrame,
) -> SeriesOrFrame:
    """
    SIZE_FACTOR: 市值因子

    对数市值的负值 (小市值因子)

    Args:
        market_cap: 市值

    Returns:
        市值因子值
    """
    return -np.log(market_cap)


def beta_factor(
    returns_: SeriesOrFrame,
    market_returns: SeriesOrFrame,
    period: int = 60,
) -> SeriesOrFrame:
    """
    BETA_FACTOR: Beta 因子

    相对于市场的系统性风险

    Args:
        returns_: 股票收益率
        market_returns: 市场收益率
        period: 计算周期

    Returns:
        Beta 因子值
    """
    cov_rm = covariance(returns_, market_returns, period)
    var_m = market_returns.rolling(window=period, min_periods=1).var()

    return cov_rm / (var_m + 1e-8)


def idiosyncratic_volatility(
    returns_: SeriesOrFrame,
    market_returns: SeriesOrFrame,
    period: int = 60,
) -> SeriesOrFrame:
    """
    IDIOSYNCRATIC_VOLATILITY: 特异性波动因子

    剔除市场因素后的残差波动率

    Args:
        returns_: 股票收益率
        market_returns: 市场收益率
        period: 计算周期

    Returns:
        特异性波动因子值
    """
    # 计算 Beta
    beta = beta_factor(returns_, market_returns, period)

    # 残差收益
    if isinstance(returns_, pd.DataFrame):
        residual = returns_.sub(beta.mul(market_returns, axis=0))
    else:
        residual = returns_ - beta * market_returns

    # 残差波动率
    return residual.rolling(window=period, min_periods=1).std()


def turnover_factor(
    volume: SeriesOrFrame,
    shares_outstanding: SeriesOrFrame,
    period: int = 20,
) -> SeriesOrFrame:
    """
    TURNOVER_FACTOR: 换手率因子

    平均换手率

    Args:
        volume: 成交量
        shares_outstanding: 流通股本
        period: 计算周期

    Returns:
        换手率因子值
    """
    daily_turnover = volume / shares_outstanding
    return daily_turnover.rolling(window=period, min_periods=1).mean()


def price_volume_divergence(
    close: SeriesOrFrame,
    volume: SeriesOrFrame,
    period: int = 20,
) -> SeriesOrFrame:
    """
    PRICE_VOLUME_DIVERGENCE: 量价背离因子

    价格和成交量变化的相关性

    Args:
        close: 收盘价
        volume: 成交量
        period: 计算周期

    Returns:
        量价背离因子值 (负值表示背离)
    """
    price_change = close.pct_change(1)
    volume_change = volume.pct_change(1)

    return correlation(price_change, volume_change, period)


def skewness(
    returns_: SeriesOrFrame,
    period: int = 20,
) -> SeriesOrFrame:
    """
    SKEWNESS: 偏度因子

    收益率分布的偏度，衡量收益率分布的不对称性

    Args:
        returns_: 收益率序列
        period: 计算周期

    Returns:
        偏度因子值 (正值右偏，负值左偏)
    """
    return returns_.rolling(window=period, min_periods=period).skew()


def kurtosis(
    returns_: SeriesOrFrame,
    period: int = 20,
) -> SeriesOrFrame:
    """
    KURTOSIS: 峰度因子

    收益率分布的峰度，衡量尾部风险

    Args:
        returns_: 收益率序列
        period: 计算周期

    Returns:
        峰度因子值 (>3 厚尾，<3 薄尾)
    """
    return returns_.rolling(window=period, min_periods=period).kurt()


# ============================================================================
# 算子统计
# ============================================================================

# L0 核心算子 (15个)
L0_OPERATORS = [
    "rd", "ref", "diff", "std", "sum_",
    "hhv", "llv", "ma", "ema", "sma",
    "wma", "slope", "forcast", "sign", "abs_",
]

# L1 时间序列算子 (21个)
L1_OPERATORS = [
    "delay", "delta", "ts_rank", "ts_min", "ts_max",
    "ts_argmax", "ts_argmin", "ts_mean", "decay_linear", "decay_exp",
    "product", "correlation", "covariance", "stddev", "adv",
    "returns", "future_returns", "count", "sumif", "barslast",
    "cross",
]

# L2 横截面算子 (10个)
L2_OPERATORS = [
    "rank", "scale", "industry_neutralize", "zscore", "percentile",
    "winsorize", "min_", "max_", "if_", "signedpower",
]

# L3 技术指标算子 (11个)
L3_OPERATORS = [
    "rsi", "macd", "boll", "atr", "kdj",
    "emv", "mass", "dpo", "ktn", "brar", "dfma",
]

# L4 高阶复合算子 (18个)
L4_OPERATORS = [
    "alpha001", "alpha002", "alpha003", "alpha004", "alpha005",
    "alpha006", "alpha007", "alpha008", "alpha009", "alpha010",
    "momentum_quality", "value_composite", "liquidity_risk",
    "volatility_regime", "trend_strength", "reversal_factor",
    "size_factor", "beta_factor",
]

# L5 风险因子 (5个)
L5_OPERATORS = [
    "idiosyncratic_volatility", "turnover_factor",
    "price_volume_divergence", "skewness", "kurtosis",
]

ALL_OPERATORS = (
    L0_OPERATORS + L1_OPERATORS + L2_OPERATORS +
    L3_OPERATORS + L4_OPERATORS + L5_OPERATORS
)

# 算子总数: 80 个
OPERATOR_COUNT = len(ALL_OPERATORS)
