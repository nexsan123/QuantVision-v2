"""
风险管理 API 端点

提供:
- VaR 计算
- 因子暴露分析
- 熔断器控制
- 压力测试
- 风险监控
"""

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/risk", tags=["风险管理"])


# === Pydantic 模型 ===

class VaRRequest(BaseModel):
    """VaR 计算请求"""
    returns: list[float] = Field(..., description="收益率序列")
    confidence_level: float = Field(0.95, ge=0.9, le=0.99)
    method: str = Field("historical", description="计算方法: historical, parametric, monte_carlo")
    horizon_days: int = Field(1, ge=1, le=30)
    portfolio_value: float = Field(1.0, gt=0)


class VaRResponse(BaseModel):
    """VaR 计算响应"""
    var: float
    cvar: float
    var_pct: float
    confidence_level: float
    horizon_days: int
    method: str


class StressTestRequest(BaseModel):
    """压力测试请求"""
    holdings: dict[str, float] = Field(..., description="持仓 {symbol: weight}")
    scenario: str = Field("2008_financial_crisis", description="情景名称")
    portfolio_value: float = Field(1000000.0, gt=0)
    asset_betas: dict[str, float] | None = Field(None, description="资产 Beta")
    asset_sectors: dict[str, str] | None = Field(None, description="资产行业")


class StressTestResponse(BaseModel):
    """压力测试响应"""
    scenario_name: str
    portfolio_loss_pct: float
    portfolio_loss_amount: float
    var_stressed: float
    max_drawdown_stressed: float
    recovery_days: int
    market_contribution: float
    sector_contribution: float


class CircuitBreakerStatus(BaseModel):
    """熔断器状态"""
    state: str
    is_tripped: bool
    can_trade: bool
    trigger_reason: str | None
    triggered_at: str | None
    consecutive_losses: int
    daily_pnl: float


class RiskMetricsUpdate(BaseModel):
    """风险指标更新"""
    daily_pnl: float | None = None
    drawdown: float | None = None
    volatility: float | None = None
    var: float | None = None
    max_position_pct: float | None = None


class RiskAlertResponse(BaseModel):
    """风险警报响应"""
    timestamp: str
    level: str
    metric_type: str
    message: str
    current_value: float
    threshold: float


# === 全局状态 ===
# 实际应该使用依赖注入，这里简化处理

_circuit_breaker = None
_risk_monitor = None


def _get_circuit_breaker():
    """获取熔断器实例"""
    global _circuit_breaker
    if _circuit_breaker is None:
        from app.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
        _circuit_breaker = CircuitBreaker(CircuitBreakerConfig())
    return _circuit_breaker


def _get_risk_monitor():
    """获取风险监控器实例"""
    global _risk_monitor
    if _risk_monitor is None:
        from app.risk.monitor import RiskMonitor
        _risk_monitor = RiskMonitor()
    return _risk_monitor


# === API 端点 ===

@router.post("/var", response_model=VaRResponse)
async def calculate_var(request: VaRRequest) -> VaRResponse:
    """
    计算 VaR

    支持方法:
    - historical: 历史模拟法
    - parametric: 参数法 (正态分布)
    - monte_carlo: 蒙特卡洛模拟
    - cornish_fisher: Cornish-Fisher 展开
    - ewma: 指数加权移动平均
    """
    from app.risk.var_calculator import VaRCalculator, VaRMethod

    try:
        method_map = {
            "historical": VaRMethod.HISTORICAL,
            "parametric": VaRMethod.PARAMETRIC,
            "monte_carlo": VaRMethod.MONTE_CARLO,
            "cornish_fisher": VaRMethod.CORNISH_FISHER,
            "ewma": VaRMethod.EWMA,
        }

        if request.method not in method_map:
            raise HTTPException(status_code=400, detail=f"不支持的方法: {request.method}")

        calculator = VaRCalculator(
            confidence_level=request.confidence_level,
            horizon_days=request.horizon_days,
        )

        returns = pd.Series(request.returns)
        result = calculator.calculate(
            returns=returns,
            method=method_map[request.method],
            portfolio_value=request.portfolio_value,
        )

        return VaRResponse(
            var=result.var,
            cvar=result.cvar,
            var_pct=result.var_pct,
            confidence_level=result.confidence_level,
            horizon_days=result.horizon_days,
            method=request.method,
        )

    except Exception as e:
        logger.error("VaR 计算失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stress-test", response_model=StressTestResponse)
