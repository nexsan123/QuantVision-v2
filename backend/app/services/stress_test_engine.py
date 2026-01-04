"""
Phase 10: 增强版压力测试引擎

支持:
- 历史情景 (2008, 2011, 2015, 2018, 2020, 2022)
- 假设情景 (市场下跌, 行业崩盘, 流动性危机)
- 自定义情景
- 逆向压力测试
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger()


# ============ 预置压力情景 ============

PRESET_SCENARIOS = {
    # 历史情景
    "2008_financial_crisis": {
        "id": "2008_financial_crisis",
        "name": "2008金融危机",
        "type": "historical",
        "description": "2008年9月-2009年3月全球金融危机，系统性风险爆发",
        "shocks": {
            "market_return": -0.50,
            "volatility_multiplier": 3.0,
            "sector_shocks": {
                "financials": -0.60,
                "real_estate": -0.50,
                "energy": -0.35,
                "information_technology": -0.45,
                "consumer_discretionary": -0.40,
            },
        },
        "historical_period": {
            "start_date": "2008-09-01",
            "end_date": "2009-03-31",
            "spy_drawdown": -0.50,
        },
    },
    "2011_euro_crisis": {
        "id": "2011_euro_crisis",
        "name": "2011欧债危机",
        "type": "historical",
        "description": "2011年7-10月欧洲主权债务危机，市场恐慌",
        "shocks": {
            "market_return": -0.19,
            "volatility_multiplier": 2.0,
            "sector_shocks": {
                "financials": -0.30,
            },
        },
        "historical_period": {
            "start_date": "2011-07-01",
            "end_date": "2011-10-31",
            "spy_drawdown": -0.19,
        },
    },
    "2015_china_crash": {
        "id": "2015_china_crash",
        "name": "2015中国股灾",
        "type": "historical",
        "description": "2015年8月中国股市暴跌引发全球市场动荡",
        "shocks": {
            "market_return": -0.12,
            "volatility_multiplier": 2.5,
            "sector_shocks": {
                "materials": -0.20,
                "industrials": -0.15,
            },
        },
        "historical_period": {
            "start_date": "2015-08-01",
            "end_date": "2015-08-31",
            "spy_drawdown": -0.12,
        },
    },
    "2018_rate_scare": {
        "id": "2018_rate_scare",
        "name": "2018年末下跌",
        "type": "historical",
        "description": "2018年10-12月美联储加息恐慌",
        "shocks": {
            "market_return": -0.20,
            "volatility_multiplier": 2.0,
            "factor_shocks": {
                "growth": -0.25,
                "momentum": -0.15,
            },
        },
        "historical_period": {
            "start_date": "2018-10-01",
            "end_date": "2018-12-31",
            "spy_drawdown": -0.20,
        },
    },
    "2020_covid": {
        "id": "2020_covid",
        "name": "2020新冠崩盘",
        "type": "historical",
        "description": "2020年2-3月新冠疫情引发的市场崩盘",
        "shocks": {
            "market_return": -0.34,
            "volatility_multiplier": 4.0,
            "sector_shocks": {
                "energy": -0.55,
                "consumer_discretionary": -0.40,
                "industrials": -0.35,
                "financials": -0.35,
                "real_estate": -0.25,
                "healthcare": -0.10,
                "information_technology": -0.20,
            },
        },
        "historical_period": {
            "start_date": "2020-02-19",
            "end_date": "2020-03-23",
            "spy_drawdown": -0.34,
        },
    },
    "2022_rate_hike": {
        "id": "2022_rate_hike",
        "name": "2022加息周期",
        "type": "historical",
        "description": "2022年美联储激进加息导致的市场下跌",
        "shocks": {
            "market_return": -0.25,
            "volatility_multiplier": 1.8,
            "factor_shocks": {
                "growth": -0.35,
                "value": 0.10,
                "momentum": -0.15,
            },
            "sector_shocks": {
                "information_technology": -0.35,
                "communication_services": -0.40,
                "consumer_discretionary": -0.30,
            },
        },
        "historical_period": {
            "start_date": "2022-01-01",
            "end_date": "2022-10-31",
            "spy_drawdown": -0.25,
        },
    },
    # 假设情景
    "market_crash_20": {
        "id": "market_crash_20",
        "name": "市场下跌20%",
        "type": "hypothetical",
        "description": "假设市场整体下跌20%的情景",
        "shocks": {
            "market_return": -0.20,
            "volatility_multiplier": 2.0,
        },
    },
    "market_crash_30_vol": {
        "id": "market_crash_30_vol",
        "name": "市场下跌30%+波动率翻倍",
        "type": "hypothetical",
        "description": "市场下跌30%且波动率翻倍的极端情景",
        "shocks": {
            "market_return": -0.30,
            "volatility_multiplier": 2.0,
        },
    },
    "tech_crash": {
        "id": "tech_crash",
        "name": "科技股崩盘",
        "type": "hypothetical",
        "description": "科技行业单独大跌40%，类似2000年互联网泡沫",
        "shocks": {
            "market_return": -0.15,
            "sector_shocks": {
                "information_technology": -0.40,
                "communication_services": -0.30,
            },
        },
    },
    "liquidity_crisis": {
        "id": "liquidity_crisis",
        "name": "流动性危机",
        "type": "hypothetical",
        "description": "市场流动性枯竭，滑点增加5倍",
        "shocks": {
            "market_return": -0.10,
            "liquidity_shock": 5.0,
        },
    },
    "inflation_shock": {
        "id": "inflation_shock",
        "name": "通胀冲击",
        "type": "hypothetical",
        "description": "高通胀环境下的市场调整",
        "shocks": {
            "market_return": -0.15,
            "factor_shocks": {
                "growth": -0.30,
                "value": 0.05,
            },
            "sector_shocks": {
                "utilities": -0.20,
                "real_estate": -0.25,
                "consumer_staples": -0.10,
            },
        },
    },
}


@dataclass
class StressTestResult:
    """压力测试结果"""
    scenario_id: str
    scenario_name: str
    scenario_type: str

    # 组合影响
    expected_loss: float
    expected_loss_percent: float
    var_impact: float
    max_drawdown: float
    recovery_days: int
    liquidation_risk: bool

    # 持仓影响
    position_impacts: list[dict] = field(default_factory=list)

    # 风险指标变化
    volatility_before: float = 0.15
    volatility_after: float = 0.30
    var_before: float = 0.02
    var_after: float = 0.05
    beta_before: float = 1.0
    beta_after: float = 1.2

    # 建议
    recommendations: list[str] = field(default_factory=list)


class StressTestEngine:
    """
    增强版压力测试引擎

    使用示例:
    ```python
    engine = StressTestEngine()

    # 运行单个情景
    result = engine.run_scenario(
        holdings={"AAPL": 0.3, "GOOGL": 0.3, "JPM": 0.4},
        portfolio_value=1000000,
        scenario_id="2008_financial_crisis",
    )

    # 运行所有情景
    results = engine.run_all_scenarios(holdings, portfolio_value)

    # 自定义情景
    custom = {
        "market_return": -0.25,
        "sector_shocks": {"financials": -0.50},
    }
    result = engine.run_custom_scenario(holdings, portfolio_value, custom)
    ```
    """

    def __init__(
        self,
        base_volatility: float = 0.15,
        risk_free_rate: float = 0.02,
    ):
        self.base_volatility = base_volatility
        self.risk_free_rate = risk_free_rate
        self.scenarios = PRESET_SCENARIOS

    def get_available_scenarios(self) -> list[dict]:
        """获取所有可用情景"""
        return [
            {
                "id": s["id"],
                "name": s["name"],
                "type": s["type"],
                "description": s["description"],
                "historical_period": s.get("historical_period"),
            }
            for s in self.scenarios.values()
        ]

    def run_scenario(
        self,
        holdings: dict[str, float],
        portfolio_value: float,
        scenario_id: str,
        asset_betas: dict[str, float] | None = None,
        asset_sectors: dict[str, str] | None = None,
    ) -> StressTestResult:
        """运行指定压力情景"""
        if scenario_id not in self.scenarios:
            raise ValueError(f"未知情景: {scenario_id}")

        scenario = self.scenarios[scenario_id]
        return self._execute_scenario(
            holdings, portfolio_value, scenario, asset_betas, asset_sectors
        )

    def run_custom_scenario(
        self,
        holdings: dict[str, float],
        portfolio_value: float,
        shocks: dict[str, Any],
        name: str = "自定义情景",
        asset_betas: dict[str, float] | None = None,
        asset_sectors: dict[str, str] | None = None,
    ) -> StressTestResult:
        """运行自定义情景"""
        scenario = {
            "id": "custom",
            "name": name,
            "type": "custom",
            "description": "用户自定义压力情景",
            "shocks": shocks,
        }
        return self._execute_scenario(
            holdings, portfolio_value, scenario, asset_betas, asset_sectors
        )

    def run_all_scenarios(
        self,
        holdings: dict[str, float],
        portfolio_value: float,
        asset_betas: dict[str, float] | None = None,
        asset_sectors: dict[str, str] | None = None,
        scenario_ids: list[str] | None = None,
    ) -> list[StressTestResult]:
        """运行多个情景"""
        if scenario_ids is None:
            scenario_ids = list(self.scenarios.keys())

        results = []
        for scenario_id in scenario_ids:
            if scenario_id in self.scenarios:
                result = self.run_scenario(
                    holdings, portfolio_value, scenario_id,
                    asset_betas, asset_sectors
                )
                results.append(result)

        return results

    def _execute_scenario(
        self,
        holdings: dict[str, float],
        portfolio_value: float,
        scenario: dict,
        asset_betas: dict[str, float] | None = None,
        asset_sectors: dict[str, str] | None = None,
    ) -> StressTestResult:
        """执行压力测试"""
        asset_betas = asset_betas or {}
        asset_sectors = asset_sectors or {}
        shocks = scenario.get("shocks", {})

        # 计算各部分损失
        market_loss = self._calc_market_impact(holdings, asset_betas, shocks)
        sector_loss = self._calc_sector_impact(holdings, asset_sectors, shocks)
        factor_loss = self._calc_factor_impact(shocks)

        # 总损失
        total_loss = market_loss + sector_loss + factor_loss
        total_loss = max(-0.99, min(0.0, total_loss))

        # 计算各持仓影响
        position_impacts = []
        for symbol, weight in holdings.items():
            beta = asset_betas.get(symbol, 1.0)
            sector = asset_sectors.get(symbol, "information_technology")

            pos_market_loss = shocks.get("market_return", 0) * beta
            pos_sector_loss = shocks.get("sector_shocks", {}).get(sector, 0)
            pos_total = pos_market_loss + pos_sector_loss

            position_impacts.append({
                "symbol": symbol,
                "current_weight": weight,
                "expected_loss": pos_total * weight * portfolio_value,
                "loss_percent": pos_total,
                "contribution": pos_total * weight / total_loss if total_loss != 0 else 0,
            })

        # 波动率冲击
        vol_mult = shocks.get("volatility_multiplier", 1.0)
        stressed_vol = self.base_volatility * vol_mult

        # VaR 计算
        var_before = 2.33 * self.base_volatility / np.sqrt(252)
        var_after = 2.33 * stressed_vol / np.sqrt(252)

        # 预计恢复天数
        recovery_days = int(abs(total_loss) * 252 / 0.10) if total_loss < 0 else 0

        # 流动性风险
        liquidity_shock = shocks.get("liquidity_shock", 1.0)
        liquidation_risk = liquidity_shock > 3.0 and abs(total_loss) > 0.20

        # 生成建议
        recommendations = self._generate_recommendations(
            total_loss, position_impacts, stressed_vol, liquidation_risk
        )

        return StressTestResult(
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
            scenario_type=scenario["type"],
            expected_loss=total_loss * portfolio_value,
            expected_loss_percent=total_loss,
            var_impact=var_after - var_before,
            max_drawdown=abs(total_loss) * 1.2,
            recovery_days=recovery_days,
            liquidation_risk=liquidation_risk,
            position_impacts=position_impacts,
            volatility_before=self.base_volatility,
            volatility_after=stressed_vol,
            var_before=var_before,
            var_after=var_after,
            recommendations=recommendations,
        )

    def _calc_market_impact(
        self,
        holdings: dict[str, float],
        asset_betas: dict[str, float],
        shocks: dict,
    ) -> float:
        """计算市场冲击影响"""
        market_shock = shocks.get("market_return", 0)
        if market_shock == 0:
            return 0.0

        portfolio_beta = sum(
            weight * asset_betas.get(symbol, 1.0)
            for symbol, weight in holdings.items()
        )
        return market_shock * portfolio_beta

    def _calc_sector_impact(
        self,
        holdings: dict[str, float],
        asset_sectors: dict[str, str],
        shocks: dict,
    ) -> float:
        """计算行业冲击影响"""
        sector_shocks = shocks.get("sector_shocks", {})
        if not sector_shocks:
            return 0.0

        total = 0.0
        for symbol, weight in holdings.items():
            sector = asset_sectors.get(symbol, "information_technology")
            shock = sector_shocks.get(sector, 0)
            total += weight * shock

        return total

    def _calc_factor_impact(self, shocks: dict) -> float:
        """计算因子冲击影响"""
        factor_shocks = shocks.get("factor_shocks", {})
        if not factor_shocks:
            return 0.0

        # 简化: 假设 30% 因子暴露
        avg_shock = np.mean(list(factor_shocks.values()))
        return avg_shock * 0.3

    def _generate_recommendations(
        self,
        total_loss: float,
        position_impacts: list[dict],
        stressed_vol: float,
        liquidation_risk: bool,
    ) -> list[str]:
        """生成建议"""
        recommendations = []

        if abs(total_loss) > 0.30:
            recommendations.append("建议降低组合Beta或增加对冲仓位")

        if stressed_vol > 0.40:
            recommendations.append("波动率过高，建议增加低波动资产配置")

        if liquidation_risk:
            recommendations.append("警告: 存在强平风险，建议降低杠杆或增加保证金")

        # 找出损失最大的持仓
        if position_impacts:
            worst = max(position_impacts, key=lambda x: abs(x.get("loss_percent", 0)))
            if abs(worst.get("loss_percent", 0)) > 0.40:
                recommendations.append(
                    f"持仓 {worst['symbol']} 预计损失 {worst['loss_percent']:.1%}，建议减仓或对冲"
                )

        if not recommendations:
            recommendations.append("组合风险在可控范围内")

        return recommendations

    def reverse_stress_test(
        self,
        holdings: dict[str, float],
        target_loss: float,
        asset_betas: dict[str, float] | None = None,
    ) -> dict:
        """
        逆向压力测试

        找出导致指定损失的市场条件
        """
        asset_betas = asset_betas or {}

        portfolio_beta = sum(
            weight * asset_betas.get(symbol, 1.0)
            for symbol, weight in holdings.items()
        )

        required_market_shock = target_loss / portfolio_beta if portfolio_beta != 0 else target_loss
        vol_shock = 1 + abs(required_market_shock) * 8

        return {
            "id": "reverse",
            "name": f"逆向测试 (损失 {target_loss:.0%})",
            "type": "reverse",
            "description": f"导致 {target_loss:.0%} 损失的市场条件",
            "shocks": {
                "market_return": required_market_shock,
                "volatility_multiplier": min(5.0, vol_shock),
            },
            "interpretation": {
                "required_market_drop": f"{required_market_shock:.1%}",
                "historical_comparable": self._find_comparable_scenario(required_market_shock),
            },
        }

    def _find_comparable_scenario(self, market_shock: float) -> str:
        """找到历史上类似的情景"""
        if market_shock <= -0.40:
            return "2008金融危机级别"
        elif market_shock <= -0.30:
            return "2020新冠崩盘级别"
        elif market_shock <= -0.20:
            return "2018/2022加息周期级别"
        elif market_shock <= -0.10:
            return "普通市场调整"
        else:
            return "轻微波动"
