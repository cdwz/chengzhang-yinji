"""
教师批注 API
支持在学生提交的图片上进行圈画批注
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import TeacherAnnotation, SubmissionImage, User, TaskSubmission, Student, Class

router = APIRouter(prefix="/annotations", tags=["批注管理"])


# ============ Schemas ============

class AnnotationData(BaseModel):
    """批注数据结构（Fabric.js 格式）"""
    version: str = "5.3.0"
    objects: List[dict] = []


class CreateAnnotationRequest(BaseModel):
    """创建批注请求"""
    image_id: UUID
    annotation_data: AnnotationData


class UpdateAnnotationRequest(BaseModel):
    """更新批注请求"""
    annotation_data: AnnotationData


class AnnotationResponse(BaseModel):
    """批注响应"""
    id: UUID
    image_id: UUID
    teacher_id: UUID
    teacher_name: str
    annotation_data: dict
    is_viewed: bool
    is_example: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ImageAnnotationsResponse(BaseModel):
    """图片及其批注响应"""
    image_id: UUID
    image_url: str
    annotations: List[AnnotationResponse]


# ============ API 端点 ============

@router.post("", response_model=AnnotationResponse)
async def create_annotation(
    request: CreateAnnotationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建批注
    教师在图片上添加批注
    """
    # 验证图片存在
    result = await db.execute(
        select(SubmissionImage).where(SubmissionImage.id == request.image_id)
    )
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    # 验证教师权限（需要是该班级的任课教师）
    submission_result = await db.execute(
        select(TaskSubmission)
        .where(TaskSubmission.id == image.submission_id)
    )
    submission = submission_result.scalar_one()
    
    # 创建批注
    annotation = TeacherAnnotation(
        image_id=request.image_id,
        teacher_id=current_user.id,
        annotation_data=request.annotation_data.model_dump(),
        is_viewed=False,
        is_example=False
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)
    
    return AnnotationResponse(
        id=annotation.id,
        image_id=annotation.image_id,
        teacher_id=annotation.teacher_id,
        teacher_name=current_user.name,
        annotation_data=annotation.annotation_data,
        is_viewed=annotation.is_viewed,
        is_example=annotation.is_example,
        created_at=annotation.created_at,
        updated_at=annotation.updated_at
    )


@router.get("/image/{image_id}", response_model=ImageAnnotationsResponse)
async def get_image_annotations(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取图片的所有批注
    """
    # 验证图片存在
    result = await db.execute(
        select(SubmissionImage).where(SubmissionImage.id == image_id)
    )
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="图片不存在"
        )
    
    # 获取所有批注
    annotations_result = await db.execute(
        select(TeacherAnnotation, User)
        .join(User, TeacherAnnotation.teacher_id == User.id)
        .where(TeacherAnnotation.image_id == image_id)
        .order_by(TeacherAnnotation.created_at.desc())
    )
    rows = annotations_result.all()
    
    annotations = [
        AnnotationResponse(
            id=annotation.id,
            image_id=annotation.image_id,
            teacher_id=annotation.teacher_id,
            teacher_name=teacher.name,
            annotation_data=annotation.annotation_data,
            is_viewed=annotation.is_viewed,
            is_example=annotation.is_example,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at
        )
        for annotation, teacher in rows
    ]
    
    return ImageAnnotationsResponse(
        image_id=image_id,
        image_url=image.original_url,
        annotations=annotations
    )


@router.put("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: UUID,
    request: UpdateAnnotationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新批注
    只有创建者可以修改
    """
    result = await db.execute(
        select(TeacherAnnotation).where(TeacherAnnotation.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批注不存在"
        )
    
    if annotation.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改他人批注"
        )
    
    annotation.annotation_data = request.annotation_data.model_dump()
    annotation.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(annotation)
    
    return AnnotationResponse(
        id=annotation.id,
        image_id=annotation.image_id,
        teacher_id=annotation.teacher_id,
        teacher_name=current_user.name,
        annotation_data=annotation.annotation_data,
        is_viewed=annotation.is_viewed,
        is_example=annotation.is_example,
        created_at=annotation.created_at,
        updated_at=annotation.updated_at
    )


@router.delete("/{annotation_id}")
async def delete_annotation(
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除批注
    只有创建者可以删除
    """
    result = await db.execute(
        select(TeacherAnnotation).where(TeacherAnnotation.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批注不存在"
        )
    
    if annotation.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除他人批注"
        )
    
    await db.delete(annotation)
    await db.commit()
    
    return {"message": "批注已删除"}


@router.post("/{annotation_id}/set-example")
async def set_as_example(
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    设置/取消为典型例
    典型例会展示给全班学生和家长
    """
    result = await db.execute(
        select(TeacherAnnotation).where(TeacherAnnotation.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批注不存在"
        )
    
    if annotation.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作"
        )
    
    annotation.is_example = not annotation.is_example
    await db.commit()
    
    return {
        "message": "已设为典型例" if annotation.is_example else "已取消典型例",
        "is_example": annotation.is_example
    }


@router.post("/{annotation_id}/mark-viewed")
async def mark_viewed(
    annotation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    标记批注已查看（家长端）
    """
    result = await db.execute(
        select(TeacherAnnotation).where(TeacherAnnotation.id == annotation_id)
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="批注不存在"
        )
    
    annotation.is_viewed = True
    await db.commit()
    
    return {"message": "已标记为已查看"}


@router.get("/examples/{class_id}")
async def get_class_examples(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取班级的典型例批注
    教师和家长均可查看
    """
    # 查询该班级所有典型例批注
    result = await db.execute(
        select(TeacherAnnotation, SubmissionImage, TaskSubmission, User)
        .select_from(TeacherAnnotation)
        .join(SubmissionImage, TeacherAnnotation.image_id == SubmissionImage.id)
        .join(TaskSubmission, SubmissionImage.submission_id == TaskSubmission.id)
        .join(User, TeacherAnnotation.teacher_id == User.id)
        .join(Student, TaskSubmission.student_id == Student.id)
        .where(
            and_(
                TeacherAnnotation.is_example == True,
                Student.class_id == class_id
            )
        )
        .order_by(TeacherAnnotation.created_at.desc())
        .limit(20)
    )
    rows = result.all()
    
    examples = [
        {
            "annotation_id": annotation.id,
            "image_url": image.original_url,
            "annotation_data": annotation.annotation_data,
            "teacher_name": teacher.name,
            "created_at": annotation.created_at.isoformat()
        }
        for annotation, image, submission, teacher in rows
    ]
    
    return {"examples": examples}
