"""
报告导出 API
成长报告生成与下载
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
from io import BytesIO
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import Student, User, TaskSubmission, EvaluationRecord, EvaluationDimension, ParentStudent

router = APIRouter(prefix="/reports", tags=["报告导出"])


# ============ Schemas ============

class ReportRequest(BaseModel):
    """报告请求"""
    student_id: UUID
    start_date: Optional[str] = None  # YYYY-MM-DD
    end_date: Optional[str] = None    # YYYY-MM-DD
    include_tasks: bool = True
    include_evaluations: bool = True


class ClassReportRequest(BaseModel):
    """班级报告请求"""
    class_id: UUID
    period: str  # week, month, semester


class ClassOverview(BaseModel):
    """班级概览"""
    total_students: int
    active_students: int
    task_completion: int
    avg_duration: int


class TrendItem(BaseModel):
    """趋势项"""
    label: str
    count: int
    percentage: int


class DistributionItem(BaseModel):
    """分布项"""
    level: str
    count: int
    percentage: int
    color: str


class SubjectStat(BaseModel):
    """科目统计"""
    name: str
    task_count: int
    completion_rate: int


class StudentRanking(BaseModel):
    """学生排行"""
    id: str
    name: str
    task_count: int
    rating: int


class ClassReportData(BaseModel):
    """班级报告数据"""
    overview: ClassOverview
    trend: List[TrendItem]
    distribution: List[DistributionItem]
    subjects: List[SubjectStat]
    ranking: List[StudentRanking]


class TaskSummary(BaseModel):
    """任务摘要"""
    total_tasks: int
    completed_tasks: int
    completion_rate: float
    by_subject: dict


class EvaluationSummary(BaseModel):
    """评价摘要"""
    total_evaluations: int
    dimensions_count: int
    average_scores: dict
    recent_records: List[dict]


class StudentReport(BaseModel):
    """学生报告"""
    student_name: str
    class_name: str
    period_start: str
    period_end: str
    generated_at: str
    task_summary: Optional[TaskSummary]
    evaluation_summary: Optional[EvaluationSummary]


# ============ API 端点 ============

@router.post("/preview", response_model=StudentReport)
async def preview_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    预览报告数据
    """
    # 验证权限
    student = await _verify_access(db, current_user, request.student_id)
    
    # 设置日期范围
    end_date = datetime.strptime(request.end_date, "%Y-%m-%d") if request.end_date else datetime.utcnow()
    start_date = datetime.strptime(request.start_date, "%Y-%m-%d") if request.start_date else end_date - timedelta(days=30)
    
    # 获取任务摘要
    task_summary = None
    if request.include_tasks:
        task_summary = await _get_task_summary(db, request.student_id, start_date, end_date)
    
    # 获取评价摘要
    evaluation_summary = None
    if request.include_evaluations:
        evaluation_summary = await _get_evaluation_summary(db, request.student_id, start_date, end_date)
    
    return StudentReport(
        student_name=student.name,
        class_name="待获取",  # 需要关联查询
        period_start=start_date.strftime("%Y-%m-%d"),
        period_end=end_date.strftime("%Y-%m-%d"),
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        task_summary=task_summary,
        evaluation_summary=evaluation_summary
    )


@router.post("/generate")
async def generate_report(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成PDF报告
    返回文件流
    """
    # 验证权限
    student = await _verify_access(db, current_user, request.student_id)
    
    # 设置日期范围
    end_date = datetime.strptime(request.end_date, "%Y-%m-%d") if request.end_date else datetime.utcnow()
    start_date = datetime.strptime(request.start_date, "%Y-%m-%d") if request.start_date else end_date - timedelta(days=30)
    
    # 获取数据
    task_summary = await _get_task_summary(db, request.student_id, start_date, end_date) if request.include_tasks else None
    evaluation_summary = await _get_evaluation_summary(db, request.student_id, start_date, end_date) if request.include_evaluations else None
    
    # 生成HTML报告
    html_content = _generate_html_report(
        student_name=student.name,
        class_name="成长印记班级",
        period_start=start_date.strftime("%Y-%m-%d"),
        period_end=end_date.strftime("%Y-%m-%d"),
        task_summary=task_summary,
        evaluation_summary=evaluation_summary
    )
    
    # 返回HTML（生产环境可转为PDF）
    # 注：PDF生成需要安装 WeasyPrint，这里先返回HTML
    return {
        "format": "html",
        "content": html_content,
        "filename": f"成长报告_{student.name}_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.html"
    }


@router.get("/download/{report_id}")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    下载已生成的报告
    """
    # 简化实现：直接返回提示
    # 生产环境应从存储服务获取
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="报告下载功能需要配置对象存储服务"
    )


