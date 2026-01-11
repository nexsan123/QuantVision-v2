"""
日内交易服务

PRD 4.8: 日内交易管理
- 交易记录持久化到数据库
- 与Alpaca订单同步
- 计算盈亏统计

数据源: Alpaca API (订单) + PostgreSQL (持久化)
"""

from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import uuid

import httpx
import structlog
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_context
from app.models.deployment import IntradayTrade, Deployment, DeploymentStatusEnum

logger = structlog.get_logger()


# ============ 数据源状态 ============

class TradeDataSourceType(str, Enum):
    ALPACA = "alpaca"
    DATABASE = "database"
    MOCK = "mock"


class TradeDataSourceStatus:
    """交易服务数据源状态"""
    def __init__(self):
        self.source = TradeDataSourceType.MOCK
        self.is_connected = False
        self.error_message: Optional[str] = None
        self.last_sync: Optional[datetime] = None

    def to_dict(self):
        return {
            "source": self.source.value,
            "is_mock": self.source == TradeDataSourceType.MOCK,
            "is_connected": self.is_connected,
            "error_message": self.error_message,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
        }


# 全局数据源状态
_data_source_status = TradeDataSourceStatus()


# ============ Pydantic模型 ============

class TradeRecord(BaseModel):
    """交易记录"""
    id: str
    deployment_id: Optional[str] = None
    user_id: str
    symbol: str
    side: str  # buy/sell
    quantity: float
    price: float
    order_type: str = "market"
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    is_open: bool = True
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    alpaca_order_id: Optional[str] = None
    created_at: datetime
    data_source: str = "database"


class TradeSummary(BaseModel):
    """交易统计摘要"""
    total_trades: int = 0
    open_trades: int = 0
    closed_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0


