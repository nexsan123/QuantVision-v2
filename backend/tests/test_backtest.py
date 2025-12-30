"""
回测引擎集成测试

测试回测引擎的完整流程
"""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from app.backtest.engine import BacktestEngine
from app.backtest.broker import SimulatedBroker
from app.backtest.portfolio import Portfolio
from app.backtest.performance import PerformanceAnalyzer as PerformanceCalculator


class TestPortfolio:
    """投资组合测试"""

    def test_initial_cash(self):
        """测试初始现金"""
        portfolio = Portfolio(initial_cash=1_000_000)
        assert portfolio.cash == 1_000_000
        assert portfolio.get_total_value({}) == 1_000_000

    def test_buy_position(self):
        """测试买入持仓"""
        portfolio = Portfolio(initial_cash=100_000)
        portfolio.update_position("AAPL", 100, 150.0)

        assert portfolio.get_position("AAPL") == 100
        assert portfolio.cash == 100_000 - 100 * 150.0

    def test_sell_position(self):
        """测试卖出持仓"""
        portfolio = Portfolio(initial_cash=100_000)
        portfolio.update_position("AAPL", 100, 150.0)
        portfolio.update_position("AAPL", -50, 155.0)

        assert portfolio.get_position("AAPL") == 50
        assert portfolio.cash == 100_000 - 100 * 150.0 + 50 * 155.0

    def test_total_value(self):
        """测试总价值计算"""
        portfolio = Portfolio(initial_cash=100_000)
        portfolio.update_position("AAPL", 100, 150.0)
        portfolio.update_position("GOOGL", 50, 140.0)

        current_prices = {"AAPL": 160.0, "GOOGL": 145.0}
        total = portfolio.get_total_value(current_prices)

        expected = (
            portfolio.cash
            + 100 * 160.0
            + 50 * 145.0
        )
        assert total == expected


class TestSimulatedBroker:
    """模拟券商测试"""

    def test_market_order(self):
        """测试市价单"""
        broker = SimulatedBroker(commission=0.001, slippage=0.0005)
        portfolio = Portfolio(initial_cash=100_000)

        fill_price, fill_qty, commission = broker.execute_order(
            symbol="AAPL",
            quantity=100,
            price=150.0,
            order_type="market",
            side="buy",
            portfolio=portfolio,
        )

        # 验证滑点
        assert fill_price > 150.0  # 买入有向上滑点
        assert fill_qty == 100
        assert commission > 0

    def test_limit_order_fill(self):
        """测试限价单成交"""
        broker = SimulatedBroker(commission=0.001, slippage=0.0)
        portfolio = Portfolio(initial_cash=100_000)

        fill_price, fill_qty, commission = broker.execute_order(
            symbol="AAPL",
            quantity=100,
            price=150.0,
            order_type="limit",
            side="buy",
            portfolio=portfolio,
            limit_price=151.0,  # 限价高于市价，应成交
        )

        assert fill_price == 150.0  # 限价单按市价成交
        assert fill_qty == 100

    def test_limit_order_not_fill(self):
        """测试限价单未成交"""
        broker = SimulatedBroker(commission=0.001, slippage=0.0)
        portfolio = Portfolio(initial_cash=100_000)

        fill_price, fill_qty, commission = broker.execute_order(
            symbol="AAPL",
            quantity=100,
            price=150.0,
            order_type="limit",
            side="buy",
            portfolio=portfolio,
            limit_price=148.0,  # 限价低于市价，不成交
        )

        assert fill_qty == 0

    def test_insufficient_cash(self):
        """测试现金不足"""
        broker = SimulatedBroker(commission=0.001, slippage=0.0)
        portfolio = Portfolio(initial_cash=1_000)

        fill_price, fill_qty, commission = broker.execute_order(
            symbol="AAPL",
            quantity=100,
            price=150.0,
            order_type="market",
            side="buy",
            portfolio=portfolio,
        )

        # 应部分成交或不成交
        assert fill_qty * fill_price <= 1_000


