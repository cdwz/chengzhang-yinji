"""
成长印记 - 学校 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload

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


# ==================== 静态路由（放在动态路由前面）====================

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


# ==================== 班级管理（静态路径）====================

@router.post("/classes", response_model=ClassResponse)
async def create_class(
    class_data: ClassCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建班级"""
    from app.models import Class as ClassModel, EvaluationDimension

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
        invite_code=invite_code,
        subjects=["语文", "数学", "英语"]  # 预置三科
    )

    db.add(new_class)
    await db.flush()  # 获取class_id

    # 自动生成六列默认评价维度（按需求规格）
    default_dimensions = [
        {"name": "数学课堂定时", "subject": "数学", "type": "star", "sort_order": 1, "config": {}},
        {"name": "数学作业改错", "subject": "数学", "type": "grade", "sort_order": 2, "config": {}},
        {"name": "数学定时改错", "subject": "数学", "type": "ab_score", "sort_order": 3, "config": {"total": 150, "a_score": 100, "b_score": 50}},
        {"name": "语文作业与课堂情况", "subject": "语文", "type": "grade", "sort_order": 4, "config": {}},
        {"name": "英语作业改错", "subject": "英语", "type": "grade", "sort_order": 5, "config": {}},
        {"name": "英语课堂情况", "subject": "英语", "type": "grade", "sort_order": 6, "config": {}},
    ]

    for dim_data in default_dimensions:
        dimension = EvaluationDimension(
            class_id=new_class.id,
            name=dim_data["name"],
            subject=dim_data.get("subject"),
            type=dim_data["type"],
            config=dim_data.get("config", {}),
            sort_order=dim_data["sort_order"],
        )
        db.add(dimension)

    await db.commit()
    await db.refresh(new_class)
    
    # 加载年级关系
    result = await db.execute(
        select(ClassModel)
        .options(selectinload(ClassModel.grade))
        .where(ClassModel.id == new_class.id)
    )
    new_class = result.scalar_one()

    return ClassResponse(
        id=new_class.id,
        name=new_class.name,
        invite_code=new_class.invite_code,
        grade=GradeResponse.model_validate(new_class.grade),
        student_count=0,
        subjects=new_class.subjects or ["语文", "数学", "英语"]
    )


@router.get("/classes", response_model=List[ClassResponse])
async def list_classes(
    grade_id: Optional[str] = Query(None, description="年级ID"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取班级列表"""
    from app.models import Class as ClassModel, Student
    
    query = select(ClassModel).options(
        selectinload(ClassModel.grade)
    )
    
    if grade_id:
        query = query.where(ClassModel.grade_id == grade_id)
    
    query = query.order_by(ClassModel.created_at.desc())
    result = await db.execute(query)
    classes = result.scalars().all()
    
    response = []
    for cls in classes:
        # 统计学生数
        count_result = await db.execute(
            select(func.count()).where(Student.class_id == cls.id)
        )
        count = count_result.scalar() or 0
        
        response.append(ClassResponse(
            id=cls.id,
            name=cls.name,
            invite_code=cls.invite_code,
            grade=GradeResponse.model_validate(cls.grade),
            student_count=count,
            subjects=cls.subjects or ["语文", "数学", "英语"]
        ))
    
    return response


@router.get("/classes/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取班级详情"""
    from app.models import Class as ClassModel, Student

    result = await db.execute(
        select(ClassModel)
        .options(selectinload(ClassModel.grade))
        .where(ClassModel.id == class_id)
    )
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )

    # 统计学生数
    count_result = await db.execute(
        select(func.count()).where(Student.class_id == class_id)
    )
    count = count_result.scalar() or 0

    return ClassResponse(
        id=cls.id,
        name=cls.name,
        invite_code=cls.invite_code,
        grade=GradeResponse.model_validate(cls.grade),
        student_count=count,
        subjects=cls.subjects or ["语文", "数学", "英语"]
    )


@router.put("/classes/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db)
):
    """修改班级名称"""
    from app.models import Class as ClassModel, Student
    from pydantic import BaseModel as PydanticModel

    class ClassUpdate(PydanticModel):
        name: str | None = None
        grade_id: str | None = None
        subjects: List[str] | None = None

    update_data = ClassUpdate(**body)

    result = await db.execute(
        select(ClassModel).where(ClassModel.id == class_id)
    )
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )

    if update_data.name is not None:
        cls.name = update_data.name
    if update_data.grade_id is not None:
        cls.grade_id = update_data.grade_id
    if update_data.subjects is not None:
        cls.subjects = update_data.subjects
    await db.commit()
    await db.refresh(cls)

    # 重新加载关联
    result = await db.execute(
        select(ClassModel)
        .options(selectinload(ClassModel.grade))
        .where(ClassModel.id == class_id)
    )
    cls = result.scalar_one()

    count_result = await db.execute(
        select(func.count()).where(Student.class_id == class_id)
    )
    count = count_result.scalar() or 0

    return ClassResponse(
        id=cls.id,
        name=cls.name,
        invite_code=cls.invite_code,
        grade=GradeResponse.model_validate(cls.grade),
        student_count=count,
        subjects=cls.subjects or ["语文", "数学", "英语"]
    )


