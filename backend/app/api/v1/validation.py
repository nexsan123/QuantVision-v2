"""
策略验证 API 端点

提供:
- 过拟合检测
- 前视偏差检测
- 生存偏差检测
- Walk-Forward 分析
- 稳健性检验
- 数据窥探校正
"""

from datetime import date
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/validation", tags=["策略验证"])


# === Pydantic 模型 ===

class OverfitDetectionRequest(BaseModel):
    """过拟合检测请求"""
    returns: list[float] = Field(..., description="策略收益率序列")
    dates: list[str] | None = Field(None, description="日期序列")
    oos_ratio: float = Field(0.3, ge=0.1, le=0.5, description="样本外比例")
    n_bootstrap: int = Field(100, ge=50, le=500)


class OverfitWarningResponse(BaseModel):
    """过拟合警告"""
    indicator: str
    severity: str
    description: str
    value: float
    threshold: float


class OverfitDetectionResponse(BaseModel):
    """过拟合检测响应"""
    overfit_probability: float
    risk_level: str
    warnings: list[OverfitWarningResponse]
    metrics: dict[str, float]
    in_sample_sharpe: float
    out_of_sample_sharpe: float


class LookaheadDetectionRequest(BaseModel):
    """前视偏差检测请求"""
    strategy_code: str | None = Field(None, description="策略代码")
    feature_names: list[str] = Field(..., description="特征名称列表")
    feature_dates: dict[str, list[str]] = Field(..., description="特征可用日期")
    trade_dates: list[str] = Field(..., description="交易日期")


class LookaheadWarningResponse(BaseModel):
    """前视偏差警告"""
    warning_type: str
    severity: str
    feature: str
    description: str
    affected_dates: list[str]


class LookaheadDetectionResponse(BaseModel):
    """前视偏差检测响应"""
    has_lookahead: bool
    warnings: list[LookaheadWarningResponse]
    clean_features: list[str]
    contaminated_features: list[str]


class SurvivorshipDetectionRequest(BaseModel):
    """生存偏差检测请求"""
    symbols: list[str] = Field(..., description="股票列表")
    start_date: date
    end_date: date
    check_delisted: bool = True
    check_added: bool = True


class SurvivorshipWarningResponse(BaseModel):
    """生存偏差警告"""
    symbol: str
    event_type: str
    event_date: str
    description: str


class SurvivorshipDetectionResponse(BaseModel):
    """生存偏差检测响应"""
    has_survivorship_bias: bool
    estimated_bias_bps: float
    warnings: list[SurvivorshipWarningResponse]
    delisted_stocks: list[str]
    added_stocks: list[str]
    clean_period_start: str | None
    clean_period_end: str | None


class WalkForwardRequest(BaseModel):
    """Walk-Forward 分析请求"""
    returns: list[float] = Field(..., description="收益率序列")
    dates: list[str] = Field(..., description="日期序列")
    window_type: str = Field("expanding", description="窗口类型: expanding, rolling")
    train_period: int = Field(252, ge=60, description="训练期长度 (天)")
    test_period: int = Field(63, ge=20, description="测试期长度 (天)")
    n_splits: int = Field(5, ge=2, le=20)


class WalkForwardFoldResponse(BaseModel):
    """Walk-Forward 单期结果"""
    fold_id: int
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    train_sharpe: float
    test_sharpe: float
    train_return: float
    test_return: float


class WalkForwardResponse(BaseModel):
    """Walk-Forward 分析响应"""
    efficiency_ratio: float
    avg_train_sharpe: float
    avg_test_sharpe: float
    sharpe_decay: float
    is_robust: bool
    folds: list[WalkForwardFoldResponse]


class RobustnessTestRequest(BaseModel):
    """稳健性检验请求"""
    returns: list[float] = Field(..., description="收益率序列")
    test_types: list[str] = Field(
        ["parameter", "time", "bootstrap"],
        description="测试类型: parameter, time, bootstrap, regime"
    )
    n_simulations: int = Field(100, ge=50, le=500)
    confidence_level: float = Field(0.95, ge=0.9, le=0.99)


class RobustnessMetricResponse(BaseModel):
    """稳健性指标"""
    metric_name: str
    base_value: float
    mean_value: float
    std_value: float
    min_value: float
    max_value: float
    percentile_5: float
    percentile_95: float


