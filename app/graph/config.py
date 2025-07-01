"""
图谱模块配置

包含Neo4j连接配置和图谱构建相关设置
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Neo4jConfig(BaseModel):
    """Neo4j数据库配置"""
    uri: str = Field(default="bolt://localhost:7687", description="Neo4j连接URI")
    username: str = Field(default="neo4j", description="用户名")
    password: str = Field(default="password", description="密码")
    database: str = Field(default="neo4j", description="数据库名称")
    max_connection_lifetime: int = Field(default=3600, description="连接最大生存时间(秒)")
    max_connection_pool_size: int = Field(default=50, description="连接池最大大小")
    connection_timeout: int = Field(default=30, description="连接超时时间(秒)")


class GraphConfig(BaseSettings):
    """图谱配置"""
    
    # Neo4j配置
    neo4j_uri: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    neo4j_username: str = Field(default="neo4j", description="Neo4j用户名")
    neo4j_password: str = Field(default="password", description="Neo4j密码")
    neo4j_database: str = Field(default="neo4j", description="Neo4j数据库")
    
    # 图谱构建配置
    enable_graph_building: bool = Field(default=True, description="是否启用图谱构建")
    character_extraction_enabled: bool = Field(default=True, description="是否启用角色提取")
    relationship_analysis_enabled: bool = Field(default=True, description="是否启用关系分析")
    
    # 性能配置
    max_characters_per_chapter: int = Field(default=20, description="每章最大角色数")
    max_relationships_per_pair: int = Field(default=3, description="每对角色最大关系数")
    character_importance_threshold: float = Field(default=0.1, description="角色重要性阈值")
    
    # 缓存配置
    enable_character_cache: bool = Field(default=True, description="是否启用角色缓存")
    cache_expiry_hours: int = Field(default=24, description="缓存过期时间(小时)")
    
    class Config:
        env_prefix = "GRAPH_"
        env_file = ".env"


def get_neo4j_config() -> Neo4jConfig:
    """获取Neo4j配置"""
    
    # 从环境变量或默认值创建配置
    config = Neo4jConfig(
        uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "password"),
        database=os.getenv("NEO4J_DATABASE", "neo4j")
    )
    
    return config


def get_graph_config() -> GraphConfig:
    """获取图谱配置"""
    return GraphConfig()


def get_neo4j_config_dict() -> Dict[str, Any]:
    """获取Neo4j配置字典"""
    config = get_neo4j_config()
    return {
        "uri": config.uri,
        "username": config.username,
        "password": config.password,
        "database": config.database
    }


# 默认配置实例
default_neo4j_config = get_neo4j_config()
default_graph_config = get_graph_config()


# 图谱构建相关常量
class GraphConstants:
    """图谱构建常量"""
    
    # 角色类型权重
    CHARACTER_TYPE_WEIGHTS = {
        "protagonist": 1.0,
        "major": 0.8,
        "minor": 0.5,
        "background": 0.2
    }
    
    # 关系类型权重
    RELATIONSHIP_TYPE_WEIGHTS = {
        "family": 0.9,
        "love": 0.9,
        "friend": 0.7,
        "ally": 0.7,
        "mentor": 0.8,
        "enemy": 0.8,
        "rival": 0.6,
        "colleague": 0.5,
        "knows": 0.3
    }
    
    # 情感倾向权重
    SENTIMENT_WEIGHTS = {
        "positive": 1.0,
        "negative": 0.8,
        "neutral": 0.5,
        "complex": 0.9
    }
    
    # 默认角色属性
    DEFAULT_CHARACTER_ATTRIBUTES = {
        "age": None,
        "gender": None,
        "appearance": "外貌未描述",
        "personality": "性格待发展",
        "background": "背景待补充",
        "abilities": ["基础能力"],
        "goals": ["未明确目标"],
        "weaknesses": ["未知弱点"],
        "importance_level": 1,
        "status": "active"
    }
    
    # Neo4j查询限制
    MAX_QUERY_RESULTS = 1000
    MAX_RELATIONSHIP_DEPTH = 3
    BATCH_SIZE = 100


# 环境检查函数
def check_neo4j_connection() -> bool:
    """检查Neo4j连接是否可用"""
    try:
        from neo4j import GraphDatabase
        
        config = get_neo4j_config()
        driver = GraphDatabase.driver(
            config.uri,
            auth=(config.username, config.password)
        )
        
        with driver.session(database=config.database) as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            success = record and record["test"] == 1
        
        driver.close()
        return success
        
    except Exception:
        return False


def get_graph_status() -> Dict[str, Any]:
    """获取图谱模块状态"""
    
    config = get_graph_config()
    neo4j_available = check_neo4j_connection()
    
    return {
        "graph_building_enabled": config.enable_graph_building,
        "neo4j_available": neo4j_available,
        "neo4j_config": {
            "uri": config.neo4j_uri,
            "database": config.neo4j_database,
            "username": config.neo4j_username
        },
        "feature_flags": {
            "character_extraction": config.character_extraction_enabled,
            "relationship_analysis": config.relationship_analysis_enabled,
            "character_cache": config.enable_character_cache
        },
        "performance_settings": {
            "max_characters_per_chapter": config.max_characters_per_chapter,
            "max_relationships_per_pair": config.max_relationships_per_pair,
            "character_importance_threshold": config.character_importance_threshold
        }
    }
