"""
策略冲突检测 Schema 定义
PRD 4.6 策略冲突检测
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class ConflictType(str, Enum):
    """冲突类型"""
    LOGIC = "logic"  # 逻辑冲突: 同一股票相反信号
    EXECUTION = "execution"  # 执行冲突: 资金/仓位限制
    TIMEOUT = "timeout"  # 超时冲突: 信号过期
    DUPLICATE = "duplicate"  # 重复冲突: 重复买入同一股票


class ConflictSeverity(str, Enum):
    """冲突严重程度"""
    CRITICAL = "critical"  # 严重: 必须处理
    WARNING = "warning"  # 警告: 建议处理
    INFO = "info"  # 提示: 仅供参考


class ConflictStatus(str, Enum):
    """冲突状态"""
    PENDING = "pending"  # 待处理
    RESOLVED = "resolved"  # 已解决
    IGNORED = "ignored"  # 已忽略
    AUTO_RESOLVED = "auto_resolved"  # 自动解决


class ResolutionAction(str, Enum):
    """解决方案"""
    EXECUTE_STRATEGY_A = "execute_strategy_a"  # 执行策略A
    EXECUTE_STRATEGY_B = "execute_strategy_b"  # 执行策略B
    EXECUTE_BOTH = "execute_both"  # 两个都执行
    CANCEL_BOTH = "cancel_both"  # 两个都取消
    REDUCE_POSITION = "reduce_position"  # 减仓执行
    DELAY_EXECUTION = "delay_execution"  # 延迟执行
    IGNORE = "ignore"  # 忽略冲突


class ConflictingSignal(BaseModel):
    """冲突信号"""
    strategy_id: str
    strategy_name: str
    signal_id: str
    symbol: str
    direction: Literal["buy", "sell"]
    quantity: int
    price: float
    signal_time: datetime
    signal_strength: float = Field(ge=0, le=1, description="信号强度 0-1")
    expected_return: Optional[float] = Field(None, description="预期收益率")
    confidence: float = Field(ge=0, le=1, description="信号置信度")


class ConflictDetail(BaseModel):
    """冲突详情"""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    status: ConflictStatus

    # 冲突双方信号
    signal_a: ConflictingSignal
    signal_b: Optional[ConflictingSignal] = None  # 执行/超时冲突可能只有一个信号

    # 冲突说明
    description: str
    reason: str = Field(description="冲突原因")
    impact: str = Field(description="潜在影响")

    # 建议解决方案
    suggested_resolution: ResolutionAction
    resolution_reason: str = Field(description="建议原因")
    alternative_resolutions: list[ResolutionAction] = Field(default=[])

    # 时间信息
    detected_at: datetime
    expires_at: Optional[datetime] = Field(None, description="冲突过期时间")
    resolved_at: Optional[datetime] = None

    # 解决信息
    resolution: Optional[ResolutionAction] = None
    resolved_by: Optional[str] = None  # "user" | "system" | "timeout"


class ConflictCheckRequest(BaseModel):
    """冲突检测请求"""
    strategy_ids: list[str] = Field(description="要检测的策略ID列表")
    symbol: Optional[str] = Field(None, description="指定股票")
    check_execution: bool = Field(True, description="是否检测执行冲突")
    check_timeout: bool = Field(True, description="是否检测超时冲突")


class ConflictCheckResult(BaseModel):
    """冲突检测结果"""
    total_conflicts: int
    critical_count: int
    warning_count: int
    info_count: int
    conflicts: list[ConflictDetail]
    checked_at: datetime


class ResolveConflictRequest(BaseModel):
    """解决冲突请求"""
    conflict_id: str
    resolution: ResolutionAction
    reason: Optional[str] = Field(None, description="解决原因说明")


class ConflictListResponse(BaseModel):
    """冲突列表响应"""
    total: int
    pending_count: int
    conflicts: list[ConflictDetail]


# 冲突类型配置
CONFLICT_TYPE_CONFIG = {
    ConflictType.LOGIC: {
        "label": "逻辑冲突",
        "description": "同一股票存在相反的交易信号",
        "icon": "⚔️",
        "default_severity": ConflictSeverity.CRITICAL,
    },
    ConflictType.EXECUTION: {
        "label": "执行冲突",
        "description": "资金或仓位限制导致无法执行",
        "icon": "💰",
        "default_severity": ConflictSeverity.WARNING,
    },
    ConflictType.TIMEOUT: {
        "label": "超时冲突",
        "description": "信号已超过有效期",
        "icon": "⏰",
        "default_severity": ConflictSeverity.WARNING,
    },
    ConflictType.DUPLICATE: {
        "label": "重复冲突",
        "description": "多个策略发出相同的买入信号",
        "icon": "📋",
        "default_severity": ConflictSeverity.INFO,
    },
}


# 严重程度配置
SEVERITY_CONFIG = {
    ConflictSeverity.CRITICAL: {
        "label": "严重",
        "color": "#ef4444",
        "bgColor": "bg-red-500/10",
        "description": "必须处理后才能继续执行",
    },
    ConflictSeverity.WARNING: {
        "label": "警告",
        "color": "#f59e0b",
        "bgColor": "bg-yellow-500/10",
        "description": "建议处理，可选择忽略",
    },
    ConflictSeverity.INFO: {
        "label": "提示",
        "color": "#3b82f6",
        "bgColor": "bg-blue-500/10",
        "description": "仅供参考，无需处理",
    },
}


# 解决方案配置
RESOLUTION_CONFIG = {
    ResolutionAction.EXECUTE_STRATEGY_A: {
        "label": "执行策略A",
        "description": "执行第一个策略的信号，取消第二个",
    },
    ResolutionAction.EXECUTE_STRATEGY_B: {
        "label": "执行策略B",
        "description": "执行第二个策略的信号，取消第一个",
    },
    ResolutionAction.EXECUTE_BOTH: {
        "label": "同时执行",
        "description": "同时执行两个策略的信号（可能导致对冲）",
    },
    ResolutionAction.CANCEL_BOTH: {
        "label": "全部取消",
        "description": "取消两个策略的信号，不执行任何交易",
    },
    ResolutionAction.REDUCE_POSITION: {
        "label": "减仓执行",
        "description": "减少执行数量以满足仓位限制",
    },
    ResolutionAction.DELAY_EXECUTION: {
        "label": "延迟执行",
        "description": "等待资金到位后再执行",
    },
    ResolutionAction.IGNORE: {
        "label": "忽略",
        "description": "忽略此冲突，按原计划执行",
    },
}
