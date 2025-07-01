"""
Neo4j图谱构建器

负责Neo4j数据库的操作和图谱构建，包括：
- 连接管理
- 节点创建
- 关系创建
- 图谱查询
- 性能优化
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.core.logger import get_logger
from .models import (
    EnrichedCharacter,
    CharacterRelationship,
    CharacterNode,
    RelationshipEdge,
    GraphData,
    GraphAnalytics,
    LocationNode,
    FactionNode
)

logger = get_logger(__name__)


class Neo4jGraphBuilder:
    """Neo4j图谱构建器"""
    
    def __init__(
        self, 
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "password",
        database: str = "neo4j"
    ):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
        self._connection_verified = False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
    
    async def connect(self) -> bool:
        """连接到Neo4j数据库"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            
            # 验证连接
            await self.verify_connection()
            self._connection_verified = True
            
            # 创建索引和约束
            await self.setup_database_schema()
            
            logger.info("Neo4j连接成功")
            return True
            
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Neo4j连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"Neo4j连接异常: {e}")
            return False
    
    async def verify_connection(self):
        """验证数据库连接"""
        async with self.driver.session(database=self.database) as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            if record["test"] != 1:
                raise Exception("连接验证失败")
    
    async def setup_database_schema(self):
        """设置数据库模式（索引和约束）"""
        
        schema_queries = [
            # 角色节点约束和索引
            "CREATE CONSTRAINT character_id_unique IF NOT EXISTS FOR (c:Character) REQUIRE c.id IS UNIQUE",
            "CREATE INDEX character_name_index IF NOT EXISTS FOR (c:Character) ON (c.name)",
            "CREATE INDEX character_type_index IF NOT EXISTS FOR (c:Character) ON (c.character_type)",
            "CREATE INDEX character_importance_index IF NOT EXISTS FOR (c:Character) ON (c.importance_level)",
            
            # 地点节点约束和索引
            "CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            "CREATE INDEX location_name_index IF NOT EXISTS FOR (l:Location) ON (l.name)",
            
            # 势力节点约束和索引
            "CREATE CONSTRAINT faction_id_unique IF NOT EXISTS FOR (f:Faction) REQUIRE f.id IS UNIQUE",
            "CREATE INDEX faction_name_index IF NOT EXISTS FOR (f:Faction) ON (f.name)",
        ]
        
        async with self.driver.session(database=self.database) as session:
            for query in schema_queries:
                try:
                    await session.run(query)
                    logger.debug(f"执行模式查询: {query}")
                except Exception as e:
                    logger.warning(f"模式查询执行失败: {query}, 错误: {e}")
    
    async def close(self):
        """关闭数据库连接"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j连接已关闭")
    
    async def create_character_node(self, character: EnrichedCharacter) -> str:
        """创建角色节点"""
        
        if not self._connection_verified:
            raise Exception("数据库连接未建立")
        
        query = """
        MERGE (c:Character {id: $id})
        SET c += $properties
        SET c:Character
        SET c += CASE $character_type
            WHEN 'protagonist' THEN {labels: ['Character', 'Protagonist']}
            WHEN 'major' THEN {labels: ['Character', 'Major']}
            WHEN 'minor' THEN {labels: ['Character', 'Minor']}
            WHEN 'background' THEN {labels: ['Character', 'Background']}
            ELSE {labels: ['Character']}
        END
        RETURN c.id as id
        """
        
        # 准备节点属性
        properties = character.model_dump(exclude={"id"})
        # 转换datetime为字符串
        if "created_at" in properties:
            properties["created_at"] = properties["created_at"].isoformat()
        if "updated_at" in properties:
            properties["updated_at"] = properties["updated_at"].isoformat()
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query, 
                    id=character.id,
                    properties=properties,
                    character_type=character.character_type.value
                )
                record = await result.single()
                
                logger.debug(f"创建角色节点: {character.name} (ID: {character.id})")
                return record["id"]
                
        except Exception as e:
            logger.error(f"创建角色节点失败: {e}")
            raise
    
    async def create_relationship(
        self, 
        char1_id: str, 
        char2_id: str, 
        relationship: CharacterRelationship
    ) -> bool:
        """创建角色关系"""
        
        if not self._connection_verified:
            raise Exception("数据库连接未建立")
        
        # 构建关系类型（大写）
        rel_type = relationship.relationship_type.value.upper()
        
        query = f"""
        MATCH (c1:Character {{id: $char1_id}})
        MATCH (c2:Character {{id: $char2_id}})
        MERGE (c1)-[r:{rel_type}]->(c2)
        SET r += $properties
        RETURN r
        """
        
        # 准备关系属性
        properties = {
            "strength": relationship.strength,
            "sentiment": relationship.sentiment.value,
            "description": relationship.description,
            "evidence": relationship.evidence,
            "established_chapter": relationship.established_chapter,
            "created_at": relationship.__dict__.get("created_at", "").isoformat() if hasattr(relationship, "created_at") else ""
        }
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query,
                    char1_id=char1_id,
                    char2_id=char2_id,
                    properties=properties
                )
                
                record = await result.single()
                if record:
                    logger.debug(f"创建关系: {char1_id} -{rel_type}-> {char2_id}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            return False
    
    async def build_complete_graph(
        self,
        characters: List[EnrichedCharacter],
        relationships: List[CharacterRelationship],
        novel_metadata: Dict[str, Any] = None
    ) -> GraphData:
        """构建完整的角色关系图谱"""
        
        try:
            # 创建字符ID映射
            char_id_map = {}
            
            # 批量创建角色节点
            character_nodes = []
            for character in characters:
                char_id = await self.create_character_node(character)
                char_id_map[character.name] = char_id
                character_nodes.append(CharacterNode.from_enriched_character(character))
            
            # 批量创建关系
            relationship_edges = []
            for relationship in relationships:
                char1_id = char_id_map.get(relationship.character1_name)
                char2_id = char_id_map.get(relationship.character2_name)
                
                if char1_id and char2_id:
                    success = await self.create_relationship(char1_id, char2_id, relationship)
                    if success:
                        edge = RelationshipEdge.from_character_relationship(
                            relationship, char1_id, char2_id
                        )
                        relationship_edges.append(edge)
            
            # 创建图谱数据对象
            graph_data = GraphData(
                characters=character_nodes,
                relationships=relationship_edges,
                novel_style=novel_metadata.get("novel_style", "") if novel_metadata else "",
                world_name=novel_metadata.get("world_name", "") if novel_metadata else "",
                chapter_count=novel_metadata.get("chapter_count", 1) if novel_metadata else 1
            )
            
            logger.info(f"图谱构建完成: {len(character_nodes)}个角色, {len(relationship_edges)}个关系")
            return graph_data
            
        except Exception as e:
            logger.error(f"构建完整图谱失败: {e}")
            raise

    async def query_character_relationships(
        self,
        character_name: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """查询角色的关系网络"""

        query = """
        MATCH (c:Character {name: $character_name})
        OPTIONAL MATCH path = (c)-[*1..$max_depth]-(connected)
        RETURN c, path, connected
        """

        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    query,
                    character_name=character_name,
                    max_depth=max_depth
                )

                records = await result.data()

                # 处理查询结果
                relationships = []
                connected_characters = set()

                for record in records:
                    if record.get("path"):
                        # 提取路径中的关系信息
                        path = record["path"]
                        for rel in path.relationships:
                            relationships.append({
                                "start_node": dict(rel.start_node),
                                "end_node": dict(rel.end_node),
                                "type": rel.type,
                                "properties": dict(rel)
                            })

                    if record.get("connected"):
                        connected_characters.add(record["connected"]["name"])

                return {
                    "character": character_name,
                    "connected_characters": list(connected_characters),
                    "relationships": relationships,
                    "total_connections": len(connected_characters)
                }

        except Exception as e:
            logger.error(f"查询角色关系失败: {e}")
            return {"character": character_name, "connected_characters": [], "relationships": []}

    async def get_graph_analytics(self) -> GraphAnalytics:
        """获取图谱分析数据"""

        queries = {
            "total_characters": "MATCH (c:Character) RETURN count(c) as count",
            "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "character_importance": """
                MATCH (c:Character)
                RETURN c.name as name, c.importance_level as importance,
                       size((c)-[]->()) + size((c)<-[]-()) as connections
                ORDER BY c.importance_level DESC, connections DESC
                LIMIT 10
            """,
            "relationship_types": """
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """,
            "network_density": """
                MATCH (c:Character)
                WITH count(c) as node_count
                MATCH ()-[r]->()
                WITH node_count, count(r) as edge_count
                RETURN toFloat(edge_count) / (node_count * (node_count - 1)) as density
            """
        }

        try:
            analytics_data = {}

            async with self.driver.session(database=self.database) as session:
                # 执行各种分析查询
                for key, query in queries.items():
                    result = await session.run(query)

                    if key in ["total_characters", "total_relationships"]:
                        record = await result.single()
                        analytics_data[key] = record["count"] if record else 0

                    elif key == "character_importance":
                        records = await result.data()
                        analytics_data["character_importance_ranking"] = [
                            {
                                "name": record["name"],
                                "importance": record["importance"],
                                "connections": record["connections"]
                            }
                            for record in records
                        ]
                        analytics_data["central_characters"] = [
                            record["name"] for record in records[:5]
                        ]

                    elif key == "relationship_types":
                        records = await result.data()
                        analytics_data["relationship_distribution"] = {
                            record["rel_type"]: record["count"]
                            for record in records
                        }

                    elif key == "network_density":
                        record = await result.single()
                        analytics_data["network_density"] = record["density"] if record else 0.0

            return GraphAnalytics(
                total_characters=analytics_data.get("total_characters", 0),
                total_relationships=analytics_data.get("total_relationships", 0),
                character_importance_ranking=analytics_data.get("character_importance_ranking", []),
                relationship_distribution=analytics_data.get("relationship_distribution", {}),
                network_density=analytics_data.get("network_density", 0.0),
                central_characters=analytics_data.get("central_characters", [])
            )

        except Exception as e:
            logger.error(f"获取图谱分析数据失败: {e}")
            return GraphAnalytics(
                total_characters=0,
                total_relationships=0,
                character_importance_ranking=[],
                relationship_distribution={},
                network_density=0.0,
                central_characters=[]
            )

    async def clear_graph(self) -> bool:
        """清空图谱数据"""

        query = "MATCH (n) DETACH DELETE n"

        try:
            async with self.driver.session(database=self.database) as session:
                await session.run(query)
                logger.info("图谱数据已清空")
                return True

        except Exception as e:
            logger.error(f"清空图谱失败: {e}")
            return False

    async def export_graph_data(self) -> Dict[str, Any]:
        """导出图谱数据"""

        queries = {
            "nodes": "MATCH (n) RETURN n",
            "relationships": "MATCH ()-[r]->() RETURN r"
        }

        try:
            export_data = {"nodes": [], "relationships": []}

            async with self.driver.session(database=self.database) as session:
                # 导出节点
                result = await session.run(queries["nodes"])
                async for record in result:
                    node = record["n"]
                    export_data["nodes"].append({
                        "id": node.element_id,
                        "labels": list(node.labels),
                        "properties": dict(node)
                    })

                # 导出关系
                result = await session.run(queries["relationships"])
                async for record in result:
                    rel = record["r"]
                    export_data["relationships"].append({
                        "id": rel.element_id,
                        "type": rel.type,
                        "start_node": rel.start_node.element_id,
                        "end_node": rel.end_node.element_id,
                        "properties": dict(rel)
                    })

            return export_data

        except Exception as e:
            logger.error(f"导出图谱数据失败: {e}")
            return {"nodes": [], "relationships": []}
