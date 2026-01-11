"""
账户 API 端点
账户总览、持仓、运行中策略

支持:
1. 获取账户概览信息
2. 获取持仓列表
3. 获取运行中策略

数据源: Alpaca API (Paper/Live)
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict

import httpx
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/account", tags=["Account"])


# ==================== 数据源状态 ====================

class DataSourceType(str, Enum):
    """数据源类型"""
    ALPACA_LIVE = "alpaca_live"
    ALPACA_PAPER = "alpaca_paper"
    MOCK = "mock"


class DataSourceStatus(BaseModel):
    """数据源状态"""
    source: DataSourceType = Field(..., description="数据源类型")
    is_mock: bool = Field(..., description="是否为模拟数据")
    is_connected: bool = Field(..., description="是否已连接")
    error_message: Optional[str] = Field(None, description="错误信息")
    last_check: str = Field(..., description="最后检查时间")


# ==================== 数据模型 ====================

class AccountInfo(BaseModel):
    """账户信息"""
    total_value: float = Field(..., description="账户总值")
    cash_balance: float = Field(..., description="现金余额")
    buying_power: float = Field(..., description="购买力")
    portfolio_value: float = Field(..., description="持仓市值")
    day_pnl: float = Field(..., description="今日盈亏")
    day_pnl_pct: float = Field(..., description="今日盈亏百分比")
    total_pnl: float = Field(..., description="总盈亏")
    total_pnl_pct: float = Field(..., description="总盈亏百分比")


class Position(BaseModel):
    """持仓"""
    symbol: str = Field(..., description="股票代码")
    quantity: float = Field(..., description="持仓数量")
    avg_cost: float = Field(..., description="平均成本")
    current_price: float = Field(..., description="当前价格")
    market_value: float = Field(..., description="市值")
    pnl: float = Field(..., description="盈亏金额")
    pnl_pct: float = Field(..., description="盈亏百分比")
    weight: float = Field(..., description="占比权重")


class RunningStrategy(BaseModel):
    """运行中策略"""
    id: str = Field(..., description="策略ID")
    name: str = Field(..., description="策略名称")
    environment: str = Field(..., description="运行环境: paper/live")
    status: str = Field(..., description="状态: running/paused")
    pnl: float = Field(..., description="策略盈亏")
    pnl_pct: float = Field(..., description="策略盈亏百分比")
    trades: int = Field(..., description="交易次数")
    win_rate: float = Field(..., description="胜率")
    started_at: str = Field(..., description="启动时间")


class AccountOverviewResponse(BaseModel):
    """账户总览响应"""
    account: AccountInfo
    positions: List[Position]
    running_strategies: List[RunningStrategy]
    last_updated: str
    data_sources: Dict[str, DataSourceStatus] = Field(
        default_factory=dict,
        description="各数据源状态: account, positions, strategies"
    )


# ==================== Alpaca API 集成 ====================

def get_alpaca_source_type() -> DataSourceType:
    """获取Alpaca数据源类型"""
    base_url = settings.ALPACA_BASE_URL
    if "paper" in base_url:
        return DataSourceType.ALPACA_PAPER
    return DataSourceType.ALPACA_LIVE


async def get_alpaca_account() -> tuple[Optional[dict], DataSourceStatus]:
    """
    获取 Alpaca 账户信息
    返回: (账户数据, 数据源状态)
    """
    api_key = settings.ALPACA_API_KEY
    api_secret = settings.ALPACA_SECRET_KEY
    base_url = settings.ALPACA_BASE_URL
    now = datetime.now().isoformat()

    logger.info(f"Alpaca API check - Key configured: {bool(api_key)}, Base URL: {base_url}")

    if not api_key or not api_secret:
        logger.warning("Alpaca credentials not configured")
        return None, DataSourceStatus(
            source=DataSourceType.MOCK,
            is_mock=True,
            is_connected=False,
            error_message="Alpaca API credentials not configured",
            last_check=now
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url}/v2/account",
                headers={
                    "APCA-API-KEY-ID": api_key,
                    "APCA-API-SECRET-KEY": api_secret,
                }
            )
            if response.status_code == 200:
                return response.json(), DataSourceStatus(
                    source=get_alpaca_source_type(),
                    is_mock=False,
                    is_connected=True,
                    error_message=None,
                    last_check=now
                )
            else:
                error_msg = f"Alpaca API error: {response.status_code}"
                logger.error(error_msg)
                return None, DataSourceStatus(
                    source=DataSourceType.MOCK,
                    is_mock=True,
                    is_connected=False,
                    error_message=error_msg,
                    last_check=now
                )
    except Exception as e:
        error_msg = f"Alpaca API connection failed: {str(e)}"
        logger.error(error_msg)
        return None, DataSourceStatus(
            source=DataSourceType.MOCK,
            is_mock=True,
            is_connected=False,
            error_message=error_msg,
            last_check=now
        )


async def get_alpaca_positions() -> tuple[List[dict], DataSourceStatus]:
    """
    获取 Alpaca 持仓
    返回: (持仓列表, 数据源状态)
    """
    api_key = settings.ALPACA_API_KEY
    api_secret = settings.ALPACA_SECRET_KEY
    base_url = settings.ALPACA_BASE_URL
    now = datetime.now().isoformat()

    if not api_key or not api_secret:
        return [], DataSourceStatus(
            source=DataSourceType.MOCK,
            is_mock=True,
            is_connected=False,
            error_message="Alpaca API credentials not configured",
            last_check=now
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url}/v2/positions",
                headers={
                    "APCA-API-KEY-ID": api_key,
                    "APCA-API-SECRET-KEY": api_secret,
                }
            )
            if response.status_code == 200:
                return response.json(), DataSourceStatus(
                    source=get_alpaca_source_type(),
                    is_mock=False,
                    is_connected=True,
                    error_message=None,
                    last_check=now
                )
            else:
                error_msg = f"Alpaca positions API error: {response.status_code}"
                logger.error(error_msg)
                return [], DataSourceStatus(
                    source=DataSourceType.MOCK,
                    is_mock=True,
                    is_connected=False,
                    error_message=error_msg,
                    last_check=now
                )
    except Exception as e:
        error_msg = f"Alpaca positions API connection failed: {str(e)}"
        logger.error(error_msg)
        return [], DataSourceStatus(
            source=DataSourceType.MOCK,
            is_mock=True,
            is_connected=False,
            error_message=error_msg,
            last_check=now
        )


# ==================== Mock 数据 ====================

def get_mock_account() -> AccountInfo:
    """模拟账户数据"""
    return AccountInfo(
        total_value=125680.50,
        cash_balance=25680.50,
        buying_power=51361.00,
        portfolio_value=100000.00,
        day_pnl=1250.30,
        day_pnl_pct=0.0101,
        total_pnl=25680.50,
        total_pnl_pct=0.2568,
    )


def get_mock_positions() -> List[Position]:
    """模拟持仓数据"""
    return [
        Position(symbol='NVDA', quantity=50, avg_cost=480.00, current_price=520.50, market_value=26025, pnl=2025, pnl_pct=0.0844, weight=0.26),
        Position(symbol='AAPL', quantity=100, avg_cost=175.00, current_price=182.30, market_value=18230, pnl=730, pnl_pct=0.0417, weight=0.18),
        Position(symbol='MSFT', quantity=40, avg_cost=380.00, current_price=415.20, market_value=16608, pnl=1408, pnl_pct=0.0926, weight=0.17),
        Position(symbol='GOOGL', quantity=80, avg_cost=140.00, current_price=152.80, market_value=12224, pnl=1024, pnl_pct=0.0914, weight=0.12),
        Position(symbol='AMZN', quantity=60, avg_cost=155.00, current_price=168.50, market_value=10110, pnl=810, pnl_pct=0.0871, weight=0.10),
        Position(symbol='TSLA', quantity=30, avg_cost=240.00, current_price=248.50, market_value=7455, pnl=255, pnl_pct=0.0354, weight=0.07),
        Position(symbol='META', quantity=20, avg_cost=450.00, current_price=495.00, market_value=9900, pnl=900, pnl_pct=0.10, weight=0.10),
    ]


def get_mock_strategies() -> List[RunningStrategy]:
    """模拟运行中策略"""
    return [
        RunningStrategy(id='stg-003', name='均值回归策略', environment='live', status='running', pnl=12500, pnl_pct=0.125, trades=45, win_rate=0.62, started_at='2024-10-15'),
        RunningStrategy(id='stg-002', name='动量突破策略', environment='paper', status='running', pnl=8200, pnl_pct=0.082, trades=120, win_rate=0.52, started_at='2024-11-20'),
    ]


# ==================== 辅助函数 ====================

def parse_alpaca_account(alpaca_account: dict) -> AccountInfo:
    """解析Alpaca账户数据"""
    equity = float(alpaca_account.get("equity", 0))
    cash = float(alpaca_account.get("cash", 0))
    buying_power = float(alpaca_account.get("buying_power", 0))
    portfolio_value = float(alpaca_account.get("long_market_value", 0))
    last_equity = float(alpaca_account.get("last_equity", equity))

    day_pnl = equity - last_equity
    day_pnl_pct = day_pnl / last_equity if last_equity > 0 else 0

    # 计算总盈亏 (从Alpaca账户初始值计算)
    initial_equity = float(alpaca_account.get("initial_margin", 100000.0)) or 100000.0
    total_pnl = equity - initial_equity
    total_pnl_pct = total_pnl / initial_equity if initial_equity > 0 else 0

    return AccountInfo(
        total_value=equity,
        cash_balance=cash,
        buying_power=buying_power,
        portfolio_value=portfolio_value,
        day_pnl=day_pnl,
        day_pnl_pct=day_pnl_pct,
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
    )


def parse_alpaca_positions(alpaca_positions: List[dict]) -> List[Position]:
    """解析Alpaca持仓数据"""
    positions = []
    total_market_value = sum(float(p.get("market_value", 0)) for p in alpaca_positions)

    for p in alpaca_positions:
        market_value = float(p.get("market_value", 0))
        positions.append(Position(
            symbol=p.get("symbol", ""),
            quantity=float(p.get("qty", 0)),
            avg_cost=float(p.get("avg_entry_price", 0)),
            current_price=float(p.get("current_price", 0)),
            market_value=market_value,
            pnl=float(p.get("unrealized_pl", 0)),
            pnl_pct=float(p.get("unrealized_plpc", 0)),
            weight=market_value / total_market_value if total_market_value > 0 else 0,
        ))
    return positions


# ==================== API 端点 ====================

@router.get("/overview", response_model=AccountOverviewResponse, summary="获取账户总览")
async def get_account_overview():
    """
    获取账户总览

    包含:
    - 账户信息 (总值、现金、盈亏等)
    - 持仓列表
    - 运行中策略
    - 数据源状态 (标识是否为真实数据)
    """
    now = datetime.now().isoformat()
    data_sources: Dict[str, DataSourceStatus] = {}

    # 获取账户数据
    alpaca_account, account_status = await get_alpaca_account()
    data_sources["account"] = account_status

    if alpaca_account:
        account = parse_alpaca_account(alpaca_account)
    else:
        account = get_mock_account()

    # 获取持仓数据
    alpaca_positions, positions_status = await get_alpaca_positions()
    data_sources["positions"] = positions_status

    if alpaca_positions:
        positions = parse_alpaca_positions(alpaca_positions)
    else:
        positions = get_mock_positions()

    # 运行中策略 (目前无真实数据源，标记为mock)
    strategies = get_mock_strategies()
    data_sources["strategies"] = DataSourceStatus(
        source=DataSourceType.MOCK,
        is_mock=True,
        is_connected=False,
        error_message="Strategies data not yet connected to database",
        last_check=now
    )

    return AccountOverviewResponse(
        account=account,
        positions=positions,
        running_strategies=strategies,
        last_updated=now,
        data_sources=data_sources,
    )


@router.get("/info", summary="获取账户信息")
async def get_account_info():
    """获取账户基本信息（含数据源状态）"""
    alpaca_account, status = await get_alpaca_account()

    if alpaca_account:
        account = parse_alpaca_account(alpaca_account)
    else:
        account = get_mock_account()

    return {
        "data": account,
        "data_source": status
    }


@router.get("/positions", summary="获取持仓列表")
async def get_positions():
    """获取所有持仓（含数据源状态）"""
    alpaca_positions, status = await get_alpaca_positions()

    if alpaca_positions:
        positions = parse_alpaca_positions(alpaca_positions)
    else:
        positions = get_mock_positions()

    return {
        "data": positions,
        "data_source": status
    }


@router.get("/strategies", summary="获取运行中策略")
async def get_running_strategies():
    """获取运行中的策略列表（含数据源状态）"""
    now = datetime.now().isoformat()

    # TODO: 从数据库获取真实运行中的策略
    strategies = get_mock_strategies()

    return {
        "data": strategies,
        "data_source": DataSourceStatus(
            source=DataSourceType.MOCK,
            is_mock=True,
            is_connected=False,
            error_message="Strategies data not yet connected to database",
            last_check=now
        )
    }


@router.get("/data-sources", summary="获取所有数据源状态")
async def get_data_sources_status():
    """
    检查所有数据源连接状态

    返回各服务的数据源状态:
    - account: Alpaca账户连接
    - positions: Alpaca持仓数据
    - strategies: 策略部署 (数据库)
    - pdt: PDT规则状态 (Alpaca + 数据库)
    - signals: 信号雷达 (Polygon行情)
    - trades: 日内交易 (数据库)
    """
    now = datetime.now().isoformat()
    sources = {}

    # 检查Alpaca账户连接
    _, account_status = await get_alpaca_account()
    _, positions_status = await get_alpaca_positions()

    sources["account"] = account_status
    sources["positions"] = positions_status

    # 检查策略部署 (数据库)
    try:
        from app.services.deployment_service import deployment_service
        deployment_status = await deployment_service.check_database_connection()
        sources["strategies"] = DataSourceStatus(
            source=DataSourceType.ALPACA_PAPER if not deployment_status.get("is_mock") else DataSourceType.MOCK,
            is_mock=deployment_status.get("is_mock", True),
            is_connected=deployment_status.get("is_connected", False),
            error_message=deployment_status.get("error_message"),
            last_check=now
        )
    except Exception as e:
        sources["strategies"] = DataSourceStatus(
            source=DataSourceType.MOCK,
            is_mock=True,
            is_connected=False,
            error_message=f"Deployment service error: {str(e)}",
            last_check=now
        )

    # 检查PDT服务 (Alpaca + 数据库)
    try:
        from app.services.pdt_service import pdt_service
        pdt_status = pdt_service.get_data_source_status()
        pdt_source_type = DataSourceType.MOCK
        if pdt_status.get("source") == "alpaca":
            pdt_source_type = get_alpaca_source_type()
        sources["pdt"] = DataSourceStatus(
            source=pdt_source_type,
            is_mock=pdt_status.get("is_mock", True),
            is_connected=pdt_status.get("is_connected", False),
            error_message=pdt_status.get("error_message"),
            last_check=now
        )
    except Exception as e:
        sources["pdt"] = DataSourceStatus(
            source=DataSourceType.MOCK,
            is_mock=True,
            is_connected=False,
            error_message=f"PDT service error: {str(e)}",
            last_check=now
        )

    # 检查信号雷达 (Polygon行情)
    polygon_connected = bool(settings.POLYGON_API_KEY)
    sources["signals"] = DataSourceStatus(
        source=DataSourceType.ALPACA_PAPER if polygon_connected else DataSourceType.MOCK,
        is_mock=not polygon_connected,
        is_connected=polygon_connected,
        error_message=None if polygon_connected else "Polygon API key not configured",
        last_check=now
    )

    # 检查日内交易 (数据库)
    try:
        from app.services.intraday_trade_service import intraday_trade_service
        trades_status = await intraday_trade_service.check_database_connection()
        sources["trades"] = DataSourceStatus(
            source=DataSourceType.ALPACA_PAPER if not trades_status.get("is_mock") else DataSourceType.MOCK,
            is_mock=trades_status.get("is_mock", True),
            is_connected=trades_status.get("is_connected", False),
            error_message=trades_status.get("error_message"),
            last_check=now
        )
    except Exception as e:
        sources["trades"] = DataSourceStatus(
            source=DataSourceType.MOCK,
            is_mock=True,
            is_connected=False,
            error_message=f"Trade service error: {str(e)}",
            last_check=now
        )

    # 计算整体状态
    connected_count = sum(1 for s in sources.values() if s.is_connected)
    total_count = len(sources)

    if connected_count == total_count:
        overall_status = "connected"
    elif connected_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "disconnected"

    return {
        **sources,
        "overall_status": overall_status,
        "connected_services": connected_count,
        "total_services": total_count
    }
