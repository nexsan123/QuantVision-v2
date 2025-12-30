"""
执行系统模块

提供:
- 订单管理
- 执行算法 (TWAP, VWAP, POV)
- 交易成本分析 (TCA)
"""

from app.execution.order_manager import (
    Order,
    OrderStatus,
    OrderType,
    OrderSide,
    OrderManager,
    OrderEvent,
)
from app.execution.twap import TWAPExecutor, TWAPConfig
from app.execution.vwap import VWAPExecutor, VWAPConfig
from app.execution.pov import POVExecutor, POVConfig
from app.execution.tca import (
    TCAAnalyzer,
    TCAReport,
    ExecutionQuality,
    calculate_slippage,
    calculate_implementation_shortfall,
)

__all__ = [
    # 订单管理
    "Order",
    "OrderStatus",
    "OrderType",
    "OrderSide",
    "OrderManager",
    "OrderEvent",
    # 执行算法
    "TWAPExecutor",
    "TWAPConfig",
    "VWAPExecutor",
    "VWAPConfig",
    "POVExecutor",
    "POVConfig",
    # TCA
    "TCAAnalyzer",
    "TCAReport",
    "ExecutionQuality",
    "calculate_slippage",
    "calculate_implementation_shortfall",
]
