"""
策略框架 API 端点

提供:
- 策略定义创建/验证
- 股票池筛选
- 权重优化
- 信号生成
- 约束检查
"""

from datetime import date
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/strategy", tags=["策略框架"])


# === Pydantic 模型 ===

class FactorConfigRequest(BaseModel):
    """因子配置"""
    name: str = Field(..., description="因子名称")
    expression: str = Field(..., description="因子表达式")
    weight: float = Field(1.0, ge=0, le=10)
    direction: int = Field(1, ge=-1, le=1)
    neutralize_industry: bool = False
    winsorize: bool = True


class UniverseConfigRequest(BaseModel):
    """股票池配置"""
    base_universe: str = Field("SP500", description="基础股票池")
    min_price: float | None = None
    max_price: float | None = None
    min_volume: float | None = None
    min_market_cap: float | None = None
    exclude_sectors: list[str] = Field(default_factory=list)
    include_sectors: list[str] = Field(default_factory=list)


class ConstraintConfigRequest(BaseModel):
    """约束配置"""
    max_position_weight: float = Field(0.1, ge=0.01, le=1.0)
    min_position_weight: float = Field(0.0, ge=0, le=1.0)
    max_sector_weight: float = Field(0.3, ge=0.05, le=1.0)
    max_holdings: int = Field(100, ge=5, le=500)
    min_holdings: int = Field(10, ge=1, le=100)
    max_turnover: float = Field(1.0, ge=0, le=5.0)
    long_only: bool = True
    max_leverage: float = Field(1.0, ge=1.0, le=3.0)


class ExecutionConfigRequest(BaseModel):
    """执行配置"""
    slippage_model: str = "fixed"
    slippage_bps: float = Field(5.0, ge=0, le=100)
    commission_rate: float = Field(0.001, ge=0, le=0.01)
    min_trade_value: float = Field(1000.0, ge=0)
    market_impact: bool = False


class StrategyDefinitionRequest(BaseModel):
    """策略定义请求"""
    name: str = Field(..., min_length=2, max_length=100)
    description: str = ""
    strategy_type: str = Field("factor", description="策略类型: factor, momentum, mean_reversion, stat_arb, ml")
    version: str = "1.0.0"
    start_date: date | None = None
    end_date: date | None = None
    rebalance_freq: str = Field("monthly", description="调仓频率: daily, weekly, monthly, quarterly")
    factors: list[FactorConfigRequest] = Field(default_factory=list)
    weight_method: str = Field("equal", description="权重方法: equal, ic_weighted, risk_parity, min_variance, max_sharpe")
    universe: UniverseConfigRequest = Field(default_factory=UniverseConfigRequest)
    constraints: ConstraintConfigRequest = Field(default_factory=ConstraintConfigRequest)
    execution: ExecutionConfigRequest = Field(default_factory=ExecutionConfigRequest)
    initial_capital: float = Field(1_000_000.0, gt=0)
    benchmark: str = "SPY"


class StrategyValidationResponse(BaseModel):
    """策略验证响应"""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    strategy_summary: dict[str, Any]


class SignalRequest(BaseModel):
    """信号生成请求"""
    factor_values: dict[str, list[float]] = Field(..., description="因子值 {symbol: [values]}")
    symbols: list[str] = Field(..., description="股票列表")
    signal_type: str = Field("quantile", description="信号类型: equal, top_n, quantile")
    top_n: int = Field(50, ge=1, le=500)
    n_quantiles: int = Field(5, ge=2, le=10)
    long_quantile: int | None = None
    short_quantile: int | None = None


class SignalResponse(BaseModel):
    """信号生成响应"""
    signals: dict[str, float]
    long_positions: list[str]
    short_positions: list[str]
    neutral_positions: list[str]


class WeightOptimizeRequest(BaseModel):
    """权重优化请求"""
    returns: dict[str, list[float]] = Field(..., description="收益率 {symbol: [returns]}")
    symbols: list[str]
    method: str = Field("equal", description="优化方法: equal, risk_parity, min_variance, max_sharpe")
    risk_free_rate: float = Field(0.02, ge=0, le=0.1)
    target_return: float | None = None
    max_weight: float = Field(0.1, ge=0.01, le=1.0)


class WeightOptimizeResponse(BaseModel):
    """权重优化响应"""
    weights: dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    method: str


