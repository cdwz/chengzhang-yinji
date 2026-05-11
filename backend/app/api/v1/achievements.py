"""
成就系统 API
学生成长成就的触发、查询和展示
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import Achievement, Student, User, TaskSubmission, EvaluationRecord, ParentStudent

router = APIRouter(prefix="/achievements", tags=["成就系统"])


# ============ 成就类型定义 ============

ACHIEVEMENT_TYPES = {
    # 任务类成就
    "task_starter": {"name": "学习起步", "description": "完成第一个任务", "icon": "🎯", "condition": {"tasks": 1}},
    "task_explorer": {"name": "探索达人", "description": "累计完成10个任务", "icon": "🚀", "condition": {"tasks": 10}},
    "task_master": {"name": "任务大师", "description": "累计完成50个任务", "icon": "🏆", "condition": {"tasks": 50}},
    "task_legend": {"name": "传奇学者", "description": "累计完成100个任务", "icon": "👑", "condition": {"tasks": 100}},
    
    # 坚持类成就
    "week_streak": {"name": "一周坚持", "description": "连续7天完成任务", "icon": "📅", "condition": {"streak": 7}},
    "month_streak": {"name": "月度之星", "description": "连续30天完成任务", "icon": "⭐", "condition": {"streak": 30}},
    
    # 评价类成就
    "star_collector": {"name": "星光收集者", "description": "获得10个五星评价", "icon": "✨", "condition": {"five_stars": 10}},
    "all_rounder": {"name": "全面发展", "description": "在5个不同维度获得评价", "icon": "🎨", "condition": {"dimensions": 5}},
    
    # 特殊成就
    "first_annotation": {"name": "首次批注", "description": "作品获得教师批注", "icon": "📝", "condition": {"annotations": 1}},
    "example_work": {"name": "榜样作品", "description": "作品被设为典型例", "icon": "🌟", "condition": {"examples": 1}},
}


# ============ Schemas ============

class AchievementResponse(BaseModel):
    """成就响应"""
    id: UUID
    achievement_type: str
    achievement_name: str
    achievement_description: str
    achievement_icon: str
    achievement_data: Optional[Dict[str, Any]]
    earned_at: datetime

    class Config:
        from_attributes = True


class AchievementTypeResponse(BaseModel):
    """成就类型响应"""
    type: str
    name: str
    description: str
    icon: str
    earned: bool
    earned_at: Optional[datetime] = None


class AchievementStatsResponse(BaseModel):
    """成就统计响应"""
    total_achievements: int
    recent_achievements: List[AchievementResponse]
    all_types: List[AchievementTypeResponse]


# ============ API 端点 ============

@router.get("/types")
async def get_achievement_types():
    """
    获取所有成就类型
    """
    types = [
        {
            "type": key,
            "name": value["name"],
            "description": value["description"],
            "icon": value["icon"],
            "condition": value["condition"]
        }
        for key, value in ACHIEVEMENT_TYPES.items()
    ]
    return {"types": types}


@router.get("/student/{student_id}", response_model=AchievementStatsResponse)
async def get_student_achievements(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取学生成就
    家长只能查看自己孩子的，教师可查看班级学生
    """
    # 验证权限
    student_result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )
    
    # 家长权限检查
    if current_user.role == "parent":
        parent_result = await db.execute(
            select(ParentStudent).where(
                and_(
                    ParentStudent.parent_id == current_user.id,
                    ParentStudent.student_id == student_id
                )
            )
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看该学生成就"
            )
    
    # 获取已获得的成就
    result = await db.execute(
        select(Achievement).where(Achievement.student_id == student_id)
        .order_by(Achievement.earned_at.desc())
    )
    achievements = result.scalars().all()
    
    # 构建已获得成就的映射
    earned_map = {a.achievement_type: a for a in achievements}
    
    # 构建所有成就类型列表
    all_types = [
        AchievementTypeResponse(
            type=type_key,
            name=type_info["name"],
            description=type_info["description"],
            icon=type_info["icon"],
            earned=type_key in earned_map,
            earned_at=earned_map[type_key].earned_at if type_key in earned_map else None
        )
        for type_key, type_info in ACHIEVEMENT_TYPES.items()
    ]
    
    # 最近获得的成就
    recent = [
        AchievementResponse(
            id=a.id,
            achievement_type=a.achievement_type,
            achievement_name=ACHIEVEMENT_TYPES.get(a.achievement_type, {}).get("name", a.achievement_type),
            achievement_description=ACHIEVEMENT_TYPES.get(a.achievement_type, {}).get("description", ""),
            achievement_icon=ACHIEVEMENT_TYPES.get(a.achievement_type, {}).get("icon", "🏅"),
            achievement_data=a.achievement_data,
            earned_at=a.earned_at
        )
        for a in achievements[:5]  # 最近5个
    ]
    
    return AchievementStatsResponse(
        total_achievements=len(achievements),
        recent_achievements=recent,
        all_types=all_types
    )