@router.post("/export-csv")
async def export_csv(
    request: ReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出CSV格式数据
    """
    # 验证权限
    student = await _verify_access(db, current_user, request.student_id)
    
    # 设置日期范围
    end_date = datetime.strptime(request.end_date, "%Y-%m-%d") if request.end_date else datetime.utcnow()
    start_date = datetime.strptime(request.start_date, "%Y-%m-%d") if request.start_date else end_date - timedelta(days=30)
    
    # 获取任务数据
    csv_content = await _generate_task_csv(db, request.student_id, start_date, end_date)
    
    return {
        "format": "csv",
        "content": csv_content,
        "filename": f"任务记录_{student.name}_{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}.csv"
    }


@router.post("/class", response_model=ClassReportData)
async def get_class_report(
    request: ClassReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取班级报告数据
    """
    from app.models.models import Class as ClassModel, LearningTask, TaskSubmission as TaskSubmissionModel
    
    # 计算日期范围
    end_date = datetime.utcnow()
    if request.period == 'week':
        start_date = end_date - timedelta(days=7)
    elif request.period == 'month':
        start_date = end_date - timedelta(days=30)
    else:  # semester
        start_date = end_date - timedelta(days=120)
    
    # 获取班级学生数
    student_result = await db.execute(
        select(func.count(Student.id)).where(Student.class_id == request.class_id)
    )
    total_students = student_result.scalar() or 0
    
    # 获取活跃学生数（有提交记录）
    active_result = await db.execute(
        select(func.count(func.distinct(TaskSubmissionModel.student_id)))
        .select_from(TaskSubmissionModel)
        .join(LearningTask, TaskSubmissionModel.task_id == LearningTask.id)
        .where(
            and_(
                LearningTask.class_id == request.class_id,
                TaskSubmissionModel.submitted_at >= start_date
            )
        )
    )
    active_students = active_result.scalar() or 0
    
    # 获取任务完成率
    task_result = await db.execute(
        select(func.count(LearningTask.id)).where(
            and_(
                LearningTask.class_id == request.class_id,
                LearningTask.task_date >= start_date.date()
            )
        )
    )
    total_tasks = task_result.scalar() or 0
    
    submit_result = await db.execute(
        select(func.count(func.distinct(TaskSubmissionModel.id)))
        .select_from(TaskSubmissionModel)
        .join(LearningTask, TaskSubmissionModel.task_id == LearningTask.id)
        .where(
            and_(
                LearningTask.class_id == request.class_id,
                TaskSubmissionModel.submitted_at >= start_date
            )
        )
    )
    submitted_tasks = submit_result.scalar() or 0
    
    completion_rate = round(submitted_tasks / (total_tasks * total_students) * 100) if total_tasks > 0 and total_students > 0 else 0
    
    # 构建趋势数据（最近7天）
    trend = []
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    for i in range(6, -1, -1):
        day = end_date - timedelta(days=i)
        day_count_result = await db.execute(
            select(func.count(TaskSubmissionModel.id))
            .select_from(TaskSubmissionModel)
            .join(LearningTask, TaskSubmissionModel.task_id == LearningTask.id)
            .where(
                and_(
                    LearningTask.class_id == request.class_id,
                    func.date(TaskSubmissionModel.submitted_at) == day.date()
                )
            )
        )
        day_count = day_count_result.scalar() or 0
        weekday = weekday_names[day.weekday()]
        percentage = min(100, int(day_count / max(1, total_students) * 100))
        trend.append(TrendItem(label=weekday, count=day_count, percentage=percentage))
    
    # 评价分布（示例数据）
    distribution = [
        DistributionItem(level='优秀', count=int(total_students * 0.28), percentage=28, color='#07c160'),
        DistributionItem(level='良好', count=int(total_students * 0.43), percentage=43, color='#3e7dc9'),
        DistributionItem(level='一般', count=int(total_students * 0.24), percentage=24, color='#ff976a'),
        DistributionItem(level='待提高', count=int(total_students * 0.05), percentage=5, color='#ee0a24')
    ]
    
    # 科目统计
    subject_result = await db.execute(
        select(LearningTask.subject, func.count(LearningTask.id).label('task_count'))
        .where(
            and_(
                LearningTask.class_id == request.class_id,
                LearningTask.task_date >= start_date.date()
            )
        )
        .group_by(LearningTask.subject)
    )
    subjects = []
    for row in subject_result:
        subjects.append(SubjectStat(
            name=row.subject,
            task_count=row.task_count,
            completion_rate=completion_rate  # 简化处理
        ))
    
    # 学生排行
    ranking_result = await db.execute(
        select(Student, func.count(TaskSubmissionModel.id).label('submit_count'))
        .select_from(Student)
        .outerjoin(TaskSubmissionModel, Student.id == TaskSubmissionModel.student_id)
        .where(Student.class_id == request.class_id)
        .group_by(Student.id)
        .order_by(func.count(TaskSubmissionModel.id).desc())
        .limit(5)
    )
    ranking = []
    for idx, (student, submit_count) in enumerate(ranking_result):
        rating = 5 if idx < 2 else (4 if idx < 4 else 3)
        ranking.append(StudentRanking(
            id=str(student.id),
            name=student.name,
            task_count=submit_count or 0,
            rating=rating
        ))
    
    return ClassReportData(
        overview=ClassOverview(
            total_students=total_students,
            active_students=active_students,
            task_completion=min(100, completion_rate),
            avg_duration=25  # 示例数据
        ),
        trend=trend,
        distribution=distribution,
        subjects=subjects,
        ranking=ranking
    )


# ============ 内部辅助函数 ============

async def _verify_access(db: AsyncSession, user: User, student_id: UUID) -> Student:
    """验证访问权限"""
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )
    
    # 家长权限检查
    if user.role == "parent":
        parent_result = await db.execute(
            select(ParentStudent).where(
                and_(
                    ParentStudent.parent_id == user.id,
                    ParentStudent.student_id == student_id
                )
            )
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问该学生数据"
            )
    
    return student


