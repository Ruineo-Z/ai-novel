from fastapi import APIRouter
from app.api.v1 import users, novels, stories

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(novels.router, prefix="/novels", tags=["novels"])
api_router.include_router(stories.router, prefix="/stories", tags=["stories"])