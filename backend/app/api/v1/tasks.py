"""
成长印记 - 任务 API 路由
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models import LearningTask, TaskSubmission, SubmissionImage, Student, StudyGroup
from app.schemas import (
    TaskCreate, TaskResponse, TaskSubmissionCreate, 
    TaskSubmissionResponse, MessageResponse
)
from app.core.security import decode_token
from app.utils.compliance import check_compliance, validate_task_duration

router = APIRouter(prefix="/tasks", tags=["任务管理"])
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


@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发布任务（教师端）"""
    # 合规检查
    if task_data.content:
        is_compliant, violations = check_compliance(task_data.content)
        if not is_compliant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"内容包含不合规词汇：{', '.join(violations)}"
            )
    
    # 时长验证
    if task_data.suggested_duration:
        is_valid, msg = validate_task_duration(task_data.suggested_duration)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg
            )
    
    # 获取小组名称
    group_name = None
    if task_data.group_id:
        result = await db.execute(
            select(StudyGroup).where(StudyGroup.id == task_data.group_id)
        )
        group = result.scalar_one_or_none()
        if group:
            group_name = group.name
    
    task = LearningTask(
        class_id=task_data.class_id,
        subject=task_data.subject,
        group_id=task_data.group_id,
        title=task_data.title,
        content=task_data.content,
        suggested_duration=task_data.suggested_duration,
        task_date=task_data.task_date,
        is_optional=True,  # 必须为选做
        created_by=user["id"]
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        subject=task.subject,
        title=task.title,
        content=task.content,
        suggested_duration=task.suggested_duration,
        task_date=task.task_date,
        is_optional=task.is_optional,
        group_name=group_name,
        created_at=task.created_at
    )


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    class_id: Optional[str] = Query(None),
    task_date: Optional[date] = Query(None),
    student_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    query = select(LearningTask)
    
    if class_id:
        query = query.where(LearningTask.class_id == class_id)
    if task_date:
        query = query.where(LearningTask.task_date == task_date)
    
    query = query.order_by(LearningTask.task_date.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    response = []
    for task in tasks:
        group_name = None
        if task.group_id:
            g_result = await db.execute(
                select(StudyGroup).where(StudyGroup.id == task.group_id)
            )
            group = g_result.scalar_one_or_none()
            if group:
                group_name = group.name
        
        response.append(TaskResponse(
            id=task.id,
            subject=task.subject,
            title=task.title,
            content=task.content,
            suggested_duration=task.suggested_duration,
            task_date=task.task_date,
            is_optional=task.is_optional,
            group_name=group_name,
            created_at=task.created_at
        ))
    
    return response


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    result = await db.execute(
        select(LearningTask).where(LearningTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    group_name = None
    if task.group_id:
        g_result = await db.execute(
            select(StudyGroup).where(StudyGroup.id == task.group_id)
        )
        group = g_result.scalar_one_or_none()
        if group:
            group_name = group.name
    
    return TaskResponse(
        id=task.id,
        subject=task.subject,
        title=task.title,
        content=task.content,
        suggested_duration=task.suggested_duration,
        task_date=task.task_date,
        is_optional=task.is_optional,
        group_name=group_name,
        created_at=task.created_at
    )


@router.post("/{task_id}/submit", response_model=TaskSubmissionResponse)
async def submit_task(
    task_id: str,
    submission_data: TaskSubmissionCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交任务记录（家长端）"""
    # 验证任务是存在
    task_result = await db.execute(
        select(LearningTask).where(LearningTask.id == task_id)
    )
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 获取家长绑定的学生
    from app.models import ParentStudent
    ps_result = await db.execute(
        select(ParentStudent).where(ParentStudent.parent_id == user["id"])
    )
    parent_students = ps_result.scalars().all()
    
    if not parent_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您还未绑定学生"
        )
    
    # 假设每个家长只绑定一个学生（实际可扩展）
    student_id = parent_students[0].student_id
    
    # 检查是否已提交
    existing = await db.execute(
        select(TaskSubmission).where(
            and_(
                TaskSubmission.task_id == task_id,
                TaskSubmission.student_id == student_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该任务已提交"
        )
    
    submission = TaskSubmission(
        task_id=task_id,
        student_id=student_id,
        parent_id=user["id"],
        feedback=submission_data.feedback
    )
    
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    
    return TaskSubmissionResponse(
        id=submission.id,
        task_id=submission.task_id,
        student_id=submission.student_id,
        feedback=submission.feedback,
        submitted_at=submission.submitted_at,
        images=[]
    )


@router.post("/submissions/{submission_id}/images", response_model=MessageResponse)
async def upload_image(
    submission_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """上传提交图片"""
    # 验证提交记录
    result = await db.execute(
        select(TaskSubmission).where(TaskSubmission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提交记录不存在"
        )
    
    # 验证权限
    if str(submission.parent_id) != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此提交记录"
        )
    
    # 上传到MinIO
    from app.core.storage import upload_file, get_file_url
    import uuid
    
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    object_name = f"submissions/{submission_id}/{uuid.uuid4()}.{file_ext}"
    
    content = await file.read()
    import io
    await upload_file(
        object_name,
        io.BytesIO(content),
        content_type=file.content_type or "image/jpeg",
        length=len(content)
    )
    
    # 图片URL（简化处理，实际应调用图片处理服务）
    image_url = await get_file_url(object_name)
    
    # 保存记录
    image = SubmissionImage(
        submission_id=submission_id,
        original_url=object_name,
        processed_url=object_name  # 后续处理
    )
    
    db.add(image)
    await db.commit()
    
    return MessageResponse(message="图片上传成功")


@router.get("/submissions", response_model=List[TaskSubmissionResponse])
async def list_submissions(
    task_id: Optional[str] = Query(None),
    class_id: Optional[str] = Query(None),
    date: Optional[date] = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取提交列表（教师端）"""
    query = select(TaskSubmission)
    
    if task_id:
        query = query.where(TaskSubmission.task_id == task_id)
    
    query = query.order_by(TaskSubmission.submitted_at.desc())
    result = await db.execute(query)
    submissions = result.scalars().all()
    
    response = []
    for sub in submissions:
        # 获取图片
        img_result = await db.execute(
            select(SubmissionImage).where(SubmissionImage.submission_id == sub.id)
        )
        images = img_result.scalars().all()
        
        response.append(TaskSubmissionResponse(
            id=sub.id,
            task_id=sub.task_id,
            student_id=sub.student_id,
            feedback=sub.feedback,
            submitted_at=sub.submitted_at,
            images=[img.original_url for img in images]
        ))
    
    return response
