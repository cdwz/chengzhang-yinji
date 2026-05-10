"""
成长印记 - 学生管理 API 路由

注意：路由顺序很重要！
- 静态路由（如 /groups, /import）必须在动态路由（如 /{student_id}）之前定义
- 否则 FastAPI 会先匹配动态路由导致错误
"""
import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Student, Class as ClassModel, Grade, School, User, ParentStudent, StudyGroup, StudentGroup
from app.schemas import (
    StudentCreate, StudentResponse, StudentListResponse,
    StudyGroupCreate, StudyGroupResponse,
    MessageResponse
)
from app.core.security import decode_token

router = APIRouter(prefix="/students", tags=["学生管理"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的访问令牌"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return user


# ==================== 学生列表和创建 ====================

@router.get("", response_model=StudentListResponse)
async def list_students(
    class_id: Optional[str] = Query(None, description="班级ID"),
    grade_id: Optional[str] = Query(None, description="年级ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取学生列表"""
    query = select(Student).options(selectinload(Student.class_))
    
    if class_id:
        query = query.where(Student.class_id == class_id)
    elif grade_id:
        # 通过班级关联年级
        subquery = select(ClassModel.id).where(ClassModel.grade_id == grade_id)
        query = query.where(Student.class_id.in_(subquery))
    
    if keyword:
        query = query.where(Student.name.ilike(f"%{keyword}%"))
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    # 分页
    query = query.order_by(Student.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    return StudentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[StudentResponse.model_validate(s) for s in students]
    )


@router.post("", response_model=StudentResponse)
async def create_student(
    student_data: StudentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建学生"""
    # 检查班级是否存在
    result = await db.execute(select(ClassModel).where(ClassModel.id == student_data.class_id))
    cls = result.scalar_one_or_none()
    
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )
    
    student = Student(
        class_id=student_data.class_id,
        name=student_data.name,
        gender=student_data.gender,
        student_number=student_data.student_number,
        birth_date=student_data.birth_date
    )
    
    db.add(student)
    await db.commit()
    await db.refresh(student)
    
    return StudentResponse.model_validate(student)


@router.post("/import", response_model=MessageResponse)
async def import_students(
    class_id: str = Form(..., description="班级ID"),
    file: UploadFile = File(..., description="Excel/CSV文件"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """批量导入学生"""
    import openpyxl
    
    # 检查班级是否存在
    result = await db.execute(select(ClassModel).where(ClassModel.id == class_id))
    cls = result.scalar_one_or_none()
    
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )
    
    # 读取文件内容
    content = await file.read()
    
    students_created = 0
    students_updated = 0
    errors = []
    
    try:
        if file.filename and file.filename.endswith('.csv'):
            # CSV格式
            text_content = content.decode('utf-8-sig')
            reader = csv.DictReader(io.StringIO(text_content))
            rows = list(reader)
        else:
            # Excel格式
            wb = openpyxl.load_workbook(io.BytesIO(content))
            ws = wb.active
            headers = [cell.value for cell in ws[1] if cell.value]
            rows = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if any(row):
                    rows.append(dict(zip(headers, row)))
        
        for idx, row in enumerate(rows, start=2):
            try:
                name = row.get('姓名') or row.get('学生姓名') or row.get('name')
                student_number = row.get('学号') or row.get('学生学号') or row.get('student_number')
                gender = row.get('性别') or row.get('gender')
                
                if not name:
                    errors.append(f"第{idx}行: 缺少姓名")
                    continue
                
                # 性别处理
                gender_value = 'male'
                if gender:
                    if gender in ['女', 'F', 'female', 'Female']:
                        gender_value = 'female'
                    elif gender in ['男', 'M', 'male', 'Male']:
                        gender_value = 'male'
                
                # 检查学号是否已存在
                existing = None
                if student_number:
                    result = await db.execute(
                        select(Student).where(
                            Student.class_id == class_id,
                            Student.student_number == student_number
                        )
                    )
                    existing = result.scalar_one_or_none()
                
                if existing:
                    existing.name = name
                    existing.gender = gender_value
                    students_updated += 1
                else:
                    student = Student(
                        class_id=class_id,
                        name=name,
                        gender=gender_value,
                        student_number=student_number
                    )
                    db.add(student)
                    students_created += 1
                    
            except Exception as e:
                errors.append(f"第{idx}行: {str(e)}")
        
        await db.commit()
        
        return MessageResponse(
            message=f"导入完成：新增 {students_created} 人，更新 {students_updated} 人" + 
                   (f"，错误 {len(errors)} 条" if errors else "")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件解析失败: {str(e)}"
        )


# ==================== 学习小组管理（静态路由，必须在 /{student_id} 之前）====================

@router.get("/groups", response_model=List[StudyGroupResponse])
async def list_study_groups(
    class_id: str = Query(..., description="班级ID"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取班级的学习小组列表"""
    result = await db.execute(
        select(StudyGroup)
        .options(selectinload(StudyGroup.students))
        .where(StudyGroup.class_id == class_id)
        .order_by(StudyGroup.sort_order)
    )
    groups = result.scalars().all()
    
    return [
        StudyGroupResponse(
            id=g.id,
            name=g.name,
            class_id=g.class_id,
            sort_order=g.sort_order,
            students=[StudentResponse.model_validate(s) for s in g.students]
        )
        for g in groups
    ]


@router.post("/groups", response_model=StudyGroupResponse)
async def create_study_group(
    group_data: StudyGroupCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建学习小组"""
    # 检查班级是否存在
    result = await db.execute(select(ClassModel).where(ClassModel.id == group_data.class_id))
    cls = result.scalar_one_or_none()
    
    if not cls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="班级不存在"
        )
    
    # 获取最大排序号
    max_order_result = await db.execute(
        select(func.max(StudyGroup.sort_order)).where(StudyGroup.class_id == group_data.class_id)
    )
    max_order = max_order_result.scalar() or 0
    
    group = StudyGroup(
        class_id=group_data.class_id,
        name=group_data.name,
        sort_order=max_order + 1
    )
    
    db.add(group)
    await db.commit()
    await db.refresh(group)
    
    return StudyGroupResponse(
        id=group.id,
        name=group.name,
        class_id=group.class_id,
        sort_order=group.sort_order,
        students=[]
    )


@router.post("/groups/{group_id}/members", response_model=MessageResponse)
async def add_student_to_group(
    group_id: str,
    student_id: str = Form(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """将学生添加到学习小组"""
    # 检查小组是否存在
    result = await db.execute(select(StudyGroup).where(StudyGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学习小组不存在"
        )
    
    # 检查学生是否存在
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )
    
    # 更新学生的小组
    student.study_group_id = group_id
    await db.commit()
    
    return MessageResponse(message="添加成功")


@router.delete("/groups/{group_id}/members/{student_id}", response_model=MessageResponse)
async def remove_student_from_group(
    group_id: str,
    student_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """将学生从学习小组移除"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )
    
    student.study_group_id = None
    await db.commit()
    
    return MessageResponse(message="移除成功")


@router.delete("/groups/{group_id}", response_model=MessageResponse)
async def delete_study_group(
    group_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除学习小组"""
    result = await db.execute(select(StudyGroup).where(StudyGroup.id == group_id))
    group = result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学习小组不存在"
        )
    
    # 先将组内学生移出
    await db.execute(
        Student.__table__.update()
        .where(Student.study_group_id == group_id)
        .values(study_group_id=None)
    )
    
    await db.delete(group)
    await db.commit()
    
    return MessageResponse(message="删除成功")


# ==================== 学生详情和删除（动态路由，必须在静态路由之后）====================

@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取学生详情"""
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.class_))
        .where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )
    
    return StudentResponse.model_validate(student)


@router.delete("/{student_id}", response_model=MessageResponse)
async def delete_student(
    student_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除学生"""
    result = await db.execute(select(Student).where(Student.id == student_id))
    student = result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )
    
    await db.delete(student)
    await db.commit()
    
    return MessageResponse(message="删除成功")
