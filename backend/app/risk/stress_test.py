"""
压力测试模块

模拟极端市场条件下的组合表现:
- 历史情景 (如: 2008金融危机, 2020新冠)
- 假设情景 (自定义冲击)
- 逆向压力测试
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger()


class ScenarioType(str, Enum):
    """情景类型"""
    HISTORICAL = "historical"       # 历史情景
    HYPOTHETICAL = "hypothetical"   # 假设情景
    REVERSE = "reverse"             # 逆向压力测试


@dataclass
class StressScenario:
    """压力测试情景"""
    name: str
    scenario_type: ScenarioType
    description: str = ""

    # 市场冲击 (比例)
    market_shock: float = 0.0           # 市场整体
    volatility_shock: float = 1.0       # 波动率乘数
    correlation_shock: float = 1.0      # 相关性乘数 (>1 表示相关性增加)

    # 因子冲击
    factor_shocks: dict[str, float] = field(default_factory=dict)

    # 资产类别冲击
    asset_class_shocks: dict[str, float] = field(default_factory=dict)

    # 行业冲击
    sector_shocks: dict[str, float] = field(default_factory=dict)

    # 历史情景日期范围
    start_date: date | None = None
    end_date: date | None = None


# 预定义历史情景
HISTORICAL_SCENARIOS = {
    "2008_financial_crisis": StressScenario(
        name="2008 金融危机",
        scenario_type=ScenarioType.HISTORICAL,
        description="2008年9-10月全球金融危机",
        market_shock=-0.40,
        volatility_shock=3.0,
        correlation_shock=1.5,
        sector_shocks={
            "金融": -0.60,
            "房地产": -0.50,
            "能源": -0.35,
            "科技": -0.45,
            "消费": -0.30,
        },
    ),
    "2020_covid_crash": StressScenario(
        name="2020 新冠崩盘",
        scenario_type=ScenarioType.HISTORICAL,
        description="2020年2-3月新冠疫情冲击",
        market_shock=-0.35,
        volatility_shock=4.0,
        correlation_shock=1.8,
        sector_shocks={
            "航空": -0.70,
            "旅游": -0.65,
            "能源": -0.55,
            "金融": -0.40,
            "科技": -0.25,
            "医疗": -0.10,
        },
    ),
    "2022_rate_hike": StressScenario(
        name="2022 加息周期",
        scenario_type=ScenarioType.HISTORICAL,
        description="2022年美联储激进加息",
        market_shock=-0.25,
        volatility_shock=1.8,
        factor_shocks={
            "value": 0.15,      # 价值股跑赢
            "growth": -0.35,    # 成长股下跌
            "momentum": -0.20,
        },
    ),
    "flash_crash": StressScenario(
        name="闪崩",
        scenario_type=ScenarioType.HYPOTHETICAL,
        description="日内闪崩情景",
        market_shock=-0.10,
        volatility_shock=5.0,
        correlation_shock=2.0,
    ),
    "bond_crisis": StressScenario(
        name="债市危机",
        scenario_type=ScenarioType.HYPOTHETICAL,
        description="利率飙升导致的债市崩盘",
        factor_shocks={
            "duration": -0.15,  # 久期越长损失越大
            "credit": -0.10,
        },
        asset_class_shocks={
            "固定收益": -0.20,
            "房地产REITs": -0.25,
            "公用事业": -0.15,
        },
    ),
}


@dataclass
class StressTestResult:
    """压力测试结果"""
    scenario: StressScenario
    portfolio_loss: float               # 组合损失 (比例)
    portfolio_loss_amount: float = 0.0  # 组合损失 (金额)
    var_stressed: float = 0.0           # 压力下 VaR
    max_drawdown_stressed: float = 0.0  # 压力下最大回撤
    recovery_days: int = 0              # 预计恢复天数

    # 详细分解
    market_contribution: float = 0.0    # 市场风险贡献
    factor_contribution: float = 0.0    # 因子风险贡献
    sector_contribution: float = 0.0    # 行业风险贡献
    idiosyncratic_contribution: float = 0.0  # 特异性风险贡献

    # 各资产影响
    asset_impacts: dict[str, float] = field(default_factory=dict)

    # 风险指标变化
    risk_metrics: dict[str, float] = field(default_factory=dict)


class StressTester:
    """
    压力测试器

    使用示例:
    ```python
    tester = StressTester()

    # 使用预定义情景
    result = tester.run_scenario(
        portfolio_returns=returns,
        holdings={"AAPL": 0.3, "GOOGL": 0.3, "JPM": 0.4},
        scenario=HISTORICAL_SCENARIOS["2008_financial_crisis"],
    )
    print(f"预计损失: {result.portfolio_loss:.2%}")

    # 自定义情景
    custom = StressScenario(
        name="自定义",
        scenario_type=ScenarioType.HYPOTHETICAL,
        market_shock=-0.20,
        volatility_shock=2.0,
    )
    result = tester.run_scenario(..., scenario=custom)
    ```
    """

    def __init__(
        self,
        base_volatility: float = 0.15,
        risk_free_rate: float = 0.02,
    ):
        """
        Args:
            base_volatility: 基准波动率 (年化)
            risk_free_rate: 无风险利率
        """
        self.base_volatility = base_volatility
        self.risk_free_rate = risk_free_rate

    def run_scenario(
        self,
        portfolio_returns: pd.Series | None = None,
        holdings: dict[str, float] | None = None,
        portfolio_value: float = 1.0,
        scenario: StressScenario | str = "2008_financial_crisis",
        asset_betas: dict[str, float] | None = None,
        asset_sectors: dict[str, str] | None = None,
    ) -> StressTestResult:
        """
        运行压力测试

        Args:
            portfolio_returns: 历史收益 (用于估计风险)
            holdings: 当前持仓
            portfolio_value: 组合价值
            scenario: 压力情景 (名称或对象)
            asset_betas: 资产 Beta
            asset_sectors: 资产行业

        Returns:
            压力测试结果
        """
        # 获取情景
        if isinstance(scenario, str):
            if scenario not in HISTORICAL_SCENARIOS:
                raise ValueError(f"未知情景: {scenario}")
            scenario = HISTORICAL_SCENARIOS[scenario]

        holdings = holdings or {}
        asset_betas = asset_betas or {}
        asset_sectors = asset_sectors or {}

        # 计算各部分损失
        market_loss = self._calculate_market_impact(holdings, asset_betas, scenario)
        sector_loss = self._calculate_sector_impact(holdings, asset_sectors, scenario)
        factor_loss = self._calculate_factor_impact(holdings, scenario)

        # 考虑相关性增加的影响
        correlation_effect = (scenario.correlation_shock - 1) * 0.05  # 简化处理

        # 总损失
        total_loss = market_loss + sector_loss + factor_loss + correlation_effect
        total_loss = max(-1.0, min(0.0, total_loss))  # 限制在合理范围

        # 计算各资产影响
        asset_impacts = {}
        for asset, weight in holdings.items():
            beta = asset_betas.get(asset, 1.0)
            sector = asset_sectors.get(asset, "其他")

            asset_market_loss = scenario.market_shock * beta
            asset_sector_loss = scenario.sector_shocks.get(sector, 0)

            asset_impacts[asset] = {
                "weight": weight,
                "market_loss": asset_market_loss,
                "sector_loss": asset_sector_loss,
                "total_loss": asset_market_loss + asset_sector_loss,
                "contribution": weight * (asset_market_loss + asset_sector_loss),
            }

        # 压力下风险指标
        stressed_vol = self.base_volatility * scenario.volatility_shock

        result = StressTestResult(
            scenario=scenario,
            portfolio_loss=total_loss,
            portfolio_loss_amount=total_loss * portfolio_value,
            var_stressed=2.33 * stressed_vol / np.sqrt(252),  # 99% 日 VaR
            max_drawdown_stressed=abs(total_loss) * 1.2,  # 估计最大回撤
            recovery_days=int(abs(total_loss) * 252 / 0.10) if total_loss < 0 else 0,  # 假设年化 10% 恢复
            market_contribution=market_loss,
            sector_contribution=sector_loss,
            factor_contribution=factor_loss,
            asset_impacts=asset_impacts,
            risk_metrics={
                "stressed_volatility": stressed_vol,
                "normal_volatility": self.base_volatility,
                "volatility_increase": scenario.volatility_shock,
                "correlation_increase": scenario.correlation_shock,
            },
        )

        logger.info(
            "压力测试完成",
            scenario=scenario.name,
            portfolio_loss=f"{total_loss:.2%}",
            loss_amount=f"{result.portfolio_loss_amount:,.2f}",
        )

        return result

    def _calculate_market_impact(
        self,
        holdings: dict[str, float],
        asset_betas: dict[str, float],
        scenario: StressScenario,
    ) -> float:
        """计算市场冲击影响"""
        if scenario.market_shock == 0:
            return 0.0

        portfolio_beta = sum(
            weight * asset_betas.get(asset, 1.0)
            for asset, weight in holdings.items()
        )

        return scenario.market_shock * portfolio_beta

    def _calculate_sector_impact(
        self,
        holdings: dict[str, float],
        asset_sectors: dict[str, str],
        scenario: StressScenario,
    ) -> float:
        """计算行业冲击影响"""
        if not scenario.sector_shocks:
            return 0.0

        total = 0.0
        for asset, weight in holdings.items():
            sector = asset_sectors.get(asset, "其他")
            sector_shock = scenario.sector_shocks.get(sector, 0)
            total += weight * sector_shock

        return total

    def _calculate_factor_impact(
        self,
        holdings: dict[str, float],
        scenario: StressScenario,
    ) -> float:
        """计算因子冲击影响 (简化版)"""
        if not scenario.factor_shocks:
            return 0.0

        # 简化: 假设均匀暴露
        avg_shock = np.mean(list(scenario.factor_shocks.values()))
        return avg_shock * 0.3  # 假设 30% 因子暴露

    def run_multiple_scenarios(
        self,
        portfolio_returns: pd.Series | None = None,
        holdings: dict[str, float] | None = None,
        portfolio_value: float = 1.0,
        scenarios: list[StressScenario | str] | None = None,
        **kwargs,
    ) -> list[StressTestResult]:
        """
        运行多个压力测试情景

        Args:
            scenarios: 情景列表 (默认使用所有预定义情景)
        """
        if scenarios is None:
            scenarios = list(HISTORICAL_SCENARIOS.keys())

        results = []
        for scenario in scenarios:
            result = self.run_scenario(
                portfolio_returns=portfolio_returns,
                holdings=holdings,
                portfolio_value=portfolio_value,
                scenario=scenario,
                **kwargs,
            )
            results.append(result)

        return results

    def reverse_stress_test(
        self,
        target_loss: float,
        holdings: dict[str, float],
        asset_betas: dict[str, float] | None = None,
    ) -> StressScenario:
        """
        逆向压力测试

        找出导致指定损失的市场条件

        Args:
            target_loss: 目标损失 (如 -0.20 表示 20% 损失)
            holdings: 持仓
            asset_betas: 资产 Beta

        Returns:
            导致该损失的情景
        """
        asset_betas = asset_betas or {}

        # 计算组合 Beta
        portfolio_beta = sum(
            weight * asset_betas.get(asset, 1.0)
            for asset, weight in holdings.items()
        )

        # 反推市场冲击
        required_market_shock = target_loss / portfolio_beta if portfolio_beta != 0 else target_loss

        # 估计对应的波动率增加
        vol_shock = 1 + abs(required_market_shock) * 10  # 简化估计

        return StressScenario(
            name=f"逆向测试 (损失 {target_loss:.0%})",
            scenario_type=ScenarioType.REVERSE,
            description=f"导致 {target_loss:.0%} 损失的市场条件",
            market_shock=required_market_shock,
            volatility_shock=min(5.0, vol_shock),
            correlation_shock=min(2.0, 1 + abs(required_market_shock)),
        )


def generate_stress_report(
    results: list[StressTestResult],
) -> pd.DataFrame:
    """
    生成压力测试报告

    Args:
        results: 压力测试结果列表

    Returns:
        报告 DataFrame
    """
    data = []
    for r in results:
        data.append({
            "情景": r.scenario.name,
            "类型": r.scenario.scenario_type.value,
            "组合损失": f"{r.portfolio_loss:.2%}",
            "损失金额": f"{r.portfolio_loss_amount:,.2f}",
            "压力VaR": f"{r.var_stressed:.2%}",
            "预计最大回撤": f"{r.max_drawdown_stressed:.2%}",
            "恢复天数": r.recovery_days,
            "市场贡献": f"{r.market_contribution:.2%}",
            "行业贡献": f"{r.sector_contribution:.2%}",
        })

    return pd.DataFrame(data)
