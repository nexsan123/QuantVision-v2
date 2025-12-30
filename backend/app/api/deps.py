"""
API 依赖注入

提供:
- 数据库会话
- Redis 连接
- 认证依赖
- 通用验证
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis

# 类型别名
DBSession = Annotated[AsyncSession, Depends(get_db)]
RedisConn = Annotated[Redis, Depends(get_redis)]


async def get_current_user(
    x_user_id: str | None = Header(None, alias="X-User-ID"),
) -> str | None:
    """
    获取当前用户

    简化版认证，后续可扩展为 JWT 验证
    """
    return x_user_id


CurrentUser = Annotated[str | None, Depends(get_current_user)]


def pagination_params(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
) -> dict[str, int]:
    """分页参数"""
    return {
        "page": page,
        "page_size": page_size,
        "offset": (page - 1) * page_size,
    }


Pagination = Annotated[dict[str, int], Depends(pagination_params)]


def validate_date_range(
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
) -> dict[str, str]:
    """验证日期范围"""
    from datetime import datetime

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="日期格式错误，应为 YYYY-MM-DD",
        )

    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="开始日期不能大于结束日期",
        )

    return {"start_date": start_date, "end_date": end_date}


DateRange = Annotated[dict[str, str], Depends(validate_date_range)]
