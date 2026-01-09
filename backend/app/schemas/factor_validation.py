"""
因子有效性验证 Schema 定义
PRD 4.3 因子有效性验证
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from enum import Enum


class EffectivenessLevel(str, Enum):
    """因子有效性等级"""
    STRONG = "strong"           # IC_IR > 0.5, 多空收益差 > 10%
    MEDIUM = "medium"           # IC_IR > 0.3, 多空收益差 > 5%
    WEAK = "weak"               # IC_IR > 0.1, 多空收益差 > 2%
    INEFFECTIVE = "ineffective" # 无效


class ICStatistics(BaseModel):
    """IC/IR 统计"""
    ic_mean: float = Field(description="IC均值")
    ic_std: float = Field(description="IC标准差")
    ic_ir: float = Field(description="IC_IR = IC均值/IC标准差")
    ic_positive_ratio: float = Field(description="IC为正的比例")
    ic_series: list[float] = Field(default=[], description="IC时序数据")
    ic_dates: list[str] = Field(default=[], description="IC日期")


class ReturnStatistics(BaseModel):
    """分组收益统计"""
    group_returns: list[float] = Field(description="各分组年化收益率")
    group_labels: list[str] = Field(default=["第1组", "第2组", "第3组", "第4组", "第5组"])
    long_short_spread: float = Field(description="多空收益差 (第1组-第5组)")
    top_group_sharpe: float = Field(description="头部组夏普比率")
    bottom_group_sharpe: float = Field(description="尾部组夏普比率")


class FactorValidationResult(BaseModel):
    """因子验证结果"""
    factor_id: str
    factor_name: str
    factor_category: str = Field(description="因子类别 (价值/成长/质量/动量/波动)")

    # 大白话描述
    plain_description: str = Field(description="通俗解释")
    investment_logic: str = Field(description="投资逻辑")

    # 统计指标
    ic_stats: ICStatistics
    return_stats: ReturnStatistics

    # 有效性判定
    is_effective: bool
    effectiveness_level: EffectivenessLevel
    effectiveness_score: float = Field(ge=0, le=100, description="有效性评分 0-100")

    # 建议
    suggested_combinations: list[str] = Field(description="建议组合的因子")
    usage_tips: list[str] = Field(description="使用建议")
    risk_warnings: list[str] = Field(description="风险提示")

    # 元数据
    validation_date: date
    data_period: str = Field(description="数据区间")
    sample_size: int = Field(description="样本量")


class FactorValidationRequest(BaseModel):
    """因子验证请求"""
    factor_id: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    universe: str = Field(default="全A", description="股票池")


class FactorCompareRequest(BaseModel):
    """因子对比请求"""
    factor_ids: list[str] = Field(min_length=2, max_length=5)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class FactorCompareResult(BaseModel):
    """因子对比结果"""
    factors: list[FactorValidationResult]
    correlation_matrix: list[list[float]] = Field(description="因子相关性矩阵")
    best_combination: list[str] = Field(description="最佳因子组合")
    combination_score: float = Field(description="组合有效性评分")


class FactorSuggestion(BaseModel):
    """因子组合建议"""
    factor_id: str
    factor_name: str
    suggestion_reason: str
    expected_improvement: float = Field(description="预期收益提升")
    correlation: float = Field(description="与当前因子相关性")


# 有效性阈值配置 (PRD 4.3)
EFFECTIVENESS_THRESHOLDS = {
    "strong": {"ic_ir": 0.5, "spread": 0.10},
    "medium": {"ic_ir": 0.3, "spread": 0.05},
    "weak": {"ic_ir": 0.1, "spread": 0.02},
}

# 因子类别配置
FACTOR_CATEGORY_CONFIG = {
    "value": {
        "label": "价值因子",
        "icon": "💰",
        "examples": ["PE_TTM", "PB", "PS", "DIVIDEND_YIELD"],
    },
    "growth": {
        "label": "成长因子",
        "icon": "📈",
        "examples": ["REVENUE_GROWTH", "EPS_GROWTH", "ROE_GROWTH"],
    },
    "quality": {
        "label": "质量因子",
        "icon": "⭐",
        "examples": ["ROE", "ROA", "GROSS_MARGIN", "DEBT_RATIO"],
    },
    "momentum": {
        "label": "动量因子",
        "icon": "🚀",
        "examples": ["MOMENTUM_1M", "MOMENTUM_3M", "MOMENTUM_6M"],
    },
    "volatility": {
        "label": "波动因子",
        "icon": "📊",
        "examples": ["VOLATILITY_20D", "BETA", "IDIOSYNCRATIC_VOL"],
    },
}

# 有效性等级配置
EFFECTIVENESS_LEVEL_CONFIG = {
    EffectivenessLevel.STRONG: {
        "label": "强",
        "stars": 5,
        "color": "#22c55e",
        "description": "该因子表现优异，可作为主要选股依据",
    },
    EffectivenessLevel.MEDIUM: {
        "label": "中",
        "stars": 3,
        "color": "#3b82f6",
        "description": "该因子表现中等，建议与其他因子组合使用",
    },
    EffectivenessLevel.WEAK: {
        "label": "弱",
        "stars": 1,
        "color": "#eab308",
        "description": "该因子表现较弱，仅作为辅助参考",
    },
    EffectivenessLevel.INEFFECTIVE: {
        "label": "无效",
        "stars": 0,
        "color": "#ef4444",
        "description": "该因子无明显选股能力，不建议使用",
    },
}
