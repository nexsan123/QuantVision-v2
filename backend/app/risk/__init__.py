"""
风险管理模块

提供:
- VaR 计算 (历史法/参数法/蒙特卡洛)
- 因子暴露分析
- 熔断器
- 压力测试
- 实时监控
"""

from app.risk.var_calculator import (
    VaRCalculator,
    VaRMethod,
    VaRResult,
    calculate_var,
    calculate_cvar,
)
from app.risk.factor_exposure import (
    FactorExposureCalculator,
    FactorExposure,
    ExposureReport,
)
from app.risk.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerConfig,
)
from app.risk.stress_test import (
    StressTester,
    StressScenario,
    StressTestResult,
)
from app.risk.monitor import (
    RiskMonitor,
    RiskAlert,
    AlertLevel,
    RiskMetrics,
)

__all__ = [
    # VaR
    "VaRCalculator",
    "VaRMethod",
    "VaRResult",
    "calculate_var",
    "calculate_cvar",
    # 因子暴露
    "FactorExposureCalculator",
    "FactorExposure",
    "ExposureReport",
    # 熔断器
    "CircuitBreaker",
    "CircuitBreakerState",
    "CircuitBreakerConfig",
    # 压力测试
    "StressTester",
    "StressScenario",
    "StressTestResult",
    # 监控
    "RiskMonitor",
    "RiskAlert",
    "AlertLevel",
    "RiskMetrics",
]
