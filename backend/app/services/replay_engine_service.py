"""
回放引擎服务
PRD 4.17 策略回放功能

控制回放流程、计算信号、生成事件
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.schemas.replay import (
    FactorSnapshot,
    HistoricalBar,
    ReplayConfig,
    ReplayInsight,
    ReplaySpeed,
    ReplayState,
    ReplayStatus,
    ReplayTickResponse,
    SignalEvent,
    SignalMarker,
)
from app.services.historical_data_service import get_historical_data_service


class ReplayEngineService:
    """回放引擎"""

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    async def init_replay(self, user_id: str, config: ReplayConfig) -> dict:
        """
        初始化回放会话

        Args:
            user_id: 用户ID
            config: 回放配置

        Returns:
            初始化结果包含状态和信号标记
        """
        session_id = f"replay_{uuid.uuid4().hex[:8]}"

        # 获取历史数据
        data_service = get_historical_data_service()
        bars = await data_service.get_historical_bars(
            config.symbol, config.start_date, config.end_date
        )

        # 获取因子快照
        factor_snapshots = await data_service.get_factor_snapshots(
            config.strategy_id, config.symbol, config.start_date, config.end_date
        )

        # 预计算信号标记
        signal_markers = self._find_signal_markers(bars, factor_snapshots)

        # 创建初始状态
        state = ReplayState(
            session_id=session_id,
            config=config,
            status=ReplayStatus.IDLE,
            current_time=bars[0].timestamp if bars else datetime.now(),
            current_bar_index=0,
            total_bars=len(bars),
            position_quantity=0,
            position_avg_cost=Decimal("0"),
            cash=Decimal("100000"),
            total_signals=len(signal_markers),
            executed_signals=0,
            total_return_pct=0,
            benchmark_return_pct=0,
        )

        # 存储会话数据
        self._sessions[session_id] = {
            "state": state,
            "bars": bars,
            "factor_snapshots": factor_snapshots,
            "signal_markers": signal_markers,
            "events": [],
            "start_price": float(bars[0].close) if bars else 0,
        }

        return {
            "state": state,
            "total_bars": len(bars),
            "signal_markers": signal_markers,
        }

    async def play(self, session_id: str) -> ReplayState:
        """开始/继续播放"""
        session = self._get_session(session_id)
        session["state"].status = ReplayStatus.PLAYING
        return session["state"]

    async def pause(self, session_id: str) -> ReplayState:
        """暂停"""
        session = self._get_session(session_id)
        session["state"].status = ReplayStatus.PAUSED
        return session["state"]

    async def step_forward(self, session_id: str) -> ReplayTickResponse:
        """前进一步"""
        session = self._get_session(session_id)
        state = session["state"]
        bars = session["bars"]

        if state.current_bar_index >= state.total_bars - 1:
            # 已到末尾
            return self._create_tick_response(session)

        # 前进一步
        state.current_bar_index += 1
        bar = bars[state.current_bar_index]
        state.current_time = bar.timestamp

        # 获取因子快照
        snapshot = session["factor_snapshots"].get(bar.timestamp)

        # 检查信号
        events = self._check_signal(snapshot, state, bar)
        session["events"].extend(events)

        # 模拟执行
        for event in events:
            self._simulate_execution(state, event, bar)

        # 更新收益
        self._update_returns(session)

        return self._create_tick_response(session)

    async def step_backward(self, session_id: str) -> ReplayTickResponse:
        """后退一步"""
        session = self._get_session(session_id)
        state = session["state"]

        if state.current_bar_index <= 0:
            return self._create_tick_response(session)

        state.current_bar_index -= 1
        bar = session["bars"][state.current_bar_index]
        state.current_time = bar.timestamp

        return self._create_tick_response(session)

    async def seek_to_time(
        self, session_id: str, target_time: datetime
    ) -> ReplayTickResponse:
        """跳转到指定时间"""
        session = self._get_session(session_id)
        state = session["state"]
        bars = session["bars"]

        # 查找目标时间对应的K线
        for i, bar in enumerate(bars):
            if bar.timestamp >= target_time:
                state.current_bar_index = i
                state.current_time = bar.timestamp
                break

        return self._create_tick_response(session)

    async def seek_to_next_signal(self, session_id: str) -> ReplayTickResponse:
        """跳转到下一个信号"""
        session = self._get_session(session_id)
        state = session["state"]
        signal_markers = session["signal_markers"]

        # 查找下一个信号
        for marker in signal_markers:
            if marker.index > state.current_bar_index:
                state.current_bar_index = marker.index
                state.current_time = session["bars"][marker.index].timestamp
                break

        return self._create_tick_response(session)

    async def set_speed(self, session_id: str, speed: ReplaySpeed) -> ReplayState:
        """设置回放速度"""
        session = self._get_session(session_id)
        session["state"].config.speed = speed
        return session["state"]

    async def get_insight(self, session_id: str) -> ReplayInsight:
        """获取回放洞察"""
        session = self._get_session(session_id)
        state = session["state"]
        events = session["events"]

        # 计算统计
        buy_events = [e for e in events if e.event_type == "buy_trigger"]
        sell_events = [e for e in events if e.event_type == "sell_trigger"]

        execution_rate = (
            state.executed_signals / state.total_signals
            if state.total_signals > 0
            else 0
        )

        # 简化胜率计算
        win_rate = 0.55 + (state.total_return_pct * 0.1)  # 模拟
        win_rate = max(0, min(1, win_rate))

        alpha = state.total_return_pct - state.benchmark_return_pct

        # 生成AI洞察
        ai_insights = self._generate_ai_insights(session)

        return ReplayInsight(
            total_signals=state.total_signals,
            execution_rate=execution_rate,
            win_rate=win_rate,
            alpha=alpha,
            ai_insights=ai_insights,
            strategy_return=state.total_return_pct,
            benchmark_return=state.benchmark_return_pct,
        )

    async def export_replay(self, session_id: str) -> dict:
        """导出回放记录"""
        session = self._get_session(session_id)
        insight = await self.get_insight(session_id)

        return {
            "events": session["events"],
            "summary": insight,
        }

    def _get_session(self, session_id: str) -> dict:
        """获取会话"""
        if session_id not in self._sessions:
            raise ValueError(f"Session not found: {session_id}")
        return self._sessions[session_id]

    def _find_signal_markers(
        self,
        bars: list[HistoricalBar],
        factor_snapshots: dict[datetime, FactorSnapshot],
    ) -> list[SignalMarker]:
        """查找信号标记位置"""
        markers = []

        prev_signal = "hold"
        for i, bar in enumerate(bars):
            snapshot = factor_snapshots.get(bar.timestamp)
            if snapshot:
                current_signal = snapshot.overall_signal

                # 信号变化时添加标记
                if current_signal != prev_signal and current_signal != "hold":
                    markers.append(
                        SignalMarker(
                            index=i,
                            time=bar.timestamp.isoformat(),
                            type="buy" if current_signal == "buy" else "sell",
                        )
                    )

                prev_signal = current_signal

        return markers

    def _check_signal(
        self,
        snapshot: Optional[FactorSnapshot],
        state: ReplayState,
        bar: HistoricalBar,
    ) -> list[SignalEvent]:
        """检查是否触发信号"""
        events = []

        if not snapshot:
            return events

        # 检查买入信号
        if snapshot.overall_signal == "buy" and state.position_quantity == 0:
            event = SignalEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                timestamp=bar.timestamp,
                event_type="buy_trigger",
                symbol=state.config.symbol,
                price=bar.close,
                description=f"买入信号触发: {snapshot.conditions_met}/{snapshot.conditions_total} 条件满足",
                factor_details=snapshot.factor_values,
            )
            events.append(event)

        # 检查卖出信号
        elif snapshot.overall_signal == "sell" and state.position_quantity > 0:
            event = SignalEvent(
                event_id=f"evt_{uuid.uuid4().hex[:8]}",
                timestamp=bar.timestamp,
                event_type="sell_trigger",
                symbol=state.config.symbol,
                price=bar.close,
                description=f"卖出信号触发: 条件不满足",
                factor_details=snapshot.factor_values,
            )
            events.append(event)

        return events

    def _simulate_execution(
        self, state: ReplayState, event: SignalEvent, bar: HistoricalBar
    ) -> None:
        """模拟执行交易"""
        if event.event_type == "buy_trigger":
            # 计算可买数量 (使用50%资金)
            available_cash = state.cash * Decimal("0.5")
            quantity = int(available_cash / bar.close)

            if quantity > 0:
                cost = bar.close * quantity
                state.cash -= cost
                state.position_quantity = quantity
                state.position_avg_cost = bar.close
                state.executed_signals += 1

        elif event.event_type == "sell_trigger":
            if state.position_quantity > 0:
                # 全部卖出
                proceeds = bar.close * state.position_quantity
                state.cash += proceeds
                state.position_quantity = 0
                state.position_avg_cost = Decimal("0")
                state.executed_signals += 1

    def _update_returns(self, session: dict) -> None:
        """更新收益率"""
        state = session["state"]
        bars = session["bars"]
        start_price = session["start_price"]

        if state.current_bar_index >= len(bars):
            return

        current_bar = bars[state.current_bar_index]
        current_price = float(current_bar.close)

        # 计算策略收益
        portfolio_value = float(state.cash) + (
            state.position_quantity * current_price
        )
        initial_value = 100000
        state.total_return_pct = (portfolio_value - initial_value) / initial_value

        # 计算基准收益 (买入持有)
        if start_price > 0:
            state.benchmark_return_pct = (current_price - start_price) / start_price

    def _create_tick_response(self, session: dict) -> ReplayTickResponse:
        """创建Tick响应"""
        state = session["state"]
        bars = session["bars"]

        bar = bars[state.current_bar_index]
        snapshot = session["factor_snapshots"].get(bar.timestamp)

        if not snapshot:
            snapshot = FactorSnapshot(
                timestamp=bar.timestamp,
                factor_values={},
                thresholds={},
                overall_signal="hold",
                conditions_met=0,
                conditions_total=0,
            )

        # 获取本Tick的事件
        tick_events = [
            e for e in session["events"] if e.timestamp == bar.timestamp
        ]

        return ReplayTickResponse(
            state=state,
            bar=bar,
            factor_snapshot=snapshot,
            events=tick_events,
        )

    def _generate_ai_insights(self, session: dict) -> list[str]:
        """生成AI洞察"""
        state = session["state"]
        insights = []

        # 基于回放统计生成洞察
        if state.total_return_pct > state.benchmark_return_pct:
            insights.append(
                f"策略在此期间跑赢基准 {((state.total_return_pct - state.benchmark_return_pct) * 100):.1f}%"
            )
        else:
            insights.append("策略在此期间未能跑赢基准，建议检查入场条件")

        if state.executed_signals < state.total_signals * 0.5:
            insights.append("信号执行率较低，可能错过部分交易机会")

        if state.total_signals > 10:
            insights.append("信号频率较高，注意交易成本对收益的影响")
        elif state.total_signals < 3:
            insights.append("信号较少，可以考虑放宽部分条件增加交易机会")

        return insights


# 单例
_service: Optional[ReplayEngineService] = None


def get_replay_engine_service() -> ReplayEngineService:
    """获取回放引擎服务单例"""
    global _service
    if _service is None:
        _service = ReplayEngineService()
    return _service
