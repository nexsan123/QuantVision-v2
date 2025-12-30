"""
组合管理

提供:
- 持仓追踪
- 市值计算
- 权重管理
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
import structlog

logger = structlog.get_logger()


@dataclass
class Position:
    """持仓"""
    symbol: str
    quantity: int
    avg_cost: float
    market_value: float = 0.0
    unrealized_pnl: float = 0.0

    def update_market_value(self, current_price: float) -> None:
        """更新市值"""
        self.market_value = current_price * self.quantity
        self.unrealized_pnl = (current_price - self.avg_cost) * self.quantity


class Portfolio:
    """
    投资组合

    管理:
    - 现金余额
    - 股票持仓
    - 市值追踪
    - 权重计算
    """

    def __init__(self, initial_capital: float = 1_000_000.0):
        """
        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: dict[str, int] = {}  # symbol -> quantity
        self.avg_costs: dict[str, float] = {}  # symbol -> avg_cost
        self.market_values: dict[str, float] = {}  # symbol -> market_value

        # 历史记录
        self._transaction_history: list[dict[str, Any]] = []

    @property
    def total_value(self) -> float:
        """总资产"""
        return self.cash + sum(self.market_values.values())

    @property
    def equity_value(self) -> float:
        """股票市值"""
        return sum(self.market_values.values())

    def update_market_value(self, prices: pd.Series) -> None:
        """
        更新所有持仓市值

        Args:
            prices: 当前价格序列
        """
        for symbol, quantity in self.positions.items():
            if symbol in prices.index and not pd.isna(prices[symbol]):
                self.market_values[symbol] = prices[symbol] * quantity
            else:
                # 保持上一个已知市值
                pass

    def add_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
    ) -> None:
        """
        增加持仓

        Args:
            symbol: 股票代码
            quantity: 买入数量
            price: 成交价格
        """
        cost = price * quantity

        # 检查现金是否充足
        if cost > self.cash:
            logger.warning(
                "现金不足",
                symbol=symbol,
                required=cost,
                available=self.cash,
            )
            # 按可用现金调整数量
            quantity = int(self.cash / price)
            cost = price * quantity

        if quantity <= 0:
            return

        # 更新现金
        self.cash -= cost

        # 更新持仓
        if symbol in self.positions:
            # 计算新的平均成本
            old_quantity = self.positions[symbol]
            old_cost = self.avg_costs[symbol]
            new_quantity = old_quantity + quantity
            new_avg_cost = (old_quantity * old_cost + quantity * price) / new_quantity

            self.positions[symbol] = new_quantity
            self.avg_costs[symbol] = new_avg_cost
        else:
            self.positions[symbol] = quantity
            self.avg_costs[symbol] = price

        # 更新市值
        self.market_values[symbol] = price * self.positions[symbol]

        # 记录交易
        self._transaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "buy",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "cost": cost,
        })

    def reduce_position(
        self,
        symbol: str,
        quantity: int,
        price: float,
    ) -> float:
        """
        减少持仓

        Args:
            symbol: 股票代码
            quantity: 卖出数量
            price: 成交价格

        Returns:
            实现盈亏
        """
        if symbol not in self.positions:
            logger.warning("持仓不存在", symbol=symbol)
            return 0.0

        current_quantity = self.positions[symbol]
        quantity = min(quantity, current_quantity)

        if quantity <= 0:
            return 0.0

        # 计算盈亏
        avg_cost = self.avg_costs[symbol]
        pnl = (price - avg_cost) * quantity

        # 更新现金
        proceeds = price * quantity
        self.cash += proceeds

        # 更新持仓
        new_quantity = current_quantity - quantity
        if new_quantity <= 0:
            del self.positions[symbol]
            del self.avg_costs[symbol]
            del self.market_values[symbol]
        else:
            self.positions[symbol] = new_quantity
            self.market_values[symbol] = price * new_quantity

        # 记录交易
        self._transaction_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "sell",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "proceeds": proceeds,
            "pnl": pnl,
        })

        return pnl

    def get_weights(self, prices: pd.Series | None = None) -> dict[str, float]:
        """
        获取当前权重

        Args:
            prices: 当前价格序列 (用于更新市值)

        Returns:
            权重字典 {symbol: weight}
        """
        if prices is not None:
            self.update_market_value(prices)

        total = self.total_value
        if total <= 0:
            return {}

        weights = {}
        for symbol, mv in self.market_values.items():
            weights[symbol] = mv / total

        return weights

    def get_position_details(self, prices: pd.Series | None = None) -> list[dict[str, Any]]:
        """
        获取持仓详情

        Returns:
            持仓详情列表
        """
        if prices is not None:
            self.update_market_value(prices)

        details = []
        for symbol in self.positions:
            quantity = self.positions[symbol]
            avg_cost = self.avg_costs[symbol]
            market_value = self.market_values.get(symbol, 0)

            current_price = market_value / quantity if quantity > 0 else 0
            unrealized_pnl = (current_price - avg_cost) * quantity
            pnl_pct = (current_price / avg_cost - 1) if avg_cost > 0 else 0

            details.append({
                "symbol": symbol,
                "quantity": quantity,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "pnl_pct": pnl_pct,
                "weight": market_value / self.total_value if self.total_value > 0 else 0,
            })

        return sorted(details, key=lambda x: x["market_value"], reverse=True)

    def get_summary(self) -> dict[str, Any]:
        """
        获取组合摘要

        Returns:
            摘要信息
        """
        unrealized_pnl = sum(
            (self.market_values.get(s, 0) / self.positions[s] - self.avg_costs[s]) * self.positions[s]
            for s in self.positions
            if self.positions[s] > 0
        )

        return {
            "total_value": self.total_value,
            "cash": self.cash,
            "equity_value": self.equity_value,
            "cash_weight": self.cash / self.total_value if self.total_value > 0 else 1,
            "num_positions": len(self.positions),
            "unrealized_pnl": unrealized_pnl,
            "total_return": (self.total_value / self.initial_capital - 1),
        }

    def get_transaction_history(self) -> list[dict[str, Any]]:
        """获取交易历史"""
        return self._transaction_history.copy()
