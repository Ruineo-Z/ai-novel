"""
AI互动小说 - 章节模型
章节内容和选择管理
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import FullModel


class ChapterStatus(str, Enum):
    """章节状态枚举"""
    DRAFT = "draft"              # 草稿
    PUBLISHED = "published"      # 已发布
    ARCHIVED = "archived"        # 已归档


class GenerationMethod(str, Enum):
    """生成方式枚举"""
    AI_GENERATED = "ai_generated"    # AI生成
    USER_WRITTEN = "user_written"   # 用户编写
    MIXED = "mixed"                  # 混合模式


class Chapter(FullModel):
    """章节模型"""
    
    __tablename__ = "chapters"
    
    # 基本信息
    title = Column(
        String(200),
        nullable=False,
        comment="章节标题"
    )
    
    content = Column(
        Text,
        nullable=False,
        comment="章节内容"
    )
    
    summary = Column(
        Text,
        nullable=True,
        comment="章节摘要"
    )
    
    # 章节属性
    story_id = Column(
        String(36),
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属故事ID"
    )
    
    chapter_number = Column(
        Integer,
        nullable=False,
        comment="章节序号"
    )
    
    parent_chapter_id = Column(
        String(36),
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="父章节ID"
    )
    
    # 内容属性
    word_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="字数统计"
    )
    
    reading_time = Column(
        Integer,
        default=0,
        nullable=False,
        comment="预估阅读时间(分钟)"
    )
    
    # 状态信息
    chapter_status = Column(
        SQLEnum(ChapterStatus),
        nullable=False,
        default=ChapterStatus.DRAFT,
        index=True,
        comment="章节状态"
    )
    
    generation_method = Column(
        SQLEnum(GenerationMethod),
        nullable=False,
        default=GenerationMethod.AI_GENERATED,
        comment="生成方式"
    )
    
    is_ending = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为结局章节"
    )
    
    # AI生成相关
    ai_prompt = Column(
        Text,
        nullable=True,
        comment="AI生成提示词"
    )
    
    ai_model_used = Column(
        String(50),
        nullable=True,
        comment="使用的AI模型"
    )
    
    generation_tokens = Column(
        Integer,
        default=0,
        nullable=False,
        comment="生成消耗的token数"
    )
    
    # 用户交互
    user_choice_text = Column(
        Text,
        nullable=True,
        comment="用户选择的文本"
    )
    
    user_input_text = Column(
        Text,
        nullable=True,
        comment="用户自定义输入"
    )
    
    # 统计信息
    read_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="阅读次数"
    )
    
    choice_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="选择次数"
    )
    
    # 发布信息
    published_at = Column(
        String(50),
        nullable=True,
        comment="发布时间"
    )
    
    # 关系
    story = relationship(
        "Story",
        back_populates="chapters"
    )
    
    parent_chapter = relationship(
        "Chapter",
        remote_side="Chapter.id",
        backref="child_chapters"
    )
    
    choices = relationship(
        "Choice",
        back_populates="chapter",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Choice.choice_order",
        foreign_keys="Choice.chapter_id"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_chapter_story_number', 'story_id', 'chapter_number'),
        Index('idx_chapter_parent', 'parent_chapter_id'),
        Index('idx_chapter_status', 'chapter_status'),
        Index('idx_chapter_published_at', 'published_at'),
        Index('idx_chapter_read_count', 'read_count'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.content:
            self.update_word_count()
    
    @property
    def is_published(self) -> bool:
        """是否已发布"""
        return self.chapter_status == ChapterStatus.PUBLISHED
    
    @property
    def has_choices(self) -> bool:
        """是否有选择"""
        return self.choices.count() > 0
    
    @property
    def is_root_chapter(self) -> bool:
        """是否为根章节"""
        return self.parent_chapter_id is None
    
    def update_word_count(self):
        """更新字数统计"""
        if self.content:
            # 简单的中文字数统计
            self.word_count = len(self.content.replace(' ', '').replace('\n', ''))
            # 预估阅读时间（按每分钟300字计算）
            self.reading_time = max(1, self.word_count // 300)
    
    def publish(self):
        """发布章节"""
        if self.chapter_status == ChapterStatus.DRAFT:
            self.chapter_status = ChapterStatus.PUBLISHED
            self.published_at = datetime.utcnow().isoformat()
    
    def archive(self):
        """归档章节"""
        self.chapter_status = ChapterStatus.ARCHIVED
    
    def increment_read_count(self):
        """增加阅读次数"""
        self.read_count += 1
    
    def increment_choice_count(self):
        """增加选择次数"""
        self.choice_count += 1
    
    def set_ai_generation_info(self, prompt: str, model: str, tokens: int):
        """设置AI生成信息"""
        self.ai_prompt = prompt
        self.ai_model_used = model
        self.generation_tokens = tokens
        self.generation_method = GenerationMethod.AI_GENERATED
    
    def set_user_choice(self, choice_text: str, input_text: Optional[str] = None):
        """设置用户选择"""
        self.user_choice_text = choice_text
        if input_text:
            self.user_input_text = input_text
    
    def get_next_chapter_number(self) -> int:
        """获取下一个章节号"""
        if self.story:
            max_number = 0
            for chapter in self.story.chapters:
                if chapter.chapter_number > max_number:
                    max_number = chapter.chapter_number
            return max_number + 1
        return self.chapter_number + 1
    
    def get_reading_stats(self) -> Dict[str, Any]:
        """获取阅读统计"""
        return {
            "word_count": self.word_count,
            "reading_time": self.reading_time,
            "read_count": self.read_count,
            "choice_count": self.choice_count,
            "choices_available": self.choices.count()
        }
    
    def to_dict(self, include_content: bool = True, include_ai_info: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "story_id": self.story_id,
            "chapter_number": self.chapter_number,
            "parent_chapter_id": self.parent_chapter_id,
            "word_count": self.word_count,
            "reading_time": self.reading_time,
            "status": self.chapter_status.value if self.chapter_status else None,
            "generation_method": self.generation_method.value if self.generation_method else None,
            "is_ending": self.is_ending,
            "read_count": self.read_count,
            "choice_count": self.choice_count,
            "published_at": self.published_at,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_content:
            result["content"] = self.content
            result["user_choice_text"] = self.user_choice_text
            result["user_input_text"] = self.user_input_text
        
        if include_ai_info:
            result["ai_prompt"] = self.ai_prompt
            result["ai_model_used"] = self.ai_model_used
            result["generation_tokens"] = self.generation_tokens
        
        return result
    
    def __repr__(self):
        return f"<Chapter(id={self.id}, story_id={self.story_id}, number={self.chapter_number})>"
