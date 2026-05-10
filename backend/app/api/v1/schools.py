"""
成长印记 - 学校 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.models import School, Region, User
from app.schemas import (
    SchoolCreate, SchoolResponse, SchoolSearchResponse,
    GradeCreate, GradeResponse, ClassCreate, ClassResponse,
    MessageResponse
)
from app.core.security import decode_token, generate_invite_code

router = APIRouter(prefix="/schools", tags=["学校管理"])
security = HTTPBearer()


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


@router.get("/regions", response_model=List[dict])
async def get_regions(
    parent_code: Optional[str] = Query(None, description="父级区划代码"),
    db: AsyncSession = Depends(get_db)
):
    """获取行政区划列表"""
    query = select(Region)
    if parent_code:
        query = query.where(Region.parent_code == parent_code)
    else:
        query = query.where(Region.parent_code.is_(None))
    
    query = query.order_by(Region.code)
    result = await db.execute(query)
    regions = result.scalars().all()
    
    return [
        {
            "code": r.code,
            "name": r.name,
            "level": r.level
        }
        for r in regions
    ]


@router.get("/search", response_model=List[SchoolSearchResponse])
async def search_schools(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    province_code: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """搜索学校"""
    query = select(School).where(
        or_(
            School.name.ilike(f"%{keyword}%"),
            School.address.ilike(f"%{keyword}%")
        )
    )
    
    if province_code:
        query = query.where(School.province_code == province_code)
    
    query = query.limit(limit)
    result = await db.execute(query)
    schools = result.scalars().all()
    
    return [SchoolSearchResponse.model_validate(s) for s in schools]


@router.post("", response_model=SchoolResponse)
async def create_school(
    school_data: SchoolCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建学校"""
    school = School(
        name=school_data.name,
        province_code=school_data.province_code,
        city_code=school_data.city_code,
        district_code=school_data.district_code,
        address=school_data.address,
        created_by=user_id,
        is_verified=False
    )
    
    db.add(school)
    await db.commit()
    await db.refresh(school)
    
    return SchoolResponse.model_validate(school)


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取学校详情"""
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学校不存在"
        )
    
    return SchoolResponse.model_validate(school)


@router.post("/{school_id}/grades", response_model=GradeResponse)
async def create_grade(
    school_id: str,
    grade_data: GradeCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建年级"""
    from app.models import Grade
    
    grade = Grade(
        school_id=school_id,
        name=grade_data.name,
        year=grade_data.year
    )
    
    db.add(grade)
    await db.commit()
    await db.refresh(grade)
    
    return GradeResponse.model_validate(grade)


@router.get("/{school_id}/grades", response_model=List[GradeResponse])
async def get_grades(
    school_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取年级列表"""
    from app.models import Grade
    
    result = await db.execute(
        select(Grade)
        .where(Grade.school_id == school_id)
        .order_by(Grade.sort_order, Grade.year.desc())
    )
    grades = result.scalars().all()
    
    return [GradeResponse.model_validate(g) for g in grades]


@router.post("/classes", response_model=ClassResponse)
async def create_class(
    class_data: ClassCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建班级"""
    from app.models import Class as ClassModel
    
    # 生成唯一邀请码
    invite_code = generate_invite_code()
    
    # 检查邀请码是否重复
    while True:
        result = await db.execute(
            select(ClassModel).where(ClassModel.invite_code == invite_code)
        )
        if not result.scalar_one_or_none():
            break
        invite_code = generate_invite_code()
    
    new_class = ClassModel(
        grade_id=class_data.grade_id,
        name=class_data.name,
        invite_code=invite_code
    )
    
    db.add(new_class)
    await db.commit()
    await db.refresh(new_class)
    
    return ClassResponse(
        id=new_class.id,
        name=new_class.name,
        invite_code=new_class.invite_code,
        grade=GradeResponse.model_validate(new_class.grade),
        student_count=0
    )


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取班级详情"""
    from app.models import Class as ClassModel, Student
    
    result = await db.execute(
        select(ClassModel).where(ClassModel.id == class_id)
    )
    cls = result.scalar_one_or_none()
    
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )
    
    # 统计学生数
    student_count = await db.execute(
        select(Student).where(Student.class_id == class_id)
    )
    count = len(student_count.scalars().all())
    
    return ClassResponse(
        id=cls.id,
        name=cls.name,
        invite_code=cls.invite_code,
        grade=GradeResponse.model_validate(cls.grade),
        student_count=count
    )
