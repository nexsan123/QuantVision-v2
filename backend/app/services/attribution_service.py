"""
Phase 13: \u5f52\u56e0\u4e0e\u62a5\u8868 - \u5f52\u56e0\u670d\u52a1

\u5305\u542b:
- Brinson \u5f52\u56e0\u5206\u6790
- \u56e0\u5b50\u5f52\u56e0\u5206\u6790
- TCA \u4ea4\u6613\u6210\u672c\u5206\u6790
"""

from datetime import date, datetime
from typing import Any

import numpy as np
import structlog

from app.schemas.attribution import (
    AttributionSummary,
    BrinsonAttribution,
    BrinsonAttributionRequest,
    ComprehensiveAttribution,
    FactorAttribution,
    FactorAttributionRequest,
    FactorExposure,
    RiskFactorType,
    SectorAttribution,
    SectorType,
    StrategyTCA,
    TCABenchmark,
    TCARequest,
    TimePeriod,
    TradeCostBreakdown,
    TradeTCA,
)

logger = structlog.get_logger()


# ============ Brinson \u5f52\u56e0\u670d\u52a1 ============

class BrinsonAttributionService:
    """
    Brinson \u5f52\u56e0\u5206\u6790\u670d\u52a1

    \u5b9e\u73b0 Brinson-Fachler \u6a21\u578b:
    - \u914d\u7f6e\u6548\u5e94 (Allocation Effect): (w_p - w_b) * (R_b_sector - R_b_total)
    - \u9009\u80a1\u6548\u5e94 (Selection Effect): w_b * (R_p_sector - R_b_sector)
    - \u4ea4\u4e92\u6548\u5e94 (Interaction Effect): (w_p - w_b) * (R_p_sector - R_b_sector)
    """

    # \u884c\u4e1a\u540d\u79f0\u6620\u5c04
    SECTOR_NAMES = {
        SectorType.TECHNOLOGY: "\u79d1\u6280",
        SectorType.HEALTHCARE: "\u533b\u7597\u4fdd\u5065",
        SectorType.FINANCIALS: "\u91d1\u878d",
        SectorType.CONSUMER_DISCRETIONARY: "\u53ef\u9009\u6d88\u8d39",
        SectorType.CONSUMER_STAPLES: "\u5fc5\u9700\u6d88\u8d39",
        SectorType.INDUSTRIALS: "\u5de5\u4e1a",
        SectorType.ENERGY: "\u80fd\u6e90",
        SectorType.MATERIALS: "\u539f\u6750\u6599",
        SectorType.UTILITIES: "\u516c\u7528\u4e8b\u4e1a",
        SectorType.REAL_ESTATE: "\u623f\u5730\u4ea7",
        SectorType.COMMUNICATION_SERVICES: "\u901a\u4fe1\u670d\u52a1",
    }

    async def calculate(
        self,
        request: BrinsonAttributionRequest,
        portfolio_data: dict[str, Any],
        benchmark_data: dict[str, Any],
    ) -> BrinsonAttribution:
        """
        \u8ba1\u7b97 Brinson \u5f52\u56e0

        Args:
            request: \u5f52\u56e0\u8bf7\u6c42
            portfolio_data: \u7ec4\u5408\u6570\u636e {\u884c\u4e1a: {weight, return}}
            benchmark_data: \u57fa\u51c6\u6570\u636e {\u884c\u4e1a: {weight, return}}
        """
        logger.info(
            "brinson_attribution_start",
            portfolio_id=request.portfolio_id,
            benchmark_id=request.benchmark_id,
        )

        # \u8ba1\u7b97\u603b\u6536\u76ca
        portfolio_return = sum(
            d["weight"] * d["return"]
            for d in portfolio_data.values()
        )
        benchmark_return = sum(
            d["weight"] * d["return"]
            for d in benchmark_data.values()
        )
        excess_return = portfolio_return - benchmark_return

        # \u8ba1\u7b97\u5404\u884c\u4e1a\u5f52\u56e0
        sector_details = []
        total_allocation = 0.0
        total_selection = 0.0
        total_interaction = 0.0

        for sector in SectorType:
            p_data = portfolio_data.get(sector.value, {"weight": 0, "return": 0})
            b_data = benchmark_data.get(sector.value, {"weight": 0, "return": 0})

            w_p = p_data["weight"]
            w_b = b_data["weight"]
            r_p = p_data["return"]
            r_b = b_data["return"]

            # Brinson-Fachler \u5206\u89e3
            allocation = (w_p - w_b) * (r_b - benchmark_return)
            selection = w_b * (r_p - r_b)
            interaction = (w_p - w_b) * (r_p - r_b)
            total_effect = allocation + selection + interaction

            total_allocation += allocation
            total_selection += selection
            total_interaction += interaction

            sector_details.append(SectorAttribution(
                sector=sector,
                sector_name=self.SECTOR_NAMES.get(sector, sector.value),
                portfolio_weight=w_p,
                benchmark_weight=w_b,
                active_weight=w_p - w_b,
                portfolio_return=r_p,
                benchmark_return=r_b,
                active_return=r_p - r_b,
                allocation_effect=allocation,
                selection_effect=selection,
                interaction_effect=interaction,
                total_effect=total_effect,
            ))

        # \u751f\u6210\u89e3\u8bfb
        interpretation = self._generate_interpretation(
            portfolio_return,
            benchmark_return,
            total_allocation,
            total_selection,
            total_interaction,
            sector_details,
        )

        result = BrinsonAttribution(
            period=TimePeriod(start=request.start_date, end=request.end_date),
            portfolio_return=portfolio_return,
            benchmark_return=benchmark_return,
            excess_return=excess_return,
            total_allocation_effect=total_allocation,
            total_selection_effect=total_selection,
            total_interaction_effect=total_interaction,
            sector_details=sector_details,
            interpretation=interpretation,
        )

        logger.info(
            "brinson_attribution_complete",
            excess_return=f"{excess_return:.2%}",
            allocation=f"{total_allocation:.2%}",
            selection=f"{total_selection:.2%}",
        )

        return result

    def _generate_interpretation(
        self,
        portfolio_return: float,
        benchmark_return: float,
        allocation: float,
        selection: float,
        interaction: float,
        sector_details: list[SectorAttribution],
    ) -> str:
        """\u751f\u6210\u5f52\u56e0\u89e3\u8bfb"""
        excess = portfolio_return - benchmark_return

        lines = []
        lines.append(f"\u7ec4\u5408\u6536\u76ca {portfolio_return:.2%}\uff0c\u57fa\u51c6\u6536\u76ca {benchmark_return:.2%}\uff0c")

        if excess > 0:
            lines.append(f"\u8d85\u989d\u6536\u76ca +{excess:.2%}\u3002")
        else:
            lines.append(f"\u8d85\u989d\u6536\u76ca {excess:.2%}\u3002")

        # \u5206\u6790\u4e3b\u8981\u8d21\u732e
        if abs(allocation) > abs(selection):
            lines.append(f"\u914d\u7f6e\u6548\u5e94({allocation:.2%})\u8d21\u732e\u8f83\u5927\uff0c")
        else:
            lines.append(f"\u9009\u80a1\u6548\u5e94({selection:.2%})\u8d21\u732e\u8f83\u5927\uff0c")

        # \u627e\u51fa\u8d21\u732e\u6700\u5927\u7684\u884c\u4e1a
        sorted_sectors = sorted(
            sector_details,
            key=lambda x: abs(x.total_effect),
            reverse=True
        )

        if sorted_sectors:
            top = sorted_sectors[0]
            lines.append(f"\u8d21\u732e\u6700\u5927\u7684\u884c\u4e1a\u662f{top.sector_name}({top.total_effect:.2%})\u3002")

        return "".join(lines)

    async def calculate_with_mock_data(
        self,
        request: BrinsonAttributionRequest,
    ) -> BrinsonAttribution:
        """
        \u4f7f\u7528\u6a21\u62df\u6570\u636e\u8ba1\u7b97 Brinson \u5f52\u56e0
        \u7528\u4e8e\u6f14\u793a\u548c\u6d4b\u8bd5
        """
        np.random.seed(42)

        # \u751f\u6210\u6a21\u62df\u7ec4\u5408\u6570\u636e
        portfolio_data = {}
        benchmark_data = {}

        # S&P 500 \u884c\u4e1a\u6743\u91cd (\u8fd1\u4f3c)
        benchmark_weights = {
            "technology": 0.28,
            "healthcare": 0.13,
            "financials": 0.12,
            "consumer_discretionary": 0.10,
            "communication_services": 0.09,
            "industrials": 0.08,
            "consumer_staples": 0.07,
            "energy": 0.05,
            "utilities": 0.03,
            "real_estate": 0.03,
            "materials": 0.02,
        }

        for sector in SectorType:
            b_weight = benchmark_weights.get(sector.value, 0.05)
            b_return = np.random.normal(0.08, 0.15)  # \u5e74\u5316\u6536\u76ca

            # \u7ec4\u5408\u7a0d\u6709\u504f\u79bb
            p_weight = b_weight + np.random.uniform(-0.05, 0.05)
            p_weight = max(0, min(1, p_weight))
            p_return = b_return + np.random.normal(0.02, 0.05)

            portfolio_data[sector.value] = {"weight": p_weight, "return": p_return}
            benchmark_data[sector.value] = {"weight": b_weight, "return": b_return}

        # \u5f52\u4e00\u5316\u6743\u91cd
        p_total = sum(d["weight"] for d in portfolio_data.values())
        b_total = sum(d["weight"] for d in benchmark_data.values())

        for sector in portfolio_data:
            portfolio_data[sector]["weight"] /= p_total
        for sector in benchmark_data:
            benchmark_data[sector]["weight"] /= b_total

        return await self.calculate(request, portfolio_data, benchmark_data)