@router.post("/check/{student_id}")
async def check_achievements(
    student_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    检查并触发成就（内部调用）
    """
    new_achievements = []
    
    # 获取已获得的成就类型
    result = await db.execute(
        select(Achievement.achievement_type).where(Achievement.student_id == student_id)
    )
    earned_types = [row[0] for row in result.all()]
    
    # 检查任务类成就
    task_count = await _get_task_count(db, student_id)
    new_achievements.extend(await _check_task_achievements(
        db, student_id, task_count, earned_types
    ))
    
    # 检查连续打卡成就
    streak = await _get_streak(db, student_id)
    new_achievements.extend(await _check_streak_achievements(
        db, student_id, streak, earned_types
    ))
    
    # 检查评价类成就
    five_stars, dimensions = await _get_evaluation_stats(db, student_id)
    new_achievements.extend(await _check_evaluation_achievements(
        db, student_id, five_stars, dimensions, earned_types
    ))
    
    return {
        "new_achievements": len(new_achievements),
        "achievements": new_achievements
    }


# ============ 内部辅助函数 ============

async def _get_task_count(db: AsyncSession, student_id: UUID) -> int:
    """获取完成的任务数量"""
    result = await db.execute(
        select(func.count(TaskSubmission.id)).where(TaskSubmission.student_id == student_id)
    )
    return result.scalar() or 0


async def _get_streak(db: AsyncSession, student_id: UUID) -> int:
    """获取连续打卡天数"""
    result = await db.execute(
        select(TaskSubmission.submitted_at)
        .where(TaskSubmission.student_id == student_id)
        .order_by(TaskSubmission.submitted_at.desc())
        .limit(60)  # 最近60天
    )
    dates = [row[0].date() for row in result.all()]
    
    if not dates:
        return 0
    
    streak = 0
    today = datetime.utcnow().date()
    
    for i, date in enumerate(dates):
        expected = today - timedelta(days=i)
        if date == expected:
            streak += 1
        else:
            break
    
    return streak


async def _get_evaluation_stats(db: AsyncSession, student_id: UUID) -> tuple[int, int]:
    """获取评价统计：五星数、维度数"""
    # 五星评价数
    five_star_result = await db.execute(
        select(func.count(EvaluationRecord.id)).where(
            and_(
                EvaluationRecord.student_id == student_id,
                EvaluationRecord.value == "5"
            )
        )
    )
    five_stars = five_star_result.scalar() or 0
    
    # 不同维度数
    dimensions_result = await db.execute(
        select(func.count(func.distinct(EvaluationRecord.dimension_id))).where(
            EvaluationRecord.student_id == student_id
        )
    )
    dimensions = dimensions_result.scalar() or 0
    
    return five_stars, dimensions


async def _check_task_achievements(
    db: AsyncSession,
    student_id: UUID,
    task_count: int,
    earned_types: List[str]
) -> List[dict]:
    """检查任务类成就"""
    new = []
    
    task_achievements = [
        ("task_starter", 1),
        ("task_explorer", 10),
        ("task_master", 50),
        ("task_legend", 100)
    ]
    
    for type_key, threshold in task_achievements:
        if type_key not in earned_types and task_count >= threshold:
            achievement = await _create_achievement(db, student_id, type_key)
            new.append(achievement)
    
    return new


async def _check_streak_achievements(
    db: AsyncSession,
    student_id: UUID,
    streak: int,
    earned_types: List[str]
) -> List[dict]:
    """检查连续打卡成就"""
    new = []
    
    streak_achievements = [
        ("week_streak", 7),
        ("month_streak", 30)
    ]
    
    for type_key, threshold in streak_achievements:
        if type_key not in earned_types and streak >= threshold:
            achievement = await _create_achievement(db, student_id, type_key, {"streak": streak})
            new.append(achievement)
    
    return new


async def _check_evaluation_achievements(
    db: AsyncSession,
    student_id: UUID,
    five_stars: int,
    dimensions: int,
    earned_types: List[str]
) -> List[dict]:
    """检查评价类成就"""
    new = []
    
    if "star_collector" not in earned_types and five_stars >= 10:
        achievement = await _create_achievement(db, student_id, "star_collector", {"five_stars": five_stars})
        new.append(achievement)
    
    if "all_rounder" not in earned_types and dimensions >= 5:
        achievement = await _create_achievement(db, student_id, "all_rounder", {"dimensions": dimensions})
        new.append(achievement)
    
    return new


async def _create_achievement(
    db: AsyncSession,
    student_id: UUID,
    achievement_type: str,
    data: Optional[dict] = None
) -> dict:
    """创建成就记录"""
    achievement = Achievement(
        student_id=student_id,
        achievement_type=achievement_type,
        achievement_data=data or {}
    )
    db.add(achievement)
    await db.commit()
    await db.refresh(achievement)
    
    return {
        "id": str(achievement.id),
        "type": achievement_type,
        "name": ACHIEVEMENT_TYPES[achievement_type]["name"],
        "earned_at": achievement.earned_at.isoformat()
    }


# ============ 特殊成就触发（供其他模块调用）============

async def grant_annotation_achievement(db: AsyncSession, student_id: UUID):
    """授予批注成就"""
    result = await db.execute(
        select(Achievement).where(
            and_(
                Achievement.student_id == student_id,
                Achievement.achievement_type == "first_annotation"
            )
        )
    )
    if not result.scalar_one_or_none():
        await _create_achievement(db, student_id, "first_annotation")


async def grant_example_achievement(db: AsyncSession, student_id: UUID):
    """授予典型例成就"""
    result = await db.execute(
        select(Achievement).where(
            and_(
                Achievement.student_id == student_id,
                Achievement.achievement_type == "example_work"
            )
        )
    )
    if not result.scalar_one_or_none():
        await _create_achievement(db, student_id, "example_work")
