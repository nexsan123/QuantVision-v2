"""
PDT (Pattern Day Trader) API

PRD 4.7: PDT规则管理
端点:
- GET /pdt/status - 获取PDT状态
- GET /pdt/check - 检查是否允许日内交易
- GET /pdt/trades - 获取日内交易记录
- GET /pdt/data-sources - 获取数据源状态

数据源: Alpaca API (实时) / 数据库 (缓存) / Mock (降级)
"""

from fastapi import APIRouter, HTTPException

from app.services.pdt_service import pdt_service, PDTStatus, DayTradeRecord, get_pdt_data_source_status

router = APIRouter(prefix="/pdt", tags=["PDT"])

# 模拟当前用户的账户ID
DEMO_ACCOUNT_ID = "demo-account"


@router.get("/status", response_model=PDTStatus, summary="获取PDT状态")
async def get_pdt_status():
    """
    获取当前用户的PDT状态

    数据源优先级:
    1. Alpaca API (实时)
    2. 数据库缓存 (降级)
    3. Mock数据 (开发)

    返回:
    - 账户余额
    - 是否受PDT限制
    - 剩余日内交易次数
    - 重置时间
    - 最近的日内交易记录
    - data_source: 数据来源标识
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


@router.get("/data-sources", summary="获取PDT数据源状态")
async def get_data_sources():
    """
    获取PDT服务的数据源连接状态

    返回:
    - source: 当前使用的数据源 (alpaca/database/mock)
    - is_connected: 是否已连接
    - error_message: 错误信息 (如有)
    - last_sync: 最后同步时间
    """
    return get_pdt_data_source_status()
