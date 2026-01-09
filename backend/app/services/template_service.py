"""
策略模板服务
PRD 4.13 策略模板库
"""

from datetime import datetime
from typing import Optional
import uuid

from app.schemas.strategy_template import (
    TemplateCategory,
    DifficultyLevel,
    HoldingPeriod,
    RiskLevel,
    StrategyTemplate,
    TemplateDeployRequest,
    TemplateDeployResult,
)


class TemplateService:
    """策略模板服务"""

    # 预设模板存储
    _templates: dict[str, StrategyTemplate] = {}

    def __init__(self):
        """初始化服务"""
        self._init_preset_templates()

    def _init_preset_templates(self):
        """初始化6个预设模板"""
        templates = [
            # 1. 巴菲特价值
            StrategyTemplate(
                template_id="tpl-value-buffett",
                name="巴菲特价值",
                description="基于巴菲特投资理念，寻找具有护城河的优质低估值公司。适合长期持有，追求稳健增值。",
                category=TemplateCategory.VALUE,
                difficulty=DifficultyLevel.BEGINNER,
                holding_period=HoldingPeriod.LONG_TERM,
                risk_level=RiskLevel.LOW,
                expected_annual_return="10-15%",
                max_drawdown="15-20%",
                sharpe_ratio="0.8-1.2",
                strategy_config={
                    "factors": [
                        {"id": "PE_TTM", "weight": 0.3, "direction": "asc"},
                        {"id": "PB", "weight": 0.2, "direction": "asc"},
                        {"id": "ROE", "weight": 0.3, "direction": "desc"},
                        {"id": "DEBT_RATIO", "weight": 0.2, "direction": "asc"},
                    ],
                    "universe": "SP500",
                    "rebalance_frequency": "monthly",
                    "position_count": 20,
                    "position_sizing": "equal_weight",
                },
                user_count=1523,
                rating=4.5,
                tags=["经典策略", "低风险", "长线投资"],
                icon="💎",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            # 2. 动量突破
            StrategyTemplate(
                template_id="tpl-momentum-breakout",
                name="动量突破",
                description="追踪强势股票的价格突破，顺势加仓。适合趋势行情，需要较强的执行力。",
                category=TemplateCategory.MOMENTUM,
                difficulty=DifficultyLevel.INTERMEDIATE,
                holding_period=HoldingPeriod.SHORT_TERM,
                risk_level=RiskLevel.MEDIUM,
                expected_annual_return="15-25%",
                max_drawdown="20-30%",
                sharpe_ratio="1.0-1.5",
                strategy_config={
                    "factors": [
                        {"id": "MOMENTUM_3M", "weight": 0.4, "direction": "desc"},
                        {"id": "MOMENTUM_6M", "weight": 0.3, "direction": "desc"},
                        {"id": "VOLUME_RATIO", "weight": 0.3, "direction": "desc"},
                    ],
                    "universe": "NASDAQ100",
                    "rebalance_frequency": "weekly",
                    "position_count": 10,
                    "position_sizing": "momentum_weight",
                    "stop_loss": 0.08,
                    "take_profit": 0.20,
                },
                user_count=892,
                rating=4.2,
                tags=["趋势跟踪", "高收益", "需要盯盘"],
                icon="🚀",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            # 3. 低波红利
            StrategyTemplate(
                template_id="tpl-dividend-low-vol",
                name="低波红利",
                description="选择高股息率且波动较低的股票，追求稳定的现金流收益。适合稳健型投资者。",
                category=TemplateCategory.DIVIDEND,
                difficulty=DifficultyLevel.BEGINNER,
                holding_period=HoldingPeriod.LONG_TERM,
                risk_level=RiskLevel.LOW,
                expected_annual_return="8-12%",
                max_drawdown="10-15%",
                sharpe_ratio="1.0-1.4",
                strategy_config={
                    "factors": [
                        {"id": "DIVIDEND_YIELD", "weight": 0.4, "direction": "desc"},
                        {"id": "VOLATILITY_252D", "weight": 0.3, "direction": "asc"},
                        {"id": "PAYOUT_RATIO", "weight": 0.15, "direction": "asc"},
                        {"id": "DIVIDEND_GROWTH_5Y", "weight": 0.15, "direction": "desc"},
                    ],
                    "universe": "SP500",
                    "rebalance_frequency": "quarterly",
                    "position_count": 30,
                    "position_sizing": "equal_weight",
                    "dividend_reinvest": True,
                },
                user_count=1105,
                rating=4.6,
                tags=["稳健收益", "现金分红", "防守型"],
                icon="💰",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            # 4. 多因子增强
            StrategyTemplate(
                template_id="tpl-multi-factor",
                name="多因子增强",
                description="综合价值、动量、质量、低波动等多个因子，构建风险调整后收益最优的组合。",
                category=TemplateCategory.MULTI_FACTOR,
                difficulty=DifficultyLevel.ADVANCED,
                holding_period=HoldingPeriod.MEDIUM_TERM,
                risk_level=RiskLevel.MEDIUM,
                expected_annual_return="12-18%",
                max_drawdown="18-25%",
                sharpe_ratio="1.2-1.8",
                strategy_config={
                    "factors": [
                        {"id": "PE_TTM", "weight": 0.15, "direction": "asc"},
                        {"id": "MOMENTUM_6M", "weight": 0.2, "direction": "desc"},
                        {"id": "ROE", "weight": 0.2, "direction": "desc"},
                        {"id": "VOLATILITY_252D", "weight": 0.15, "direction": "asc"},
                        {"id": "EARNINGS_SURPRISE", "weight": 0.15, "direction": "desc"},
                        {"id": "ANALYST_RATING", "weight": 0.15, "direction": "desc"},
                    ],
                    "universe": "RUSSELL1000",
                    "rebalance_frequency": "bi-weekly",
                    "position_count": 50,
                    "position_sizing": "risk_parity",
                    "sector_neutral": True,
                },
                user_count=567,
                rating=4.3,
                tags=["量化策略", "因子投资", "专业级"],
                icon="🔬",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            # 5. 行业轮动
            StrategyTemplate(
                template_id="tpl-sector-rotation",
                name="行业轮动",
                description="根据宏观经济周期和行业相对强弱，动态调整行业配置，追求超额收益。",
                category=TemplateCategory.TIMING,
                difficulty=DifficultyLevel.ADVANCED,
                holding_period=HoldingPeriod.MEDIUM_TERM,
                risk_level=RiskLevel.MEDIUM,
                expected_annual_return="15-20%",
                max_drawdown="20-28%",
                sharpe_ratio="1.1-1.6",
                strategy_config={
                    "factors": [
                        {"id": "SECTOR_MOMENTUM_1M", "weight": 0.3, "direction": "desc"},
                        {"id": "SECTOR_MOMENTUM_3M", "weight": 0.25, "direction": "desc"},
                        {"id": "SECTOR_BREADTH", "weight": 0.25, "direction": "desc"},
                        {"id": "SECTOR_FLOW", "weight": 0.2, "direction": "desc"},
                    ],
                    "universe": "SECTOR_ETFS",
                    "rebalance_frequency": "weekly",
                    "position_count": 5,
                    "position_sizing": "momentum_weight",
                    "top_sectors": 3,
                    "cash_threshold": 0.2,
                },
                user_count=432,
                rating=4.1,
                tags=["行业ETF", "宏观择时", "高换手"],
                icon="🔄",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            # 6. 日内动量
            StrategyTemplate(
                template_id="tpl-intraday-momentum",
                name="日内动量",
                description="捕捉日内价格动量，快速进出。高频交易，需要严格的风控和执行纪律。",
                category=TemplateCategory.INTRADAY,
                difficulty=DifficultyLevel.ADVANCED,
                holding_period=HoldingPeriod.INTRADAY,
                risk_level=RiskLevel.HIGH,
                expected_annual_return="20-40%",
                max_drawdown="25-35%",
                sharpe_ratio="1.5-2.5",
                strategy_config={
                    "factors": [
                        {"id": "PRICE_MOMENTUM_5MIN", "weight": 0.3, "direction": "desc"},
                        {"id": "VOLUME_SURGE", "weight": 0.25, "direction": "desc"},
                        {"id": "SPREAD_RATIO", "weight": 0.2, "direction": "asc"},
                        {"id": "RELATIVE_STRENGTH", "weight": 0.25, "direction": "desc"},
                    ],
                    "universe": "HIGH_VOLUME_100",
                    "trading_hours": "9:30-16:00",
                    "max_positions": 5,
                    "position_sizing": "fixed_risk",
                    "stop_loss": 0.02,
                    "take_profit": 0.05,
                    "max_daily_trades": 20,
                    "close_eod": True,
                },
                user_count=289,
                rating=3.9,
                tags=["高频交易", "日内平仓", "高风险高收益"],
                icon="⚡",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

        for tpl in templates:
            self._templates[tpl.template_id] = tpl

    async def get_templates(
        self,
        category: Optional[TemplateCategory] = None,
        difficulty: Optional[DifficultyLevel] = None,
        search: Optional[str] = None,
    ) -> list[StrategyTemplate]:
        """获取模板列表"""
        templates = list(self._templates.values())

        # 分类筛选
        if category:
            templates = [t for t in templates if t.category == category]

        # 难度筛选
        if difficulty:
            templates = [t for t in templates if t.difficulty == difficulty]

        # 搜索
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.name.lower()
                or search_lower in t.description.lower()
                or any(search_lower in tag.lower() for tag in t.tags)
            ]

        # 按使用人数排序
        templates.sort(key=lambda t: t.user_count, reverse=True)

        return templates

    async def get_template_by_id(self, template_id: str) -> Optional[StrategyTemplate]:
        """获取模板详情"""
        return self._templates.get(template_id)

    async def get_categories(self) -> list[dict]:
        """获取模板分类"""
        from app.schemas.strategy_template import CATEGORY_CONFIG
        return [
            {
                "category": cat.value,
                "label": config["label"],
                "icon": config["icon"],
                "color": config["color"],
                "description": config["description"],
                "count": sum(1 for t in self._templates.values() if t.category == cat),
            }
            for cat, config in CATEGORY_CONFIG.items()
        ]

    async def deploy_template(
        self,
        request: TemplateDeployRequest,
    ) -> TemplateDeployResult:
        """从模板部署策略"""
        template = self._templates.get(request.template_id)
        if not template:
            raise ValueError(f"模板不存在: {request.template_id}")

        # 创建策略 (这里模拟，实际应调用策略服务)
        strategy_id = str(uuid.uuid4())

        # 更新使用人数
        template.user_count += 1

        return TemplateDeployResult(
            strategy_id=strategy_id,
            strategy_name=request.strategy_name,
            template_id=template.template_id,
            template_name=template.name,
            created_at=datetime.now(),
            message=f"策略 '{request.strategy_name}' 已从模板 '{template.name}' 创建成功",
        )


# 单例服务实例
template_service = TemplateService()
