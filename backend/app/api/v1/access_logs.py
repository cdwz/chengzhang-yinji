"""
访问日志 API
数据访问记录与审计
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import AccessLog, User, Student

router = APIRouter(prefix="/access-logs", tags=["访问日志"])


# ============ Schemas ============

class AccessLogResponse(BaseModel):
    """访问日志响应"""
    id: UUID
    viewer_id: Optional[UUID]
    viewer_name: Optional[str]
    target_student_id: Optional[UUID]
    target_student_name: Optional[str]
    action: str
    created_at: datetime

    class Config:
        from_attributes = True


class LogStatsResponse(BaseModel):
    """日志统计响应"""
    total_views: int
    today_views: int
    top_viewers: List[dict]
    top_targets: List[dict]


class LogListResponse(BaseModel):
    """日志列表响应"""
    items: List[AccessLogResponse]
    total: int


# ============ 敏感接口配置 ============

SENSITIVE_ENDPOINTS = [
    "/api/v1/students",
    "/api/v1/evaluations",
    "/api/v1/tasks/submissions",
    "/api/v1/reports",
]


# ============ API 端点 ============

@router.get("", response_model=LogListResponse)
async def get_access_logs(
    viewer_id: Optional[UUID] = None,
    target_student_id: Optional[UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取访问日志列表（管理员）
    """
    # 权限检查
    if current_user.role not in ["super_admin", "school_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看访问日志"
        )
    
    # 构建查询
    query = select(AccessLog)
    count_query = select(func.count(AccessLog.id))
    
    if viewer_id:
        query = query.where(AccessLog.viewer_id == viewer_id)
        count_query = count_query.where(AccessLog.viewer_id == viewer_id)
    
    if target_student_id:
        query = query.where(AccessLog.target_student_id == target_student_id)
        count_query = count_query.where(AccessLog.target_student_id == target_student_id)
    
    if action:
        query = query.where(AccessLog.action == action)
        count_query = count_query.where(AccessLog.action == action)
    
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.where(AccessLog.created_at >= start)
        count_query = count_query.where(AccessLog.created_at >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        query = query.where(AccessLog.created_at < end)
        count_query = count_query.where(AccessLog.created_at < end)
    
    # 排序和分页
    query = query.order_by(AccessLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    # 执行查询
    result = await db.execute(query)
    logs = result.scalars().all()
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 构建响应
    items = []
    for log in logs:
        viewer_name = None
        if log.viewer_id:
            viewer_result = await db.execute(
                select(User).where(User.id == log.viewer_id)
            )
            viewer = viewer_result.scalar_one_or_none()
            viewer_name = viewer.name if viewer else None
        
        student_name = None
        if log.target_student_id:
            student_result = await db.execute(
                select(Student).where(Student.id == log.target_student_id)
            )
            student = student_result.scalar_one_or_none()
            student_name = student.name if student else None
        
        items.append(AccessLogResponse(
            id=log.id,
            viewer_id=log.viewer_id,
            viewer_name=viewer_name,
            target_student_id=log.target_student_id,
            target_student_name=student_name,
            action=log.action,
            created_at=log.created_at
        ))
    
    return LogListResponse(items=items, total=total)


@router.get("/stats", response_model=LogStatsResponse)
async def get_log_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取访问统计（管理员）
    """
    # 权限检查
    if current_user.role not in ["super_admin", "school_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看访问统计"
        )
    
    now = datetime.utcnow()
    start = now - timedelta(days=days)
    
    # 总访问量
    total_result = await db.execute(
        select(func.count(AccessLog.id)).where(AccessLog.created_at >= start)
    )
    total_views = total_result.scalar() or 0
    
    # 今日访问量
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(AccessLog.id)).where(AccessLog.created_at >= today_start)
    )
    today_views = today_result.scalar() or 0
    
    # 活跃查看者
    top_viewers_result = await db.execute(
        select(AccessLog.viewer_id, func.count(AccessLog.id).label("count"))
        .where(AccessLog.created_at >= start)
        .group_by(AccessLog.viewer_id)
        .order_by(func.count(AccessLog.id).desc())
        .limit(5)
    )
    
    top_viewers = []
    for row in top_viewers_result:
        viewer_id, count = row
        viewer_name = None
        if viewer_id:
            user_result = await db.execute(
                select(User).where(User.id == viewer_id)
            )
            user = user_result.scalar_one_or_none()
            viewer_name = user.name if user else str(viewer_id)
        top_viewers.append({"name": viewer_name, "count": count})
    
    # 最常被查看的学生
    top_targets_result = await db.execute(
        select(AccessLog.target_student_id, func.count(AccessLog.id).label("count"))
        .where(AccessLog.created_at >= start)
        .group_by(AccessLog.target_student_id)
        .order_by(func.count(AccessLog.id).desc())
        .limit(5)
    )
    
    top_targets = []
    for row in top_targets_result:
        student_id, count = row
        student_name = None
        if student_id:
            student_result = await db.execute(
                select(Student).where(Student.id == student_id)
            )
            student = student_result.scalar_one_or_none()
            student_name = student.name if student else str(student_id)
        top_targets.append({"name": student_name, "count": count})
    
    return LogStatsResponse(
        total_views=total_views,
        today_views=today_views,
        top_viewers=top_viewers,
        top_targets=top_targets
    )


# ============ 内部记录函数 ============

async def log_access(
    db: AsyncSession,
    viewer_id: UUID,
    target_student_id: Optional[UUID],
    action: str
):
    """
    记录访问日志（内部调用）
    """
    log = AccessLog(
        viewer_id=viewer_id,
        target_student_id=target_student_id,
        action=action
    )
    db.add(log)
    # 不立即提交，由调用者控制事务


async def log_request(
    request: Request,
    db: AsyncSession,
    current_user: User,
    target_student_id: Optional[UUID] = None
):
    """
    记录请求日志（中间件调用）
    """
    path = request.url.path
    
    # 检查是否是敏感接口
    is_sensitive = any(path.startswith(endpoint) for endpoint in SENSITIVE_ENDPOINTS)
    
    if is_sensitive:
        action = f"{request.method} {path}"
        await log_access(db, current_user.id, target_student_id, action)
