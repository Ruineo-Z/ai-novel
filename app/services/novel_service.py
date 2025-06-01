from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.novel import Novel, Chapter
from app.schemas.novel import NovelCreate, NovelUpdate, NovelSummary
from typing import List, Optional

class NovelService:
    async def create_novel(self, db: Session, novel_data: NovelCreate, 
                          outline: str, owner_id: int) -> Novel:
        """创建新小说"""
        db_novel = Novel(
            title=novel_data.title,
            genre=novel_data.genre,
            world_setting=novel_data.world_setting,
            protagonist_info=novel_data.protagonist_info.dict(),
            outline=outline,
            owner_id=owner_id
        )
        
        db.add(db_novel)
        db.commit()
        db.refresh(db_novel)
        
        return db_novel
    
    async def get_novel(self, db: Session, novel_id: int, 
                       include_chapters: bool = False) -> Optional[Novel]:
        """获取小说详情"""
        query = db.query(Novel).filter(Novel.id == novel_id)
        
        if include_chapters:
            query = query.options(db.joinedload(Novel.chapters))
        
        return query.first()
    
    async def get_user_novels(self, db: Session, user_id: int, 
                             skip: int = 0, limit: int = 10) -> List[NovelSummary]:
        """获取用户的小说列表"""
        # 使用子查询计算章节数和总字数
        chapter_stats = (
            db.query(
                Chapter.novel_id,
                func.count(Chapter.id).label('chapter_count'),
                func.sum(Chapter.word_count).label('total_words')
            )
            .group_by(Chapter.novel_id)
            .subquery()
        )
        
        novels = (
            db.query(
                Novel,
                func.coalesce(chapter_stats.c.chapter_count, 0).label('chapter_count'),
                func.coalesce(chapter_stats.c.total_words, 0).label('total_words')
            )
            .outerjoin(chapter_stats, Novel.id == chapter_stats.c.novel_id)
            .filter(Novel.owner_id == user_id)
            .order_by(desc(Novel.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        result = []
        for novel, chapter_count, total_words in novels:
            summary = NovelSummary(
                id=novel.id,
                title=novel.title,
                genre=novel.genre,
                status=novel.status,
                chapter_count=chapter_count or 0,
                total_words=total_words or 0,
                created_at=novel.created_at,
                updated_at=novel.updated_at
            )
            result.append(summary)
        
        return result
    
    async def update_novel(self, db: Session, novel_id: int, 
                          novel_update: NovelUpdate) -> Optional[Novel]:
        """更新小说信息"""
        novel = await self.get_novel(db, novel_id)
        if not novel:
            return None
        
        update_data = novel_update.dict(exclude_unset=True)
        
        # 处理主人公信息
        if 'protagonist_info' in update_data:
            update_data['protagonist_info'] = update_data['protagonist_info'].dict()
        
        for field, value in update_data.items():
            setattr(novel, field, value)
        
        db.commit()
        db.refresh(novel)
        
        return novel
    
    async def delete_novel(self, db: Session, novel_id: int) -> bool:
        """删除小说"""
        novel = await self.get_novel(db, novel_id)
        if not novel:
            return False
        
        db.delete(novel)
        db.commit()
        
        return True
    
    async def create_chapter(self, db: Session, novel_id: int, content: str,
                           choices: List[str], user_choice: Optional[str] = None,
                           title: Optional[str] = None) -> Chapter:
        """创建新章节"""
        # 获取下一个章节号
        last_chapter = (
            db.query(Chapter)
            .filter(Chapter.novel_id == novel_id)
            .order_by(desc(Chapter.chapter_number))
            .first()
        )
        
        next_chapter_number = (last_chapter.chapter_number + 1) if last_chapter else 1
        
        # 计算字数
        word_count = len(content.replace(' ', '').replace('\n', ''))
        
        db_chapter = Chapter(
            novel_id=novel_id,
            chapter_number=next_chapter_number,
            title=title or f"第{next_chapter_number}章",
            content=content,
            choices=choices,
            user_choice=user_choice,
            word_count=word_count
        )
        
        db.add(db_chapter)
        db.commit()
        db.refresh(db_chapter)
        
        # 更新小说的更新时间
        novel = await self.get_novel(db, novel_id)
        if novel:
            db.commit()  # 触发updated_at更新
        
        return db_chapter
    
    async def get_chapters(self, db: Session, novel_id: int, 
                          skip: int = 0, limit: int = 50) -> List[Chapter]:
        """获取小说章节列表"""
        return (
            db.query(Chapter)
            .filter(Chapter.novel_id == novel_id)
            .order_by(Chapter.chapter_number)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    async def get_chapter_by_number(self, db: Session, novel_id: int, 
                                   chapter_number: int) -> Optional[Chapter]:
        """根据章节号获取章节"""
        return (
            db.query(Chapter)
            .filter(
                Chapter.novel_id == novel_id,
                Chapter.chapter_number == chapter_number
            )
            .first()
        )
    
    async def get_chapter_by_id(self, db: Session, chapter_id: int) -> Optional[Chapter]:
        """根据ID获取章节"""
        return db.query(Chapter).filter(Chapter.id == chapter_id).first()
    
    async def update_chapter(self, db: Session, chapter_id: int, 
                           content: Optional[str] = None,
                           choices: Optional[List[str]] = None,
                           user_choice: Optional[str] = None) -> Optional[Chapter]:
        """更新章节"""
        chapter = await self.get_chapter_by_id(db, chapter_id)
        if not chapter:
            return None
        
        if content is not None:
            chapter.content = content
            chapter.word_count = len(content.replace(' ', '').replace('\n', ''))
        
        if choices is not None:
            chapter.choices = choices
        
        if user_choice is not None:
            chapter.user_choice = user_choice
        
        db.commit()
        db.refresh(chapter)
        
        return chapter
    
    async def delete_chapter(self, db: Session, chapter_id: int) -> bool:
        """删除章节"""
        chapter = await self.get_chapter_by_id(db, chapter_id)
        if not chapter:
            return False
        
        db.delete(chapter)
        db.commit()
        
        return True
    
    async def get_recent_chapters(self, db: Session, novel_id: int, 
                                 count: int = 3) -> List[Chapter]:
        """获取最近的章节（用于上下文）"""
        return (
            db.query(Chapter)
            .filter(Chapter.novel_id == novel_id)
            .order_by(desc(Chapter.chapter_number))
            .limit(count)
            .all()
        )