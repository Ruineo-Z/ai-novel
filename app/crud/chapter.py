"""
AI互动小说 - 章节CRUD操作
章节相关的数据库操作
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.chapter import Chapter, ChapterStatus
from app.models.story import Story


class CRUDChapter(CRUDBase[Chapter, Dict[str, Any], Dict[str, Any]]):
    """章节CRUD操作类"""
    
    def get_by_story(
        self,
        db: Session,
        *,
        story_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chapter]:
        """根据故事获取章节列表"""
        return db.query(Chapter).filter(
            and_(
                Chapter.story_id == story_id,
                Chapter.is_deleted == False
            )
        ).order_by(asc(Chapter.chapter_number)).offset(skip).limit(limit).all()
    
    async def get_by_story_async(
        self,
        db: AsyncSession,
        *,
        story_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chapter]:
        """异步根据故事获取章节列表"""
        stmt = select(Chapter).where(
            and_(
                Chapter.story_id == story_id,
                Chapter.is_deleted == False
            )
        ).order_by(asc(Chapter.chapter_number)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_by_number(
        self,
        db: Session,
        *,
        story_id: str,
        chapter_number: int
    ) -> Optional[Chapter]:
        """根据章节号获取章节"""
        return db.query(Chapter).filter(
            and_(
                Chapter.story_id == story_id,
                Chapter.chapter_number == chapter_number,
                Chapter.is_deleted == False
            )
        ).first()
    
    async def get_by_number_async(
        self,
        db: AsyncSession,
        *,
        story_id: str,
        chapter_number: int
    ) -> Optional[Chapter]:
        """异步根据章节号获取章节"""
        stmt = select(Chapter).where(
            and_(
                Chapter.story_id == story_id,
                Chapter.chapter_number == chapter_number,
                Chapter.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    def get_published_by_story(
        self,
        db: Session,
        *,
        story_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chapter]:
        """获取故事的已发布章节"""
        return db.query(Chapter).filter(
            and_(
                Chapter.story_id == story_id,
                Chapter.chapter_status == ChapterStatus.PUBLISHED,
                Chapter.is_deleted == False
            )
        ).order_by(asc(Chapter.chapter_number)).offset(skip).limit(limit).all()
    
    async def get_published_by_story_async(
        self,
        db: AsyncSession,
        *,
        story_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chapter]:
        """异步获取故事的已发布章节"""
        stmt = select(Chapter).where(
            and_(
                Chapter.story_id == story_id,
                Chapter.chapter_status == ChapterStatus.PUBLISHED,
                Chapter.is_deleted == False
            )
        ).order_by(asc(Chapter.chapter_number)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def create_chapter(self, db: Session, *, chapter_data: Dict[str, Any]) -> Chapter:
        """创建章节"""
        # 自动设置章节号
        if 'chapter_number' not in chapter_data:
            story_id = chapter_data['story_id']
            max_number = db.query(Chapter.chapter_number).filter(
                Chapter.story_id == story_id
            ).order_by(desc(Chapter.chapter_number)).first()
            
            chapter_data['chapter_number'] = (max_number[0] if max_number else 0) + 1
        
        # 设置默认值
        chapter_data.setdefault('chapter_status', ChapterStatus.DRAFT)
        chapter_data.setdefault('read_count', 0)
        chapter_data.setdefault('choice_count', 0)
        chapter_data.setdefault('word_count', 0)
        chapter_data.setdefault('reading_time', 0)
        
        db_chapter = Chapter(**chapter_data)
        
        # 更新字数统计
        if db_chapter.content:
            db_chapter.update_word_count()
        
        db.add(db_chapter)
        db.commit()
        db.refresh(db_chapter)
        
        # 更新故事的章节数量
        story = db.query(Story).filter(Story.id == chapter_data['story_id']).first()
        if story:
            story.increment_chapters(db_chapter.word_count)
            db.add(story)
            db.commit()
        
        return db_chapter
    
    async def create_chapter_async(self, db: AsyncSession, *, chapter_data: Dict[str, Any]) -> Chapter:
        """异步创建章节"""
        # 自动设置章节号
        if 'chapter_number' not in chapter_data:
            story_id = chapter_data['story_id']
            max_number_stmt = select(Chapter.chapter_number).where(
                Chapter.story_id == story_id
            ).order_by(desc(Chapter.chapter_number)).limit(1)
            
            max_number_result = await db.execute(max_number_stmt)
            max_number = max_number_result.scalar()
            
            chapter_data['chapter_number'] = (max_number if max_number else 0) + 1
        
        # 设置默认值
        chapter_data.setdefault('chapter_status', ChapterStatus.DRAFT)
        chapter_data.setdefault('read_count', 0)
        chapter_data.setdefault('choice_count', 0)
        chapter_data.setdefault('word_count', 0)
        chapter_data.setdefault('reading_time', 0)
        
        db_chapter = Chapter(**chapter_data)
        
        # 更新字数统计
        if db_chapter.content:
            db_chapter.update_word_count()
        
        db.add(db_chapter)
        await db.commit()
        await db.refresh(db_chapter)
        
        # 更新故事的章节数量
        story_stmt = select(Story).where(Story.id == chapter_data['story_id'])
        story_result = await db.execute(story_stmt)
        story = story_result.scalar_one_or_none()
        if story:
            story.increment_chapters(db_chapter.word_count)
            db.add(story)
            await db.commit()
        
        return db_chapter
    
    def publish_chapter(self, db: Session, *, chapter: Chapter) -> Chapter:
        """发布章节"""
        chapter.publish()
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        return chapter
    
    async def publish_chapter_async(self, db: AsyncSession, *, chapter: Chapter) -> Chapter:
        """异步发布章节"""
        chapter.publish()
        db.add(chapter)
        await db.commit()
        await db.refresh(chapter)
        return chapter
    
    def increment_read_count(self, db: Session, *, chapter: Chapter) -> Chapter:
        """增加阅读次数"""
        chapter.increment_read_count()
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        
        # 同时更新故事的阅读次数
        story = db.query(Story).filter(Story.id == chapter.story_id).first()
        if story:
            story.increment_reads()
            db.add(story)
            db.commit()
        
        return chapter
    
    async def increment_read_count_async(self, db: AsyncSession, *, chapter: Chapter) -> Chapter:
        """异步增加阅读次数"""
        chapter.increment_read_count()
        db.add(chapter)
        await db.commit()
        await db.refresh(chapter)
        
        # 同时更新故事的阅读次数
        story_stmt = select(Story).where(Story.id == chapter.story_id)
        story_result = await db.execute(story_stmt)
        story = story_result.scalar_one_or_none()
        if story:
            story.increment_reads()
            db.add(story)
            await db.commit()
        
        return chapter
    
    async def get_chapter_with_choices_async(
        self,
        db: AsyncSession,
        *,
        chapter_id: str
    ) -> Optional[Chapter]:
        """异步获取包含选择的章节"""
        stmt = select(Chapter).options(
            joinedload(Chapter.choices)
        ).where(
            and_(
                Chapter.id == chapter_id,
                Chapter.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_chapter_stats_async(self, db: AsyncSession, *, story_id: str) -> Dict[str, Any]:
        """异步获取章节统计信息"""
        total_chapters = await self.count_async(db, filters={'story_id': story_id})
        published_chapters = await self.count_async(db, filters={
            'story_id': story_id,
            'chapter_status': ChapterStatus.PUBLISHED
        })
        draft_chapters = await self.count_async(db, filters={
            'story_id': story_id,
            'chapter_status': ChapterStatus.DRAFT
        })
        
        return {
            'total_chapters': total_chapters,
            'published_chapters': published_chapters,
            'draft_chapters': draft_chapters
        }


# 创建章节CRUD实例
chapter = CRUDChapter(Chapter)
