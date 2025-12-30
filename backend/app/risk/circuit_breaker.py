"""
熔断器 (Circuit Breaker)

在风险超限时自动暂停交易，保护组合

状态机:
CLOSED (正常) -> OPEN (熔断) -> HALF_OPEN (试探) -> CLOSED
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable

import structlog

logger = structlog.get_logger()


class CircuitBreakerState(str, Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 正常交易
    OPEN = "open"           # 熔断中，停止交易
    HALF_OPEN = "half_open" # 试探性恢复


class TriggerReason(str, Enum):
    """熔断触发原因"""
    MAX_DRAWDOWN = "max_drawdown"           # 最大回撤超限
    DAILY_LOSS = "daily_loss"               # 日亏损超限
    VAR_BREACH = "var_breach"               # VaR 超限
    VOLATILITY_SPIKE = "volatility_spike"   # 波动率飙升
    POSITION_LIMIT = "position_limit"       # 持仓超限
    CONSECUTIVE_LOSS = "consecutive_loss"   # 连续亏损
    MANUAL = "manual"                       # 手动触发
    API_ERROR = "api_error"                 # API 错误过多


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    # 阈值
    max_drawdown_pct: float = 0.10          # 最大回撤 10%
    max_daily_loss_pct: float = 0.05        # 日亏损 5%
    max_var_pct: float = 0.08               # VaR 8%
    max_volatility_ratio: float = 2.0       # 波动率放大 2 倍
    max_position_pct: float = 0.20          # 单票持仓 20%
    max_consecutive_losses: int = 5         # 连续亏损次数
    max_api_errors: int = 3                 # API 错误次数

    # 时间控制
    cooldown_minutes: int = 30              # 熔断冷却时间
    half_open_duration_minutes: int = 5     # 半开状态持续时间
    daily_reset_hour: int = 9               # 每日重置时间 (小时)

    # 行为控制
    auto_reduce_position: bool = True       # 自动减仓
    reduce_position_pct: float = 0.5        # 减仓比例
    allow_close_only: bool = True           # 熔断时只允许平仓
    notify_on_trigger: bool = True          # 触发时通知


@dataclass
class CircuitBreakerEvent:
    """熔断事件"""
    timestamp: datetime
    state: CircuitBreakerState
    reason: TriggerReason | None = None
    details: dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    """
    熔断器

    自动监控风险指标，在超限时触发熔断

    使用示例:
    ```python
    breaker = CircuitBreaker(config)

    # 检查是否允许交易
    if breaker.can_trade():
        execute_order(order)

    # 更新风险指标
    breaker.update_metrics(
        daily_pnl=-0.03,
        drawdown=0.08,
        volatility=0.25,
    )
    ```
    """

    def __init__(
        self,
        config: CircuitBreakerConfig | None = None,
        on_trigger: Callable[[CircuitBreakerEvent], None] | None = None,
    ):
        """
        Args:
            config: 熔断器配置
            on_trigger: 触发回调函数
        """
        self.config = config or CircuitBreakerConfig()
        self.on_trigger = on_trigger

        self._state = CircuitBreakerState.CLOSED
        self._triggered_at: datetime | None = None
        self._trigger_reason: TriggerReason | None = None
        self._events: list[CircuitBreakerEvent] = []

        # 计数器
        self._consecutive_losses = 0
        self._api_error_count = 0
        self._daily_pnl = 0.0
        self._last_reset_date: datetime | None = None

        # 基准值 (用于比较)
        self._base_volatility: float | None = None

    @property
    def state(self) -> CircuitBreakerState:
        """当前状态"""
        return self._state

    @property
    def is_tripped(self) -> bool:
        """是否已熔断"""
        return self._state == CircuitBreakerState.OPEN

    def can_trade(self, is_closing: bool = False) -> bool:
        """
        检查是否可以交易

        Args:
            is_closing: 是否是平仓操作

        Returns:
            是否允许交易
        """
        self._check_auto_recovery()

        if self._state == CircuitBreakerState.CLOSED:
            return True

        if self._state == CircuitBreakerState.HALF_OPEN:
            return True  # 试探性允许

        if self._state == CircuitBreakerState.OPEN:
            if is_closing and self.config.allow_close_only:
                return True
            return False

        return False

    def update_metrics(
        self,
        daily_pnl: float | None = None,
        drawdown: float | None = None,
        volatility: float | None = None,
        var: float | None = None,
        max_position_pct: float | None = None,
        trade_result: float | None = None,
    ) -> None:
        """
        更新风险指标

        Args:
            daily_pnl: 日盈亏 (比例)
            drawdown: 当前回撤 (比例)
            volatility: 当前波动率 (年化)
            var: 当前 VaR (比例)
            max_position_pct: 最大持仓比例
            trade_result: 最近交易结果 (>0 盈利, <0 亏损)
        """
        self._check_daily_reset()

        # 更新日盈亏
        if daily_pnl is not None:
            self._daily_pnl = daily_pnl

        # 更新连续亏损计数
        if trade_result is not None:
            if trade_result < 0:
                self._consecutive_losses += 1
            else:
                self._consecutive_losses = 0

        # 设置基准波动率
        if self._base_volatility is None and volatility is not None:
            self._base_volatility = volatility

        # 检查各项阈值
        self._check_thresholds(
            daily_pnl=daily_pnl,
            drawdown=drawdown,
            volatility=volatility,
            var=var,
            max_position_pct=max_position_pct,
        )

    def _check_thresholds(
        self,
        daily_pnl: float | None = None,
        drawdown: float | None = None,
        volatility: float | None = None,
        var: float | None = None,
        max_position_pct: float | None = None,
    ) -> None:
        """检查阈值"""
        if self._state == CircuitBreakerState.OPEN:
            return  # 已经熔断

        # 最大回撤
        if drawdown is not None and drawdown > self.config.max_drawdown_pct:
            self._trigger(
                TriggerReason.MAX_DRAWDOWN,
                {"drawdown": drawdown, "threshold": self.config.max_drawdown_pct},
            )
            return

        # 日亏损
        if daily_pnl is not None and daily_pnl < -self.config.max_daily_loss_pct:
            self._trigger(
                TriggerReason.DAILY_LOSS,
                {"daily_pnl": daily_pnl, "threshold": -self.config.max_daily_loss_pct},
            )
            return

        # VaR
        if var is not None and var > self.config.max_var_pct:
            self._trigger(
                TriggerReason.VAR_BREACH,
                {"var": var, "threshold": self.config.max_var_pct},
            )
            return

        # 波动率飙升
        if volatility is not None and self._base_volatility is not None:
            vol_ratio = volatility / self._base_volatility
            if vol_ratio > self.config.max_volatility_ratio:
                self._trigger(
                    TriggerReason.VOLATILITY_SPIKE,
                    {"volatility": volatility, "base": self._base_volatility, "ratio": vol_ratio},
                )
                return

        # 持仓超限
        if max_position_pct is not None and max_position_pct > self.config.max_position_pct:
            self._trigger(
                TriggerReason.POSITION_LIMIT,
                {"max_position": max_position_pct, "threshold": self.config.max_position_pct},
            )
            return

        # 连续亏损
        if self._consecutive_losses >= self.config.max_consecutive_losses:
            self._trigger(
                TriggerReason.CONSECUTIVE_LOSS,
                {"count": self._consecutive_losses, "threshold": self.config.max_consecutive_losses},
            )
            return

    def record_api_error(self) -> None:
        """记录 API 错误"""
        self._api_error_count += 1
        if self._api_error_count >= self.config.max_api_errors:
            self._trigger(
                TriggerReason.API_ERROR,
                {"count": self._api_error_count, "threshold": self.config.max_api_errors},
            )

    def clear_api_errors(self) -> None:
        """清除 API 错误计数"""
        self._api_error_count = 0

    def manual_trigger(self, reason: str = "") -> None:
        """手动触发熔断"""
        self._trigger(TriggerReason.MANUAL, {"reason": reason})

    def manual_reset(self) -> None:
        """手动重置熔断器"""
        self._state = CircuitBreakerState.CLOSED
        self._triggered_at = None
        self._trigger_reason = None
        self._api_error_count = 0

        event = CircuitBreakerEvent(
            timestamp=datetime.now(),
            state=CircuitBreakerState.CLOSED,
            details={"action": "manual_reset"},
        )
        self._events.append(event)

        logger.info("熔断器已手动重置")

    def _trigger(self, reason: TriggerReason, details: dict[str, Any]) -> None:
        """触发熔断"""
        if self._state == CircuitBreakerState.OPEN:
            return

        self._state = CircuitBreakerState.OPEN
        self._triggered_at = datetime.now()
        self._trigger_reason = reason

        event = CircuitBreakerEvent(
            timestamp=self._triggered_at,
            state=CircuitBreakerState.OPEN,
            reason=reason,
            details=details,
        )
        self._events.append(event)

        logger.warning(
            "熔断器触发",
            reason=reason.value,
            details=details,
        )

        if self.on_trigger:
            self.on_trigger(event)

    def _check_auto_recovery(self) -> None:
        """检查自动恢复"""
        if self._state != CircuitBreakerState.OPEN:
            return

        if self._triggered_at is None:
            return

        now = datetime.now()
        elapsed = (now - self._triggered_at).total_seconds() / 60

        # 进入半开状态
        if elapsed >= self.config.cooldown_minutes:
            if self._state == CircuitBreakerState.OPEN:
                self._state = CircuitBreakerState.HALF_OPEN

                event = CircuitBreakerEvent(
                    timestamp=now,
                    state=CircuitBreakerState.HALF_OPEN,
                    details={"elapsed_minutes": elapsed},
                )
                self._events.append(event)

                logger.info("熔断器进入半开状态", elapsed_minutes=elapsed)

        # 从半开恢复
        if self._state == CircuitBreakerState.HALF_OPEN:
            half_open_elapsed = (now - self._triggered_at).total_seconds() / 60
            if half_open_elapsed >= self.config.cooldown_minutes + self.config.half_open_duration_minutes:
                self._state = CircuitBreakerState.CLOSED
                self._triggered_at = None
                self._trigger_reason = None

                event = CircuitBreakerEvent(
                    timestamp=now,
                    state=CircuitBreakerState.CLOSED,
                    details={"action": "auto_recovery"},
                )
                self._events.append(event)

                logger.info("熔断器自动恢复")

    def _check_daily_reset(self) -> None:
        """检查每日重置"""
        now = datetime.now()

        if self._last_reset_date is None or self._last_reset_date.date() != now.date():
            if now.hour >= self.config.daily_reset_hour:
                self._daily_pnl = 0.0
                self._consecutive_losses = 0
                self._api_error_count = 0
                self._last_reset_date = now

                logger.debug("熔断器每日重置")

    def get_status(self) -> dict[str, Any]:
        """获取当前状态"""
        return {
            "state": self._state.value,
            "triggered_at": self._triggered_at.isoformat() if self._triggered_at else None,
            "trigger_reason": self._trigger_reason.value if self._trigger_reason else None,
            "can_trade": self.can_trade(),
            "can_close_only": self.can_trade(is_closing=True),
            "consecutive_losses": self._consecutive_losses,
            "api_error_count": self._api_error_count,
            "daily_pnl": self._daily_pnl,
            "events_count": len(self._events),
        }

    def get_events(self, limit: int = 50) -> list[CircuitBreakerEvent]:
        """获取最近事件"""
        return self._events[-limit:]


class MultiCircuitBreaker:
    """
    多级熔断器

    支持多个熔断级别 (如: 警告/暂停/停止)
    """

    def __init__(
        self,
        levels: list[tuple[str, CircuitBreakerConfig]],
    ):
        """
        Args:
            levels: 熔断级别列表 [(name, config), ...]
        """
        self.breakers = {
            name: CircuitBreaker(config)
            for name, config in levels
        }
        self.level_order = [name for name, _ in levels]

    def get_current_level(self) -> str | None:
        """获取当前触发的最高级别"""
        for level in reversed(self.level_order):
            if self.breakers[level].is_tripped:
                return level
        return None

    def update_all(self, **kwargs) -> None:
        """更新所有熔断器"""
        for breaker in self.breakers.values():
            breaker.update_metrics(**kwargs)

    def can_trade(self) -> bool:
        """是否可以交易"""
        return all(b.can_trade() for b in self.breakers.values())

    def get_status(self) -> dict[str, Any]:
        """获取所有状态"""
        return {
            name: breaker.get_status()
            for name, breaker in self.breakers.items()
        }
