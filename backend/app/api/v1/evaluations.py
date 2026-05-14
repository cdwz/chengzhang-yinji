"""
成长印记 - 评价 API 路由
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models import EvaluationDimension, EvaluationRecord, Student
from app.schemas import (
    DimensionCreate, DimensionResponse,
    EvaluationCreate, EvaluationBatchCreate, EvaluationResponse,
    MessageResponse
)
from app.core.security import decode_token

router = APIRouter(prefix="/evaluations", tags=["评价管理"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """获取当前用户"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    
    return {
        "id": payload.get("sub"),
        "role": payload.get("role")
    }


@router.post("/dimensions", response_model=DimensionResponse)
async def create_dimension(
    dimension_data: DimensionCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建评价维度（班主任）"""
    dimension = EvaluationDimension(
        class_id=dimension_data.class_id,
        name=dimension_data.name,
        subject=dimension_data.subject,
        type=dimension_data.type.value
    )
    
    db.add(dimension)
    await db.commit()
    await db.refresh(dimension)
    
    return DimensionResponse.model_validate(dimension)


@router.get("/dimensions", response_model=List[DimensionResponse])
async def list_dimensions(
    class_id: str = Query(..., description="班级ID"),
    db: AsyncSession = Depends(get_db)
):
    """获取评价维度列表"""
    result = await db.execute(
        select(EvaluationDimension)
        .where(EvaluationDimension.class_id == class_id)
        .where(EvaluationDimension.is_active == True)
        .order_by(EvaluationDimension.sort_order)
    )
    dimensions = result.scalars().all()
    
    return [DimensionResponse.model_validate(d) for d in dimensions]


@router.post("/records", response_model=MessageResponse)
async def create_evaluation(
    eval_data: EvaluationCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交评价记录"""
    # 检查是否已存在
    existing = await db.execute(
        select(EvaluationRecord).where(
            and_(
                EvaluationRecord.dimension_id == eval_data.dimension_id,
                EvaluationRecord.student_id == eval_data.student_id,
                EvaluationRecord.record_date == eval_data.record_date
            )
        )
    )
    
    if existing.scalar_one_or_none():
        # 更新
        record = existing.scalar_one()
        record.value = eval_data.value
        record.teacher_id = user["id"]
    else:
        # 新建
        record = EvaluationRecord(
            dimension_id=eval_data.dimension_id,
            student_id=eval_data.student_id,
            record_date=eval_data.record_date,
            value=eval_data.value,
            teacher_id=user["id"]
        )
        db.add(record)
    
    await db.commit()
    
    return MessageResponse(message="评价记录已保存")


@router.post("/records/batch", response_model=MessageResponse)
async def batch_create_evaluations(
    batch_data: EvaluationBatchCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量提交评价记录"""
    for eval_data in batch_data.records:
        # 检查是否已存在
        existing = await db.execute(
            select(EvaluationRecord).where(
                and_(
                    EvaluationRecord.dimension_id == eval_data.dimension_id,
                    EvaluationRecord.student_id == eval_data.student_id,
                    EvaluationRecord.record_date == eval_data.record_date
                )
            )
        )
        
        if existing.scalar_one_or_none():
            record = existing.scalar_one()
            record.value = eval_data.value
            record.teacher_id = user["id"]
        else:
            record = EvaluationRecord(
                dimension_id=eval_data.dimension_id,
                student_id=eval_data.student_id,
                record_date=eval_data.record_date,
                value=eval_data.value,
                teacher_id=user["id"]
            )
            db.add(record)
    
    await db.commit()
    
    return MessageResponse(message=f"已保存{len(batch_data.records)}条评价记录")


@router.get("/records", response_model=List[EvaluationResponse])
async def list_evaluations(
    class_id: str = Query(..., description="班级ID"),
    dimension_id: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """获取评价记录列表"""
    # 先获取班级的所有维度
    dim_result = await db.execute(
        select(EvaluationDimension.id).where(EvaluationDimension.class_id == class_id)
    )
    dimension_ids = [d[0] for d in dim_result.all()]
    
    if not dimension_ids:
        return []
    
    query = select(EvaluationRecord).where(
        EvaluationRecord.dimension_id.in_(dimension_ids)
    )
    
    if dimension_id:
        query = query.where(EvaluationRecord.dimension_id == dimension_id)
    if student_id:
        query = query.where(EvaluationRecord.student_id == student_id)
    if start_date:
        query = query.where(EvaluationRecord.record_date >= start_date)
    if end_date:
        query = query.where(EvaluationRecord.record_date <= end_date)
    
    query = query.order_by(EvaluationRecord.record_date.desc())
    result = await db.execute(query)
    records = result.scalars().all()
    
    return [EvaluationResponse.model_validate(r) for r in records]


@router.get("/my", response_model=List[EvaluationResponse])
async def get_my_evaluations(
    student_id: str = Query(..., description="学生ID"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取自己孩子的评价记录（家长端）"""
    # 验证家长是否有权限查看该学生
    from app.models import ParentStudent
    
    ps_result = await db.execute(
        select(ParentStudent).where(
            and_(
                ParentStudent.parent_id == user["id"],
                ParentStudent.student_id == student_id
            )
        )
    )
    
    if not ps_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该学生的评价记录"
        )
    
    query = select(EvaluationRecord).where(
        EvaluationRecord.student_id == student_id
    )
    
    if start_date:
        query = query.where(EvaluationRecord.record_date >= start_date)
    if end_date:
        query = query.where(EvaluationRecord.record_date <= end_date)
    
    query = query.order_by(EvaluationRecord.record_date.desc())
    result = await db.execute(query)
    records = result.scalars().all()
    
    return [EvaluationResponse.model_validate(r) for r in records]


@router.get("/my-with-class-stats")
async def get_my_evaluations_with_class_stats(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取自己孩子的评价记录及班级整体分布（家长端）"""
    from app.models import ParentStudent
    from sqlalchemy import func
    
    # 获取家长绑定的学生
    ps_result = await db.execute(
        select(ParentStudent).where(ParentStudent.parent_id == user["id"])
    )
    parent_students = ps_result.scalars().all()
    
    if not parent_students:
        return {"my_records": [], "class_stats": None}
    
    student_id = parent_students[0].student_id
    
    # 获取学生信息
    s_result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = s_result.scalar_one_or_none()
    
    if not student:
        return {"my_records": [], "class_stats": None}
    
    class_id = student.class_id
    
    # 查询自己孩子的评价记录
    query = select(EvaluationRecord).where(
        EvaluationRecord.student_id == student_id
    )
    
    if start_date:
        query = query.where(EvaluationRecord.record_date >= start_date)
    if end_date:
        query = query.where(EvaluationRecord.record_date <= end_date)
    
    query = query.order_by(EvaluationRecord.record_date.desc())
    result = await db.execute(query)
    my_records = result.scalars().all()
    
    # 查询班级所有评价记录
    # 先获取班级所有学生
    all_students_result = await db.execute(
        select(Student).where(Student.class_id == class_id)
    )
    all_students = all_students_result.scalars().all()
    student_map = {s.id: s for s in all_students}
    all_student_ids = [s.id for s in all_students]
    
    # 获取班级所有评价
    class_query = select(EvaluationRecord).where(
        EvaluationRecord.student_id.in_(all_student_ids)
    )
    
    if start_date:
        class_query = class_query.where(EvaluationRecord.record_date >= start_date)
    if end_date:
        class_query = class_query.where(EvaluationRecord.record_date <= end_date)
    
    class_result = await db.execute(class_query)
    class_records = class_result.scalars().all()
    
    # 计算班级平均星级（假设value是数字）
    class_avg = None
    if class_records:
        try:
            values = [float(r.value) for r in class_records if r.value.replace('.', '').isdigit()]
            if values:
                class_avg = round(sum(values) / len(values), 2)
        except:
            pass
    
    # 构建班级记录列表（其他学生用学号代替姓名）
    class_records_anonymous = []
    for r in class_records:
        s = student_map.get(r.student_id)
        display_name = s.name if r.student_id == student_id else (s.student_number if s else "未知")
        class_records_anonymous.append({
            "id": str(r.id),
            "dimension_id": str(r.dimension_id),
            "student_id": str(r.student_id),
            "student_name": display_name,
            "record_date": str(r.record_date),
            "value": r.value,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            "is_my_child": r.student_id == student_id
        })
    
    return {
        "my_records": [EvaluationResponse.model_validate(r).model_dump() for r in my_records],
        "my_child_name": student.name,
        "my_child_id": str(student_id),
        "class_stats": {
            "avg_rating": class_avg,
            "total_records": len(class_records),
            "total_students": len(all_students)
        },
        "class_records": class_records_anonymous
    }
