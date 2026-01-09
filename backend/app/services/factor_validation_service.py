"""
因子有效性验证服务
PRD 4.3 因子有效性验证
"""

from datetime import date, datetime
from typing import Optional
import random
import math

from app.schemas.factor_validation import (
    FactorValidationResult,
    ICStatistics,
    ReturnStatistics,
    EffectivenessLevel,
    FactorCompareResult,
    FactorSuggestion,
    EFFECTIVENESS_THRESHOLDS,
)


class FactorValidationService:
    """因子有效性验证服务"""

    # 因子元数据 (模拟)
    FACTOR_METADATA = {
        "PE_TTM": {
            "name": "市盈率TTM",
            "category": "value",
            "plain_description": "PE越低，说明股价相对于公司盈利越便宜。买入低PE股票，期望在估值修复时获得超额收益。",
            "investment_logic": "低PE策略基于均值回归原理，认为被低估的股票最终会回归合理估值。适合在市场恐慌时买入优质但被错杀的股票。",
        },
        "PB": {
            "name": "市净率",
            "category": "value",
            "plain_description": "PB越低，说明股价相对于公司净资产越便宜。适合寻找被市场低估的资产型公司。",
            "investment_logic": "PB策略关注公司的账面价值，适合重资产行业和周期性行业的投资。低PB往往意味着安全边际较高。",
        },
        "ROE": {
            "name": "净资产收益率",
            "category": "quality",
            "plain_description": "ROE衡量公司用股东的钱赚钱的能力。ROE越高，说明公司盈利能力越强，是好公司的标志。",
            "investment_logic": "高ROE公司通常具有竞争优势和护城河，能持续为股东创造价值。巴菲特最看重的指标之一。",
        },
        "MOMENTUM_3M": {
            "name": "3个月动量",
            "category": "momentum",
            "plain_description": "过去3个月涨得好的股票，接下来可能继续涨。这就是动量效应，追涨策略的理论基础。",
            "investment_logic": "动量策略利用市场的趋势延续特征，适合趋势明确的市场环境。但在震荡市中容易回撤。",
        },
        "DIVIDEND_YIELD": {
            "name": "股息率",
            "category": "value",
            "plain_description": "股息率高意味着每年能拿到更多的分红。适合追求稳定现金流的投资者。",
            "investment_logic": "高股息策略强调现金回报，高股息公司通常经营稳健、现金流充沛。在利率下行环境中优势明显。",
        },
        "VOLATILITY_20D": {
            "name": "20日波动率",
            "category": "volatility",
            "plain_description": "低波动股票涨跌幅小，风险较低。历史数据显示，低波动股票长期表现反而更好。",
            "investment_logic": "低波动策略利用'低风险异象'，在控制风险的同时获得合理收益。适合风险厌恶型投资者。",
        },
        "EPS_GROWTH": {
            "name": "每股收益增长率",
            "category": "growth",
            "plain_description": "EPS增长快的公司，说明盈利在快速增加。成长股投资的核心指标。",
            "investment_logic": "高成长策略追逐业绩高增长的公司，期望市场给予更高估值。适合经济上行期和牛市。",
        },
    }

    # 建议组合配置
    SUGGESTED_COMBINATIONS = {
        "PE_TTM": ["ROE", "DIVIDEND_YIELD", "EPS_GROWTH"],
        "PB": ["ROE", "DIVIDEND_YIELD"],
        "ROE": ["PE_TTM", "EPS_GROWTH", "MOMENTUM_3M"],
        "MOMENTUM_3M": ["ROE", "VOLATILITY_20D"],
        "DIVIDEND_YIELD": ["PE_TTM", "PB", "ROE"],
        "VOLATILITY_20D": ["ROE", "DIVIDEND_YIELD"],
        "EPS_GROWTH": ["ROE", "PE_TTM", "MOMENTUM_3M"],
    }

    def __init__(self):
        """初始化服务"""
        self._validation_cache: dict[str, FactorValidationResult] = {}

    async def validate_factor(
        self,
        factor_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        universe: str = "全A",
    ) -> FactorValidationResult:
        """
        验证因子有效性

        Args:
            factor_id: 因子ID
            start_date: 开始日期
            end_date: 结束日期
            universe: 股票池

        Returns:
            因子验证结果
        """
        # 获取因子元数据
        metadata = self.FACTOR_METADATA.get(factor_id, {})
        factor_name = metadata.get("name", factor_id)
        category = metadata.get("category", "other")

        # 生成模拟的IC统计数据
        ic_stats = self._generate_ic_stats(factor_id)

        # 生成模拟的收益统计数据
        return_stats = self._generate_return_stats(factor_id)

        # 判定有效性等级
        effectiveness_level = self._determine_effectiveness(
            ic_stats.ic_ir, return_stats.long_short_spread
        )

        # 计算有效性评分
        effectiveness_score = self._calculate_effectiveness_score(
            ic_stats, return_stats
        )

        # 生成使用建议
        usage_tips = self._generate_usage_tips(effectiveness_level, factor_id)

        # 生成风险提示
        risk_warnings = self._generate_risk_warnings(factor_id, category)

        # 构建结果
        result = FactorValidationResult(
            factor_id=factor_id,
            factor_name=factor_name,
            factor_category=category,
            plain_description=metadata.get(
                "plain_description", f"{factor_name}是一个常用的选股因子。"
            ),
            investment_logic=metadata.get(
                "investment_logic", "该因子基于特定的投资逻辑构建。"
            ),
            ic_stats=ic_stats,
            return_stats=return_stats,
            is_effective=effectiveness_level != EffectivenessLevel.INEFFECTIVE,
            effectiveness_level=effectiveness_level,
            effectiveness_score=effectiveness_score,
            suggested_combinations=self.SUGGESTED_COMBINATIONS.get(factor_id, []),
            usage_tips=usage_tips,
            risk_warnings=risk_warnings,
            validation_date=date.today(),
            data_period=f"{start_date or '2020-01-01'} ~ {end_date or date.today()}",
            sample_size=random.randint(2000, 4000),
        )

        # 缓存结果
        self._validation_cache[factor_id] = result

        return result

    def _generate_ic_stats(self, factor_id: str) -> ICStatistics:
        """生成IC统计数据 (模拟)"""
        # 根据因子类型生成不同的IC数据
        base_ic = {
            "PE_TTM": 0.045,
            "PB": 0.038,
            "ROE": 0.052,
            "MOMENTUM_3M": 0.048,
            "DIVIDEND_YIELD": 0.035,
            "VOLATILITY_20D": 0.028,
            "EPS_GROWTH": 0.042,
        }.get(factor_id, 0.03)

        ic_mean = base_ic + random.uniform(-0.01, 0.01)
        ic_std = abs(ic_mean) / random.uniform(0.3, 0.7)
        ic_ir = ic_mean / ic_std if ic_std > 0 else 0

        # 生成IC时序
        ic_series = []
        ic_dates = []
        current_date = date(2023, 1, 1)
        for i in range(24):  # 24个月
            ic_value = ic_mean + random.uniform(-0.03, 0.03)
            ic_series.append(round(ic_value, 4))
            ic_dates.append(current_date.strftime("%Y-%m"))
            current_date = date(
                current_date.year + (current_date.month // 12),
                (current_date.month % 12) + 1,
                1,
            )

        return ICStatistics(
            ic_mean=round(ic_mean, 4),
            ic_std=round(ic_std, 4),
            ic_ir=round(ic_ir, 2),
            ic_positive_ratio=round(0.5 + ic_mean * 5, 2),
            ic_series=ic_series,
            ic_dates=ic_dates,
        )

    def _generate_return_stats(self, factor_id: str) -> ReturnStatistics:
        """生成收益统计数据 (模拟)"""
        # 根据因子类型生成不同的收益数据
        base_spread = {
            "PE_TTM": 0.062,
            "PB": 0.048,
            "ROE": 0.085,
            "MOMENTUM_3M": 0.072,
            "DIVIDEND_YIELD": 0.045,
            "VOLATILITY_20D": 0.038,
            "EPS_GROWTH": 0.068,
        }.get(factor_id, 0.05)

        # 生成5组收益 (从高到低)
        top_return = 0.12 + random.uniform(-0.02, 0.04)
        spread = base_spread + random.uniform(-0.02, 0.02)

        group_returns = []
        for i in range(5):
            ret = top_return - (spread * i / 4)
            group_returns.append(round(ret, 3))

        return ReturnStatistics(
            group_returns=group_returns,
            group_labels=["第1组(高)", "第2组", "第3组", "第4组", "第5组(低)"],
            long_short_spread=round(group_returns[0] - group_returns[-1], 3),
            top_group_sharpe=round(1.2 + random.uniform(-0.3, 0.5), 2),
            bottom_group_sharpe=round(0.5 + random.uniform(-0.2, 0.3), 2),
        )

    def _determine_effectiveness(
        self, ic_ir: float, spread: float
    ) -> EffectivenessLevel:
        """判定有效性等级"""
        thresholds = EFFECTIVENESS_THRESHOLDS

        if ic_ir >= thresholds["strong"]["ic_ir"] and spread >= thresholds["strong"]["spread"]:
            return EffectivenessLevel.STRONG
        elif ic_ir >= thresholds["medium"]["ic_ir"] and spread >= thresholds["medium"]["spread"]:
            return EffectivenessLevel.MEDIUM
        elif ic_ir >= thresholds["weak"]["ic_ir"] and spread >= thresholds["weak"]["spread"]:
            return EffectivenessLevel.WEAK
        else:
            return EffectivenessLevel.INEFFECTIVE

    def _calculate_effectiveness_score(
        self, ic_stats: ICStatistics, return_stats: ReturnStatistics
    ) -> float:
        """计算有效性评分 (0-100)"""
        # IC_IR 贡献 40%
        ic_ir_score = min(ic_stats.ic_ir / 0.8, 1.0) * 40

        # 多空收益差贡献 40%
        spread_score = min(return_stats.long_short_spread / 0.15, 1.0) * 40

        # IC为正比例贡献 20%
        positive_score = (ic_stats.ic_positive_ratio - 0.5) * 40

        return round(max(0, min(100, ic_ir_score + spread_score + positive_score)), 1)

    def _generate_usage_tips(
        self, level: EffectivenessLevel, factor_id: str
    ) -> list[str]:
        """生成使用建议"""
        tips = []

        if level == EffectivenessLevel.STRONG:
            tips.append("该因子表现优异，可作为策略的主要选股依据")
            tips.append("建议在回测中给予较高权重")
        elif level == EffectivenessLevel.MEDIUM:
            tips.append("该因子表现中等，建议与其他因子组合使用")
            tips.append(f"推荐搭配: {', '.join(self.SUGGESTED_COMBINATIONS.get(factor_id, [])[:2])}")
        elif level == EffectivenessLevel.WEAK:
            tips.append("该因子表现较弱，仅作为辅助参考")
            tips.append("建议降低权重或与强因子配合使用")
        else:
            tips.append("该因子无明显选股能力，不建议单独使用")
            tips.append("可尝试改进因子构建方法或更换因子")

        return tips

    def _generate_risk_warnings(self, factor_id: str, category: str) -> list[str]:
        """生成风险提示"""
        warnings = []

        if category == "value":
            warnings.append("价值因子在成长股行情中可能表现不佳")
            warnings.append("注意区分低估值和价值陷阱")
        elif category == "momentum":
            warnings.append("动量因子在市场反转时回撤较大")
            warnings.append("需配合止损策略使用")
        elif category == "growth":
            warnings.append("成长因子估值敏感度高")
            warnings.append("高增长可能不可持续，需关注业绩兑现")
        elif category == "quality":
            warnings.append("高质量股票可能已被充分定价")
        elif category == "volatility":
            warnings.append("低波动策略在牛市中可能跑输大盘")

        warnings.append("历史表现不代表未来收益")

        return warnings

    async def compare_factors(
        self, factor_ids: list[str]
    ) -> FactorCompareResult:
        """对比多个因子"""
        factors = []
        for fid in factor_ids:
            result = await self.validate_factor(fid)
            factors.append(result)

        # 生成相关性矩阵 (模拟)
        n = len(factor_ids)
        correlation_matrix = []
        for i in range(n):
            row = []
            for j in range(n):
                if i == j:
                    row.append(1.0)
                else:
                    corr = random.uniform(-0.3, 0.5)
                    row.append(round(corr, 2))
            correlation_matrix.append(row)

        # 找出最佳组合 (有效性最高且相关性较低的)
        sorted_factors = sorted(
            factors, key=lambda f: f.effectiveness_score, reverse=True
        )
        best_combination = [f.factor_id for f in sorted_factors[:3]]

        return FactorCompareResult(
            factors=factors,
            correlation_matrix=correlation_matrix,
            best_combination=best_combination,
            combination_score=sum(f.effectiveness_score for f in sorted_factors[:3]) / 3,
        )

    async def get_suggestions(self, factor_id: str) -> list[FactorSuggestion]:
        """获取因子组合建议"""
        suggestions = []
        suggested_ids = self.SUGGESTED_COMBINATIONS.get(factor_id, [])

        for sid in suggested_ids:
            metadata = self.FACTOR_METADATA.get(sid, {})
            suggestions.append(
                FactorSuggestion(
                    factor_id=sid,
                    factor_name=metadata.get("name", sid),
                    suggestion_reason=f"与{factor_id}互补，可提升策略稳定性",
                    expected_improvement=round(random.uniform(0.01, 0.05), 3),
                    correlation=round(random.uniform(-0.2, 0.3), 2),
                )
            )

        return suggestions

    async def get_validation_result(
        self, factor_id: str
    ) -> Optional[FactorValidationResult]:
        """获取缓存的验证结果"""
        return self._validation_cache.get(factor_id)


# 单例服务实例
factor_validation_service = FactorValidationService()
