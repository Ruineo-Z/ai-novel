from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class StorySessionBase(BaseModel):
    current_chapter: int
    session_data: Optional[Dict[str, Any]] = None

class StorySessionCreate(StorySessionBase):
    novel_id: int

class StorySessionUpdate(BaseModel):
    current_chapter: Optional[int] = None
    session_data: Optional[Dict[str, Any]] = None

class StorySessionResponse(StorySessionBase):
    id: int
    user_id: int
    novel_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class GenerationRequest(BaseModel):
    """章节生成请求"""
    novel_id: int
    user_choice: Optional[str] = None
    model_preference: Optional[str] = "openai"  # openai, gemini, ollama
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1500

class GenerationResponse(BaseModel):
    """章节生成响应"""
    chapter_id: int
    content: str
    choices: List[str]
    word_count: int
    generation_time: float
    model_used: str
    quality_score: Optional[float] = None

class GenerationLogResponse(BaseModel):
    """生成日志响应"""
    id: int
    chapter_id: int
    model_used: str
    quality_score: Optional[float] = None
    generation_time: float
    token_usage: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True