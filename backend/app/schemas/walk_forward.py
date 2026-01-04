"""
Phase 9: 回测引擎升级 - Pydantic Schema

包含:
- Walk-Forward 验证
- 过拟合检测
- 偏差检测
"""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================
# 枚举类型
# ============================================================

class OptimizeTarget(str, Enum):
    """优化目标"""
    SHARPE = "sharpe"
    RETURNS = "returns"
    CALMAR = "calmar"
    SORTINO = "sortino"


class Severity(str, Enum):
    """严重程度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Verdict(str, Enum):
    """评估结论"""
    ROBUST = "robust"
    MODERATE = "moderate"
    LIKELY_OVERFIT = "likely_overfit"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class BiasRiskLevel(str, Enum):
    """偏差风险等级"""
    CLEAN = "clean"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"


class Assessment(str, Enum):
    """综合评估"""
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    OVERFIT = "overfit"


class Confidence(str, Enum):
    """置信度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AdjustmentMethod(str, Enum):
    """多重检验调整方法"""
    BONFERRONI = "bonferroni"
    HOLM = "holm"
    FDR = "fdr"


class ParameterVerdict(str, Enum):
    """参数敏感性评估"""
    STABLE = "stable"
    MODERATE = "moderate"
    SENSITIVE = "sensitive"


# ============================================================
# Walk-Forward 验证
# ============================================================

class ParameterRange(BaseModel):
    """参数范围"""
    min: float = Field(..., description="最小值")
    max: float = Field(..., description="最大值")
    step: float = Field(..., description="步长")


class WalkForwardConfig(BaseModel):
    """Walk-Forward 配置"""
    train_period: int = Field(36, ge=12, le=120, description="训练期长度 (月)")
    test_period: int = Field(12, ge=1, le=36, description="测试期长度 (月)")
    step_size: int = Field(12, ge=1, le=24, description="滚动步长 (月)")
    optimize_target: OptimizeTarget = Field(
        OptimizeTarget.SHARPE,
        description="优化目标"
    )
    parameter_ranges: dict[str, list[float]] = Field(
        default_factory=dict,
        description="参数优化范围 {name: [min, max, step]}"
    )
    min_train_samples: int = Field(252, ge=60, description="最小训练样本数")
    expanding_window: bool = Field(False, description="是否使用扩展窗口")


