"""
策略漂移监控 Schema 定义
PRD 4.8 实盘vs回测差异监控
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, date
from enum import Enum


class DriftMetricType(str, Enum):
    """漂移指标类型"""
    RETURN = "return"               # 收益差异
    WIN_RATE = "win_rate"           # 胜率差异
    TURNOVER = "turnover"           # 换手率差异
    SLIPPAGE = "slippage"           # 滑点差异
    MAX_DRAWDOWN = "max_drawdown"   # 最大回撤差异
    HOLD_PERIOD = "hold_period"     # 持仓时间差异


class DriftSeverity(str, Enum):
    """漂移严重程度"""
    NORMAL = "normal"       # 正常范围
    WARNING = "warning"     # 黄色预警
    CRITICAL = "critical"   # 红色严重


class DriftMetric(BaseModel):
    """单个漂移指标"""
    metric_type: DriftMetricType
    backtest_value: float           # 回测值
    live_value: float               # 实盘值
    difference: float               # 差异 (绝对值)
    difference_pct: float           # 差异百分比
    warning_threshold: float        # 黄色预警阈值
    critical_threshold: float       # 红色严重阈值
    severity: DriftSeverity
    description: str


class StrategyDriftReport(BaseModel):
    """策略漂移报告"""
    report_id: str
    strategy_id: str
    strategy_name: str
    deployment_id: str
    environment: Literal["paper", "live"]

    # 时间范围
    period_start: date
    period_end: date
    days_compared: int

    # 整体状态
    overall_severity: DriftSeverity
    drift_score: float = Field(ge=0, le=100, description="漂移评分 0-100, 越高越偏离")

    # 各指标详情
    metrics: list[DriftMetric]

    # 建议
    recommendations: list[str]
    should_pause: bool = Field(default=False, description="是否建议暂停策略")

    # 元数据
    created_at: datetime
    is_acknowledged: bool = Field(default=False, description="用户是否已确认")


class DriftThresholds(BaseModel):
    """
    漂移阈值配置 (PRD 附录C)
    """
    # 黄色预警阈值
    return_warning: float = Field(default=0.10, description="收益差异 > 10%")
    win_rate_warning: float = Field(default=0.05, description="胜率差异 > 5%")
    turnover_warning: float = Field(default=0.20, description="换手率差异 > 20%")
    slippage_warning: float = Field(default=0.30, description="滑点差异 > 30%")
    max_drawdown_warning: float = Field(default=0.15, description="最大回撤差异 > 15%")
    hold_period_warning: float = Field(default=0.25, description="持仓时间差异 > 25%")

    # 红色严重阈值
    return_critical: float = Field(default=0.20, description="收益差异 > 20%")
    win_rate_critical: float = Field(default=0.10, description="胜率差异 > 10%")
    turnover_critical: float = Field(default=0.35, description="换手率差异 > 35%")
    slippage_critical: float = Field(default=0.50, description="滑点差异 > 50%")
    max_drawdown_critical: float = Field(default=0.25, description="最大回撤差异 > 25%")
    hold_period_critical: float = Field(default=0.40, description="持仓时间差异 > 40%")


class DriftCheckRequest(BaseModel):
    """漂移检查请求"""
    strategy_id: str
    deployment_id: str
    period_days: int = Field(default=30, ge=7, le=365, description="比较周期 (天)")


class DriftCheckResponse(BaseModel):
    """漂移检查响应"""
    success: bool
    message: str
    report: Optional[StrategyDriftReport] = None


class DriftReportListResponse(BaseModel):
    """漂移报告列表响应"""
    total: int
    reports: list[StrategyDriftReport]


class DriftAcknowledgeRequest(BaseModel):
    """确认漂移报告请求"""
    notes: Optional[str] = Field(default=None, description="确认备注")


# 指标显示配置
DRIFT_METRIC_CONFIG = {
    DriftMetricType.RETURN: {
        "label": "收益率",
        "icon": "📈",
        "format": "percent",
    },
    DriftMetricType.WIN_RATE: {
        "label": "胜率",
        "icon": "🎯",
        "format": "percent",
    },
    DriftMetricType.TURNOVER: {
        "label": "换手率",
        "icon": "🔄",
        "format": "percent",
    },
    DriftMetricType.SLIPPAGE: {
        "label": "滑点",
        "icon": "💸",
        "format": "percent",
    },
    DriftMetricType.MAX_DRAWDOWN: {
        "label": "最大回撤",
        "icon": "📉",
        "format": "percent",
    },
    DriftMetricType.HOLD_PERIOD: {
        "label": "持仓天数",
        "icon": "📅",
        "format": "days",
    },
}

# 严重程度配置
DRIFT_SEVERITY_CONFIG = {
    DriftSeverity.NORMAL: {
        "icon": "✅",
        "color": "#22c55e",
        "text": "正常",
        "bg_color": "bg-green-500/10",
    },
    DriftSeverity.WARNING: {
        "icon": "⚠️",
        "color": "#eab308",
        "text": "需关注",
        "bg_color": "bg-yellow-500/10",
    },
    DriftSeverity.CRITICAL: {
        "icon": "🔴",
        "color": "#ef4444",
        "text": "异常",
        "bg_color": "bg-red-500/10",
    },
}
