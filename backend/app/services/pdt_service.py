"""
PDT (Pattern Day Trader) 服务

PRD 4.7: PDT规则管理
- 账户 < $25,000 时受限
- 5个交易日内最多4次日内交易
- 超过限制账户被限制90天

数据源: Alpaca API (账户和交易数据)
当API不可用时降级到缓存/数据库数据
"""

from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import uuid

import httpx
import structlog
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_context
from app.models.deployment import PDTStatus as PDTStatusModel, IntradayTrade

logger = structlog.get_logger()


# ============ 数据源状态 ============

class PDTDataSourceType(str, Enum):
    ALPACA = "alpaca"
    DATABASE = "database"
    MOCK = "mock"


class PDTDataSourceStatus:
    """PDT服务数据源状态"""
    def __init__(self):
        self.source = PDTDataSourceType.MOCK
        self.is_connected = False
        self.error_message: Optional[str] = None
        self.last_sync: Optional[datetime] = None

    def to_dict(self):
        return {
            "source": self.source.value,
            "is_mock": self.source == PDTDataSourceType.MOCK,
            "is_connected": self.is_connected,
            "error_message": self.error_message,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }


# 全局数据源状态
_data_source_status = PDTDataSourceStatus()


# ============ Pydantic模型 ============

class DayTradeRecord(BaseModel):
    """日内交易记录"""
    trade_id: str
    symbol: str
    buy_time: datetime
    sell_time: datetime
    pnl: float
    expires_at: datetime  # 计入PDT的到期时间


class PDTStatus(BaseModel):
    """PDT状态"""
    account_id: str
    account_balance: float
    is_pdt_restricted: bool  # 账户是否受PDT限制 (<$25K)
    remaining_day_trades: int
    max_day_trades: int = 4
    rolling_days: int = 5
    is_blocked: bool  # 是否已被限制
    blocked_until: Optional[datetime] = None
    reset_at: datetime  # 下次重置时间
    recent_day_trades: list[DayTradeRecord] = Field(default_factory=list)
    data_source: str = "mock"  # 数据来源标识


