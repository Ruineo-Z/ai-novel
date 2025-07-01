"""
角色提取Agent

从章节内容中智能提取角色信息，包括：
- 识别所有出场角色
- 分析角色重要性
- 提取角色行为和对话
- 分类角色类型
"""

import re
import json
from typing import List, Dict, Any, Optional
from llama_index.core.prompts import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from app.novel_generation.llm_config import gemini_llm
from app.schemas.agent_outputs import ProtagonistGenerationOutput, WorldSettingOutput
from app.core.logger import get_logger
from .models import (
    ExtractedCharacter, 
    CharacterType, 
    EnrichedCharacter
)

logger = get_logger(__name__)


class CharacterExtractionAgent:
    """角色提取Agent"""
    
    def __init__(self):
        self.llm = gemini_llm()
        
    async def extract_characters_from_chapter(
        self, 
        chapter_content: str,
        protagonist: ProtagonistGenerationOutput,
        world_setting: WorldSettingOutput,
        chapter_number: int = 1
    ) -> List[ExtractedCharacter]:
        """从章节中提取所有角色信息"""
        
        try:
            # 构建提取prompt
            extraction_prompt = self._build_extraction_prompt(
                chapter_content, protagonist, world_setting
            )
            
            # 使用LLM提取角色信息
            extracted_data = await self._llm_extract_characters(extraction_prompt)
            
            # 解析和验证提取结果
            characters = self._parse_extraction_result(extracted_data, chapter_number)
            
            # 确保主角包含在结果中
            characters = self._ensure_protagonist_included(characters, protagonist, chapter_number)
            
            logger.info(f"从章节{chapter_number}中提取到{len(characters)}个角色")
            return characters
            
        except Exception as e:
            logger.error(f"角色提取失败: {e}")
            # 返回至少包含主角的基本结果
            return [self._create_protagonist_character(protagonist, chapter_number)]
    
    def _build_extraction_prompt(
        self, 
        chapter_content: str,
        protagonist: ProtagonistGenerationOutput,
        world_setting: WorldSettingOutput
    ) -> str:
        """构建角色提取prompt"""
        
        prompt = f"""
你是一个专业的小说角色分析专家。请从以下章节内容中提取所有出场的角色信息。

## 世界设定背景
世界名称: {world_setting.world_name}
世界描述: {world_setting.world_description}
力量体系: {world_setting.power_system}

## 主角信息
主角姓名: {protagonist.name}
主角背景: {protagonist.background}

## 章节内容
{chapter_content}

## 提取要求
请提取章节中所有出场的角色，包括：
1. 直接出场并有对话或行为的角色
2. 被提及但未直接出场的重要角色
3. 背景角色（如路人、店主等）

对每个角色，请分析：
- 姓名（如果没有明确姓名，请根据描述给出合理的称呼）
- 在章节中被提及的次数
- 角色描述（外貌、身份、特征等）
- 具体行为（角色在章节中做了什么）
- 对话内容（如果有的话）
- 角色类型：protagonist（主角）、major（主要角色）、minor（次要角色）、background（背景角色）
- 重要性评分（0-1，1为最重要）

请以JSON格式返回结果，格式如下：
{{
    "characters": [
        {{
            "name": "角色姓名",
            "mentions": 提及次数,
            "description": "角色描述",
            "actions": ["行为1", "行为2"],
            "dialogue": ["对话1", "对话2"],
            "character_type": "角色类型",
            "importance_score": 重要性评分
        }}
    ]
}}

注意：
- 确保主角 {protagonist.name} 包含在结果中
- 重要性评分要合理，主角应该是1.0
- 对话要保持原文，行为要具体描述
- 角色类型要准确分类
"""
        return prompt
    
    async def _llm_extract_characters(self, prompt: str) -> Dict[str, Any]:
        """使用LLM提取角色信息"""
        
        messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
        
        try:
            response = await self.llm.achat(messages)
            content = response.message.content
            
            # 尝试解析JSON
            # 清理可能的markdown格式
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            # 尝试使用正则表达式提取JSON部分
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            # 如果都失败了，返回空结果
            return {"characters": []}
    
    def _parse_extraction_result(
        self, 
        extracted_data: Dict[str, Any], 
        chapter_number: int
    ) -> List[ExtractedCharacter]:
        """解析提取结果为ExtractedCharacter对象"""
        
        characters = []
        
        for char_data in extracted_data.get("characters", []):
            try:
                # 验证和清理数据
                character = ExtractedCharacter(
                    name=char_data.get("name", "未知角色"),
                    mentions=max(1, char_data.get("mentions", 1)),
                    description=char_data.get("description", ""),
                    actions=char_data.get("actions", []),
                    dialogue=char_data.get("dialogue", []),
                    character_type=CharacterType(char_data.get("character_type", "background")),
                    importance_score=min(1.0, max(0.0, char_data.get("importance_score", 0.1)))
                )
                characters.append(character)
                
            except Exception as e:
                logger.warning(f"解析角色数据失败: {e}, 数据: {char_data}")
                continue
        
        return characters
    
    def _ensure_protagonist_included(
        self, 
        characters: List[ExtractedCharacter],
        protagonist: ProtagonistGenerationOutput,
        chapter_number: int
    ) -> List[ExtractedCharacter]:
        """确保主角包含在提取结果中"""
        
        # 检查是否已包含主角
        protagonist_found = False
        for char in characters:
            if char.name == protagonist.name or char.character_type == CharacterType.PROTAGONIST:
                protagonist_found = True
                # 确保主角类型正确
                char.character_type = CharacterType.PROTAGONIST
                char.importance_score = 1.0
                break
        
        # 如果没有找到主角，添加主角
        if not protagonist_found:
            protagonist_char = self._create_protagonist_character(protagonist, chapter_number)
            characters.insert(0, protagonist_char)
        
        return characters
    
    def _create_protagonist_character(
        self, 
        protagonist: ProtagonistGenerationOutput,
        chapter_number: int
    ) -> ExtractedCharacter:
        """创建主角的ExtractedCharacter对象"""
        
        return ExtractedCharacter(
            name=protagonist.name,
            mentions=5,  # 假设主角被提及多次
            description=f"{protagonist.appearance}。{protagonist.personality}",
            actions=["作为主角出场"],
            dialogue=["主角对话"],
            character_type=CharacterType.PROTAGONIST,
            importance_score=1.0
        )
    
    async def enrich_character_data(
        self,
        character: ExtractedCharacter,
        protagonist: ProtagonistGenerationOutput,
        world_setting: WorldSettingOutput,
        chapter_number: int = 1
    ) -> EnrichedCharacter:
        """基于主人公信息丰富其他角色数据"""
        
        try:
            if character.character_type == CharacterType.PROTAGONIST:
                # 主角直接使用已有详细信息
                return self._enrich_protagonist(character, protagonist, chapter_number)
            else:
                # 其他角色需要AI生成详细信息
                return await self._enrich_other_character(
                    character, protagonist, world_setting, chapter_number
                )
                
        except Exception as e:
            logger.error(f"丰富角色数据失败: {e}")
            # 返回基本的丰富角色信息
            return self._create_basic_enriched_character(character, chapter_number)
    
    def _enrich_protagonist(
        self, 
        character: ExtractedCharacter,
        protagonist: ProtagonistGenerationOutput,
        chapter_number: int
    ) -> EnrichedCharacter:
        """丰富主角信息"""
        
        return EnrichedCharacter(
            name=protagonist.name,
            character_type=CharacterType.PROTAGONIST,
            age=protagonist.age,
            gender=protagonist.gender,
            appearance=protagonist.appearance,
            personality=protagonist.personality,
            background=protagonist.background,
            abilities=protagonist.initial_abilities,
            goals=protagonist.goals,
            weaknesses=protagonist.weaknesses,
            special_traits=protagonist.special_traits,
            importance_level=10,
            first_appearance_chapter=chapter_number,
            mentions_count=character.mentions,
            dialogue_samples=character.dialogue[:3],  # 保留前3个对话样本
            action_samples=character.actions[:3]  # 保留前3个行为样本
        )

    async def _enrich_other_character(
        self,
        character: ExtractedCharacter,
        protagonist: ProtagonistGenerationOutput,
        world_setting: WorldSettingOutput,
        chapter_number: int
    ) -> EnrichedCharacter:
        """使用AI丰富其他角色的详细信息"""

        enrichment_prompt = f"""
你是一个专业的小说角色设计师。请基于以下信息，为角色生成完整的详细信息。

## 世界设定
世界名称: {world_setting.world_name}
世界描述: {world_setting.world_description}
力量体系: {world_setting.power_system}

## 主角参考信息
主角姓名: {protagonist.name}
主角年龄: {protagonist.age}
主角性别: {protagonist.gender}
主角背景: {protagonist.background}

## 待丰富的角色信息
姓名: {character.name}
描述: {character.description}
角色类型: {character.character_type.value}
重要性: {character.importance_score}
行为: {character.actions}
对话: {character.dialogue}

## 生成要求
请为这个角色生成完整的信息，要求：
1. 与世界设定和主角信息保持一致
2. 符合角色的重要性等级
3. 性格和背景要合理
4. 能力要符合世界的力量体系

请以JSON格式返回：
{{
    "age": 年龄,
    "gender": "性别",
    "appearance": "外貌描述",
    "personality": "性格特点",
    "background": "背景故事",
    "abilities": ["能力1", "能力2"],
    "goals": ["目标1", "目标2"],
    "weaknesses": ["弱点1", "弱点2"],
    "special_traits": "特殊特质",
    "importance_level": 重要程度1-10
}}
"""

        try:
            messages = [ChatMessage(role=MessageRole.USER, content=enrichment_prompt)]
            response = await self.llm.achat(messages)
            content = response.message.content

            # 清理和解析JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]

            enriched_data = json.loads(content)

            # 创建丰富的角色对象
            return EnrichedCharacter(
                name=character.name,
                character_type=character.character_type,
                age=enriched_data.get("age"),
                gender=enriched_data.get("gender"),
                appearance=enriched_data.get("appearance", character.description),
                personality=enriched_data.get("personality", ""),
                background=enriched_data.get("background", ""),
                abilities=enriched_data.get("abilities", []),
                goals=enriched_data.get("goals", []),
                weaknesses=enriched_data.get("weaknesses", []),
                special_traits=enriched_data.get("special_traits"),
                importance_level=min(10, max(1, enriched_data.get("importance_level",
                    int(character.importance_score * 10)))),
                first_appearance_chapter=chapter_number,
                mentions_count=character.mentions,
                dialogue_samples=character.dialogue[:3],
                action_samples=character.actions[:3]
            )

        except Exception as e:
            logger.error(f"AI丰富角色信息失败: {e}")
            return self._create_basic_enriched_character(character, chapter_number)

    def _create_basic_enriched_character(
        self,
        character: ExtractedCharacter,
        chapter_number: int
    ) -> EnrichedCharacter:
        """创建基本的丰富角色信息（作为fallback）"""

        return EnrichedCharacter(
            name=character.name,
            character_type=character.character_type,
            appearance=character.description or "外貌未详细描述",
            personality="性格待发展",
            background="背景待补充",
            abilities=["基础能力"],
            goals=["未明确目标"],
            weaknesses=["未知弱点"],
            importance_level=max(1, int(character.importance_score * 10)),
            first_appearance_chapter=chapter_number,
            mentions_count=character.mentions,
            dialogue_samples=character.dialogue[:3],
            action_samples=character.actions[:3]
        )
