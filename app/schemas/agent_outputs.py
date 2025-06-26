import json

from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.base import Choice, NovelStyle


class WorldSettingOutput(BaseModel):
    """世界观生成输出"""
    world_setting: str = Field(description="完整的世界观")
    world_name: str = Field(description="世界名称")
    world_description: str = Field(description="世界背景描述")
    power_system: Optional[str] = Field(description="力量体系（修仙、科技等）")
    main_locations: List[str] = Field(description="主要地点")
    key_factions: List[str] = Field(description="重要势力")
    world_rules: List[str] = Field(description="世界规则")


class CharacterOutput(BaseModel):
    """小说人物基类"""
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    gender: str = Field(description="性别")
    appearance: str = Field(description="外貌描述")
    personality: str = Field(description="性格特点")
    background: str = Field(description="背景故事")
    initial_abilities: List[str] = Field(description="初始能力")
    goals: List[str] = Field(description="目标")
    weaknesses: List[str] = Field(description="弱点")
    special_traits: Optional[str] = Field(description="特殊特质")


class ProtagonistGenerationOutput(CharacterOutput):
    """主人公生成输出"""
    starting_scenario: str = Field(description="开局场景")

  
class ChapterOutput(BaseModel):
    """章节内容生成输出"""
    chapter_title: str = Field(description="章节标题")
    chapter_content: str = Field(description="章节内容")
    story_summary: str = Field(description="剧情摘要")
    character_development: Optional[str] = Field(description="角色发展")
    world_expansion: Optional[str] = Field(description="世界观扩展")
    choices: List[Choice] = Field(description="用户选择项")
    is_critical_moment: bool = Field(description="是否为关键节点")
    is_ending: bool = Field(default=False, description="是否为结局")
