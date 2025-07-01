"""
Neo4j图谱模块

该模块负责处理小说角色关系图谱的构建和管理，包括：
- 角色信息提取
- 关系分析
- Neo4j图数据库操作
- 图谱可视化支持
"""

from .models import (
    CharacterNode,
    RelationshipEdge,
    GraphData,
    ExtractedCharacter,
    CharacterRelationship,
    EnrichedCharacter,
    GraphAnalytics,
    LocationNode,
    FactionNode
)

from .character_extractor import CharacterExtractionAgent
from .relationship_analyzer import RelationshipAnalyzer
from .neo4j_builder import Neo4jGraphBuilder
from .graph_workflow import NovelGraphWorkflow
from .config import (
    Neo4jConfig,
    GraphConfig,
    get_neo4j_config,
    get_graph_config,
    get_neo4j_config_dict,
    get_graph_status,
    check_neo4j_connection
)

__all__ = [
    # 数据模型
    "CharacterNode",
    "RelationshipEdge",
    "GraphData",
    "ExtractedCharacter",
    "CharacterRelationship",
    "EnrichedCharacter",
    "GraphAnalytics",
    "LocationNode",
    "FactionNode",

    # 核心组件
    "CharacterExtractionAgent",
    "RelationshipAnalyzer",
    "Neo4jGraphBuilder",
    "NovelGraphWorkflow",

    # 配置和工具
    "Neo4jConfig",
    "GraphConfig",
    "get_neo4j_config",
    "get_graph_config",
    "get_neo4j_config_dict",
    "get_graph_status",
    "check_neo4j_connection"
]
