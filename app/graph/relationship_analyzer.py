"""
关系分析Agent

分析角色间的关系，包括：
- 识别角色间的直接交互
- 推断关系类型和强度
- 分析情感倾向
- 提取关系证据
"""

import json
import re
from typing import List, Dict, Any, Tuple
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from app.novel_generation.llm_config import gemini_llm
from app.core.logger import get_logger
from .models import (
    ExtractedCharacter,
    CharacterRelationship,
    RelationshipType,
    SentimentType
)

logger = get_logger(__name__)


class RelationshipAnalyzer:
    """关系分析Agent"""
    
    def __init__(self):
        self.llm = gemini_llm()
    
    async def analyze_character_relationships(
        self, 
        chapter_content: str,
        characters: List[ExtractedCharacter],
        chapter_number: int = 1
    ) -> List[CharacterRelationship]:
        """分析角色间的关系"""
        
        try:
            if len(characters) < 2:
                logger.info("角色数量不足，无法分析关系")
                return []
            
            # 生成角色对组合
            character_pairs = self._generate_character_pairs(characters)
            
            # 分析每对角色的关系
            relationships = []
            for char1, char2 in character_pairs:
                relationship = await self._analyze_pair_relationship(
                    chapter_content, char1, char2, chapter_number
                )
                if relationship:
                    relationships.append(relationship)
            
            logger.info(f"分析出{len(relationships)}个角色关系")
            return relationships
            
        except Exception as e:
            logger.error(f"关系分析失败: {e}")
            return []
    
    def _generate_character_pairs(
        self, 
        characters: List[ExtractedCharacter]
    ) -> List[Tuple[ExtractedCharacter, ExtractedCharacter]]:
        """生成角色对组合"""
        
        pairs = []
        
        # 按重要性排序，优先分析重要角色间的关系
        sorted_characters = sorted(characters, key=lambda x: x.importance_score, reverse=True)
        
        for i in range(len(sorted_characters)):
            for j in range(i + 1, len(sorted_characters)):
                char1 = sorted_characters[i]
                char2 = sorted_characters[j]
                
                # 跳过重要性都很低的角色对
                if char1.importance_score < 0.3 and char2.importance_score < 0.3:
                    continue
                
                pairs.append((char1, char2))
        
        return pairs
    
    async def _analyze_pair_relationship(
        self,
        chapter_content: str,
        char1: ExtractedCharacter,
        char2: ExtractedCharacter,
        chapter_number: int
    ) -> CharacterRelationship:
        """分析两个角色间的关系"""
        
        # 构建关系分析prompt
        analysis_prompt = self._build_relationship_prompt(chapter_content, char1, char2)
        
        try:
            # 使用LLM分析关系
            relationship_data = await self._llm_analyze_relationship(analysis_prompt)
            
            # 解析分析结果
            if relationship_data and relationship_data.get("has_relationship", False):
                return self._parse_relationship_result(
                    relationship_data, char1, char2, chapter_number
                )
            
            return None
            
        except Exception as e:
            logger.error(f"分析角色关系失败 {char1.name} - {char2.name}: {e}")
            return None
    
    def _build_relationship_prompt(
        self,
        chapter_content: str,
        char1: ExtractedCharacter,
        char2: ExtractedCharacter
    ) -> str:
        """构建关系分析prompt"""
        
        prompt = f"""
你是一个专业的小说关系分析专家。请分析以下两个角色在章节中的关系。

## 角色1信息
姓名: {char1.name}
描述: {char1.description}
行为: {char1.actions}
对话: {char1.dialogue}

## 角色2信息  
姓名: {char2.name}
描述: {char2.description}
行为: {char2.actions}
对话: {char2.dialogue}

## 章节内容
{chapter_content}

## 分析要求
请分析这两个角色在章节中是否有关系，如果有关系，请分析：

1. 关系类型（从以下选择）：
   - family: 家族关系
   - friend: 朋友关系
   - enemy: 敌对关系
   - mentor: 师徒关系
   - ally: 盟友关系
   - rival: 竞争关系
   - love: 爱情关系
   - colleague: 同事关系
   - knows: 认识关系

2. 关系强度（0-1）：
   - 0.1-0.3: 微弱关系
   - 0.4-0.6: 一般关系
   - 0.7-0.9: 强烈关系
   - 1.0: 极强关系

3. 情感倾向：
   - positive: 正面
   - negative: 负面
   - neutral: 中性
   - complex: 复杂

4. 关系描述和证据

请以JSON格式返回：
{{
    "has_relationship": true/false,
    "relationship_type": "关系类型",
    "strength": 关系强度,
    "sentiment": "情感倾向",
    "description": "关系描述",
    "evidence": ["证据1", "证据2"]
}}

注意：
- 只有在章节中明确显示两个角色有交互或关联时才认为有关系
- 关系强度要基于实际交互程度
- 证据要引用章节中的具体内容
"""
        return prompt
    
    async def _llm_analyze_relationship(self, prompt: str) -> Dict[str, Any]:
        """使用LLM分析关系"""
        
        messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
        
        try:
            response = await self.llm.achat(messages)
            content = response.message.content
            
            # 清理和解析JSON
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            logger.error(f"关系分析JSON解析失败: {e}")
            # 尝试正则表达式提取
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            return {"has_relationship": False}
    
    def _parse_relationship_result(
        self,
        relationship_data: Dict[str, Any],
        char1: ExtractedCharacter,
        char2: ExtractedCharacter,
        chapter_number: int
    ) -> CharacterRelationship:
        """解析关系分析结果"""
        
        try:
            # 验证关系类型
            rel_type_str = relationship_data.get("relationship_type", "knows")
            try:
                relationship_type = RelationshipType(rel_type_str)
            except ValueError:
                relationship_type = RelationshipType.KNOWS
            
            # 验证情感倾向
            sentiment_str = relationship_data.get("sentiment", "neutral")
            try:
                sentiment = SentimentType(sentiment_str)
            except ValueError:
                sentiment = SentimentType.NEUTRAL
            
            # 验证关系强度
            strength = relationship_data.get("strength", 0.5)
            strength = min(1.0, max(0.0, float(strength)))
            
            return CharacterRelationship(
                character1_name=char1.name,
                character2_name=char2.name,
                relationship_type=relationship_type,
                strength=strength,
                sentiment=sentiment,
                description=relationship_data.get("description", ""),
                evidence=relationship_data.get("evidence", []),
                established_chapter=chapter_number
            )
            
        except Exception as e:
            logger.error(f"解析关系结果失败: {e}")
            # 返回基本关系
            return CharacterRelationship(
                character1_name=char1.name,
                character2_name=char2.name,
                relationship_type=RelationshipType.KNOWS,
                strength=0.3,
                sentiment=SentimentType.NEUTRAL,
                description="基本认识关系",
                evidence=[],
                established_chapter=chapter_number
            )
    
    def analyze_relationship_network(
        self, 
        relationships: List[CharacterRelationship]
    ) -> Dict[str, Any]:
        """分析关系网络的整体特征"""
        
        if not relationships:
            return {
                "total_relationships": 0,
                "relationship_types": {},
                "sentiment_distribution": {},
                "average_strength": 0.0,
                "central_characters": []
            }
        
        # 统计关系类型分布
        type_distribution = {}
        for rel in relationships:
            rel_type = rel.relationship_type.value
            type_distribution[rel_type] = type_distribution.get(rel_type, 0) + 1
        
        # 统计情感分布
        sentiment_distribution = {}
        for rel in relationships:
            sentiment = rel.sentiment.value
            sentiment_distribution[sentiment] = sentiment_distribution.get(sentiment, 0) + 1
        
        # 计算平均关系强度
        average_strength = sum(rel.strength for rel in relationships) / len(relationships)
        
        # 找出中心角色（参与关系最多的角色）
        character_counts = {}
        for rel in relationships:
            character_counts[rel.character1_name] = character_counts.get(rel.character1_name, 0) + 1
            character_counts[rel.character2_name] = character_counts.get(rel.character2_name, 0) + 1
        
        central_characters = sorted(character_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_relationships": len(relationships),
            "relationship_types": type_distribution,
            "sentiment_distribution": sentiment_distribution,
            "average_strength": round(average_strength, 2),
            "central_characters": [{"name": name, "connections": count} for name, count in central_characters]
        }
