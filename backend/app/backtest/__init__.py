"""
回测引擎模块

提供:
- 事件驱动回测引擎
- 模拟券商
- 组合管理
- 绩效分析
"""

from app.backtest.broker import SimulatedBroker
from app.backtest.engine import BacktestEngine
from app.backtest.performance import PerformanceAnalyzer
from app.backtest.portfolio import Portfolio

__all__ = [
    "BacktestEngine",
    "SimulatedBroker",
    "Portfolio",
    "PerformanceAnalyzer",
]
