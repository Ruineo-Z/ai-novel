"""
AI互动小说 - 故事记忆CRUD操作
故事记忆相关的数据库操作
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import and_, desc, asc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.memory import StoryMemory, MemoryType, MemoryImportance


class CRUDStoryMemory(CRUDBase[StoryMemory, Dict[str, Any], Dict[str, Any]]):
    """故事记忆CRUD操作类"""
    
    def get_by_story(
        self,
        db: Session,
        *,
        story_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoryMemory]:
        """根据故事获取记忆列表"""
        return db.query(StoryMemory).filter(
            and_(
                StoryMemory.story_id == story_id,
                StoryMemory.is_active == True,
                StoryMemory.is_deleted == False
            )
        ).order_by(desc(StoryMemory.importance), desc(StoryMemory.access_count)).offset(skip).limit(limit).all()
    
    async def get_by_story_async(
        self,
        db: AsyncSession,
        *,
        story_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoryMemory]:
        """异步根据故事获取记忆列表"""
        stmt = select(StoryMemory).where(
            and_(
                StoryMemory.story_id == story_id,
                StoryMemory.is_active == True,
                StoryMemory.is_deleted == False
            )
        ).order_by(desc(StoryMemory.importance), desc(StoryMemory.access_count)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_by_type(
        self,
        db: Session,
        *,
        story_id: str,
        memory_type: MemoryType,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoryMemory]:
        """根据类型获取记忆"""
        return db.query(StoryMemory).filter(
            and_(
                StoryMemory.story_id == story_id,
                StoryMemory.memory_type == memory_type,
                StoryMemory.is_active == True,
                StoryMemory.is_deleted == False
            )
        ).order_by(desc(StoryMemory.importance), desc(StoryMemory.access_count)).offset(skip).limit(limit).all()
    
    async def get_by_type_async(
        self,
        db: AsyncSession,
        *,
        story_id: str,
        memory_type: MemoryType,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoryMemory]:
        """异步根据类型获取记忆"""
        stmt = select(StoryMemory).where(
            and_(
                StoryMemory.story_id == story_id,
                StoryMemory.memory_type == memory_type,
                StoryMemory.is_active == True,
                StoryMemory.is_deleted == False
            )
        ).order_by(desc(StoryMemory.importance), desc(StoryMemory.access_count)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def get_by_importance(
        self,
        db: Session,
        *,
        story_id: str,
        importance: MemoryImportance,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoryMemory]:
        """根据重要性获取记忆"""
        return db.query(StoryMemory).filter(
            and_(
                StoryMemory.story_id == story_id,
                StoryMemory.importance == importance,
                StoryMemory.is_active == True,
                StoryMemory.is_deleted == False
            )
        ).order_by(desc(StoryMemory.access_count)).offset(skip).limit(limit).all()
    
    async def get_by_importance_async(
        self,
        db: AsyncSession,
        *,
        story_id: str,
        importance: MemoryImportance,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoryMemory]:
        """异步根据重要性获取记忆"""
        stmt = select(StoryMemory).where(
            and_(
                StoryMemory.story_id == story_id,
                StoryMemory.importance == importance,
                StoryMemory.is_active == True,
                StoryMemory.is_deleted == False
            )
        ).order_by(desc(StoryMemory.access_count)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    def create_memory(self, db: Session, *, memory_data: Dict[str, Any]) -> StoryMemory:
        """创建记忆"""
        # 设置默认值
        memory_data.setdefault('memory_type', MemoryType.PLOT)
        memory_data.setdefault('importance', MemoryImportance.MEDIUM)
        memory_data.setdefault('access_count', 0)
        memory_data.setdefault('similarity_score', 0.0)
        memory_data.setdefault('is_active', True)
        memory_data.setdefault('ai_generated', True)
        
        db_memory = StoryMemory(**memory_data)
        db.add(db_memory)
        db.commit()
        db.refresh(db_memory)
        return db_memory
    
    async def create_memory_async(self, db: AsyncSession, *, memory_data: Dict[str, Any]) -> StoryMemory:
        """异步创建记忆"""
        # 设置默认值
        memory_data.setdefault('memory_type', MemoryType.PLOT)
        memory_data.setdefault('importance', MemoryImportance.MEDIUM)
        memory_data.setdefault('access_count', 0)
        memory_data.setdefault('similarity_score', 0.0)
        memory_data.setdefault('is_active', True)
        memory_data.setdefault('ai_generated', True)
        
        db_memory = StoryMemory(**memory_data)
        db.add(db_memory)
        await db.commit()
        await db.refresh(db_memory)
        return db_memory
    
    def access_memory(self, db: Session, *, memory: StoryMemory) -> StoryMemory:
        """记录记忆访问"""
        memory.access()
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory
    
    async def access_memory_async(self, db: AsyncSession, *, memory: StoryMemory) -> StoryMemory:
        """异步记录记忆访问"""
        memory.access()
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        return memory
    
    async def search_memories_async(
        self,
        db: AsyncSession,
        *,
        story_id: str,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoryMemory]:
        """异步搜索记忆"""
        # 在标题、内容、摘要、标签、关键词中搜索
        search_fields = [
            StoryMemory.title,
            StoryMemory.content,
            StoryMemory.summary,
            StoryMemory.tags,
            StoryMemory.keywords
        ]
        
        search_conditions = []
        for field in search_fields:
            search_conditions.append(field.ilike(f"%{query}%"))
        
        stmt = select(StoryMemory).where(
            and_(
                StoryMemory.story_id == story_id,
                StoryMemory.is_active == True,
                StoryMemory.is_deleted == False,
                or_(*search_conditions)
            )
        ).order_by(desc(StoryMemory.importance), desc(StoryMemory.access_count)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_similar_memories_async(
        self,
        db: AsyncSession,
        *,
        story_id: str,
        similarity_threshold: float = 0.7,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoryMemory]:
        """异步获取相似记忆"""
        stmt = select(StoryMemory).where(
            and_(
                StoryMemory.story_id == story_id,
                StoryMemory.similarity_score >= similarity_threshold,
                StoryMemory.is_active == True,
                StoryMemory.is_deleted == False
            )
        ).order_by(desc(StoryMemory.similarity_score)).offset(skip).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def get_memory_stats_async(self, db: AsyncSession, *, story_id: str) -> Dict[str, Any]:
        """异步获取记忆统计信息"""
        total_memories = await self.count_async(db, filters={'story_id': story_id, 'is_active': True})
        
        # 按类型统计
        type_stats = {}
        for memory_type in MemoryType:
            count = await self.count_async(db, filters={
                'story_id': story_id,
                'memory_type': memory_type,
                'is_active': True
            })
            type_stats[memory_type.value] = count
        
        # 按重要性统计
        importance_stats = {}
        for importance in MemoryImportance:
            count = await self.count_async(db, filters={
                'story_id': story_id,
                'importance': importance,
                'is_active': True
            })
            importance_stats[importance.value] = count
        
        return {
            'total_memories': total_memories,
            'type_distribution': type_stats,
            'importance_distribution': importance_stats
        }
    
    async def get_popular_memories_async(
        self,
        db: AsyncSession,
        *,
        story_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoryMemory]:
        """异步获取热门记忆"""
        stmt = select(StoryMemory).where(
            and_(
                StoryMemory.is_active == True,
                StoryMemory.is_deleted == False
            )
        )
        
        if story_id:
            stmt = stmt.where(StoryMemory.story_id == story_id)
        
        stmt = stmt.order_by(desc(StoryMemory.access_count)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def cleanup_expired_memories_async(self, db: AsyncSession) -> int:
        """异步清理过期记忆"""
        from datetime import datetime
        
        # 查找过期的记忆
        current_time = datetime.utcnow().isoformat()
        stmt = select(StoryMemory).where(
            and_(
                StoryMemory.expires_at.isnot(None),
                StoryMemory.expires_at < current_time,
                StoryMemory.is_active == True
            )
        )
        
        result = await db.execute(stmt)
        expired_memories = result.scalars().all()
        
        # 停用过期记忆
        count = 0
        for memory in expired_memories:
            memory.deactivate()
            db.add(memory)
            count += 1
        
        if count > 0:
            await db.commit()
        
        return count


# 创建CRUD实例
story_memory = CRUDStoryMemory(StoryMemory)
