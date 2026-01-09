"""
交易归因服务
PRD 4.5 交易归因系统

Sprint 5 新增: 交易记录管理、归因报告生成、AI诊断
"""

from datetime import datetime, date, timedelta
from typing import Optional
import uuid
import random

from app.schemas.trade_attribution import (
    TradeRecord,
    AttributionReport,
    AIDiagnosis,
    AttributionFactor,
    FactorSnapshot,
    MarketSnapshot,
    TradeSide,
    TradeOutcome,
)


class TradeAttributionService:
    """交易归因服务 (Sprint 5)"""

    # 模拟数据存储
    _trades: dict[str, TradeRecord] = {}
    _reports: dict[str, AttributionReport] = {}
    _diagnoses: dict[str, AIDiagnosis] = {}
    _strategy_trades: dict[str, list[str]] = {}  # strategy_id -> [trade_ids]
    _strategy_reports: dict[str, list[str]] = {}  # strategy_id -> [report_ids]

    def __init__(self):
        """初始化服务"""
        # 生成一些模拟交易数据
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化模拟数据"""
        strategy_id = "demo-strategy-001"
        symbols = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN", "META"]

        for i in range(20):
            trade_id = str(uuid.uuid4())
            symbol = random.choice(symbols)
            side = random.choice([TradeSide.BUY, TradeSide.SELL])
            entry_price = random.uniform(100, 500)
            exit_price = entry_price * (1 + random.uniform(-0.1, 0.15))
            pnl = (exit_price - entry_price) * random.randint(10, 100)
            pnl_pct = (exit_price - entry_price) / entry_price

            entry_time = datetime.now() - timedelta(days=random.randint(1, 30))
            exit_time = entry_time + timedelta(days=random.randint(1, 5))

            trade = TradeRecord(
                trade_id=trade_id,
                strategy_id=strategy_id,
                strategy_name="动量突破策略",
                deployment_id="deploy-001",
                symbol=symbol,
                side=side,
                quantity=random.randint(10, 100),
                entry_price=round(entry_price, 2),
                entry_time=entry_time,
                exit_price=round(exit_price, 2),
                exit_time=exit_time,
                pnl=round(pnl, 2),
                pnl_pct=round(pnl_pct, 4),
                outcome=TradeOutcome.WIN if pnl > 0 else TradeOutcome.LOSS,
                factor_snapshot=[
                    FactorSnapshot(
                        factor_id="MOMENTUM_3M",
                        factor_name="3个月动量",
                        factor_value=random.uniform(-0.2, 0.3),
                        factor_rank=random.uniform(0.1, 0.9),
                        signal_contribution=random.uniform(0.2, 0.5),
                    ),
                    FactorSnapshot(
                        factor_id="ROE",
                        factor_name="净资产收益率",
                        factor_value=random.uniform(0.05, 0.25),
                        factor_rank=random.uniform(0.3, 0.8),
                        signal_contribution=random.uniform(0.1, 0.3),
                    ),
                ],
                market_snapshot=MarketSnapshot(
                    market_index=random.uniform(4800, 5200),
                    market_change_1d=random.uniform(-0.02, 0.02),
                    market_change_5d=random.uniform(-0.05, 0.05),
                    vix=random.uniform(15, 30),
                    sector_rank=random.randint(1, 10),
                    market_sentiment=random.choice(["bullish", "neutral", "bearish"]),
                ),
                hold_days=random.randint(1, 10),
                created_at=entry_time,
                updated_at=exit_time,
            )

            self._trades[trade_id] = trade
            if strategy_id not in self._strategy_trades:
                self._strategy_trades[strategy_id] = []
            self._strategy_trades[strategy_id].append(trade_id)

    async def get_trades(
        self,
        strategy_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TradeRecord]:
        """获取交易记录列表"""
        if strategy_id:
            trade_ids = self._strategy_trades.get(strategy_id, [])
            trades = [self._trades[tid] for tid in trade_ids if tid in self._trades]
        else:
            trades = list(self._trades.values())

        # 按时间倒序
        trades.sort(key=lambda t: t.entry_time, reverse=True)
        return trades[offset : offset + limit]

    async def get_trade_by_id(self, trade_id: str) -> Optional[TradeRecord]:
        """获取单个交易记录"""
        return self._trades.get(trade_id)

    async def generate_attribution(
        self,
        strategy_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        trigger_reason: str = "手动触发",
    ) -> AttributionReport:
        """生成归因报告"""
        # 获取策略交易
        trade_ids = self._strategy_trades.get(strategy_id, [])
        trades = [self._trades[tid] for tid in trade_ids if tid in self._trades]

        # 过滤日期范围
        if start_date:
            trades = [t for t in trades if t.entry_time.date() >= start_date]
        if end_date:
            trades = [t for t in trades if t.entry_time.date() <= end_date]

        # 计算统计
        total_trades = len(trades)
        win_trades = sum(1 for t in trades if t.outcome == TradeOutcome.WIN)
        loss_trades = sum(1 for t in trades if t.outcome == TradeOutcome.LOSS)

        total_pnl = sum(t.pnl or 0 for t in trades)
        wins_pnl = [t.pnl for t in trades if t.pnl and t.pnl > 0]
        losses_pnl = [abs(t.pnl) for t in trades if t.pnl and t.pnl < 0]

        avg_win = sum(wins_pnl) / len(wins_pnl) if wins_pnl else 0
        avg_loss = sum(losses_pnl) / len(losses_pnl) if losses_pnl else 0
        profit_factor = sum(wins_pnl) / sum(losses_pnl) if losses_pnl and sum(losses_pnl) > 0 else 0

        # 生成因子归因
        factor_attributions = self._calculate_factor_attributions(trades)

        # 生成报告
        report = AttributionReport(
            report_id=str(uuid.uuid4()),
            strategy_id=strategy_id,
            strategy_name="动量突破策略",
            period_start=start_date or (date.today() - timedelta(days=30)),
            period_end=end_date or date.today(),
            total_trades=total_trades,
            win_trades=win_trades,
            loss_trades=loss_trades,
            win_rate=win_trades / total_trades if total_trades > 0 else 0,
            total_pnl=round(total_pnl, 2),
            total_pnl_pct=round(total_pnl / 100000, 4),  # 假设初始资金10万
            avg_win=round(avg_win, 2),
            avg_loss=round(avg_loss, 2),
            profit_factor=round(profit_factor, 2),
            factor_attributions=factor_attributions,
            market_attribution=round(random.uniform(-0.02, 0.03), 4),
            alpha_attribution=round(random.uniform(0.01, 0.05), 4),
            best_market_condition="市场震荡上行时表现最佳",
            worst_market_condition="市场急跌时表现较差",
            patterns=[
                "动量因子在趋势行情中贡献显著",
                "ROE因子帮助筛选优质标的",
                "市场高波动时交易胜率下降",
            ],
            created_at=datetime.now(),
            trigger_reason=trigger_reason,
        )

        # 保存报告
        self._reports[report.report_id] = report
        if strategy_id not in self._strategy_reports:
            self._strategy_reports[strategy_id] = []
        self._strategy_reports[strategy_id].insert(0, report.report_id)

        # 自动生成AI诊断
        await self._generate_ai_diagnosis(report)

        return report

    def _calculate_factor_attributions(
        self, trades: list[TradeRecord]
    ) -> list[AttributionFactor]:
        """计算因子归因"""
        factor_stats: dict[str, list[float]] = {}

        for trade in trades:
            for snapshot in trade.factor_snapshot:
                if snapshot.factor_name not in factor_stats:
                    factor_stats[snapshot.factor_name] = []
                contribution = (trade.pnl or 0) * snapshot.signal_contribution
                factor_stats[snapshot.factor_name].append(contribution)

        attributions = []
        total_contribution = sum(
            sum(contribs) for contribs in factor_stats.values()
        )

        for factor_name, contribs in factor_stats.items():
            factor_contribution = sum(contribs)
            attributions.append(
                AttributionFactor(
                    factor_name=factor_name,
                    contribution=round(factor_contribution, 2),
                    contribution_pct=round(
                        factor_contribution / total_contribution if total_contribution else 0,
                        4,
                    ),
                    is_positive=factor_contribution > 0,
                )
            )

        return sorted(attributions, key=lambda a: abs(a.contribution), reverse=True)

    async def _generate_ai_diagnosis(self, report: AttributionReport):
        """生成AI诊断"""
        diagnosis = AIDiagnosis(
            diagnosis_id=str(uuid.uuid4()),
            report_id=report.report_id,
            summary=self._generate_diagnosis_summary(report),
            strengths=self._generate_strengths(report),
            weaknesses=self._generate_weaknesses(report),
            suggestions=self._generate_suggestions(report),
            risk_alerts=self._generate_risk_alerts(report),
            confidence=round(random.uniform(0.7, 0.95), 2),
            created_at=datetime.now(),
        )

        self._diagnoses[report.report_id] = diagnosis

    def _generate_diagnosis_summary(self, report: AttributionReport) -> str:
        """生成诊断摘要"""
        if report.win_rate >= 0.6:
            return f"策略整体表现优秀，胜率{report.win_rate*100:.1f}%，盈亏比{report.profit_factor:.2f}。建议继续保持当前策略框架。"
        elif report.win_rate >= 0.5:
            return f"策略表现中等，胜率{report.win_rate*100:.1f}%。建议关注亏损交易的共性特征，优化入场时机。"
        else:
            return f"策略近期表现较弱，胜率仅{report.win_rate*100:.1f}%。建议暂停交易，深入分析原因后再恢复。"

    def _generate_strengths(self, report: AttributionReport) -> list[str]:
        """生成优势分析"""
        strengths = []
        if report.profit_factor > 1.5:
            strengths.append("盈亏比优秀，赢利交易的收益显著高于亏损")
        if report.win_rate > 0.55:
            strengths.append("胜率稳定，选股能力较强")
        if report.alpha_attribution > 0.02:
            strengths.append("Alpha贡献显著，策略具有独立的选股能力")

        positive_factors = [f for f in report.factor_attributions if f.is_positive]
        if positive_factors:
            top_factor = positive_factors[0]
            strengths.append(f"{top_factor.factor_name}因子贡献显著，是收益的主要来源")

        return strengths if strengths else ["暂无明显优势，建议优化策略"]

    def _generate_weaknesses(self, report: AttributionReport) -> list[str]:
        """生成劣势分析"""
        weaknesses = []
        if report.profit_factor < 1.0:
            weaknesses.append("盈亏比偏低，需要控制单笔亏损幅度")
        if report.win_rate < 0.45:
            weaknesses.append("胜率偏低，信号质量需要提升")
        if report.avg_loss > report.avg_win * 1.5:
            weaknesses.append("平均亏损过大，止损执行可能不到位")

        negative_factors = [f for f in report.factor_attributions if not f.is_positive]
        if negative_factors:
            weaknesses.append(f"部分因子({negative_factors[0].factor_name})产生负贡献，需检查因子有效性")

        return weaknesses if weaknesses else ["暂无明显劣势"]

    def _generate_suggestions(self, report: AttributionReport) -> list[str]:
        """生成改进建议"""
        suggestions = []

        if report.win_rate < 0.5:
            suggestions.append("建议提高信号阈值，减少低质量交易")
        if report.profit_factor < 1.2:
            suggestions.append("建议设置更严格的止损，控制单笔亏损")
        if report.total_trades > 30:
            suggestions.append("交易频率较高，考虑减少交易次数以降低成本")

        suggestions.append("建议定期回顾交易记录，总结经验教训")
        suggestions.append("关注市场环境变化，及时调整策略参数")

        return suggestions

    def _generate_risk_alerts(self, report: AttributionReport) -> list[str]:
        """生成风险提示"""
        alerts = []

        if report.loss_trades > report.win_trades:
            alerts.append("近期亏损交易多于盈利交易，请注意风险")
        if report.total_pnl < 0:
            alerts.append("累计收益为负，建议降低仓位或暂停交易")

        return alerts if alerts else ["暂无特别风险提示"]

    async def get_reports(
        self, strategy_id: str, limit: int = 10
    ) -> list[AttributionReport]:
        """获取归因报告列表"""
        report_ids = self._strategy_reports.get(strategy_id, [])[:limit]
        return [
            self._reports[rid] for rid in report_ids if rid in self._reports
        ]

    async def get_diagnosis(self, report_id: str) -> Optional[AIDiagnosis]:
        """获取AI诊断"""
        return self._diagnoses.get(report_id)

    async def get_trade_count(self, strategy_id: str) -> int:
        """获取策略交易数量"""
        return len(self._strategy_trades.get(strategy_id, []))


# 单例服务实例
trade_attribution_service = TradeAttributionService()
