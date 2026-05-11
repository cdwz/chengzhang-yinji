"""
成长印记 - 评价维度 API 路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import EvaluationDimension, Class, User
from app.schemas import MessageResponse
from app.core.security import decode_token
from pydantic import BaseModel

router = APIRouter(prefix="/dimensions", tags=["评价维度"])
security = HTTPBearer()


class DimensionCreate(BaseModel):
    name: str
    type: str  # star, grade, boolean, score, text
    subject: str | None = None


class DimensionUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    subject: str | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class DimensionResponse(BaseModel):
    id: str
    class_id: str
    name: str
    subject: str | None
    type: str
    sort_order: int
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """获取当前用户ID"""
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )

    return payload.get("sub")


# 获取班级评价维度（通过班级ID）
@router.get("/class/{class_id}", response_model=List[DimensionResponse])
async def get_class_dimensions(
    class_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取班级评价维度列表"""
    result = await db.execute(
        select(EvaluationDimension)
        .where(EvaluationDimension.class_id == class_id)
        .order_by(EvaluationDimension.sort_order)
    )
    dimensions = result.scalars().all()
    
    return [
        DimensionResponse(
            id=str(d.id),
            class_id=str(d.class_id),
            name=d.name,
            subject=d.subject,
            type=d.type,
            sort_order=d.sort_order,
            is_active=d.is_active,
            created_at=d.created_at.isoformat()
        )
        for d in dimensions
    ]


# 创建评价维度（通过班级ID）
@router.post("/class/{class_id}", response_model=DimensionResponse)
async def create_dimension(
    class_id: str,
    data: DimensionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建评价维度"""
    # 检查班级是否存在
    result = await db.execute(select(Class).where(Class.id == class_id))
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )
    
    # 获取当前最大排序号
    result = await db.execute(
        select(EvaluationDimension)
        .where(EvaluationDimension.class_id == class_id)
        .order_by(EvaluationDimension.sort_order.desc())
        .limit(1)
    )
    last_dim = result.scalar_one_or_none()
    next_order = (last_dim.sort_order + 1) if last_dim else 1
    
    dimension = EvaluationDimension(
        class_id=class_id,
        name=data.name,
        type=data.type,
        subject=data.subject,
        sort_order=next_order
    )
    
    db.add(dimension)
    await db.commit()
    await db.refresh(dimension)
    
    return DimensionResponse(
        id=str(dimension.id),
        class_id=str(dimension.class_id),
        name=dimension.name,
        subject=dimension.subject,
        type=dimension.type,
        sort_order=dimension.sort_order,
        is_active=dimension.is_active,
        created_at=dimension.created_at.isoformat()
    )


# 更新评价维度
@router.patch("/{dimension_id}", response_model=DimensionResponse)
async def update_dimension(
    dimension_id: str,
    data: DimensionUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新评价维度"""
    result = await db.execute(
        select(EvaluationDimension).where(EvaluationDimension.id == dimension_id)
    )
    dimension = result.scalar_one_or_none()
    
    if not dimension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="维度不存在"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dimension, key, value)
    
    await db.commit()
    await db.refresh(dimension)
    
    return DimensionResponse(
        id=str(dimension.id),
        class_id=str(dimension.class_id),
        name=dimension.name,
        subject=dimension.subject,
        type=dimension.type,
        sort_order=dimension.sort_order,
        is_active=dimension.is_active,
        created_at=dimension.created_at.isoformat()
    )


# 删除评价维度
@router.delete("/{dimension_id}", response_model=MessageResponse)
async def delete_dimension(
    dimension_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除评价维度"""
    result = await db.execute(
        select(EvaluationDimension).where(EvaluationDimension.id == dimension_id)
    )
    dimension = result.scalar_one_or_none()
    
    if not dimension:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="维度不存在"
        )
    
    await db.delete(dimension)
    await db.commit()
    
    return MessageResponse(message="删除成功")


# 批量更新排序
class DimensionOrderItem(BaseModel):
    id: str
    sort_order: int


class DimensionOrderUpdate(BaseModel):
    dimensions: List[DimensionOrderItem]


@router.patch("/order", response_model=MessageResponse)
async def update_dimension_order(
    data: DimensionOrderUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """批量更新维度排序"""
    for item in data.dimensions:
        result = await db.execute(
            select(EvaluationDimension).where(EvaluationDimension.id == item.id)
        )
        dimension = result.scalar_one_or_none()
        if dimension:
            dimension.sort_order = item.sort_order
    
    await db.commit()
    return MessageResponse(message="排序更新成功")
