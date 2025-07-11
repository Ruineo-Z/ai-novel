"""
AI互动小说 - 用户API端点
用户相关的REST API接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.crud.user import user as user_crud
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserList
from app.schemas.common import MessageResponse

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_in: UserCreate
):
    """创建新用户"""
    # 检查邮箱是否已存在
    if await user_crud.check_email_exists_async(db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 检查用户名是否已存在
    if await user_crud.check_username_exists_async(db, username=user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )
    
    user = await user_crud.create_user_async(db, user_data=user_in.dict())
    return UserResponse.from_orm(user)


@router.get("/", response_model=UserList)
async def list_users(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取用户列表"""
    if search:
        users = await user_crud.search_users_async(db, query=search, skip=skip, limit=limit)
    else:
        users = await user_crud.get_multi_async(db, skip=skip, limit=limit)
    
    total = await user_crud.count_async(db)
    
    return UserList(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_id: str
):
    """获取用户详情"""
    user = await user_crud.get_async(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_id: str,
    user_in: UserUpdate
):
    """更新用户信息"""
    user = await user_crud.get_async(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 如果更新邮箱，检查是否已存在
    if user_in.email and user_in.email != user.email:
        if await user_crud.check_email_exists_async(db, email=user_in.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    # 如果更新用户名，检查是否已存在
    if user_in.username and user_in.username != user.username:
        if await user_crud.check_username_exists_async(db, username=user_in.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
    
    user = await user_crud.update_async(db, db_obj=user, obj_in=user_in.dict(exclude_unset=True))
    return UserResponse.from_orm(user)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_id: str
):
    """删除用户（软删除）"""
    user = await user_crud.get_async(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await user_crud.remove_async(db, id=user_id)
    return MessageResponse(message="用户删除成功")


@router.get("/active/list", response_model=UserList)
async def list_active_users(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """获取活跃用户列表"""
    users = await user_crud.get_active_users_async(db, skip=skip, limit=limit)
    total = await user_crud.count_async(db, filters={'is_active': True})
    
    return UserList(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/premium/list", response_model=UserList)
async def list_premium_users(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """获取高级用户列表"""
    users = await user_crud.get_premium_users_async(db, skip=skip, limit=limit)
    total = await user_crud.count_async(db, filters={'is_premium': True})
    
    return UserList(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/stats/overview")
async def get_user_stats(
    *,
    db: AsyncSession = Depends(get_async_db)
):
    """获取用户统计信息"""
    stats = await user_crud.get_user_stats_async(db)
    return stats


@router.post("/{user_id}/verify-email", response_model=MessageResponse)
async def verify_user_email(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_id: str
):
    """验证用户邮箱"""
    user = await user_crud.get_async(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await user_crud.verify_email_async(db, user=user)
    return MessageResponse(message="邮箱验证成功")


@router.post("/{user_id}/activate-premium", response_model=MessageResponse)
async def activate_user_premium(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_id: str,
    days: int = Query(30, ge=1, le=365, description="高级会员天数")
):
    """激活用户高级会员"""
    user = await user_crud.get_async(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await user_crud.activate_premium_async(db, user=user, days=days)
    return MessageResponse(message=f"高级会员激活成功，有效期{days}天")


@router.post("/{user_id}/update-login", response_model=MessageResponse)
async def update_user_login_time(
    *,
    db: AsyncSession = Depends(get_async_db),
    user_id: str
):
    """更新用户最后登录时间"""
    user = await user_crud.get_async(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await user_crud.update_login_time_async(db, user=user)
    return MessageResponse(message="登录时间更新成功")
