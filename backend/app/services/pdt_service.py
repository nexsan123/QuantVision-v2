"""
PDT (Pattern Day Trader) 服务

PRD 4.7: PDT规则管理
- 账户 < $25,000 时受限
- 5个交易日内最多4次日内交易
- 超过限制账户被限制90天
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()


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


class PDTService:
    """PDT规则管理服务"""

    MAX_DAY_TRADES = 4  # 5交易日内最多4次
    ROLLING_DAYS = 5    # 滚动5个交易日
    PDT_THRESHOLD = 25000  # $25,000 阈值
    BLOCK_DAYS = 90  # 违规后限制天数

    # 模拟数据存储
    _accounts: dict[str, dict] = {}
    _day_trades: dict[str, list[DayTradeRecord]] = {}

    def __init__(self):
        # 初始化模拟数据
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化模拟数据"""
        # 模拟账户
        self._accounts = {
            "demo-account": {
                "balance": 18500.00,  # 低于PDT阈值
                "blocked_until": None,
            }
        }

        # 模拟最近的日内交易
        now = datetime.now()
        self._day_trades["demo-account"] = [
            DayTradeRecord(
                trade_id=str(uuid.uuid4()),
                symbol="AAPL",
                buy_time=now - timedelta(days=2, hours=3),
                sell_time=now - timedelta(days=2, hours=1),
                pnl=125.50,
                expires_at=now + timedelta(days=3),
            ),
            DayTradeRecord(
                trade_id=str(uuid.uuid4()),
                symbol="MSFT",
                buy_time=now - timedelta(days=1, hours=4),
                sell_time=now - timedelta(days=1, hours=2),
                pnl=-45.20,
                expires_at=now + timedelta(days=4),
            ),
        ]

    async def get_pdt_status(self, account_id: str) -> PDTStatus:
        """获取PDT状态"""
        logger.info("get_pdt_status", account_id=account_id)

        # 获取账户信息
        account = self._accounts.get(account_id, {"balance": 20000, "blocked_until": None})
        balance = account["balance"]
        is_restricted = balance < self.PDT_THRESHOLD

        # 检查是否被限制
        blocked_until = account.get("blocked_until")
        is_blocked_by_violation = False
        if blocked_until and datetime.now() < blocked_until:
            is_blocked_by_violation = True

        # 获取最近的日内交易
        cutoff_date = self._get_rolling_cutoff()
        all_trades = self._day_trades.get(account_id, [])
        recent_trades = [t for t in all_trades if t.sell_time >= cutoff_date]

        # 计算剩余次数
        remaining = max(0, self.MAX_DAY_TRADES - len(recent_trades))
        is_blocked = remaining == 0 or is_blocked_by_violation

        # 计算重置时间
        reset_at = self._calculate_reset_time(recent_trades)

        return PDTStatus(
            account_id=account_id,
            account_balance=balance,
            is_pdt_restricted=is_restricted,
            remaining_day_trades=remaining,
            is_blocked=is_blocked,
            blocked_until=blocked_until if is_blocked_by_violation else None,
            reset_at=reset_at,
            recent_day_trades=recent_trades,
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
    ) -> PDTStatus:
        """记录一次日内交易"""
        logger.info(
            "record_day_trade",
            account_id=account_id,
            symbol=symbol,
            pnl=pnl,
        )

        # 计算过期时间 (5个交易日后)
        expires_at = sell_time + timedelta(days=7)  # 简化：7自然日约等于5交易日

        trade = DayTradeRecord(
            trade_id=str(uuid.uuid4()),
            symbol=symbol,
            buy_time=buy_time,
            sell_time=sell_time,
            pnl=pnl,
            expires_at=expires_at,
        )

        # 保存交易
        if account_id not in self._day_trades:
            self._day_trades[account_id] = []
        self._day_trades[account_id].append(trade)

        # 检查是否超限
        status = await self.get_pdt_status(account_id)
        if status.is_pdt_restricted and status.remaining_day_trades < 0:
            # 触发90天限制
            self._accounts[account_id]["blocked_until"] = datetime.now() + timedelta(days=self.BLOCK_DAYS)
            logger.warning("pdt_violation", account_id=account_id)

        return await self.get_pdt_status(account_id)

    async def get_recent_trades(self, account_id: str) -> list[DayTradeRecord]:
        """获取最近的日内交易记录"""
        cutoff_date = self._get_rolling_cutoff()
        all_trades = self._day_trades.get(account_id, [])
        return [t for t in all_trades if t.sell_time >= cutoff_date]

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


# 全局服务实例
pdt_service = PDTService()
