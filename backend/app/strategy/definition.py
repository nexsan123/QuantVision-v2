"""
策略定义数据结构

提供:
- StrategyDefinition: 完整策略定义
- StrategyType: 策略类型枚举
- RebalanceFrequency: 调仓频率
- WeightMethod: 权重计算方法
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class StrategyType(str, Enum):
    """策略类型"""
    FACTOR = "factor"               # 因子策略
    MOMENTUM = "momentum"           # 动量策略
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    STATISTICAL_ARB = "stat_arb"    # 统计套利
    MACHINE_LEARNING = "ml"         # 机器学习
    CUSTOM = "custom"               # 自定义


class RebalanceFrequency(str, Enum):
    """调仓频率"""
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class WeightMethod(str, Enum):
    """权重计算方法"""
    EQUAL = "equal"                 # 等权
    IC_WEIGHTED = "ic_weighted"     # IC 加权
    RISK_PARITY = "risk_parity"     # 风险平价
    MIN_VARIANCE = "min_variance"   # 最小方差
    MAX_SHARPE = "max_sharpe"       # 最大夏普
    CUSTOM = "custom"               # 自定义权重


@dataclass
class FactorConfig:
    """因子配置"""
    name: str                       # 因子名称
    expression: str                 # 因子表达式
    weight: float = 1.0             # 因子权重
    direction: int = 1              # 方向 (1: 正向, -1: 反向)
    neutralize_industry: bool = False  # 行业中性化
    winsorize: bool = True          # 是否截尾
    winsorize_quantile: float = 0.01   # 截尾分位数


@dataclass
class UniverseConfig:
    """股票池配置"""
    base_universe: str              # 基础股票池 (如 "SP500", "NASDAQ100")
    min_price: float | None = None  # 最低价格
    max_price: float | None = None  # 最高价格
    min_volume: float | None = None # 最低成交量
    min_market_cap: float | None = None  # 最低市值
    exclude_sectors: list[str] = field(default_factory=list)  # 排除行业
    include_sectors: list[str] = field(default_factory=list)  # 只包含行业
    custom_filters: list[dict[str, Any]] = field(default_factory=list)  # 自定义筛选


@dataclass
class ConstraintConfig:
    """约束配置"""
    max_position_weight: float = 0.1    # 单只股票最大权重
    min_position_weight: float = 0.0    # 单只股票最小权重
    max_sector_weight: float = 0.3      # 单行业最大权重
    max_holdings: int = 100             # 最大持仓数量
    min_holdings: int = 10              # 最小持仓数量
    max_turnover: float = 1.0           # 最大换手率 (单次调仓)
    long_only: bool = True              # 是否只做多
    max_leverage: float = 1.0           # 最大杠杆


@dataclass
class ExecutionConfig:
    """执行配置"""
    slippage_model: str = "fixed"       # 滑点模型
    slippage_bps: float = 5.0           # 滑点基点
    commission_rate: float = 0.001      # 手续费率
    min_trade_value: float = 1000.0     # 最小交易金额
    market_impact: bool = False         # 是否考虑市场冲击


@dataclass
class StrategyDefinition:
    """
    完整策略定义

    包含:
    - 策略元信息
    - 因子配置
    - 股票池配置
    - 约束配置
    - 执行配置
    """

    # === 元信息 ===
    name: str                           # 策略名称
    description: str = ""               # 策略描述
    strategy_type: StrategyType = StrategyType.FACTOR
    version: str = "1.0.0"              # 版本号

    # === 时间配置 ===
    start_date: date | None = None      # 开始日期
    end_date: date | None = None        # 结束日期
    rebalance_freq: RebalanceFrequency = RebalanceFrequency.MONTHLY

    # === 因子配置 ===
    factors: list[FactorConfig] = field(default_factory=list)
    weight_method: WeightMethod = WeightMethod.EQUAL

    # === 股票池配置 ===
    universe: UniverseConfig = field(default_factory=lambda: UniverseConfig(base_universe="SP500"))

    # === 约束配置 ===
    constraints: ConstraintConfig = field(default_factory=ConstraintConfig)

    # === 执行配置 ===
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)

    # === 资金配置 ===
    initial_capital: float = 1_000_000.0
    benchmark: str = "SPY"

    # === 元数据 ===
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> list[str]:
        """
        验证策略定义的完整性

        Returns:
            错误消息列表，空列表表示验证通过
        """
        errors = []

        # 检查名称
        if not self.name or len(self.name) < 2:
            errors.append("策略名称至少需要2个字符")

        # 检查因子
        if self.strategy_type == StrategyType.FACTOR and not self.factors:
            errors.append("因子策略必须至少配置一个因子")

        # 检查日期
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                errors.append("开始日期必须早于结束日期")

        # 检查约束
        if self.constraints.min_holdings > self.constraints.max_holdings:
            errors.append("最小持仓数量不能超过最大持仓数量")

        if self.constraints.min_position_weight > self.constraints.max_position_weight:
            errors.append("最小仓位不能超过最大仓位")

        # 检查资金
        if self.initial_capital <= 0:
            errors.append("初始资金必须大于0")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "strategy_type": self.strategy_type.value,
            "version": self.version,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "rebalance_freq": self.rebalance_freq.value,
            "factors": [
                {
                    "name": f.name,
                    "expression": f.expression,
                    "weight": f.weight,
                    "direction": f.direction,
                }
                for f in self.factors
            ],
            "weight_method": self.weight_method.value,
            "universe": {
                "base_universe": self.universe.base_universe,
                "min_price": self.universe.min_price,
                "min_volume": self.universe.min_volume,
                "min_market_cap": self.universe.min_market_cap,
            },
            "constraints": {
                "max_position_weight": self.constraints.max_position_weight,
                "max_sector_weight": self.constraints.max_sector_weight,
                "max_holdings": self.constraints.max_holdings,
                "max_turnover": self.constraints.max_turnover,
                "long_only": self.constraints.long_only,
            },
            "initial_capital": self.initial_capital,
            "benchmark": self.benchmark,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StrategyDefinition":
        """从字典创建策略定义"""
        factors = [
            FactorConfig(
                name=f["name"],
                expression=f["expression"],
                weight=f.get("weight", 1.0),
                direction=f.get("direction", 1),
            )
            for f in data.get("factors", [])
        ]

        universe_data = data.get("universe", {})
        universe = UniverseConfig(
            base_universe=universe_data.get("base_universe", "SP500"),
            min_price=universe_data.get("min_price"),
            min_volume=universe_data.get("min_volume"),
            min_market_cap=universe_data.get("min_market_cap"),
        )

        constraints_data = data.get("constraints", {})
        constraints = ConstraintConfig(
            max_position_weight=constraints_data.get("max_position_weight", 0.1),
            max_sector_weight=constraints_data.get("max_sector_weight", 0.3),
            max_holdings=constraints_data.get("max_holdings", 100),
            max_turnover=constraints_data.get("max_turnover", 1.0),
            long_only=constraints_data.get("long_only", True),
        )

        return cls(
            name=data["name"],
            description=data.get("description", ""),
            strategy_type=StrategyType(data.get("strategy_type", "factor")),
            version=data.get("version", "1.0.0"),
            start_date=date.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=date.fromisoformat(data["end_date"]) if data.get("end_date") else None,
            rebalance_freq=RebalanceFrequency(data.get("rebalance_freq", "monthly")),
            factors=factors,
            weight_method=WeightMethod(data.get("weight_method", "equal")),
            universe=universe,
            constraints=constraints,
            initial_capital=data.get("initial_capital", 1_000_000.0),
            benchmark=data.get("benchmark", "SPY"),
        )