# ============ \u56e0\u5b50\u5f52\u56e0\u670d\u52a1 ============

class FactorAttributionService:
    """
    \u56e0\u5b50\u5f52\u56e0\u5206\u6790\u670d\u52a1

    \u57fa\u4e8e\u591a\u56e0\u5b50\u6a21\u578b\u5206\u89e3\u6536\u76ca:
    R_p = \u03b1 + \u03b2_mkt * R_mkt + \u03b2_smb * R_smb + \u03b2_hml * R_hml + ... + \u03b5
    """

    # \u56e0\u5b50\u540d\u79f0\u6620\u5c04
    FACTOR_NAMES = {
        RiskFactorType.MARKET: "\u5e02\u573a",
        RiskFactorType.SIZE: "\u89c4\u6a21",
        RiskFactorType.VALUE: "\u4ef7\u503c",
        RiskFactorType.MOMENTUM: "\u52a8\u91cf",
        RiskFactorType.QUALITY: "\u8d28\u91cf",
        RiskFactorType.VOLATILITY: "\u6ce2\u52a8",
        RiskFactorType.DIVIDEND: "\u80a1\u606f",
        RiskFactorType.GROWTH: "\u6210\u957f",
    }

    # \u9ed8\u8ba4\u56e0\u5b50\u53c2\u6570 (\u6a21\u62df)
    DEFAULT_FACTOR_PARAMS = {
        RiskFactorType.MARKET: {"premium": 0.06, "vol": 0.15},
        RiskFactorType.SIZE: {"premium": 0.02, "vol": 0.10},
        RiskFactorType.VALUE: {"premium": 0.03, "vol": 0.12},
        RiskFactorType.MOMENTUM: {"premium": 0.04, "vol": 0.14},
        RiskFactorType.QUALITY: {"premium": 0.02, "vol": 0.08},
        RiskFactorType.VOLATILITY: {"premium": -0.01, "vol": 0.18},
        RiskFactorType.DIVIDEND: {"premium": 0.015, "vol": 0.06},
        RiskFactorType.GROWTH: {"premium": 0.025, "vol": 0.11},
    }

    async def calculate(
        self,
        request: FactorAttributionRequest,
        portfolio_returns: np.ndarray,
        factor_returns: dict[RiskFactorType, np.ndarray],
        benchmark_returns: np.ndarray | None = None,
    ) -> FactorAttribution:
        """
        \u8ba1\u7b97\u56e0\u5b50\u5f52\u56e0

        Args:
            request: \u5f52\u56e0\u8bf7\u6c42
            portfolio_returns: \u7ec4\u5408\u65e5\u6536\u76ca\u7387\u5e8f\u5217
            factor_returns: \u5404\u56e0\u5b50\u6536\u76ca\u7387\u5e8f\u5217
            benchmark_returns: \u57fa\u51c6\u6536\u76ca\u7387\u5e8f\u5217
        """
        logger.info(
            "factor_attribution_start",
            portfolio_id=request.portfolio_id,
            factors=len(factor_returns),
        )

        # \u56de\u5f52\u5206\u6790
        factors_to_use = request.factors or list(RiskFactorType)

        # \u6784\u5efa\u56e0\u5b50\u77e9\u9635
        X = np.column_stack([
            factor_returns.get(f, np.zeros_like(portfolio_returns))
            for f in factors_to_use
        ])
        X = np.column_stack([np.ones(len(portfolio_returns)), X])  # \u6dfb\u52a0\u622a\u8ddd

        # OLS \u56de\u5f52
        try:
            betas, residuals, _, _ = np.linalg.lstsq(X, portfolio_returns, rcond=None)
        except np.linalg.LinAlgError:
            betas = np.zeros(len(factors_to_use) + 1)
            residuals = np.array([np.var(portfolio_returns)])

        alpha = betas[0]
        factor_betas = betas[1:]

        # \u8ba1\u7b97\u56e0\u5b50\u8d21\u732e
        factor_contributions = []
        total_factor_return = 0.0

        for i, factor in enumerate(factors_to_use):
            beta = factor_betas[i] if i < len(factor_betas) else 0
            f_returns = factor_returns.get(factor, np.zeros_like(portfolio_returns))
            f_mean_return = float(np.mean(f_returns)) * 252  # \u5e74\u5316
            contribution = beta * f_mean_return
            total_factor_return += contribution

            # \u8ba1\u7b97 t \u7edf\u8ba1\u91cf
            if len(residuals) > 0 and residuals[0] > 0:
                se = np.sqrt(residuals[0] / (len(portfolio_returns) - len(betas)))
                t_stat = beta / se if se > 0 else 0
            else:
                t_stat = 0

            factor_contributions.append(FactorExposure(
                factor=factor,
                factor_name=self.FACTOR_NAMES.get(factor, factor.value),
                exposure=beta,
                factor_return=f_mean_return,
                contribution=contribution,
                t_stat=float(t_stat),
            ))

        # \u8ba1\u7b97\u603b\u6536\u76ca\u548c\u7279\u8d28\u6536\u76ca
        total_return = float(np.mean(portfolio_returns)) * 252
        specific_return = total_return - total_factor_return

        # \u8ba1\u7b97\u57fa\u51c6\u6536\u76ca
        if benchmark_returns is not None:
            benchmark_return = float(np.mean(benchmark_returns)) * 252
            active_return = total_return - benchmark_return
        else:
            benchmark_return = 0.0
            active_return = total_return

        # \u98ce\u9669\u6307\u6807
        tracking_error = 0.0
        if benchmark_returns is not None:
            tracking_error = float(np.std(portfolio_returns - benchmark_returns)) * np.sqrt(252)

        information_ratio = active_return / tracking_error if tracking_error > 0 else 0
        active_risk = float(np.std(portfolio_returns)) * np.sqrt(252)

        # \u751f\u6210\u89e3\u8bfb
        interpretation = self._generate_interpretation(
            total_return,
            total_factor_return,
            specific_return,
            factor_contributions,
        )

        result = FactorAttribution(
            period=TimePeriod(start=request.start_date, end=request.end_date),
            total_return=total_return,
            benchmark_return=benchmark_return,
            active_return=active_return,
            factor_contributions=factor_contributions,
            total_factor_return=total_factor_return,
            specific_return=specific_return,
            information_ratio=information_ratio,
            tracking_error=tracking_error,
            active_risk=active_risk,
            interpretation=interpretation,
        )

        logger.info(
            "factor_attribution_complete",
            total_return=f"{total_return:.2%}",
            factor_return=f"{total_factor_return:.2%}",
            specific_return=f"{specific_return:.2%}",
        )

        return result

    def _generate_interpretation(
        self,
        total_return: float,
        factor_return: float,
        specific_return: float,
        contributions: list[FactorExposure],
    ) -> str:
        """\u751f\u6210\u56e0\u5b50\u5f52\u56e0\u89e3\u8bfb"""
        lines = []
        lines.append(f"\u7ec4\u5408\u603b\u6536\u76ca {total_return:.2%}\uff0c")
        lines.append(f"\u5176\u4e2d\u56e0\u5b50\u8d21\u732e {factor_return:.2%}\uff0c")
        lines.append(f"\u7279\u8d28\u6536\u76ca(\u9009\u80a1\u80fd\u529b) {specific_return:.2%}\u3002")

        # \u627e\u51fa\u8d21\u732e\u6700\u5927\u7684\u56e0\u5b50
        sorted_factors = sorted(
            contributions,
            key=lambda x: abs(x.contribution),
            reverse=True,
        )

        if sorted_factors:
            top = sorted_factors[0]
            lines.append(f"\u8d21\u732e\u6700\u5927\u7684\u56e0\u5b50\u662f{top.factor_name}")
            lines.append(f"(\u66b4\u9732{top.exposure:.2f}\uff0c\u8d21\u732e{top.contribution:.2%})\u3002")

        return "".join(lines)

    async def calculate_with_mock_data(
        self,
        request: FactorAttributionRequest,
    ) -> FactorAttribution:
        """
        \u4f7f\u7528\u6a21\u62df\u6570\u636e\u8ba1\u7b97\u56e0\u5b50\u5f52\u56e0
        """
        np.random.seed(42)
        n_days = 252  # \u4e00\u5e74\u4ea4\u6613\u65e5

        # \u751f\u6210\u56e0\u5b50\u6536\u76ca
        factor_returns = {}
        for factor in RiskFactorType:
            params = self.DEFAULT_FACTOR_PARAMS.get(
                factor,
                {"premium": 0.02, "vol": 0.10}
            )
            daily_premium = params["premium"] / 252
            daily_vol = params["vol"] / np.sqrt(252)
            factor_returns[factor] = np.random.normal(daily_premium, daily_vol, n_days)

        # \u751f\u6210\u7ec4\u5408\u6536\u76ca (\u56e0\u5b50\u52a0\u6743 + \u7279\u8d28\u6536\u76ca)
        portfolio_returns = np.zeros(n_days)
        exposures = {
            RiskFactorType.MARKET: 1.1,
            RiskFactorType.SIZE: 0.3,
            RiskFactorType.VALUE: -0.2,
            RiskFactorType.MOMENTUM: 0.4,
            RiskFactorType.QUALITY: 0.2,
        }

        for factor, beta in exposures.items():
            portfolio_returns += beta * factor_returns[factor]

        # \u6dfb\u52a0 alpha \u548c\u566a\u97f3
        portfolio_returns += 0.02 / 252  # 2% \u5e74\u5316 alpha
        portfolio_returns += np.random.normal(0, 0.01, n_days)  # \u7279\u8d28\u98ce\u9669

        # \u751f\u6210\u57fa\u51c6\u6536\u76ca
        benchmark_returns = factor_returns[RiskFactorType.MARKET]

        return await self.calculate(
            request,
            portfolio_returns,
            factor_returns,
            benchmark_returns,
        )


