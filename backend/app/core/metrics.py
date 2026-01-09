"""
性能指标收集系统
Sprint 13: T34 - 性能监控指标

提供:
- 请求计数器
- 响应时间直方图
- 业务指标
- 系统资源监控
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import psutil


# ==================== 指标数据结构 ====================

@dataclass
class Counter:
    """计数器"""
    value: int = 0
    labels: dict[str, str] = field(default_factory=dict)

    def inc(self, amount: int = 1) -> None:
        self.value += amount

    def reset(self) -> None:
        self.value = 0


@dataclass
class Gauge:
    """仪表盘值"""
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)

    def set(self, value: float) -> None:
        self.value = value

    def inc(self, amount: float = 1.0) -> None:
        self.value += amount

    def dec(self, amount: float = 1.0) -> None:
        self.value -= amount


@dataclass
class Histogram:
    """直方图"""
    buckets: list[float] = field(default_factory=lambda: [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
    counts: dict[float, int] = field(default_factory=dict)
    sum: float = 0.0
    count: int = 0
    labels: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        self.counts = {b: 0 for b in self.buckets}
        self.counts[float('inf')] = 0

    def observe(self, value: float) -> None:
        self.sum += value
        self.count += 1
        for bucket in self.buckets:
            if value <= bucket:
                self.counts[bucket] += 1
        self.counts[float('inf')] += 1


# ==================== 指标收集器 ====================

class MetricsCollector:
    """指标收集器单例"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._start_time = datetime.now()

        # HTTP 请求指标
        self._http_requests_total: dict[str, Counter] = defaultdict(Counter)
        self._http_request_duration: dict[str, Histogram] = defaultdict(
            lambda: Histogram(buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0])
        )
        self._http_requests_in_progress = Gauge()

        # 业务指标
        self._trades_total: dict[str, Counter] = defaultdict(Counter)
        self._strategies_active = Gauge()
        self._signals_generated = Counter()
        self._alerts_triggered = Counter()

        # 数据库指标
        self._db_queries_total = Counter()
        self._db_query_duration = Histogram(buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0])
        self._db_connections_active = Gauge()

        # WebSocket 指标
        self._ws_connections_active = Gauge()
        self._ws_messages_sent = Counter()
        self._ws_messages_received = Counter()

    # ==================== HTTP 指标 ====================

    def record_http_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
    ) -> None:
        """记录 HTTP 请求"""
        key = f"{method}:{path}:{status_code}"
        self._http_requests_total[key].inc()
        self._http_request_duration[f"{method}:{path}"].observe(duration)

    def http_request_started(self) -> None:
        """HTTP 请求开始"""
        self._http_requests_in_progress.inc()

    def http_request_finished(self) -> None:
        """HTTP 请求结束"""
        self._http_requests_in_progress.dec()

    # ==================== 业务指标 ====================

    def record_trade(self, action: str, symbol: str) -> None:
        """记录交易"""
        self._trades_total[f"{action}:{symbol}"].inc()

    def set_active_strategies(self, count: int) -> None:
        """设置活跃策略数"""
        self._strategies_active.set(count)

    def record_signal(self) -> None:
        """记录信号生成"""
        self._signals_generated.inc()

    def record_alert(self) -> None:
        """记录告警触发"""
        self._alerts_triggered.inc()

    # ==================== 数据库指标 ====================

    def record_db_query(self, duration: float) -> None:
        """记录数据库查询"""
        self._db_queries_total.inc()
        self._db_query_duration.observe(duration)

    def set_db_connections(self, count: int) -> None:
        """设置数据库连接数"""
        self._db_connections_active.set(count)

    # ==================== WebSocket 指标 ====================

    def ws_connection_opened(self) -> None:
        """WebSocket 连接打开"""
        self._ws_connections_active.inc()

    def ws_connection_closed(self) -> None:
        """WebSocket 连接关闭"""
        self._ws_connections_active.dec()

    def record_ws_message(self, direction: str) -> None:
        """记录 WebSocket 消息"""
        if direction == "sent":
            self._ws_messages_sent.inc()
        else:
            self._ws_messages_received.inc()

    # ==================== 系统指标 ====================

    def get_system_metrics(self) -> dict[str, Any]:
        """获取系统资源指标"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used / (1024 * 1024),
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_used_gb": disk.used / (1024 * 1024 * 1024),
        }

    # ==================== 导出 ====================

    def get_all_metrics(self) -> dict[str, Any]:
        """获取所有指标"""
        uptime = datetime.now() - self._start_time

        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime.total_seconds(),

            # 系统指标
            "system": self.get_system_metrics(),

            # HTTP 指标
            "http": {
                "requests_in_progress": self._http_requests_in_progress.value,
                "requests_total": sum(c.value for c in self._http_requests_total.values()),
                "request_duration_sum": sum(
                    h.sum for h in self._http_request_duration.values()
                ),
            },

            # 业务指标
            "business": {
                "trades_total": sum(c.value for c in self._trades_total.values()),
                "strategies_active": self._strategies_active.value,
                "signals_generated": self._signals_generated.value,
                "alerts_triggered": self._alerts_triggered.value,
            },

            # 数据库指标
            "database": {
                "queries_total": self._db_queries_total.value,
                "query_duration_sum": self._db_query_duration.sum,
                "connections_active": self._db_connections_active.value,
            },

            # WebSocket 指标
            "websocket": {
                "connections_active": self._ws_connections_active.value,
                "messages_sent": self._ws_messages_sent.value,
                "messages_received": self._ws_messages_received.value,
            },
        }

    def get_prometheus_metrics(self) -> str:
        """生成 Prometheus 格式指标"""
        lines = []
        metrics = self.get_all_metrics()

        # 系统指标
        lines.append(f'# HELP system_cpu_percent CPU usage percentage')
        lines.append(f'# TYPE system_cpu_percent gauge')
        lines.append(f'system_cpu_percent {metrics["system"]["cpu_percent"]}')

        lines.append(f'# HELP system_memory_percent Memory usage percentage')
        lines.append(f'# TYPE system_memory_percent gauge')
        lines.append(f'system_memory_percent {metrics["system"]["memory_percent"]}')

        # HTTP 指标
        lines.append(f'# HELP http_requests_total Total HTTP requests')
        lines.append(f'# TYPE http_requests_total counter')
        lines.append(f'http_requests_total {metrics["http"]["requests_total"]}')

        lines.append(f'# HELP http_requests_in_progress HTTP requests in progress')
        lines.append(f'# TYPE http_requests_in_progress gauge')
        lines.append(f'http_requests_in_progress {metrics["http"]["requests_in_progress"]}')

        # 业务指标
        lines.append(f'# HELP trades_total Total trades executed')
        lines.append(f'# TYPE trades_total counter')
        lines.append(f'trades_total {metrics["business"]["trades_total"]}')

        lines.append(f'# HELP strategies_active Active strategies')
        lines.append(f'# TYPE strategies_active gauge')
        lines.append(f'strategies_active {metrics["business"]["strategies_active"]}')

        # WebSocket 指标
        lines.append(f'# HELP websocket_connections_active Active WebSocket connections')
        lines.append(f'# TYPE websocket_connections_active gauge')
        lines.append(f'websocket_connections_active {metrics["websocket"]["connections_active"]}')

        return '\n'.join(lines) + '\n'


# ==================== 全局实例 ====================

metrics = MetricsCollector()


# ==================== 上下文管理器 ====================

class TimerContext:
    """计时上下文管理器"""

    def __init__(self, callback):
        self.callback = callback
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        duration = time.perf_counter() - self.start_time
        self.callback(duration)


def time_db_query():
    """数据库查询计时"""
    return TimerContext(metrics.record_db_query)


# ==================== 导出 ====================

__all__ = [
    "metrics",
    "MetricsCollector",
    "time_db_query",
]
