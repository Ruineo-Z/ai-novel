"""
AI互动小说 - 故事API端点
故事相关的REST API接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.crud.story import story as story_crud
from app.crud.user import user as user_crud
from app.schemas.story import (
    StoryCreate, StoryUpdate, StoryResponse, StoryDetailResponse, 
    StoryList, StoryStats, StorySearchRequest, StoryTheme, StoryStatus
)
from app.schemas.common import MessageResponse

router = APIRouter()


@router.post("/", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    *,
    db: AsyncSession = Depends(get_async_db),
    story_in: StoryCreate
):
    """创建新故事"""
    # 验证作者是否存在
    author = await user_crud.get_async(db, id=story_in.author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作者不存在"
        )
    
    story = await story_crud.create_story_async(db, story_data=story_in.dict())
    return StoryResponse.from_orm(story)


@router.get("/", response_model=StoryList)
async def list_stories(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    theme: Optional[StoryTheme] = Query(None, description="故事主题"),
    status: Optional[StoryStatus] = Query(None, description="故事状态"),
    author_id: Optional[str] = Query(None, description="作者ID"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取故事列表"""
    if search:
        stories = await story_crud.search_stories_async(db, query=search, skip=skip, limit=limit)
    elif theme:
        stories = await story_crud.get_by_theme_async(db, theme=theme, skip=skip, limit=limit)
    elif author_id:
        stories = await story_crud.get_by_author_async(db, author_id=author_id, skip=skip, limit=limit)
    else:
        if status:
            filters = {'story_status': status}
        else:
            filters = None
        stories = await story_crud.get_multi_async(db, skip=skip, limit=limit, filters=filters)
    
    total = await story_crud.count_async(db)
    
    return StoryList(
        stories=[StoryResponse.from_orm(story) for story in stories],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/published", response_model=StoryList)
async def list_published_stories(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """获取已发布的故事列表"""
    stories = await story_crud.get_published_async(db, skip=skip, limit=limit)
    total = await story_crud.count_async(db, filters={'story_status': StoryStatus.PUBLISHED})
    
    return StoryList(
        stories=[StoryResponse.from_orm(story) for story in stories],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/popular", response_model=StoryList)
async def list_popular_stories(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """获取热门故事列表"""
    stories = await story_crud.get_popular_async(db, skip=skip, limit=limit)
    total = await story_crud.count_async(db)
    
    return StoryList(
        stories=[StoryResponse.from_orm(story) for story in stories],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/trending", response_model=StoryList)
async def list_trending_stories(
    *,
    db: AsyncSession = Depends(get_async_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    days: int = Query(7, ge=1, le=30, description="趋势天数")
):
    """获取趋势故事列表"""
    stories = await story_crud.get_trending_stories_async(db, days=days, skip=skip, limit=limit)
    total = len(stories)  # 趋势故事数量有限
    
    return StoryList(
        stories=[StoryResponse.from_orm(story) for story in stories],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{story_id}", response_model=StoryDetailResponse)
async def get_story(
    *,
    db: AsyncSession = Depends(get_async_db),
    story_id: str
):
    """获取故事详情"""
    story = await story_crud.get_async(db, id=story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="故事不存在"
        )
    
    # 获取作者信息
    author = await user_crud.get_async(db, id=story.author_id)
    
    # 构建详情响应
    story_dict = StoryResponse.from_orm(story).dict()
    if author:
        story_dict['author_username'] = author.username
        story_dict['author_nickname'] = author.nickname
    
    return StoryDetailResponse(**story_dict)


@router.put("/{story_id}", response_model=StoryResponse)
async def update_story(
    *,
    db: AsyncSession = Depends(get_async_db),
    story_id: str,
    story_in: StoryUpdate
):
    """更新故事信息"""
    story = await story_crud.get_async(db, id=story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="故事不存在"
        )
    
    story = await story_crud.update_async(db, db_obj=story, obj_in=story_in.dict(exclude_unset=True))
    return StoryResponse.from_orm(story)


@router.delete("/{story_id}", response_model=MessageResponse)
async def delete_story(
    *,
    db: AsyncSession = Depends(get_async_db),
    story_id: str
):
    """删除故事（软删除）"""
    story = await story_crud.get_async(db, id=story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="故事不存在"
        )
    
    await story_crud.remove_async(db, id=story_id)
    return MessageResponse(message="故事删除成功")


@router.post("/{story_id}/publish", response_model=MessageResponse)
async def publish_story(
    *,
    db: AsyncSession = Depends(get_async_db),
    story_id: str
):
    """发布故事"""
    story = await story_crud.get_async(db, id=story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="故事不存在"
        )
    
    if story.story_status != StoryStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有草稿状态的故事可以发布"
        )
    
    await story_crud.publish_story_async(db, story=story)
    return MessageResponse(message="故事发布成功")


@router.post("/{story_id}/complete", response_model=MessageResponse)
async def complete_story(
    *,
    db: AsyncSession = Depends(get_async_db),
    story_id: str
):
    """完结故事"""
    story = await story_crud.get_async(db, id=story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="故事不存在"
        )
    
    if story.story_status != StoryStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有已发布的故事可以完结"
        )
    
    await story_crud.complete_story_async(db, story=story)
    return MessageResponse(message="故事完结成功")


@router.get("/stats/overview")
async def get_story_stats(
    *,
    db: AsyncSession = Depends(get_async_db)
):
    """获取故事统计信息"""
    stats = await story_crud.get_story_stats_async(db)
    return stats


@router.get("/author/{author_id}", response_model=StoryList)
async def get_author_stories(
    *,
    db: AsyncSession = Depends(get_async_db),
    author_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """获取作者的故事列表"""
    # 验证作者是否存在
    author = await user_crud.get_async(db, id=author_id)
    if not author:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作者不存在"
        )
    
    stories = await story_crud.get_by_author_async(db, author_id=author_id, skip=skip, limit=limit)
    total = await story_crud.count_async(db, filters={'author_id': author_id})
    
    return StoryList(
        stories=[StoryResponse.from_orm(story) for story in stories],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/theme/{theme}", response_model=StoryList)
async def get_stories_by_theme(
    *,
    db: AsyncSession = Depends(get_async_db),
    theme: StoryTheme,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """根据主题获取故事列表"""
    stories = await story_crud.get_by_theme_async(db, theme=theme, skip=skip, limit=limit)
    total = await story_crud.count_async(db, filters={'theme': theme})
    
    return StoryList(
        stories=[StoryResponse.from_orm(story) for story in stories],
        total=total,
        skip=skip,
        limit=limit
    )
