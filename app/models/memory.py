"""
AI互动小说 - 故事记忆模型
用于存储故事上下文和AI生成记忆
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import StandardModel


class MemoryType(str, Enum):
    """记忆类型枚举"""
    CHARACTER = "character"      # 角色记忆
    PLOT = "plot"               # 情节记忆
    WORLD = "world"             # 世界观记忆
    CHOICE = "choice"           # 选择记忆
    EMOTION = "emotion"         # 情感记忆
    SETTING = "setting"         # 场景记忆


class MemoryImportance(str, Enum):
    """记忆重要性枚举"""
    LOW = "low"                 # 低重要性
    MEDIUM = "medium"           # 中等重要性
    HIGH = "high"               # 高重要性
    CRITICAL = "critical"       # 关键重要性


class StoryMemory(StandardModel):
    """故事记忆模型"""
    
    __tablename__ = "story_memories"
    
    # 基本信息
    title = Column(
        String(200),
        nullable=False,
        comment="记忆标题"
    )
    
    content = Column(
        Text,
        nullable=False,
        comment="记忆内容"
    )
    
    summary = Column(
        Text,
        nullable=True,
        comment="记忆摘要"
    )
    
    # 关联信息
    story_id = Column(
        String(36),
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属故事ID"
    )
    
    chapter_id = Column(
        String(36),
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联章节ID"
    )
    
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="关联用户ID"
    )
    
    # 记忆属性
    memory_type = Column(
        SQLEnum(MemoryType),
        nullable=False,
        default=MemoryType.PLOT,
        index=True,
        comment="记忆类型"
    )
    
    importance = Column(
        SQLEnum(MemoryImportance),
        nullable=False,
        default=MemoryImportance.MEDIUM,
        index=True,
        comment="重要性级别"
    )
    
    # 向量化信息
    embedding_vector = Column(
        Text,
        nullable=True,
        comment="嵌入向量(JSON格式)"
    )
    
    similarity_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="相似度分数"
    )
    
    # 使用统计
    access_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="访问次数"
    )
    
    last_accessed_at = Column(
        String(50),
        nullable=True,
        comment="最后访问时间"
    )
    
    # 标签和关键词
    tags = Column(
        Text,
        nullable=True,
        comment="标签(逗号分隔)"
    )
    
    keywords = Column(
        Text,
        nullable=True,
        comment="关键词(逗号分隔)"
    )
    
    # AI相关
    ai_generated = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否AI生成"
    )
    
    ai_model_used = Column(
        String(50),
        nullable=True,
        comment="使用的AI模型"
    )
    
    # 有效性
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )
    
    expires_at = Column(
        String(50),
        nullable=True,
        comment="过期时间"
    )
    
    # 关系
    story = relationship(
        "Story",
        back_populates="story_memories"
    )
    
    chapter = relationship(
        "Chapter",
        foreign_keys=[chapter_id]
    )
    
    user = relationship(
        "User",
        foreign_keys=[user_id]
    )
    
    # 索引
    __table_args__ = (
        Index('idx_memory_story_type', 'story_id', 'memory_type'),
        Index('idx_memory_importance', 'importance'),
        Index('idx_memory_chapter', 'chapter_id'),
        Index('idx_memory_access_count', 'access_count'),
        Index('idx_memory_similarity', 'similarity_score'),
        Index('idx_memory_active', 'is_active'),
    )
    
    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if not self.expires_at:
            return False
        
        try:
            expire_time = datetime.fromisoformat(self.expires_at)
            return datetime.utcnow() > expire_time
        except (ValueError, TypeError):
            return False
    
    @property
    def is_valid(self) -> bool:
        """是否有效"""
        return self.is_active and not self.is_expired and not self.is_deleted
    
    def access(self):
        """记录访问"""
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow().isoformat()
    
    def set_embedding(self, vector: List[float]):
        """设置嵌入向量"""
        import json
        self.embedding_vector = json.dumps(vector)
    
    def get_embedding(self) -> Optional[List[float]]:
        """获取嵌入向量"""
        if not self.embedding_vector:
            return None
        
        try:
            import json
            return json.loads(self.embedding_vector)
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_tags(self, tags: List[str]):
        """设置标签"""
        self.tags = ",".join(tags) if tags else None
    
    def get_tags(self) -> List[str]:
        """获取标签列表"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
    
    def set_keywords(self, keywords: List[str]):
        """设置关键词"""
        self.keywords = ",".join(keywords) if keywords else None
    
    def get_keywords(self) -> List[str]:
        """获取关键词列表"""
        if not self.keywords:
            return []
        return [kw.strip() for kw in self.keywords.split(",") if kw.strip()]
    
    def add_tag(self, tag: str):
        """添加标签"""
        current_tags = self.get_tags()
        if tag not in current_tags:
            current_tags.append(tag)
            self.set_tags(current_tags)
    
    def remove_tag(self, tag: str):
        """移除标签"""
        current_tags = self.get_tags()
        if tag in current_tags:
            current_tags.remove(tag)
            self.set_tags(current_tags)
    
    def set_expiry(self, days: int):
        """设置过期时间"""
        from datetime import timedelta
        expire_time = datetime.utcnow() + timedelta(days=days)
        self.expires_at = expire_time.isoformat()
    
    def extend_expiry(self, days: int):
        """延长过期时间"""
        if self.expires_at:
            try:
                current_expire = datetime.fromisoformat(self.expires_at)
                from datetime import timedelta
                new_expire = current_expire + timedelta(days=days)
                self.expires_at = new_expire.isoformat()
            except (ValueError, TypeError):
                self.set_expiry(days)
        else:
            self.set_expiry(days)
    
    def deactivate(self):
        """停用记忆"""
        self.is_active = False
    
    def activate(self):
        """激活记忆"""
        self.is_active = True
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        return {
            "access_count": self.access_count,
            "last_accessed_at": self.last_accessed_at,
            "is_popular": self.access_count > 10,
            "memory_type": self.memory_type.value if self.memory_type else None,
            "importance": self.importance.value if self.importance else None
        }
    
    def to_dict(self, include_vector: bool = False) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "story_id": self.story_id,
            "chapter_id": self.chapter_id,
            "user_id": self.user_id,
            "memory_type": self.memory_type.value if self.memory_type else None,
            "importance": self.importance.value if self.importance else None,
            "similarity_score": self.similarity_score,
            "access_count": self.access_count,
            "last_accessed_at": self.last_accessed_at,
            "tags": self.get_tags(),
            "keywords": self.get_keywords(),
            "ai_generated": self.ai_generated,
            "ai_model_used": self.ai_model_used,
            "is_active": self.is_active,
            "expires_at": self.expires_at,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_vector:
            result["embedding_vector"] = self.get_embedding()
        
        return result
    
    def __repr__(self):
        return f"<StoryMemory(id={self.id}, story_id={self.story_id}, type={self.memory_type})>"
