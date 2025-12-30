"""
Pytest 配置和 Fixtures

提供测试所需的共享配置和数据
"""

import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator

import numpy as np
import pandas as pd
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


# ============================================================
# 基础 Fixtures
# ============================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """同步测试客户端"""
    with TestClient(app) as c:
        yield c


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================
# 市场数据 Fixtures
# ============================================================

@pytest.fixture
def sample_ohlcv() -> pd.DataFrame:
    """生成示例 OHLCV 数据"""
    dates = pd.date_range(start="2020-01-01", periods=252, freq="B")
    np.random.seed(42)

    # 模拟价格随机游走
    returns = np.random.randn(252) * 0.02
    prices = 100 * np.exp(np.cumsum(returns))

    return pd.DataFrame({
        "date": dates,
        "open": prices * (1 + np.random.randn(252) * 0.005),
        "high": prices * (1 + np.abs(np.random.randn(252) * 0.01)),
        "low": prices * (1 - np.abs(np.random.randn(252) * 0.01)),
        "close": prices,
        "volume": np.random.randint(1_000_000, 10_000_000, 252),
    }).set_index("date")


@pytest.fixture
def sample_multi_stock_ohlcv() -> pd.DataFrame:
    """生成多只股票的 OHLCV 数据"""
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]
    dates = pd.date_range(start="2020-01-01", periods=252, freq="B")
    np.random.seed(42)

    data = []
    for symbol in symbols:
        returns = np.random.randn(252) * 0.02
        prices = 100 * np.exp(np.cumsum(returns))

        for i, date in enumerate(dates):
            data.append({
                "date": date,
                "symbol": symbol,
                "open": prices[i] * (1 + np.random.randn() * 0.005),
                "high": prices[i] * (1 + abs(np.random.randn()) * 0.01),
                "low": prices[i] * (1 - abs(np.random.randn()) * 0.01),
                "close": prices[i],
                "volume": np.random.randint(1_000_000, 10_000_000),
            })

    return pd.DataFrame(data)


@pytest.fixture
def sample_returns() -> pd.Series:
    """生成示例收益率序列"""
    dates = pd.date_range(start="2020-01-01", periods=252, freq="B")
    np.random.seed(42)
    returns = np.random.randn(252) * 0.02
    return pd.Series(returns, index=dates, name="returns")


@pytest.fixture
def sample_returns_df() -> pd.DataFrame:
    """生成多资产收益率 DataFrame"""
    dates = pd.date_range(start="2020-01-01", periods=252, freq="B")
    symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]
    np.random.seed(42)

    data = {}
    for symbol in symbols:
        data[symbol] = np.random.randn(252) * 0.02

    return pd.DataFrame(data, index=dates)


# ============================================================
# 策略配置 Fixtures
# ============================================================

@pytest.fixture
def sample_strategy_config() -> dict:
    """示例策略配置"""
    return {
        "name": "测试动量策略",
        "universe": {
            "type": "sp500",
            "min_market_cap": 10_000_000_000,
        },
        "factors": [
            {
                "name": "momentum_20",
                "operator": "momentum",
                "params": {"period": 20},
            },
            {
                "name": "volatility_20",
                "operator": "volatility",
                "params": {"period": 20},
            },
        ],
        "signal": {
            "type": "long",
            "entry_condition": "momentum_20 > 0",
            "exit_condition": "momentum_20 < -0.05",
        },
        "weight": {
            "method": "equal",
            "max_weight": 0.1,
        },
        "output": {
            "rebalance_frequency": "monthly",
            "target_positions": 20,
        },
    }


@pytest.fixture
def sample_backtest_config() -> dict:
    """示例回测配置"""
    return {
        "start_date": "2020-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 1_000_000,
        "commission": 0.001,
        "slippage": 0.0005,
        "benchmark": "SPY",
    }


# ============================================================
# 辅助函数
# ============================================================

def generate_random_prices(
    n_days: int = 252,
    n_stocks: int = 100,
    seed: int = 42,
) -> pd.DataFrame:
    """
    生成随机价格数据

    用于性能测试
    """
    np.random.seed(seed)
    dates = pd.date_range(start="2020-01-01", periods=n_days, freq="B")
    symbols = [f"STOCK_{i:03d}" for i in range(n_stocks)]

    data = []
    for symbol in symbols:
        returns = np.random.randn(n_days) * 0.02
        prices = 100 * np.exp(np.cumsum(returns))

        for i, date in enumerate(dates):
            data.append({
                "date": date,
                "symbol": symbol,
                "close": prices[i],
            })

    return pd.DataFrame(data)