# ============ TCA \u670d\u52a1 ============

class TCAService:
    """
    \u4ea4\u6613\u6210\u672c\u5206\u6790 (Transaction Cost Analysis) \u670d\u52a1

    \u5206\u6790\u5185\u5bb9:
    - \u6267\u884c\u7f3a\u53e3 (Implementation Shortfall)
    - \u4f63\u91d1\u3001\u6ed1\u70b9\u3001\u5e02\u573a\u51b2\u51fb
    - \u65f6\u673a\u6210\u672c\u3001\u673a\u4f1a\u6210\u672c
    """

    async def analyze(
        self,
        request: TCARequest,
        trades: list[dict[str, Any]],
        market_data: dict[str, Any] | None = None,
    ) -> StrategyTCA:
        """
        \u5206\u6790\u4ea4\u6613\u6210\u672c

        Args:
            request: TCA \u8bf7\u6c42
            trades: \u4ea4\u6613\u5217\u8868
            market_data: \u5e02\u573a\u6570\u636e (VWAP/TWAP \u7b49)
        """
        logger.info(
            "tca_analysis_start",
            portfolio_id=request.portfolio_id,
            trades=len(trades),
        )

        trade_tcas = []
        total_costs = TradeCostBreakdown()
        buy_costs = TradeCostBreakdown()
        sell_costs = TradeCostBreakdown()

        total_volume = 0.0
        total_notional = 0.0

        for trade in trades:
            tca = self._analyze_single_trade(trade, request.benchmark, market_data)
            trade_tcas.append(tca)

            # \u7d2f\u52a0\u6210\u672c
            total_costs.commission += tca.costs.commission
            total_costs.slippage += tca.costs.slippage
            total_costs.market_impact += tca.costs.market_impact
            total_costs.timing_cost += tca.costs.timing_cost
            total_costs.opportunity_cost += tca.costs.opportunity_cost
            total_costs.total_cost += tca.costs.total_cost

            notional = tca.execution_price * tca.quantity
            total_volume += tca.quantity
            total_notional += notional

            # \u6309\u65b9\u5411\u7d2f\u52a0
            if tca.side == "buy":
                buy_costs.commission += tca.costs.commission
                buy_costs.slippage += tca.costs.slippage
                buy_costs.market_impact += tca.costs.market_impact
                buy_costs.total_cost += tca.costs.total_cost
            else:
                sell_costs.commission += tca.costs.commission
                sell_costs.slippage += tca.costs.slippage
                sell_costs.market_impact += tca.costs.market_impact
                sell_costs.total_cost += tca.costs.total_cost

        # \u8ba1\u7b97\u5e73\u5747\u6210\u672c
        avg_cost_bps = (total_costs.total_cost / total_notional * 10000) if total_notional > 0 else 0

        # \u6309\u65f6\u6bb5\u5206\u7ec4
        by_time_of_day = self._group_by_time(trade_tcas)

        # \u6309\u80a1\u7968\u5206\u7ec4
        by_symbol = self._group_by_symbol(trade_tcas)

        # \u57fa\u51c6\u5bf9\u6bd4
        vs_benchmark = self._calculate_benchmark_comparison(trade_tcas)

        result = StrategyTCA(
            period=TimePeriod(start=request.start_date, end=request.end_date),
            total_trades=len(trade_tcas),
            total_volume=total_volume,
            total_notional=total_notional,
            total_costs=total_costs,
            avg_cost_bps=avg_cost_bps,
            buy_costs=buy_costs,
            sell_costs=sell_costs,
            by_time_of_day=by_time_of_day,
            by_symbol=by_symbol,
            vs_benchmark=vs_benchmark,
            trades=trade_tcas,
        )

        logger.info(
            "tca_analysis_complete",
            total_trades=len(trade_tcas),
            avg_cost_bps=f"{avg_cost_bps:.2f}",
        )

        return result

    def _analyze_single_trade(
        self,
        trade: dict[str, Any],
        benchmark: TCABenchmark,
        market_data: dict[str, Any] | None,
    ) -> TradeTCA:
        """\u5206\u6790\u5355\u7b14\u4ea4\u6613"""
        symbol = trade.get("symbol", "")
        side = trade.get("side", "buy")
        quantity = trade.get("quantity", 0)
        decision_price = trade.get("decision_price", 0)
        execution_price = trade.get("execution_price", 0)

        # \u83b7\u53d6\u57fa\u51c6\u4ef7\u683c
        if market_data and symbol in market_data:
            md = market_data[symbol]
            if benchmark == TCABenchmark.VWAP:
                benchmark_price = md.get("vwap", execution_price)
            elif benchmark == TCABenchmark.TWAP:
                benchmark_price = md.get("twap", execution_price)
            else:
                benchmark_price = md.get("arrival", decision_price)
        else:
            benchmark_price = decision_price

        arrival_price = trade.get("arrival_price", decision_price)

        # \u8ba1\u7b97\u6267\u884c\u7f3a\u53e3
        if side == "buy":
            impl_shortfall = (execution_price - decision_price) * quantity
        else:
            impl_shortfall = (decision_price - execution_price) * quantity

        impl_shortfall_bps = (impl_shortfall / (decision_price * quantity)) * 10000 if decision_price > 0 else 0

        # \u6210\u672c\u5206\u89e3
        commission = trade.get("commission", quantity * 0.005)  # \u9ed8\u8ba4 $0.005/\u80a1
        slippage = abs(execution_price - arrival_price) * quantity
        market_impact = abs(execution_price - benchmark_price) * quantity * 0.3
        timing_cost = abs(arrival_price - decision_price) * quantity
        opportunity_cost = trade.get("unfilled_quantity", 0) * abs(execution_price - decision_price)

        costs = TradeCostBreakdown(
            commission=commission,
            slippage=slippage,
            market_impact=market_impact,
            timing_cost=timing_cost,
            opportunity_cost=opportunity_cost,
            total_cost=commission + slippage + market_impact + timing_cost + opportunity_cost,
        )

        # \u65f6\u95f4
        decision_time = trade.get("decision_time", datetime.now())
        execution_time = trade.get("execution_time", datetime.now())
        if isinstance(decision_time, str):
            decision_time = datetime.fromisoformat(decision_time)
        if isinstance(execution_time, str):
            execution_time = datetime.fromisoformat(execution_time)

        execution_duration = (execution_time - decision_time).total_seconds()

        return TradeTCA(
            trade_id=trade.get("id", ""),
            symbol=symbol,
            side=side,
            quantity=quantity,
            decision_price=decision_price,
            arrival_price=arrival_price,
            execution_price=execution_price,
            benchmark_price=benchmark_price,
            implementation_shortfall=impl_shortfall,
            implementation_shortfall_bps=impl_shortfall_bps,
            costs=costs,
            decision_time=decision_time,
            execution_time=execution_time,
            execution_duration=execution_duration,
            market_volatility=trade.get("volatility", 0.02),
            volume_participation=trade.get("volume_participation", 0.01),
        )

    def _group_by_time(self, trades: list[TradeTCA]) -> list[dict[str, Any]]:
        """\u6309\u65f6\u6bb5\u5206\u7ec4"""
        periods = {
            "09:30-10:00": [],
            "10:00-11:00": [],
            "11:00-12:00": [],
            "12:00-13:00": [],
            "13:00-14:00": [],
            "14:00-15:00": [],
            "15:00-16:00": [],
        }

        for trade in trades:
            hour = trade.execution_time.hour
            minute = trade.execution_time.minute

            if hour == 9 and minute >= 30:
                periods["09:30-10:00"].append(trade)
            elif hour == 10:
                periods["10:00-11:00"].append(trade)
            elif hour == 11:
                periods["11:00-12:00"].append(trade)
            elif hour == 12:
                periods["12:00-13:00"].append(trade)
            elif hour == 13:
                periods["13:00-14:00"].append(trade)
            elif hour == 14:
                periods["14:00-15:00"].append(trade)
            elif hour == 15:
                periods["15:00-16:00"].append(trade)

        result = []
        for period, period_trades in periods.items():
            if period_trades:
                total_cost = sum(t.costs.total_cost for t in period_trades)
                total_notional = sum(t.execution_price * t.quantity for t in period_trades)
                avg_bps = (total_cost / total_notional * 10000) if total_notional > 0 else 0

                result.append({
                    "period": period,
                    "avgCostBps": avg_bps,
                    "trades": len(period_trades),
                })

        return result

    def _group_by_symbol(self, trades: list[TradeTCA]) -> list[dict[str, Any]]:
        """\u6309\u80a1\u7968\u5206\u7ec4"""
        by_symbol: dict[str, list[TradeTCA]] = {}

        for trade in trades:
            if trade.symbol not in by_symbol:
                by_symbol[trade.symbol] = []
            by_symbol[trade.symbol].append(trade)

        result = []
        for symbol, symbol_trades in by_symbol.items():
            total_cost = sum(t.costs.total_cost for t in symbol_trades)
            total_notional = sum(t.execution_price * t.quantity for t in symbol_trades)
            avg_bps = (total_cost / total_notional * 10000) if total_notional > 0 else 0

            result.append({
                "symbol": symbol,
                "avgCostBps": avg_bps,
                "trades": len(symbol_trades),
                "totalNotional": total_notional,
            })

        return sorted(result, key=lambda x: x["totalNotional"], reverse=True)

    def _calculate_benchmark_comparison(
        self,
        trades: list[TradeTCA],
    ) -> dict[str, float]:
        """\u8ba1\u7b97\u57fa\u51c6\u5bf9\u6bd4"""
        vwap_slippage = 0.0
        twap_slippage = 0.0
        arrival_slippage = 0.0
        total_notional = 0.0

        for trade in trades:
            notional = trade.execution_price * trade.quantity
            total_notional += notional

            # \u7b80\u5316\u8ba1\u7b97\uff0c\u5b9e\u9645\u9700\u8981\u771f\u5b9e\u5e02\u573a\u6570\u636e
            vwap_slippage += abs(trade.execution_price - trade.benchmark_price) * trade.quantity
            twap_slippage += abs(trade.execution_price - trade.benchmark_price) * trade.quantity * 0.9
            arrival_slippage += abs(trade.execution_price - trade.arrival_price) * trade.quantity

        return {
            "vwapSlippage": (vwap_slippage / total_notional * 10000) if total_notional > 0 else 0,
            "twapSlippage": (twap_slippage / total_notional * 10000) if total_notional > 0 else 0,
            "arrivalSlippage": (arrival_slippage / total_notional * 10000) if total_notional > 0 else 0,
        }

    async def analyze_with_mock_data(
        self,
        request: TCARequest,
    ) -> StrategyTCA:
        """
        \u4f7f\u7528\u6a21\u62df\u6570\u636e\u8fdb\u884c TCA \u5206\u6790
        """
        np.random.seed(42)

        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
        trades = []

        for i in range(50):
            symbol = np.random.choice(symbols)
            side = np.random.choice(["buy", "sell"])
            quantity = np.random.randint(100, 1000)

            base_price = {
                "AAPL": 180, "MSFT": 380, "GOOGL": 140,
                "AMZN": 180, "NVDA": 480
            }[symbol]

            decision_price = base_price * (1 + np.random.normal(0, 0.01))
            arrival_price = decision_price * (1 + np.random.normal(0, 0.002))
            execution_price = arrival_price * (1 + np.random.normal(0, 0.001))

            # \u968f\u673a\u65f6\u95f4
            hour = np.random.randint(9, 16)
            minute = np.random.randint(0, 60)
            if hour == 9:
                minute = max(30, minute)

            decision_time = datetime(2024, 1, 15, hour, minute, 0)
            execution_time = datetime(
                2024, 1, 15, hour,
                min(59, minute + np.random.randint(1, 10)),
                np.random.randint(0, 60)
            )

            trades.append({
                "id": f"TRD-{i+1:04d}",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "decision_price": decision_price,
                "arrival_price": arrival_price,
                "execution_price": execution_price,
                "decision_time": decision_time,
                "execution_time": execution_time,
                "commission": quantity * 0.005,
                "volatility": np.random.uniform(0.01, 0.03),
                "volume_participation": np.random.uniform(0.005, 0.02),
            })

        return await self.analyze(request, trades)


