"""
Phase 10: \u98ce\u9669\u7cfb\u7edf\u5347\u7ea7 - \u9ad8\u7ea7\u98ce\u9669\u7ba1\u7406 API

\u63d0\u4f9b:
- \u98ce\u9669\u56e0\u5b50\u6a21\u578b (Barra \u7b80\u5316\u7248)
- \u98ce\u9669\u5206\u89e3
- \u589e\u5f3a\u538b\u529b\u6d4b\u8bd5
- \u5b9e\u65f6\u98ce\u9669\u76d1\u63a7\u4eea\u8868\u76d8
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
import structlog

from app.schemas.risk_factor import (
    # Request/Response models
    RiskDecompositionRequest,
    RiskDecompositionResult,
    StressTestRequest,
    StressTestResult,
    StressTestBatchRequest,
    StressTestBatchResponse,
    StressScenario,
    ScenarioListResponse,
    RiskMonitorStatus,
    RiskLimits,
    RiskLimitsUpdateRequest,
    RiskDashboardResponse,
    # Enums
    ScenarioType,
    AlertLevel,
    RiskLevel,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/risk/advanced", tags=["\u98ce\u9669\u7cfb\u7edf\u5347\u7ea7"])


# === \u5168\u5c40\u670d\u52a1\u5b9e\u4f8b ===

_risk_factor_model = None
_stress_test_engine = None
_risk_monitor_service = None


def _get_risk_factor_model():
    """\u83b7\u53d6\u98ce\u9669\u56e0\u5b50\u6a21\u578b\u5b9e\u4f8b"""
    global _risk_factor_model
    if _risk_factor_model is None:
        from app.services.risk_factor_model import RiskFactorModel
        _risk_factor_model = RiskFactorModel()
    return _risk_factor_model


def _get_stress_test_engine():
    """\u83b7\u53d6\u538b\u529b\u6d4b\u8bd5\u5f15\u64ce\u5b9e\u4f8b"""
    global _stress_test_engine
    if _stress_test_engine is None:
        from app.services.stress_test_engine import StressTestEngine
        _stress_test_engine = StressTestEngine()
    return _stress_test_engine


def _get_risk_monitor_service():
    """\u83b7\u53d6\u98ce\u9669\u76d1\u63a7\u670d\u52a1\u5b9e\u4f8b"""
    global _risk_monitor_service
    if _risk_monitor_service is None:
        from app.services.risk_factor_model import RiskMonitorService
        _risk_monitor_service = RiskMonitorService()
    return _risk_monitor_service


# === \u98ce\u9669\u5206\u89e3 API ===

@router.post("/decomposition", response_model=RiskDecompositionResult)
async def decompose_risk(request: RiskDecompositionRequest) -> RiskDecompositionResult:
    """
    \u98ce\u9669\u5206\u89e3\u5206\u6790

    \u5c06\u7ec4\u5408\u98ce\u9669\u5206\u89e3\u4e3a:
    - \u5e02\u573a\u98ce\u9669 (Beta)
    - \u98ce\u683c\u98ce\u9669 (\u89c4\u6a21\u3001\u4ef7\u503c\u3001\u52a8\u91cf\u7b49)
    - \u884c\u4e1a\u98ce\u9669 (GICS\u4e00\u7ea7\u884c\u4e1a)
    - \u7279\u8d28\u98ce\u9669 (\u4e2a\u80a1\u7279\u6709)
    """
    try:
        model = _get_risk_factor_model()

        result = await model.decompose_risk(
            holdings=request.holdings,
            benchmark=request.benchmark,
            lookback_days=request.lookback_days
        )

        return result

    except Exception as e:
        logger.error("\u98ce\u9669\u5206\u89e3\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=f"\u98ce\u9669\u5206\u89e3\u5931\u8d25: {str(e)}")


@router.post("/factor-exposures")
async def get_factor_exposures(
    holdings: dict[str, float],
    benchmark: str = "SPY",
) -> dict[str, Any]:
    """
    \u83b7\u53d6\u56e0\u5b50\u66b4\u9732

    \u8fd4\u56de\u7ec4\u5408\u5bf9\u5404\u98ce\u683c\u56e0\u5b50\u548c\u884c\u4e1a\u56e0\u5b50\u7684\u66b4\u9732
    """
    try:
        model = _get_risk_factor_model()

        exposures = await model.calculate_factor_exposures(
            holdings=holdings,
            benchmark=benchmark
        )

        return {
            "market_beta": exposures.get("market", 1.0),
            "style_exposures": exposures.get("style", {}),
            "industry_exposures": exposures.get("industry", {}),
            "significant_factors": [
                k for k, v in exposures.get("style", {}).items()
                if abs(v) > 0.3
            ]
        }

    except Exception as e:
        logger.error("\u56e0\u5b50\u66b4\u9732\u8ba1\u7b97\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marginal-risk")
async def calculate_marginal_risk(
    holdings: dict[str, float],
    new_position: dict[str, float],
) -> dict[str, Any]:
    """
    \u8ba1\u7b97\u8fb9\u9645\u98ce\u9669

    \u8bc4\u4f30\u65b0\u589e\u6301\u4ed3\u5bf9\u7ec4\u5408\u98ce\u9669\u7684\u5f71\u54cd
    """
    try:
        model = _get_risk_factor_model()

        result = await model.calculate_marginal_risk(
            current_holdings=holdings,
            new_position=new_position
        )

        return result

    except Exception as e:
        logger.error("\u8fb9\u9645\u98ce\u9669\u8ba1\u7b97\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === \u538b\u529b\u6d4b\u8bd5 API ===

@router.get("/scenarios", response_model=ScenarioListResponse)
async def list_scenarios(
    scenario_type: ScenarioType | None = Query(None, description="\u60c5\u666f\u7c7b\u578b\u7b5b\u9009"),
) -> ScenarioListResponse:
    """
    \u83b7\u53d6\u53ef\u7528\u7684\u538b\u529b\u6d4b\u8bd5\u60c5\u666f\u5217\u8868

    \u60c5\u666f\u7c7b\u578b:
    - historical: \u5386\u53f2\u60c5\u666f (2008\u91d1\u878d\u5371\u673a\u3001COVID\u7b49)
    - hypothetical: \u5047\u8bbe\u60c5\u666f (\u5e02\u573a\u4e0b\u8dcc20%\u7b49)
    - custom: \u81ea\u5b9a\u4e49\u60c5\u666f
    """
    try:
        engine = _get_stress_test_engine()
        scenarios = engine.get_available_scenarios(scenario_type)

        return ScenarioListResponse(
            scenarios=scenarios,
            total=len(scenarios)
        )

    except Exception as e:
        logger.error("\u83b7\u53d6\u60c5\u666f\u5217\u8868\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stress-test/run", response_model=StressTestResult)
async def run_stress_test(request: StressTestRequest) -> StressTestResult:
    """
    \u8fd0\u884c\u5355\u4e2a\u538b\u529b\u6d4b\u8bd5\u60c5\u666f

    \u53ef\u4ee5\u4f7f\u7528\u9884\u7f6e\u60c5\u666f(scenario_id)\u6216\u81ea\u5b9a\u4e49\u60c5\u666f(custom_scenario)
    """
    try:
        engine = _get_stress_test_engine()

        if request.custom_scenario:
            # \u81ea\u5b9a\u4e49\u60c5\u666f
            result = await engine.run_custom_scenario(
                holdings=request.holdings,
                portfolio_value=request.portfolio_value,
                scenario=request.custom_scenario,
                asset_betas=request.asset_betas,
                asset_sectors=request.asset_sectors
            )
        elif request.scenario_id:
            # \u9884\u7f6e\u60c5\u666f
            result = await engine.run_scenario(
                holdings=request.holdings,
                portfolio_value=request.portfolio_value,
                scenario_id=request.scenario_id,
                asset_betas=request.asset_betas,
                asset_sectors=request.asset_sectors
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="\u5fc5\u987b\u63d0\u4f9b scenario_id \u6216 custom_scenario"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("\u538b\u529b\u6d4b\u8bd5\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stress-test/batch", response_model=StressTestBatchResponse)
async def run_batch_stress_test(request: StressTestBatchRequest) -> StressTestBatchResponse:
    """
    \u6279\u91cf\u8fd0\u884c\u538b\u529b\u6d4b\u8bd5

    \u5982\u679c scenario_ids \u4e3a\u7a7a\uff0c\u5219\u8fd0\u884c\u6240\u6709\u53ef\u7528\u60c5\u666f
    """
    try:
        engine = _get_stress_test_engine()

        results = await engine.run_all_scenarios(
            holdings=request.holdings,
            portfolio_value=request.portfolio_value,
            scenario_ids=request.scenario_ids if request.scenario_ids else None,
            asset_betas=request.asset_betas,
            asset_sectors=request.asset_sectors
        )

        # \u751f\u6210\u6458\u8981
        if results:
            worst_scenario = max(results, key=lambda r: r.portfolio_impact.expected_loss_percent)
            best_scenario = min(results, key=lambda r: r.portfolio_impact.expected_loss_percent)
            avg_loss = sum(r.portfolio_impact.expected_loss_percent for r in results) / len(results)

            summary = {
                "total_scenarios": len(results),
                "worst_case": {
                    "scenario": worst_scenario.scenario.name,
                    "loss_percent": worst_scenario.portfolio_impact.expected_loss_percent,
                },
                "best_case": {
                    "scenario": best_scenario.scenario.name,
                    "loss_percent": best_scenario.portfolio_impact.expected_loss_percent,
                },
                "average_loss_percent": avg_loss,
                "liquidation_risk_count": sum(1 for r in results if r.portfolio_impact.liquidation_risk),
            }
        else:
            summary = {"total_scenarios": 0}

        return StressTestBatchResponse(
            results=results,
            summary=summary
        )

    except Exception as e:
        logger.error("\u6279\u91cf\u538b\u529b\u6d4b\u8bd5\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stress-test/reverse")
async def run_reverse_stress_test(
    holdings: dict[str, float],
    portfolio_value: float = 1000000.0,
    target_loss_percent: float = 0.20,
) -> dict[str, Any]:
    """
    \u53cd\u5411\u538b\u529b\u6d4b\u8bd5

    \u627e\u51fa\u4f1a\u5bfc\u81f4\u6307\u5b9a\u4e8f\u635f\u6c34\u5e73\u7684\u5e02\u573a\u60c5\u666f
    """
    try:
        engine = _get_stress_test_engine()

        result = await engine.reverse_stress_test(
            holdings=holdings,
            portfolio_value=portfolio_value,
            target_loss_percent=target_loss_percent
        )

        return result

    except Exception as e:
        logger.error("\u53cd\u5411\u538b\u529b\u6d4b\u8bd5\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === \u5b9e\u65f6\u76d1\u63a7 API ===

@router.get("/monitor/status", response_model=RiskMonitorStatus)
async def get_monitor_status(
    portfolio_id: str | None = Query(None, description="\u7ec4\u5408ID"),
) -> RiskMonitorStatus:
    """
    \u83b7\u53d6\u5b9e\u65f6\u98ce\u9669\u76d1\u63a7\u72b6\u6001

    \u5305\u62ec:
    - \u5f53\u524d\u98ce\u9669\u6307\u6807 (\u56de\u64a4\u3001VaR\u3001\u6ce2\u52a8\u7387)
    - \u56e0\u5b50\u66b4\u9732\u72b6\u6001
    - \u6d3b\u8dc3\u8b66\u62a5
    - \u7efc\u5408\u98ce\u9669\u8bc4\u5206
    """
    try:
        monitor = _get_risk_monitor_service()
        status = await monitor.get_status(portfolio_id)
        return status

    except Exception as e:
        logger.error("\u83b7\u53d6\u76d1\u63a7\u72b6\u6001\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/dashboard", response_model=RiskDashboardResponse)
async def get_risk_dashboard(
    portfolio_id: str | None = Query(None),
    holdings: str | None = Query(None, description="JSON\u683c\u5f0f\u7684\u6301\u4ed3"),
) -> RiskDashboardResponse:
    """
    \u83b7\u53d6\u98ce\u9669\u4eea\u8868\u76d8\u6570\u636e

    \u5408\u5e76\u8fd4\u56de:
    - \u76d1\u63a7\u72b6\u6001
    - \u98ce\u9669\u5206\u89e3\u7ed3\u679c
    - \u6700\u8fd1\u538b\u529b\u6d4b\u8bd5\u7ed3\u679c
    """
    import json

    try:
        monitor = _get_risk_monitor_service()
        model = _get_risk_factor_model()
        engine = _get_stress_test_engine()

        # \u83b7\u53d6\u76d1\u63a7\u72b6\u6001
        monitor_status = await monitor.get_status(portfolio_id)

        # \u89e3\u6790\u6301\u4ed3
        parsed_holdings = {}
        if holdings:
            try:
                parsed_holdings = json.loads(holdings)
            except json.JSONDecodeError:
                pass

        # \u98ce\u9669\u5206\u89e3
        risk_decomposition = None
        if parsed_holdings:
            try:
                risk_decomposition = await model.decompose_risk(
                    holdings=parsed_holdings,
                    benchmark="SPY",
                    lookback_days=252
                )
            except Exception as e:
                logger.warning("\u98ce\u9669\u5206\u89e3\u5931\u8d25", error=str(e))

        # \u6700\u8fd1\u538b\u529b\u6d4b\u8bd5 (\u53ea\u8fd0\u884c\u51e0\u4e2a\u5173\u952e\u60c5\u666f)
        recent_stress_tests = []
        if parsed_holdings:
            try:
                key_scenarios = ["2008_financial_crisis", "2020_covid", "market_crash_20"]
                batch_result = await engine.run_all_scenarios(
                    holdings=parsed_holdings,
                    portfolio_value=1000000.0,
                    scenario_ids=key_scenarios
                )
                recent_stress_tests = batch_result[:3] if batch_result else []
            except Exception as e:
                logger.warning("\u538b\u529b\u6d4b\u8bd5\u5931\u8d25", error=str(e))

        return RiskDashboardResponse(
            monitor_status=monitor_status,
            risk_decomposition=risk_decomposition,
            recent_stress_tests=recent_stress_tests
        )

    except Exception as e:
        logger.error("\u83b7\u53d6\u98ce\u9669\u4eea\u8868\u76d8\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limits", response_model=RiskLimits)
async def get_risk_limits(
    portfolio_id: str | None = Query(None),
) -> RiskLimits:
    """
    \u83b7\u53d6\u98ce\u9669\u9650\u5236\u914d\u7f6e
    """
    try:
        monitor = _get_risk_monitor_service()
        limits = await monitor.get_limits(portfolio_id)
        return limits

    except Exception as e:
        logger.error("\u83b7\u53d6\u98ce\u9669\u9650\u5236\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/limits", response_model=RiskLimits)
async def update_risk_limits(
    request: RiskLimitsUpdateRequest,
    portfolio_id: str | None = Query(None),
) -> RiskLimits:
    """
    \u66f4\u65b0\u98ce\u9669\u9650\u5236\u914d\u7f6e
    """
    try:
        monitor = _get_risk_monitor_service()
        updated = await monitor.update_limits(portfolio_id, request.limits)
        return updated

    except Exception as e:
        logger.error("\u66f4\u65b0\u98ce\u9669\u9650\u5236\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/acknowledge/{alert_id}")
async def acknowledge_alert(alert_id: str) -> dict[str, str]:
    """
    \u786e\u8ba4\u98ce\u9669\u8b66\u62a5
    """
    try:
        monitor = _get_risk_monitor_service()
        await monitor.acknowledge_alert(alert_id)
        return {"status": "acknowledged", "alert_id": alert_id}

    except Exception as e:
        logger.error("\u786e\u8ba4\u8b66\u62a5\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/history")
async def get_alert_history(
    portfolio_id: str | None = Query(None),
    level: AlertLevel | None = Query(None),
    days: int = Query(7, ge=1, le=90),
) -> list[dict[str, Any]]:
    """
    \u83b7\u53d6\u8b66\u62a5\u5386\u53f2
    """
    try:
        monitor = _get_risk_monitor_service()
        alerts = await monitor.get_alert_history(
            portfolio_id=portfolio_id,
            level=level,
            days=days
        )
        return alerts

    except Exception as e:
        logger.error("\u83b7\u53d6\u8b66\u62a5\u5386\u53f2\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# === \u98ce\u9669\u62a5\u544a API ===

@router.post("/report/generate")
async def generate_risk_report(
    holdings: dict[str, float],
    portfolio_value: float = 1000000.0,
    report_type: str = "comprehensive",
) -> dict[str, Any]:
    """
    \u751f\u6210\u98ce\u9669\u62a5\u544a

    \u62a5\u544a\u7c7b\u578b:
    - comprehensive: \u7efc\u5408\u62a5\u544a
    - factor: \u56e0\u5b50\u5206\u6790\u62a5\u544a
    - stress: \u538b\u529b\u6d4b\u8bd5\u62a5\u544a
    """
    try:
        model = _get_risk_factor_model()
        engine = _get_stress_test_engine()

        report = {
            "generated_at": datetime.now().isoformat(),
            "portfolio_value": portfolio_value,
            "holdings_count": len(holdings),
            "report_type": report_type,
        }

        # \u98ce\u9669\u5206\u89e3
        decomposition = await model.decompose_risk(
            holdings=holdings,
            benchmark="SPY",
            lookback_days=252
        )
        report["risk_decomposition"] = {
            "total_risk": decomposition.total_risk,
            "risk_contributions": decomposition.risk_contributions.model_dump(),
            "factor_exposures": decomposition.factor_exposures.model_dump(),
            "r_squared": decomposition.r_squared,
        }

        # \u538b\u529b\u6d4b\u8bd5
        if report_type in ["comprehensive", "stress"]:
            stress_results = await engine.run_all_scenarios(
                holdings=holdings,
                portfolio_value=portfolio_value
            )
            report["stress_tests"] = {
                "scenarios_tested": len(stress_results),
                "worst_case": {
                    "scenario": max(stress_results, key=lambda r: r.portfolio_impact.expected_loss_percent).scenario.name,
                    "loss_percent": max(r.portfolio_impact.expected_loss_percent for r in stress_results),
                },
                "average_loss": sum(r.portfolio_impact.expected_loss_percent for r in stress_results) / len(stress_results) if stress_results else 0,
            }

        # \u98ce\u9669\u8bc4\u7ea7
        total_risk = decomposition.total_risk
        if total_risk > 0.30:
            risk_rating = "HIGH"
        elif total_risk > 0.20:
            risk_rating = "MEDIUM"
        else:
            risk_rating = "LOW"

        report["risk_rating"] = risk_rating
        report["recommendations"] = _generate_recommendations(decomposition, stress_results if report_type != "factor" else [])

        return report

    except Exception as e:
        logger.error("\u751f\u6210\u98ce\u9669\u62a5\u544a\u5931\u8d25", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def _generate_recommendations(
    decomposition: RiskDecompositionResult,
    stress_results: list[StressTestResult]
) -> list[str]:
    """\u751f\u6210\u98ce\u9669\u7ba1\u7406\u5efa\u8bae"""
    recommendations = []

    # \u57fa\u4e8e\u98ce\u9669\u5206\u89e3
    if decomposition.risk_contributions.specific > 40:
        recommendations.append("\u7279\u8d28\u98ce\u9669\u5360\u6bd4\u8fc7\u9ad8\uff0c\u5efa\u8bae\u589e\u52a0\u6301\u4ed3\u5206\u6563\u5ea6")

    if decomposition.risk_contributions.industry > 30:
        recommendations.append("\u884c\u4e1a\u96c6\u4e2d\u5ea6\u8fc7\u9ad8\uff0c\u5efa\u8bae\u5206\u6563\u884c\u4e1a\u914d\u7f6e")

    if decomposition.factor_exposures.market > 1.3:
        recommendations.append("\u5e02\u573a Beta \u8f83\u9ad8\uff0c\u5728\u5e02\u573a\u4e0b\u8dcc\u65f6\u98ce\u9669\u653e\u5927")

    # \u57fa\u4e8e\u98ce\u683c\u56e0\u5b50
    style = decomposition.factor_exposures.style
    if hasattr(style, 'momentum') and style.momentum > 0.5:
        recommendations.append("\u52a8\u91cf\u56e0\u5b50\u66b4\u9732\u8f83\u9ad8\uff0c\u6ce8\u610f\u52a8\u91cf\u53cd\u8f6c\u98ce\u9669")
    if hasattr(style, 'leverage') and style.leverage > 0.5:
        recommendations.append("\u6760\u6746\u56e0\u5b50\u66b4\u9732\u8f83\u9ad8\uff0c\u5229\u7387\u4e0a\u5347\u65f6\u98ce\u9669\u589e\u52a0")

    # \u57fa\u4e8e\u538b\u529b\u6d4b\u8bd5
    for result in stress_results:
        if result.portfolio_impact.liquidation_risk:
            recommendations.append(
                f"\u5728 {result.scenario.name} \u60c5\u666f\u4e0b\u6709\u5f3a\u5e73\u98ce\u9669\uff0c\u5efa\u8bae\u964d\u4f4e\u6760\u6746"
            )
            break

    if not recommendations:
        recommendations.append("\u7ec4\u5408\u98ce\u9669\u72b6\u51b5\u826f\u597d\uff0c\u7ee7\u7eed\u4fdd\u6301\u5f53\u524d\u914d\u7f6e")

    return recommendations
