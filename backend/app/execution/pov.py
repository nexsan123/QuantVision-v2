"""
POV (Percentage of Volume) 执行算法

按市场成交量的固定比例执行，控制市场影响
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable
from uuid import UUID

import numpy as np
import structlog

from app.execution.order_manager import (
    OrderManager,
    OrderSide,
    OrderType,
)

logger = structlog.get_logger()


@dataclass
class POVConfig:
    """POV 配置"""
    # 参与率
    target_rate: float = 0.05               # 目标参与率 (5%)
    min_rate: float = 0.01                  # 最小参与率
    max_rate: float = 0.20                  # 最大参与率

    # 时间设置
    start_time: datetime | None = None
    end_time: datetime | None = None
    max_duration_minutes: int = 240         # 最大执行时间

    # 采样
    sample_interval_seconds: float = 30.0   # 成交量采样间隔
    volume_lookback_seconds: float = 60.0   # 成交量回看窗口

    # 执行
    min_order_qty: float = 1.0
    use_limit_orders: bool = True
    limit_offset_bps: float = 5.0

    # 自适应
    adaptive_rate: bool = True              # 根据市场流动性调整
    spread_threshold_bps: float = 20.0      # 价差阈值 (超过则降低参与率)


@dataclass
class POVProgress:
    """POV 执行进度"""
    total_quantity: float
    filled_quantity: float
    remaining_quantity: float
    target_rate: float
    actual_rate: float                      # 实际参与率
    avg_fill_price: float
    market_volume: float                    # 累计市场成交量
    elapsed_seconds: float
    is_complete: bool
    is_rate_adjusted: bool                  # 参与率是否被调整


class POVExecutor:
    """
    POV 执行器

    按市场成交量的固定比例执行，最小化市场冲击

    使用示例:
    ```python
    executor = POVExecutor(order_manager)

    config = POVConfig(
        target_rate=0.05,  # 5% 参与率
        max_duration_minutes=120,
    )

    result = await executor.execute(
        symbol="AAPL",
        side=OrderSide.BUY,
        total_quantity=100000,
        config=config,
    )
    ```
    """

    def __init__(
        self,
        order_manager: OrderManager,
        on_progress: Callable[[POVProgress], None] | None = None,
        get_current_price: Callable[[str], float] | None = None,
        get_market_volume: Callable[[str, float], float] | None = None,
        get_spread: Callable[[str], float] | None = None,
    ):
        """
        Args:
            order_manager: 订单管理器
            on_progress: 进度回调
            get_current_price: 获取当前价格
            get_market_volume: 获取区间成交量 (symbol, seconds)
            get_spread: 获取买卖价差 (bps)
        """
        self.order_manager = order_manager
        self.on_progress = on_progress
        self.get_current_price = get_current_price
        self.get_market_volume = get_market_volume
        self.get_spread = get_spread

        self._is_running = False
        self._is_paused = False
        self._cancel_requested = False

    async def execute(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: float,
        config: POVConfig | None = None,
    ) -> POVProgress:
        """
        执行 POV

        Args:
            symbol: 标的代码
            side: 方向
            total_quantity: 总数量
            config: POV 配置

        Returns:
            执行结果
        """
        config = config or POVConfig()

        self._is_running = True
        self._is_paused = False
        self._cancel_requested = False

        start_time = config.start_time or datetime.now()
        end_time = config.end_time or (start_time + timedelta(minutes=config.max_duration_minutes))

        # 初始化进度
        progress = POVProgress(
            total_quantity=total_quantity,
            filled_quantity=0.0,
            remaining_quantity=total_quantity,
            target_rate=config.target_rate,
            actual_rate=0.0,
            avg_fill_price=0.0,
            market_volume=0.0,
            elapsed_seconds=0.0,
            is_complete=False,
            is_rate_adjusted=False,
        )

        total_cost = 0.0
        cumulative_market_volume = 0.0
        last_sample_time = datetime.now()

        logger.info(
            "POV开始执行",
            symbol=symbol,
            side=side.value,
            total_quantity=total_quantity,
            target_rate=f"{config.target_rate:.1%}",
        )

        while progress.remaining_quantity > config.min_order_qty:
            if self._cancel_requested:
                break

            if datetime.now() > end_time:
                logger.warning("POV达到最大执行时间")
                break

            if self._is_paused:
                while self._is_paused and not self._cancel_requested:
                    await asyncio.sleep(1)

            # 等待采样间隔
            await asyncio.sleep(config.sample_interval_seconds)

            # 获取区间成交量
            interval_volume = 0.0
            if self.get_market_volume:
                interval_volume = self.get_market_volume(symbol, config.volume_lookback_seconds)
            else:
                # 模拟成交量 (约 1000 股/分钟)
                interval_volume = 1000 * config.sample_interval_seconds / 60

            cumulative_market_volume += interval_volume
            progress.market_volume = cumulative_market_volume

            # 确定参与率
            current_rate = config.target_rate

            # 自适应调整
            if config.adaptive_rate:
                # 根据价差调整
                if self.get_spread:
                    spread_bps = self.get_spread(symbol)
                    if spread_bps > config.spread_threshold_bps:
                        # 价差过大，降低参与率
                        rate_reduction = (spread_bps - config.spread_threshold_bps) / 100
                        current_rate = max(config.min_rate, current_rate * (1 - rate_reduction))
                        progress.is_rate_adjusted = True

                # 如果落后于计划，提高参与率
                expected_filled = cumulative_market_volume * config.target_rate
                if progress.filled_quantity < expected_filled * 0.8:
                    current_rate = min(config.max_rate, current_rate * 1.5)
                    progress.is_rate_adjusted = True

            # 计算本次订单数量
            order_quantity = interval_volume * current_rate
            order_quantity = min(order_quantity, progress.remaining_quantity)
            order_quantity = max(order_quantity, config.min_order_qty)

            if order_quantity < config.min_order_qty:
                continue

            # 获取价格
            current_price = 100.0
            if self.get_current_price:
                current_price = self.get_current_price(symbol)

            # 执行订单
            try:
                order = self.order_manager.create_order(
                    symbol=symbol,
                    side=side,
                    quantity=order_quantity,
                    order_type=OrderType.LIMIT if config.use_limit_orders else OrderType.MARKET,
                    limit_price=self._calculate_limit_price(
                        current_price, side, config.limit_offset_bps
                    ) if config.use_limit_orders else None,
                    metadata={"pov_execution": True},
                )

                await self.order_manager.submit_order(order.order_id)

                # 模拟成交
                fill_price = current_price
                progress.filled_quantity += order_quantity
                progress.remaining_quantity = total_quantity - progress.filled_quantity
                total_cost += order_quantity * fill_price

                if progress.filled_quantity > 0:
                    progress.avg_fill_price = total_cost / progress.filled_quantity

            except Exception as e:
                logger.error("POV订单失败", error=str(e))

            # 更新进度
            progress.elapsed_seconds = (datetime.now() - start_time).total_seconds()
            if cumulative_market_volume > 0:
                progress.actual_rate = progress.filled_quantity / cumulative_market_volume

            if self.on_progress:
                self.on_progress(progress)

        progress.is_complete = progress.remaining_quantity < config.min_order_qty
        self._is_running = False

        logger.info(
            "POV执行完成",
            symbol=symbol,
            filled=f"{progress.filled_quantity}/{total_quantity}",
            avg_price=f"{progress.avg_fill_price:.2f}",
            actual_rate=f"{progress.actual_rate:.2%}",
            elapsed_minutes=f"{progress.elapsed_seconds / 60:.1f}",
        )

        return progress

    def _calculate_limit_price(
        self, current_price: float, side: OrderSide, offset_bps: float
    ) -> float:
        """计算限价"""
        offset = current_price * offset_bps / 10000
        if side == OrderSide.BUY:
            return current_price + offset
        return current_price - offset

    def pause(self) -> None:
        """暂停"""
        self._is_paused = True
        logger.info("POV已暂停")

    def resume(self) -> None:
        """恢复"""
        self._is_paused = False
        logger.info("POV已恢复")

    def cancel(self) -> None:
        """取消"""
        self._cancel_requested = True
        logger.info("POV已请求取消")

    @property
    def is_running(self) -> bool:
        return self._is_running


def estimate_completion_time(
    quantity: float,
    target_rate: float,
    avg_volume_per_minute: float,
) -> float:
    """
    估算完成时间

    Args:
        quantity: 总数量
        target_rate: 目标参与率
        avg_volume_per_minute: 平均每分钟成交量

    Returns:
        预计完成时间 (分钟)
    """
    if target_rate <= 0 or avg_volume_per_minute <= 0:
        return float("inf")

    volume_per_minute = avg_volume_per_minute * target_rate
    return quantity / volume_per_minute
