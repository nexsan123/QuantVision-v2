"""
策略验证模块

提供:
- 偏差检测 (前视、生存、过拟合)
- 数据窥探校正
- Walk-Forward 分析
- 稳健性检验
"""

from app.validation.data_snooping import (
    BootstrapCorrector,
    CorrectionMethod,
    CorrectionResult,
    DataSnoopingCorrector,
    DataSnoopingReport,
    adjusted_sharpe_ratio,
)
from app.validation.lookahead_detector import (
    LookaheadDetector,
    LookaheadReport,
    LookaheadType,
    LookaheadWarning,
    quick_lookahead_check,
)
from app.validation.overfitting_detector import (
    OverfitIndicator,
    OverfitReport,
    OverfittingDetector,
    OverfitWarning,
    deflated_sharpe_ratio,
    quick_overfit_check,
)
from app.validation.robustness import (
    RobustnessMetric,
    RobustnessReport,
    RobustnessTester,
    RobustnessTestType,
    stress_test,
)
from app.validation.survivorship_detector import (
    DelistedStock,
    DelistReason,
    SurvivorshipDetector,
    SurvivorshipReport,
    SurvivorshipWarning,
    estimate_survivorship_bias,
)
from app.validation.walk_forward import (
    SampleSplitter,
    WalkForwardAnalyzer,
    WalkForwardFold,
    WalkForwardResult,
    WalkForwardWindow,
    WindowType,
    walk_forward_efficiency,
)

__all__ = [
    # 前视偏差检测
    "LookaheadDetector",
    "LookaheadType",
    "LookaheadWarning",
    "LookaheadReport",
    "quick_lookahead_check",
    # 生存偏差检测
    "SurvivorshipDetector",
    "DelistReason",
    "DelistedStock",
    "SurvivorshipWarning",
    "SurvivorshipReport",
    "estimate_survivorship_bias",
    # 过拟合检测
    "OverfittingDetector",
    "OverfitIndicator",
    "OverfitWarning",
    "OverfitReport",
    "quick_overfit_check",
    "deflated_sharpe_ratio",
    # 数据窥探校正
    "DataSnoopingCorrector",
    "CorrectionMethod",
    "CorrectionResult",
    "DataSnoopingReport",
    "BootstrapCorrector",
    "adjusted_sharpe_ratio",
    # Walk-Forward
    "WalkForwardAnalyzer",
    "WindowType",
    "WalkForwardWindow",
    "WalkForwardFold",
    "WalkForwardResult",
    "SampleSplitter",
    "walk_forward_efficiency",
    # 稳健性检验
    "RobustnessTester",
    "RobustnessTestType",
    "RobustnessMetric",
    "RobustnessReport",
    "stress_test",
]
