from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.schemas.story import (
    GenerationRequest, GenerationResponse, 
    StorySessionCreate, StorySessionResponse, StorySessionUpdate
)
from app.schemas.novel import ChapterResponse
from app.services.story_service import StoryService
from app.services.novel_service import NovelService
from app.models.user import User

router = APIRouter()
story_service = StoryService()
novel_service = NovelService()

@router.post("/stories/generate", response_model=GenerationResponse)
async def generate_chapter(
    request: GenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """生成新章节"""
    try:
        # 检查小说权限
        novel = await novel_service.get_novel(db, request.novel_id)
        if not novel:
            raise HTTPException(status_code=404, detail="Novel not found")
        
        if novel.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # 生成章节
        result = await story_service.generate_chapter(
            db=db,
            novel_id=request.novel_id,
            user_choice=request.user_choice,
            model_preference=request.model_preference,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate chapter: {str(e)}")

@router.post("/stories/sessions", response_model=StorySessionResponse, status_code=status.HTTP_201_CREATED)
async def create_story_session(
    session_data: StorySessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建故事会话"""
    # 检查小说权限
    novel = await novel_service.get_novel(db, session_data.novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    
    if novel.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    session = await story_service.create_session(
        db=db,
        user_id=current_user.id,
        session_data=session_data
    )
    
    return session

@router.get("/stories/sessions", response_model=List[StorySessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的故事会话列表"""
    sessions = await story_service.get_user_sessions(db, current_user.id)
    return sessions

@router.get("/stories/sessions/{session_id}", response_model=StorySessionResponse)
async def get_story_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取特定故事会话"""
    session = await story_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session

@router.put("/stories/sessions/{session_id}", response_model=StorySessionResponse)
async def update_story_session(
    session_id: int,
    session_update: StorySessionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新故事会话"""
    session = await story_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_session = await story_service.update_session(db, session_id, session_update)
    return updated_session

@router.delete("/stories/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除故事会话"""
    session = await story_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    await story_service.delete_session(db, session_id)
    return None

@router.post("/stories/continue/{session_id}", response_model=GenerationResponse)
async def continue_story(
    session_id: int,
    user_choice: str,
    model_preference: str = "openai",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """继续故事（基于会话）"""
    session = await story_service.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        result = await story_service.continue_story(
            db=db,
            session_id=session_id,
            user_choice=user_choice,
            model_preference=model_preference
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to continue story: {str(e)}")

@router.get("/stories/regenerate/{chapter_id}", response_model=GenerationResponse)
async def regenerate_chapter(
    chapter_id: int,
    model_preference: str = "openai",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """重新生成章节"""
    try:
        result = await story_service.regenerate_chapter(
            db=db,
            chapter_id=chapter_id,
            user_id=current_user.id,
            model_preference=model_preference
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate chapter: {str(e)}")

@router.get("/stories/quality/{chapter_id}")
async def evaluate_chapter_quality(
    chapter_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """评估章节质量"""
    try:
        quality_score = await story_service.evaluate_chapter_quality(db, chapter_id, current_user.id)
        return {"chapter_id": chapter_id, "quality_score": quality_score}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate quality: {str(e)}")