"""
信号雷达服务

PRD 4.16.2: 信号雷达功能
- 实时信号获取
- 接近触发计算
- 信号状态管理
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

import structlog

from app.schemas.signal_radar import (
    Signal,
    SignalType,
    SignalStrength,
    SignalStatus,
    FactorTrigger,
    SignalListResponse,
    SignalHistoryResponse,
    StockSearchResult,
    StockSearchResponse,
    StatusSummary,
    StatusSummaryResponse,
    SignalStatusCache,
)

logger = structlog.get_logger()


# ============ 接近触发计算 (PRD 4.16.2) ============

def calc_near_trigger_pct(
    current_value: float,
    threshold: float,
    start_value: float,
    direction: str  # 'above' 或 'below'
) -> float:
    """
    计算因子接近触发程度

    PRD 4.16.2 定义:
    - 如果 当前值 已满足阈值: 100%
    - 如果 当前值 接近阈值: (当前值 - 起始值) / (阈值 - 起始值) * 100%

    示例: PE 阈值 < 20
    - 当前 PE = 21.5, 起始观察值 = 25
    - 接近程度 = (25 - 21.5) / (25 - 20) * 100% = 70%

    当接近程度 >= 80% 时，标记为接近触发
    """
    if direction == 'below':
        # 阈值要求小于某值 (如 PE < 20)
        if current_value <= threshold:
            return 100.0
        if start_value <= threshold:
            return 0.0  # 起始值已满足，无法计算接近程度
        return max(0, (start_value - current_value) / (start_value - threshold) * 100)
    else:
        # 阈值要求大于某值 (如 ROE > 15%)
        if current_value >= threshold:
            return 100.0
        if start_value >= threshold:
            return 0.0
        return max(0, (current_value - start_value) / (threshold - start_value) * 100)


def get_stock_signal_status(
    factor_values: dict[str, float],
    thresholds: dict[str, dict],
    is_holding: bool
) -> tuple[SignalStatus, float, list[FactorTrigger]]:
    """
    获取股票信号状态

    返回: (status, signal_strength, factor_triggers)

    状态优先级 (PRD 4.16.2):
    1. holding - 已持仓
    2. buy_signal - 已触发买入
    3. sell_signal - 已触发卖出
    4. near_trigger - 接近触发 (>=80%)
    5. monitoring - 正常监控
    6. excluded - 不符合条件
    """
    if is_holding:
        return (SignalStatus.HOLDING, 100.0, [])

    # 计算各因子接近程度
    near_percentages = []
    factor_triggers = []
    all_satisfied = True

    for factor_name, config in thresholds.items():
        current = factor_values.get(factor_name)
        if current is None:
            continue

        pct = calc_near_trigger_pct(
            current,
            config['threshold'],
            config.get('start_value', current),
            config['direction']
        )
        near_percentages.append(pct)

        is_satisfied = pct >= 100
        if not is_satisfied:
            all_satisfied = False

        factor_triggers.append(FactorTrigger(
            factor_id=factor_name,
            factor_name=config.get('display_name', factor_name),
            current_value=current,
            threshold=config['threshold'],
            direction=config['direction'],
            near_trigger_pct=pct,
            is_satisfied=is_satisfied,
        ))

    if not near_percentages:
        return (SignalStatus.EXCLUDED, 0.0, factor_triggers)

    min_pct = min(near_percentages)
    avg_pct = sum(near_percentages) / len(near_percentages)

    if all_satisfied:
        return (SignalStatus.BUY_SIGNAL, 100.0, factor_triggers)
    elif min_pct >= 80:
        return (SignalStatus.NEAR_TRIGGER, avg_pct, factor_triggers)
    else:
        return (SignalStatus.MONITORING, avg_pct, factor_triggers)


def calculate_signal_strength(score: float) -> SignalStrength:
    """根据分数计算信号强度"""
    if score >= 80:
        return SignalStrength.STRONG
    elif score >= 60:
        return SignalStrength.MEDIUM
    else:
        return SignalStrength.WEAK


# ============ 信号服务 ============

class SignalService:
    """信号雷达服务"""

    # 模拟数据存储
    _signals: dict[str, list[Signal]] = {}
    _status_cache: dict[str, dict[str, SignalStatusCache]] = {}

    # 模拟股票数据
    MOCK_STOCKS = {
        "AAPL": {"name": "Apple Inc.", "sector": "Technology", "price": 185.50},
        "MSFT": {"name": "Microsoft Corp.", "sector": "Technology", "price": 378.20},
        "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "price": 142.80},
        "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer", "price": 178.90},
        "META": {"name": "Meta Platforms", "sector": "Technology", "price": 485.30},
        "NVDA": {"name": "NVIDIA Corp.", "sector": "Technology", "price": 495.60},
        "TSLA": {"name": "Tesla Inc.", "sector": "Consumer", "price": 248.50},
        "JPM": {"name": "JPMorgan Chase", "sector": "Financials", "price": 172.30},
        "V": {"name": "Visa Inc.", "sector": "Financials", "price": 278.40},
        "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "price": 156.80},
    }

    async def get_signals(
        self,
        strategy_id: str,
        signal_type: Optional[SignalType] = None,
        signal_strength: Optional[SignalStrength] = None,
        status: Optional[SignalStatus] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SignalListResponse:
        """获取策略信号列表"""
        logger.info(
            "get_signals",
            strategy_id=strategy_id,
            signal_type=signal_type,
            limit=limit,
        )

        # 生成模拟信号
        signals = self._generate_mock_signals(strategy_id)

        # 筛选
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        if signal_strength:
            signals = [s for s in signals if s.signal_strength == signal_strength]
        if status:
            signals = [s for s in signals if s.status == status]
        if search:
            search_lower = search.lower()
            signals = [
                s for s in signals
                if search_lower in s.symbol.lower() or search_lower in s.company_name.lower()
            ]

        # 统计
        summary = {
            "buy": sum(1 for s in signals if s.signal_type == SignalType.BUY),
            "sell": sum(1 for s in signals if s.signal_type == SignalType.SELL),
            "hold": sum(1 for s in signals if s.signal_type == SignalType.HOLD),
        }

        # 分页
        total = len(signals)
        signals = signals[offset:offset + limit]

        return SignalListResponse(
            total=total,
            signals=signals,
            summary=summary,
        )

    async def get_signal_history(
        self,
        strategy_id: str,
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> SignalHistoryResponse:
        """获取历史信号"""
        logger.info(
            "get_signal_history",
            strategy_id=strategy_id,
            symbol=symbol,
        )

        # 模拟历史数据
        signals = self._generate_mock_signals(strategy_id, historical=True)

        if symbol:
            signals = [s for s in signals if s.symbol == symbol]

        signals = signals[:limit]

        return SignalHistoryResponse(
            total=len(signals),
            signals=signals,
        )

    async def search_stocks(
        self,
        query: str,
        strategy_id: Optional[str] = None,
        limit: int = 20,
    ) -> StockSearchResponse:
        """搜索股票"""
        logger.info("search_stocks", query=query)

        query_lower = query.lower()
        results = []

        for symbol, info in self.MOCK_STOCKS.items():
            if (query_lower in symbol.lower() or
                query_lower in info["name"].lower()):
                results.append(StockSearchResult(
                    symbol=symbol,
                    company_name=info["name"],
                    sector=info["sector"],
                    current_price=info["price"],
                    signal_status=SignalStatus.MONITORING,
                    signal_score=50.0,
                ))

        return StockSearchResponse(results=results[:limit])

    async def get_status_summary(
        self,
        strategy_id: str,
    ) -> StatusSummaryResponse:
        """获取信号状态分布统计"""
        signals = self._generate_mock_signals(strategy_id)

        summary = StatusSummary(
            holding=sum(1 for s in signals if s.status == SignalStatus.HOLDING),
            buy_signal=sum(1 for s in signals if s.status == SignalStatus.BUY_SIGNAL),
            sell_signal=sum(1 for s in signals if s.status == SignalStatus.SELL_SIGNAL),
            near_trigger=sum(1 for s in signals if s.status == SignalStatus.NEAR_TRIGGER),
            monitoring=sum(1 for s in signals if s.status == SignalStatus.MONITORING),
            excluded=sum(1 for s in signals if s.status == SignalStatus.EXCLUDED),
        )

        return StatusSummaryResponse(
            strategy_id=strategy_id,
            summary=summary,
            updated_at=datetime.now(),
        )

    async def refresh_signals(self, strategy_id: str) -> bool:
        """刷新策略信号"""
        logger.info("refresh_signals", strategy_id=strategy_id)
        # 清除缓存，强制重新计算
        if strategy_id in self._signals:
            del self._signals[strategy_id]
        return True

    def _generate_mock_signals(
        self,
        strategy_id: str,
        historical: bool = False
    ) -> list[Signal]:
        """生成模拟信号数据"""
        import random
        random.seed(hash(strategy_id) % 1000)

        signals = []
        now = datetime.now()

        for symbol, info in self.MOCK_STOCKS.items():
            # 随机信号类型
            signal_type = random.choice([
                SignalType.BUY, SignalType.BUY, SignalType.BUY,
                SignalType.SELL,
                SignalType.HOLD, SignalType.HOLD,
            ])

            # 随机分数
            score = random.uniform(40, 95)
            strength = calculate_signal_strength(score)

            # 随机状态
            status = random.choice([
                SignalStatus.BUY_SIGNAL,
                SignalStatus.NEAR_TRIGGER,
                SignalStatus.MONITORING,
                SignalStatus.MONITORING,
            ])

            # 因子触发
            factors = [
                FactorTrigger(
                    factor_id="pe_ratio",
                    factor_name="市盈率",
                    current_value=random.uniform(15, 30),
                    threshold=25,
                    direction="below",
                    near_trigger_pct=random.uniform(60, 100),
                    is_satisfied=random.choice([True, False]),
                ),
                FactorTrigger(
                    factor_id="momentum_20d",
                    factor_name="20日动量",
                    current_value=random.uniform(-0.1, 0.2),
                    threshold=0.05,
                    direction="above",
                    near_trigger_pct=random.uniform(50, 100),
                    is_satisfied=random.choice([True, False]),
                ),
            ]

            price = Decimal(str(info["price"]))

            signals.append(Signal(
                signal_id=str(uuid.uuid4()),
                strategy_id=strategy_id,
                symbol=symbol,
                company_name=info["name"],
                signal_type=signal_type,
                signal_strength=strength,
                signal_score=round(score, 1),
                status=status,
                triggered_factors=factors,
                current_price=price,
                target_price=price * Decimal("1.1") if signal_type == SignalType.BUY else None,
                stop_loss_price=price * Decimal("0.95") if signal_type == SignalType.BUY else None,
                expected_return_pct=10.0 if signal_type == SignalType.BUY else None,
                signal_time=now,
                expires_at=None,
                is_holding=status == SignalStatus.HOLDING,
            ))

        # 按信号分数排序
        signals.sort(key=lambda s: s.signal_score, reverse=True)

        return signals


# 全局服务实例
signal_service = SignalService()
