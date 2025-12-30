"""
通用 Schema

提供:
- 响应基类
- 分页响应
- 错误响应
- 日期范围请求
"""

from datetime import date, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseBase(BaseModel, Generic[T]):
    """
    API 响应基类

    标准化响应格式:
    {
        "success": true,
        "data": {...},
        "message": "成功"
    }
    """
    success: bool = True
    data: T | None = None
    message: str = "成功"


class ErrorResponse(BaseModel):
    """
    错误响应

    {
        "success": false,
        "error": {
            "code": "INVALID_INPUT",
            "message": "参数错误",
            "details": {...}
        }
    }
    """
    success: bool = False
    error: dict[str, Any]


class PaginatedResponse(BaseModel, Generic[T]):
    """
    分页响应

    {
        "success": true,
        "data": {
            "items": [...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "pages": 5
        }
    }
    """
    success: bool = True
    data: dict[str, Any]

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse":
        """创建分页响应"""
        pages = (total + page_size - 1) // page_size
        return cls(
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": pages,
            }
        )


class DateRangeRequest(BaseModel):
    """日期范围请求"""
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")

    def validate_range(self) -> None:
        """验证日期范围"""
        if self.start_date > self.end_date:
            raise ValueError("开始日期不能大于结束日期")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    components: dict[str, str] = Field(default_factory=dict)