async def run_stress_test(request: StressTestRequest) -> StressTestResponse:
    """
    运行压力测试

    可用情景:
    - 2008_financial_crisis: 2008金融危机
    - 2020_covid_crash: 2020新冠崩盘
    - 2022_rate_hike: 2022加息周期
    - flash_crash: 闪崩
    - bond_crisis: 债市危机
    """
    from app.risk.stress_test import StressTester, HISTORICAL_SCENARIOS

    try:
        if request.scenario not in HISTORICAL_SCENARIOS:
            available = list(HISTORICAL_SCENARIOS.keys())
            raise HTTPException(
                status_code=400,
                detail=f"未知情景: {request.scenario}. 可用: {available}",
            )

        tester = StressTester()
        result = tester.run_scenario(
            holdings=request.holdings,
            portfolio_value=request.portfolio_value,
            scenario=request.scenario,
            asset_betas=request.asset_betas,
            asset_sectors=request.asset_sectors,
        )

        return StressTestResponse(
            scenario_name=result.scenario.name,
            portfolio_loss_pct=result.portfolio_loss,
            portfolio_loss_amount=result.portfolio_loss_amount,
            var_stressed=result.var_stressed,
            max_drawdown_stressed=result.max_drawdown_stressed,
            recovery_days=result.recovery_days,
            market_contribution=result.market_contribution,
            sector_contribution=result.sector_contribution,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("压力测试失败", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stress-test/scenarios")
async def list_stress_scenarios() -> list[dict[str, Any]]:
    """列出可用的压力测试情景"""
    from app.risk.stress_test import HISTORICAL_SCENARIOS

    return [
        {
            "name": key,
            "display_name": scenario.name,
            "description": scenario.description,
            "market_shock": scenario.market_shock,
            "volatility_shock": scenario.volatility_shock,
        }
        for key, scenario in HISTORICAL_SCENARIOS.items()
    ]


@router.get("/circuit-breaker", response_model=CircuitBreakerStatus)
async def get_circuit_breaker_status() -> CircuitBreakerStatus:
    """获取熔断器状态"""
    breaker = _get_circuit_breaker()
    status = breaker.get_status()

    return CircuitBreakerStatus(
        state=status["state"],
        is_tripped=breaker.is_tripped,
        can_trade=status["can_trade"],
        trigger_reason=status["trigger_reason"],
        triggered_at=status["triggered_at"],
        consecutive_losses=status["consecutive_losses"],
        daily_pnl=status["daily_pnl"],
    )


@router.post("/circuit-breaker/update")
async def update_circuit_breaker(metrics: RiskMetricsUpdate) -> CircuitBreakerStatus:
    """更新熔断器风险指标"""
    breaker = _get_circuit_breaker()

    breaker.update_metrics(
        daily_pnl=metrics.daily_pnl,
        drawdown=metrics.drawdown,
        volatility=metrics.volatility,
        var=metrics.var,
        max_position_pct=metrics.max_position_pct,
    )

    return await get_circuit_breaker_status()


@router.post("/circuit-breaker/trigger")
async def trigger_circuit_breaker(reason: str = "手动触发") -> CircuitBreakerStatus:
    """手动触发熔断"""
    breaker = _get_circuit_breaker()
    breaker.manual_trigger(reason)

    return await get_circuit_breaker_status()


@router.post("/circuit-breaker/reset")
async def reset_circuit_breaker() -> CircuitBreakerStatus:
    """重置熔断器"""
    breaker = _get_circuit_breaker()
    breaker.manual_reset()

    return await get_circuit_breaker_status()


@router.get("/monitor/status")
async def get_risk_monitor_status() -> dict[str, Any]:
    """获取风险监控状态"""
    monitor = _get_risk_monitor()
    return monitor.get_status()


@router.get("/monitor/alerts", response_model=list[RiskAlertResponse])
async def get_risk_alerts(
    level: str | None = Query(None, description="筛选级别: info, warning, critical, emergency"),
    since_hours: float = Query(24, ge=1, le=168),
) -> list[RiskAlertResponse]:
    """获取风险警报"""
    from app.risk.monitor import AlertLevel

    monitor = _get_risk_monitor()

    alert_level = None
    if level:
        try:
            alert_level = AlertLevel(level)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效级别: {level}")

    alerts = monitor.get_active_alerts(level=alert_level, since_hours=since_hours)

    return [
        RiskAlertResponse(
            timestamp=a.timestamp.isoformat(),
            level=a.level.value,
            metric_type=a.metric_type.value,
            message=a.message,
            current_value=a.current_value,
            threshold=a.threshold,
        )
        for a in alerts
    ]


@router.get("/monitor/score")
async def get_risk_score() -> dict[str, Any]:
    """获取综合风险评分"""
    monitor = _get_risk_monitor()

    score = monitor.calculate_risk_score()
    status = monitor.get_status()

    return {
        "risk_score": score,
        "risk_level": "high" if score > 60 else "medium" if score > 30 else "low",
        "active_alerts": status["active_alerts_count"],
        "current_drawdown": status["current_drawdown"],
        "current_volatility": status["current_volatility"],
    }
