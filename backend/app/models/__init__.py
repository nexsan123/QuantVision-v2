"""
数据模型模块

包含所有 SQLAlchemy ORM 模型定义:
- 市场数据模型
- 财务数据模型
- 股票池模型
- 数据血缘模型
- 策略V2模型
- 审计日志模型
"""

from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.audit_log import AuditLog, AuditActionType, log_audit_event
from app.models.data_lineage import DataLineage
from app.models.financial_data import FinancialStatement
from app.models.market_data import MacroData, StockOHLCV
from app.models.strategy_v2 import StrategyStatusEnum, StrategyV2
from app.models.universe import Universe, UniverseSnapshot
from app.models.user import User, UserRole, UserStatus, check_permission, ROLE_PERMISSIONS

__all__ = [
    # Mixins
    "UUIDMixin",
    "TimestampMixin",
    "SoftDeleteMixin",
    # 市场数据
    "StockOHLCV",
    "MacroData",
    # 财务数据
    "FinancialStatement",
    # 股票池
    "Universe",
    "UniverseSnapshot",
    # 数据血缘
    "DataLineage",
    # 策略V2
    "StrategyV2",
    "StrategyStatusEnum",
    # 审计日志
    "AuditLog",
    "AuditActionType",
    "log_audit_event",
    # 用户管理
    "User",
    "UserRole",
    "UserStatus",
    "check_permission",
    "ROLE_PERMISSIONS",
]