# ============ \u7efc\u5408\u5f52\u56e0\u670d\u52a1 ============

class ComprehensiveAttributionService:
    """
    \u7efc\u5408\u5f52\u56e0\u670d\u52a1

    \u6574\u5408 Brinson\u3001\u56e0\u5b50\u5f52\u56e0\u548c TCA
    """

    def __init__(self):
        self.brinson_service = BrinsonAttributionService()
        self.factor_service = FactorAttributionService()
        self.tca_service = TCAService()

    async def generate_report(
        self,
        portfolio_id: str,
        portfolio_name: str,
        benchmark_id: str,
        benchmark_name: str,
        start_date: date,
        end_date: date,
        include_brinson: bool = True,
        include_factor: bool = True,
        include_tca: bool = True,
    ) -> ComprehensiveAttribution:
        """
        \u751f\u6210\u7efc\u5408\u5f52\u56e0\u62a5\u544a
        """
        logger.info(
            "comprehensive_attribution_start",
            portfolio_id=portfolio_id,
            start_date=str(start_date),
            end_date=str(end_date),
        )

        brinson = None
        factor = None
        tca = None

        # Brinson \u5f52\u56e0
        if include_brinson:
            brinson_request = BrinsonAttributionRequest(
                portfolio_id=portfolio_id,
                benchmark_id=benchmark_id,
                start_date=start_date,
                end_date=end_date,
            )
            brinson = await self.brinson_service.calculate_with_mock_data(brinson_request)

        # \u56e0\u5b50\u5f52\u56e0
        if include_factor:
            factor_request = FactorAttributionRequest(
                portfolio_id=portfolio_id,
                benchmark_id=benchmark_id,
                start_date=start_date,
                end_date=end_date,
            )
            factor = await self.factor_service.calculate_with_mock_data(factor_request)

        # TCA
        if include_tca:
            tca_request = TCARequest(
                portfolio_id=portfolio_id,
                start_date=start_date,
                end_date=end_date,
            )
            tca = await self.tca_service.analyze_with_mock_data(tca_request)

        # \u6c47\u603b
        portfolio_return = brinson.portfolio_return if brinson else (factor.total_return if factor else 0)
        benchmark_return = brinson.benchmark_return if brinson else (factor.benchmark_return if factor else 0)
        excess_return = portfolio_return - benchmark_return

        summary = AttributionSummary(
            portfolio_return=portfolio_return,
            benchmark_return=benchmark_return,
            excess_return=excess_return,
            information_ratio=factor.information_ratio if factor else 0,
            tracking_error=factor.tracking_error if factor else 0,
            sharpe_ratio=portfolio_return / (factor.active_risk if factor and factor.active_risk > 0 else 0.15),
            max_drawdown=-0.12,  # \u6a21\u62df\u6570\u636e
        )

        # \u751f\u6210\u65f6\u5e8f\u6570\u636e (\u6a21\u62df)
        np.random.seed(42)
        n_days = (end_date - start_date).days
        dates = [start_date.isoformat()]
        portfolio_values = [100.0]
        benchmark_values = [100.0]
        excess_returns = [0.0]
        drawdowns = [0.0]

        for i in range(1, min(n_days, 252)):
            dates.append((start_date.replace(day=1) + __import__('datetime').timedelta(days=i)).isoformat())
            p_ret = np.random.normal(portfolio_return / 252, 0.015)
            b_ret = np.random.normal(benchmark_return / 252, 0.012)

            portfolio_values.append(portfolio_values[-1] * (1 + p_ret))
            benchmark_values.append(benchmark_values[-1] * (1 + b_ret))
            excess_returns.append((portfolio_values[-1] / benchmark_values[-1] - 1))

            peak = max(portfolio_values)
            drawdowns.append((portfolio_values[-1] / peak - 1))

        result = ComprehensiveAttribution(
            period=TimePeriod(start=start_date, end=end_date),
            portfolio_id=portfolio_id,
            portfolio_name=portfolio_name,
            benchmark_id=benchmark_id,
            benchmark_name=benchmark_name,
            summary=summary,
            brinson=brinson,
            factor=factor,
            tca=tca,
            time_series={
                "dates": dates,
                "portfolio_values": portfolio_values,
                "benchmark_values": benchmark_values,
                "excess_returns": excess_returns,
                "drawdowns": drawdowns,
            },
            generated_at=datetime.now(),
        )

        logger.info(
            "comprehensive_attribution_complete",
            portfolio_return=f"{portfolio_return:.2%}",
            excess_return=f"{excess_return:.2%}",
        )

        return result


# ============ \u5168\u5c40\u5b9e\u4f8b ============

brinson_service = BrinsonAttributionService()
factor_service = FactorAttributionService()
tca_service = TCAService()
comprehensive_service = ComprehensiveAttributionService()
