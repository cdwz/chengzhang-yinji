"""
成长印记 - 模型初始化
"""
from app.models.models import (
    User, Region, School, SchoolAdmin, Grade, Class, Student,
    ParentStudent, StudyGroup, StudentGroup, TeachingAssignment,
    LearningTask, TaskAttachment, TaskSubmission, SubmissionImage,
    TeacherAnnotation, EvaluationDimension, EvaluationRecord,
    Achievement, Message, AccessLog
)

__all__ = [
    "User", "Region", "School", "SchoolAdmin", "Grade", "Class", "Student",
    "ParentStudent", "StudyGroup", "StudentGroup", "TeachingAssignment",
    "LearningTask", "TaskAttachment", "TaskSubmission", "SubmissionImage",
    "TeacherAnnotation", "EvaluationDimension", "EvaluationRecord",
    "Achievement", "Message", "AccessLog"
]