class WalkForwardRequest(BaseModel):
    """Walk-Forward 验证请求"""
    strategy_id: str = Field(..., description="策略 ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    initial_capital: float = Field(1_000_000, ge=10000, description="初始资金")
    config: WalkForwardConfig = Field(
        default_factory=WalkForwardConfig,
        description="Walk-Forward 配置"
    )


class BacktestMetricsSchema(BaseModel):
    """回测指标"""
    total_return: float = Field(..., description="总收益")
    annual_return: float = Field(..., description="年化收益")
    volatility: float = Field(0.0, description="年化波动率")
    max_drawdown: float = Field(..., description="最大回撤")
    sharpe_ratio: float = Field(..., description="夏普比率")
    sortino_ratio: float = Field(0.0, description="索提诺比率")
    calmar_ratio: float = Field(0.0, description="卡尔马比率")
    win_rate: float = Field(0.0, description="胜率")
    profit_factor: float = Field(0.0, description="盈亏比")
    beta: float = Field(0.0, description="贝塔")
    alpha: float = Field(0.0, description="阿尔法")


class WalkForwardRound(BaseModel):
    """Walk-Forward 单轮结果"""
    round_number: int = Field(..., description="轮次")
    train_start: date = Field(..., description="训练开始日期")
    train_end: date = Field(..., description="训练结束日期")
    test_start: date = Field(..., description="测试开始日期")
    test_end: date = Field(..., description="测试结束日期")
    optimized_params: dict[str, float] = Field(..., description="优化后参数")
    in_sample_metrics: BacktestMetricsSchema = Field(..., description="样本内指标")
    out_of_sample_metrics: BacktestMetricsSchema = Field(..., description="样本外指标")
    stability_ratio: float = Field(..., description="稳定性比率")


class AggregatedMetrics(BaseModel):
    """汇总指标"""
    oos_sharpe: float = Field(..., description="样本外夏普")
    oos_returns: float = Field(..., description="样本外年化收益")
    oos_max_drawdown: float = Field(..., description="样本外最大回撤")
    stability_ratio: float = Field(..., description="稳定性比率")
    oos_win_rate: float = Field(0.0, description="样本外胜率")


class EquityPoint(BaseModel):
    """权益曲线点"""
    date: str
    value: float


class WalkForwardResult(BaseModel):
    """Walk-Forward 验证结果"""
    config: WalkForwardConfig
    rounds: list[WalkForwardRound]
    aggregated_metrics: AggregatedMetrics
    overfit_probability: float = Field(..., ge=0, le=100, description="过拟合概率")
    assessment: Assessment = Field(..., description="综合评估")
    recommendations: list[str] = Field(default_factory=list, description="建议")
    oos_equity_curve: list[EquityPoint] = Field(
        default_factory=list,
        description="样本外权益曲线"
    )


# ============================================================
# 过拟合检测
# ============================================================

class SensitivityCurvePoint(BaseModel):
    """敏感性曲线点"""
    param_value: float
    sharpe: float
    returns: float


class ParameterSensitivity(BaseModel):
    """参数敏感性分析"""
    parameter: str = Field(..., description="参数名")
    parameter_label: str = Field(..., description="参数标签")
    sensitivity_score: float = Field(..., ge=0, le=1, description="敏感度得分")
    optimal_range: list[float] = Field(..., description="最优范围 [min, max]")
    current_value: float = Field(..., description="当前值")
    curve: list[SensitivityCurvePoint] = Field(..., description="敏感性曲线")
    verdict: ParameterVerdict = Field(..., description="评估")


class InOutSampleComparison(BaseModel):
    """样本内外对比"""
    in_sample_sharpe: float
    out_sample_sharpe: float
    in_sample_returns: float
    out_sample_returns: float
    stability_ratio: float
    verdict: Verdict


class DeflatedSharpeRatio(BaseModel):
    """Deflated Sharpe Ratio"""
    original_sharpe: float = Field(..., description="原始夏普")
    deflated_sharpe: float = Field(..., description="调整后夏普")
    trials_count: int = Field(..., description="试验次数")
    adjustment_factor: float = Field(..., description="调整系数")
    p_value: float = Field(..., description="p值")
    significant: bool = Field(..., description="是否显著")


class SharpeUpperBound(BaseModel):
    """夏普比率上限检验"""
    observed_sharpe: float
    theoretical_upper_bound: float
    exceeds_probability: float
    verdict: Verdict


class OverallOverfitAssessment(BaseModel):
    """综合过拟合评估"""
    overfit_probability: float = Field(..., ge=0, le=100, description="过拟合概率")
    confidence: Confidence = Field(..., description="置信度")
    risk_level: RiskLevel = Field(..., description="风险等级")
    recommendations: list[str] = Field(default_factory=list, description="建议")
    explanation: str = Field("", description="详细说明")


class OverfitDetectionResult(BaseModel):
    """过拟合检测结果"""
    parameter_sensitivity: list[ParameterSensitivity] = Field(
        default_factory=list,
        description="参数敏感性分析"
    )
    in_out_sample_comparison: InOutSampleComparison | None = None
    deflated_sharpe_ratio: DeflatedSharpeRatio | None = None
    sharpe_upper_bound: SharpeUpperBound | None = None
    overall_assessment: OverallOverfitAssessment


class SensitivityAnalysisRequest(BaseModel):
    """参数敏感性分析请求"""
    strategy_id: str = Field(..., description="策略 ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    initial_capital: float = Field(1_000_000, ge=10000, description="初始资金")
    parameters: list[dict[str, Any]] = Field(
        ...,
        description="要分析的参数 [{name, range: [min, max], steps}]"
    )


class OverfitDetectionRequest(BaseModel):
    """过拟合检测请求"""
    strategy_id: str = Field(..., description="策略 ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    initial_capital: float = Field(1_000_000, ge=10000, description="初始资金")
    in_sample_ratio: float = Field(0.7, ge=0.5, le=0.9, description="样本内占比")
    historical_trials: int | None = Field(None, ge=1, description="历史试验次数")


# ============================================================
# 偏差检测
# ============================================================

class LookaheadBiasIssue(BaseModel):
    """前视偏差问题"""
    field: str = Field(..., description="字段名")
    description: str = Field(..., description="问题描述")
    severity: Severity = Field(..., description="严重程度")
    location: str = Field(..., description="位置")
    suggestion: str = Field(..., description="修复建议")


class LookaheadBiasDetection(BaseModel):
    """前视偏差检测"""
    detected: bool = Field(..., description="是否检测到")
    issues: list[LookaheadBiasIssue] = Field(default_factory=list, description="问题列表")
    risk_score: float = Field(0.0, ge=0, le=100, description="风险得分")


class SurvivorshipBiasDetection(BaseModel):
    """幸存者偏差检测"""
    detected: bool = Field(..., description="是否检测到")
    delisted_stocks_used: list[str] = Field(
        default_factory=list,
        description="使用的已退市股票"
    )
    delisted_count: int = Field(0, description="退市股票数量")
    impact_estimate: float = Field(0.0, description="对收益的影响估计")
    recommendation: str = Field("", description="建议")


class DataSnoopingBias(BaseModel):
    """数据窥探偏差"""
    trials_count: int = Field(..., description="试验次数")
    original_p_value: float = Field(..., description="原始 p 值")
    adjusted_p_value: float = Field(..., description="调整后 p 值")
    adjustment_method: AdjustmentMethod = Field(..., description="调整方法")
    still_significant: bool = Field(..., description="是否仍显著")


class OverallBiasAssessment(BaseModel):
    """综合偏差评估"""
    total_issues: int = Field(0, description="总问题数")
    critical_issues: int = Field(0, description="严重问题数")
    risk_level: BiasRiskLevel = Field(..., description="风险等级")
    recommendations: list[str] = Field(default_factory=list, description="建议")


class BiasDetectionResult(BaseModel):
    """偏差检测结果"""
    lookahead_bias: LookaheadBiasDetection | None = None
    survivorship_bias: SurvivorshipBiasDetection | None = None
    data_snooping_bias: DataSnoopingBias | None = None
    overall_assessment: OverallBiasAssessment


class BiasDetectionRequest(BaseModel):
    """偏差检测请求"""
    strategy_id: str = Field(..., description="策略 ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    detection_types: list[str] = Field(
        ["lookahead", "survivorship", "snooping"],
        description="检测类型"
    )


# ============================================================
# 任务状态
# ============================================================

class AdvancedBacktestStatus(str, Enum):
    """高级回测状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AdvancedBacktestTask(BaseModel):
    """高级回测任务"""
    task_id: str = Field(..., description="任务 ID")
    task_type: str = Field(..., description="任务类型")
    strategy_id: str = Field(..., description="策略 ID")
    status: AdvancedBacktestStatus = Field(..., description="状态")
    progress: int = Field(0, ge=0, le=100, description="进度")
    created_at: str = Field(..., description="创建时间")
    completed_at: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = None
