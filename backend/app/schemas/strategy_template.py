"""
策略模板 Schema 定义
PRD 4.13 策略模板库
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TemplateCategory(str, Enum):
    """模板分类"""
    VALUE = "value"  # 价值投资
    MOMENTUM = "momentum"  # 动量趋势
    DIVIDEND = "dividend"  # 红利收益
    MULTI_FACTOR = "multi_factor"  # 多因子
    TIMING = "timing"  # 择时轮动
    INTRADAY = "intraday"  # 日内交易


class DifficultyLevel(str, Enum):
    """难度等级"""
    BEGINNER = "beginner"  # 入门
    INTERMEDIATE = "intermediate"  # 进阶
    ADVANCED = "advanced"  # 专业


class HoldingPeriod(str, Enum):
    """持仓周期"""
    INTRADAY = "intraday"  # 日内
    SHORT_TERM = "short_term"  # 短线 (1-5天)
    MEDIUM_TERM = "medium_term"  # 中线 (5-30天)
    LONG_TERM = "long_term"  # 长线 (>30天)


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"  # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"  # 高风险


class StrategyTemplate(BaseModel):
    """策略模板"""
    template_id: str
    name: str
    description: str
    category: TemplateCategory
    difficulty: DifficultyLevel
    holding_period: HoldingPeriod
    risk_level: RiskLevel

    # 预期表现
    expected_annual_return: str = Field(description="预期年化收益，如'10-15%'")
    max_drawdown: str = Field(description="最大回撤，如'15-20%'")
    sharpe_ratio: str = Field(description="夏普比率，如'1.2-1.5'")

    # 策略配置 (7步配置JSON)
    strategy_config: dict = Field(description="策略配置JSON")

    # 使用信息
    user_count: int = Field(0, description="使用人数")
    rating: float = Field(4.0, ge=0, le=5, description="评分")

    # 标签
    tags: list[str] = Field(default=[], description="标签")

    # 元数据
    icon: str = Field("📊", description="图标")
    created_at: datetime
    updated_at: datetime


class TemplateDeployRequest(BaseModel):
    """模板部署请求"""
    template_id: str
    strategy_name: str = Field(description="策略名称")
    initial_capital: float = Field(100000, gt=0, description="初始资金")


class TemplateDeployResult(BaseModel):
    """模板部署结果"""
    strategy_id: str
    strategy_name: str
    template_id: str
    template_name: str
    created_at: datetime
    message: str


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    total: int
    templates: list[StrategyTemplate]


# 分类配置
CATEGORY_CONFIG = {
    TemplateCategory.VALUE: {
        "label": "价值投资",
        "icon": "💎",
        "color": "#3b82f6",
        "description": "基于基本面分析，寻找被低估的优质股票",
    },
    TemplateCategory.MOMENTUM: {
        "label": "动量趋势",
        "icon": "🚀",
        "color": "#22c55e",
        "description": "追踪价格趋势，顺势而为",
    },
    TemplateCategory.DIVIDEND: {
        "label": "红利收益",
        "icon": "💰",
        "color": "#f59e0b",
        "description": "追求稳定分红收益的防守型策略",
    },
    TemplateCategory.MULTI_FACTOR: {
        "label": "多因子",
        "icon": "🔬",
        "color": "#8b5cf6",
        "description": "综合多个因子进行量化选股",
    },
    TemplateCategory.TIMING: {
        "label": "择时轮动",
        "icon": "🔄",
        "color": "#ec4899",
        "description": "根据市场环境切换行业/风格配置",
    },
    TemplateCategory.INTRADAY: {
        "label": "日内交易",
        "icon": "⚡",
        "color": "#ef4444",
        "description": "日内短线交易，当日完成买卖",
    },
}


# 难度配置
DIFFICULTY_CONFIG = {
    DifficultyLevel.BEGINNER: {
        "label": "入门",
        "stars": 1,
        "color": "#22c55e",
        "description": "适合新手，规则简单易懂",
    },
    DifficultyLevel.INTERMEDIATE: {
        "label": "进阶",
        "stars": 2,
        "color": "#f59e0b",
        "description": "需要一定投资经验",
    },
    DifficultyLevel.ADVANCED: {
        "label": "专业",
        "stars": 3,
        "color": "#ef4444",
        "description": "适合专业投资者",
    },
}


# 持仓周期配置
HOLDING_PERIOD_CONFIG = {
    HoldingPeriod.INTRADAY: {
        "label": "日内",
        "description": "当日买入当日卖出",
    },
    HoldingPeriod.SHORT_TERM: {
        "label": "短线",
        "description": "持仓1-5天",
    },
    HoldingPeriod.MEDIUM_TERM: {
        "label": "中线",
        "description": "持仓5-30天",
    },
    HoldingPeriod.LONG_TERM: {
        "label": "长线",
        "description": "持仓30天以上",
    },
}


# 风险配置
RISK_LEVEL_CONFIG = {
    RiskLevel.LOW: {
        "label": "低",
        "color": "#22c55e",
        "description": "波动较小，回撤可控",
    },
    RiskLevel.MEDIUM: {
        "label": "中",
        "color": "#f59e0b",
        "description": "波动适中，风险可接受",
    },
    RiskLevel.HIGH: {
        "label": "高",
        "color": "#ef4444",
        "description": "波动较大，可能有较大回撤",
    },
}
