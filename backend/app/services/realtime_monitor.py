"""
实时监控服务
Sprint 10: 集成 Alpaca 实时数据与风险预警

功能:
- 实时持仓监控
- 自动风险检测
- WebSocket 推送
"""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional, Callable

import structlog

from app.core.config import settings
from app.services.alpaca_client import get_alpaca_client, AlpacaPosition
from app.services.alert_service import alert_service
from app.schemas.alert import AlertType, AlertSeverity

logger = structlog.get_logger()


class RealtimeMonitorService:
    """
    实时监控服务

    集成 Alpaca 账户数据，实时计算风险指标并触发预警
    """

    def __init__(self):
        self.alpaca = get_alpaca_client()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._callbacks: list[Callable] = []

        # 监控状态
        self._last_equity: Optional[Decimal] = None
        self._day_start_equity: Optional[Decimal] = None
        self._peak_equity: Optional[Decimal] = None

    async def start(self, user_id: str = "demo-user"):
        """启动实时监控"""
        if self._running:
            logger.warning("monitor_already_running")
            return

        self._running = True
        self._monitor_task = asyncio.create_task(
            self._monitor_loop(user_id)
        )
        logger.info("realtime_monitor_started")

    async def stop(self):
        """停止监控"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("realtime_monitor_stopped")

    def on_update(self, callback: Callable):
        """注册更新回调"""
        self._callbacks.append(callback)

    async def _monitor_loop(self, user_id: str):
        """监控主循环"""
        try:
            # 初始化基准值
            await self._init_baseline()

            while self._running:
                try:
                    await self._check_risks(user_id)
                    await asyncio.sleep(30)  # 每30秒检查一次
                except Exception as e:
                    logger.error("monitor_check_error", error=str(e))
                    await asyncio.sleep(60)

        except asyncio.CancelledError:
            logger.info("monitor_loop_cancelled")

    async def _init_baseline(self):
        """初始化基准值"""
        try:
            account = await self.alpaca.get_account()
            self._last_equity = account["equity"]
            self._day_start_equity = account["last_equity"]
            self._peak_equity = max(
                account["equity"],
                account["last_equity"]
            )
            logger.info(
                "baseline_initialized",
                equity=float(self._last_equity),
                day_start=float(self._day_start_equity),
            )
        except Exception as e:
            logger.error("baseline_init_error", error=str(e))

    async def _check_risks(self, user_id: str):
        """检查风险指标"""
        try:
            # 获取最新账户数据
            account = await self.alpaca.get_account()
            positions = await self.alpaca.get_positions()

            equity = account["equity"]
            portfolio_value = account["portfolio_value"]

            # 更新峰值
            if self._peak_equity is None or equity > self._peak_equity:
                self._peak_equity = equity

            # 1. 检查单日亏损
            if self._day_start_equity and self._day_start_equity > 0:
                daily_return = (equity - self._day_start_equity) / self._day_start_equity
                if daily_return < -0.03:  # 亏损超过 3%
                    await alert_service.check_and_alert(
                        user_id=user_id,
                        alert_type=AlertType.DAILY_LOSS,
                        current_value=float(daily_return),
                    )

            # 2. 检查最大回撤
            if self._peak_equity and self._peak_equity > 0:
                drawdown = (self._peak_equity - equity) / self._peak_equity
                if drawdown > 0.10:  # 回撤超过 10%
                    await alert_service.check_and_alert(
                        user_id=user_id,
                        alert_type=AlertType.MAX_DRAWDOWN,
                        current_value=float(drawdown),
                    )

            # 3. 检查持仓集中度
            if portfolio_value and portfolio_value > 0:
                for position in positions:
                    weight = abs(position.market_value) / portfolio_value
                    if weight > 0.30:  # 单股超过 30%
                        await alert_service.check_and_alert(
                            user_id=user_id,
                            alert_type=AlertType.CONCENTRATION,
                            current_value=float(weight),
                            extra_details={"symbol": position.symbol},
                        )

            # 通知回调
            update_data = {
                "timestamp": datetime.now().isoformat(),
                "equity": float(equity),
                "portfolio_value": float(portfolio_value),
                "daily_pnl": float(equity - self._day_start_equity) if self._day_start_equity else 0,
                "daily_return_pct": float(
                    (equity - self._day_start_equity) / self._day_start_equity * 100
                ) if self._day_start_equity else 0,
                "positions_count": len(positions),
            }

            for callback in self._callbacks:
                try:
                    await callback(update_data)
                except Exception as e:
                    logger.error("callback_error", error=str(e))

            self._last_equity = equity

        except Exception as e:
            logger.error("risk_check_error", error=str(e))

    async def get_current_status(self) -> dict:
        """获取当前状态"""
        try:
            account = await self.alpaca.get_account()
            positions = await self.alpaca.get_positions()
            clock = await self.alpaca.get_clock()

            equity = account["equity"]

            # 计算日收益
            daily_pnl = Decimal("0")
            daily_return_pct = Decimal("0")
            if self._day_start_equity and self._day_start_equity > 0:
                daily_pnl = equity - self._day_start_equity
                daily_return_pct = daily_pnl / self._day_start_equity * 100

            # 计算回撤
            drawdown = Decimal("0")
            if self._peak_equity and self._peak_equity > 0:
                drawdown = (self._peak_equity - equity) / self._peak_equity * 100

            # 持仓统计
            long_count = sum(1 for p in positions if p.side == "long")
            short_count = sum(1 for p in positions if p.side == "short")

            total_unrealized_pnl = sum(p.unrealized_pl for p in positions)

            return {
                "timestamp": datetime.now().isoformat(),
                "market": {
                    "is_open": clock["is_open"],
                    "next_open": clock["next_open"],
                    "next_close": clock["next_close"],
                },
                "account": {
                    "equity": float(equity),
                    "cash": float(account["cash"]),
                    "buying_power": float(account["buying_power"]),
                    "portfolio_value": float(account["portfolio_value"]),
                },
                "performance": {
                    "daily_pnl": float(daily_pnl),
                    "daily_return_pct": float(daily_return_pct),
                    "unrealized_pnl": float(total_unrealized_pnl),
                    "drawdown_pct": float(drawdown),
                },
                "positions": {
                    "total": len(positions),
                    "long": long_count,
                    "short": short_count,
                },
                "monitoring": {
                    "is_running": self._running,
                    "peak_equity": float(self._peak_equity) if self._peak_equity else None,
                },
            }

        except Exception as e:
            logger.error("get_status_error", error=str(e))
            return {"error": str(e)}

    async def get_positions_detail(self) -> list[dict]:
        """获取持仓详情"""
        try:
            positions = await self.alpaca.get_positions()
            account = await self.alpaca.get_account()
            portfolio_value = account["portfolio_value"]

            result = []
            for pos in positions:
                weight = abs(pos.market_value) / portfolio_value if portfolio_value > 0 else 0

                result.append({
                    "symbol": pos.symbol,
                    "side": pos.side,
                    "quantity": float(pos.quantity),
                    "avg_entry_price": float(pos.avg_entry_price),
                    "current_price": float(pos.current_price),
                    "market_value": float(pos.market_value),
                    "cost_basis": float(pos.cost_basis),
                    "unrealized_pnl": float(pos.unrealized_pl),
                    "unrealized_pnl_pct": float(pos.unrealized_plpc) * 100,
                    "weight_pct": float(weight) * 100,
                    "exchange": pos.exchange,
                })

            # 按市值排序
            result.sort(key=lambda x: abs(x["market_value"]), reverse=True)

            return result

        except Exception as e:
            logger.error("get_positions_error", error=str(e))
            return []


# 全局服务实例
realtime_monitor = RealtimeMonitorService()
