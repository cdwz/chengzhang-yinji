"""
成长印记 - 任务 API 路由
"""
from typing import List, Optional
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, case

from app.core.database import get_db
from app.models import LearningTask, TaskSubmission, SubmissionImage, Student, StudyGroup, Class
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


def _build_target_names(task: LearningTask, db: AsyncSession) -> str:
    """构建发布对象名称字符串（同步，需在async中调用）"""
    return ""  # 在async函数中单独处理


async def _get_task_response(task: LearningTask, db: AsyncSession) -> TaskResponse:
    """构建任务响应对象，含提交统计和发布对象名称"""
    # 获取小组名称
    group_name = None
    if task.group_id:
        g_result = await db.execute(
            select(StudyGroup).where(StudyGroup.id == task.group_id)
        )
        group = g_result.scalar_one_or_none()
        if group:
            group_name = group.name

    # 获取发布对象名称
    target_names = None
    if task.target_type == 'groups' and task.target_ids:
        g_result = await db.execute(
            select(StudyGroup).where(StudyGroup.id.in_(task.target_ids))
        )
        groups = g_result.scalars().all()
        target_names = ",".join(g.name for g in groups)
    elif task.target_type == 'students' and task.target_ids:
        s_result = await db.execute(
            select(Student).where(Student.id.in_(task.target_ids))
        )
        students = s_result.scalars().all()
        target_names = ",".join(s.name for s in students)

    # 获取提交统计
    submission_count = 0
    total_student_count = 0

    # 获取班级学生总数
    if task.target_type == 'all':
        count_result = await db.execute(
            select(func.count()).where(Student.class_id == task.class_id)
        )
        total_student_count = count_result.scalar() or 0
    elif task.target_type == 'groups' and task.target_ids:
        # 统计这些小组中的学生数
        count_result = await db.execute(
            select(func.count()).where(Student.study_group_id.in_(task.target_ids))
        )
        total_student_count = count_result.scalar() or 0
    elif task.target_type == 'students' and task.target_ids:
        total_student_count = len(task.target_ids)

    # 获取已提交数
    sub_result = await db.execute(
        select(func.count()).where(
            and_(
                TaskSubmission.task_id == task.id,
            )
        )
    )
    submission_count = sub_result.scalar() or 0

    return TaskResponse(
        id=task.id,
        subject=task.subject,
        title=task.title,
        content=task.content,
        suggested_duration=task.suggested_duration,
        task_date=task.task_date,
        task_period=getattr(task, 'task_period', 'day') or 'day',
        is_optional=task.is_optional,
        group_name=group_name,
        target_type=task.target_type or 'all',
        target_names=target_names,
        submission_count=submission_count,
        total_student_count=total_student_count,
        created_at=task.created_at
    )


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
    
    # 兼容旧字段 group_id
    target_type = task_data.target_type or 'all'
    target_ids = task_data.target_ids or []
    if task_data.group_id and not target_ids:
        target_type = 'groups'
        target_ids = [task_data.group_id]
    
    task = LearningTask(
        class_id=task_data.class_id,
        subject=task_data.subject,
        group_id=task_data.group_id,
        target_type=target_type,
        target_ids=[str(tid) for tid in target_ids] if target_ids else [],
        title=task_data.title,
        content=task_data.content,
        suggested_duration=task_data.suggested_duration,
        task_date=task_data.task_date,
        task_period=task_data.task_period or 'day',
        is_optional=True,  # 必须为选做
        created_by=user["id"]
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    return await _get_task_response(task, db)


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    class_id: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None),
    task_date: Optional[date] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    query = select(LearningTask)
    
    if class_id:
        query = query.where(LearningTask.class_id == class_id)
    if subject:
        query = query.where(LearningTask.subject == subject)
    if group_id:
        query = query.where(LearningTask.group_id == group_id)
    if task_date:
        query = query.where(LearningTask.task_date == task_date)
    if date_from:
        query = query.where(LearningTask.task_date >= date_from)
    if date_to:
        query = query.where(LearningTask.task_date <= date_to)
    
    query = query.order_by(LearningTask.task_date.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    response = []
    for task in tasks:
        response.append(await _get_task_response(task, db))
    
    return response


@router.get("/stats/detail")
async def get_task_stats_detail(
    class_id: str = Query(..., description="班级ID"),
    period: str = Query("week", description="时间范围: yesterday/week/month/all"),
    subject: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取任务统计详情（教师端）"""
    # 计算日期范围
    today = date.today()
    if period == 'yesterday':
        start_date = today - timedelta(days=1)
        end_date = today - timedelta(days=1)
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    else:  # all
        start_date = None
        end_date = None

    # 基础查询条件
    base_query = select(LearningTask).where(LearningTask.class_id == class_id)
    if start_date:
        base_query = base_query.where(LearningTask.task_date >= start_date)
    if end_date:
        base_query = base_query.where(LearningTask.task_date <= end_date)
    if subject:
        base_query = base_query.where(LearningTask.subject == subject)
    if group_id:
        base_query = base_query.where(LearningTask.group_id == group_id)

    # 获取任务列表
    result = await db.execute(base_query.order_by(LearningTask.task_date.desc()))
    tasks = result.scalars().all()

    # 总任务数
    total_tasks = len(tasks)
    task_ids = [t.id for t in tasks]

    # 本周任务数
    week_start = today - timedelta(days=today.weekday())
    week_tasks = [t for t in tasks if t.task_date >= week_start]
    week_task_count = len(week_tasks)

    # 提交统计
    total_submissions = 0
    total_students_in_class = 0
    count_result = await db.execute(
        select(func.count()).where(Student.class_id == class_id)
    )
    total_students_in_class = count_result.scalar() or 0

    if task_ids:
        sub_result = await db.execute(
            select(func.count()).where(TaskSubmission.task_id.in_(task_ids))
        )
        total_submissions = sub_result.scalar() or 0

    # 平均提交率
    total_possible = total_tasks * total_students_in_class if total_students_in_class > 0 else 1
    avg_completion_rate = round(total_submissions / total_possible * 100, 1) if total_possible > 0 else 0

    # 未提交人数（今天有任务但未提交的学生数）
    unsubmitted_count = 0

    # 科目统计
    subject_stats = []
    subjects_seen = set()
    for t in tasks:
        if t.subject not in subjects_seen:
            subjects_seen.add(t.subject)
            subject_tasks = [tt for tt in tasks if tt.subject == t.subject]
            st_ids = [tt.id for tt in subject_tasks]
            st_sub_count = 0
            if st_ids:
                st_result = await db.execute(
                    select(func.count()).where(TaskSubmission.task_id.in_(st_ids))
                )
                st_sub_count = st_result.scalar() or 0
            st_possible = len(subject_tasks) * total_students_in_class if total_students_in_class > 0 else 1
            subject_stats.append({
                "subject": t.subject,
                "count": len(subject_tasks),
                "completionRate": round(st_sub_count / st_possible * 100, 1) if st_possible > 0 else 0
            })

    # 组别统计
    group_stats = []
    g_result = await db.execute(
        select(StudyGroup).where(StudyGroup.class_id == class_id)
    )
    groups = g_result.scalars().all()
    for g in groups:
        # 该组学生数
        g_student_count = await db.execute(
            select(func.count()).where(Student.study_group_id == g.id)
        )
        g_count = g_student_count.scalar() or 0
        # 该组任务（全班任务或指定该组的任务）
        g_tasks = [t for t in tasks if t.target_type == 'all' or (t.target_ids and str(g.id) in t.target_ids) or str(t.group_id) == str(g.id)]
        g_task_ids = [t.id for t in g_tasks]
        g_sub_count = 0
        if g_task_ids:
            # 该组学生的提交数
            g_student_ids_result = await db.execute(
                select(Student.id).where(Student.study_group_id == g.id)
            )
            g_student_ids = [row[0] for row in g_student_ids_result.all()]
            if g_student_ids:
                g_sub_result = await db.execute(
                    select(func.count()).where(
                        and_(
                            TaskSubmission.task_id.in_(g_task_ids),
                            TaskSubmission.student_id.in_(g_student_ids)
                        )
                    )
                )
                g_sub_count = g_sub_result.scalar() or 0
        g_possible = len(g_tasks) * g_count if g_count > 0 else 1
        group_stats.append({
            "name": g.name,
            "count": g_count,
            "completionRate": round(g_sub_count / g_possible * 100, 1) if g_possible > 0 else 0
        })

    # 完成趋势（按天）
    trend_data = []
    if period == 'week' or period == 'yesterday':
        days = 7 if period == 'week' else 1
        for i in range(days):
            d = today - timedelta(days=days - 1 - i)
            day_tasks = [t for t in tasks if t.task_date == d]
            day_task_ids = [t.id for t in day_tasks]
            day_sub = 0
            if day_task_ids:
                ds_result = await db.execute(
                    select(func.count()).where(TaskSubmission.task_id.in_(day_task_ids))
                )
                day_sub = ds_result.scalar() or 0
            day_possible = len(day_tasks) * total_students_in_class if total_students_in_class > 0 else 1
            trend_data.append({
                "date": str(d),
                "label": d.strftime("%m/%d"),
                "count": len(day_tasks),
                "submissions": day_sub,
                "percentage": round(day_sub / day_possible * 100, 1) if day_possible > 0 else 0
            })
    elif period == 'month':
        # 按周汇总
        current = start_date
        while current <= end_date:
            week_end = min(current + timedelta(days=6), end_date)
            week_tasks_range = [t for t in tasks if current <= t.task_date <= week_end]
            wt_ids = [t.id for t in week_tasks_range]
            wt_sub = 0
            if wt_ids:
                wt_result = await db.execute(
                    select(func.count()).where(TaskSubmission.task_id.in_(wt_ids))
                )
                wt_sub = wt_result.scalar() or 0
            wt_possible = len(wt_tasks_range) * total_students_in_class if total_students_in_class > 0 else 1
            trend_data.append({
                "date": f"{current}-{week_end}",
                "label": f"{current.strftime('%m/%d')}-{week_end.strftime('%m/%d')}",
                "count": len(week_tasks_range),
                "submissions": wt_sub,
                "percentage": round(wt_sub / wt_possible * 100, 1) if wt_possible > 0 else 0
            })
            current = week_end + timedelta(days=1)
    else:
        # 全部按月汇总
        months_seen = set()
        for t in sorted(tasks, key=lambda x: x.task_date):
            m = t.task_date.strftime("%Y-%m")
            if m not in months_seen:
                months_seen.add(m)
        for m in sorted(months_seen):
            m_tasks = [t for t in tasks if t.task_date.strftime("%Y-%m") == m]
            mt_ids = [t.id for t in m_tasks]
            mt_sub = 0
            if mt_ids:
                mt_result = await db.execute(
                    select(func.count()).where(TaskSubmission.task_id.in_(mt_ids))
                )
                mt_sub = mt_result.scalar() or 0
            mt_possible = len(m_tasks) * total_students_in_class if total_students_in_class > 0 else 1
            trend_data.append({
                "date": m,
                "label": m,
                "count": len(m_tasks),
                "submissions": mt_sub,
                "percentage": round(mt_sub / mt_possible * 100, 1) if mt_possible > 0 else 0
            })

    return {
        "total": total_tasks,
        "weekCount": week_task_count,
        "avgCompletionRate": avg_completion_rate,
        "unsubmittedCount": unsubmitted_count,
        "bySubject": subject_stats,
        "byGroup": group_stats,
        "trend": trend_data
    }


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
        
        # 获取学生名称
        s_result = await db.execute(
            select(Student).where(Student.id == sub.student_id)
        )
        student = s_result.scalar_one_or_none()
        
        response.append(TaskSubmissionResponse(
            id=sub.id,
            task_id=sub.task_id,
            student_id=sub.student_id,
            student_name=student.name if student else None,
            feedback=sub.feedback,
            submitted_at=sub.submitted_at,
            images=[img.original_url for img in images]
        ))
    
    return response


@router.get("/my-submissions", response_model=List[TaskSubmissionResponse])
async def list_my_submissions(
    task_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前家长的提交记录（家长端）"""
    from app.models import ParentStudent
    
    # 获取家长绑定的学生
    ps_result = await db.execute(
        select(ParentStudent).where(ParentStudent.parent_id == user["id"])
    )
    parent_students = ps_result.scalars().all()
    
    if not parent_students:
        return []
    
    student_ids = [ps.student_id for ps in parent_students]
    
    # 查询提交记录
    query = select(TaskSubmission).where(TaskSubmission.student_id.in_(student_ids))
    
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
        
        # 获取图片完整URL
        from app.core.storage import get_file_url
        image_urls = []
        for img in images:
            url = await get_file_url(img.original_url)
            image_urls.append(url)
        
        response.append(TaskSubmissionResponse(
            id=sub.id,
            task_id=sub.task_id,
            student_id=sub.student_id,
            feedback=sub.feedback,
            submitted_at=sub.submitted_at,
            images=image_urls
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
    
    return await _get_task_response(task, db)


@router.post("/{task_id}/submit", response_model=TaskSubmissionResponse)
async def submit_task(
    task_id: str,
    submission_data: TaskSubmissionCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交任务记录（家长端）"""
    # 验证任务是否存在
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
    
    # 图片URL
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