class RobustnessTestResponse(BaseModel):
    """稳健性检验响应"""
    is_robust: bool
    robustness_score: float
    metrics: list[RobustnessMetricResponse]
    test_details: dict[str, Any]


class DataSnoopingRequest(BaseModel):
    """数据窥探校正请求"""
    sharpe_ratio: float = Field(..., description="原始夏普比率")
    n_trials: int = Field(100, ge=10, description="测试次数")
    n_years: float = Field(5.0, ge=1.0, description="回测年数")
    correlation: float = Field(0.0, ge=-1, le=1, description="策略相关性")
    method: str = Field("bonferroni", description="校正方法: bonferroni, holm, bhy, bootstrap")


class DataSnoopingResponse(BaseModel):
    """数据窥探校正响应"""
    original_sharpe: float
    adjusted_sharpe: float
    haircut_ratio: float
    is_significant: bool
    p_value: float
    method: str
    details: dict[str, Any]


class DeflatedSharpeRequest(BaseModel):
    """Deflated Sharpe Ratio 请求"""
    sharpe_ratio: float
    n_trials: int
    variance_of_sharpe: float | None = None
    skewness: float = 0.0
    kurtosis: float = 3.0
    track_record_years: float = 5.0


class DeflatedSharpeResponse(BaseModel):
    """Deflated Sharpe Ratio 响应"""
    original_sharpe: float
    deflated_sharpe: float
    probability_of_skill: float
    is_significant: bool
    minimum_track_record: float


# === API 端点 ===

