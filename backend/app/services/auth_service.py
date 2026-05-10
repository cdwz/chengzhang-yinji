"""
成长印记 - 认证服务
"""
from datetime import timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import UserCreate, UserRole
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token,
    generate_verification_code
)
from app.core.config import settings
from app.core.redis_client import set_sms_code, get_sms_code, delete_sms_code


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """创建用户"""
    user = User(
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name,
        role=user_data.role.value
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, phone: str, password: str) -> Optional[User]:
    """验证用户"""
    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    
    return user


async def get_user_by_phone(db: AsyncSession, phone: str) -> Optional[User]:
    """根据手机号获取用户"""
    result = await db.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """根据ID获取用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def generate_tokens(user: User) -> dict:
    """生成访问令牌"""
    access_token = create_access_token(
        subject=str(user.id),
        extra_data={"role": user.role}
    )
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


async def refresh_tokens(refresh_token: str, db: AsyncSession) -> Optional[dict]:
    """刷新令牌"""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return None
    
    user_id = payload.get("sub")
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        return None
    
    return await generate_tokens(user)


async def send_verification_code(phone: str) -> str:
    """发送验证码（测试环境返回固定值）"""
    code = settings.SMS_TEST_CODE  # 测试环境固定验证码
    await set_sms_code(phone, code, expire=300)
    return code


async def verify_code(phone: str, code: str) -> bool:
    """验证验证码"""
    stored_code = await get_sms_code(phone)
    if not stored_code:
        return False
    
    is_valid = stored_code == code
    if is_valid:
        await delete_sms_code(phone)
    
    return is_valid
