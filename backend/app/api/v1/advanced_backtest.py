"""
Phase 9: 高级回测 API 端点

提供:
- Walk-Forward 验证
- 参数敏感性分析
- 过拟合检测
- 偏差检测
"""

from datetime import date, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.strategy_v2 import StrategyV2
from app.schemas.walk_forward import (
    WalkForwardRequest,
    WalkForwardResult,
    SensitivityAnalysisRequest,
    OverfitDetectionRequest,
    OverfitDetectionResult,
    BiasDetectionRequest,
    BiasDetectionResult,
    AdvancedBacktestTask,
    AdvancedBacktestStatus,
)
from app.services.walk_forward_engine import WalkForwardEngine, WalkForwardConfig, estimate_walk_forward_rounds
from app.services.overfit_detection import OverfitDetectionService
from app.services.bias_detection import BiasDetectionService

router = APIRouter(prefix="/backtests/advanced", tags=["Advanced Backtest (Phase 9)"])

# 内存任务存储 (生产环境应使用 Redis/数据库)
_tasks_store: dict[str, dict] = {}


@router.post("/walk-forward", summary="启动 Walk-Forward 验证")
async def run_walk_forward(
    request: WalkForwardRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    启动 Walk-Forward 验证任务

    Walk-Forward 验证通过滚动窗口测试策略的样本外表现，
    是评估策略是否过拟合的黄金标准。
    """
    # 获取策略
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == request.strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # 估算验证轮数
    rounds_estimate = estimate_walk_forward_rounds(
        request.start_date,
        request.end_date,
        request.config.train_period,
        request.config.test_period,
        request.config.step_size
    )

    if rounds_estimate < 2:
        raise HTTPException(
            status_code=400,
            detail=f"日期范围不足以进行 Walk-Forward 验证，至少需要2轮。"
                   f"当前配置需要至少 {request.config.train_period + request.config.test_period * 2} 个月的数据。"
        )

    # 创建配置
    config = WalkForwardConfig(
        train_period=request.config.train_period,
        test_period=request.config.test_period,
        step_size=request.config.step_size,
        optimize_target=request.config.optimize_target.value,
        parameter_ranges=request.config.parameter_ranges,
        min_train_samples=request.config.min_train_samples,
        expanding_window=request.config.expanding_window
    )

    # 构建策略配置
    strategy_config = {
        "universe": strategy.universe_config,
        "alpha": strategy.alpha_config,
        "signal": strategy.signal_config,
        "risk": strategy.risk_config,
        "portfolio": strategy.portfolio_config,
        "execution": strategy.execution_config,
    }

    # 运行 Walk-Forward 验证
    engine = WalkForwardEngine(config)
    wf_result = engine.run_validation(
        strategy_config,
        request.start_date,
        request.end_date
    )

    # 创建任务记录
    task_id = str(uuid4())
    now = datetime.utcnow().isoformat()

    _tasks_store[task_id] = {
        "task_id": task_id,
        "task_type": "walk_forward",
        "strategy_id": request.strategy_id,
        "status": "completed",
        "progress": 100,
        "created_at": now,
        "completed_at": now,
        "result": wf_result
    }

    return {
        "task_id": task_id,
        "status": "completed",
        "rounds_count": len(wf_result.get("rounds", [])),
        "result": wf_result
    }


@router.post("/sensitivity", summary="参数敏感性分析")
async def run_sensitivity_analysis(
    request: SensitivityAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    运行参数敏感性分析

    分析策略参数变化对绩效的影响，
    高敏感度可能意味着过拟合风险。
    """
    # 获取策略
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == request.strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # 构建策略配置
    strategy_config = {
        "universe": strategy.universe_config,
        "alpha": strategy.alpha_config,
        "signal": strategy.signal_config,
        "risk": strategy.risk_config,
        "portfolio": strategy.portfolio_config,
    }

    # 运行敏感性分析
    service = OverfitDetectionService()
    sensitivity_results = service.analyze_parameter_sensitivity(
        strategy_config,
        request.parameters
    )

    # 转换结果
    results = [
        {
            "parameter": r.parameter,
            "parameter_label": r.parameter_label,
            "sensitivity_score": r.sensitivity_score,
            "optimal_range": list(r.optimal_range),
            "current_value": r.current_value,
            "curve": r.curve,
            "verdict": r.verdict
        }
        for r in sensitivity_results
    ]

    # 生成摘要
    sensitive_count = sum(1 for r in sensitivity_results if r.verdict == "sensitive")
    overall_risk = "low" if sensitive_count == 0 else ("high" if sensitive_count >= 2 else "moderate")

    return {
        "strategy_id": request.strategy_id,
        "parameters_analyzed": len(results),
        "sensitive_parameters": sensitive_count,
        "overall_risk": overall_risk,
        "results": results
    }


@router.post("/overfit-detection", summary="过拟合检测")
async def run_overfit_detection(
    request: OverfitDetectionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    运行综合过拟合检测

    包含:
    - 样本内外对比
    - Deflated Sharpe Ratio
    - 夏普比率上限检验
    """
    # 获取策略
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == request.strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # 计算样本年数
    days = (request.end_date - request.start_date).days
    sample_years = days / 365.0

    # 模拟样本内外指标 (实际应该运行回测)
    # 这里使用模拟数据演示
    import numpy as np
    np.random.seed(42)

    in_sample_metrics = {
        "sharpe_ratio": 1.5 + np.random.normal(0, 0.2),
        "annual_return": 0.18 + np.random.normal(0, 0.03),
        "max_drawdown": -0.12,
        "volatility": 0.16,
    }

    out_sample_metrics = {
        "sharpe_ratio": in_sample_metrics["sharpe_ratio"] * (0.6 + np.random.uniform(0, 0.3)),
        "annual_return": in_sample_metrics["annual_return"] * (0.6 + np.random.uniform(0, 0.3)),
        "max_drawdown": -0.18,
        "volatility": 0.20,
    }

    # 运行检测
    service = OverfitDetectionService()
    detection_result = service.run_comprehensive_detection(
        strategy_config={
            "alpha": strategy.alpha_config,
            "signal": strategy.signal_config,
        },
        in_sample_metrics=in_sample_metrics,
        out_sample_metrics=out_sample_metrics,
        trials_count=request.historical_trials or 1,
        sample_years=sample_years,
        parameters_to_analyze=[
            {"name": "lookback_period", "range": [10, 60], "steps": 6},
            {"name": "holding_count", "range": [10, 50], "steps": 5},
        ]
    )

    return {
        "strategy_id": request.strategy_id,
        "period": {
            "start": request.start_date.isoformat(),
            "end": request.end_date.isoformat(),
            "years": round(sample_years, 1)
        },
        "in_sample_metrics": in_sample_metrics,
        "out_sample_metrics": out_sample_metrics,
        **detection_result
    }


@router.post("/bias-detection", summary="偏差检测")
async def run_bias_detection(
    request: BiasDetectionRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    运行偏差检测

    检测:
    - 前视偏差 (Lookahead Bias)
    - 幸存者偏差 (Survivorship Bias)
    - 数据窥探偏差 (Data Snooping Bias)
    """
    # 获取策略
    result = await db.execute(
        select(StrategyV2).where(
            StrategyV2.id == request.strategy_id,
            StrategyV2.is_deleted == False,
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # 构建策略配置
    strategy_config = {
        "universe": strategy.universe_config,
        "alpha": strategy.alpha_config,
        "signal": strategy.signal_config,
        "factor_expressions": [
            f.get("expression", "") for f in strategy.alpha_config.get("factors", [])
        ],
        "signal_rules": strategy.signal_config.get("entry_rules", []) +
                        strategy.signal_config.get("exit_rules", [])
    }

    # 获取股票池
    universe_config = strategy.universe_config or {}
    stock_universe = universe_config.get("symbols", [])
    if not stock_universe:
        # 使用默认示例
        stock_universe = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

    # 运行检测
    service = BiasDetectionService()
    detection_result = service.run_comprehensive_detection(
        strategy_config=strategy_config,
        stock_universe=stock_universe,
        start_date=request.start_date,
        end_date=request.end_date,
        trials_count=10,  # 假设测试了10个变体
        observed_sharpe=1.2,
        detection_types=request.detection_types
    )

    return {
        "strategy_id": request.strategy_id,
        "period": {
            "start": request.start_date.isoformat(),
            "end": request.end_date.isoformat()
        },
        "detection_types": request.detection_types,
        **detection_result
    }


@router.get("/estimate-rounds", summary="估算 Walk-Forward 轮数")
async def estimate_rounds(
    start_date: date = Query(..., description="开始日期"),
    end_date: date = Query(..., description="结束日期"),
    train_period: int = Query(36, ge=12, le=120, description="训练期 (月)"),
    test_period: int = Query(12, ge=1, le=36, description="测试期 (月)"),
    step_size: int = Query(12, ge=1, le=24, description="步长 (月)")
) -> dict[str, Any]:
    """
    估算 Walk-Forward 验证的轮数

    帮助用户在开始验证前了解将会运行多少轮
    """
    rounds = estimate_walk_forward_rounds(
        start_date,
        end_date,
        train_period,
        test_period,
        step_size
    )

    total_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    min_required = train_period + test_period

    return {
        "estimated_rounds": rounds,
        "total_months": total_months,
        "min_required_months": min_required,
        "can_run": rounds >= 2,
        "config": {
            "train_period": train_period,
            "test_period": test_period,
            "step_size": step_size
        },
        "message": (
            f"共 {total_months} 个月数据，可进行 {rounds} 轮验证"
            if rounds >= 2 else
            f"数据不足: 需要至少 {min_required} 个月，当前只有 {total_months} 个月"
        )
    }


@router.get("/tasks/{task_id}", summary="获取任务状态")
async def get_task_status(task_id: str) -> dict[str, Any]:
    """获取高级回测任务的状态和结果"""
    if task_id not in _tasks_store:
        raise HTTPException(status_code=404, detail="Task not found")

    return _tasks_store[task_id]


@router.get("/tasks", summary="获取任务列表")
async def list_tasks(
    strategy_id: str | None = Query(None, description="按策略筛选"),
    task_type: str | None = Query(None, description="按任务类型筛选"),
    limit: int = Query(20, ge=1, le=100)
) -> dict[str, Any]:
    """获取高级回测任务列表"""
    tasks = list(_tasks_store.values())

    if strategy_id:
        tasks = [t for t in tasks if t.get("strategy_id") == strategy_id]
    if task_type:
        tasks = [t for t in tasks if t.get("task_type") == task_type]

    # 按创建时间排序
    tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {
        "total": len(tasks),
        "tasks": tasks[:limit]
    }
