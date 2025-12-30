"""
Pydantic Schema 模块

API 请求/响应数据验证:
- 通用 Schema
- 因子 Schema
- 回测 Schema
"""

from app.schemas.backtest import (
    BacktestCreateRequest,
    BacktestResponse,
    BacktestResultResponse,
)
from app.schemas.common import (
    DateRangeRequest,
    ErrorResponse,
    PaginatedResponse,
    ResponseBase,
)
from app.schemas.factor import (
    FactorCreateRequest,
    FactorResponse,
    ICAnalysisResponse,
)

__all__ = [
    # 通用
    "ResponseBase",
    "PaginatedResponse",
    "ErrorResponse",
    "DateRangeRequest",
    # 因子
    "FactorCreateRequest",
    "FactorResponse",
    "ICAnalysisResponse",
    # 回测
    "BacktestCreateRequest",
    "BacktestResponse",
    "BacktestResultResponse",
]
