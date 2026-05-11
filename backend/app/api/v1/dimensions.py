"""
成长印记 - 评价维度 API 路由
支持6种类型：star, grade, score, ab_score, boolean, text
"""
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import EvaluationDimension, Class, User, EvaluationRecord
from app.schemas import MessageResponse
from app.core.security import decode_token
from pydantic import BaseModel, Field

router = APIRouter(prefix="/dimensions", tags=["评价维度"])
security = HTTPBearer()

VALID_TYPES = ["star", "grade", "score", "ab_score", "boolean", "text"]


class DimensionCreate(BaseModel):
    name: str
    type: str  # star, grade, score, ab_score, boolean, text
    subject: Optional[str] = None
    config: dict = {}  # score: {score_type, max_score}, ab_score: {total, a_score, b_score}


class DimensionUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    subject: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class DimensionResponse(BaseModel):
    id: str
    class_id: str
    name: str
    subject: Optional[str]
    type: str
    config: dict = {}
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


def validate_config(dim_type: str, config: dict):
    """验证类型配置"""
    if dim_type == "score":
        score_type = config.get("score_type", "100")
        max_score = config.get("max_score", 100)
        if score_type not in ("10", "100", "custom"):
            raise HTTPException(400, "score_type 必须为 10/100/custom")
        if score_type == "custom" and (not isinstance(max_score, (int, float)) or max_score <= 0):
            raise HTTPException(400, "自定义分制必须设置有效的 max_score")
    elif dim_type == "ab_score":
        total = config.get("total", 150)
        a_score = config.get("a_score", 100)
        b_score = config.get("b_score", 50)
        if a_score + b_score != total:
            raise HTTPException(400, f"A卷{a_score} + B卷{b_score} ≠ 总分{total}")


def dim_to_response(d: EvaluationDimension) -> DimensionResponse:
    return DimensionResponse(
        id=str(d.id),
        class_id=str(d.class_id),
        name=d.name,
        subject=d.subject,
        type=d.type,
        config=d.config or {},
        sort_order=d.sort_order,
        is_active=d.is_active,
        created_at=d.created_at.isoformat()
    )


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
    return [dim_to_response(d) for d in dimensions]


@router.post("/class/{class_id}", response_model=DimensionResponse)
async def create_dimension(
    class_id: str,
    data: DimensionCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建评价维度"""
    if data.type not in VALID_TYPES:
        raise HTTPException(400, f"无效类型，可选: {', '.join(VALID_TYPES)}")
    
    # 检查班级
    result = await db.execute(select(Class).where(Class.id == class_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "班级不存在")
    
    # 验证配置
    config = data.config or {}
    if data.type in ("score", "ab_score"):
        if data.type == "score" and not config:
            config = {"score_type": "100", "max_score": 100}
        elif data.type == "ab_score" and not config:
            config = {"total": 150, "a_score": 100, "b_score": 50}
        validate_config(data.type, config)
    
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
        config=config,
        sort_order=next_order
    )
    
    db.add(dimension)
    await db.commit()
    await db.refresh(dimension)
    return dim_to_response(dimension)


@router.put("/{dimension_id}", response_model=DimensionResponse)
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
        raise HTTPException(404, "维度不存在")
    
    if data.type and data.type not in VALID_TYPES:
        raise HTTPException(400, f"无效类型，可选: {', '.join(VALID_TYPES)}")
    
    update_data = data.model_dump(exclude_unset=True)
    
    # 处理config更新
    if "config" in update_data and update_data["config"] is not None:
        new_type = update_data.get("type", dimension.type)
        validate_config(new_type, update_data["config"])
    
    for key, value in update_data.items():
        if value is not None:
            setattr(dimension, key, value)
    
    await db.commit()
    await db.refresh(dimension)
    return dim_to_response(dimension)


@router.delete("/{dimension_id}", response_model=MessageResponse)
async def delete_dimension(
    dimension_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除评价维度（级联删除评价记录）"""
    result = await db.execute(
        select(EvaluationDimension).where(EvaluationDimension.id == dimension_id)
    )
    dimension = result.scalar_one_or_none()
    if not dimension:
        raise HTTPException(404, "维度不存在")
    
    # 级联删除评价记录
    await db.execute(
        EvaluationRecord.__table__.delete().where(
            EvaluationRecord.dimension_id == dimension_id
        )
    )
    
    await db.delete(dimension)
    await db.commit()
    return MessageResponse(message="维度及关联评价记录已删除")


class DimensionOrderItem(BaseModel):
    id: str
    sort_order: int


class DimensionOrderUpdate(BaseModel):
    dimensions: List[DimensionOrderItem]


@router.put("/order", response_model=MessageResponse)
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
