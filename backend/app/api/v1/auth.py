"""
认证 API

提供:
- 用户登录
- 令牌刷新
- 用户登出
- 密码修改
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    Token,
    UserInfo,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user_required,
    get_password_hash,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.core.database import get_db
from app.models.user import User, UserStatus
from app.models.audit_log import AuditActionType, log_audit_event

router = APIRouter(prefix="/auth", tags=["认证"])


# === 请求/响应模型 ===

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str = Field(..., min_length=8)


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    token: Token | None = None
    user: UserInfo | None = None
    message: str | None = None


# === API 端点 ===

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """
    用户登录

    使用用户名/邮箱 + 密码登录，返回 JWT 令牌
    """
    # 查找用户 (支持用户名或邮箱)
    result = await db.execute(
        select(User).where(
            (User.username == form_data.username) |
            (User.email == form_data.username)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        return LoginResponse(
            success=False,
            message="用户名或密码错误",
        )

    # 检查账户状态
    if not user.is_active:
        return LoginResponse(
            success=False,
            message="账户已被禁用",
        )

    if user.is_locked:
        return LoginResponse(
            success=False,
            message="账户已被锁定，请稍后重试",
        )

    # 验证密码
    if not verify_password(form_data.password, user.hashed_password):
        # 增加失败次数
        user.failed_login_count += 1

        # 锁定账户 (5 次失败后锁定 15 分钟)
        if user.failed_login_count >= 5:
            from datetime import timedelta
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)

        await db.commit()

        # 记录审计日志
        await log_audit_event(
            db,
            action=AuditActionType.USER_LOGIN,
            resource_type="user",
            resource_id=str(user.id),
            user_id=str(user.id),
            user_name=user.username,
            status="failure",
            error_message="密码错误",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return LoginResponse(
            success=False,
            message="用户名或密码错误",
        )

    # 登录成功
    access_token, access_expire = create_access_token(user)
    refresh_token, refresh_expire = create_refresh_token(user)

    # 更新登录信息
    user.last_login = datetime.utcnow()
    user.last_login_ip = request.client.host if request.client else None
    user.login_count += 1
    user.failed_login_count = 0
    user.locked_until = None
    await db.commit()

    # 记录审计日志
    await log_audit_event(
        db,
        action=AuditActionType.USER_LOGIN,
        resource_type="user",
        resource_id=str(user.id),
        user_id=str(user.id),
        user_name=user.username,
        status="success",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return LoginResponse(
        success=True,
        token=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        user=UserInfo(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_superuser=user.is_superuser,
            permissions=user.permissions,
        ),
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    刷新访问令牌

    使用刷新令牌获取新的访问令牌
    """
    payload = decode_token(request.refresh_token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌类型错误",
        )

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )

    # 生成新令牌
    access_token, access_expire = create_access_token(user)
    refresh_token, refresh_expire = create_refresh_token(user)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> dict:
    """
    用户登出

    记录登出日志
    """
    # 记录审计日志
    await log_audit_event(
        db,
        action=AuditActionType.USER_LOGOUT,
        resource_type="user",
        resource_id=str(user.id),
        user_id=str(user.id),
        user_name=user.username,
        status="success",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"success": True, "message": "已登出"}


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    user: User = Depends(get_current_user_required),
) -> UserInfo:
    """
    获取当前用户信息
    """
    return UserInfo(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_superuser=user.is_superuser,
        permissions=user.permissions,
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user_required),
) -> dict:
    """
    修改密码
    """
    # 验证旧密码
    if not verify_password(request.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误",
        )

    # 更新密码
    user.hashed_password = get_password_hash(request.new_password)
    await db.commit()

    return {"success": True, "message": "密码已修改"}


# === 管理端点 (仅管理员) ===

@router.post("/register", response_model=UserInfo)
async def register_user(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserInfo:
    """
    注册新用户

    仅在开发环境开放，生产环境需要管理员创建
    """
    from app.core.config import settings

    # 检查环境
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="生产环境不允许自助注册",
        )

    # 检查用户名是否已存在
    result = await db.execute(
        select(User).where(
            (User.username == request.username) |
            (User.email == request.email)
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已被使用",
        )

    # 创建用户
    user = User(
        email=request.email,
        username=request.username,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        role="viewer",  # 默认观察者角色
        status=UserStatus.ACTIVE.value,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserInfo(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_superuser=user.is_superuser,
        permissions=user.permissions,
    )