@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除班级（级联删除关联数据）"""
    from app.models import (
        Class as ClassModel, Student, TaskSubmission, LearningTask,
        EvaluationRecord, EvaluationDimension, StudyGroup, TeachingAssignment,
        TeacherAnnotation, SubmissionImage
    )

    result = await db.execute(
        select(ClassModel).where(ClassModel.id == class_id)
    )
    cls = result.scalar_one_or_none()

    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )

    # 查找该班级所有学生
    student_result = await db.execute(
        select(Student.id).where(Student.class_id == class_id)
    )
    student_ids = [row[0] for row in student_result.all()]

    # 查找该班级所有任务
    task_result = await db.execute(
        select(LearningTask.id).where(LearningTask.class_id == class_id)
    )
    task_ids = [row[0] for row in task_result.all()]

    # 按依赖顺序删除关联数据
    # 1. 批注（关联提交图片）
    if task_ids:
        sub_result = await db.execute(
            select(TaskSubmission.id).where(TaskSubmission.task_id.in_(task_ids))
        )
        submission_ids = [row[0] for row in sub_result.all()]

        if submission_ids:
            # 删除批注
            img_result = await db.execute(
                select(SubmissionImage.id).where(SubmissionImage.submission_id.in_(submission_ids))
            )
            image_ids = [row[0] for row in img_result.all()]
            if image_ids:
                await db.execute(
                    TeacherAnnotation.__table__.delete().where(
                        TeacherAnnotation.image_id.in_(image_ids)
                    )
                )
                await db.execute(
                    SubmissionImage.__table__.delete().where(
                        SubmissionImage.id.in_(image_ids)
                    )
                )
            await db.execute(
                TaskSubmission.__table__.delete().where(
                    TaskSubmission.task_id.in_(task_ids)
                )
            )

    # 2. 学习任务
    if task_ids:
        await db.execute(
            LearningTask.__table__.delete().where(LearningTask.class_id == class_id)
        )

    # 3. 评价记录 & 维度 & 成就 & 访问日志
    if student_ids:
        await db.execute(
            EvaluationRecord.__table__.delete().where(
                EvaluationRecord.student_id.in_(student_ids)
            )
        )
        # 删除成就记录
        from app.models import Achievement
        await db.execute(
            Achievement.__table__.delete().where(
                Achievement.student_id.in_(student_ids)
            )
        )
        # 删除访问日志
        from app.models import AccessLog
        await db.execute(
            AccessLog.__table__.delete().where(
                AccessLog.target_student_id.in_(student_ids)
            )
        )
    await db.execute(
        EvaluationDimension.__table__.delete().where(EvaluationDimension.class_id == class_id)
    )

    # 4. 删除学生-小组关联，清除 study_group_id 引用，再删除学习小组
    if student_ids:
        await db.execute(
            Student.__table__.update()
            .where(Student.id.in_(student_ids))
            .values(study_group_id=None)
        )
    # 删除 student_groups 关联表（该班级的学生关联的小组记录）
    from app.models import StudentGroup
    if student_ids:
        await db.execute(
            StudentGroup.__table__.delete().where(
                StudentGroup.student_id.in_(student_ids)
            )
        )
    await db.execute(
        StudyGroup.__table__.delete().where(StudyGroup.class_id == class_id)
    )

    # 5. 教学分配
    await db.execute(
        TeachingAssignment.__table__.delete().where(
            TeachingAssignment.class_id == class_id
        )
    )

    # 6. 家长-学生关系 & 学生
    if student_ids:
        from app.models import ParentStudent
        await db.execute(
            ParentStudent.__table__.delete().where(
                ParentStudent.student_id.in_(student_ids)
            )
        )
        await db.execute(
            Student.__table__.delete().where(Student.class_id == class_id)
        )

    # 7. 删除班级
    await db.delete(cls)
    await db.commit()

    return {"message": "班级及关联数据已删除"}


# ==================== 动态路由（放在静态路由后面）====================

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
