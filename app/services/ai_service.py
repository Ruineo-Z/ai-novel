from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.schemas.base import NovelStyle, ProtagonistInfo
from app.schemas.agent_outputs import WorldSettingOutput, ChapterOutput, ProtagonistGenerationOutput, \
    ChoiceConsequenceOutput


class AIService(ABC):
    """AI服务基类"""

    @abstractmethod
    async def generate_world_setting(
            self,
            novel_style: NovelStyle,
            protagonist: Optional[ProtagonistInfo] = None
    ) -> WorldSettingOutput:
        """生成世界观设置"""
        pass

    @abstractmethod
    async def generate_protagonist(
            self,
            novel_style: NovelStyle,
            world_setting: str
    ) -> ProtagonistGenerationOutput:
        """生成主人公"""
        pass

    @abstractmethod
    async def generate_chapter(
            self,
            novel_style: NovelStyle,
            world_setting: str,
            protagonist: ProtagonistInfo,
            story_history: list,
            choice_history: list,
            chapter_number: int
    ) -> ChapterOutput:
        """生成章节内容"""
        pass

    @abstractmethod
    async def analyze_choice_consequence(
            self,
            choice_text: str,
            current_context: str,
            story_history: list
    ) -> ChoiceConsequenceOutput:
        """分析选择后果"""
        pass

    def _build_context(self, **kwargs) -> str:
        """构建上下文信息"""
        context_parts = []

        if 'novel_style' in kwargs:
            context_parts.append(f"小说风格: {kwargs['novel_style']}")

        if 'world_setting' in kwargs:
            context_parts.append(f"世界设定: {kwargs['world_setting']}")

        if 'protagonist' in kwargs and kwargs['protagonist']:
            p = kwargs['protagonist']
            protagonist_info = f"主人公: {p.name or '未命名'}"
            if p.background:
                protagonist_info += f", 背景: {p.background}"
            if p.personality:
                protagonist_info += f", 性格: {p.personality}"
            context_parts.append(protagonist_info)

        if 'story_history' in kwargs and kwargs['story_history']:
            context_parts.append("故事历史:")
            for i, story in enumerate(kwargs['story_history'][-3:], 1):  # 只取最近3个
                context_parts.append(f"{i}. {story}")

        return "\n".join(context_parts)
