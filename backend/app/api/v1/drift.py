"""
策略漂移监控 API
PRD 4.8 实盘vs回测差异监控
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Optional

from app.services.drift_service import drift_service
from app.schemas.drift import (
    StrategyDriftReport,
    DriftCheckRequest,
    DriftCheckResponse,
    DriftReportListResponse,
    DriftThresholds,
    DriftAcknowledgeRequest,
)

router = APIRouter(prefix="/drift", tags=["漂移监控"])


@router.post("/check", response_model=DriftCheckResponse)
async def check_strategy_drift(request: DriftCheckRequest):
    """
    立即检查策略漂移

    对比策略的回测数据和实盘/模拟盘数据，生成漂移报告

    - **strategy_id**: 策略ID
    - **deployment_id**: 部署ID
    - **period_days**: 比较周期 (天)，默认30天
    """
    try:
        report = await drift_service.check_drift(
            strategy_id=request.strategy_id,
            deployment_id=request.deployment_id,
            period_days=request.period_days,
        )
        return DriftCheckResponse(
            success=True,
            message="漂移检查完成",
            report=report,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"漂移检查失败: {str(e)}")


@router.get("/reports/{strategy_id}", response_model=DriftReportListResponse)
async def get_drift_reports(
    strategy_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="返回数量限制"),
):
    """
    获取策略的漂移报告历史

    返回指定策略的历史漂移报告列表，按时间倒序排列
    """
    reports = await drift_service.get_drift_history(strategy_id, limit)
    return DriftReportListResponse(
        total=len(reports),
        reports=reports,
    )


@router.get("/reports/{strategy_id}/latest", response_model=Optional[StrategyDriftReport])
async def get_latest_drift_report(strategy_id: str):
    """
    获取策略最新的漂移报告

    返回指定策略最近一次的漂移检查报告
    """
    report = await drift_service.get_latest_report(strategy_id)
    return report


@router.get("/report/{report_id}", response_model=StrategyDriftReport)
async def get_drift_report_by_id(report_id: str):
    """
    根据报告ID获取漂移报告

    返回指定ID的漂移报告详情
    """
    report = await drift_service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report


@router.post("/reports/{report_id}/acknowledge")
async def acknowledge_drift_report(
    report_id: str,
    request: Optional[DriftAcknowledgeRequest] = None,
):
    """
    确认漂移报告

    标记用户已阅读并了解该漂移报告，表示已采取相应措施

    - **report_id**: 报告ID
    - **notes**: 可选的确认备注
    """
    success = await drift_service.acknowledge_report(report_id, user_id="demo")
    if not success:
        raise HTTPException(status_code=404, detail="报告不存在")

    return {
        "success": True,
        "message": "报告已确认",
        "report_id": report_id,
    }


@router.get("/thresholds", response_model=DriftThresholds)
async def get_drift_thresholds():
    """
    获取漂移监控阈值配置

    返回当前使用的漂移预警阈值配置 (PRD 附录C)

    阈值说明:
    - warning: 黄色预警阈值
    - critical: 红色严重阈值
    """
    return DriftThresholds()


@router.post("/schedule-check")
async def schedule_drift_check(
    strategy_id: str,
    deployment_id: str,
    background_tasks: BackgroundTasks,
):
    """
    安排后台漂移检查

    将漂移检查任务添加到后台队列执行，适用于不需要立即返回结果的场景
    """

    async def run_check():
        await drift_service.check_drift(
            strategy_id=strategy_id,
            deployment_id=deployment_id,
        )

    background_tasks.add_task(run_check)

    return {
        "success": True,
        "message": "漂移检查已安排",
        "strategy_id": strategy_id,
        "deployment_id": deployment_id,
    }


@router.get("/summary/{strategy_id}")
async def get_drift_summary(strategy_id: str):
    """
    获取策略漂移摘要

    返回策略的漂移状态概要信息，用于在策略卡片等处显示
    """
    report = await drift_service.get_latest_report(strategy_id)

    if not report:
        return {
            "has_report": False,
            "strategy_id": strategy_id,
            "overall_severity": "normal",
            "drift_score": 0,
            "should_pause": False,
            "is_acknowledged": True,
        }

    return {
        "has_report": True,
        "strategy_id": strategy_id,
        "report_id": report.report_id,
        "overall_severity": report.overall_severity.value,
        "drift_score": report.drift_score,
        "should_pause": report.should_pause,
        "is_acknowledged": report.is_acknowledged,
        "created_at": report.created_at.isoformat(),
        "days_compared": report.days_compared,
    }
