import google.generativeai as genai
import json
from typing import Optional
from app.core.config import settings
from app.schemas.base import NovelStyle, ProtagonistInfo
from app.schemas.agent_outputs import WorldSettingOutput, ChapterOutput, ProtagonistGenerationOutput, \
    ChoiceConsequenceOutput, Choice
from app.services.ai_service import AIService


class GeminiService(AIService):
    """Gemini AI服务实现"""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")

        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')

    async def generate_world_setting(
            self,
            novel_style: NovelStyle,
            protagonist: Optional[ProtagonistInfo] = None
    ) -> WorldSettingOutput:
        """生成世界观设置"""

        prompt = f"""
你是一个专业的{novel_style}小说世界观设计师。请为一个{novel_style}风格的互动小说创建详细的世界观设置。

要求：
1. 创造一个独特且引人入胜的世界
2. 确保世界观与{novel_style}风格相符
3. 提供丰富的背景设定供后续剧情发展

{f'主人公信息: {protagonist.name or "未命名"}, 背景: {protagonist.background or "普通人"}' if protagonist else '主人公将在后续生成'}

请以JSON格式返回，包含以下字段：
{{
    "world_name": "世界名称",
    "world_description": "详细的世界背景描述(200-300字)",
    "power_system": "力量体系描述",
    "main_locations": ["地点1", "地点2", "地点3"],
    "key_factions": ["势力1", "势力2", "势力3"],
    "world_rules": ["规则1", "规则2", "规则3"],
    "starting_scenario": "开局场景描述(100-150字)"
}}
"""

        response = await self._generate_content(prompt)
        return WorldSettingOutput.model_validate(response)

    async def generate_protagonist(
            self,
            novel_style: NovelStyle,
            world_setting: str
    ) -> ProtagonistGenerationOutput:
        """生成主人公"""

        prompt = f"""
你是一个专业的{novel_style}小说角色设计师。请为以下世界观创建一个适合的主人公。

世界设定：
{world_setting}

要求：
1. 角色要符合{novel_style}风格
2. 具有成长潜力和吸引力
3. 适合互动小说的主角设定

请以JSON格式返回：
{{
    "name": "角色姓名",
    "age": 年龄数字,
    "gender": "性别",
    "appearance": "外貌描述",
    "personality": "性格特点",
    "background": "背景故事",
    "initial_abilities": ["能力1", "能力2"],
    "goals": ["目标1", "目标2"],
    "weaknesses": ["弱点1", "弱点2"],
    "special_traits": "特殊特质"
}}
"""

        response = await self._generate_content(prompt)
        return ProtagonistGenerationOutput.model_validate(response)

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

        context = self._build_context(
            novel_style=novel_style,
            world_setting=world_setting,
            protagonist=protagonist,
            story_history=story_history
        )

        choice_context = ""
        if choice_history:
            choice_context = f"\n上一章选择: {choice_history[-1].get('choice_text', '')}" if choice_history else ""

        prompt = f"""
你是一个专业的{novel_style}小说作家。请为互动小说写第{chapter_number}章。

{context}{choice_context}

要求：
1. 章节内容要生动有趣，符合{novel_style}风格
2. 长度控制在{settings.MAX_CHAPTER_LENGTH}字以内
3. 在关键节点提供{settings.MAX_CHOICES}个有意义的选择
4. 确保剧情连贯性和角色发展

请以JSON格式返回：
{{
    "chapter_title": "第{chapter_number}章 章节标题",
    "chapter_content": "章节正文内容",
    "story_summary": "本章剧情摘要",
    "character_development": "角色发展描述",
    "world_expansion": "世界观扩展",
    "choices": [
        {{"id": 1, "text": "选择1", "description": "选择描述"}},
        {{"id": 2, "text": "选择2", "description": "选择描述"}},
        {{"id": 3, "text": "选择3", "description": "选择描述"}}
    ],
    "is_critical_moment": true/false,
    "is_ending": false
}}
"""

        response = await self._generate_content(prompt)
        return ChapterOutput.model_validate(response)

    async def analyze_choice_consequence(
            self,
            choice_text: str,
            current_context: str,
            story_history: list
    ) -> ChoiceConsequenceOutput:
        """分析选择后果"""

        prompt = f"""
你是一个专业的剧情分析师。请分析以下选择的可能后果：

当前情况：{current_context}
用户选择：{choice_text}
故事历史：{story_history[-2:] if len(story_history) >= 2 else story_history}

请以JSON格式返回分析结果：
{{
    "immediate_consequence": "直接后果描述",
    "long_term_impact": "长期影响分析",
    "character_change": "角色变化",
    "relationship_change": "关系变化",
    "plot_direction": "剧情走向"
}}
"""

        response = await self._generate_content(prompt)
        return ChoiceConsequenceOutput.model_validate(response)

    async def _generate_content(self, prompt: str) -> dict:
        """生成内容并解析JSON"""
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()

            # 尝试提取JSON部分
            if '```json' in content:
                start = content.find('```json') + 7
                end = content.find('```', start)
                content = content[start:end].strip()
            elif '```' in content:
                start = content.find('```') + 3
                end = content.find('```', start)
                content = content[start:end].strip()

            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}")
        except Exception as e:
            raise ValueError(f"AI generation failed: {e}")
