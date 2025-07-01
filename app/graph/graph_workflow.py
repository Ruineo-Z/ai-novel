"""
图谱工作流

将图谱构建功能集成到现有的小说生成工作流中，包括：
- 扩展原有工作流
- 添加图谱构建步骤
- 提供流式输出
- 错误处理和恢复
"""

import asyncio
from typing import AsyncGenerator, Dict, Any, List, Optional

from app.novel_generation.novel_workflow import NovelStartFlow
from app.schemas.base import NovelStyle
from app.schemas.agent_outputs import WorldSettingOutput, ProtagonistGenerationOutput, ChapterOutput
from app.core.logger import get_logger

from .character_extractor import CharacterExtractionAgent
from .relationship_analyzer import RelationshipAnalyzer
from .neo4j_builder import Neo4jGraphBuilder
from .models import (
    ExtractedCharacter,
    EnrichedCharacter,
    CharacterRelationship,
    GraphData,
    GraphAnalytics
)

logger = get_logger(__name__)


class NovelGraphWorkflow(NovelStartFlow):
    """扩展的小说图谱工作流"""
    
    def __init__(
        self, 
        novel_style: NovelStyle,
        neo4j_config: Optional[Dict[str, str]] = None,
        enable_graph_building: bool = True
    ):
        super().__init__(novel_style)
        
        # 图谱相关组件
        self.character_extractor = CharacterExtractionAgent()
        self.relationship_analyzer = RelationshipAnalyzer()
        
        # Neo4j配置
        self.neo4j_config = neo4j_config or {
            "uri": "bolt://localhost:7687",
            "username": "neo4j", 
            "password": "password",
            "database": "neo4j"
        }
        
        self.enable_graph_building = enable_graph_building
        self.graph_builder = None
        
        # 图谱数据存储
        self.extracted_characters: List[ExtractedCharacter] = []
        self.enriched_characters: List[EnrichedCharacter] = []
        self.character_relationships: List[CharacterRelationship] = []
        self.graph_data: Optional[GraphData] = None
    
    async def run_with_graph_building(self) -> AsyncGenerator[Dict[str, Any], None]:
        """运行工作流并构建角色关系图谱"""
        
        try:
            # 初始化Neo4j连接（如果启用）
            if self.enable_graph_building:
                yield {
                    "event_type": "graph_init",
                    "data": {"status": "initializing"},
                    "message": "初始化图谱数据库连接..."
                }
                
                success = await self._initialize_graph_builder()
                if not success:
                    yield {
                        "event_type": "graph_error",
                        "data": {"error": "Neo4j连接失败"},
                        "message": "图谱数据库连接失败，将跳过图谱构建"
                    }
                    self.enable_graph_building = False
            
            # 运行原有的小说生成流程
            novel_data = None
            async for event in self.run_with_streaming():
                yield event
                
                # 保存完成事件的数据用于图谱构建
                if event["event_type"] == "complete":
                    novel_data = event["data"]
            
            # 如果启用图谱构建且有完整数据，开始构建图谱
            if self.enable_graph_building and novel_data:
                async for graph_event in self._build_character_graph(novel_data):
                    yield graph_event
            
        except Exception as e:
            logger.error(f"图谱工作流执行失败: {e}")
            yield {
                "event_type": "graph_error",
                "data": {"error": str(e)},
                "message": f"图谱工作流失败: {str(e)}"
            }
        
        finally:
            # 清理资源
            if self.graph_builder:
                await self.graph_builder.close()
    
    async def _initialize_graph_builder(self) -> bool:
        """初始化图谱构建器"""
        
        try:
            self.graph_builder = Neo4jGraphBuilder(**self.neo4j_config)
            success = await self.graph_builder.connect()
            
            if success:
                logger.info("Neo4j图谱构建器初始化成功")
            else:
                logger.warning("Neo4j图谱构建器初始化失败")
            
            return success
            
        except Exception as e:
            logger.error(f"初始化图谱构建器失败: {e}")
            return False
    
    async def _build_character_graph(self, novel_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """构建角色关系图谱"""
        
        try:
            world_setting = WorldSettingOutput(**novel_data["world_setting"])
            protagonist = ProtagonistGenerationOutput(**novel_data["protagonist"])
            chapter = ChapterOutput(**novel_data["chapter"])
            
            # 步骤1: 角色提取
            yield {
                "event_type": "graph_progress",
                "data": {"step": "character_extraction", "status": "started"},
                "message": "开始提取章节中的角色信息..."
            }
            
            self.extracted_characters = await self.character_extractor.extract_characters_from_chapter(
                chapter.chapter_content,
                protagonist,
                world_setting,
                chapter_number=1
            )
            
            yield {
                "event_type": "characters_extracted",
                "data": {
                    "characters": [char.model_dump() for char in self.extracted_characters],
                    "count": len(self.extracted_characters)
                },
                "message": f"成功提取{len(self.extracted_characters)}个角色"
            }
            
            # 步骤2: 角色数据丰富
            yield {
                "event_type": "graph_progress", 
                "data": {"step": "character_enrichment", "status": "started"},
                "message": "开始丰富角色详细信息..."
            }
            
            self.enriched_characters = []
            for char in self.extracted_characters:
                enriched_char = await self.character_extractor.enrich_character_data(
                    char, protagonist, world_setting, chapter_number=1
                )
                self.enriched_characters.append(enriched_char)
            
            yield {
                "event_type": "characters_enriched",
                "data": {
                    "characters": [char.model_dump() for char in self.enriched_characters],
                    "count": len(self.enriched_characters)
                },
                "message": f"成功丰富{len(self.enriched_characters)}个角色信息"
            }
            
            # 步骤3: 关系分析
            yield {
                "event_type": "graph_progress",
                "data": {"step": "relationship_analysis", "status": "started"},
                "message": "开始分析角色间关系..."
            }
            
            self.character_relationships = await self.relationship_analyzer.analyze_character_relationships(
                chapter.chapter_content,
                self.extracted_characters,
                chapter_number=1
            )
            
            # 分析关系网络特征
            network_analysis = self.relationship_analyzer.analyze_relationship_network(
                self.character_relationships
            )
            
            yield {
                "event_type": "relationships_analyzed",
                "data": {
                    "relationships": [rel.model_dump() for rel in self.character_relationships],
                    "network_analysis": network_analysis,
                    "count": len(self.character_relationships)
                },
                "message": f"成功分析{len(self.character_relationships)}个角色关系"
            }
            
            # 步骤4: 构建Neo4j图谱
            if self.graph_builder:
                yield {
                    "event_type": "graph_progress",
                    "data": {"step": "neo4j_building", "status": "started"},
                    "message": "开始构建Neo4j图谱..."
                }
                
                # 准备元数据
                novel_metadata = {
                    "novel_style": self.style_value,
                    "world_name": world_setting.world_name,
                    "chapter_count": 1
                }
                
                self.graph_data = await self.graph_builder.build_complete_graph(
                    self.enriched_characters,
                    self.character_relationships,
                    novel_metadata
                )
                
                # 获取图谱分析数据
                graph_analytics = await self.graph_builder.get_graph_analytics()
                
                yield {
                    "event_type": "graph_built",
                    "data": {
                        "graph_data": self.graph_data.model_dump(),
                        "analytics": graph_analytics.model_dump()
                    },
                    "message": "Neo4j图谱构建完成"
                }
            
            # 最终完成事件
            yield {
                "event_type": "graph_complete",
                "data": {
                    "summary": {
                        "characters_count": len(self.enriched_characters),
                        "relationships_count": len(self.character_relationships),
                        "graph_built": self.graph_data is not None,
                        "novel_metadata": {
                            "style": self.style_value,
                            "world_name": world_setting.world_name,
                            "protagonist_name": protagonist.name
                        }
                    }
                },
                "message": "角色关系图谱构建完成"
            }
            
        except Exception as e:
            logger.error(f"构建角色图谱失败: {e}")
            yield {
                "event_type": "graph_error",
                "data": {"error": str(e)},
                "message": f"图谱构建失败: {str(e)}"
            }
    
    async def get_character_network(self, character_name: str) -> Dict[str, Any]:
        """获取指定角色的关系网络"""
        
        if not self.graph_builder:
            return {"error": "图谱构建器未初始化"}
        
        try:
            return await self.graph_builder.query_character_relationships(character_name)
        except Exception as e:
            logger.error(f"查询角色网络失败: {e}")
            return {"error": str(e)}
    
    async def get_graph_analytics(self) -> Dict[str, Any]:
        """获取图谱分析数据"""
        
        if not self.graph_builder:
            return {"error": "图谱构建器未初始化"}
        
        try:
            analytics = await self.graph_builder.get_graph_analytics()
            return analytics.model_dump()
        except Exception as e:
            logger.error(f"获取图谱分析失败: {e}")
            return {"error": str(e)}
    
    async def export_graph(self) -> Dict[str, Any]:
        """导出图谱数据"""
        
        if not self.graph_builder:
            return {"error": "图谱构建器未初始化"}
        
        try:
            return await self.graph_builder.export_graph_data()
        except Exception as e:
            logger.error(f"导出图谱失败: {e}")
            return {"error": str(e)}
