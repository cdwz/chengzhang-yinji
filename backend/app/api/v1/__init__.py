"""
成长印记 - API 路由初始化
"""
from fastapi import APIRouter
from app.api.v1 import auth, schools, students, tasks, evaluations, dimensions, annotations, messages, achievements, reports, access_logs, images

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(schools.router)
api_router.include_router(students.router)
api_router.include_router(tasks.router)
api_router.include_router(evaluations.router)
api_router.include_router(dimensions.router)
api_router.include_router(annotations.router)
api_router.include_router(messages.router)
api_router.include_router(achievements.router)
api_router.include_router(reports.router)
api_router.include_router(access_logs.router)
api_router.include_router(images.router)
