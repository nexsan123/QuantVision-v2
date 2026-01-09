"""
交易成本计算服务
PRD 4.4 交易成本配置
"""

from decimal import Decimal
from typing import Optional
import uuid
import math

from app.schemas.trading_cost import (
    CostMode,
    MarketCap,
    TradingCostConfig,
    SlippageConfig,
    MarketImpactConfig,
    CostEstimateRequest,
    CostEstimateResult,
    CostConfigUpdate,
    DEFAULT_COST_CONFIG,
    COST_MINIMUMS,
)


class CostService:
    """交易成本计算服务"""

    # 模拟配置存储
    _configs: dict[str, TradingCostConfig] = {}

    def __init__(self):
        """初始化服务"""
        self._init_default_config()

    def _init_default_config(self):
        """初始化默认配置"""
        # 创建默认用户配置
        default_config = TradingCostConfig(
            config_id=str(uuid.uuid4()),
            user_id="default",
            mode=CostMode.SIMPLE,
            commission_per_share=Decimal("0.005"),
            sec_fee_rate=Decimal("0.0000278"),
            taf_fee_per_share=Decimal("0.000166"),
            simple_slippage=0.001,
            slippage=SlippageConfig(),
            market_impact=MarketImpactConfig(),
            cost_buffer=0.2,
        )
        self._configs["default"] = default_config

    async def get_config(self, user_id: str = "default") -> TradingCostConfig:
        """获取用户成本配置"""
        if user_id not in self._configs:
            # 创建新用户的默认配置
            config = TradingCostConfig(
                config_id=str(uuid.uuid4()),
                user_id=user_id,
                mode=CostMode.SIMPLE,
                commission_per_share=Decimal("0.005"),
                sec_fee_rate=Decimal("0.0000278"),
                taf_fee_per_share=Decimal("0.000166"),
                simple_slippage=0.001,
                slippage=SlippageConfig(),
                market_impact=MarketImpactConfig(),
                cost_buffer=0.2,
            )
            self._configs[user_id] = config
        return self._configs[user_id]

    async def update_config(
        self,
        user_id: str,
        update: CostConfigUpdate,
    ) -> TradingCostConfig:
        """更新成本配置"""
        config = await self.get_config(user_id)

        # 更新字段
        if update.mode is not None:
            config.mode = update.mode

        if update.commission_per_share is not None:
            # 应用最低限制
            min_commission = COST_MINIMUMS["commission_per_share"]
            config.commission_per_share = max(update.commission_per_share, min_commission)

        if update.simple_slippage is not None:
            config.simple_slippage = max(update.simple_slippage, 0.0005)

        if update.slippage is not None:
            # 应用最低限制
            config.slippage = SlippageConfig(
                large_cap=max(update.slippage.large_cap, COST_MINIMUMS["slippage_large_cap"]),
                mid_cap=max(update.slippage.mid_cap, COST_MINIMUMS["slippage_mid_cap"]),
                small_cap=max(update.slippage.small_cap, COST_MINIMUMS["slippage_small_cap"]),
            )

        if update.market_impact is not None:
            config.market_impact = update.market_impact

        if update.cost_buffer is not None:
            config.cost_buffer = max(0, min(update.cost_buffer, 0.5))

        self._configs[user_id] = config
        return config

    async def reset_to_default(self, user_id: str) -> TradingCostConfig:
        """重置为默认配置"""
        config = TradingCostConfig(
            config_id=str(uuid.uuid4()),
            user_id=user_id,
            mode=CostMode.SIMPLE,
            commission_per_share=Decimal("0.005"),
            sec_fee_rate=Decimal("0.0000278"),
            taf_fee_per_share=Decimal("0.000166"),
            simple_slippage=0.001,
            slippage=SlippageConfig(),
            market_impact=MarketImpactConfig(),
            cost_buffer=0.2,
        )
        self._configs[user_id] = config
        return config

    async def estimate_cost(
        self,
        request: CostEstimateRequest,
        user_id: str = "default",
    ) -> CostEstimateResult:
        """估算交易成本"""
        config = await self.get_config(user_id)

        trade_value = request.quantity * request.price

        # 1. 佣金计算
        commission = float(config.commission_per_share) * request.quantity

        # 2. SEC费用 (仅卖出)
        sec_fee = 0.0
        if request.side == "sell":
            sec_fee = float(config.sec_fee_rate) * trade_value

        # 3. TAF费用
        taf_fee = float(config.taf_fee_per_share) * request.quantity

        # 4. 滑点成本
        slippage_cost = self._calculate_slippage(
            config=config,
            trade_value=trade_value,
            market_cap=request.market_cap,
        )

        # 5. 市场冲击成本 (专业模式)
        market_impact_cost = 0.0
        if config.mode == CostMode.PROFESSIONAL and config.market_impact and config.market_impact.enabled:
            market_impact_cost = self._calculate_market_impact(
                config=config,
                quantity=request.quantity,
                price=request.price,
                daily_volume=request.daily_volume,
                volatility=request.volatility,
            )

        # 汇总
        total_cost = commission + sec_fee + taf_fee + slippage_cost + market_impact_cost
        total_cost_pct = total_cost / trade_value if trade_value > 0 else 0
        cost_with_buffer = total_cost * (1 + config.cost_buffer)

        # 成本明细
        breakdown = {
            "commission": {
                "amount": round(commission, 4),
                "rate": f"${float(config.commission_per_share)}/股",
                "pct": round(commission / trade_value * 100, 4) if trade_value > 0 else 0,
            },
            "sec_fee": {
                "amount": round(sec_fee, 4),
                "rate": f"{float(config.sec_fee_rate) * 100:.6f}%",
                "note": "仅卖出收取",
            },
            "taf_fee": {
                "amount": round(taf_fee, 4),
                "rate": f"${float(config.taf_fee_per_share)}/股",
            },
            "slippage": {
                "amount": round(slippage_cost, 4),
                "rate": f"{self._get_slippage_rate(config, request.market_cap) * 100:.2f}%",
            },
            "market_impact": {
                "amount": round(market_impact_cost, 4),
                "enabled": config.mode == CostMode.PROFESSIONAL and config.market_impact and config.market_impact.enabled,
            },
        }

        return CostEstimateResult(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            trade_value=round(trade_value, 2),
            commission=round(commission, 4),
            sec_fee=round(sec_fee, 4),
            taf_fee=round(taf_fee, 4),
            slippage_cost=round(slippage_cost, 4),
            market_impact_cost=round(market_impact_cost, 4),
            total_cost=round(total_cost, 4),
            total_cost_pct=round(total_cost_pct, 6),
            cost_with_buffer=round(cost_with_buffer, 4),
            breakdown=breakdown,
        )

    def _calculate_slippage(
        self,
        config: TradingCostConfig,
        trade_value: float,
        market_cap: Optional[MarketCap],
    ) -> float:
        """计算滑点成本"""
        slippage_rate = self._get_slippage_rate(config, market_cap)
        return trade_value * slippage_rate

    def _get_slippage_rate(
        self,
        config: TradingCostConfig,
        market_cap: Optional[MarketCap],
    ) -> float:
        """获取滑点率"""
        if config.mode == CostMode.SIMPLE:
            return config.simple_slippage

        # 专业模式
        if config.slippage is None:
            return config.simple_slippage

        if market_cap == MarketCap.LARGE:
            return config.slippage.large_cap
        elif market_cap == MarketCap.MID:
            return config.slippage.mid_cap
        elif market_cap == MarketCap.SMALL:
            return config.slippage.small_cap
        else:
            # 默认使用中盘股滑点
            return config.slippage.mid_cap

    def _calculate_market_impact(
        self,
        config: TradingCostConfig,
        quantity: int,
        price: float,
        daily_volume: Optional[int],
        volatility: Optional[float],
    ) -> float:
        """
        计算市场冲击成本 (Almgren-Chriss 模型)

        市场冲击 = η × σ × √(Q/ADV) × 交易额

        η: 冲击系数 (0.05-0.5)
        σ: 日波动率
        Q: 交易量
        ADV: 日均成交量
        """
        if not config.market_impact or not config.market_impact.enabled:
            return 0.0

        # 默认值
        if daily_volume is None or daily_volume <= 0:
            daily_volume = 1_000_000  # 默认100万股
        if volatility is None or volatility <= 0:
            volatility = 0.02  # 默认2%日波动率

        eta = config.market_impact.impact_coefficient
        trade_value = quantity * price

        # Q/ADV 比例
        volume_ratio = quantity / daily_volume

        # 市场冲击 = η × σ × √(Q/ADV) × 交易额
        impact = eta * volatility * math.sqrt(volume_ratio) * trade_value

        return impact

    def get_defaults(self) -> dict:
        """获取默认配置"""
        return {
            "simple": DEFAULT_COST_CONFIG["simple"],
            "professional": DEFAULT_COST_CONFIG["professional"],
            "minimums": {
                "commission_per_share": float(COST_MINIMUMS["commission_per_share"]),
                "slippage_large_cap": COST_MINIMUMS["slippage_large_cap"],
                "slippage_mid_cap": COST_MINIMUMS["slippage_mid_cap"],
                "slippage_small_cap": COST_MINIMUMS["slippage_small_cap"],
            },
        }


# 单例服务实例
cost_service = CostService()
