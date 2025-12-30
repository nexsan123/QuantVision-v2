"""
VWAP (Volume-Weighted Average Price) 执行算法

根据历史成交量分布拆分订单，目标是获得接近成交量加权平均价的成交
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Any, Callable
from uuid import UUID

import numpy as np
import pandas as pd
import structlog

from app.execution.order_manager import (
    Order,
    OrderManager,
    OrderSide,
    OrderType,
)

logger = structlog.get_logger()


# 典型的美股日内成交量分布 (按30分钟划分)
DEFAULT_VOLUME_PROFILE = {
    time(9, 30): 0.08,   # 开盘高峰
    time(10, 0): 0.06,
    time(10, 30): 0.05,
    time(11, 0): 0.04,
    time(11, 30): 0.04,
    time(12, 0): 0.03,   # 午间低谷
    time(12, 30): 0.03,
    time(13, 0): 0.04,
    time(13, 30): 0.05,
    time(14, 0): 0.05,
    time(14, 30): 0.06,
    time(15, 0): 0.07,
    time(15, 30): 0.10,  # 收盘高峰
}


@dataclass
class VWAPConfig:
    """VWAP 配置"""
    # 时间设置
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_minutes: int = 60

    # 成交量分布
    volume_profile: dict[time, float] | None = None  # 自定义分布
    use_historical_profile: bool = True     # 使用历史分布
    lookback_days: int = 20                 # 历史回看天数

    # 执行设置
    min_slice_qty: float = 1.0
    max_participation_rate: float = 0.10    # 最大参与率
    adapt_to_market: bool = True            # 根据实际成交量调整
    urgency_factor: float = 1.0             # 紧迫度因子 (>1 更激进)

    # 限价设置
    use_limit_orders: bool = True
    limit_offset_bps: float = 3.0
    aggressive_limit_bps: float = 10.0      # 激进限价偏移


@dataclass
class VWAPSlice:
    """VWAP 切片"""
    slice_idx: int
    start_time: datetime
    end_time: datetime
    target_pct: float                       # 目标占比
    target_quantity: float
    actual_quantity: float = 0.0
    fill_price: float = 0.0
    market_volume: float = 0.0              # 区间市场成交量
    participation_rate: float = 0.0         # 实际参与率
    status: str = "pending"


@dataclass
class VWAPProgress:
    """VWAP 执行进度"""
    total_quantity: float
    filled_quantity: float
    remaining_quantity: float
    slices_completed: int
    slices_total: int
    avg_fill_price: float
    vwap_benchmark: float                   # 成交量加权平均基准价
    slippage_bps: float
    participation_rate: float               # 整体参与率
    is_complete: bool
    is_behind_schedule: bool                # 是否落后于计划
    slices: list[VWAPSlice] = field(default_factory=list)


class VWAPExecutor:
    """
    VWAP 执行器

    根据成交量分布拆分订单，目标是匹配 VWAP

    使用示例:
    ```python
    executor = VWAPExecutor(order_manager)

    config = VWAPConfig(
        duration_minutes=120,
        max_participation_rate=0.05,
    )

    result = await executor.execute(
        symbol="AAPL",
        side=OrderSide.BUY,
        total_quantity=50000,
        config=config,
    )
    ```
    """

    def __init__(
        self,
        order_manager: OrderManager,
        on_progress: Callable[[VWAPProgress], None] | None = None,
        get_current_price: Callable[[str], float] | None = None,
        get_market_volume: Callable[[str], float] | None = None,
    ):
        """
        Args:
            order_manager: 订单管理器
            on_progress: 进度回调
            get_current_price: 获取当前价格
            get_market_volume: 获取市场成交量
        """
        self.order_manager = order_manager
        self.on_progress = on_progress
        self.get_current_price = get_current_price
        self.get_market_volume = get_market_volume

        self._is_running = False
        self._is_paused = False
        self._cancel_requested = False

    async def execute(
        self,
        symbol: str,
        side: OrderSide,
        total_quantity: float,
        config: VWAPConfig | None = None,
        historical_volume: pd.DataFrame | None = None,
    ) -> VWAPProgress:
        """
        执行 VWAP

        Args:
            symbol: 标的代码
            side: 方向
            total_quantity: 总数量
            config: VWAP 配置
            historical_volume: 历史成交量数据

        Returns:
            执行结果
        """
        config = config or VWAPConfig()

        self._is_running = True
        self._is_paused = False
        self._cancel_requested = False

        start_time = config.start_time or datetime.now()
        end_time = config.end_time or (start_time + timedelta(minutes=config.duration_minutes))

        # 获取成交量分布
        volume_profile = self._get_volume_profile(
            config=config,
            historical_volume=historical_volume,
            start_time=start_time,
            end_time=end_time,
        )

        # 生成切片计划
        slices = self._generate_slices(
            total_quantity=total_quantity,
            start_time=start_time,
            end_time=end_time,
            volume_profile=volume_profile,
            config=config,
        )

        # 初始化进度
        progress = VWAPProgress(
            total_quantity=total_quantity,
            filled_quantity=0.0,
            remaining_quantity=total_quantity,
            slices_completed=0,
            slices_total=len(slices),
            avg_fill_price=0.0,
            vwap_benchmark=0.0,
            slippage_bps=0.0,
            participation_rate=0.0,
            is_complete=False,
            is_behind_schedule=False,
            slices=slices,
        )

        # 价格和成交量记录
        price_volume_samples: list[tuple[float, float]] = []  # (price, volume)

        logger.info(
            "VWAP开始执行",
            symbol=symbol,
            side=side.value,
            total_quantity=total_quantity,
            n_slices=len(slices),
        )

        # 执行循环
        for slice_obj in slices:
            if self._cancel_requested:
                break

            # 等待到切片开始时间
            now = datetime.now()
            if slice_obj.start_time > now:
                await asyncio.sleep((slice_obj.start_time - now).total_seconds())

            if self._is_paused:
                while self._is_paused and not self._cancel_requested:
                    await asyncio.sleep(1)

            if self._cancel_requested:
                break

            # 获取市场数据
            current_price = 0.0
            market_volume = 0.0

            if self.get_current_price:
                current_price = self.get_current_price(symbol)

            if self.get_market_volume:
                market_volume = self.get_market_volume(symbol)

            slice_obj.market_volume = market_volume

            # 根据市场成交量调整数量
            adjusted_quantity = slice_obj.target_quantity
            if config.adapt_to_market and market_volume > 0:
                max_qty = market_volume * config.max_participation_rate
                adjusted_quantity = min(adjusted_quantity, max_qty)
                adjusted_quantity = max(adjusted_quantity, config.min_slice_qty)

            # 检查是否落后于计划
            expected_filled = sum(s.target_quantity for s in slices[:slice_obj.slice_idx + 1])
            if progress.filled_quantity < expected_filled * 0.8:
                progress.is_behind_schedule = True
                # 激进追赶
                adjusted_quantity *= config.urgency_factor

            # 执行切片
            try:
                limit_offset = config.limit_offset_bps
                if progress.is_behind_schedule:
                    limit_offset = config.aggressive_limit_bps

                order = self.order_manager.create_order(
                    symbol=symbol,
                    side=side,
                    quantity=adjusted_quantity,
                    order_type=OrderType.LIMIT if config.use_limit_orders else OrderType.MARKET,
                    limit_price=self._calculate_limit_price(
                        current_price, side, limit_offset
                    ) if config.use_limit_orders and current_price > 0 else None,
                    metadata={"vwap_slice": slice_obj.slice_idx},
                )

                await self.order_manager.submit_order(order.order_id)
                await asyncio.sleep(0.5)

                # 模拟成交
                fill_price = current_price if current_price > 0 else 100.0
                slice_obj.actual_quantity = adjusted_quantity
                slice_obj.fill_price = fill_price
                slice_obj.status = "filled"

                if market_volume > 0:
                    slice_obj.participation_rate = adjusted_quantity / market_volume

                # 记录用于 VWAP 计算
                if fill_price > 0:
                    price_volume_samples.append((fill_price, adjusted_quantity))

                # 更新进度
                progress.filled_quantity += slice_obj.actual_quantity
                progress.remaining_quantity = total_quantity - progress.filled_quantity
                progress.slices_completed += 1

            except Exception as e:
                logger.error("VWAP切片失败", slice_idx=slice_obj.slice_idx, error=str(e))
                slice_obj.status = "failed"

            # 更新均价和 VWAP
            if price_volume_samples:
                total_cost = sum(p * v for p, v in price_volume_samples)
                total_vol = sum(v for _, v in price_volume_samples)
                if total_vol > 0:
                    progress.avg_fill_price = total_cost / total_vol
                    progress.vwap_benchmark = progress.avg_fill_price  # 简化: 假设我们就是 VWAP

            progress.slices = slices

            if self.on_progress:
                self.on_progress(progress)

        # 最终计算
        total_market_volume = sum(s.market_volume for s in slices if s.market_volume > 0)
        if total_market_volume > 0:
            progress.participation_rate = progress.filled_quantity / total_market_volume

        progress.is_complete = progress.filled_quantity >= total_quantity * 0.99
        self._is_running = False

        logger.info(
            "VWAP执行完成",
            symbol=symbol,
            filled=f"{progress.filled_quantity}/{total_quantity}",
            avg_price=f"{progress.avg_fill_price:.2f}",
            participation_rate=f"{progress.participation_rate:.2%}",
        )

        return progress

    def _get_volume_profile(
        self,
        config: VWAPConfig,
        historical_volume: pd.DataFrame | None,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[time, float]:
        """获取成交量分布"""
        if config.volume_profile:
            return config.volume_profile

        if historical_volume is not None and config.use_historical_profile:
            # 从历史数据计算分布
            return self._calculate_historical_profile(historical_volume)

        # 使用默认分布
        return DEFAULT_VOLUME_PROFILE

    def _calculate_historical_profile(
        self, volume_data: pd.DataFrame
    ) -> dict[time, float]:
        """从历史数据计算成交量分布"""
        # 假设 volume_data 有 'time' 和 'volume' 列
        if "time" not in volume_data.columns or "volume" not in volume_data.columns:
            return DEFAULT_VOLUME_PROFILE

        # 按时间段聚合
        profile = volume_data.groupby("time")["volume"].mean()
        total = profile.sum()

        if total == 0:
            return DEFAULT_VOLUME_PROFILE

        return {t: v / total for t, v in profile.items()}

    def _generate_slices(
        self,
        total_quantity: float,
        start_time: datetime,
        end_time: datetime,
        volume_profile: dict[time, float],
        config: VWAPConfig,
    ) -> list[VWAPSlice]:
        """根据成交量分布生成切片"""
        duration = (end_time - start_time).total_seconds()

        # 计算每个时间段的比例
        slices = []
        current_time = start_time

        # 按30分钟切分
        slice_duration = timedelta(minutes=30)
        slice_idx = 0

        while current_time < end_time:
            slice_end = min(current_time + slice_duration, end_time)

            # 查找对应的成交量比例
            slot_time = current_time.time()
            # 找到最接近的时间槽
            closest_slot = min(
                volume_profile.keys(),
                key=lambda t: abs(
                    (datetime.combine(datetime.today(), t) - datetime.combine(datetime.today(), slot_time)).total_seconds()
                )
            )
            volume_pct = volume_profile.get(closest_slot, 0.05)

            slices.append(VWAPSlice(
                slice_idx=slice_idx,
                start_time=current_time,
                end_time=slice_end,
                target_pct=volume_pct,
                target_quantity=total_quantity * volume_pct,
            ))

            current_time = slice_end
            slice_idx += 1

        # 归一化以匹配总量
        total_target = sum(s.target_quantity for s in slices)
        if total_target > 0:
            for s in slices:
                s.target_quantity = s.target_quantity / total_target * total_quantity
                s.target_quantity = max(config.min_slice_qty, s.target_quantity)

        return slices

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

    def resume(self) -> None:
        """恢复"""
        self._is_paused = False

    def cancel(self) -> None:
        """取消"""
        self._cancel_requested = True
