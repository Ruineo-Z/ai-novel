from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.deps import get_current_active_user, get_optional_user
from app.schemas.novel import (
    NovelCreate, NovelResponse, NovelUpdate, NovelSummary,
    ChapterResponse
)
from app.services.novel_service import NovelService
from app.services.llm_service import LLMService
from app.models.user import User

router = APIRouter()
novel_service = NovelService()
llm_service = LLMService()

@router.post("/novels/", response_model=NovelResponse, status_code=status.HTTP_201_CREATED)
async def create_novel(
    novel_data: NovelCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建新小说并生成大纲"""
    try:
        # 生成小说大纲
        outline = await llm_service.generate_outline(
            genre=novel_data.genre,
            world_setting=novel_data.world_setting,
            protagonist_info=novel_data.protagonist_info.dict()
        )
        
        # 保存到数据库
        novel = await novel_service.create_novel(
            db=db,
            novel_data=novel_data,
            outline=outline,
            owner_id=current_user.id
        )
        
        return novel
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create novel: {str(e)}")

@router.get("/novels/", response_model=List[NovelSummary])
async def get_user_novels(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的小说列表"""
    novels = await novel_service.get_user_novels(db, current_user.id, skip, limit)
    return novels

@router.get("/novels/{novel_id}", response_model=NovelResponse)
async def get_novel(
    novel_id: int,
    include_chapters: bool = Query(False),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """获取小说详情"""
    novel = await novel_service.get_novel(db, novel_id, include_chapters)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # 检查权限（如果是私有小说）
    if novel.owner_id != (current_user.id if current_user else None):
        # 这里可以添加公开小说的逻辑
        if not current_user or novel.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return novel

@router.put("/novels/{novel_id}", response_model=NovelResponse)
async def update_novel(
    novel_id: int,
    novel_update: NovelUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新小说信息"""
    novel = await novel_service.get_novel(db, novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    if novel.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_novel = await novel_service.update_novel(db, novel_id, novel_update)
    return updated_novel

@router.delete("/novels/{novel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_novel(
    novel_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除小说"""
    novel = await novel_service.get_novel(db, novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    if novel.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await novel_service.delete_novel(db, novel_id)
    return None

@router.get("/novels/{novel_id}/chapters/", response_model=List[ChapterResponse])
async def get_novel_chapters(
    novel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """获取小说章节列表"""
    novel = await novel_service.get_novel(db, novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # 检查权限
    if novel.owner_id != (current_user.id if current_user else None):
        if not current_user or novel.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    chapters = await novel_service.get_chapters(db, novel_id, skip, limit)
    return chapters

@router.get("/novels/{novel_id}/chapters/{chapter_number}", response_model=ChapterResponse)
async def get_chapter(
    novel_id: int,
    chapter_number: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """获取特定章节"""
    novel = await novel_service.get_novel(db, novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    # 检查权限
    if novel.owner_id != (current_user.id if current_user else None):
        if not current_user or novel.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    chapter = await novel_service.get_chapter_by_number(db, novel_id, chapter_number)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    return chapter