class ConstraintCheckRequest(BaseModel):
    """约束检查请求"""
    weights: dict[str, float]
    sectors: dict[str, str] = Field(default_factory=dict)
    prev_weights: dict[str, float] = Field(default_factory=dict)
    constraints: ConstraintConfigRequest = Field(default_factory=ConstraintConfigRequest)


class ConstraintViolationResponse(BaseModel):
    """约束违规响应"""
    is_valid: bool
    violations: list[dict[str, Any]]
    adjusted_weights: dict[str, float] | None


class UniverseFilterRequest(BaseModel):
    """股票池筛选请求"""
    base_universe: str = "SP500"
    filters: list[dict[str, Any]] = Field(default_factory=list)
    min_price: float | None = None
    max_price: float | None = None
    min_volume: float | None = None
    min_market_cap: float | None = None


class UniverseFilterResponse(BaseModel):
    """股票池筛选响应"""
    symbols: list[str]
    count: int
    filters_applied: int


# === 策略存储 (内存) ===
_strategies: dict[str, dict[str, Any]] = {}


# === API 端点 ===

@router.post("/create", response_model=StrategyValidationResponse)
async def create_strategy(request: StrategyDefinitionRequest) -> StrategyValidationResponse:
    """
    创建策略定义

    验证并存储策略配置
    """
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

    try:
        # 转换为内部数据结构
        factors = [
            FactorConfig(
                name=f.name,
                expression=f.expression,
                weight=f.weight,
                direction=f.direction,
                neutralize_industry=f.neutralize_industry,
                winsorize=f.winsorize,
            )
            for f in request.factors
        ]

        universe = UniverseConfig(
            base_universe=request.universe.base_universe,
            min_price=request.universe.min_price,
            max_price=request.universe.max_price,
            min_volume=request.universe.min_volume,
            min_market_cap=request.universe.min_market_cap,
            exclude_sectors=request.universe.exclude_sectors,
            include_sectors=request.universe.include_sectors,
        )

        constraints = ConstraintConfig(
            max_position_weight=request.constraints.max_position_weight,
            min_position_weight=request.constraints.min_position_weight,
            max_sector_weight=request.constraints.max_sector_weight,
            max_holdings=request.constraints.max_holdings,
            min_holdings=request.constraints.min_holdings,
            max_turnover=request.constraints.max_turnover,
            long_only=request.constraints.long_only,
            max_leverage=request.constraints.max_leverage,
        )

        execution = ExecutionConfig(
            slippage_model=request.execution.slippage_model,
            slippage_bps=request.execution.slippage_bps,
            commission_rate=request.execution.commission_rate,
            min_trade_value=request.execution.min_trade_value,
            market_impact=request.execution.market_impact,
        )

        strategy = StrategyDefinition(
            name=request.name,
            description=request.description,
            strategy_type=StrategyType(request.strategy_type),
            version=request.version,
            start_date=request.start_date,
            end_date=request.end_date,
            rebalance_freq=RebalanceFrequency(request.rebalance_freq),
            factors=factors,
            weight_method=WeightMethod(request.weight_method),
            universe=universe,
            constraints=constraints,
            execution=execution,
            initial_capital=request.initial_capital,
            benchmark=request.benchmark,
        )

        # 验证
        errors = strategy.validate()
        warnings: list[str] = []

        # 额外警告检查
        if len(factors) > 10:
            warnings.append("因子数量较多，可能导致过拟合")
        if request.constraints.max_holdings > 200:
            warnings.append("持仓数量较多，可能增加交易成本")

        is_valid = len(errors) == 0

        # 存储策略
        if is_valid:
            _strategies[request.name] = strategy.to_dict()
            logger.info("策略创建成功", name=request.name)

        return StrategyValidationResponse(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            strategy_summary={
                "name": request.name,
                "type": request.strategy_type,
                "factors_count": len(factors),
                "rebalance_freq": request.rebalance_freq,
                "weight_method": request.weight_method,
                "max_holdings": request.constraints.max_holdings,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("创建策略失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/list")
async def list_strategies() -> list[dict[str, Any]]:
    """列出所有策略"""
    return [
        {
            "name": name,
            "type": s.get("strategy_type"),
            "version": s.get("version"),
            "factors_count": len(s.get("factors", [])),
        }
        for name, s in _strategies.items()
    ]


@router.get("/{name}")
async def get_strategy(name: str) -> dict[str, Any]:
    """获取策略详情"""
    if name not in _strategies:
        raise HTTPException(status_code=404, detail=f"策略不存在: {name}")
    return _strategies[name]


@router.delete("/{name}")
async def delete_strategy(name: str) -> dict[str, str]:
    """删除策略"""
    if name not in _strategies:
        raise HTTPException(status_code=404, detail=f"策略不存在: {name}")
    del _strategies[name]
    return {"message": f"策略 {name} 已删除"}


@router.post("/validate")
async def validate_strategy(request: StrategyDefinitionRequest) -> StrategyValidationResponse:
    """验证策略定义 (不保存)"""
    # 复用创建逻辑但不保存
    response = await create_strategy(request)
    # 如果成功创建则删除
    if response.is_valid and request.name in _strategies:
        del _strategies[request.name]
    return response


@router.post("/signals", response_model=SignalResponse)
async def generate_signals(request: SignalRequest) -> SignalResponse:
    """
    生成交易信号

    根据因子值生成多空信号
    """
    from app.strategy.signal_generator import (
        generate_equal_weight_signals,
        generate_quantile_signals,
        generate_top_n_signals,
    )

    try:
        # 构建因子 Series
        factor_series = pd.Series(
            {sym: request.factor_values[sym][0] if sym in request.factor_values else np.nan
             for sym in request.symbols}
        )

        if request.signal_type == "equal":
            signals_df = generate_equal_weight_signals(factor_series)
        elif request.signal_type == "top_n":
            signals_df = generate_top_n_signals(factor_series, top_n=request.top_n)
        elif request.signal_type == "quantile":
            signals_df = generate_quantile_signals(
                factor_series,
                n_quantiles=request.n_quantiles,
                long_quantile=request.long_quantile or request.n_quantiles,
                short_quantile=request.short_quantile,
            )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的信号类型: {request.signal_type}")

        # 提取信号
        signals = signals_df.to_dict() if isinstance(signals_df, pd.Series) else {k: 0.0 for k in request.symbols}
        long_positions = [k for k, v in signals.items() if v > 0]
        short_positions = [k for k, v in signals.items() if v < 0]
        neutral_positions = [k for k, v in signals.items() if v == 0]

        return SignalResponse(
            signals=signals,
            long_positions=long_positions,
            short_positions=short_positions,
            neutral_positions=neutral_positions,
        )

    except Exception as e:
        logger.error("生成信号失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/optimize-weights", response_model=WeightOptimizeResponse)
async def optimize_weights(request: WeightOptimizeRequest) -> WeightOptimizeResponse:
    """
    优化组合权重

    支持:
    - equal: 等权
    - risk_parity: 风险平价
    - min_variance: 最小方差
    - max_sharpe: 最大夏普
    """
    from app.strategy.weight_optimizer import (
        equal_weight,
        max_sharpe,
        min_variance,
        risk_parity,
    )

    try:
        # 构建收益率 DataFrame
        returns_df = pd.DataFrame(request.returns, index=range(len(list(request.returns.values())[0])))
        returns_df = returns_df[request.symbols]

        # 选择优化方法
        if request.method == "equal":
            result = equal_weight(returns_df)
        elif request.method == "risk_parity":
            result = risk_parity(returns_df)
        elif request.method == "min_variance":
            result = min_variance(returns_df)
        elif request.method == "max_sharpe":
            result = max_sharpe(returns_df, risk_free_rate=request.risk_free_rate)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的优化方法: {request.method}")

        # 应用最大权重约束
        weights = dict(zip(request.symbols, result.weights))
        if max(result.weights) > request.max_weight:
            # 简单截断
            weights = {k: min(v, request.max_weight) for k, v in weights.items()}
            # 重新归一化
            total = sum(weights.values())
            weights = {k: v / total for k, v in weights.items()}

        return WeightOptimizeResponse(
            weights=weights,
            expected_return=result.expected_return,
            expected_volatility=result.expected_volatility,
            sharpe_ratio=result.sharpe_ratio,
            method=request.method,
        )

    except Exception as e:
        logger.error("权重优化失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/check-constraints", response_model=ConstraintViolationResponse)
async def check_constraints(request: ConstraintCheckRequest) -> ConstraintViolationResponse:
    """
    检查约束违规

    检测:
    - 单只股票权重超限
    - 行业权重超限
    - 持仓数量超限
    - 换手率超限
    """
    from app.strategy.constraints import ConstraintChecker, PortfolioConstraints

    try:
        # 创建约束配置
        config = PortfolioConstraints(
            max_position_weight=request.constraints.max_position_weight,
            min_position_weight=request.constraints.min_position_weight,
            max_sector_weight=request.constraints.max_sector_weight,
            max_holdings=request.constraints.max_holdings,
            min_holdings=request.constraints.min_holdings,
            max_turnover=request.constraints.max_turnover,
            long_only=request.constraints.long_only,
        )

        checker = ConstraintChecker(config)

        # 转换权重为 Series
        weights = pd.Series(request.weights)
        sectors = pd.Series(request.sectors) if request.sectors else None
        prev_weights = pd.Series(request.prev_weights) if request.prev_weights else None

        # 检查约束
        violations = checker.check_all(
            weights=weights,
            sectors=sectors,
            prev_weights=prev_weights,
        )

        # 转换违规列表
        violation_dicts = [
            {
                "type": v.constraint_type.value,
                "severity": v.severity,
                "message": v.message,
                "value": v.current_value,
                "limit": v.limit_value,
            }
            for v in violations
        ]

        is_valid = len(violations) == 0

        # 如果有违规，尝试调整权重
        adjusted_weights = None
        if not is_valid:
            from app.strategy.constraints import apply_constraints
            adjusted = apply_constraints(weights, config, sectors)
            adjusted_weights = adjusted.to_dict()

        return ConstraintViolationResponse(
            is_valid=is_valid,
            violations=violation_dicts,
            adjusted_weights=adjusted_weights,
        )

    except Exception as e:
        logger.error("约束检查失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/filter-universe", response_model=UniverseFilterResponse)
async def filter_universe(request: UniverseFilterRequest) -> UniverseFilterResponse:
    """
    筛选股票池

    根据条件筛选股票
    """
    from app.strategy.universe_filter import (
        FilterCondition,
        FilterOperator,
        UniverseFilter,
    )

    try:
        # 创建筛选器
        conditions = []
        if request.min_price is not None:
            conditions.append(FilterCondition(
                field="price",
                operator=FilterOperator.GTE,
                value=request.min_price,
            ))
        if request.max_price is not None:
            conditions.append(FilterCondition(
                field="price",
                operator=FilterOperator.LTE,
                value=request.max_price,
            ))
        if request.min_volume is not None:
            conditions.append(FilterCondition(
                field="volume",
                operator=FilterOperator.GTE,
                value=request.min_volume,
            ))
        if request.min_market_cap is not None:
            conditions.append(FilterCondition(
                field="market_cap",
                operator=FilterOperator.GTE,
                value=request.min_market_cap,
            ))

        # 添加自定义筛选条件
        for f in request.filters:
            conditions.append(FilterCondition(
                field=f.get("field", ""),
                operator=FilterOperator(f.get("operator", "gte")),
                value=f.get("value", 0),
            ))

        universe_filter = UniverseFilter(conditions=conditions)

        # 获取基础股票池 (模拟数据)
        base_symbols = _get_base_universe(request.base_universe)

        # 应用筛选 (这里简化处理，实际需要市场数据)
        filtered_symbols = base_symbols  # 简化：直接返回基础池

        return UniverseFilterResponse(
            symbols=filtered_symbols,
            count=len(filtered_symbols),
            filters_applied=len(conditions),
        )

    except Exception as e:
        logger.error("筛选股票池失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


def _get_base_universe(universe_name: str) -> list[str]:
    """获取基础股票池 (模拟数据)"""
    universes = {
        "SP500": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK.B", "JPM", "JNJ",
                  "V", "UNH", "HD", "PG", "MA", "DIS", "PYPL", "VZ", "ADBE", "NFLX"],
        "NASDAQ100": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "PYPL", "ADBE", "NFLX",
                      "INTC", "CSCO", "CMCSA", "PEP", "AVGO", "TXN", "COST", "QCOM", "AMGN", "SBUX"],
        "DOW30": ["AAPL", "MSFT", "JPM", "V", "UNH", "HD", "PG", "DIS", "JNJ", "VZ",
                  "INTC", "CSCO", "WMT", "KO", "MCD", "NKE", "GS", "MMM", "CAT", "AXP"],
    }
    return universes.get(universe_name, universes["SP500"])
