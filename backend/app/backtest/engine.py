"""
回测引擎

事件驱动回测框架:
- 支持多策略组合
- 滑点和手续费建模
- 实时绩效追踪
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog

from app.backtest.broker import Order, OrderSide, SimulatedBroker
from app.backtest.performance import PerformanceAnalyzer
from app.backtest.portfolio import Portfolio

logger = structlog.get_logger()


class BacktestStatus(str, Enum):
    """回测状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BacktestConfig:
    """回测配置"""

    # 时间范围
    start_date: date
    end_date: date

    # 资金配置
    initial_capital: float = 1_000_000.0
    commission_rate: float = 0.001      # 0.1%
    slippage_rate: float = 0.001        # 0.1%

    # 滑点模型
    slippage_model: str = "fixed"       # fixed, volume_based, sqrt

    # 仓位限制
    max_position_pct: float = 0.1       # 单只股票最大仓位
    max_leverage: float = 1.0           # 最大杠杆

    # 调仓频率
    rebalance_freq: str = "daily"       # daily, weekly, monthly

    # 基准
    benchmark: str = "SPY"


@dataclass
class BacktestResult:
    """回测结果"""

    # 基本信息
    config: BacktestConfig
    status: BacktestStatus = BacktestStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # 权益曲线
    equity_curve: pd.Series = field(default_factory=pd.Series)
    benchmark_curve: pd.Series = field(default_factory=pd.Series)

    # 持仓历史
    positions_history: pd.DataFrame = field(default_factory=pd.DataFrame)
    trades_history: list[dict[str, Any]] = field(default_factory=list)

    # 绩效指标
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    calmar_ratio: float = 0.0
    win_rate: float = 0.0

    # 详细分析
    monthly_returns: pd.Series = field(default_factory=pd.Series)
    drawdown_series: pd.Series = field(default_factory=pd.Series)
    rolling_sharpe: pd.Series = field(default_factory=pd.Series)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "calmar_ratio": self.calmar_ratio,
            "win_rate": self.win_rate,
        }


