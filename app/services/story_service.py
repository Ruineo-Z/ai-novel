from sqlalchemy.orm import Session
from app.models.story import StorySession, GenerationLog
from app.models.novel import Novel, Chapter
from app.schemas.story import (
    StorySessionCreate, StorySessionUpdate, GenerationResponse
)
from app.services.llm_service import LLMService
from app.services.novel_service import NovelService
from typing import List, Optional
import time

class StoryService:
    def __init__(self):
        self.llm_service = LLMService()
        self.novel_service = NovelService()
    
    async def generate_chapter(self, db: Session, novel_id: int,
                             user_choice: Optional[str] = None,
                             model_preference: str = "openai",
                             temperature: float = 0.7,
                             max_tokens: int = 1500) -> GenerationResponse:
        """生成新章节"""
        # 获取小说信息
        novel = await self.novel_service.get_novel(db, novel_id)
        if not novel:
            raise ValueError("Novel not found")
        
        # 获取最近的章节作为上下文
        recent_chapters = await self.novel_service.get_recent_chapters(db, novel_id, 3)
        previous_chapters = [chapter.content for chapter in reversed(recent_chapters)]
        
        # 构建小说上下文
        novel_context = f"""
        小说标题：{novel.title}
        类型：{novel.genre}
        世界观：{novel.world_setting}
        主人公：{novel.protagonist_info}
        大纲：{novel.outline}
        """
        
        start_time = time.time()
        
        # 调用LLM生成章节
        generation_result = await self.llm_service.generate_chapter(
            novel_context=novel_context,
            previous_chapters=previous_chapters,
            user_choice=user_choice,
            temperature=temperature,
            max_tokens=max_tokens,
            model_name=model_preference
        )
        
        generation_time = time.time() - start_time
        
        # 保存章节到数据库
        chapter = await self.novel_service.create_chapter(
            db=db,
            novel_id=novel_id,
            content=generation_result['content'],
            choices=generation_result['choices'],
            user_choice=user_choice
        )
        
        # 评估内容质量
        quality_score = await self.llm_service.evaluate_content_quality(
            generation_result['content']
        )
        
        # 记录生成日志
        await self._log_generation(
            db=db,
            chapter_id=chapter.id,
            model_used=model_preference,
            quality_score=quality_score,
            generation_time=generation_time,
            token_usage={}  # 这里可以添加token使用统计
        )
        
        return GenerationResponse(
            chapter_id=chapter.id,
            content=generation_result['content'],
            choices=generation_result['choices'],
            word_count=chapter.word_count,
            generation_time=generation_time,
            model_used=model_preference,
            quality_score=quality_score
        )
    
    async def create_session(self, db: Session, user_id: int,
                           session_data: StorySessionCreate) -> StorySession:
        """创建故事会话"""
        db_session = StorySession(
            user_id=user_id,
            novel_id=session_data.novel_id,
            current_chapter=session_data.current_chapter,
            session_data=session_data.session_data or {}
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        return db_session
    
    async def get_session(self, db: Session, session_id: int) -> Optional[StorySession]:
        """获取故事会话"""
        return db.query(StorySession).filter(StorySession.id == session_id).first()
    
    async def get_user_sessions(self, db: Session, user_id: int) -> List[StorySession]:
        """获取用户的所有会话"""
        return (
            db.query(StorySession)
            .filter(StorySession.user_id == user_id)
            .order_by(StorySession.updated_at.desc())
            .all()
        )
    
    async def update_session(self, db: Session, session_id: int,
                           session_update: StorySessionUpdate) -> Optional[StorySession]:
        """更新故事会话"""
        session = await self.get_session(db, session_id)
        if not session:
            return None
        
        update_data = session_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(session, field, value)
        
        db.commit()
        db.refresh(session)
        
        return session
    
    async def delete_session(self, db: Session, session_id: int) -> bool:
        """删除故事会话"""
        session = await self.get_session(db, session_id)
        if not session:
            return False
        
        db.delete(session)
        db.commit()
        
        return True
    
    async def continue_story(self, db: Session, session_id: int,
                           user_choice: str, model_preference: str = "openai") -> GenerationResponse:
        """基于会话继续故事"""
        session = await self.get_session(db, session_id)
        if not session:
            raise ValueError("Session not found")
        
        # 生成新章节
        result = await self.generate_chapter(
            db=db,
            novel_id=session.novel_id,
            user_choice=user_choice,
            model_preference=model_preference
        )
        
        # 更新会话状态
        session.current_chapter += 1
        if not session.session_data:
            session.session_data = {}
        
        # 记录用户选择历史
        if 'choice_history' not in session.session_data:
            session.session_data['choice_history'] = []
        
        session.session_data['choice_history'].append({
            'chapter': session.current_chapter - 1,
            'choice': user_choice,
            'timestamp': time.time()
        })
        
        db.commit()
        
        return result
    
    async def regenerate_chapter(self, db: Session, chapter_id: int,
                               user_id: int, model_preference: str = "openai") -> GenerationResponse:
        """重新生成章节"""
        chapter = await self.novel_service.get_chapter_by_id(db, chapter_id)
        if not chapter:
            raise ValueError("Chapter not found")
        
        # 检查权限（通过小说所有者）
        novel = await self.novel_service.get_novel(db, chapter.novel_id)
        if not novel or novel.owner_id != user_id:
            raise ValueError("Access denied")
        
        # 获取上下文（排除当前章节）
        all_chapters = await self.novel_service.get_chapters(db, chapter.novel_id)
        previous_chapters = [
            ch.content for ch in all_chapters 
            if ch.chapter_number < chapter.chapter_number
        ][-3:]  # 最近3章
        
        # 构建小说上下文
        novel_context = f"""
        小说标题：{novel.title}
        类型：{novel.genre}
        世界观：{novel.world_setting}
        主人公：{novel.protagonist_info}
        大纲：{novel.outline}
        """
        
        # 重新生成
        generation_result = await self.llm_service.generate_chapter(
            novel_context=novel_context,
            previous_chapters=previous_chapters,
            user_choice=chapter.user_choice,
            model_name=model_preference
        )
        
        # 更新章节
        await self.novel_service.update_chapter(
            db=db,
            chapter_id=chapter_id,
            content=generation_result['content'],
            choices=generation_result['choices']
        )
        
        # 评估质量
        quality_score = await self.llm_service.evaluate_content_quality(
            generation_result['content']
        )
        
        # 记录生成日志
        await self._log_generation(
            db=db,
            chapter_id=chapter_id,
            model_used=model_preference,
            quality_score=quality_score,
            generation_time=generation_result.get('generation_time', 0),
            token_usage={}
        )
        
        return GenerationResponse(
            chapter_id=chapter_id,
            content=generation_result['content'],
            choices=generation_result['choices'],
            word_count=len(generation_result['content'].replace(' ', '').replace('\n', '')),
            generation_time=generation_result.get('generation_time', 0),
            model_used=model_preference,
            quality_score=quality_score
        )
    
    async def evaluate_chapter_quality(self, db: Session, chapter_id: int, user_id: int) -> float:
        """评估章节质量"""
        chapter = await self.novel_service.get_chapter_by_id(db, chapter_id)
        if not chapter:
            raise ValueError("Chapter not found")
        
        # 检查权限
        novel = await self.novel_service.get_novel(db, chapter.novel_id)
        if not novel or novel.owner_id != user_id:
            raise ValueError("Access denied")
        
        return await self.llm_service.evaluate_content_quality(chapter.content)
    
    async def _log_generation(self, db: Session, chapter_id: int,
                            model_used: str, quality_score: float,
                            generation_time: float, token_usage: dict):
        """记录生成日志"""
        log = GenerationLog(
            chapter_id=chapter_id,
            model_used=model_used,
            quality_score=quality_score,
            generation_time=generation_time,
            token_usage=token_usage
        )
        
        db.add(log)
        db.commit()
    
    async def get_generation_stats(self, db: Session, user_id: int) -> dict:
        """获取用户的生成统计"""
        # 这里可以添加统计逻辑，比如：
        # - 总生成章节数
        # - 平均质量分数
        # - 各模型使用情况
        # - 生成时间统计等
        
        from sqlalchemy import func
        
        stats = (
            db.query(
                func.count(GenerationLog.id).label('total_generations'),
                func.avg(GenerationLog.quality_score).label('avg_quality'),
                func.avg(GenerationLog.generation_time).label('avg_time')
            )
            .join(Chapter, GenerationLog.chapter_id == Chapter.id)
            .join(Novel, Chapter.novel_id == Novel.id)
            .filter(Novel.owner_id == user_id)
            .first()
        )
        
        return {
            'total_generations': stats.total_generations or 0,
            'average_quality_score': float(stats.avg_quality or 0),
            'average_generation_time': float(stats.avg_time or 0)
        }