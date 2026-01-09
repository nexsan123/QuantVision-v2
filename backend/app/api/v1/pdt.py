"""
PDT (Pattern Day Trader) API

PRD 4.7: PDT规则管理
端点:
- GET /pdt/status - 获取PDT状态
- GET /pdt/check - 检查是否允许日内交易
- GET /pdt/trades - 获取日内交易记录
"""

from fastapi import APIRouter, HTTPException

from app.services.pdt_service import pdt_service, PDTStatus, DayTradeRecord

router = APIRouter(prefix="/pdt", tags=["PDT"])

# 模拟当前用户的账户ID
DEMO_ACCOUNT_ID = "demo-account"


@router.get("/status", response_model=PDTStatus, summary="获取PDT状态")
async def get_pdt_status():
    """
    获取当前用户的PDT状态

    返回:
    - 账户余额
    - 是否受PDT限制
    - 剩余日内交易次数
    - 重置时间
    - 最近的日内交易记录
    """
    try:
        return await pdt_service.get_pdt_status(DEMO_ACCOUNT_ID)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check", summary="检查是否允许日内交易")
async def check_day_trade_allowed():
    """
    检查是否允许进行日内交易

    返回:
    - allowed: 是否允许
    - reason: 原因说明
    """
    try:
        allowed, reason = await pdt_service.check_can_day_trade(DEMO_ACCOUNT_ID)
        return {
            "allowed": allowed,
            "reason": reason,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades", summary="获取日内交易记录")
async def get_recent_day_trades():
    """
    获取最近的日内交易记录

    返回5个交易日内的所有日内交易
    """
    try:
        trades = await pdt_service.get_recent_trades(DEMO_ACCOUNT_ID)
        return {
            "trades": trades,
            "count": len(trades),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