class BacktestEngine:
    """
    回测引擎

    事件驱动架构:
    1. 数据馈送 (Data Feed)
    2. 策略信号生成 (Strategy)
    3. 订单提交 (Order)
    4. 订单执行 (Broker)
    5. 组合更新 (Portfolio)
    """

    def __init__(self, config: BacktestConfig):
        """
        Args:
            config: 回测配置
        """
        self.config = config
        self.broker = SimulatedBroker(
            commission_rate=config.commission_rate,
            slippage_rate=config.slippage_rate,
            slippage_model=config.slippage_model,
        )
        self.portfolio = Portfolio(initial_capital=config.initial_capital)
        self.analyzer = PerformanceAnalyzer()

        # 状态
        self.current_date: date | None = None
        self.prices: pd.DataFrame | None = None
        self.volumes: pd.DataFrame | None = None

        # 历史记录
        self._equity_history: list[tuple[date, float]] = []
        self._positions_history: list[tuple[date, dict[str, float]]] = []

    def run(
        self,
        prices: pd.DataFrame,
        signals: pd.DataFrame,
        volumes: pd.DataFrame | None = None,
        benchmark_prices: pd.Series | None = None,
    ) -> BacktestResult:
        """
        运行回测

        Args:
            prices: 价格数据 (index=date, columns=symbols)
            signals: 目标权重信号 (同结构, 值为 0-1 的权重)
            volumes: 成交量数据 (用于流动性约束)
            benchmark_prices: 基准价格序列

        Returns:
            回测结果
        """
        result = BacktestResult(config=self.config)
        result.started_at = datetime.now()
        result.status = BacktestStatus.RUNNING

        try:
            # 过滤日期范围
            mask = (prices.index >= pd.Timestamp(self.config.start_date)) & \
                   (prices.index <= pd.Timestamp(self.config.end_date))
            prices = prices[mask]
            signals = signals[mask]

            if volumes is not None:
                volumes = volumes[mask]

            self.prices = prices
            self.volumes = volumes

            # 交易日列表
            trading_days = prices.index.tolist()

            logger.info(
                "开始回测",
                start=self.config.start_date,
                end=self.config.end_date,
                trading_days=len(trading_days),
            )

            # 主循环
            for i, dt in enumerate(trading_days):
                self.current_date = dt.date() if hasattr(dt, "date") else dt

                # 获取当日价格
                current_prices = prices.loc[dt]
                current_volumes = volumes.loc[dt] if volumes is not None else None

                # 更新组合市值
                self.portfolio.update_market_value(current_prices)

                # 获取目标信号
                target_weights = signals.loc[dt].dropna()

                # 执行调仓
                if self._should_rebalance(i):
                    self._rebalance(target_weights, current_prices, current_volumes)

                # 记录权益
                equity = self.portfolio.total_value
                self._equity_history.append((self.current_date, equity))
                self._positions_history.append(
                    (self.current_date, self.portfolio.get_weights(current_prices))
                )

            # 汇总结果
            result.equity_curve = pd.Series(
                dict(self._equity_history)
            )
            result.positions_history = pd.DataFrame(
                [pos for _, pos in self._positions_history],
                index=[dt for dt, _ in self._positions_history],
            )
            result.trades_history = self.broker.get_trade_history()

            # 基准收益
            if benchmark_prices is not None:
                bench_mask = (benchmark_prices.index >= pd.Timestamp(self.config.start_date)) & \
                            (benchmark_prices.index <= pd.Timestamp(self.config.end_date))
                result.benchmark_curve = benchmark_prices[bench_mask]

            # 计算绩效指标
            self._calculate_performance(result)

            result.status = BacktestStatus.COMPLETED
            result.completed_at = datetime.now()

            logger.info(
                "回测完成",
                total_return=f"{result.total_return:.2%}",
                annual_return=f"{result.annual_return:.2%}",
                sharpe=f"{result.sharpe_ratio:.2f}",
                max_dd=f"{result.max_drawdown:.2%}",
            )

        except Exception as e:
            result.status = BacktestStatus.FAILED
            result.completed_at = datetime.now()
            logger.error("回测失败", error=str(e))
            raise

        return result

    def _should_rebalance(self, day_index: int) -> bool:
        """判断是否需要调仓"""
        if self.config.rebalance_freq == "daily":
            return True
        elif self.config.rebalance_freq == "weekly":
            return day_index % 5 == 0
        elif self.config.rebalance_freq == "monthly":
            return day_index % 21 == 0
        return False

    def _rebalance(
        self,
        target_weights: pd.Series,
        prices: pd.Series,
        volumes: pd.Series | None,
    ) -> None:
        """
        执行调仓

        Args:
            target_weights: 目标权重
            prices: 当前价格
            volumes: 当前成交量
        """
        # 当前权重
        current_weights = self.portfolio.get_weights(prices)

        # 计算目标仓位
        total_value = self.portfolio.total_value
        target_positions = {}

        for symbol in target_weights.index:
            if symbol not in prices.index or pd.isna(prices[symbol]):
                continue

            weight = target_weights[symbol]

            # 仓位限制
            weight = min(weight, self.config.max_position_pct)

            target_value = total_value * weight
            target_shares = int(target_value / prices[symbol])
            target_positions[symbol] = target_shares

        # 计算需要交易的订单
        for symbol, target_shares in target_positions.items():
            current_shares = self.portfolio.positions.get(symbol, 0)
            diff = target_shares - current_shares

            if abs(diff) < 1:
                continue

            # 创建订单
            side = OrderSide.BUY if diff > 0 else OrderSide.SELL
            order = Order(
                symbol=symbol,
                side=side,
                quantity=abs(diff),
                price=prices[symbol],
            )

            # 执行订单
            fill = self.broker.execute_order(order, prices, volumes)

            if fill:
                # 更新组合
                if side == OrderSide.BUY:
                    self.portfolio.add_position(symbol, fill.quantity, fill.fill_price)
                else:
                    self.portfolio.reduce_position(symbol, fill.quantity, fill.fill_price)

        # 清仓不在目标中的股票
        for symbol in list(self.portfolio.positions.keys()):
            if symbol not in target_positions or target_positions[symbol] == 0:
                current_shares = self.portfolio.positions[symbol]
                if current_shares > 0:
                    order = Order(
                        symbol=symbol,
                        side=OrderSide.SELL,
                        quantity=current_shares,
                        price=prices[symbol],
                    )
                    fill = self.broker.execute_order(order, prices, volumes)
                    if fill:
                        self.portfolio.reduce_position(symbol, fill.quantity, fill.fill_price)

    def _calculate_performance(self, result: BacktestResult) -> None:
        """计算绩效指标"""
        equity = result.equity_curve

        if len(equity) < 2:
            return

        # 收益率序列
        returns = equity.pct_change().dropna()

        # 总收益
        result.total_return = (equity.iloc[-1] / equity.iloc[0]) - 1

        # 年化收益
        days = (equity.index[-1] - equity.index[0]).days
        if days > 0:
            result.annual_return = (1 + result.total_return) ** (365 / days) - 1

        # 最大回撤
        cummax = equity.cummax()
        drawdown = (equity - cummax) / cummax
        result.max_drawdown = abs(drawdown.min())
        result.drawdown_series = drawdown

        # 夏普比率 (假设无风险利率 0)
        if returns.std() > 0:
            result.sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)

        # 卡尔马比率
        if result.max_drawdown > 0:
            result.calmar_ratio = result.annual_return / result.max_drawdown

        # 胜率
        trades = result.trades_history
        if trades:
            profitable = sum(1 for t in trades if t.get("pnl", 0) > 0)
            result.win_rate = profitable / len(trades)

        # 月度收益
        result.monthly_returns = equity.resample("M").last().pct_change().dropna()

        # 滚动夏普
        result.rolling_sharpe = (
            returns.rolling(60).mean() / returns.rolling(60).std() * np.sqrt(252)
        )
