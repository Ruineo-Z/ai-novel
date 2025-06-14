from fastapi import APIRouter, HTTPException, status
from typing import List
from app.schemas.api import CreateNovelRequest, CreateNovelResponse, MakeChoiceRequest, ChapterResponse, \
    NovelStatusResponse, ErrorResponse, AvailableStylesResponse

from app.schemas.base import NovelStyle
from app.services.novel_service import novel_service
from app.core.config import settings

router = APIRouter()


@router.get("/styles", response_model=AvailableStylesResponse)
async def get_available_styles():
    """获取可用的小说风格"""
    descriptions = {
        NovelStyle.XIANXIA: "修仙小说：以修炼仙法、追求长生不老为主题的奇幻小说",
        NovelStyle.SCIFI: "科幻小说：以科学技术和未来世界为背景的小说",
        NovelStyle.URBAN: "都市小说：以现代都市生活为背景的现实题材小说",
        NovelStyle.ROMANCE: "言情小说：以爱情故事为主线的浪漫小说",
        NovelStyle.WUXIA: "武侠小说：以武功、江湖恩怨为主题的传统武侠小说"
    }

    return AvailableStylesResponse(
        styles=list(NovelStyle),
        descriptions=descriptions
    )


@router.post("/novel/create", response_model=CreateNovelResponse)
async def create_novel(request: CreateNovelRequest):
    """创建新的互动小说"""
    try:
        session_id, world_setting, first_chapter, protagonist = await novel_service.create_novel(
            novel_style=request.novel_style,
            ai_model=request.ai_model,
            use_custom_protagonist=request.use_custom_protagonist,
            protagonist_info=request.protagonist_info
        )

        return CreateNovelResponse(
            session_id=session_id,
            world_setting=world_setting,
            first_chapter=first_chapter,
            protagonist_info=protagonist
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create novel: {str(e)}"
        )


@router.post("/novel/choice", response_model=ChapterResponse)
async def make_choice(request: MakeChoiceRequest):
    """做出选择并获取下一章"""
    try:
        # 检查会话是否存在
        session = novel_service.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

        # 生成下一章
        next_chapter = await novel_service.make_choice(
            session_id=request.session_id,
            choice_id=request.choice_id,
            custom_action=request.custom_action
        )

        # 获取更新后的会话信息
        updated_session = novel_service.get_session(request.session_id)
        total_chapters = len(novel_service.get_chapters(request.session_id))

        return ChapterResponse(
            session_id=request.session_id,
            chapter=next_chapter,
            current_chapter_number=updated_session.current_chapter,
            total_chapters=total_chapters
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process choice: {str(e)}"
        )


@router.get("/novel/{session_id}/status", response_model=NovelStatusResponse)
async def get_novel_status(session_id: str):
    """获取小说状态"""
    session = novel_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    chapters = novel_service.get_chapters(session_id)
    current_chapter = novel_service.get_current_chapter(session_id)

    # 生成故事摘要
    story_summary = "\n".join(session.story_history[-3:])  # 最近3章的摘要

    return NovelStatusResponse(
        session_id=session_id,
        novel_style=session.novel_style,
        current_chapter=session.current_chapter,
        protagonist_name=session.protagonist.name if session.protagonist else None,
        world_name=novel_service.get_world_setting(session_id).world_name if novel_service.get_world_setting(
            session_id) else None,
        is_completed=current_chapter.is_ending if current_chapter else False,
        story_summary=story_summary
    )


@router.get("/novel/{session_id}/chapter/{chapter_number}")
async def get_chapter(session_id: str, chapter_number: int):
    """获取指定章节"""
    session = novel_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    chapters = novel_service.get_chapters(session_id)
    if chapter_number < 1 or chapter_number > len(chapters):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )

    chapter = chapters[chapter_number - 1]
    return {
        "session_id": session_id,
        "chapter": chapter,
        "chapter_number": chapter_number,
        "total_chapters": len(chapters)
    }


@router.get("/novel/{session_id}/chapters")
async def get_all_chapters(session_id: str):
    """获取所有章节"""
    session = novel_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    chapters = novel_service.get_chapters(session_id)
    world_setting = novel_service.get_world_setting(session_id)

    return {
        "session_id": session_id,
        "novel_style": session.novel_style,
        "protagonist": session.protagonist,
        "world_setting": world_setting,
        "chapters": chapters,
        "total_chapters": len(chapters)
    }


@router.delete("/novel/{session_id}")
async def delete_novel(session_id: str):
    """删除小说会话"""
    success = novel_service.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return {"message": "Novel session deleted successfully"}


@router.get("/novels")
async def list_novels():
    """列出所有小说会话"""
    sessions = novel_service.list_sessions()
    return {
        "sessions": sessions,
        "total": len(sessions)
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AI Interactive Novel System",
        "version": "0.1.0"
    }
