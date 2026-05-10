"""
成长印记 - Schemas 初始化
"""
from app.schemas.schemas import (
    UserRole, EvaluationType,
    UserBase, UserCreate, UserLogin, UserResponse,
    TokenResponse, RefreshTokenRequest,
    SchoolCreate, SchoolResponse, SchoolSearchResponse,
    GradeCreate, GradeResponse,
    ClassCreate, ClassResponse, ClassDetailResponse,
    StudentImport, StudentImportBatch, StudentResponse, ParentBindRequest,
    TaskCreate, TaskResponse, TaskSubmissionCreate, TaskSubmissionResponse, ImageUploadResponse,
    DimensionCreate, DimensionResponse, EvaluationCreate, EvaluationBatchCreate, EvaluationResponse,
    MessageResponse, ErrorResponse, PaginatedResponse
)

__all__ = [
    "UserRole", "EvaluationType",
    "UserBase", "UserCreate", "UserLogin", "UserResponse",
    "TokenResponse", "RefreshTokenRequest",
    "SchoolCreate", "SchoolResponse", "SchoolSearchResponse",
    "GradeCreate", "GradeResponse",
    "ClassCreate", "ClassResponse", "ClassDetailResponse",
    "StudentImport", "StudentImportBatch", "StudentResponse", "ParentBindRequest",
    "TaskCreate", "TaskResponse", "TaskSubmissionCreate", "TaskSubmissionResponse", "ImageUploadResponse",
    "DimensionCreate", "DimensionResponse", "EvaluationCreate", "EvaluationBatchCreate", "EvaluationResponse",
    "MessageResponse", "ErrorResponse", "PaginatedResponse"
]
