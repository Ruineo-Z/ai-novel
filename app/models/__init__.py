"""
AI互动小说 - 数据模型模块
导入所有数据模型以确保SQLAlchemy能够发现它们
"""

# 导入基础模型
from app.models.base import (
    BaseModel,
    StandardModel,
    VersionedModel,
    StatusModel,
    FullModel,
    TimestampMixin,
    UUIDMixin,
    SoftDeleteMixin,
    MetadataMixin,
    VersionMixin,
    StatusMixin
)

# 导入业务模型
from app.models.user import User
from app.models.story import Story, StoryTheme, StoryStatus, StoryDifficulty
from app.models.chapter import Chapter, ChapterStatus, GenerationMethod
from app.models.choice import Choice, UserStoryProgress
from app.models.memory import StoryMemory, MemoryType, MemoryImportance

# 导出所有模型类
__all__ = [
    # 基础模型
    "BaseModel",
    "StandardModel",
    "VersionedModel",
    "StatusModel",
    "FullModel",
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    "MetadataMixin",
    "VersionMixin",
    "StatusMixin",

    # 业务模型
    "User",
    "Story",
    "Chapter",
    "Choice",
    "UserStoryProgress",
    "StoryMemory",

    # 枚举类型
    "StoryTheme",
    "StoryStatus",
    "StoryDifficulty",
    "ChapterStatus",
    "GenerationMethod",
    "MemoryType",
    "MemoryImportance"
]