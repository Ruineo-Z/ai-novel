import httpx
import json
from typing import Optional

from app.core.config import settings
from app.schemas.base import NovelStyle, ProtagonistInfo
from app.schemas.agent_outputs import WorldSettingOutput, ChapterOutput, ProtagonistGenerationOutput, \
    ChoiceConsequenceOutput

from .ai_service import AIService


class OllamaService(AIService):
    """Ollama AI服务实现"""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_world_setting(
            self,
            novel_style: NovelStyle,
            protagonist: Optional[ProtagonistInfo] = None
    ) -> WorldSettingOutput:
        """生成世界观设置"""

        # 简化实现，返回默认值
        return WorldSettingOutput(
            world_name=f"{novel_style}世界",
            world_description=f"这是一个充满{novel_style}元素的奇幻世界，拥有独特的文化和传统。",
            power_system=f"{novel_style}力量体系",
            main_locations=["主城", "秘境", "边疆"],
            key_factions=["正派", "邪派", "中立势力"],
            world_rules=["基本规则1", "基本规则2", "基本规则3"],
            starting_scenario=f"在这个{novel_style}世界中，一个新的冒险即将开始..."
        )

    async def generate_protagonist(
            self,
            novel_style: NovelStyle,
            world_setting: str
    ) -> ProtagonistGenerationOutput:
        """生成主人公"""

        # 简化实现，返回默认值
        return ProtagonistGenerationOutput(
            name="主角",
            age=20,
            gender="未知",
            appearance="普通外貌",
            personality="勇敢、善良",
            background="普通出身",
            initial_abilities=["基础能力"],
            goals=["成长", "冒险"],
            weaknesses=["经验不足"],
            special_traits="潜力无限"
        )

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

        # 简化实现，返回默认章节
        from ..schemas.agent_outputs import Choice

        choices = [
            Choice(id=1, text="选择A", description="这是选择A的描述"),
            Choice(id=2, text="选择B", description="这是选择B的描述"),
            Choice(id=3, text="选择C", description="这是选择C的描述")
        ]

        return ChapterOutput(
            chapter_title=f"第{chapter_number}章 新的开始",
            chapter_content=f"这是第{chapter_number}章的内容。在这个{novel_style}世界中，{protagonist.name or '主角'}面临着新的挑战...",
            story_summary=f"第{chapter_number}章摘要",
            character_development="角色有所成长",
            world_expansion="世界观得到扩展",
            choices=choices,
            is_critical_moment=True,
            is_ending=False
        )

    async def analyze_choice_consequence(
            self,
            choice_text: str,
            current_context: str,
            story_history: list
    ) -> ChoiceConsequenceOutput:
        """分析选择后果"""

        # 简化实现，返回默认分析
        return ChoiceConsequenceOutput(
            immediate_consequence=f"选择'{choice_text}'的直接后果",
            long_term_impact="这个选择将对未来产生深远影响",
            character_change="角色性格有所变化",
            relationship_change="人际关系发生变化",
            plot_direction="剧情朝着新的方向发展"
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
