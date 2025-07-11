"""
AI互动小说 - 选择模型
章节选择选项管理
"""
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import StandardModel


class Choice(StandardModel):
    """选择模型"""
    
    __tablename__ = "choices"
    
    # 基本信息
    text = Column(
        Text,
        nullable=False,
        comment="选择文本"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="选择描述"
    )
    
    # 关联信息
    chapter_id = Column(
        String(36),
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属章节ID"
    )
    
    next_chapter_id = Column(
        String(36),
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="下一章节ID"
    )
    
    # 选择属性
    choice_order = Column(
        Integer,
        nullable=False,
        comment="选择顺序"
    )
    
    is_default = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为默认选择"
    )
    
    is_premium = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否为高级选择"
    )
    
    is_hidden = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否隐藏选择"
    )
    
    # 条件和效果
    condition_text = Column(
        Text,
        nullable=True,
        comment="显示条件描述"
    )
    
    effect_text = Column(
        Text,
        nullable=True,
        comment="选择效果描述"
    )
    
    # 统计信息
    selection_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="被选择次数"
    )
    
    # AI生成相关
    ai_generated = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否AI生成"
    )
    
    generation_prompt = Column(
        Text,
        nullable=True,
        comment="生成提示词"
    )
    
    # 关系
    chapter = relationship(
        "Chapter",
        back_populates="choices",
        foreign_keys=[chapter_id]
    )
    
    next_chapter = relationship(
        "Chapter",
        foreign_keys=[next_chapter_id],
        post_update=True
    )
    
    # 索引
    __table_args__ = (
        Index('idx_choice_chapter_order', 'chapter_id', 'choice_order'),
        Index('idx_choice_next_chapter', 'next_chapter_id'),
        Index('idx_choice_selection_count', 'selection_count'),
        Index('idx_choice_is_default', 'is_default'),
    )
    
    @property
    def is_available(self) -> bool:
        """选择是否可用"""
        return not self.is_hidden and not self.is_deleted
    
    @property
    def requires_premium(self) -> bool:
        """是否需要高级会员"""
        return self.is_premium
    
    def increment_selection(self):
        """增加选择次数"""
        self.selection_count += 1
    
    def set_as_default(self):
        """设置为默认选择"""
        self.is_default = True
    
    def remove_default(self):
        """移除默认选择"""
        self.is_default = False
    
    def hide(self):
        """隐藏选择"""
        self.is_hidden = True
    
    def show(self):
        """显示选择"""
        self.is_hidden = False
    
    def set_premium(self, is_premium: bool = True):
        """设置高级选择"""
        self.is_premium = is_premium
    
    def set_condition(self, condition: str):
        """设置显示条件"""
        self.condition_text = condition
    
    def set_effect(self, effect: str):
        """设置选择效果"""
        self.effect_text = effect
    
    def set_ai_generation_info(self, prompt: str):
        """设置AI生成信息"""
        self.ai_generated = True
        self.generation_prompt = prompt
    
    def get_selection_stats(self) -> Dict[str, Any]:
        """获取选择统计"""
        return {
            "selection_count": self.selection_count,
            "is_popular": self.selection_count > 0,
            "choice_order": self.choice_order
        }
    
    def to_dict(self, include_ai_info: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "id": self.id,
            "text": self.text,
            "description": self.description,
            "chapter_id": self.chapter_id,
            "next_chapter_id": self.next_chapter_id,
            "choice_order": self.choice_order,
            "is_default": self.is_default,
            "is_premium": self.is_premium,
            "is_hidden": self.is_hidden,
            "condition_text": self.condition_text,
            "effect_text": self.effect_text,
            "selection_count": self.selection_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_ai_info:
            result["ai_generated"] = self.ai_generated
            result["generation_prompt"] = self.generation_prompt
        
        return result
    
    def to_user_dict(self, user_is_premium: bool = False) -> Dict[str, Any]:
        """转换为用户可见的字典"""
        # 检查用户是否可以看到此选择
        if self.is_hidden:
            return None
        
        if self.is_premium and not user_is_premium:
            return {
                "id": self.id,
                "text": "🔒 高级选择",
                "description": "此选择需要高级会员权限",
                "choice_order": self.choice_order,
                "is_premium": True,
                "is_locked": True
            }
        
        return {
            "id": self.id,
            "text": self.text,
            "description": self.description,
            "choice_order": self.choice_order,
            "is_default": self.is_default,
            "is_premium": self.is_premium,
            "condition_text": self.condition_text,
            "effect_text": self.effect_text,
            "is_locked": False
        }
    
    def __repr__(self):
        return f"<Choice(id={self.id}, chapter_id={self.chapter_id}, order={self.choice_order})>"


class UserStoryProgress(StandardModel):
    """用户故事进度模型"""
    
    __tablename__ = "user_story_progress"
    
    # 关联信息
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID"
    )
    
    story_id = Column(
        String(36),
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="故事ID"
    )
    
    current_chapter_id = Column(
        String(36),
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="当前章节ID"
    )
    
    # 进度信息
    chapters_read = Column(
        Integer,
        default=0,
        nullable=False,
        comment="已读章节数"
    )
    
    total_reading_time = Column(
        Integer,
        default=0,
        nullable=False,
        comment="总阅读时间(分钟)"
    )
    
    last_choice_id = Column(
        String(36),
        ForeignKey("choices.id", ondelete="SET NULL"),
        nullable=True,
        comment="最后选择ID"
    )
    
    # 状态信息
    is_completed = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已完成"
    )
    
    is_bookmarked = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已收藏"
    )
    
    # 评分
    user_rating = Column(
        Integer,
        nullable=True,
        comment="用户评分(1-5)"
    )
    
    # 关系
    user = relationship(
        "User",
        back_populates="story_progress"
    )
    
    story = relationship(
        "Story",
        back_populates="user_progress"
    )
    
    current_chapter = relationship(
        "Chapter",
        foreign_keys=[current_chapter_id]
    )
    
    last_choice = relationship(
        "Choice",
        foreign_keys=[last_choice_id]
    )
    
    # 索引
    __table_args__ = (
        Index('idx_user_story_progress', 'user_id', 'story_id'),
        Index('idx_progress_current_chapter', 'current_chapter_id'),
        Index('idx_progress_completed', 'is_completed'),
        Index('idx_progress_bookmarked', 'is_bookmarked'),
    )
    
    def update_progress(self, chapter_id: str, choice_id: Optional[str] = None, reading_time: int = 0):
        """更新阅读进度"""
        self.current_chapter_id = chapter_id
        self.chapters_read += 1
        self.total_reading_time += reading_time
        if choice_id:
            self.last_choice_id = choice_id
    
    def complete_story(self, rating: Optional[int] = None):
        """完成故事"""
        self.is_completed = True
        if rating:
            self.user_rating = rating
    
    def bookmark(self):
        """收藏故事"""
        self.is_bookmarked = True
    
    def unbookmark(self):
        """取消收藏"""
        self.is_bookmarked = False
    
    def get_progress_percentage(self, total_chapters: int) -> float:
        """获取进度百分比"""
        if total_chapters == 0:
            return 0.0
        return min(100.0, (self.chapters_read / total_chapters) * 100)
    
    def __repr__(self):
        return f"<UserStoryProgress(user_id={self.user_id}, story_id={self.story_id})>"
