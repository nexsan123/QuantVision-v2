"""
手动交易服务
PRD 4.16 实时交易监控界面
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

import structlog

from app.schemas.manual_trade import (
    CancelOrderResponse,
    ManualTradeOrder,
    OrderSide,
    OrderStatus,
    OrderType,
    PlaceOrderRequest,
    PlaceOrderResponse,
    QuoteData,
)

logger = structlog.get_logger()


class ManualTradeService:
    """手动交易服务"""

    # 模拟数据 - 实际使用时连接券商 API
    _orders: dict[str, ManualTradeOrder] = {}
    _quotes: dict[str, QuoteData] = {}

    async def place_order(
        self,
        user_id: str,
        account_id: str,
        request: PlaceOrderRequest,
    ) -> PlaceOrderResponse:
        """下单"""
        logger.info(
            "下单请求",
            user_id=user_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
        )

        # 1. 验证订单参数
        validation_error = await self._validate_order(
            user_id=user_id,
            account_id=account_id,
            request=request,
        )
        if validation_error:
            return PlaceOrderResponse(success=False, error=validation_error)

        # 2. 检查 PDT 规则 (如果是日内交易)
        pdt_warning = None
        if await self._is_day_trade(account_id, request.symbol, request.side):
            can_trade, reason = await self._check_pdt(account_id)
            if not can_trade:
                return PlaceOrderResponse(
                    success=False,
                    error=f"PDT限制: {reason}",
                )
            pdt_warning = reason  # 可能有警告但仍可交易

        # 3. 获取当前报价
        quote = await self.get_quote(request.symbol)

        # 4. 计算执行价格
        if request.order_type == OrderType.MARKET.value:
            exec_price = quote.ask if request.side == OrderSide.BUY.value else quote.bid
        else:
            exec_price = request.limit_price

        # 5. 创建订单
        order = ManualTradeOrder(
            order_id=str(uuid.uuid4()),
            user_id=user_id,
            account_id=account_id,
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            side=OrderSide(request.side),
            order_type=OrderType(request.order_type),
            quantity=request.quantity,
            limit_price=request.limit_price,
            stop_price=request.stop_price,
            take_profit=request.take_profit,
            stop_loss=request.stop_loss,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
        )

        # 6. 模拟发送到券商 (实际实现需要连接券商 API)
        try:
            # 市价单立即成交
            if request.order_type == OrderType.MARKET.value:
                order.status = OrderStatus.FILLED
                order.filled_quantity = request.quantity
                order.filled_price = exec_price
                order.filled_at = datetime.now()
                order.commission = 0.005 * request.quantity  # 模拟佣金
                order.total_cost = exec_price * request.quantity + order.commission
            else:
                # 限价单/止损单等待触发
                order.status = OrderStatus.PENDING

            # 保存订单
            self._orders[order.order_id] = order

            # 7. 如果有止盈止损，创建条件单
            if order.status == OrderStatus.FILLED and request.side == OrderSide.BUY.value:
                if request.take_profit:
                    await self._create_take_profit_order(order, request.take_profit)
                if request.stop_loss:
                    await self._create_stop_loss_order(order, request.stop_loss)

            logger.info(
                "订单创建成功",
                order_id=order.order_id,
                status=order.status,
            )

            return PlaceOrderResponse(
                success=True,
                order=order,
                pdt_warning=pdt_warning,
            )

        except Exception as e:
            logger.error("订单创建失败", error=str(e))
            return PlaceOrderResponse(success=False, error=str(e))

    async def cancel_order(
        self,
        order_id: str,
        user_id: str,
    ) -> CancelOrderResponse:
        """取消订单"""
        order = self._orders.get(order_id)

        if not order:
            return CancelOrderResponse(success=False, message="订单不存在")

        if order.user_id != user_id:
            return CancelOrderResponse(success=False, message="无权操作此订单")

        if order.status != OrderStatus.PENDING:
            return CancelOrderResponse(
                success=False,
                message=f"订单状态为 {order.status.value}，无法取消",
            )

        # 执行取消
        order.status = OrderStatus.CANCELLED
        order.cancelled_at = datetime.now()

        logger.info("订单已取消", order_id=order_id)

        return CancelOrderResponse(success=True, message="订单已取消")

    async def get_orders(
        self,
        user_id: str,
        status: Optional[str] = None,
        symbol: Optional[str] = None,
        strategy_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ManualTradeOrder], int]:
        """获取订单列表"""
        # 过滤订单
        orders = [o for o in self._orders.values() if o.user_id == user_id]

        if status:
            orders = [o for o in orders if o.status.value == status]

        if symbol:
            orders = [o for o in orders if o.symbol == symbol]

        if strategy_id:
            orders = [o for o in orders if o.strategy_id == strategy_id]

        # 按创建时间排序
        orders.sort(key=lambda x: x.created_at, reverse=True)

        total = len(orders)
        orders = orders[offset : offset + limit]

        return orders, total

    async def get_order(self, order_id: str) -> Optional[ManualTradeOrder]:
        """获取订单详情"""
        return self._orders.get(order_id)

    async def get_quote(self, symbol: str) -> QuoteData:
        """获取实时报价"""
        # 模拟数据 - 实际实现需要连接行情 API
        import random

        base_price = 150.0  # 模拟基础价格

        # 根据 symbol 哈希生成稳定的基础价格
        symbol_hash = sum(ord(c) for c in symbol)
        base_price = 50 + (symbol_hash % 200)

        # 添加随机波动
        change = random.uniform(-2, 2)
        current = base_price + change

        return QuoteData(
            symbol=symbol,
            bid=current - 0.01,
            ask=current + 0.01,
            last=current,
            volume=random.randint(100000, 10000000),
            change=change,
            change_pct=(change / base_price) * 100,
            high=current + random.uniform(0, 3),
            low=current - random.uniform(0, 3),
            open=base_price,
            prev_close=base_price,
            timestamp=datetime.now(),
        )

    async def _validate_order(
        self,
        user_id: str,
        account_id: str,
        request: PlaceOrderRequest,
    ) -> Optional[str]:
        """验证订单"""
        # 检查数量
        if request.quantity <= 0:
            return "数量必须大于0"

        # 限价单必须有价格
        if request.order_type == OrderType.LIMIT.value and not request.limit_price:
            return "限价单必须设置限价"

        # 止损单必须有价格
        if request.order_type == OrderType.STOP.value and not request.stop_price:
            return "止损单必须设置止损价"

        # TODO: 检查账户资金是否足够
        # TODO: 检查持仓是否足够（卖出时）

        return None

    async def _is_day_trade(
        self,
        account_id: str,
        symbol: str,
        side: str,
    ) -> bool:
        """判断是否为日内交易"""
        # 查找当天是否有相反方向的交易
        today = datetime.now().date()

        for order in self._orders.values():
            if (
                order.account_id == account_id
                and order.symbol == symbol
                and order.status == OrderStatus.FILLED
                and order.filled_at
                and order.filled_at.date() == today
            ):
                # 如果今天已经有买入，现在卖出，则是日内交易
                if order.side == OrderSide.BUY and side == OrderSide.SELL.value:
                    return True
                # 如果今天已经有卖出（做空），现在买入，则是日内交易
                if order.side == OrderSide.SELL and side == OrderSide.BUY.value:
                    return True

        return False

    async def _check_pdt(self, account_id: str) -> tuple[bool, Optional[str]]:
        """
        检查 PDT 规则
        返回: (是否可以交易, 警告/错误信息)
        """
        # 模拟 PDT 检查
        # 实际实现需要:
        # 1. 检查账户权益是否 >= $25,000
        # 2. 检查过去5个交易日的日内交易次数

        # 模拟账户权益
        account_equity = 30000  # 假设 > $25,000

        if account_equity >= 25000:
            return True, None

        # 检查日内交易次数
        day_trade_count = await self._get_day_trade_count(account_id)

        if day_trade_count >= 3:
            return False, f"您已使用 {day_trade_count}/3 次日内交易，继续交易将触发 PDT 限制"

        if day_trade_count >= 2:
            return True, f"警告: 您已使用 {day_trade_count}/3 次日内交易"

        return True, None

    async def _get_day_trade_count(self, account_id: str) -> int:
        """获取过去5个交易日的日内交易次数"""
        # 模拟 - 实际需要从数据库查询
        return 1

    async def _create_take_profit_order(
        self,
        parent_order: ManualTradeOrder,
        take_profit: float,
    ) -> None:
        """创建止盈单"""
        logger.info(
            "创建止盈条件单",
            parent_order_id=parent_order.order_id,
            take_profit=take_profit,
        )
        # 实际实现需要创建 OCO (One-Cancels-Other) 订单

    async def _create_stop_loss_order(
        self,
        parent_order: ManualTradeOrder,
        stop_loss: float,
    ) -> None:
        """创建止损单"""
        logger.info(
            "创建止损条件单",
            parent_order_id=parent_order.order_id,
            stop_loss=stop_loss,
        )
        # 实际实现需要创建 OCO 订单


# 单例服务
_manual_trade_service: Optional[ManualTradeService] = None


def get_manual_trade_service() -> ManualTradeService:
    """获取手动交易服务实例"""
    global _manual_trade_service
    if _manual_trade_service is None:
        _manual_trade_service = ManualTradeService()
    return _manual_trade_service
