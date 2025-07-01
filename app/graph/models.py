"""
图谱数据模型定义

定义了Neo4j图谱中的节点、关系和相关数据结构
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import uuid
from datetime import datetime


class CharacterType(str, Enum):
    """角色类型枚举"""
    PROTAGONIST = "protagonist"  # 主角
    MAJOR = "major"  # 主要角色
    MINOR = "minor"  # 次要角色
    BACKGROUND = "background"  # 背景角色


class RelationshipType(str, Enum):
    """关系类型枚举"""
    FAMILY = "family"  # 家族关系
    FRIEND = "friend"  # 朋友关系
    ENEMY = "enemy"  # 敌对关系
    MENTOR = "mentor"  # 师徒关系
    ALLY = "ally"  # 盟友关系
    RIVAL = "rival"  # 竞争关系
    LOVE = "love"  # 爱情关系
    COLLEAGUE = "colleague"  # 同事关系
    KNOWS = "knows"  # 认识关系
    BELONGS_TO = "belongs_to"  # 归属关系
    LOCATED_IN = "located_in"  # 位于关系


class SentimentType(str, Enum):
    """情感倾向枚举"""
    POSITIVE = "positive"  # 正面
    NEGATIVE = "negative"  # 负面
    NEUTRAL = "neutral"  # 中性
    COMPLEX = "complex"  # 复杂


class ExtractedCharacter(BaseModel):
    """从章节中提取的原始角色信息"""
    name: str = Field(description="角色姓名")
    mentions: int = Field(description="在章节中被提及的次数")
    description: Optional[str] = Field(description="角色描述")
    actions: List[str] = Field(default=[], description="角色在章节中的行为")
    dialogue: List[str] = Field(default=[], description="角色的对话")
    character_type: CharacterType = Field(description="角色类型")
    importance_score: float = Field(description="重要性评分 0-1")


class CharacterRelationship(BaseModel):
    """角色关系信息"""
    character1_name: str = Field(description="角色1姓名")
    character2_name: str = Field(description="角色2姓名")
    relationship_type: RelationshipType = Field(description="关系类型")
    strength: float = Field(description="关系强度 0-1")
    sentiment: SentimentType = Field(description="情感倾向")
    description: str = Field(description="关系描述")
    evidence: List[str] = Field(default=[], description="关系证据（文本片段）")
    established_chapter: int = Field(description="关系建立的章节")


class EnrichedCharacter(BaseModel):
    """丰富后的角色信息（用于Neo4j存储）"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="唯一标识")
    name: str = Field(description="角色姓名")
    character_type: CharacterType = Field(description="角色类型")
    
    # 基本信息
    age: Optional[int] = Field(description="年龄")
    gender: Optional[str] = Field(description="性别")
    appearance: Optional[str] = Field(description="外貌描述")
    personality: Optional[str] = Field(description="性格特点")
    background: Optional[str] = Field(description="背景故事")
    
    # 能力和特征
    abilities: List[str] = Field(default=[], description="能力列表")
    goals: List[str] = Field(default=[], description="目标列表")
    weaknesses: List[str] = Field(default=[], description="弱点列表")
    special_traits: Optional[str] = Field(description="特殊特质")
    
    # 故事相关
    importance_level: int = Field(description="重要程度 1-10")
    first_appearance_chapter: int = Field(description="首次出现章节")
    status: str = Field(default="active", description="状态：active/dead/missing")
    
    # 提取信息
    mentions_count: int = Field(description="被提及次数")
    dialogue_samples: List[str] = Field(default=[], description="对话样本")
    action_samples: List[str] = Field(default=[], description="行为样本")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CharacterNode(BaseModel):
    """Neo4j角色节点模型"""
    id: str = Field(description="节点ID")
    labels: List[str] = Field(default=["Character"], description="节点标签")
    properties: Dict[str, Any] = Field(description="节点属性")
    
    @classmethod
    def from_enriched_character(cls, character: EnrichedCharacter) -> "CharacterNode":
        """从丰富角色信息创建节点"""
        return cls(
            id=character.id,
            labels=["Character", character.character_type.value.title()],
            properties=character.model_dump(exclude={"id"})
        )


class RelationshipEdge(BaseModel):
    """Neo4j关系边模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="关系ID")
    start_node_id: str = Field(description="起始节点ID")
    end_node_id: str = Field(description="结束节点ID")
    relationship_type: str = Field(description="关系类型")
    properties: Dict[str, Any] = Field(description="关系属性")
    
    @classmethod
    def from_character_relationship(
        cls, 
        relationship: CharacterRelationship,
        char1_id: str,
        char2_id: str
    ) -> "RelationshipEdge":
        """从角色关系创建边"""
        return cls(
            start_node_id=char1_id,
            end_node_id=char2_id,
            relationship_type=relationship.relationship_type.value.upper(),
            properties={
                "strength": relationship.strength,
                "sentiment": relationship.sentiment.value,
                "description": relationship.description,
                "evidence": relationship.evidence,
                "established_chapter": relationship.established_chapter,
                "created_at": datetime.now().isoformat()
            }
        )


class LocationNode(BaseModel):
    """地点节点模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(description="地点名称")
    description: Optional[str] = Field(description="地点描述")
    location_type: Optional[str] = Field(description="地点类型")
    properties: Dict[str, Any] = Field(default={})


class FactionNode(BaseModel):
    """势力节点模型"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(description="势力名称")
    description: Optional[str] = Field(description="势力描述")
    power_level: Optional[int] = Field(description="势力等级")
    properties: Dict[str, Any] = Field(default={})


class GraphData(BaseModel):
    """完整的图谱数据"""
    characters: List[CharacterNode] = Field(default=[], description="角色节点列表")
    relationships: List[RelationshipEdge] = Field(default=[], description="关系边列表")
    locations: List[LocationNode] = Field(default=[], description="地点节点列表")
    factions: List[FactionNode] = Field(default=[], description="势力节点列表")
    
    # 元数据
    novel_style: str = Field(description="小说风格")
    world_name: str = Field(description="世界名称")
    chapter_count: int = Field(description="章节数量")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class GraphAnalytics(BaseModel):
    """图谱分析结果"""
    total_characters: int = Field(description="总角色数")
    total_relationships: int = Field(description="总关系数")
    character_importance_ranking: List[Dict[str, Any]] = Field(description="角色重要性排名")
    relationship_distribution: Dict[str, int] = Field(description="关系类型分布")
    network_density: float = Field(description="网络密度")
    central_characters: List[str] = Field(description="中心角色列表")
