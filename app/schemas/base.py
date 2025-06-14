from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class NovelStyle(str, Enum):
    XIANXIA = "修仙"
    SCIFI = "科幻"
    URBAN = "都市"
    ROMANCE = "言情"
    WUXIA = "武侠"


class AIModel(str, Enum):
    GEMINI = "gemini"
    OLLAMA = "ollama"


class ProtagonistInfo(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    background: Optional[str] = None
    personality: Optional[str] = None
    special_abilities: Optional[str] = None


class Choice(BaseModel):
    id: int
    text: str
    description: Optional[str] = None


class ChapterContent(BaseModel):
    chapter_number: int
    title: str
    content: str
    choices: List[Choice]
    is_ending: bool = False


class NovelSession(BaseModel):
    session_id: str
    novel_style: NovelStyle
    protagonist: Optional[ProtagonistInfo] = None
    world_setting: Optional[str] = None
    current_chapter: int = 0
    story_history: List[str] = []
    choice_history: List[Dict[str, Any]] = []
    ai_model: AIModel = AIModel.GEMINI
