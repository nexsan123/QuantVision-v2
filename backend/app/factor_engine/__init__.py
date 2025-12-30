"""
因子引擎模块

提供:
- 50 因子算子 (L0-L3)
- 因子检验与 IC 分析
- 因子预处理
"""

from app.factor_engine.factor_tester import FactorTester
from app.factor_engine.operators import (
    ALL_OPERATORS,
    # 算子列表
    L0_OPERATORS,
    L1_OPERATORS,
    L2_OPERATORS,
    L3_OPERATORS,
    OPERATOR_COUNT,
    abs_,
    adv,
    atr,
    barslast,
    boll,
    correlation,
    count,
    covariance,
    cross,
    decay_linear,
    # L1 时间序列算子
    delay,
    delta,
    diff,
    ema,
    forcast,
    future_returns,
    hhv,
    if_,
    industry_neutralize,
    kdj,
    llv,
    ma,
    macd,
    max_,
    min_,
    percentile,
    product,
    # L2 横截面算子
    rank,
    # L0 核心算子
    rd,
    ref,
    returns,
    # L3 技术指标算子
    rsi,
    scale,
    sign,
    signedpower,
    slope,
    sma,
    std,
    stddev,
    sum_,
    sumif,
    ts_argmax,
    ts_argmin,
    ts_max,
    ts_mean,
    ts_min,
    ts_rank,
    winsorize,
    wma,
    zscore,
)
from app.factor_engine.preprocessor import FactorPreprocessor

__all__ = [
    # L0 核心算子
    "rd", "ref", "diff", "std", "sum_",
    "hhv", "llv", "ma", "ema", "sma",
    "wma", "slope", "forcast", "sign", "abs_",
    # L1 时间序列算子
    "delay", "delta", "ts_rank", "ts_min", "ts_max",
    "ts_argmax", "ts_argmin", "ts_mean", "decay_linear", "product",
    "correlation", "covariance", "stddev", "adv", "returns",
    "future_returns", "count", "sumif", "barslast", "cross",
    # L2 横截面算子
    "rank", "scale", "industry_neutralize", "zscore", "percentile",
    "winsorize", "min_", "max_", "if_", "signedpower",
    # L3 技术指标算子
    "rsi", "macd", "boll", "atr", "kdj",
    # 算子列表
    "L0_OPERATORS", "L1_OPERATORS", "L2_OPERATORS", "L3_OPERATORS",
    "ALL_OPERATORS", "OPERATOR_COUNT",
    # 分析工具
    "FactorTester",
    "FactorPreprocessor",
]
