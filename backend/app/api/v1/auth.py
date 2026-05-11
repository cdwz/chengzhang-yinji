"""
成长印记 - 认证 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.schemas import (
    UserCreate, UserLogin, UserResponse, TokenResponse,
    RefreshTokenRequest, MessageResponse
)
from app.services.auth_service import (
    create_user, authenticate_user, get_user_by_phone,
    generate_tokens, refresh_tokens, send_verification_code, verify_code
)

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()


@router.post("/send-code", response_model=MessageResponse)
async def send_code(phone: str):
    """发送验证码"""
    code = await send_verification_code(phone)
    return MessageResponse(message=f"验证码已发送（测试环境固定为：{code}）")


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    # 验证验证码
    if not await verify_code(user_data.phone, user_data.verification_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误或已过期"
        )
    
    # 检查用户是否已存在
    existing_user = await get_user_by_phone(db, user_data.phone)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该手机号已注册"
        )
    
    # 创建用户
    user = await create_user(db, user_data)
    
    # 生成令牌
    tokens = await generate_tokens(user)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user = await authenticate_user(db, credentials.phone, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误"
        )
    
    tokens = await generate_tokens(user)
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """刷新令牌"""
    tokens = await refresh_tokens(request.refresh_token, db)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )
    
    # 获取用户信息
    from app.core.security import decode_token
    payload = decode_token(request.refresh_token)
    from app.services.auth_service import get_user_by_id
    user = await get_user_by_id(db, payload.get("sub"))
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户信息"""
    from app.core.security import decode_token
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    
    user_id = payload.get("sub")
    from app.services.auth_service import get_user_by_id
    user = await get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return UserResponse.model_validate(user)


@router.get("/my-school")
async def get_my_school(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户关联的学校"""
    from app.core.security import decode_token
    from app.models import SchoolAdmin, School
    from sqlalchemy import select
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    
    user_id = payload.get("sub")
    role = payload.get("role")
    
    # 学校管理员和教师通过SchoolAdmin获取学校
    if role in ["school_admin", "teacher"]:
        result = await db.execute(
            select(School)
            .join(SchoolAdmin, SchoolAdmin.school_id == School.id)
            .where(SchoolAdmin.user_id == user_id)
        )
        school = result.scalar_one_or_none()
        
        if school:
            return {
                "id": str(school.id),
                "name": school.name,
                "address": school.address
            }
    
    # 如果没有关联学校，返回提示
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="您还未关联学校，请联系管理员"
    )
