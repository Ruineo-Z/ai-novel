"""
AI互动小说 - 故事模型
故事基本信息、设置和配置
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import FullModel


class StoryTheme(str, Enum):
    """故事主题枚举"""
    URBAN = "urban"              # 都市
    SCIFI = "scifi"              # 科幻
    CULTIVATION = "cultivation"   # 修仙
    MARTIAL_ARTS = "martial_arts" # 武侠
    FANTASY = "fantasy"          # 奇幻
    ROMANCE = "romance"          # 言情
    MYSTERY = "mystery"          # 悬疑
    HORROR = "horror"            # 恐怖
    HISTORICAL = "historical"    # 历史
    ADVENTURE = "adventure"      # 冒险


class StoryStatus(str, Enum):
    """故事状态枚举"""
    DRAFT = "draft"              # 草稿
    PUBLISHED = "published"      # 已发布
    COMPLETED = "completed"      # 已完结
    PAUSED = "paused"           # 暂停
    ARCHIVED = "archived"        # 已归档


class StoryDifficulty(str, Enum):
    """故事难度枚举"""
    EASY = "easy"               # 简单
    MEDIUM = "medium"           # 中等
    HARD = "hard"               # 困难
    EXPERT = "expert"           # 专家


class Story(FullModel):
    """故事模型"""
    
    __tablename__ = "stories"
    
    # 基本信息
    title = Column(
        String(200),
        nullable=False,
        index=True,
        comment="故事标题"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="故事描述"
    )
    
    cover_image_url = Column(
        String(500),
        nullable=True,
        comment="封面图片URL"
    )
    
    # 故事设置
    theme = Column(
        SQLEnum(StoryTheme),
        nullable=False,
        default=StoryTheme.URBAN,
        index=True,
        comment="故事主题"
    )
    
    story_status = Column(
        SQLEnum(StoryStatus),
        nullable=False,
        default=StoryStatus.DRAFT,
        index=True,
        comment="故事状态"
    )
    
    difficulty = Column(
        SQLEnum(StoryDifficulty),
        nullable=False,
        default=StoryDifficulty.MEDIUM,
        comment="故事难度"
    )
    
    # 作者信息
    author_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="作者ID"
    )
    
    # 故事配置
    max_chapters = Column(
        Integer,
        default=100,
        nullable=False,
        comment="最大章节数"
    )
    
    choices_per_chapter = Column(
        Integer,
        default=3,
        nullable=False,
        comment="每章选择数量"
    )
    
    auto_generate = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否自动生成内容"
    )
    
    allow_user_input = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否允许用户自定义输入"
    )
    
    # 内容设置
    protagonist_name = Column(
        String(100),
        nullable=True,
        comment="主角姓名"
    )
    
    protagonist_description = Column(
        Text,
        nullable=True,
        comment="主角描述"
    )
    
    world_setting = Column(
        Text,
        nullable=True,
        comment="世界观设定"
    )
    
    story_background = Column(
        Text,
        nullable=True,
        comment="故事背景"
    )
    
    writing_style = Column(
        String(50),
        default="narrative",
        nullable=False,
        comment="写作风格"
    )
    
    # 统计信息
    total_chapters = Column(
        Integer,
        default=0,
        nullable=False,
        comment="总章节数"
    )
    
    total_words = Column(
        Integer,
        default=0,
        nullable=False,
        comment="总字数"
    )
    
    total_readers = Column(
        Integer,
        default=0,
        nullable=False,
        comment="总读者数"
    )
    
    total_reads = Column(
        Integer,
        default=0,
        nullable=False,
        comment="总阅读次数"
    )
    
    average_rating = Column(
        Integer,
        default=0,
        nullable=False,
        comment="平均评分(1-5)"
    )
    
    # 发布信息
    published_at = Column(
        String(50),
        nullable=True,
        comment="发布时间"
    )
    
    completed_at = Column(
        String(50),
        nullable=True,
        comment="完结时间"
    )
    
    # 关系
    author = relationship(
        "User",
        back_populates="stories"
    )
    
    chapters = relationship(
        "Chapter",
        back_populates="story",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Chapter.chapter_number"
    )
    
    user_progress = relationship(
        "UserStoryProgress",
        back_populates="story",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    story_memories = relationship(
        "StoryMemory",
        back_populates="story",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_story_author_status', 'author_id', 'story_status'),
        Index('idx_story_theme_status', 'theme', 'story_status'),
        Index('idx_story_published_at', 'published_at'),
        Index('idx_story_total_readers', 'total_readers'),
        Index('idx_story_average_rating', 'average_rating'),
    )
    
    @property
    def is_published(self) -> bool:
        """是否已发布"""
        return self.story_status in [StoryStatus.PUBLISHED, StoryStatus.COMPLETED]
    
    @property
    def is_completed(self) -> bool:
        """是否已完结"""
        return self.story_status == StoryStatus.COMPLETED
    
    @property
    def can_add_chapters(self) -> bool:
        """是否可以添加章节"""
        return (
            self.story_status in [StoryStatus.DRAFT, StoryStatus.PUBLISHED] and
            self.total_chapters < self.max_chapters
        )
    
    def publish(self):
        """发布故事"""
        if self.story_status == StoryStatus.DRAFT:
            self.story_status = StoryStatus.PUBLISHED
            self.published_at = datetime.utcnow().isoformat()
    
    def complete(self):
        """完结故事"""
        if self.story_status == StoryStatus.PUBLISHED:
            self.story_status = StoryStatus.COMPLETED
            self.completed_at = datetime.utcnow().isoformat()
    
    def pause(self):
        """暂停故事"""
        if self.story_status == StoryStatus.PUBLISHED:
            self.story_status = StoryStatus.PAUSED
    
    def resume(self):
        """恢复故事"""
        if self.story_status == StoryStatus.PAUSED:
            self.story_status = StoryStatus.PUBLISHED
    
    def archive(self):
        """归档故事"""
        self.story_status = StoryStatus.ARCHIVED
    
    def increment_chapters(self, words: int = 0):
        """增加章节数和字数"""
        self.total_chapters += 1
        self.total_words += words
    
    def increment_readers(self):
        """增加读者数"""
        self.total_readers += 1
    
    def increment_reads(self):
        """增加阅读次数"""
        self.total_reads += 1
    
    def update_rating(self, new_rating: int, total_ratings: int):
        """更新平均评分"""
        if total_ratings > 0:
            self.average_rating = new_rating
    
    def get_reading_stats(self) -> Dict[str, Any]:
        """获取阅读统计"""
        return {
            "total_chapters": self.total_chapters,
            "total_words": self.total_words,
            "total_readers": self.total_readers,
            "total_reads": self.total_reads,
            "average_rating": self.average_rating,
            "words_per_chapter": (
                self.total_words // self.total_chapters 
                if self.total_chapters > 0 else 0
            )
        }
    
    def to_public_dict(self) -> Dict[str, Any]:
        """转换为公开信息字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "cover_image_url": self.cover_image_url,
            "theme": self.theme.value if self.theme else None,
            "status": self.story_status.value if self.story_status else None,
            "difficulty": self.difficulty.value if self.difficulty else None,
            "author_id": self.author_id,
            "total_chapters": self.total_chapters,
            "total_words": self.total_words,
            "total_readers": self.total_readers,
            "average_rating": self.average_rating,
            "published_at": self.published_at,
            "completed_at": self.completed_at,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<Story(id={self.id}, title={self.title}, author_id={self.author_id})>"
