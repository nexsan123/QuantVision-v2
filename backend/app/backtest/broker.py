"""
模拟券商

提供:
- 订单执行
- 滑点模型
- 手续费计算
- 交易记录
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


class OrderSide(str, Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """订单"""
    symbol: str
    side: OrderSide
    quantity: int
    price: float
    order_type: OrderType = OrderType.MARKET
    limit_price: float | None = None
    stop_price: float | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Fill:
    """成交记录"""
    order: Order
    fill_price: float
    quantity: int
    commission: float
    slippage: float
    filled_at: datetime = field(default_factory=datetime.now)

    @property
    def total_cost(self) -> float:
        """总成本 (含手续费和滑点)"""
        return self.fill_price * self.quantity + self.commission


class SlippageModel:
    """滑点模型基类"""

    def calculate(
        self,
        price: float,
        quantity: int,
        volume: float | None,
        side: OrderSide,
    ) -> float:
        """
        计算滑点

        Args:
            price: 当前价格
            quantity: 交易数量
            volume: 当日成交量
            side: 交易方向

        Returns:
            滑点金额 (正值表示不利滑点)
        """
        raise NotImplementedError


class FixedSlippage(SlippageModel):
    """
    固定比例滑点

    滑点 = 价格 * 固定比例
    """

    def __init__(self, rate: float = 0.001):
        self.rate = rate

    def calculate(
        self,
        price: float,
        quantity: int,
        volume: float | None,
        side: OrderSide,
    ) -> float:
        return price * self.rate


class VolumeBasedSlippage(SlippageModel):
    """
    成交量相关滑点

    滑点与成交占比成正比:
    滑点 = 基础滑点 * (1 + 成交量占比 * 放大系数)
    """

    def __init__(
        self,
        base_rate: float = 0.001,
        volume_impact: float = 0.1,
    ):
        self.base_rate = base_rate
        self.volume_impact = volume_impact

    def calculate(
        self,
        price: float,
        quantity: int,
        volume: float | None,
        side: OrderSide,
    ) -> float:
        if volume is None or volume <= 0:
            return price * self.base_rate

        volume_pct = quantity / volume
        impact = 1 + volume_pct * self.volume_impact

        return price * self.base_rate * impact


class SqrtSlippage(SlippageModel):
    """
    平方根滑点模型

    更符合市场微观结构:
    滑点 ∝ √(成交量占比) * 波动率
    """

    def __init__(
        self,
        base_rate: float = 0.001,
        volatility: float = 0.02,
    ):
        self.base_rate = base_rate
        self.volatility = volatility

    def calculate(
        self,
        price: float,
        quantity: int,
        volume: float | None,
        side: OrderSide,
    ) -> float:
        if volume is None or volume <= 0:
            return price * self.base_rate

        volume_pct = quantity / volume
        impact = np.sqrt(volume_pct) * self.volatility

        return price * (self.base_rate + impact)


class SimulatedBroker:
    """
    模拟券商

    处理订单执行:
    1. 订单验证
    2. 滑点计算
    3. 成交确认
    4. 手续费扣除
    """

    def __init__(
        self,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.001,
        slippage_model: str = "fixed",
    ):
        """
        Args:
            commission_rate: 手续费率
            slippage_rate: 滑点率
            slippage_model: 滑点模型 (fixed, volume_based, sqrt)
        """
        self.commission_rate = commission_rate

        # 初始化滑点模型
        if slippage_model == "volume_based":
            self.slippage_model = VolumeBasedSlippage(slippage_rate)
        elif slippage_model == "sqrt":
            self.slippage_model = SqrtSlippage(slippage_rate)
        else:
            self.slippage_model = FixedSlippage(slippage_rate)

        # 交易记录
        self._trades: list[dict[str, Any]] = []
        self._orders: list[Order] = []

    def execute_order(
        self,
        order: Order,
        prices: pd.Series,
        volumes: pd.Series | None = None,
    ) -> Fill | None:
        """
        执行订单

        Args:
            order: 订单
            prices: 当前价格序列
            volumes: 当前成交量序列

        Returns:
            成交记录，如果无法成交返回 None
        """
        self._orders.append(order)

        # 检查股票是否存在
        if order.symbol not in prices.index:
            logger.warning("股票不存在", symbol=order.symbol)
            return None

        price = prices[order.symbol]
        if pd.isna(price) or price <= 0:
            logger.warning("价格无效", symbol=order.symbol, price=price)
            return None

        # 获取成交量
        volume = None
        if volumes is not None and order.symbol in volumes.index:
            volume = volumes[order.symbol]

        # 计算滑点
        slippage = self.slippage_model.calculate(
            price, order.quantity, volume, order.side
        )

        # 计算成交价格
        if order.side == OrderSide.BUY:
            fill_price = price + slippage
        else:
            fill_price = price - slippage

        # 确保成交价格合理
        fill_price = max(fill_price, price * 0.9)
        fill_price = min(fill_price, price * 1.1)

        # 计算手续费
        commission = fill_price * order.quantity * self.commission_rate

        # 创建成交记录
        fill = Fill(
            order=order,
            fill_price=fill_price,
            quantity=order.quantity,
            commission=commission,
            slippage=slippage,
        )

        # 记录交易
        self._trades.append({
            "timestamp": fill.filled_at.isoformat(),
            "symbol": order.symbol,
            "side": order.side.value,
            "quantity": order.quantity,
            "price": price,
            "fill_price": fill_price,
            "commission": commission,
            "slippage": slippage,
        })

        return fill

    def get_trade_history(self) -> list[dict[str, Any]]:
        """获取交易历史"""
        return self._trades.copy()

    def get_order_history(self) -> list[Order]:
        """获取订单历史"""
        return self._orders.copy()

    def get_statistics(self) -> dict[str, Any]:
        """获取交易统计"""
        if not self._trades:
            return {
                "total_trades": 0,
                "total_commission": 0,
                "total_slippage": 0,
            }

        return {
            "total_trades": len(self._trades),
            "total_commission": sum(t["commission"] for t in self._trades),
            "total_slippage": sum(t["slippage"] for t in self._trades),
            "avg_commission": np.mean([t["commission"] for t in self._trades]),
            "avg_slippage": np.mean([t["slippage"] for t in self._trades]),
            "buy_trades": sum(1 for t in self._trades if t["side"] == "buy"),
            "sell_trades": sum(1 for t in self._trades if t["side"] == "sell"),
        }
