"""
策略框架模块

提供:
- 策略定义数据结构
- 股票池筛选器
- 因子权重优化器
- 组合约束处理
- 信号生成器
"""

from app.strategy.constraints import (
    Constraint,
    ConstraintChecker,
    ConstraintType,
    ConstraintViolation,
    PortfolioConstraints,
    apply_constraints,
)
from app.strategy.definition import (
    ConstraintConfig,
    ExecutionConfig,
    FactorConfig,
    RebalanceFrequency,
    StrategyDefinition,
    StrategyType,
    UniverseConfig,
    WeightMethod,
)
from app.strategy.signal_generator import (
    SignalConfig,
    SignalGenerator,
    SignalOutput,
    SignalScaling,
    SignalType,
    combine_signals,
    generate_equal_weight_signals,
    generate_quantile_signals,
    generate_top_n_signals,
)
from app.strategy.universe_filter import (
    FilterCondition,
    FilterOperator,
    UniverseFilter,
    create_large_cap_filter,
    create_mid_cap_filter,
    create_quality_filter,
    create_small_cap_filter,
)
from app.strategy.weight_optimizer import (
    OptimizationMethod,
    OptimizationResult,
    WeightOptimizer,
    equal_weight,
    max_sharpe,
    min_variance,
    risk_parity,
)

__all__ = [
    # 策略定义
    "StrategyDefinition",
    "StrategyType",
    "RebalanceFrequency",
    "WeightMethod",
    "FactorConfig",
    "UniverseConfig",
    "ConstraintConfig",
    "ExecutionConfig",
    # 股票池筛选
    "UniverseFilter",
    "FilterCondition",
    "FilterOperator",
    "create_large_cap_filter",
    "create_mid_cap_filter",
    "create_small_cap_filter",
    "create_quality_filter",
    # 权重优化
    "WeightOptimizer",
    "OptimizationMethod",
    "OptimizationResult",
    "equal_weight",
    "risk_parity",
    "min_variance",
    "max_sharpe",
    # 组合约束
    "PortfolioConstraints",
    "ConstraintType",
    "ConstraintChecker",
    "Constraint",
    "ConstraintViolation",
    "apply_constraints",
    # 信号生成
    "SignalGenerator",
    "SignalType",
    "SignalConfig",
    "SignalScaling",
    "SignalOutput",
    "generate_equal_weight_signals",
    "generate_top_n_signals",
    "generate_quantile_signals",
    "combine_signals",
]
