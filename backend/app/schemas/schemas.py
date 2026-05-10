"""
成长印记 - Pydantic Schemas
"""
from datetime import datetime, date
from typing import Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


# ==================== 枚举类型 ====================

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    SCHOOL_ADMIN = "school_admin"
    TEACHER = "teacher"
    PARENT = "parent"


class EvaluationType(str, Enum):
    STAR = "star"          # 星级 1-5
    GRADE = "grade"        # 等第 A/B/C/D
    BOOLEAN = "boolean"    # 是否完成
    SCORE = "score"        # 分数
    TEXT = "text"          # 文本备注


# ==================== 用户相关 ====================

class UserBase(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    name: str = Field(..., min_length=1, max_length=50, description="姓名")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=50, description="密码")
    role: UserRole = Field(default=UserRole.TEACHER, description="角色")
    verification_code: str = Field(..., min_length=6, max_length=6, description="验证码")


class UserLogin(BaseModel):
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ==================== 学校相关 ====================

class SchoolCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="学校名称")
    province_code: Optional[str] = None
    city_code: Optional[str] = None
    district_code: Optional[str] = None
    address: Optional[str] = None


class SchoolResponse(BaseModel):
    id: UUID
    name: str
    province_code: Optional[str] = None
    city_code: Optional[str] = None
    district_code: Optional[str] = None
    address: Optional[str] = None
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SchoolSearchResponse(BaseModel):
    id: UUID
    name: str
    province_code: Optional[str] = None
    city_code: Optional[str] = None
    is_verified: bool


# ==================== 年级班级相关 ====================

class GradeCreate(BaseModel):
    name: str = Field(..., max_length=20, description="年级名称")
    year: int = Field(..., description="学年")


class GradeResponse(BaseModel):
    id: UUID
    name: str
    year: int
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClassCreate(BaseModel):
    grade_id: UUID
    name: str = Field(..., max_length=50, description="班级名称")


class ClassResponse(BaseModel):
    id: UUID
    name: str
    invite_code: str
    grade: GradeResponse
    student_count: int = 0

    class Config:
        from_attributes = True


class ClassDetailResponse(ClassResponse):
    homeroom_teacher_id: Optional[UUID] = None
    created_at: datetime


# ==================== 学生相关 ====================

class StudentImport(BaseModel):
    student_no: str = Field(..., max_length=20, description="学号")
    name: str = Field(..., max_length=50, description="姓名")


class StudentImportBatch(BaseModel):
    students: List[StudentImport]


class StudentResponse(BaseModel):
    id: UUID
    student_no: str
    name: str
    display_name: Optional[str] = None
    class_id: UUID

    class Config:
        from_attributes = True


class ParentBindRequest(BaseModel):
    invite_code: str = Field(..., description="班级邀请码")
    student_id: UUID = Field(..., description="学生ID")
    relationship: str = Field(default="家长", description="关系")


# ==================== 任务相关 ====================

class TaskCreate(BaseModel):
    class_id: UUID
    subject: str = Field(..., max_length=50, description="科目")
    group_id: Optional[UUID] = None  # NULL表示全班
    title: str = Field(..., max_length=200, description="标题")
    content: Optional[str] = None
    suggested_duration: Optional[int] = Field(None, ge=1, le=180, description="建议时长(分钟)")
    task_date: date = Field(..., description="任务日期")


class TaskResponse(BaseModel):
    id: UUID
    subject: str
    title: str
    content: Optional[str] = None
    suggested_duration: Optional[int] = None
    task_date: date
    is_optional: bool = True
    group_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskSubmissionCreate(BaseModel):
    feedback: Optional[str] = Field(None, max_length=500, description="家长反馈")


class TaskSubmissionResponse(BaseModel):
    id: UUID
    task_id: UUID
    student_id: UUID
    feedback: Optional[str] = None
    submitted_at: datetime
    images: List[str] = []

    class Config:
        from_attributes = True


class ImageUploadResponse(BaseModel):
    id: UUID
    original_url: str
    processed_url: Optional[str] = None


# ==================== 评价相关 ====================

class DimensionCreate(BaseModel):
    class_id: UUID
    name: str = Field(..., max_length=100, description="维度名称")
    subject: Optional[str] = Field(None, max_length=50, description="科目")
    type: EvaluationType = Field(..., description="评价类型")


class DimensionResponse(BaseModel):
    id: UUID
    name: str
    subject: Optional[str] = None
    type: EvaluationType
    sort_order: int
    is_active: bool

    class Config:
        from_attributes = True


class EvaluationCreate(BaseModel):
    dimension_id: UUID
    student_id: UUID
    record_date: date
    value: str = Field(..., description="评价值")


class EvaluationBatchCreate(BaseModel):
    records: List[EvaluationCreate]


class EvaluationResponse(BaseModel):
    id: UUID
    dimension_id: UUID
    student_id: UUID
    record_date: date
    value: str
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
