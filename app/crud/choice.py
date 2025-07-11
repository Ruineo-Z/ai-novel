"""
AI互动小说 - 选择CRUD操作
选择相关的数据库操作
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import and_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.choice import Choice, UserStoryProgress


class CRUDChoice(CRUDBase[Choice, Dict[str, Any], Dict[str, Any]]):
    """选择CRUD操作类"""
    
    def get_by_chapter(
        self,
        db: Session,
        *,
        chapter_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Choice]:
        """根据章节获取选择列表"""
        return db.query(Choice).filter(
            and_(
                Choice.chapter_id == chapter_id,
                Choice.is_deleted == False
            )
        ).order_by(asc(Choice.choice_order)).offset(skip).limit(limit).all()
    
    async def get_by_chapter_async(
        self,
        db: AsyncSession,
        *,
        chapter_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Choice]:
        """异步根据章节获取选择列表"""
        stmt = select(Choice).where(
            and_(
                Choice.chapter_id == chapter_id,
                Choice.is_deleted == False
            )
        ).order_by(asc(Choice.choice_order)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_available_choices(
        self,
        db: Session,
        *,
        chapter_id: str,
        user_is_premium: bool = False
    ) -> List[Choice]:
        """获取可用的选择"""
        query = db.query(Choice).filter(
            and_(
                Choice.chapter_id == chapter_id,
                Choice.is_hidden == False,
                Choice.is_deleted == False
            )
        )
        
        if not user_is_premium:
            query = query.filter(Choice.is_premium == False)
        
        return query.order_by(asc(Choice.choice_order)).all()
    
    async def get_available_choices_async(
        self,
        db: AsyncSession,
        *,
        chapter_id: str,
        user_is_premium: bool = False
    ) -> List[Choice]:
        """异步获取可用的选择"""
        stmt = select(Choice).where(
            and_(
                Choice.chapter_id == chapter_id,
                Choice.is_hidden == False,
                Choice.is_deleted == False
            )
        )
        
        if not user_is_premium:
            stmt = stmt.where(Choice.is_premium == False)
        
        stmt = stmt.order_by(asc(Choice.choice_order))
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def create_choice(self, db: Session, *, choice_data: Dict[str, Any]) -> Choice:
        """创建选择"""
        # 自动设置选择顺序
        if 'choice_order' not in choice_data:
            chapter_id = choice_data['chapter_id']
            max_order = db.query(func.max(Choice.choice_order)).filter(
                Choice.chapter_id == chapter_id
            ).scalar()
            
            choice_data['choice_order'] = (max_order if max_order else 0) + 1
        
        # 设置默认值
        choice_data.setdefault('selection_count', 0)
        choice_data.setdefault('is_default', False)
        choice_data.setdefault('is_premium', False)
        choice_data.setdefault('is_hidden', False)
        choice_data.setdefault('ai_generated', True)
        
        db_choice = Choice(**choice_data)
        db.add(db_choice)
        db.commit()
        db.refresh(db_choice)
        return db_choice
    
    async def create_choice_async(self, db: AsyncSession, *, choice_data: Dict[str, Any]) -> Choice:
        """异步创建选择"""
        # 自动设置选择顺序
        if 'choice_order' not in choice_data:
            chapter_id = choice_data['chapter_id']
            max_order_stmt = select(func.max(Choice.choice_order)).where(
                Choice.chapter_id == chapter_id
            )
            max_order_result = await db.execute(max_order_stmt)
            max_order = max_order_result.scalar()
            
            choice_data['choice_order'] = (max_order if max_order else 0) + 1
        
        # 设置默认值
        choice_data.setdefault('selection_count', 0)
        choice_data.setdefault('is_default', False)
        choice_data.setdefault('is_premium', False)
        choice_data.setdefault('is_hidden', False)
        choice_data.setdefault('ai_generated', True)
        
        db_choice = Choice(**choice_data)
        db.add(db_choice)
        await db.commit()
        await db.refresh(db_choice)
        return db_choice
    
    def increment_selection(self, db: Session, *, choice: Choice) -> Choice:
        """增加选择次数"""
        choice.increment_selection()
        db.add(choice)
        db.commit()
        db.refresh(choice)
        return choice
    
    async def increment_selection_async(self, db: AsyncSession, *, choice: Choice) -> Choice:
        """异步增加选择次数"""
        choice.increment_selection()
        db.add(choice)
        await db.commit()
        await db.refresh(choice)
        return choice
    
    async def get_popular_choices_async(
        self,
        db: AsyncSession,
        *,
        chapter_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Choice]:
        """异步获取热门选择"""
        stmt = select(Choice).where(Choice.is_deleted == False)
        
        if chapter_id:
            stmt = stmt.where(Choice.chapter_id == chapter_id)
        
        stmt = stmt.order_by(desc(Choice.selection_count)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_choice_stats_async(self, db: AsyncSession, *, chapter_id: str) -> Dict[str, Any]:
        """异步获取选择统计信息"""
        total_choices = await self.count_async(db, filters={'chapter_id': chapter_id})
        premium_choices = await self.count_async(db, filters={
            'chapter_id': chapter_id,
            'is_premium': True
        })
        hidden_choices = await self.count_async(db, filters={
            'chapter_id': chapter_id,
            'is_hidden': True
        })
        
        return {
            'total_choices': total_choices,
            'premium_choices': premium_choices,
            'hidden_choices': hidden_choices,
            'available_choices': total_choices - hidden_choices
        }


class CRUDUserStoryProgress(CRUDBase[UserStoryProgress, Dict[str, Any], Dict[str, Any]]):
    """用户故事进度CRUD操作类"""
    
    def get_by_user_story(
        self,
        db: Session,
        *,
        user_id: str,
        story_id: str
    ) -> Optional[UserStoryProgress]:
        """根据用户和故事获取进度"""
        return db.query(UserStoryProgress).filter(
            and_(
                UserStoryProgress.user_id == user_id,
                UserStoryProgress.story_id == story_id,
                UserStoryProgress.is_deleted == False
            )
        ).first()
    
    async def get_by_user_story_async(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        story_id: str
    ) -> Optional[UserStoryProgress]:
        """异步根据用户和故事获取进度"""
        stmt = select(UserStoryProgress).where(
            and_(
                UserStoryProgress.user_id == user_id,
                UserStoryProgress.story_id == story_id,
                UserStoryProgress.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_progress_list_async(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserStoryProgress]:
        """异步获取用户的所有故事进度"""
        stmt = select(UserStoryProgress).options(
            joinedload(UserStoryProgress.story)
        ).where(
            and_(
                UserStoryProgress.user_id == user_id,
                UserStoryProgress.is_deleted == False
            )
        ).order_by(desc(UserStoryProgress.updated_at)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def update_progress_async(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        story_id: str,
        chapter_id: str,
        choice_id: Optional[str] = None,
        reading_time: int = 0
    ) -> UserStoryProgress:
        """异步更新阅读进度"""
        progress = await self.get_by_user_story_async(db, user_id=user_id, story_id=story_id)
        
        if not progress:
            # 创建新的进度记录
            progress_data = {
                'user_id': user_id,
                'story_id': story_id,
                'current_chapter_id': chapter_id,
                'chapters_read': 1,
                'total_reading_time': reading_time,
                'last_choice_id': choice_id
            }
            progress = await self.create_async(db, obj_in=progress_data)
        else:
            # 更新现有进度
            progress.update_progress(chapter_id, choice_id, reading_time)
            db.add(progress)
            await db.commit()
            await db.refresh(progress)
        
        return progress


# 创建CRUD实例
choice = CRUDChoice(Choice)
user_story_progress = CRUDUserStoryProgress(UserStoryProgress)
