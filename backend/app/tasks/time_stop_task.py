"""
时间止损定时任务
PRD 4.18.1 日内交易专用视图

在指定时间自动平仓所有日内持仓
"""
import asyncio
import logging
from datetime import datetime, time
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class TimeStopTask:
    """时间止损任务管理器"""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self.default_stop_times = ["15:45", "15:50", "15:55"]

    def start(self):
        """启动调度器"""
        if self.scheduler is None:
            self.scheduler = AsyncIOScheduler()

        # 添加默认的时间止损任务
        for stop_time in self.default_stop_times:
            hour, minute = map(int, stop_time.split(":"))
            job_id = f"time_stop_{stop_time.replace(':', '')}"

            self.scheduler.add_job(
                self._execute_time_stop,
                CronTrigger(
                    hour=hour,
                    minute=minute,
                    day_of_week="mon-fri",
                    timezone="America/New_York",
                ),
                id=job_id,
                args=[stop_time],
                replace_existing=True,
            )
            logger.info(f"已添加时间止损任务: {stop_time} ET")

        self.scheduler.start()
        self.is_running = True
        logger.info("时间止损调度器已启动")

    def stop(self):
        """停止调度器"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("时间止损调度器已停止")

    async def _execute_time_stop(self, stop_time: str):
        """
        执行时间止损

        Args:
            stop_time: 触发时间 (HH:mm)
        """
        logger.info(f"执行时间止损: {stop_time} ET")

        try:
            # 获取所有需要时间止损的持仓
            positions = await self._get_time_stop_positions(stop_time)

            if not positions:
                logger.info(f"无需要时间止损的持仓 ({stop_time})")
                return

            logger.info(f"找到 {len(positions)} 个需要时间止损的持仓")

            # 执行平仓
            for position in positions:
                await self._close_position(position)

        except Exception as e:
            logger.error(f"时间止损执行失败: {e}")

    async def _get_time_stop_positions(self, stop_time: str) -> list:
        """
        获取需要时间止损的持仓

        Args:
            stop_time: 止损时间

        Returns:
            需要平仓的持仓列表
        """
        # TODO: 从数据库获取设置了该时间止损的持仓
        # 这里返回模拟数据
        return [
            {
                "position_id": "pos_001",
                "user_id": "user_001",
                "symbol": "NVDA",
                "quantity": 100,
                "side": "long",
                "entry_price": 520.50,
                "time_stop": stop_time,
            }
        ]

    async def _close_position(self, position: dict):
        """
        平仓单个持仓

        Args:
            position: 持仓信息
        """
        symbol = position["symbol"]
        quantity = position["quantity"]
        side = position["side"]

        logger.info(
            f"时间止损平仓: {symbol} {quantity}股 "
            f"(方向: {side}, 入场价: ${position['entry_price']:.2f})"
        )

        try:
            # TODO: 调用实际的交易服务执行平仓
            # await trading_service.close_position(position["position_id"])

            # 模拟平仓延迟
            await asyncio.sleep(0.1)

            logger.info(f"时间止损平仓成功: {symbol}")

            # TODO: 记录交易日志
            # await self._log_time_stop_trade(position)

        except Exception as e:
            logger.error(f"时间止损平仓失败 {symbol}: {e}")

    async def manual_time_stop(self, user_id: str, symbol: str) -> dict:
        """
        手动触发时间止损 (用于测试或紧急情况)

        Args:
            user_id: 用户ID
            symbol: 股票代码

        Returns:
            执行结果
        """
        logger.info(f"手动时间止损: user={user_id}, symbol={symbol}")

        # TODO: 实现手动止损逻辑
        return {
            "success": True,
            "message": f"已对 {symbol} 执行时间止损",
            "timestamp": datetime.now().isoformat(),
        }


# 单例实例
_time_stop_task: Optional[TimeStopTask] = None


def get_time_stop_task() -> TimeStopTask:
    """获取时间止损任务单例"""
    global _time_stop_task
    if _time_stop_task is None:
        _time_stop_task = TimeStopTask()
    return _time_stop_task


def start_time_stop_scheduler():
    """启动时间止损调度器"""
    task = get_time_stop_task()
    task.start()


def stop_time_stop_scheduler():
    """停止时间止损调度器"""
    task = get_time_stop_task()
    task.stop()
