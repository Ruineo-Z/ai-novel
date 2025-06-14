from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.base import NovelStyle, ProtagonistInfo, AIModel, ChapterContent
from app.schemas.agent_outputs import WorldSettingOutput, ChapterOutput


# Request Models
class CreateNovelRequest(BaseModel):
    novel_style: NovelStyle = Field(description="小说风格")
    ai_model: AIModel = Field(default=AIModel.GEMINI, description="AI模型选择")
    use_custom_protagonist: bool = Field(default=False, description="是否自定义主人公")
    protagonist_info: Optional[ProtagonistInfo] = Field(default=None, description="主人公信息")


class MakeChoiceRequest(BaseModel):
    session_id: str = Field(description="会话ID")
    choice_id: int = Field(description="选择ID")
    custom_action: Optional[str] = Field(default=None, description="自定义行动")


class ContinueStoryRequest(BaseModel):
    session_id: str = Field(description="会话ID")


# Response Models
class CreateNovelResponse(BaseModel):
    session_id: str = Field(description="会话ID")
    world_setting: WorldSettingOutput = Field(description="世界观设置")
    first_chapter: ChapterOutput = Field(description="第一章内容")
    protagonist_info: ProtagonistInfo = Field(description="主人公信息")


class ChapterResponse(BaseModel):
    session_id: str = Field(description="会话ID")
    chapter: ChapterOutput = Field(description="章节内容")
    current_chapter_number: int = Field(description="当前章节号")
    total_chapters: int = Field(description="总章节数")


class NovelStatusResponse(BaseModel):
    session_id: str = Field(description="会话ID")
    novel_style: NovelStyle = Field(description="小说风格")
    current_chapter: int = Field(description="当前章节")
    protagonist_name: Optional[str] = Field(description="主人公姓名")
    world_name: Optional[str] = Field(description="世界名称")
    is_completed: bool = Field(description="是否完成")
    story_summary: str = Field(description="故事摘要")


class ErrorResponse(BaseModel):
    error: str = Field(description="错误信息")
    detail: Optional[str] = Field(description="详细信息")


class AvailableStylesResponse(BaseModel):
    styles: List[NovelStyle] = Field(description="可用的小说风格")
    descriptions: dict = Field(description="风格描述")
