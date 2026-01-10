"""
JWT 认证模块

机构级认证系统:
- JWT 令牌生成与验证
- 刷新令牌机制
- 密码哈希
- 登录追踪
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserStatus

# === 密码哈希配置 ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === OAuth2 配置 ===
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,  # 允许可选认证
)

# === JWT 配置 ===
JWT_SECRET_KEY = getattr(settings, "JWT_SECRET_KEY", "quantvision-dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


# === 数据模型 ===

class Token(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    """令牌载荷"""
    sub: str  # user_id
    exp: datetime
    type: str  # "access" or "refresh"
    role: str
    permissions: dict[str, list[str]] | None = None


class UserInfo(BaseModel):
    """用户信息响应"""
    id: str
    email: str
    username: str
    full_name: str | None
    role: str
    is_superuser: bool
    permissions: dict[str, list[str]] | None


# === 密码函数 ===

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


# === JWT 函数 ===

def create_access_token(user: User) -> tuple[str, datetime]:
    """
    创建访问令牌

    Args:
        user: 用户对象

    Returns:
        (令牌, 过期时间)
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user.id),
        "exp": expire,
        "type": "access",
        "role": user.role,
        "email": user.email,
        "username": user.username,
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expire


def create_refresh_token(user: User) -> tuple[str, datetime]:
    """
    创建刷新令牌

    Args:
        user: 用户对象

    Returns:
        (令牌, 过期时间)
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user.id),
        "exp": expire,
        "type": "refresh",
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token, expire


def decode_token(token: str) -> dict[str, Any] | None:
    """
    解码令牌

    Args:
        token: JWT 令牌

    Returns:
        载荷或 None (如果无效)
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# === 认证依赖 ===

async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    获取当前用户 (可选认证)

    如果没有令牌，返回 None
    如果令牌无效，抛出 401
    """
    if not token:
        return None

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌载荷无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被锁定",
        )

    return user


async def get_current_user_required(
    user: User | None = Depends(get_current_user),
) -> User:
    """
    获取当前用户 (必须认证)
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_admin(
    user: User = Depends(get_current_user_required),
) -> User:
    """
    获取当前管理员
    """
    if user.role != "admin" and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return user


# === 权限检查装饰器 ===

class PermissionChecker:
    """权限检查器"""

    def __init__(self, resource: str, action: str):
        self.resource = resource
        self.action = action

    async def __call__(
        self,
        user: User = Depends(get_current_user_required),
    ) -> User:
        from app.models.user import check_permission

        if not check_permission(user, self.resource, self.action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"没有 {self.resource}:{self.action} 权限",
            )
        return user


# 常用权限依赖
require_trading_submit = PermissionChecker("trading", "submit")
require_trading_view = PermissionChecker("trading", "view")
require_strategy_create = PermissionChecker("strategies", "create")
require_strategy_deploy = PermissionChecker("strategies", "deploy")
require_users_manage = PermissionChecker("users", "update")
require_audit_read = PermissionChecker("audit", "read")
