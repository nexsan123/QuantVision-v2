"""
分策略持仓服务
PRD 4.18 分策略持仓管理
"""
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Optional

import structlog

from app.schemas.position import (
    AccountPositionSummary,
    ConsolidatedPosition,
    PositionGroup,
    PositionSource,
    SellPositionRequest,
    SellPositionResponse,
    StrategyPosition,
    UpdateStopLossRequest,
)

logger = structlog.get_logger()


class PositionService:
    """分策略持仓服务"""

    CONCENTRATION_WARNING_THRESHOLD = 0.30  # 30%

    # 模拟持仓数据
    _positions: dict[str, StrategyPosition] = {}
    _accounts: dict[str, dict] = {
        "account_001": {"cash": 50000.0, "user_id": "user_001"},
    }

    def __init__(self):
        # 初始化示例持仓数据
        self._init_sample_positions()

    def _init_sample_positions(self):
        """初始化示例持仓数据"""
        if self._positions:
            return

        sample_data = [
            # 策略1: 动量策略
            {
                "strategy_id": "strategy_001",
                "strategy_name": "动量突破策略",
                "symbol": "AAPL",
                "quantity": 100,
                "avg_cost": 175.50,
                "current_price": 185.20,
            },
            {
                "strategy_id": "strategy_001",
                "strategy_name": "动量突破策略",
                "symbol": "MSFT",
                "quantity": 50,
                "avg_cost": 380.00,
                "current_price": 395.50,
            },
            # 策略2: 价值投资策略
            {
                "strategy_id": "strategy_002",
                "strategy_name": "价值投资策略",
                "symbol": "AAPL",
                "quantity": 200,
                "avg_cost": 170.00,
                "current_price": 185.20,
            },
            {
                "strategy_id": "strategy_002",
                "strategy_name": "价值投资策略",
                "symbol": "JPM",
                "quantity": 80,
                "avg_cost": 145.00,
                "current_price": 158.30,
            },
            # 手动交易
            {
                "strategy_id": None,
                "strategy_name": "手动交易",
                "symbol": "NVDA",
                "quantity": 30,
                "avg_cost": 450.00,
                "current_price": 520.00,
            },
            {
                "strategy_id": None,
                "strategy_name": "手动交易",
                "symbol": "AAPL",
                "quantity": 50,
                "avg_cost": 180.00,
                "current_price": 185.20,
            },
        ]

        now = datetime.now()
        for data in sample_data:
            position_id = str(uuid.uuid4())
            market_value = data["quantity"] * data["current_price"]
            cost_basis = data["quantity"] * data["avg_cost"]
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100 if cost_basis > 0 else 0

            self._positions[position_id] = StrategyPosition(
                position_id=position_id,
                user_id="user_001",
                account_id="account_001",
                strategy_id=data["strategy_id"],
                strategy_name=data["strategy_name"],
                symbol=data["symbol"],
                quantity=data["quantity"],
                avg_cost=data["avg_cost"],
                current_price=data["current_price"],
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                unrealized_pnl_pct=unrealized_pnl_pct,
                created_at=now,
                updated_at=now,
            )

    async def get_account_positions(
        self,
        user_id: str,
        account_id: str,
    ) -> AccountPositionSummary:
        """获取账户持仓汇总"""
        # 1. 获取所有持仓
        all_positions = [
            p for p in self._positions.values()
            if p.user_id == user_id and p.account_id == account_id
        ]

        # 2. 更新实时价格 (模拟)
        await self._update_prices(all_positions)

        # 3. 按策略分组
        groups = self._group_by_strategy(all_positions)

        # 4. 生成同股票汇总
        consolidated = self._consolidate_positions(all_positions)

        # 5. 计算账户总值
        account = self._accounts.get(account_id, {"cash": 0})
        total_market_value = sum(p.market_value for p in all_positions)
        total_cash = account.get("cash", 0)
        total_equity = total_cash + total_market_value
        total_cost = sum(p.quantity * p.avg_cost for p in all_positions)
        total_unrealized_pnl = sum(p.unrealized_pnl for p in all_positions)
        total_unrealized_pnl_pct = (total_unrealized_pnl / total_cost * 100) if total_cost > 0 else 0

        # 6. 检查集中度风险
        warnings = self._check_concentration(consolidated, total_equity)

        # 7. 计算组合 Beta
        portfolio_beta = self._calculate_portfolio_beta(all_positions, total_market_value)

        return AccountPositionSummary(
            account_id=account_id,
            total_market_value=total_market_value,
            total_cash=total_cash,
            total_equity=total_equity,
            total_unrealized_pnl=total_unrealized_pnl,
            total_unrealized_pnl_pct=total_unrealized_pnl_pct,
            groups=groups,
            consolidated=consolidated,
            concentration_warnings=warnings,
            portfolio_beta=portfolio_beta,
            updated_at=datetime.now(),
        )

    async def get_positions_by_strategy(
        self,
        user_id: str,
        strategy_id: Optional[str],
    ) -> list[StrategyPosition]:
        """获取特定策略的持仓"""
        positions = [
            p for p in self._positions.values()
            if p.user_id == user_id and p.strategy_id == strategy_id
        ]
        await self._update_prices(positions)
        return positions

    async def get_position(
        self,
        position_id: str,
    ) -> Optional[StrategyPosition]:
        """获取单个持仓"""
        return self._positions.get(position_id)

    async def sell_position(
        self,
        user_id: str,
        request: SellPositionRequest,
    ) -> SellPositionResponse:
        """卖出特定策略的持仓"""
        position = self._positions.get(request.position_id)

        if not position:
            return SellPositionResponse(success=False, message="持仓不存在")

        if position.user_id != user_id:
            return SellPositionResponse(success=False, message="无权操作此持仓")

        if request.quantity > position.quantity:
            return SellPositionResponse(
                success=False,
                message=f"卖出数量 {request.quantity} 超过持仓 {position.quantity}",
            )

        # 模拟卖出
        order_id = str(uuid.uuid4())

        # 更新持仓
        if request.quantity == position.quantity:
            # 全部卖出
            del self._positions[request.position_id]
        else:
            # 部分卖出
            position.quantity -= request.quantity
            position.market_value = position.quantity * position.current_price
            cost_basis = position.quantity * position.avg_cost
            position.unrealized_pnl = position.market_value - cost_basis
            position.unrealized_pnl_pct = (position.unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            position.updated_at = datetime.now()

        # 更新现金
        account = self._accounts.get(position.account_id)
        if account:
            sale_amount = request.quantity * position.current_price
            account["cash"] = account.get("cash", 0) + sale_amount

        logger.info(
            "持仓卖出成功",
            position_id=request.position_id,
            quantity=request.quantity,
            order_id=order_id,
        )

        return SellPositionResponse(
            success=True,
            order_id=order_id,
            message=f"已卖出 {request.quantity} 股 {position.symbol}",
        )

    async def update_stop_loss(
        self,
        user_id: str,
        position_id: str,
        request: UpdateStopLossRequest,
    ) -> bool:
        """更新止盈止损"""
        position = self._positions.get(position_id)

        if not position or position.user_id != user_id:
            return False

        if request.stop_loss is not None:
            position.stop_loss = request.stop_loss

        if request.take_profit is not None:
            position.take_profit = request.take_profit

        position.updated_at = datetime.now()

        logger.info(
            "止盈止损已更新",
            position_id=position_id,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
        )

        return True

    async def _update_prices(self, positions: list[StrategyPosition]) -> None:
        """更新实时价格"""
        import random

        for pos in positions:
            # 模拟价格波动 (±1%)
            change_pct = random.uniform(-0.01, 0.01)
            pos.current_price = pos.current_price * (1 + change_pct)
            pos.market_value = pos.quantity * pos.current_price
            cost_basis = pos.quantity * pos.avg_cost
            pos.unrealized_pnl = pos.market_value - cost_basis
            pos.unrealized_pnl_pct = (pos.unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            pos.updated_at = datetime.now()

    def _group_by_strategy(
        self,
        positions: list[StrategyPosition],
    ) -> list[PositionGroup]:
        """按策略分组"""
        grouped: dict[str, list[StrategyPosition]] = defaultdict(list)

        for pos in positions:
            key = pos.strategy_id or "__manual__"
            grouped[key].append(pos)

        groups = []
        for strategy_id, pos_list in grouped.items():
            total_value = sum(p.market_value for p in pos_list)
            total_cost = sum(p.quantity * p.avg_cost for p in pos_list)
            total_pnl = sum(p.unrealized_pnl for p in pos_list)

            groups.append(PositionGroup(
                strategy_id=None if strategy_id == "__manual__" else strategy_id,
                strategy_name=pos_list[0].strategy_name or "手动交易",
                positions=pos_list,
                total_market_value=total_value,
                total_unrealized_pnl=total_pnl,
                total_unrealized_pnl_pct=(total_pnl / total_cost * 100) if total_cost > 0 else 0,
                position_count=len(pos_list),
            ))

        # 按市值排序
        groups.sort(key=lambda x: x.total_market_value, reverse=True)

        return groups

    def _consolidate_positions(
        self,
        positions: list[StrategyPosition],
    ) -> list[ConsolidatedPosition]:
        """同股票汇总"""
        by_symbol: dict[str, list[StrategyPosition]] = defaultdict(list)

        for pos in positions:
            by_symbol[pos.symbol].append(pos)

        consolidated = []
        for symbol, pos_list in by_symbol.items():
            total_qty = sum(p.quantity for p in pos_list)
            total_cost = sum(p.quantity * p.avg_cost for p in pos_list)
            weighted_avg = total_cost / total_qty if total_qty > 0 else 0
            total_market_value = sum(p.market_value for p in pos_list)
            total_pnl = sum(p.unrealized_pnl for p in pos_list)

            sources = [
                PositionSource(
                    strategy_id=p.strategy_id,
                    strategy_name=p.strategy_name or "手动交易",
                    quantity=p.quantity,
                    avg_cost=p.avg_cost,
                    pnl=p.unrealized_pnl,
                    pnl_pct=p.unrealized_pnl_pct,
                )
                for p in pos_list
            ]

            consolidated.append(ConsolidatedPosition(
                symbol=symbol,
                total_quantity=total_qty,
                weighted_avg_cost=weighted_avg,
                current_price=pos_list[0].current_price,
                total_market_value=total_market_value,
                total_unrealized_pnl=total_pnl,
                total_unrealized_pnl_pct=(total_pnl / total_cost * 100) if total_cost > 0 else 0,
                sources=sources,
                concentration_pct=0,  # 后续计算
            ))

        # 按市值排序
        consolidated.sort(key=lambda x: x.total_market_value, reverse=True)

        return consolidated

    def _check_concentration(
        self,
        consolidated: list[ConsolidatedPosition],
        total_equity: float,
    ) -> list[str]:
        """检查集中度风险"""
        warnings = []

        for pos in consolidated:
            pos.concentration_pct = (pos.total_market_value / total_equity * 100) if total_equity > 0 else 0

            if pos.concentration_pct > self.CONCENTRATION_WARNING_THRESHOLD * 100:
                warnings.append(
                    f"⚠️ {pos.symbol} 持仓占比 {pos.concentration_pct:.1f}%，"
                    f"超过安全阈值 {self.CONCENTRATION_WARNING_THRESHOLD * 100:.0f}%"
                )

        return warnings

    def _calculate_portfolio_beta(
        self,
        positions: list[StrategyPosition],
        total_market_value: float,
    ) -> float:
        """计算组合 Beta"""
        # 模拟 Beta 值
        SYMBOL_BETAS = {
            "AAPL": 1.2,
            "MSFT": 1.1,
            "NVDA": 1.8,
            "JPM": 1.3,
            "GOOGL": 1.1,
        }

        if total_market_value == 0:
            return 1.0

        weighted_beta = 0.0
        for pos in positions:
            beta = SYMBOL_BETAS.get(pos.symbol, 1.0)
            weight = pos.market_value / total_market_value
            weighted_beta += beta * weight

        return round(weighted_beta, 2)


# 单例服务
_position_service: Optional[PositionService] = None


def get_position_service() -> PositionService:
    """获取持仓服务实例"""
    global _position_service
    if _position_service is None:
        _position_service = PositionService()
    return _position_service
