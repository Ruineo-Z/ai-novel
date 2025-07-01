# 📊 AI小说角色关系图谱模块

## 🎯 功能概述

本模块为AI小说生成系统提供智能角色关系图谱构建功能，能够：

- 🤖 **智能角色提取**: 从章节内容中自动识别和提取所有出场角色
- 🔗 **关系分析**: 分析角色间的复杂关系网络
- 📈 **图谱构建**: 使用Neo4j构建可查询的角色关系图谱
- 📊 **数据分析**: 提供图谱分析和可视化支持

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    图谱工作流 (NovelGraphWorkflow)              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   角色提取Agent   │  │   关系分析Agent   │  │  Neo4j图谱构建器  │ │
│  │CharacterExtractor│  │RelationshipAnalyzer│  │ Neo4jGraphBuilder│ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                        数据模型层                              │
│  ExtractedCharacter → EnrichedCharacter → CharacterNode      │
│  CharacterRelationship → RelationshipEdge                   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install neo4j>=5.15.0

# 配置环境变量
cp .env.example .env
```

在 `.env` 文件中配置Neo4j连接：

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

### 2. 启动Neo4j

```bash
# 使用Docker启动Neo4j
docker run \
    --name neo4j \
    -p7474:7474 -p7687:7687 \
    -d \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
    --env NEO4J_AUTH=neo4j/your_password \
    neo4j:latest
```

### 3. 使用图谱功能

```python
import asyncio
from app.schemas.base import NovelStyle
from app.graph import NovelGraphWorkflow

async def main():
    # 创建图谱工作流
    workflow = NovelGraphWorkflow(
        novel_style=NovelStyle.XIANXIA,
        enable_graph_building=True
    )
    
    # 运行工作流
    async for event in workflow.run_with_graph_building():
        print(f"{event['event_type']}: {event['message']}")
    
    # 查询图谱数据
    analytics = await workflow.get_graph_analytics()
    print(f"图谱统计: {analytics}")

asyncio.run(main())
```

## 📋 核心组件

### CharacterExtractionAgent
负责从章节内容中提取角色信息：

```python
extractor = CharacterExtractionAgent()

# 提取角色
characters = await extractor.extract_characters_from_chapter(
    chapter_content, protagonist, world_setting
)

# 丰富角色数据
enriched_char = await extractor.enrich_character_data(
    character, protagonist, world_setting
)
```

### RelationshipAnalyzer
分析角色间的关系：

```python
analyzer = RelationshipAnalyzer()

# 分析关系
relationships = await analyzer.analyze_character_relationships(
    chapter_content, characters
)

# 网络分析
network_stats = analyzer.analyze_relationship_network(relationships)
```

### Neo4jGraphBuilder
构建和管理Neo4j图谱：

```python
async with Neo4jGraphBuilder() as builder:
    # 创建角色节点
    char_id = await builder.create_character_node(character)
    
    # 创建关系
    await builder.create_relationship(char1_id, char2_id, relationship)
    
    # 构建完整图谱
    graph_data = await builder.build_complete_graph(
        characters, relationships
    )
```

## 📊 数据模型

### 角色节点 (CharacterNode)
```python
{
    "id": "unique_id",
    "name": "角色姓名",
    "character_type": "protagonist|major|minor|background",
    "age": 25,
    "gender": "男",
    "appearance": "外貌描述",
    "personality": "性格特点",
    "background": "背景故事",
    "abilities": ["能力1", "能力2"],
    "importance_level": 8
}
```

### 关系边 (RelationshipEdge)
```python
{
    "relationship_type": "FRIEND|ENEMY|FAMILY|LOVE|...",
    "strength": 0.8,
    "sentiment": "positive|negative|neutral|complex",
    "description": "关系描述",
    "evidence": ["证据1", "证据2"],
    "established_chapter": 1
}
```

## 🔍 查询示例

### Cypher查询示例

```cypher
-- 查找主角的所有朋友
MATCH (p:Protagonist)-[:FRIEND]->(f:Character)
RETURN p.name, f.name, f.importance_level

-- 查找最重要的角色
MATCH (c:Character)
RETURN c.name, c.importance_level
ORDER BY c.importance_level DESC
LIMIT 10

-- 查找复杂关系网络
MATCH path = (c1:Character)-[*2..3]-(c2:Character)
WHERE c1.name = "主角姓名"
RETURN path
```

### Python查询示例

```python
# 查询角色关系网络
network = await workflow.get_character_network("主角姓名")

# 获取图谱分析
analytics = await workflow.get_graph_analytics()

# 导出图谱数据
graph_data = await workflow.export_graph()
```

## ⚙️ 配置选项

### 图谱配置
```python
from app.graph.config import GraphConfig

config = GraphConfig(
    enable_graph_building=True,
    max_characters_per_chapter=20,
    character_importance_threshold=0.1,
    enable_character_cache=True
)
```

### Neo4j配置
```python
from app.graph.config import Neo4jConfig

neo4j_config = Neo4jConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password",
    database="neo4j"
)
```

## 🧪 测试

运行测试脚本：

```bash
python test_graph.py
```

测试内容包括：
- Neo4j连接测试
- 角色提取测试
- 关系分析测试
- 图谱构建测试
- 查询功能测试

## 🔧 故障排除

### 常见问题

1. **Neo4j连接失败**
   - 检查Neo4j服务是否运行
   - 验证连接配置和密码
   - 确认端口7687可访问

2. **角色提取不准确**
   - 检查LLM配置和API密钥
   - 调整重要性阈值参数
   - 优化提取prompt

3. **关系分析错误**
   - 检查章节内容质量
   - 调整关系强度阈值
   - 验证角色数据完整性

### 性能优化

1. **批量操作**: 使用批量创建节点和关系
2. **索引优化**: 确保关键字段有索引
3. **连接池**: 配置合适的连接池大小
4. **缓存策略**: 启用角色数据缓存

## 📈 扩展功能

### 计划中的功能
- 🎨 图谱可视化界面
- 📊 高级分析算法
- 🔄 增量更新支持
- 🌐 多章节关系演化
- 🎯 智能推荐系统

### 自定义扩展
```python
# 自定义角色提取器
class CustomCharacterExtractor(CharacterExtractionAgent):
    async def extract_characters_from_chapter(self, ...):
        # 自定义提取逻辑
        pass

# 自定义关系分析器
class CustomRelationshipAnalyzer(RelationshipAnalyzer):
    async def analyze_character_relationships(self, ...):
        # 自定义分析逻辑
        pass
```

## 📝 许可证

本模块遵循项目主许可证。
