"""
AI互动小说 - CRUD操作模块
导入所有CRUD操作类
"""

from app.crud.base import CRUDBase
from app.crud.user import CRUDUser, user
from app.crud.story import CRUDStory, story
from app.crud.chapter import CRUDChapter, chapter

# 导出所有CRUD类和实例
__all__ = [
    "CRUDBase",
    "CRUDUser",
    "CRUDStory", 
    "CRUDChapter",
    "user",
    "story",
    "chapter"
]
