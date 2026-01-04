"""
Phase 12: \u6267\u884c\u5c42\u5347\u7ea7 - \u6ed1\u70b9\u6a21\u578b

\u652f\u6301\u7684\u6a21\u578b:
- Fixed: \u56fa\u5b9a\u6bd4\u4f8b\u6ed1\u70b9
- VolumeBased: \u6210\u4ea4\u91cf\u76f8\u5173\u6ed1\u70b9
- Sqrt: \u5e73\u65b9\u6839\u6a21\u578b
- AlmgrenChriss: \u7cbe\u786e\u5e02\u573a\u51b2\u51fb\u6a21\u578b

Almgren-Chriss \u6a21\u578b\u516c\u5f0f:
    \u603b\u6ed1\u70b9 = \u56fa\u5b9a\u6210\u672c + \u4e34\u65f6\u51b2\u51fb + \u6c38\u4e45\u51b2\u51fb

    Impact = spread/2 + \u03b7 * \u03c3 * (Q/V)^0.5 + \u03b3 * (Q/V)

    \u5176\u4e2d:
    - spread: \u4e70\u5356\u4ef7\u5dee
    - \u03b7: \u4e34\u65f6\u51b2\u51fb\u7cfb\u6570 (\u901a\u5e38 0.1-0.5)
    - \u03b3: \u6c38\u4e45\u51b2\u51fb\u7cfb\u6570 (\u901a\u5e38 0.01-0.05)
    - \u03c3: \u65e5\u6ce2\u52a8\u7387
    - Q: \u8ba2\u5355\u5927\u5c0f (\u80a1\u6570)
    - V: \u65e5\u5747\u6210\u4ea4\u91cf (\u80a1\u6570)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
import structlog

from app.schemas.trading import (
    SlippageModelType,
    AlmgrenChrissParams,
    SlippageResult,
    SlippageConfig,
    OrderSide,
)

logger = structlog.get_logger()


@dataclass
class MarketConditions:
    """\u5e02\u573a\u6761\u4ef6"""
    price: float                    # \u5f53\u524d\u4ef7\u683c
    daily_volume: float            # \u65e5\u5747\u6210\u4ea4\u91cf
    volatility: float              # \u65e5\u6ce2\u52a8\u7387
    spread_bps: float = 5.0        # \u4e70\u5356\u4ef7\u5dee (\u57fa\u70b9)
    bid_price: float | None = None
    ask_price: float | None = None


class BaseSlippageModel(ABC):
    """\u6ed1\u70b9\u6a21\u578b\u57fa\u7c7b"""

    @property
    @abstractmethod
    def model_type(self) -> SlippageModelType:
        """\u6a21\u578b\u7c7b\u578b"""
        pass

    @abstractmethod
    def calculate(
        self,
        price: float,
        quantity: float,
        side: OrderSide,
        market: MarketConditions | None = None,
    ) -> SlippageResult:
        """
        \u8ba1\u7b97\u6ed1\u70b9

        Args:
            price: \u5f53\u524d\u4ef7\u683c
            quantity: \u4ea4\u6613\u6570\u91cf
            side: \u4ea4\u6613\u65b9\u5411
            market: \u5e02\u573a\u6761\u4ef6

        Returns:
            \u6ed1\u70b9\u7ed3\u679c
        """
        pass

    def get_fill_price(
        self,
        price: float,
        quantity: float,
        side: OrderSide,
        market: MarketConditions | None = None,
    ) -> float:
        """\u83b7\u53d6\u9884\u4f30\u6210\u4ea4\u4ef7\u683c"""
        result = self.calculate(price, quantity, side, market)

        if side == OrderSide.BUY:
            return price * (1 + result.slippage_percent / 100)
        else:
            return price * (1 - result.slippage_percent / 100)


class FixedSlippageModel(BaseSlippageModel):
    """
    \u56fa\u5b9a\u6bd4\u4f8b\u6ed1\u70b9\u6a21\u578b

    \u6ed1\u70b9 = \u4ef7\u683c * \u56fa\u5b9a\u6bd4\u4f8b
    """

    def __init__(self, rate: float = 0.001):
        """
        Args:
            rate: \u6ed1\u70b9\u7387 (\u9ed8\u8ba4 0.1%)
        """
        self.rate = rate

    @property
    def model_type(self) -> SlippageModelType:
        return SlippageModelType.FIXED

    def calculate(
        self,
        price: float,
        quantity: float,
        side: OrderSide,
        market: MarketConditions | None = None,
    ) -> SlippageResult:
        slippage = price * self.rate
        slippage_bps = self.rate * 10000
        slippage_pct = self.rate * 100

        return SlippageResult(
            total_slippage=slippage,
            fixed_cost=slippage,
            temporary_impact=0.0,
            permanent_impact=0.0,
            slippage_bps=slippage_bps,
            slippage_percent=slippage_pct,
        )


class VolumeBasedSlippageModel(BaseSlippageModel):
    """
    \u6210\u4ea4\u91cf\u76f8\u5173\u6ed1\u70b9\u6a21\u578b

    \u6ed1\u70b9 = \u57fa\u7840\u6ed1\u70b9 * (1 + \u6210\u4ea4\u91cf\u5360\u6bd4 * \u653e\u5927\u7cfb\u6570)
    """

    def __init__(
        self,
        base_rate: float = 0.001,
        volume_impact: float = 0.1,
    ):
        """
        Args:
            base_rate: \u57fa\u7840\u6ed1\u70b9\u7387
            volume_impact: \u6210\u4ea4\u91cf\u5f71\u54cd\u7cfb\u6570
        """
        self.base_rate = base_rate
        self.volume_impact = volume_impact

    @property
    def model_type(self) -> SlippageModelType:
        return SlippageModelType.VOLUME_BASED

    def calculate(
        self,
        price: float,
        quantity: float,
        side: OrderSide,
        market: MarketConditions | None = None,
    ) -> SlippageResult:
        if market is None or market.daily_volume <= 0:
            # \u65e0\u5e02\u573a\u6570\u636e\u65f6\u4f7f\u7528\u57fa\u7840\u7387
            slippage = price * self.base_rate
        else:
            volume_pct = quantity / market.daily_volume
            impact = 1 + volume_pct * self.volume_impact
            slippage = price * self.base_rate * impact

        slippage_pct = slippage / price * 100

        return SlippageResult(
            total_slippage=slippage,
            fixed_cost=price * self.base_rate,
            temporary_impact=slippage - price * self.base_rate,
            permanent_impact=0.0,
            slippage_bps=slippage_pct * 100,
            slippage_percent=slippage_pct,
        )


class SqrtSlippageModel(BaseSlippageModel):
    """
    \u5e73\u65b9\u6839\u6ed1\u70b9\u6a21\u578b

    \u66f4\u7b26\u5408\u5e02\u573a\u5fae\u89c2\u7ed3\u6784:
    \u6ed1\u70b9 \u221d sqrt(\u6210\u4ea4\u91cf\u5360\u6bd4) * \u6ce2\u52a8\u7387
    """

    def __init__(
        self,
        base_rate: float = 0.001,
        default_volatility: float = 0.02,
    ):
        """
        Args:
            base_rate: \u57fa\u7840\u6ed1\u70b9\u7387
            default_volatility: \u9ed8\u8ba4\u6ce2\u52a8\u7387
        """
        self.base_rate = base_rate
        self.default_volatility = default_volatility

    @property
    def model_type(self) -> SlippageModelType:
        return SlippageModelType.SQRT

    def calculate(
        self,
        price: float,
        quantity: float,
        side: OrderSide,
        market: MarketConditions | None = None,
    ) -> SlippageResult:
        if market is None or market.daily_volume <= 0:
            slippage = price * self.base_rate
        else:
            volatility = market.volatility if market.volatility > 0 else self.default_volatility
            volume_pct = quantity / market.daily_volume
            impact = np.sqrt(volume_pct) * volatility
            slippage = price * (self.base_rate + impact)

        slippage_pct = slippage / price * 100

        return SlippageResult(
            total_slippage=slippage,
            fixed_cost=price * self.base_rate,
            temporary_impact=slippage - price * self.base_rate,
            permanent_impact=0.0,
            slippage_bps=slippage_pct * 100,
            slippage_percent=slippage_pct,
        )


class AlmgrenChrissSlippageModel(BaseSlippageModel):
    """
    Almgren-Chriss \u6ed1\u70b9\u6a21\u578b

    \u57fa\u4e8e\u5e02\u573a\u5fae\u89c2\u7ed3\u6784\u7684\u7cbe\u786e\u6ed1\u70b9\u6a21\u578b:

    \u603b\u51b2\u51fb = spread/2 + \u4e34\u65f6\u51b2\u51fb + \u6c38\u4e45\u51b2\u51fb

    \u5176\u4e2d:
    - \u4e34\u65f6\u51b2\u51fb = \u03b7 * \u03c3 * sqrt(Q/V)
    - \u6c38\u4e45\u51b2\u51fb = \u03b3 * (Q/V)

    \u53c2\u8003\u6587\u732e:
    Almgren, R. and Chriss, N. (2000). "Optimal Execution of Portfolio Transactions"

    \u793a\u4f8b:
    - AAPL: \u4ef7\u683c $180, \u65e5\u5747\u91cf 50M, \u8ba2\u5355 10,000 \u80a1
    - \u53c2\u6570: \u03b7=0.3, \u03b3=0.03, \u03c3=2%, spread=1bp
    - \u6ed1\u70b9 = 0.5bp + 0.3*2%*sqrt(0.02%) + 0.03*0.02%
           \u2248 0.5bp + 0.85bp + 0.06bp = 1.4bp \u2248 $0.025
    """

    # \u9ed8\u8ba4\u53c2\u6570 (\u6839\u636e\u7f8e\u80a1\u5e02\u573a\u7ecf\u9a8c\u6821\u51c6)
    DEFAULT_PARAMS = AlmgrenChrissParams(
        eta=0.3,        # \u4e34\u65f6\u51b2\u51fb\u7cfb\u6570
        gamma=0.03,     # \u6c38\u4e45\u51b2\u51fb\u7cfb\u6570
        sigma=0.02,     # \u65e5\u6ce2\u52a8\u7387 2%
        spread_bps=5.0, # \u4e70\u5356\u4ef7\u5dee 5\u57fa\u70b9
    )

    def __init__(self, params: AlmgrenChrissParams | None = None):
        """
        Args:
            params: \u6a21\u578b\u53c2\u6570
        """
        self.params = params or self.DEFAULT_PARAMS

    @property
    def model_type(self) -> SlippageModelType:
        return SlippageModelType.ALMGREN_CHRISS

    def calculate(
        self,
        price: float,
        quantity: float,
        side: OrderSide,
        market: MarketConditions | None = None,
    ) -> SlippageResult:
        """
        \u8ba1\u7b97 Almgren-Chriss \u6ed1\u70b9

        Args:
            price: \u5f53\u524d\u4ef7\u683c
            quantity: \u8ba2\u5355\u6570\u91cf
            side: \u4ea4\u6613\u65b9\u5411
            market: \u5e02\u573a\u6761\u4ef6

        Returns:
            \u6ed1\u70b9\u7ed3\u679c
        """
        # \u83b7\u53d6\u5e02\u573a\u53c2\u6570
        if market:
            daily_volume = market.daily_volume if market.daily_volume > 0 else 1e6
            volatility = market.volatility if market.volatility > 0 else self.params.sigma
            spread_bps = market.spread_bps if market.spread_bps > 0 else self.params.spread_bps
        else:
            daily_volume = 1e6  # \u9ed8\u8ba4 100\u4e07\u80a1
            volatility = self.params.sigma
            spread_bps = self.params.spread_bps

        # \u8ba1\u7b97\u5404\u90e8\u5206\u51b2\u51fb
        volume_ratio = quantity / daily_volume

        # 1. \u56fa\u5b9a\u6210\u672c: spread / 2
        fixed_cost_bps = spread_bps / 2
        fixed_cost = price * fixed_cost_bps / 10000

        # 2. \u4e34\u65f6\u51b2\u51fb: \u03b7 * \u03c3 * sqrt(Q/V)
        temporary_impact_bps = self.params.eta * volatility * 10000 * np.sqrt(volume_ratio)
        temporary_impact = price * temporary_impact_bps / 10000

        # 3. \u6c38\u4e45\u51b2\u51fb: \u03b3 * (Q/V)
        permanent_impact_bps = self.params.gamma * volume_ratio * 10000
        permanent_impact = price * permanent_impact_bps / 10000

        # \u603b\u6ed1\u70b9
        total_slippage = fixed_cost + temporary_impact + permanent_impact
        total_slippage_bps = fixed_cost_bps + temporary_impact_bps + permanent_impact_bps
        slippage_percent = total_slippage_bps / 100

        logger.debug(
            "Almgren-Chriss \u8ba1\u7b97",
            price=price,
            quantity=quantity,
            volume_ratio=f"{volume_ratio:.6f}",
            fixed_bps=f"{fixed_cost_bps:.2f}",
            temp_bps=f"{temporary_impact_bps:.2f}",
            perm_bps=f"{permanent_impact_bps:.2f}",
            total_bps=f"{total_slippage_bps:.2f}",
        )

        return SlippageResult(
            total_slippage=total_slippage,
            fixed_cost=fixed_cost,
            temporary_impact=temporary_impact,
            permanent_impact=permanent_impact,
            slippage_bps=total_slippage_bps,
            slippage_percent=slippage_percent,
        )

    def estimate_for_trade(
        self,
        symbol: str,
        price: float,
        quantity: float,
        side: OrderSide,
        daily_volume: float,
        volatility: float | None = None,
        spread_bps: float | None = None,
    ) -> dict[str, Any]:
        """
        \u4e3a\u5177\u4f53\u4ea4\u6613\u4f30\u7b97\u6ed1\u70b9

        Args:
            symbol: \u80a1\u7968\u4ee3\u7801
            price: \u5f53\u524d\u4ef7\u683c
            quantity: \u8ba2\u5355\u6570\u91cf
            side: \u4ea4\u6613\u65b9\u5411
            daily_volume: \u65e5\u5747\u6210\u4ea4\u91cf
            volatility: \u65e5\u6ce2\u52a8\u7387
            spread_bps: \u4e70\u5356\u4ef7\u5dee

        Returns:
            \u8be6\u7ec6\u4f30\u7b97\u7ed3\u679c
        """
        market = MarketConditions(
            price=price,
            daily_volume=daily_volume,
            volatility=volatility or self.params.sigma,
            spread_bps=spread_bps or self.params.spread_bps,
        )

        result = self.calculate(price, quantity, side, market)
        fill_price = self.get_fill_price(price, quantity, side, market)

        trade_value = price * quantity
        slippage_cost = result.total_slippage * quantity

        return {
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
            "side": side.value,
            "daily_volume": daily_volume,
            "volume_participation": quantity / daily_volume * 100,
            "slippage": {
                "total_bps": result.slippage_bps,
                "total_percent": result.slippage_percent,
                "fixed_cost_bps": result.fixed_cost / price * 10000,
                "temporary_impact_bps": result.temporary_impact / price * 10000,
                "permanent_impact_bps": result.permanent_impact / price * 10000,
            },
            "estimated_fill_price": fill_price,
            "slippage_cost": slippage_cost,
            "trade_value": trade_value,
            "total_cost": trade_value + slippage_cost if side == OrderSide.BUY else trade_value - slippage_cost,
        }


class SlippageModelFactory:
    """\u6ed1\u70b9\u6a21\u578b\u5de5\u5382"""

    @staticmethod
    def create(config: SlippageConfig | None = None) -> BaseSlippageModel:
        """
        \u521b\u5efa\u6ed1\u70b9\u6a21\u578b

        Args:
            config: \u6ed1\u70b9\u914d\u7f6e

        Returns:
            \u6ed1\u70b9\u6a21\u578b\u5b9e\u4f8b
        """
        if config is None:
            return AlmgrenChrissSlippageModel()

        model_type = config.model_type

        if model_type == SlippageModelType.FIXED:
            return FixedSlippageModel(rate=config.fixed_rate)
        elif model_type == SlippageModelType.VOLUME_BASED:
            return VolumeBasedSlippageModel(base_rate=config.fixed_rate)
        elif model_type == SlippageModelType.SQRT:
            return SqrtSlippageModel(base_rate=config.fixed_rate)
        elif model_type == SlippageModelType.ALMGREN_CHRISS:
            params = config.almgren_chriss or AlmgrenChrissParams()
            return AlmgrenChrissSlippageModel(params=params)
        else:
            return AlmgrenChrissSlippageModel()

    @staticmethod
    def get_available_models() -> list[dict[str, Any]]:
        """\u83b7\u53d6\u53ef\u7528\u6a21\u578b\u5217\u8868"""
        return [
            {
                "type": SlippageModelType.FIXED.value,
                "name": "\u56fa\u5b9a\u6bd4\u4f8b",
                "description": "\u6ed1\u70b9 = \u4ef7\u683c * \u56fa\u5b9a\u6bd4\u4f8b",
                "params": ["fixed_rate"],
            },
            {
                "type": SlippageModelType.VOLUME_BASED.value,
                "name": "\u6210\u4ea4\u91cf\u76f8\u5173",
                "description": "\u6ed1\u70b9\u4e0e\u6210\u4ea4\u91cf\u5360\u6bd4\u7ebf\u6027\u76f8\u5173",
                "params": ["fixed_rate", "volume_impact"],
            },
            {
                "type": SlippageModelType.SQRT.value,
                "name": "\u5e73\u65b9\u6839\u6a21\u578b",
                "description": "\u6ed1\u70b9\u4e0esqrt(\u6210\u4ea4\u91cf\u5360\u6bd4)\u76f8\u5173",
                "params": ["fixed_rate"],
            },
            {
                "type": SlippageModelType.ALMGREN_CHRISS.value,
                "name": "Almgren-Chriss",
                "description": "\u7cbe\u786e\u7684\u5e02\u573a\u51b2\u51fb\u6a21\u578b\uff0c\u533a\u5206\u4e34\u65f6\u548c\u6c38\u4e45\u51b2\u51fb",
                "params": ["eta", "gamma", "sigma", "spread_bps"],
                "recommended": True,
            },
        ]


# \u5168\u5c40\u9ed8\u8ba4\u6a21\u578b
default_slippage_model = AlmgrenChrissSlippageModel()


def estimate_slippage(
    symbol: str,
    price: float,
    quantity: float,
    side: OrderSide,
    daily_volume: float,
    volatility: float | None = None,
    config: SlippageConfig | None = None,
) -> SlippageResult:
    """
    \u4fbf\u6377\u51fd\u6570: \u4f30\u7b97\u6ed1\u70b9

    Args:
        symbol: \u80a1\u7968\u4ee3\u7801
        price: \u5f53\u524d\u4ef7\u683c
        quantity: \u8ba2\u5355\u6570\u91cf
        side: \u4ea4\u6613\u65b9\u5411
        daily_volume: \u65e5\u5747\u6210\u4ea4\u91cf
        volatility: \u65e5\u6ce2\u52a8\u7387
        config: \u6ed1\u70b9\u914d\u7f6e

    Returns:
        \u6ed1\u70b9\u7ed3\u679c
    """
    model = SlippageModelFactory.create(config)
    market = MarketConditions(
        price=price,
        daily_volume=daily_volume,
        volatility=volatility or 0.02,
    )
    return model.calculate(price, quantity, side, market)
