"""
交易归因 API
PRD 4.5 交易归因系统
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import date
from typing import Optional

from app.schemas.trade_attribution import (
    TradeRecord,
    AttributionReport,
    AIDiagnosis,
    TradeListResponse,
    AttributionListResponse,
    GenerateAttributionRequest,
)
from app.services.trade_attribution_service import trade_attribution_service

router = APIRouter(prefix="/trade-attribution", tags=["交易归因"])


@router.get("/trades", response_model=TradeListResponse)
async def get_trades(
    strategy_id: Optional[str] = Query(None, description="策略ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    获取交易记录列表

    - 支持按策略ID筛选
    - 分页查询
    """
    trades = await trade_attribution_service.get_trades(
        strategy_id=strategy_id,
        limit=limit,
        offset=offset,
    )
    total = await trade_attribution_service.get_trade_count(strategy_id) if strategy_id else len(trades)
    return TradeListResponse(total=total, trades=trades)


@router.get("/trades/{trade_id}", response_model=TradeRecord)
async def get_trade_detail(trade_id: str):
    """
    获取单个交易记录详情

    包含:
    - 交易基本信息
    - 入场时因子快照
    - 入场时市场环境快照
    """
    trade = await trade_attribution_service.get_trade_by_id(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="交易记录不存在")
    return trade


@router.post("/reports/generate", response_model=AttributionReport)
async def generate_attribution_report(request: GenerateAttributionRequest):
    """
    生成归因报告

    - 分析指定时间范围内的交易
    - 计算因子归因、市场归因、Alpha归因
    - 识别交易模式
    - 自动生成AI诊断
    """
    report = await trade_attribution_service.generate_attribution(
        strategy_id=request.strategy_id,
        start_date=request.start_date,
        end_date=request.end_date,
        trigger_reason="手动触发" if request.force else "定期生成",
    )
    return report


@router.get("/reports", response_model=AttributionListResponse)
async def get_attribution_reports(
    strategy_id: str = Query(..., description="策略ID"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    获取策略的归因报告列表
    """
    reports = await trade_attribution_service.get_reports(
        strategy_id=strategy_id,
        limit=limit,
    )
    return AttributionListResponse(total=len(reports), reports=reports)


@router.get("/reports/{report_id}/diagnosis", response_model=AIDiagnosis)
async def get_ai_diagnosis(report_id: str):
    """
    获取归因报告的AI诊断

    包含:
    - 诊断摘要
    - 优势分析
    - 劣势分析
    - 改进建议
    - 风险提示
    """
    diagnosis = await trade_attribution_service.get_diagnosis(report_id)
    if not diagnosis:
        raise HTTPException(status_code=404, detail="AI诊断不存在")
    return diagnosis


@router.get("/strategies/{strategy_id}/summary")
async def get_strategy_attribution_summary(strategy_id: str):
    """
    获取策略归因摘要

    快速概览:
    - 最近交易统计
    - 整体胜率和盈亏比
    - 主要贡献因子
    """
    trades = await trade_attribution_service.get_trades(
        strategy_id=strategy_id,
        limit=100,
    )

    if not trades:
        return {
            "strategy_id": strategy_id,
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "top_factors": [],
            "has_reports": False,
        }

    # 计算统计
    from app.schemas.trade_attribution import TradeOutcome

    total = len(trades)
    wins = sum(1 for t in trades if t.outcome == TradeOutcome.WIN)
    win_rate = wins / total if total > 0 else 0

    wins_pnl = [t.pnl for t in trades if t.pnl and t.pnl > 0]
    losses_pnl = [abs(t.pnl) for t in trades if t.pnl and t.pnl < 0]
    profit_factor = sum(wins_pnl) / sum(losses_pnl) if losses_pnl and sum(losses_pnl) > 0 else 0

    # 收集因子贡献
    factor_contributions: dict[str, float] = {}
    for trade in trades:
        for snapshot in trade.factor_snapshot:
            if snapshot.factor_name not in factor_contributions:
                factor_contributions[snapshot.factor_name] = 0
            factor_contributions[snapshot.factor_name] += (trade.pnl or 0) * snapshot.signal_contribution

    top_factors = sorted(
        [{"name": k, "contribution": round(v, 2)} for k, v in factor_contributions.items()],
        key=lambda x: abs(x["contribution"]),
        reverse=True,
    )[:3]

    reports = await trade_attribution_service.get_reports(strategy_id, limit=1)

    return {
        "strategy_id": strategy_id,
        "total_trades": total,
        "win_rate": round(win_rate, 4),
        "profit_factor": round(profit_factor, 2),
        "top_factors": top_factors,
        "has_reports": len(reports) > 0,
        "latest_report_id": reports[0].report_id if reports else None,
    }
