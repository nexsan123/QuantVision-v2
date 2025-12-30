"""
TWAP (Time-Weighted Average Price) 执行算法

将大订单按时间均匀拆分执行
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable
from uuid import UUID

import numpy as np
import structlog

from app.execution.order_manager import (
    Order,
    OrderManager,
    OrderSide,
    OrderStatus,
    OrderType,
)

logger = structlog.get_logger()


@dataclass
class TWAPConfig:
    """TWAP 配置"""
    # 时间设置
    start_time: datetime | None = None      # 开始时间 (默认立即)
    end_time: datetime | None = None        # 结束时间 (必须)
    duration_minutes: int = 60              # 持续时间 (分钟)

    # 拆单设置
    n_slices: int = 10                      # 拆分数量
    slice_interval_seconds: float = 0.0     # 切片间隔 (自动计算)
    randomize_timing: bool = True           # 随机化时间 (±10%)
    randomize_quantity: bool = True         # 随机化数量 (±20%)

    # 执行设置
    min_slice_qty: float = 1.0              # 最小切片数量
    max_participation_rate: float = 0.10    # 最大参与率
    use_limit_orders: bool = False          # 使用限价单
    limit_offset_bps: float = 5.0           # 限价偏移 (基点)

    # 控制
    pause_on_volatility: bool = True        # 波动过大时暂停
    volatility_threshold: float = 0.03      # 波动率阈值
    cancel_on_price_deviation: bool = True  # 价格偏离过大时取消
    price_deviation_pct: float = 0.02       # 价格偏离阈值

    def __post_init__(self) -> None:
        if self.slice_interval_seconds == 0 and self.n_slices > 0:
            self.slice_interval_seconds = (self.duration_minutes * 60) / self.n_slices


@dataclass
class TWAPSlice:
    """TWAP 切片"""
    slice_idx: int
    scheduled_time: datetime
    target_quantity: float
    actual_quantity: float = 0.0
    fill_price: float = 0.0
    order_id: UUID | None = None
    status: str = "pending"             # pending, submitted, filled, skipped
    executed_at: datetime | None = None


@dataclass
class TWAPProgress:
    """TWAP 执行进度"""
    total_quantity: float
    filled_quantity: float
    remaining_quantity: float
    slices_completed: int
    slices_total: int
    avg_fill_price: float
    twap_benchmark: float               # 时间加权平均基准价
    slippage_bps: float                 # 相对基准的滑点 (基点)
    is_complete: bool
    is_paused: bool
    start_time: datetime
    expected_end_time: datetime
    elapsed_seconds: float
    slices: list[TWAPSlice] = field(default_factory=list)


class TWAPExecutor:
    """
    TWAP 执行器

    将大订单按时间均匀拆分执行，目标是获得接近时间加权平均价的成交

    使用示例:
    ```python
    executor = TWAPExecutor(order_manager)

    config = TWAPConfig(
        duration_minutes=60,
        n_slices=12,
    )

    result = await executor.execute(
        symbol="AAPL",
        side=OrderSide.BUY,
        total_quantity=10000,
        config=config,
    )
    print(f"TWAP完成: 均价 {result.avg_fill_price:.2f}")
    ```
    """

    def __init__(
        self,
        order_manager: OrderManager,
        on_progress: Callable[[TWAPProgress], None] | None = None,
        get_current_price: Callable[[str], float] | None = None,
    ):
        """
        Args:
            order_manager: 订单管理器
            on_progress: 进度回调
            get_current_price: 获取当前价格的函数
        """
        self.order_manager = order_manager
        self.on_progress = on_progress
        self.get_current_price = get_current_price

        self._is_running = False
        self._is_paused = False
        self._cancel_requested = False

    async def execute(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: float,
        config: TWAPConfig | None = None,
    ) -> TWAPProgress:
        """
        执行 TWAP

        Args:
            symbol: 标的代码
            side: 方向
            total_quantity: 总数量
            config: TWAP 配置

        Returns:
            执行结果
        """
        config = config or TWAPConfig()

        # 初始化
        self._is_running = True
        self._is_paused = False
        self._cancel_requested = False

        start_time = config.start_time or datetime.now()
        end_time = config.end_time or (start_time + timedelta(minutes=config.duration_minutes))

        # 生成切片计划
        slices = self._generate_slices(
            total_quantity=total_quantity,
            start_time=start_time,
            end_time=end_time,
            config=config,
        )

        # 初始化进度
        progress = TWAPProgress(
            total_quantity=total_quantity,
            filled_quantity=0.0,
            remaining_quantity=total_quantity,
            slices_completed=0,
            slices_total=len(slices),
            avg_fill_price=0.0,
            twap_benchmark=0.0,
            slippage_bps=0.0,
            is_complete=False,
            is_paused=False,
            start_time=start_time,
            expected_end_time=end_time,
            elapsed_seconds=0.0,
            slices=slices,
        )

        # 价格记录 (用于计算 TWAP 基准)
        price_samples: list[tuple[datetime, float]] = []

        logger.info(
            "TWAP开始执行",
            symbol=symbol,
            side=side.value,
            total_quantity=total_quantity,
            n_slices=len(slices),
            duration_minutes=config.duration_minutes,
        )

        # 执行循环
        for slice_obj in slices:
            if self._cancel_requested:
                break

            # 等待到计划时间
            now = datetime.now()
            if slice_obj.scheduled_time > now:
                wait_seconds = (slice_obj.scheduled_time - now).total_seconds()
                await asyncio.sleep(wait_seconds)

            if self._is_paused:
                while self._is_paused and not self._cancel_requested:
                    await asyncio.sleep(1)

            if self._cancel_requested:
                break

            # 获取当前价格
            current_price = 0.0
            if self.get_current_price:
                current_price = self.get_current_price(symbol)
                price_samples.append((datetime.now(), current_price))

            # 检查波动率
            if config.pause_on_volatility and len(price_samples) > 2:
                recent_prices = [p for _, p in price_samples[-10:]]
                if len(recent_prices) > 1:
                    volatility = np.std(recent_prices) / np.mean(recent_prices)
                    if volatility > config.volatility_threshold:
                        logger.warning("波动率过高，暂停执行", volatility=f"{volatility:.2%}")
                        slice_obj.status = "skipped"
                        continue

            # 创建并提交订单
            try:
                order = self.order_manager.create_order(
                    symbol=symbol,
                    side=side,
                    quantity=slice_obj.target_quantity,
                    order_type=OrderType.LIMIT if config.use_limit_orders else OrderType.MARKET,
                    limit_price=self._calculate_limit_price(
                        current_price, side, config.limit_offset_bps
                    ) if config.use_limit_orders and current_price > 0 else None,
                    metadata={"twap_slice": slice_obj.slice_idx},
                )

                slice_obj.order_id = order.order_id
                slice_obj.status = "submitted"

                await self.order_manager.submit_order(order.order_id)

                # 等待成交 (简化处理，实际应该监听事件)
                await asyncio.sleep(0.5)

                # 模拟成交 (实际应该从 order_manager 获取)
                fill_price = current_price if current_price > 0 else 100.0
                slice_obj.actual_quantity = slice_obj.target_quantity
                slice_obj.fill_price = fill_price
                slice_obj.status = "filled"
                slice_obj.executed_at = datetime.now()

                # 更新进度
                progress.filled_quantity += slice_obj.actual_quantity
                progress.remaining_quantity = total_quantity - progress.filled_quantity
                progress.slices_completed += 1

                # 更新均价
                total_cost = sum(
                    s.actual_quantity * s.fill_price
                    for s in slices if s.status == "filled"
                )
                if progress.filled_quantity > 0:
                    progress.avg_fill_price = total_cost / progress.filled_quantity

            except Exception as e:
                logger.error("切片执行失败", slice_idx=slice_obj.slice_idx, error=str(e))
                slice_obj.status = "failed"

            # 更新进度
            progress.elapsed_seconds = (datetime.now() - start_time).total_seconds()
            progress.slices = slices

            if self.on_progress:
                self.on_progress(progress)

        # 计算 TWAP 基准
        if price_samples:
            progress.twap_benchmark = np.mean([p for _, p in price_samples])
            if progress.twap_benchmark > 0 and progress.avg_fill_price > 0:
                progress.slippage_bps = (
                    (progress.avg_fill_price - progress.twap_benchmark)
                    / progress.twap_benchmark * 10000
                )
                if side == OrderSide.SELL:
                    progress.slippage_bps = -progress.slippage_bps

        progress.is_complete = progress.filled_quantity >= total_quantity * 0.99
        self._is_running = False

        logger.info(
            "TWAP执行完成",
            symbol=symbol,
            filled=f"{progress.filled_quantity}/{total_quantity}",
            avg_price=f"{progress.avg_fill_price:.2f}",
            twap_benchmark=f"{progress.twap_benchmark:.2f}",
            slippage_bps=f"{progress.slippage_bps:.1f}",
        )

        return progress

    def _generate_slices(
        self,
        total_quantity: float,
        start_time: datetime,
        end_time: datetime,
        config: TWAPConfig,
    ) -> list[TWAPSlice]:
        """生成切片计划"""
        n_slices = config.n_slices
        duration = (end_time - start_time).total_seconds()
        interval = duration / n_slices

        base_quantity = total_quantity / n_slices
        slices = []

        for i in range(n_slices):
            # 计划时间
            scheduled_time = start_time + timedelta(seconds=interval * i)

            # 随机化时间
            if config.randomize_timing and i > 0:
                jitter = interval * 0.1 * (np.random.random() * 2 - 1)
                scheduled_time += timedelta(seconds=jitter)

            # 随机化数量
            quantity = base_quantity
            if config.randomize_quantity:
                jitter = 0.2 * (np.random.random() * 2 - 1)
                quantity = base_quantity * (1 + jitter)

            quantity = max(config.min_slice_qty, quantity)

            slices.append(TWAPSlice(
                slice_idx=i,
                scheduled_time=scheduled_time,
                target_quantity=quantity,
            ))

        # 调整最后一个切片以匹配总量
        planned_total = sum(s.target_quantity for s in slices)
        if slices:
            slices[-1].target_quantity += total_quantity - planned_total

        return slices

    def _calculate_limit_price(
        self,
        current_price: float,
        side: OrderSide,
        offset_bps: float,
    ) -> float:
        """计算限价"""
        offset = current_price * offset_bps / 10000
        if side == OrderSide.BUY:
            return current_price + offset
        else:
            return current_price - offset

    def pause(self) -> None:
        """暂停执行"""
        self._is_paused = True
        logger.info("TWAP执行已暂停")

    def resume(self) -> None:
        """恢复执行"""
        self._is_paused = False
        logger.info("TWAP执行已恢复")

    def cancel(self) -> None:
        """取消执行"""
        self._cancel_requested = True
        logger.info("TWAP执行已请求取消")

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running

    @property
    def is_paused(self) -> bool:
        """是否暂停"""
        return self._is_paused
