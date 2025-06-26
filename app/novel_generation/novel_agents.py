import json
import re

from typing import Dict, Any
from app.novel_generation import llm_config
from app.schemas.agent_outputs import (
    WorldSettingOutput,
    ProtagonistGenerationOutput,
    ChapterOutput,
)
from app.schemas.base import NovelStyle
from app.core.logger import get_logger

logger = get_logger(__name__)


class NovelAgentTools:
    """小说创作工具集合"""

    def __init__(self, novel_style: NovelStyle):
        self.novel_style = novel_style
        self.style_value = novel_style.value
        self.llm = llm_config.gemini_llm()

    async def generate_world_setting(self) -> WorldSettingOutput:
        """生成世界观设定"""
        prompt = f"""
        为{self.style_value}类型的小说创建一个完整且引人入胜的世界观设定。
        
        任务要求：
        1. 创建世界名称和背景描述
        2. 设计力量体系（如修仙境界、科技等级、武功体系等）
        3. 规划主要地点和地理环境
        4. 设定重要势力和组织
        5. 制定世界运行规则和法则
        
        请确保世界观设定符合{self.style_value}小说的特点和读者期待。
        禁止生成任何人物信息。
        
        请以JSON格式返回结果，包含以下字段：
        - world_setting: 完整的世界观描述
        - world_name: 世界名称
        - world_description: 世界背景描述
        - power_system: 力量体系
        - main_locations: 主要地点列表
        - key_factions: 重要势力列表
        - world_rules: 世界规则列表
        """

        try:
            response = await self.llm.acomplete(prompt)
            response_text = str(response)

            # Try to extract JSON from the response
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed_data = json.loads(json_match.group())
                    return WorldSettingOutput(
                        world_setting=parsed_data.get("world_setting", f"一个充满{self.style_value}色彩的奇幻世界"),
                        world_name=parsed_data.get("world_name", f"{self.style_value}世界"),
                        world_description=parsed_data.get("world_description", "一个充满奇幻色彩的世界"),
                        power_system=parsed_data.get("power_system", "基础力量体系"),
                        main_locations=parsed_data.get("main_locations", ["主城", "野外"]),
                        key_factions=parsed_data.get("key_factions", ["正义联盟", "邪恶势力"]),
                        world_rules=parsed_data.get("world_rules", ["基本规则1", "基本规则2"])
                    )
                except json.JSONDecodeError:
                    pass

            # Fallback: extract information using regex patterns
            world_name_match = re.search(r'世界名称[：:](.*?)(?:\n|$)', response_text)
            world_name = world_name_match.group(1).strip() if world_name_match else f"{self.style_value}世界"

            world_desc_match = re.search(r'世界描述[：:](.*?)(?:\n|世界规则)', response_text, re.DOTALL)
            world_description = world_desc_match.group(1).strip() if world_desc_match else "一个充满奇幻色彩的世界"

            return WorldSettingOutput(
                world_setting=f"一个充满{self.style_value}色彩的奇幻世界",
                world_name=world_name,
                world_description=world_description,
                power_system="基础力量体系",
                main_locations=["主城", "野外"],
                key_factions=["正义联盟", "邪恶势力"],
                world_rules=["基本规则1", "基本规则2"]
            )
        except Exception as e:
            logger.error(f"世界观生成失败: {str(e)}")
            return WorldSettingOutput(
                world_setting=f"默认{self.style_value}世界观",
                world_name=f"{self.style_value}世界",
                world_description="一个充满奇幻色彩的世界",
                power_system="基础力量体系",
                main_locations=["主城", "野外"],
                key_factions=["正义联盟", "邪恶势力"],
                world_rules=["基本规则1", "基本规则2"]
            )

    async def generate_protagonist(self, world_setting: WorldSettingOutput) -> ProtagonistGenerationOutput:
        """生成主人公信息"""
        prompt = f"""
        基于世界观设定，为{self.style_value}小说创造一个主人公角色：
        
        世界观：
        - 世界名称：{world_setting.world_name}
        - 世界描述：{world_setting.world_description}
        - 力量体系：{world_setting.power_system}
        - 主要地点：{', '.join(world_setting.main_locations)}
        - 重要势力：{', '.join(world_setting.key_factions)}
        
        任务要求：
        1. 创造符合世界观的主人公形象
        2. 设定合理的年龄、性别、外貌
        3. 设计独特的性格特点和背景故事
        4. 规划初始能力和成长目标
        5. 设定角色弱点和特殊特质
        6. 创造引人入胜的开局场景
        
        确保角色与世界观完美融合，具有成长潜力和读者吸引力。
        
        请以JSON格式返回结果。
        """

        try:
            response = await self.llm.acomplete(prompt)
            response_text = str(response)

            # Try to extract JSON from the response
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed_data = json.loads(json_match.group())
                    return ProtagonistGenerationOutput(
                        name=parsed_data.get("name", "主角"),
                        age=parsed_data.get("age", 20),
                        gender=parsed_data.get("gender", "未知"),
                        appearance=parsed_data.get("appearance", "普通外貌"),
                        personality=parsed_data.get("personality", "勇敢、善良"),
                        background=parsed_data.get("background", "普通出身"),
                        initial_abilities=parsed_data.get("initial_abilities", ["基础能力"]),
                        goals=parsed_data.get("goals", ["成长", "冒险"]),
                        weaknesses=parsed_data.get("weaknesses", ["经验不足"]),
                        special_traits=parsed_data.get("special_traits", "潜力无限"),
                        starting_scenario=parsed_data.get("starting_scenario",
                                                          "在一个平凡的日子里，主角的命运即将发生改变")
                    )
                except json.JSONDecodeError:
                    pass

            # Fallback: extract information using regex patterns
            name_match = re.search(r'姓名[：:](.*?)(?:\n|$)', response_text)
            name = name_match.group(1).strip() if name_match else "主角"

            age_match = re.search(r'年龄[：:]([0-9]+)', response_text)
            age = int(age_match.group(1)) if age_match else 20

            background_match = re.search(r'背景[：:](.*?)(?:\n|性格)', response_text, re.DOTALL)
            background = background_match.group(1).strip() if background_match else "普通出身"

            return ProtagonistGenerationOutput(
                name=name,
                age=age,
                gender="未知",
                appearance="普通外貌",
                personality="勇敢、善良",
                background=background,
                initial_abilities=["基础能力"],
                goals=["成长", "冒险"],
                weaknesses=["经验不足"],
                special_traits="潜力无限",
                starting_scenario="在一个平凡的日子里，主角的命运即将发生改变"
            )
        except Exception as e:
            logger.error(f"主人公生成失败: {str(e)}")
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
                special_traits="潜力无限",
                starting_scenario="在一个平凡的日子里，主角的命运即将发生改变"
            )

    async def generate_chapter(self, world_setting: WorldSettingOutput,
                               protagonist: ProtagonistGenerationOutput) -> ChapterOutput:
        """生成章节内容"""
        prompt = f"""
        基于世界观和主人公信息，创作{self.style_value}小说的第一章内容：
        
        世界观：{world_setting.world_name} - {world_setting.world_description}
        主人公：{protagonist.name}，{protagonist.age}岁，{protagonist.personality}
        背景：{protagonist.background}
        开局场景：{protagonist.starting_scenario}
        
        任务要求：
        1. 创作引人入胜的章节标题
        2. 编写详细的章节内容（1500-2000字）
        3. 总结故事梗概
        4. 描述角色发展
        5. 扩展世界观
        6. 提供2-3个选择选项
        
        请以JSON格式返回结果。
        """

        try:
            response = await self.llm.acomplete(prompt)
            response_text = str(response)

            # Try to extract JSON from the response
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed_data = json.loads(json_match.group())
                    from app.schemas.base import Choice
                    return ChapterOutput(
                        chapter_title=parsed_data.get("chapter_title", "第一章：命运的开始"),
                        chapter_content=parsed_data.get("chapter_content", response_text),
                        story_summary=parsed_data.get("story_summary", "主角开始了他的冒险之旅"),
                        character_development=parsed_data.get("character_development", "主角初次展现潜力"),
                        world_expansion=parsed_data.get("world_expansion", "介绍了基本的世界设定"),
                        choices=[
                            Choice(text=choice.get("text", f"选择{i + 1}"),
                                   description=choice.get("description", f"描述{i + 1}"), id=i + 1)
                            for i, choice in enumerate(parsed_data.get("choices",
                                                                       [{"text": "选择A", "description": "描述A"},
                                                                        {"text": "选择B", "description": "描述B"}]))
                        ],
                        is_critical_moment=parsed_data.get("is_critical_moment", False),
                        is_ending=parsed_data.get("is_ending", False)
                    )
                except json.JSONDecodeError:
                    pass

            # Fallback: extract title and use full response as content
            title_match = re.search(r'(?:标题|章节标题|第.*?章)[：:](.*?)(?:\n|$)', response_text)
            title = title_match.group(1).strip() if title_match else "第一章：命运的开始"

            # Remove title from content if found
            content = response_text
            if title_match:
                content = response_text[title_match.end():].strip()

            from app.schemas.base import Choice
            return ChapterOutput(
                chapter_title=title,
                chapter_content=content if content else "这是一个关于冒险的故事...",
                story_summary="主角开始了他的冒险之旅",
                character_development="主角初次展现潜力",
                world_expansion="介绍了基本的世界设定",
                choices=[
                    Choice(text="选择A", description="描述A", id=1),
                    Choice(text="选择B", description="描述B", id=2)
                ],
                is_critical_moment=False,
                is_ending=False
            )
        except Exception as e:
            logger.error(f"章节生成失败: {str(e)}")
            from app.schemas.base import Choice
            return ChapterOutput(
                chapter_title="第一章：命运的开始",
                chapter_content="这是一个关于冒险的故事...",
                story_summary="主角开始了他的冒险之旅",
                character_development="主角初次展现潜力",
                world_expansion="介绍了基本的世界设定",
                choices=[
                    Choice(text="选择A", description="描述A", id=1),
                    Choice(text="选择B", description="描述B", id=2)
                ],
                is_critical_moment=False,
                is_ending=False
            )
