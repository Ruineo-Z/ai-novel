from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class ProtagonistInfo(BaseModel):
    name: str
    gender: str
    age: Optional[int] = None
    background: Optional[str] = None
    personality: Optional[str] = None
    special_abilities: Optional[str] = None


class NovelBase(BaseModel):
    title: str
    genre: str
    world_setting: str
    protagonist_info: ProtagonistInfo


class NovelCreate(NovelBase):
    pass


class NovelUpdate(BaseModel):
    title: Optional[str] = None
    genre: Optional[str] = None
    world_setting: Optional[str] = None
    protagonist_info: Optional[ProtagonistInfo] = None
    status: Optional[str] = None


class ChapterBase(BaseModel):
    title: Optional[str] = None
    content: str
    choices: Optional[List[str]] = None
    user_choice: Optional[str] = None


class ChapterCreate(ChapterBase):
    pass


class ChapterResponse(ChapterBase):
    id: int
    novel_id: int
    chapter_number: int
    word_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class NovelResponse(NovelBase):
    id: int
    outline: Optional[str] = None
    status: str
    owner_id: int
    created_at: datetime
    updated_at: datetime
    chapters: Optional[List[ChapterResponse]] = None

    class Config:
        from_attributes = True


class NovelSummary(BaseModel):
    """小说摘要信息"""
    id: int
    title: str
    genre: str
    status: str
    chapter_count: int
    total_words: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