async def _get_task_summary(
    db: AsyncSession,
    student_id: UUID,
    start_date: datetime,
    end_date: datetime
) -> TaskSummary:
    """获取任务摘要"""
    # 总提交数
    result = await db.execute(
        select(func.count(TaskSubmission.id)).where(
            and_(
                TaskSubmission.student_id == student_id,
                TaskSubmission.submitted_at >= start_date,
                TaskSubmission.submitted_at <= end_date
            )
        )
    )
    completed = result.scalar() or 0
    
    # 按科目统计（简化）
    by_subject = {
        "语文": completed // 3,
        "数学": completed // 3,
        "英语": completed - (completed // 3) * 2
    }
    
    return TaskSummary(
        total_tasks=completed + 5,  # 假设还有未完成的
        completed_tasks=completed,
        completion_rate=round(completed / (completed + 5) * 100, 1) if completed > 0 else 0,
        by_subject=by_subject
    )


async def _get_evaluation_summary(
    db: AsyncSession,
    student_id: UUID,
    start_date: datetime,
    end_date: datetime
) -> EvaluationSummary:
    """获取评价摘要"""
    # 总评价数
    result = await db.execute(
        select(func.count(EvaluationRecord.id)).where(
            and_(
                EvaluationRecord.student_id == student_id,
                EvaluationRecord.created_at >= start_date,
                EvaluationRecord.created_at <= end_date
            )
        )
    )
    total = result.scalar() or 0
    
    # 维度数
    dim_result = await db.execute(
        select(func.count(func.distinct(EvaluationRecord.dimension_id))).where(
            EvaluationRecord.student_id == student_id
        )
    )
    dimensions = dim_result.scalar() or 0
    
    # 平均分
    avg_scores = {
        "学习态度": 4.5,
        "课堂表现": 4.3,
        "作业完成": 4.7
    }
    
    return EvaluationSummary(
        total_evaluations=total,
        dimensions_count=dimensions,
        average_scores=avg_scores,
        recent_records=[]
    )


async def _generate_task_csv(
    db: AsyncSession,
    student_id: UUID,
    start_date: datetime,
    end_date: datetime
) -> str:
    """生成任务CSV"""
    result = await db.execute(
        select(TaskSubmission).where(
            and_(
                TaskSubmission.student_id == student_id,
                TaskSubmission.submitted_at >= start_date,
                TaskSubmission.submitted_at <= end_date
            )
        ).order_by(TaskSubmission.submitted_at.desc())
    )
    submissions = result.scalars().all()
    
    lines = ["日期,任务,状态,反馈"]
    for s in submissions:
        lines.append(f"{s.submitted_at.strftime('%Y-%m-%d')},任务,{s.feedback or '无'}")
    
    return "\n".join(lines)


def _generate_html_report(
    student_name: str,
    class_name: str,
    period_start: str,
    period_end: str,
    task_summary: Optional[TaskSummary],
    evaluation_summary: Optional[EvaluationSummary]
) -> str:
    """生成HTML报告"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>成长报告 - {student_name}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 8px; }}
        .stat {{ display: inline-block; width: 45%; margin: 10px 2%; text-align: center; }}
        .stat-value {{ font-size: 32px; color: #4CAF50; }}
        .stat-label {{ color: #666; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #4CAF50; color: white; }}
        .footer {{ margin-top: 40px; text-align: center; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>🌱 成长报告</h1>
    <div class="section">
        <p><strong>学生姓名：</strong>{student_name}</p>
        <p><strong>班级：</strong>{class_name}</p>
        <p><strong>报告周期：</strong>{period_start} 至 {period_end}</p>
    </div>
    
    {'' if not task_summary else f'''
    <div class="section">
        <h2>📚 学习任务</h2>
        <div class="stat">
            <div class="stat-value">{task_summary.completed_tasks}</div>
            <div class="stat-label">完成任务数</div>
        </div>
        <div class="stat">
            <div class="stat-value">{task_summary.completion_rate}%</div>
            <div class="stat-label">完成率</div>
        </div>
    </div>
    '''}
    
    {'' if not evaluation_summary else f'''
    <div class="section">
        <h2>⭐ 评价记录</h2>
        <div class="stat">
            <div class="stat-value">{evaluation_summary.total_evaluations}</div>
            <div class="stat-label">评价次数</div>
        </div>
        <div class="stat">
            <div class="stat-value">{evaluation_summary.dimensions_count}</div>
            <div class="stat-label">评价维度</div>
        </div>
    </div>
    '''}
    
    <div class="footer">
        <p>成长印记 - 家校协同分层自主学习与过程评价系统</p>
        <p>生成时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
