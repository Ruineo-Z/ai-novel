"""
AI互动小说 - 故事CRUD操作
故事相关的数据库操作
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.story import Story, StoryTheme, StoryStatus
from app.models.user import User


class CRUDStory(CRUDBase[Story, Dict[str, Any], Dict[str, Any]]):
    """故事CRUD操作类"""
    
    def get_by_author(
        self,
        db: Session,
        *,
        author_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """根据作者获取故事列表"""
        return db.query(Story).filter(
            and_(
                Story.author_id == author_id,
                Story.is_deleted == False
            )
        ).order_by(desc(Story.created_at)).offset(skip).limit(limit).all()
    
    async def get_by_author_async(
        self,
        db: AsyncSession,
        *,
        author_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """异步根据作者获取故事列表"""
        stmt = select(Story).where(
            and_(
                Story.author_id == author_id,
                Story.is_deleted == False
            )
        ).order_by(desc(Story.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_by_theme(
        self,
        db: Session,
        *,
        theme: StoryTheme,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """根据主题获取故事列表"""
        return db.query(Story).filter(
            and_(
                Story.theme == theme,
                Story.story_status == StoryStatus.PUBLISHED,
                Story.is_deleted == False
            )
        ).order_by(desc(Story.total_readers)).offset(skip).limit(limit).all()
    
    async def get_by_theme_async(
        self,
        db: AsyncSession,
        *,
        theme: StoryTheme,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """异步根据主题获取故事列表"""
        stmt = select(Story).where(
            and_(
                Story.theme == theme,
                Story.story_status == StoryStatus.PUBLISHED,
                Story.is_deleted == False
            )
        ).order_by(desc(Story.total_readers)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_published(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """获取已发布的故事"""
        return db.query(Story).filter(
            and_(
                Story.story_status.in_([StoryStatus.PUBLISHED, StoryStatus.COMPLETED]),
                Story.is_deleted == False
            )
        ).order_by(desc(Story.published_at)).offset(skip).limit(limit).all()
    
    async def get_published_async(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """异步获取已发布的故事"""
        stmt = select(Story).where(
            and_(
                Story.story_status.in_([StoryStatus.PUBLISHED, StoryStatus.COMPLETED]),
                Story.is_deleted == False
            )
        ).order_by(desc(Story.published_at)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_popular(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """获取热门故事"""
        return db.query(Story).filter(
            and_(
                Story.story_status.in_([StoryStatus.PUBLISHED, StoryStatus.COMPLETED]),
                Story.is_deleted == False
            )
        ).order_by(desc(Story.total_readers), desc(Story.average_rating)).offset(skip).limit(limit).all()
    
    async def get_popular_async(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """异步获取热门故事"""
        stmt = select(Story).where(
            and_(
                Story.story_status.in_([StoryStatus.PUBLISHED, StoryStatus.COMPLETED]),
                Story.is_deleted == False
            )
        ).order_by(desc(Story.total_readers), desc(Story.average_rating)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def create_story(self, db: Session, *, story_data: Dict[str, Any]) -> Story:
        """创建故事"""
        # 设置默认值
        story_data.setdefault('story_status', StoryStatus.DRAFT)
        story_data.setdefault('total_chapters', 0)
        story_data.setdefault('total_words', 0)
        story_data.setdefault('total_readers', 0)
        story_data.setdefault('total_reads', 0)
        story_data.setdefault('average_rating', 0)
        
        db_story = Story(**story_data)
        db.add(db_story)
        db.commit()
        db.refresh(db_story)
        
        # 更新作者的故事创建数量
        author = db.query(User).filter(User.id == story_data['author_id']).first()
        if author:
            author.increment_stories_created()
            db.add(author)
            db.commit()
        
        return db_story
    
    async def create_story_async(self, db: AsyncSession, *, story_data: Dict[str, Any]) -> Story:
        """异步创建故事"""
        # 设置默认值
        story_data.setdefault('story_status', StoryStatus.DRAFT)
        story_data.setdefault('total_chapters', 0)
        story_data.setdefault('total_words', 0)
        story_data.setdefault('total_readers', 0)
        story_data.setdefault('total_reads', 0)
        story_data.setdefault('average_rating', 0)
        
        db_story = Story(**story_data)
        db.add(db_story)
        await db.commit()
        await db.refresh(db_story)
        
        # 更新作者的故事创建数量
        author_stmt = select(User).where(User.id == story_data['author_id'])
        author_result = await db.execute(author_stmt)
        author = author_result.scalar_one_or_none()
        if author:
            author.increment_stories_created()
            db.add(author)
            await db.commit()
        
        return db_story
    
    def publish_story(self, db: Session, *, story: Story) -> Story:
        """发布故事"""
        story.publish()
        db.add(story)
        db.commit()
        db.refresh(story)
        return story
    
    async def publish_story_async(self, db: AsyncSession, *, story: Story) -> Story:
        """异步发布故事"""
        story.publish()
        db.add(story)
        await db.commit()
        await db.refresh(story)
        return story
    
    def complete_story(self, db: Session, *, story: Story) -> Story:
        """完结故事"""
        story.complete()
        db.add(story)
        db.commit()
        db.refresh(story)
        return story
    
    async def complete_story_async(self, db: AsyncSession, *, story: Story) -> Story:
        """异步完结故事"""
        story.complete()
        db.add(story)
        await db.commit()
        await db.refresh(story)
        return story
    
    async def search_stories_async(
        self,
        db: AsyncSession,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """异步搜索故事"""
        return await self.search_async(
            db,
            query=query,
            search_fields=['title', 'description', 'protagonist_name'],
            skip=skip,
            limit=limit
        )
    
    async def get_story_stats_async(self, db: AsyncSession) -> Dict[str, Any]:
        """异步获取故事统计信息"""
        total_stories = await self.count_async(db)
        published_stories = await self.count_async(db, filters={'story_status': StoryStatus.PUBLISHED})
        completed_stories = await self.count_async(db, filters={'story_status': StoryStatus.COMPLETED})
        draft_stories = await self.count_async(db, filters={'story_status': StoryStatus.DRAFT})
        
        # 获取主题分布
        theme_stats = {}
        for theme in StoryTheme:
            count = await self.count_async(db, filters={'theme': theme})
            theme_stats[theme.value] = count
        
        return {
            'total_stories': total_stories,
            'published_stories': published_stories,
            'completed_stories': completed_stories,
            'draft_stories': draft_stories,
            'theme_distribution': theme_stats
        }
    
    async def get_trending_stories_async(
        self,
        db: AsyncSession,
        *,
        days: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """异步获取趋势故事（最近几天热门）"""
        from datetime import datetime, timedelta
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        stmt = select(Story).where(
            and_(
                Story.story_status.in_([StoryStatus.PUBLISHED, StoryStatus.COMPLETED]),
                Story.published_at >= cutoff_date,
                Story.is_deleted == False
            )
        ).order_by(desc(Story.total_reads), desc(Story.total_readers)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_recommended_stories_async(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Story]:
        """异步获取推荐故事（基于用户偏好）"""
        # 简单的推荐算法：基于用户阅读过的故事主题
        from app.models.choice import UserStoryProgress
        
        # 获取用户阅读过的故事主题
        user_progress_stmt = select(UserStoryProgress.story_id).where(
            UserStoryProgress.user_id == user_id
        )
        user_progress_result = await db.execute(user_progress_stmt)
        read_story_ids = [row[0] for row in user_progress_result.fetchall()]
        
        if read_story_ids:
            # 获取用户阅读过的故事主题
            read_stories_stmt = select(Story.theme).where(
                Story.id.in_(read_story_ids)
            )
            read_stories_result = await db.execute(read_stories_stmt)
            preferred_themes = [row[0] for row in read_stories_result.fetchall()]
            
            # 推荐相同主题的其他故事
            if preferred_themes:
                stmt = select(Story).where(
                    and_(
                        Story.theme.in_(preferred_themes),
                        Story.id.notin_(read_story_ids),
                        Story.story_status.in_([StoryStatus.PUBLISHED, StoryStatus.COMPLETED]),
                        Story.is_deleted == False
                    )
                ).order_by(desc(Story.average_rating), desc(Story.total_readers)).offset(skip).limit(limit)
                
                result = await db.execute(stmt)
                return result.scalars().all()
        
        # 如果没有阅读历史，返回热门故事
        return await self.get_popular_async(db, skip=skip, limit=limit)


# 创建故事CRUD实例
story = CRUDStory(Story)
