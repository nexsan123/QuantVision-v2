"""
风险预警 Schema

PRD 4.14: 风险预警通知
- 单日亏损预警
- 最大回撤预警
- 持仓集中度预警
- VIX波动预警
- 系统异常预警
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AlertType(str, Enum):
    """预警类型"""
    DAILY_LOSS = "daily_loss"           # 单日亏损
    MAX_DRAWDOWN = "max_drawdown"       # 最大回撤
    CONCENTRATION = "concentration"      # 持仓集中度
    VIX_HIGH = "vix_high"               # VIX过高
    CONFLICT_PENDING = "conflict_pending"  # 策略冲突待决策
    SYSTEM_ERROR = "system_error"       # 系统异常
    PDT_WARNING = "pdt_warning"         # PDT警告


class AlertSeverity(str, Enum):
    """预警严重级别"""
    INFO = "info"           # 信息
    WARNING = "warning"     # 黄色警告
    CRITICAL = "critical"   # 红色严重


class AlertChannel(str, Enum):
    """通知渠道"""
    EMAIL = "email"
    # Phase 2: WECHAT = "wechat"
    # Phase 3: APP_PUSH = "app_push"


class RiskAlert(BaseModel):
    """风险预警"""
    alert_id: str
    user_id: str
    strategy_id: Optional[str] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    details: Optional[dict] = None
    is_read: bool = False
    is_sent: bool = False
    sent_channels: list[AlertChannel] = Field(default_factory=list)
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertConfig(BaseModel):
    """用户预警配置"""
    user_id: str
    enabled: bool = True

    # 触发阈值
    daily_loss_threshold: float = Field(0.03, description="单日亏损阈值 (3%)")
    max_drawdown_threshold: float = Field(0.10, description="最大回撤阈值 (10%)")
    concentration_threshold: float = Field(0.30, description="集中度阈值 (30%)")
    vix_threshold: float = Field(30.0, description="VIX阈值")

    # 通知渠道
    email_enabled: bool = True
    email_address: Optional[str] = None

    # 静默时段 (避免夜间打扰)
    quiet_hours_start: Optional[int] = Field(22, description="静默开始时间 (22:00)")
    quiet_hours_end: Optional[int] = Field(8, description="静默结束时间 (08:00)")

    class Config:
        from_attributes = True


class CreateAlertRequest(BaseModel):
    """创建预警请求"""
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    strategy_id: Optional[str] = None
    details: Optional[dict] = None


class AlertListResponse(BaseModel):
    """预警列表响应"""
    total: int
    alerts: list[RiskAlert]
    unread_count: int


class UpdateAlertConfigRequest(BaseModel):
    """更新预警配置请求"""
    enabled: Optional[bool] = None
    daily_loss_threshold: Optional[float] = None
    max_drawdown_threshold: Optional[float] = None
    concentration_threshold: Optional[float] = None
    vix_threshold: Optional[float] = None
    email_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