class PDTService:
    """
    PDT规则管理服务

    数据源优先级:
    1. Alpaca API (实时)
    2. 数据库缓存 (降级)
    3. Mock数据 (开发)
    """

    MAX_DAY_TRADES = 4  # 5交易日内最多4次
    ROLLING_DAYS = 5    # 滚动5个交易日
    PDT_THRESHOLD = 25000  # $25,000 阈值
    BLOCK_DAYS = 90  # 违规后限制天数

    async def get_alpaca_client(self) -> Optional[httpx.AsyncClient]:
        """获取Alpaca HTTP客户端"""
        api_key = settings.ALPACA_API_KEY
        api_secret = settings.ALPACA_SECRET_KEY
        base_url = settings.ALPACA_BASE_URL

        if not api_key or not api_secret:
            return None

        return httpx.AsyncClient(
            base_url=base_url,
            headers={
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": api_secret,
            },
            timeout=10.0,
        )

    async def _fetch_alpaca_account(self) -> Optional[dict]:
        """从Alpaca获取账户信息"""
        client = await self.get_alpaca_client()
        if not client:
            return None

        try:
            async with client:
                response = await client.get("/v2/account")
                if response.status_code == 200:
                    _data_source_status.source = PDTDataSourceType.ALPACA
                    _data_source_status.is_connected = True
                    _data_source_status.error_message = None
                    _data_source_status.last_sync = datetime.now()
                    return response.json()
                else:
                    logger.warning("alpaca_account_error", status=response.status_code)
                    return None
        except Exception as e:
            logger.warning("alpaca_connection_error", error=str(e))
            _data_source_status.is_connected = False
            _data_source_status.error_message = str(e)
            return None

    async def _fetch_alpaca_activities(self, activity_type: str = "FILL") -> list[dict]:
        """从Alpaca获取交易活动"""
        client = await self.get_alpaca_client()
        if not client:
            return []

        try:
            async with client:
                # 获取最近7天的活动 (约5个交易日)
                after = (datetime.now() - timedelta(days=7)).isoformat()
                response = await client.get(
                    "/v2/account/activities/FILL",
                    params={"after": after, "direction": "desc", "page_size": 100}
                )
                if response.status_code == 200:
                    return response.json()
                return []
        except Exception as e:
            logger.warning("alpaca_activities_error", error=str(e))
            return []

    def _identify_day_trades(self, activities: list[dict]) -> list[DayTradeRecord]:
        """从活动记录中识别日内交易"""
        # 按symbol分组
        symbol_trades: dict[str, list[dict]] = {}
        for activity in activities:
            symbol = activity.get("symbol")
            if symbol:
                if symbol not in symbol_trades:
                    symbol_trades[symbol] = []
                symbol_trades[symbol].append(activity)

        day_trades = []

        for symbol, trades in symbol_trades.items():
            # 按时间排序
            trades.sort(key=lambda x: x.get("transaction_time", ""))

            # 找出同一天的买入和卖出配对
            buys = [t for t in trades if t.get("side") == "buy"]
            sells = [t for t in trades if t.get("side") == "sell"]

            for buy in buys:
                buy_time_str = buy.get("transaction_time", "")
                if not buy_time_str:
                    continue

                buy_time = datetime.fromisoformat(buy_time_str.replace("Z", "+00:00"))
                buy_date = buy_time.date()

                # 找同一天的卖出
                for sell in sells:
                    sell_time_str = sell.get("transaction_time", "")
                    if not sell_time_str:
                        continue

                    sell_time = datetime.fromisoformat(sell_time_str.replace("Z", "+00:00"))
                    sell_date = sell_time.date()

                    if buy_date == sell_date and sell_time > buy_time:
                        # 这是一个日内交易
                        buy_price = float(buy.get("price", 0))
                        sell_price = float(sell.get("price", 0))
                        qty = float(buy.get("qty", 0))
                        pnl = (sell_price - buy_price) * qty

                        day_trades.append(DayTradeRecord(
                            trade_id=sell.get("id", str(uuid.uuid4())),
                            symbol=symbol,
                            buy_time=buy_time,
                            sell_time=sell_time,
                            pnl=pnl,
                            expires_at=sell_time + timedelta(days=7),  # 约5交易日
                        ))
                        break

        return day_trades

    async def _get_from_database(self, user_id: str) -> Optional[dict]:
        """从数据库获取缓存的PDT状态"""
        try:
            async with get_db_context() as session:
                stmt = select(PDTStatusModel).where(PDTStatusModel.user_id == user_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

                if model:
                    return {
                        "account_equity": model.account_equity,
                        "is_pdt_account": model.is_pdt_account,
                        "day_trades_count": model.day_trades_count,
                        "remaining_day_trades": model.remaining_day_trades,
                        "reset_date": model.reset_date,
                        "is_warning": model.is_warning,
                    }
                return None
        except Exception as e:
            logger.warning("database_fetch_error", error=str(e))
            return None

    async def _save_to_database(
        self,
        user_id: str,
        account_equity: float,
        is_pdt_account: bool,
        day_trades_count: int,
        remaining_day_trades: int,
        reset_date: Optional[datetime],
        is_warning: bool,
    ):
        """保存PDT状态到数据库"""
        try:
            async with get_db_context() as session:
                # 检查是否存在
                stmt = select(PDTStatusModel).where(PDTStatusModel.user_id == user_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()

                if existing:
                    # 更新
                    stmt = (
                        update(PDTStatusModel)
                        .where(PDTStatusModel.user_id == user_id)
                        .values(
                            account_equity=account_equity,
                            is_pdt_account=is_pdt_account,
                            day_trades_count=day_trades_count,
                            remaining_day_trades=remaining_day_trades,
                            reset_date=reset_date,
                            is_warning=is_warning,
                            last_sync_at=datetime.now(),
                        )
                    )
                    await session.execute(stmt)
                else:
                    # 插入
                    model = PDTStatusModel(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        account_equity=account_equity,
                        is_pdt_account=is_pdt_account,
                        day_trades_count=day_trades_count,
                        remaining_day_trades=remaining_day_trades,
                        reset_date=reset_date,
                        is_warning=is_warning,
                        last_sync_at=datetime.now(),
                    )
                    session.add(model)
        except Exception as e:
            logger.warning("database_save_error", error=str(e))

    async def get_pdt_status(self, account_id: str) -> PDTStatus:
        """
        获取PDT状态

        优先级:
        1. Alpaca API实时数据
        2. 数据库缓存
        3. Mock数据
        """
        logger.info("get_pdt_status", account_id=account_id)

        # 尝试从Alpaca获取
        alpaca_account = await self._fetch_alpaca_account()

        if alpaca_account:
            # 从Alpaca获取成功
            equity = float(alpaca_account.get("equity", 0))
            is_pdt = alpaca_account.get("pattern_day_trader", False)
            day_trading_buying_power = float(alpaca_account.get("daytrading_buying_power", 0))

            # Alpaca直接告诉我们是否是PDT账户
            is_restricted = equity < self.PDT_THRESHOLD

            # 获取日内交易活动
            activities = await self._fetch_alpaca_activities()
            day_trades = self._identify_day_trades(activities)
            recent_trades = [t for t in day_trades if t.sell_time >= self._get_rolling_cutoff()]

            remaining = max(0, self.MAX_DAY_TRADES - len(recent_trades))
            is_blocked = remaining == 0 and is_restricted
            reset_at = self._calculate_reset_time(recent_trades)

            # 保存到数据库缓存
            await self._save_to_database(
                user_id=account_id,
                account_equity=equity,
                is_pdt_account=is_pdt,
                day_trades_count=len(recent_trades),
                remaining_day_trades=remaining,
                reset_date=reset_at,
                is_warning=remaining <= 1,
            )

            return PDTStatus(
                account_id=account_id,
                account_balance=equity,
                is_pdt_restricted=is_restricted,
                remaining_day_trades=remaining,
                is_blocked=is_blocked,
                blocked_until=None,  # TODO: 从Alpaca获取
                reset_at=reset_at,
                recent_day_trades=recent_trades,
                data_source="alpaca",
            )

        # 降级到数据库
        db_data = await self._get_from_database(account_id)
        if db_data:
            _data_source_status.source = PDTDataSourceType.DATABASE
            _data_source_status.is_connected = True

            equity = db_data["account_equity"]
            is_restricted = equity < self.PDT_THRESHOLD
            remaining = db_data["remaining_day_trades"]

            return PDTStatus(
                account_id=account_id,
                account_balance=equity,
                is_pdt_restricted=is_restricted,
                remaining_day_trades=remaining,
                is_blocked=remaining == 0 and is_restricted,
                blocked_until=None,
                reset_at=db_data["reset_date"] or datetime.now(),
                recent_day_trades=[],  # 数据库不存储详细记录
                data_source="database",
            )

        # 降级到Mock数据
        _data_source_status.source = PDTDataSourceType.MOCK
        _data_source_status.is_connected = False
        _data_source_status.error_message = "Alpaca API不可用，使用演示数据"

        return PDTStatus(
            account_id=account_id,
            account_balance=18500.00,  # 模拟低于PDT阈值
            is_pdt_restricted=True,
            remaining_day_trades=2,
            is_blocked=False,
            blocked_until=None,
            reset_at=datetime.now() + timedelta(days=3),
            recent_day_trades=[
                DayTradeRecord(
                    trade_id=str(uuid.uuid4()),
                    symbol="AAPL",
                    buy_time=datetime.now() - timedelta(days=2, hours=3),
                    sell_time=datetime.now() - timedelta(days=2, hours=1),
                    pnl=125.50,
                    expires_at=datetime.now() + timedelta(days=3),
                ),
                DayTradeRecord(
                    trade_id=str(uuid.uuid4()),
                    symbol="MSFT",
                    buy_time=datetime.now() - timedelta(days=1, hours=4),
                    sell_time=datetime.now() - timedelta(days=1, hours=2),
                    pnl=-45.20,
                    expires_at=datetime.now() + timedelta(days=4),
                ),
            ],
            data_source="mock",
        )

    async def check_can_day_trade(self, account_id: str) -> tuple[bool, str]:
        """检查是否可以进行日内交易"""
        status = await self.get_pdt_status(account_id)

        # 高余额账户无限制
        if not status.is_pdt_restricted:
            return True, "账户余额 >= $25,000，无PDT限制"

        # 检查是否被违规限制
        if status.blocked_until:
            return False, f"账户因PDT违规被限制至 {status.blocked_until.strftime('%Y-%m-%d')}"

        # 检查剩余次数
        if status.remaining_day_trades > 0:
            return True, f"剩余 {status.remaining_day_trades} 次日内交易机会"

        return False, f"已达PDT限制，将于 {status.reset_at.strftime('%Y-%m-%d %H:%M')} 重置"

    async def record_day_trade(
        self,
        account_id: str,
        symbol: str,
        buy_time: datetime,
        sell_time: datetime,
        pnl: float,
        db: Optional[AsyncSession] = None,
    ) -> PDTStatus:
        """记录一次日内交易"""
        logger.info(
            "record_day_trade",
            account_id=account_id,
            symbol=symbol,
            pnl=pnl,
        )

        # 保存到数据库
        trade_model = IntradayTrade(
            id=str(uuid.uuid4()),
            user_id=account_id,
            symbol=symbol,
            side="sell",  # 日内交易以卖出时间为准
            quantity=0,  # 需要从实际订单获取
            price=0,
            is_open=False,
            exit_price=0,
            exit_time=sell_time,
            pnl=pnl,
        )

        if db:
            db.add(trade_model)
            await db.commit()
        else:
            try:
                async with get_db_context() as session:
                    session.add(trade_model)
            except Exception as e:
                logger.warning("trade_save_error", error=str(e))

        # 返回更新后的状态
        return await self.get_pdt_status(account_id)

    async def get_recent_trades(self, account_id: str) -> list[DayTradeRecord]:
        """获取最近的日内交易记录"""
        status = await self.get_pdt_status(account_id)
        return status.recent_day_trades

    def _get_rolling_cutoff(self) -> datetime:
        """获取滚动窗口起始日期"""
        # 简化处理：7自然日约等于5交易日
        return datetime.now() - timedelta(days=7)

    def _calculate_reset_time(self, trades: list[DayTradeRecord]) -> datetime:
        """计算下次重置时间"""
        if not trades:
            return datetime.now()
        # 最早的交易过期时间
        return min(t.expires_at for t in trades)

    def get_data_source_status(self) -> dict:
        """获取数据源状态"""
        return _data_source_status.to_dict()


# 全局服务实例
pdt_service = PDTService()


def get_pdt_data_source_status() -> dict:
    """获取PDT服务数据源状态"""
    return pdt_service.get_data_source_status()