class IntradayTradeService:
    """
    日内交易服务

    数据源优先级:
    1. Alpaca API (实时订单同步)
    2. 数据库 (持久化)
    """

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

    async def record_trade(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_type: str = "market",
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        deployment_id: Optional[str] = None,
        alpaca_order_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> TradeRecord:
        """
        记录新交易

        Returns:
            TradeRecord: 创建的交易记录
        """
        trade_id = str(uuid.uuid4())
        now = datetime.now()

        logger.info(
            "record_trade",
            trade_id=trade_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
        )

        # 创建数据库记录
        trade_model = IntradayTrade(
            id=trade_id,
            deployment_id=deployment_id,
            user_id=user_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
            stop_loss=stop_loss,
            take_profit=take_profit,
            is_open=True,
            alpaca_order_id=alpaca_order_id,
        )

        # 保存到数据库
        if db:
            db.add(trade_model)
            await db.commit()
            await db.refresh(trade_model)
        else:
            try:
                async with get_db_context() as session:
                    session.add(trade_model)
                    await session.commit()
                    # 重新查询以获取完整数据
                    stmt = select(IntradayTrade).where(IntradayTrade.id == trade_id)
                    result = await session.execute(stmt)
                    trade_model = result.scalar_one()
            except Exception as e:
                logger.error("trade_record_error", error=str(e))
                raise

        return TradeRecord(
            id=trade_model.id,
            deployment_id=trade_model.deployment_id,
            user_id=trade_model.user_id,
            symbol=trade_model.symbol,
            side=trade_model.side,
            quantity=trade_model.quantity,
            price=trade_model.price,
            order_type=trade_model.order_type,
            stop_loss=trade_model.stop_loss,
            take_profit=trade_model.take_profit,
            is_open=trade_model.is_open,
            alpaca_order_id=trade_model.alpaca_order_id,
            created_at=trade_model.created_at,
            data_source="database",
        )

    async def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        db: Optional[AsyncSession] = None,
    ) -> TradeRecord:
        """
        关闭交易 (计算盈亏)
        """
        logger.info("close_trade", trade_id=trade_id, exit_price=exit_price)

        # 获取交易记录
        trade = await self.get_trade(trade_id, db)
        if not trade:
            raise ValueError(f"交易不存在: {trade_id}")

        if not trade.is_open:
            raise ValueError(f"交易已关闭: {trade_id}")

        # 计算盈亏
        if trade.side == "buy":
            pnl = (exit_price - trade.price) * trade.quantity
        else:  # sell (short)
            pnl = (trade.price - exit_price) * trade.quantity

        pnl_pct = (pnl / (trade.price * trade.quantity)) * 100

        # 更新数据库
        exit_time = datetime.now()
        update_data = {
            "is_open": False,
            "exit_price": exit_price,
            "exit_time": exit_time,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        }

        if db:
            stmt = (
                update(IntradayTrade)
                .where(IntradayTrade.id == trade_id)
                .values(**update_data)
            )
            await db.execute(stmt)
            await db.commit()
        else:
            async with get_db_context() as session:
                stmt = (
                    update(IntradayTrade)
                    .where(IntradayTrade.id == trade_id)
                    .values(**update_data)
                )
                await session.execute(stmt)

        # 更新部署的统计数据
        if trade.deployment_id:
            await self._update_deployment_stats(trade.deployment_id, pnl, db)

        # 返回更新后的记录
        return TradeRecord(
            id=trade.id,
            deployment_id=trade.deployment_id,
            user_id=trade.user_id,
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            price=trade.price,
            order_type=trade.order_type,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
            is_open=False,
            exit_price=exit_price,
            exit_time=exit_time,
            pnl=pnl,
            pnl_pct=pnl_pct,
            alpaca_order_id=trade.alpaca_order_id,
            created_at=trade.created_at,
            data_source="database",
        )

    async def get_trade(
        self,
        trade_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[TradeRecord]:
        """获取单个交易记录"""
        if db:
            stmt = select(IntradayTrade).where(IntradayTrade.id == trade_id)
            result = await db.execute(stmt)
            model = result.scalar_one_or_none()
        else:
            async with get_db_context() as session:
                stmt = select(IntradayTrade).where(IntradayTrade.id == trade_id)
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_record(model)

    async def get_trades(
        self,
        user_id: str,
        deployment_id: Optional[str] = None,
        symbol: Optional[str] = None,
        is_open: Optional[bool] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        db: Optional[AsyncSession] = None,
    ) -> list[TradeRecord]:
        """获取交易列表"""
        # 构建查询
        stmt = select(IntradayTrade).where(IntradayTrade.user_id == user_id)

        if deployment_id:
            stmt = stmt.where(IntradayTrade.deployment_id == deployment_id)
        if symbol:
            stmt = stmt.where(IntradayTrade.symbol == symbol)
        if is_open is not None:
            stmt = stmt.where(IntradayTrade.is_open == is_open)
        if start_date:
            stmt = stmt.where(IntradayTrade.created_at >= start_date)
        if end_date:
            stmt = stmt.where(IntradayTrade.created_at <= end_date)

        stmt = stmt.order_by(IntradayTrade.created_at.desc()).limit(limit)

        if db:
            result = await db.execute(stmt)
            models = result.scalars().all()
        else:
            async with get_db_context() as session:
                result = await session.execute(stmt)
                models = result.scalars().all()

        return [self._model_to_record(m) for m in models]

    async def get_today_trades(
        self,
        user_id: str,
        db: Optional[AsyncSession] = None,
    ) -> list[TradeRecord]:
        """获取今日交易"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.get_trades(
            user_id=user_id,
            start_date=today_start,
            db=db,
        )

    async def get_trade_summary(
        self,
        user_id: str,
        deployment_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: Optional[AsyncSession] = None,
    ) -> TradeSummary:
        """获取交易统计摘要"""
        trades = await self.get_trades(
            user_id=user_id,
            deployment_id=deployment_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000,
            db=db,
        )

        if not trades:
            return TradeSummary()

        open_trades = [t for t in trades if t.is_open]
        closed_trades = [t for t in trades if not t.is_open]
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]

        total_pnl = sum(t.pnl or 0 for t in closed_trades)
        win_rate = len(winning_trades) / len(closed_trades) if closed_trades else 0

        avg_win = (
            sum(t.pnl for t in winning_trades) / len(winning_trades)
            if winning_trades
            else 0
        )
        avg_loss = (
            sum(t.pnl for t in losing_trades) / len(losing_trades)
            if losing_trades
            else 0
        )

        pnls = [t.pnl for t in closed_trades if t.pnl]
        best_trade = max(pnls) if pnls else 0
        worst_trade = min(pnls) if pnls else 0

        return TradeSummary(
            total_trades=len(trades),
            open_trades=len(open_trades),
            closed_trades=len(closed_trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            total_pnl=total_pnl,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            best_trade=best_trade,
            worst_trade=worst_trade,
        )

    async def sync_from_alpaca(
        self,
        user_id: str,
        db: Optional[AsyncSession] = None,
    ) -> int:
        """
        从Alpaca同步今日订单

        Returns:
            int: 同步的订单数量
        """
        client = await self.get_alpaca_client()
        if not client:
            _data_source_status.source = TradeDataSourceType.DATABASE
            _data_source_status.is_connected = False
            _data_source_status.error_message = "Alpaca API未配置"
            return 0

        try:
            async with client:
                # 获取今日已成交订单
                today = datetime.now().strftime("%Y-%m-%d")
                response = await client.get(
                    "/v2/orders",
                    params={
                        "status": "filled",
                        "after": f"{today}T00:00:00Z",
                        "limit": 500,
                    }
                )

                if response.status_code != 200:
                    logger.warning("alpaca_orders_error", status=response.status_code)
                    return 0

                orders = response.json()
                synced_count = 0

                for order in orders:
                    order_id = order.get("id")

                    # 检查是否已存在
                    existing = await self._get_trade_by_alpaca_id(order_id, db)
                    if existing:
                        continue

                    # 创建交易记录
                    await self.record_trade(
                        user_id=user_id,
                        symbol=order.get("symbol"),
                        side=order.get("side"),
                        quantity=float(order.get("filled_qty", 0)),
                        price=float(order.get("filled_avg_price", 0)),
                        order_type=order.get("type", "market"),
                        alpaca_order_id=order_id,
                        db=db,
                    )
                    synced_count += 1

                _data_source_status.source = TradeDataSourceType.ALPACA
                _data_source_status.is_connected = True
                _data_source_status.error_message = None
                _data_source_status.last_sync = datetime.now()

                logger.info("alpaca_sync_complete", synced_count=synced_count)
                return synced_count

        except Exception as e:
            logger.error("alpaca_sync_error", error=str(e))
            _data_source_status.is_connected = False
            _data_source_status.error_message = str(e)
            return 0

    async def _get_trade_by_alpaca_id(
        self,
        alpaca_order_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[TradeRecord]:
        """根据Alpaca订单ID获取交易"""
        if db:
            stmt = select(IntradayTrade).where(
                IntradayTrade.alpaca_order_id == alpaca_order_id
            )
            result = await db.execute(stmt)
            model = result.scalar_one_or_none()
        else:
            async with get_db_context() as session:
                stmt = select(IntradayTrade).where(
                    IntradayTrade.alpaca_order_id == alpaca_order_id
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

        if not model:
            return None

        return self._model_to_record(model)

    async def _update_deployment_stats(
        self,
        deployment_id: str,
        pnl: float,
        db: Optional[AsyncSession] = None,
    ):
        """更新部署的统计数据"""
        try:
            if db:
                # 获取当前部署
                stmt = select(Deployment).where(Deployment.id == deployment_id)
                result = await db.execute(stmt)
                deployment = result.scalar_one_or_none()

                if deployment:
                    # 获取所有已关闭交易的统计
                    trades_stmt = select(IntradayTrade).where(
                        IntradayTrade.deployment_id == deployment_id,
                        IntradayTrade.is_open == False
                    )
                    trades_result = await db.execute(trades_stmt)
                    trades = trades_result.scalars().all()

                    total_trades = len(trades)
                    winning = sum(1 for t in trades if t.pnl and t.pnl > 0)
                    total_pnl = sum(t.pnl or 0 for t in trades)
                    win_rate = winning / total_trades if total_trades > 0 else 0

                    # 更新部署
                    update_stmt = (
                        update(Deployment)
                        .where(Deployment.id == deployment_id)
                        .values(
                            current_pnl=total_pnl,
                            total_trades=total_trades,
                            win_rate=win_rate,
                        )
                    )
                    await db.execute(update_stmt)
                    await db.commit()
            else:
                async with get_db_context() as session:
                    stmt = select(Deployment).where(Deployment.id == deployment_id)
                    result = await session.execute(stmt)
                    deployment = result.scalar_one_or_none()

                    if deployment:
                        trades_stmt = select(IntradayTrade).where(
                            IntradayTrade.deployment_id == deployment_id,
                            IntradayTrade.is_open == False
                        )
                        trades_result = await session.execute(trades_stmt)
                        trades = trades_result.scalars().all()

                        total_trades = len(trades)
                        winning = sum(1 for t in trades if t.pnl and t.pnl > 0)
                        total_pnl = sum(t.pnl or 0 for t in trades)
                        win_rate = winning / total_trades if total_trades > 0 else 0

                        update_stmt = (
                            update(Deployment)
                            .where(Deployment.id == deployment_id)
                            .values(
                                current_pnl=total_pnl,
                                total_trades=total_trades,
                                win_rate=win_rate,
                            )
                        )
                        await session.execute(update_stmt)

        except Exception as e:
            logger.error("deployment_stats_update_error", error=str(e))

    def _model_to_record(self, model: IntradayTrade) -> TradeRecord:
        """转换模型到记录"""
        return TradeRecord(
            id=model.id,
            deployment_id=model.deployment_id,
            user_id=model.user_id,
            symbol=model.symbol,
            side=model.side,
            quantity=model.quantity,
            price=model.price,
            order_type=model.order_type,
            stop_loss=model.stop_loss,
            take_profit=model.take_profit,
            is_open=model.is_open,
            exit_price=model.exit_price,
            exit_time=model.exit_time,
            pnl=model.pnl,
            pnl_pct=model.pnl_pct,
            alpaca_order_id=model.alpaca_order_id,
            created_at=model.created_at,
            data_source="database",
        )

    def get_data_source_status(self) -> dict:
        """获取数据源状态"""
        return _data_source_status.to_dict()

    async def check_database_connection(self) -> dict:
        """检查数据库连接状态"""
        try:
            async with get_db_context() as session:
                # 执行简单查询测试连接
                stmt = select(IntradayTrade).limit(1)
                await session.execute(stmt)
                return {
                    "source": "database",
                    "is_mock": False,
                    "is_connected": True,
                    "error_message": None
                }
        except Exception as e:
            logger.error("trade_db_check_failed", error=str(e))
            return {
                "source": "mock",
                "is_mock": True,
                "is_connected": False,
                "error_message": f"Database connection failed: {str(e)}"
            }


# 全局服务实例
intraday_trade_service = IntradayTradeService()


def get_trade_data_source_status() -> dict:
    """获取交易服务数据源状态"""
    return intraday_trade_service.get_data_source_status()
