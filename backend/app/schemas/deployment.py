"""
策略部署 Pydantic Schema

包含:
- 部署配置
- 参数范围限制
- 环境类型
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DeploymentEnvironment(str, Enum):
    """部署环境"""
    PAPER = "paper"  # 模拟盘
    LIVE = "live"    # 实盘


class DeploymentStatus(str, Enum):
    """部署状态"""
    DRAFT = "draft"      # 草稿
    RUNNING = "running"  # 运行中
    PAUSED = "paused"    # 已暂停
    STOPPED = "stopped"  # 已停止


class StrategyType(str, Enum):
    """策略类型"""
    INTRADAY = "intraday"       # 日内交易
    SHORT_TERM = "short_term"   # 短线 (1-5天)
    MEDIUM_TERM = "medium_term" # 中线 (1-4周)
    LONG_TERM = "long_term"     # 长线 (>1月)


# ============ 参数范围定义 ============

class ParamRange(BaseModel):
    """参数范围"""
    min_value: float
    max_value: float
    default_value: float
    step: float = 0.01
    unit: str = ""
    description: str = ""


class RiskParams(BaseModel):
    """风控参数"""
    stop_loss: float = Field(-0.05, ge=-0.50, le=-0.01, description="止损比例")
    take_profit: float = Field(0.10, ge=0.02, le=1.0, description="止盈比例")
    max_position_pct: float = Field(0.10, ge=0.01, le=0.50, description="单只最大仓位")
    max_drawdown: float = Field(-0.15, ge=-0.50, le=-0.05, description="最大回撤限制")


class CapitalConfig(BaseModel):
    """资金配置"""
    total_capital: Decimal = Field(..., gt=0, description="总资金")
    initial_position_pct: float = Field(0.80, ge=0.10, le=1.0, description="初始仓位比例")
    reserve_cash_pct: float = Field(0.20, ge=0.0, le=0.50, description="预留现金比例")


# ============ 部署配置 ============

class DeploymentConfig(BaseModel):
    """部署配置"""
    # 基础信息
    strategy_id: str
    deployment_name: str = Field(..., min_length=1, max_length=100)
    environment: DeploymentEnvironment = DeploymentEnvironment.PAPER
    strategy_type: StrategyType = StrategyType.MEDIUM_TERM

    # 股票池配置 (继承自策略，可选择子集)
    universe_subset: Optional[list[str]] = None  # 为空则使用策略默认股票池

    # 风控参数 (继承自策略回测，可在范围内调整)
    risk_params: RiskParams = Field(default_factory=RiskParams)

    # 资金配置
    capital_config: CapitalConfig

    # 调仓设置
    rebalance_frequency: str = Field("daily", pattern="^(daily|weekly|monthly)$")
    rebalance_time: str = Field("09:35", pattern="^[0-2][0-9]:[0-5][0-9]$")


class DeploymentCreate(BaseModel):
    """创建部署请求"""
    config: DeploymentConfig
    auto_start: bool = False


class DeploymentUpdate(BaseModel):
    """更新部署请求"""
    deployment_name: Optional[str] = None
    risk_params: Optional[RiskParams] = None
    capital_config: Optional[CapitalConfig] = None
    rebalance_frequency: Optional[str] = None
    rebalance_time: Optional[str] = None


class Deployment(BaseModel):
    """部署实体"""
    deployment_id: str
    strategy_id: str
    strategy_name: str
    deployment_name: str
    environment: DeploymentEnvironment
    status: DeploymentStatus
    strategy_type: StrategyType

    # 配置
    config: DeploymentConfig

    # 运行时数据
    current_pnl: Decimal = Decimal("0")
    current_pnl_pct: float = 0
    total_trades: int = 0
    win_rate: float = 0

    # 时间戳
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    """部署列表响应"""
    total: int
    items: list[Deployment]


# ============ 参数范围限制 ============

class ParamLimits(BaseModel):
    """参数范围限制 (从策略回测结果继承)"""
    strategy_id: str

    # 风控参数范围
    stop_loss_range: ParamRange
    take_profit_range: ParamRange
    max_position_pct_range: ParamRange
    max_drawdown_range: ParamRange

    # 资金范围
    min_capital: Decimal = Field(Decimal("1000"), description="最低资金要求")

    # 股票池
    available_symbols: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True