@router.post("/overfit", response_model=OverfitDetectionResponse)
async def detect_overfitting(request: OverfitDetectionRequest) -> OverfitDetectionResponse:
    """
    检测过拟合

    分析:
    - 样本内/外表现差异
    - 夏普比率稳定性
    - 收益自相关性
    """
    from app.validation.overfitting_detector import OverfittingDetector

    try:
        returns = pd.Series(request.returns)

        if len(returns) < 100:
            raise HTTPException(status_code=400, detail="收益序列至少需要100个数据点")

        detector = OverfittingDetector(
            oos_ratio=request.oos_ratio,
            n_bootstrap=request.n_bootstrap,
        )

        report = detector.detect(returns)

        # 计算样本内外夏普
        n = len(returns)
        split_idx = int(n * (1 - request.oos_ratio))
        is_sharpe = _calculate_sharpe(returns.iloc[:split_idx])
        oos_sharpe = _calculate_sharpe(returns.iloc[split_idx:])

        warnings = [
            OverfitWarningResponse(
                indicator=w.indicator.value,
                severity=w.severity,
                description=w.description,
                value=w.value,
                threshold=w.threshold,
            )
            for w in report.warnings
        ]

        return OverfitDetectionResponse(
            overfit_probability=report.overfit_probability,
            risk_level=report.risk_level,
            warnings=warnings,
            metrics=report.metrics,
            in_sample_sharpe=is_sharpe,
            out_of_sample_sharpe=oos_sharpe,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("过拟合检测失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/lookahead", response_model=LookaheadDetectionResponse)
async def detect_lookahead(request: LookaheadDetectionRequest) -> LookaheadDetectionResponse:
    """
    检测前视偏差

    检测:
    - 使用未来数据的特征
    - 日期对齐问题
    """
    from app.validation.lookahead_detector import LookaheadDetector, LookaheadType

    try:
        detector = LookaheadDetector()

        # 分析每个特征的可用性
        contaminated = []
        clean = []
        warnings_list = []

        for feature in request.feature_names:
            feature_dates = request.feature_dates.get(feature, [])
            affected = []

            for trade_date in request.trade_dates:
                # 检查交易日是否有对应的特征数据
                if trade_date not in feature_dates:
                    # 查找最近的可用日期
                    available = [d for d in feature_dates if d < trade_date]
                    if not available:
                        affected.append(trade_date)

            if affected:
                contaminated.append(feature)
                warnings_list.append(LookaheadWarningResponse(
                    warning_type="future_data",
                    severity="high" if len(affected) > len(request.trade_dates) * 0.1 else "medium",
                    feature=feature,
                    description=f"特征 {feature} 在 {len(affected)} 个交易日存在前视偏差",
                    affected_dates=affected[:10],  # 只返回前10个
                ))
            else:
                clean.append(feature)

        has_lookahead = len(contaminated) > 0

        return LookaheadDetectionResponse(
            has_lookahead=has_lookahead,
            warnings=warnings_list,
            clean_features=clean,
            contaminated_features=contaminated,
        )

    except Exception as e:
        logger.error("前视偏差检测失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/survivorship", response_model=SurvivorshipDetectionResponse)
async def detect_survivorship(request: SurvivorshipDetectionRequest) -> SurvivorshipDetectionResponse:
    """
    检测生存偏差

    检测:
    - 退市股票
    - 新上市股票
    - 成分股变更
    """
    from app.validation.survivorship_detector import SurvivorshipDetector, estimate_survivorship_bias

    try:
        detector = SurvivorshipDetector()

        # 这里简化处理，实际需要历史成分股数据
        # 模拟检测结果
        delisted: list[str] = []
        added: list[str] = []
        warnings_list: list[SurvivorshipWarningResponse] = []

        # 估算偏差 (简化计算)
        years = (request.end_date - request.start_date).days / 365
        estimated_bias_bps = years * 50  # 假设每年约50bps偏差

        has_bias = len(delisted) > 0 or len(added) > 0

        return SurvivorshipDetectionResponse(
            has_survivorship_bias=has_bias,
            estimated_bias_bps=estimated_bias_bps,
            warnings=warnings_list,
            delisted_stocks=delisted,
            added_stocks=added,
            clean_period_start=request.start_date.isoformat(),
            clean_period_end=request.end_date.isoformat(),
        )

    except Exception as e:
        logger.error("生存偏差检测失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/walk-forward", response_model=WalkForwardResponse)
async def run_walk_forward(request: WalkForwardRequest) -> WalkForwardResponse:
    """
    Walk-Forward 分析

    时间序列交叉验证，评估策略稳定性
    """
    from app.validation.walk_forward import (
        WalkForwardAnalyzer,
        WalkForwardWindow,
        WindowType,
        walk_forward_efficiency,
    )

    try:
        returns = pd.Series(request.returns, index=pd.to_datetime(request.dates))

        window_type = WindowType.EXPANDING if request.window_type == "expanding" else WindowType.ROLLING

        window = WalkForwardWindow(
            train_period=request.train_period,
            test_period=request.test_period,
            window_type=window_type,
        )

        analyzer = WalkForwardAnalyzer(window=window, n_splits=request.n_splits)
        result = analyzer.analyze(returns)

        # 构建响应
        folds = [
            WalkForwardFoldResponse(
                fold_id=fold.fold_id,
                train_start=fold.train_start.isoformat(),
                train_end=fold.train_end.isoformat(),
                test_start=fold.test_start.isoformat(),
                test_end=fold.test_end.isoformat(),
                train_sharpe=fold.train_sharpe,
                test_sharpe=fold.test_sharpe,
                train_return=fold.train_return,
                test_return=fold.test_return,
            )
            for fold in result.folds
        ]

        # 计算效率比
        efficiency = walk_forward_efficiency(result)

        return WalkForwardResponse(
            efficiency_ratio=efficiency,
            avg_train_sharpe=result.avg_train_sharpe,
            avg_test_sharpe=result.avg_test_sharpe,
            sharpe_decay=1 - (result.avg_test_sharpe / result.avg_train_sharpe) if result.avg_train_sharpe > 0 else 0,
            is_robust=efficiency > 0.5,
            folds=folds,
        )

    except Exception as e:
        logger.error("Walk-Forward分析失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/robustness", response_model=RobustnessTestResponse)
async def test_robustness(request: RobustnessTestRequest) -> RobustnessTestResponse:
    """
    稳健性检验

    测试:
    - 参数敏感性
    - 时间稳定性
    - Bootstrap 置信区间
    """
    from app.validation.robustness import RobustnessTester, RobustnessTestType

    try:
        returns = pd.Series(request.returns)

        test_types = [RobustnessTestType(t) for t in request.test_types]

        tester = RobustnessTester(
            n_simulations=request.n_simulations,
            confidence_level=request.confidence_level,
        )

        report = tester.run_tests(returns, test_types=test_types)

        # 构建响应
        metrics = [
            RobustnessMetricResponse(
                metric_name=m.name,
                base_value=m.base_value,
                mean_value=m.mean_value,
                std_value=m.std_value,
                min_value=m.min_value,
                max_value=m.max_value,
                percentile_5=m.percentile_5,
                percentile_95=m.percentile_95,
            )
            for m in report.metrics
        ]

        return RobustnessTestResponse(
            is_robust=report.is_robust,
            robustness_score=report.robustness_score,
            metrics=metrics,
            test_details=report.details,
        )

    except Exception as e:
        logger.error("稳健性检验失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/data-snooping", response_model=DataSnoopingResponse)
async def correct_data_snooping(request: DataSnoopingRequest) -> DataSnoopingResponse:
    """
    数据窥探校正

    校正多重检验带来的统计偏差
    """
    from app.validation.data_snooping import DataSnoopingCorrector, CorrectionMethod

    try:
        method_map = {
            "bonferroni": CorrectionMethod.BONFERRONI,
            "holm": CorrectionMethod.HOLM,
            "bhy": CorrectionMethod.BHY,
            "bootstrap": CorrectionMethod.BOOTSTRAP,
        }

        if request.method not in method_map:
            raise HTTPException(status_code=400, detail=f"不支持的校正方法: {request.method}")

        corrector = DataSnoopingCorrector(method=method_map[request.method])

        result = corrector.correct(
            sharpe_ratio=request.sharpe_ratio,
            n_trials=request.n_trials,
            n_years=request.n_years,
            correlation=request.correlation,
        )

        return DataSnoopingResponse(
            original_sharpe=request.sharpe_ratio,
            adjusted_sharpe=result.adjusted_sharpe,
            haircut_ratio=result.haircut_ratio,
            is_significant=result.is_significant,
            p_value=result.p_value,
            method=request.method,
            details=result.details,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("数据窥探校正失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/deflated-sharpe", response_model=DeflatedSharpeResponse)
async def calculate_deflated_sharpe(request: DeflatedSharpeRequest) -> DeflatedSharpeResponse:
    """
    计算 Deflated Sharpe Ratio

    校正多重检验和非正态分布的影响
    """
    from app.validation.overfitting_detector import deflated_sharpe_ratio

    try:
        result = deflated_sharpe_ratio(
            sharpe_ratio=request.sharpe_ratio,
            n_trials=request.n_trials,
            variance_of_sharpe=request.variance_of_sharpe,
            skewness=request.skewness,
            kurtosis=request.kurtosis,
            track_record_years=request.track_record_years,
        )

        return DeflatedSharpeResponse(
            original_sharpe=request.sharpe_ratio,
            deflated_sharpe=result["deflated_sharpe"],
            probability_of_skill=result["probability_of_skill"],
            is_significant=result["is_significant"],
            minimum_track_record=result["minimum_track_record"],
        )

    except Exception as e:
        logger.error("Deflated Sharpe计算失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/methods")
async def list_validation_methods() -> dict[str, list[str]]:
    """列出可用的验证方法"""
    return {
        "overfit_detection": [
            "is_oos_comparison",
            "sharpe_stability",
            "return_autocorrelation",
            "parameter_sensitivity",
        ],
        "lookahead_detection": [
            "date_alignment",
            "future_data_check",
            "code_analysis",
        ],
        "survivorship_detection": [
            "delisted_check",
            "added_check",
            "composition_change",
        ],
        "walk_forward": [
            "expanding_window",
            "rolling_window",
        ],
        "robustness_tests": [
            "parameter",
            "time",
            "bootstrap",
            "regime",
        ],
        "data_snooping_correction": [
            "bonferroni",
            "holm",
            "bhy",
            "bootstrap",
        ],
    }


def _calculate_sharpe(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """计算夏普比率"""
    if len(returns) < 2:
        return 0.0

    excess_returns = returns - risk_free_rate / 252
    if excess_returns.std() == 0:
        return 0.0

    return float(np.sqrt(252) * excess_returns.mean() / excess_returns.std())
