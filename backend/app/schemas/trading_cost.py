"""
交易成本配置 Schema 定义
PRD 4.4 交易成本配置
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from decimal import Decimal
from enum import Enum


class CostMode(str, Enum):
    """成本模式"""
    SIMPLE = "simple"  # 简单模式
    PROFESSIONAL = "professional"  # 专业模式


class MarketCap(str, Enum):
    """市值分类"""
    LARGE = "large"  # 大盘股 (>$10B)
    MID = "mid"  # 中盘股 ($2B-$10B)
    SMALL = "small"  # 小盘股 (<$2B)


class SlippageConfig(BaseModel):
    """滑点配置 (专业模式)"""
    large_cap: float = Field(0.0005, ge=0.0002, description="大盘股滑点 (最低0.02%)")
    mid_cap: float = Field(0.0010, ge=0.0005, description="中盘股滑点 (最低0.05%)")
    small_cap: float = Field(0.0025, ge=0.0015, description="小盘股滑点 (最低0.15%)")


class MarketImpactConfig(BaseModel):
    """市场冲击配置 (专业模式)"""
    impact_coefficient: float = Field(
        0.1,
        ge=0.05,
        le=0.5,
        description="冲击系数 η (0.05-0.5)"
    )
    enabled: bool = Field(True, description="是否启用市场冲击计算")


class TradingCostConfig(BaseModel):
    """交易成本配置"""
    config_id: str
    user_id: str

    # 成本模式
    mode: CostMode = CostMode.SIMPLE

    # 佣金 ($/股)
    commission_per_share: Decimal = Field(
        Decimal("0.005"),
        ge=Decimal("0.003"),
        description="佣金 (最低 $0.003/股)"
    )

    # SEC费用 (卖出时按交易额收取)
    sec_fee_rate: Decimal = Field(
        Decimal("0.0000278"),
        description="SEC费用率 ($27.80 per million)"
    )

    # TAF费用 (每笔交易固定)
    taf_fee_per_share: Decimal = Field(
        Decimal("0.000166"),
        description="TAF费用 ($/股)"
    )

    # 简单模式滑点 (固定百分比)
    simple_slippage: float = Field(
        0.001,
        ge=0.0005,
        le=0.005,
        description="简单模式固定滑点 (0.05%-0.50%)"
    )

    # 专业模式滑点配置
    slippage: Optional[SlippageConfig] = None

    # 市场冲击配置
    market_impact: Optional[MarketImpactConfig] = None

    # 成本缓冲
    cost_buffer: float = Field(
        0.2,
        ge=0,
        le=0.5,
        description="成本缓冲 (0%-50%)"
    )

    @field_validator("commission_per_share")
    @classmethod
    def validate_commission(cls, v: Decimal) -> Decimal:
        """验证佣金最低限制"""
        min_commission = Decimal("0.003")
        if v < min_commission:
            return min_commission
        return v


class CostEstimateRequest(BaseModel):
    """成本估算请求"""
    symbol: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
    side: str = Field(description="buy 或 sell")
    market_cap: Optional[MarketCap] = None
    daily_volume: Optional[int] = Field(None, description="日均成交量")
    volatility: Optional[float] = Field(None, ge=0, le=1, description="日波动率")


class CostEstimateResult(BaseModel):
    """成本估算结果"""
    symbol: str
    side: str
    quantity: int
    price: float
    trade_value: float = Field(description="交易金额")

    # 各项成本
    commission: float = Field(description="佣金")
    sec_fee: float = Field(description="SEC费用 (仅卖出)")
    taf_fee: float = Field(description="TAF费用")
    slippage_cost: float = Field(description="滑点成本")
    market_impact_cost: float = Field(description="市场冲击成本")

    # 汇总
    total_cost: float = Field(description="总成本")
    total_cost_pct: float = Field(description="成本占比")
    cost_with_buffer: float = Field(description="含缓冲成本")

    # 成本明细
    breakdown: dict = Field(description="成本明细")


class CostConfigUpdate(BaseModel):
    """成本配置更新请求"""
    mode: Optional[CostMode] = None
    commission_per_share: Optional[Decimal] = None
    simple_slippage: Optional[float] = None
    slippage: Optional[SlippageConfig] = None
    market_impact: Optional[MarketImpactConfig] = None
    cost_buffer: Optional[float] = None


# 默认配置常量
DEFAULT_COST_CONFIG = {
    "simple": {
        "commission_per_share": Decimal("0.005"),
        "simple_slippage": 0.001,  # 0.10%
        "cost_buffer": 0.2,  # 20%
    },
    "professional": {
        "commission_per_share": Decimal("0.005"),
        "slippage": {
            "large_cap": 0.0005,  # 0.05%
            "mid_cap": 0.0010,  # 0.10%
            "small_cap": 0.0025,  # 0.25%
        },
        "market_impact": {
            "impact_coefficient": 0.1,
            "enabled": True,
        },
        "cost_buffer": 0.15,  # 15%
    },
}


# 最低限制常量
COST_MINIMUMS = {
    "commission_per_share": Decimal("0.003"),  # $0.003/股
    "slippage_large_cap": 0.0002,  # 0.02%
    "slippage_mid_cap": 0.0005,  # 0.05%
    "slippage_small_cap": 0.0015,  # 0.15%
}


# 市值分类阈值 (美元)
MARKET_CAP_THRESHOLDS = {
    "large": 10_000_000_000,  # > $10B
    "mid": 2_000_000_000,  # $2B - $10B
    "small": 0,  # < $2B
}
