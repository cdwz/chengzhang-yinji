"""
成长印记 - API 路由初始化
"""
from fastapi import APIRouter
from app.api.v1 import auth, schools, students, tasks, evaluations

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(schools.router)
api_router.include_router(students.router)
api_router.include_router(tasks.router)
api_router.include_router(evaluations.router)