class TestPerformanceCalculator:
    """绩效计算测试"""

    @pytest.fixture
    def sample_equity_curve(self):
        """生成示例权益曲线"""
        dates = pd.date_range(start="2020-01-01", periods=252, freq="B")
        np.random.seed(42)
        returns = np.random.randn(252) * 0.01
        values = 1_000_000 * np.exp(np.cumsum(returns))
        return pd.Series(values, index=dates)

    def test_total_return(self, sample_equity_curve):
        """测试总收益率"""
        calc = PerformanceCalculator(sample_equity_curve)
        total_return = calc.total_return()
        expected = sample_equity_curve.iloc[-1] / sample_equity_curve.iloc[0] - 1
        assert abs(total_return - expected) < 1e-10

    def test_annualized_return(self, sample_equity_curve):
        """测试年化收益率"""
        calc = PerformanceCalculator(sample_equity_curve)
        ann_return = calc.annualized_return()
        # 年化收益率应在合理范围内
        assert -1.0 < ann_return < 10.0

    def test_sharpe_ratio(self, sample_equity_curve):
        """测试夏普比率"""
        calc = PerformanceCalculator(sample_equity_curve)
        sharpe = calc.sharpe_ratio()
        # 夏普比率应在合理范围内
        assert -5.0 < sharpe < 10.0

    def test_max_drawdown(self, sample_equity_curve):
        """测试最大回撤"""
        calc = PerformanceCalculator(sample_equity_curve)
        max_dd = calc.max_drawdown()
        assert -1.0 <= max_dd <= 0.0

    def test_win_rate(self, sample_equity_curve):
        """测试胜率"""
        calc = PerformanceCalculator(sample_equity_curve)
        win_rate = calc.win_rate()
        assert 0.0 <= win_rate <= 1.0


class TestBacktestEngine:
    """回测引擎集成测试"""

    @pytest.fixture
    def sample_price_data(self):
        """生成示例价格数据"""
        dates = pd.date_range(start="2020-01-01", periods=252, freq="B")
        symbols = ["AAPL", "GOOGL", "MSFT"]
        np.random.seed(42)

        data = {}
        for symbol in symbols:
            returns = np.random.randn(252) * 0.02
            prices = 100 * np.exp(np.cumsum(returns))
            data[symbol] = pd.DataFrame({
                "open": prices * (1 + np.random.randn(252) * 0.005),
                "high": prices * (1 + np.abs(np.random.randn(252) * 0.01)),
                "low": prices * (1 - np.abs(np.random.randn(252) * 0.01)),
                "close": prices,
                "volume": np.random.randint(1_000_000, 10_000_000, 252),
            }, index=dates)

        return data

    @pytest.fixture
    def simple_strategy(self):
        """简单策略: 等权买入持有"""
        def strategy(date, data, portfolio):
            signals = {}
            for symbol in data.keys():
                signals[symbol] = 1.0 / len(data)  # 等权
            return signals
        return strategy

    def test_backtest_runs(self, sample_price_data, simple_strategy):
        """测试回测引擎运行"""
        engine = BacktestEngine(
            initial_capital=1_000_000,
            commission=0.001,
            slippage=0.0005,
        )

        results = engine.run(
            price_data=sample_price_data,
            strategy=simple_strategy,
            start_date="2020-01-01",
            end_date="2020-12-31",
        )

        assert "equity_curve" in results
        assert "trades" in results
        assert "metrics" in results

    def test_backtest_metrics(self, sample_price_data, simple_strategy):
        """测试回测指标计算"""
        engine = BacktestEngine(
            initial_capital=1_000_000,
            commission=0.001,
            slippage=0.0005,
        )

        results = engine.run(
            price_data=sample_price_data,
            strategy=simple_strategy,
            start_date="2020-01-01",
            end_date="2020-12-31",
        )

        metrics = results["metrics"]
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics


class TestBacktestPerformance:
    """回测性能测试"""

    def test_performance_benchmark(self, sample_price_data, simple_strategy):
        """性能基准测试: 1年日频数据应在 10 秒内完成"""
        import time

        # 生成 5 年数据
        dates = pd.date_range(start="2019-01-01", periods=252 * 5, freq="B")
        symbols = [f"STOCK_{i:03d}" for i in range(100)]
        np.random.seed(42)

        large_data = {}
        for symbol in symbols:
            returns = np.random.randn(len(dates)) * 0.02
            prices = 100 * np.exp(np.cumsum(returns))
            large_data[symbol] = pd.DataFrame({
                "close": prices,
            }, index=dates)

        def equal_weight_strategy(date, data, portfolio):
            return {s: 1.0 / len(data) for s in data.keys()}

        engine = BacktestEngine(
            initial_capital=10_000_000,
            commission=0.001,
            slippage=0.0005,
        )

        start_time = time.time()
        results = engine.run(
            price_data=large_data,
            strategy=equal_weight_strategy,
            start_date="2019-01-01",
            end_date="2023-12-31",
        )
        elapsed = time.time() - start_time

        # 5年100只股票日频回测应在 30 秒内完成
        assert elapsed < 30, f"回测耗时 {elapsed:.2f}s 超过 30s 限制"
        print(f"\n回测性能: 5年100股日频, 耗时 {elapsed:.2f}s")
