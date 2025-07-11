"""
AI互动小说 - API v1 模块
"""
from fastapi import APIRouter

from app.api.v1.endpoints import users, stories

api_router = APIRouter()

# 注册路由
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])