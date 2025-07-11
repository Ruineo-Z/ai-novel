# 记忆系统技术实现文档

## 📋 文档信息

- **文档标题**: AI互动小说记忆系统技术实现
- **版本**: v1.0
- **创建日期**: 2024-01-10
- **关联文档**: [前后关联技术方案](./story-coherence-design.md)

## 🗄️ 数据库详细设计

### PostgreSQL表结构详解

#### 1. users表 - 用户管理
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

#### 2. stories表 - 故事主体
```sql
CREATE TABLE stories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    theme VARCHAR(50) NOT NULL CHECK (theme IN ('urban', 'sci-fi', 'cultivation', 'martial-arts')),
    protagonist_info JSONB NOT NULL,
    current_chapter_id UUID,
    metadata JSONB DEFAULT '{}',
    total_chapters INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_stories_user_id ON stories(user_id);
CREATE INDEX idx_stories_theme ON stories(theme);
CREATE INDEX idx_stories_created_at ON stories(created_at);
CREATE INDEX idx_stories_protagonist_name ON stories USING GIN ((protagonist_info->>'name'));
```

#### 3. chapters表 - 章节内容
```sql
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID REFERENCES stories(id) ON DELETE CASCADE,
    previous_chapter_id UUID REFERENCES chapters(id),
    chapter_number INTEGER NOT NULL,
    title VARCHAR(255),
    content TEXT NOT NULL,
    ai_prompt_used TEXT,
    choices_offered JSONB DEFAULT '[]',
    user_choice_made TEXT,
    choice_impact_score FLOAT DEFAULT 0.0,
    word_count INTEGER,
    generation_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(story_id, chapter_number)
);

-- 索引优化
CREATE INDEX idx_chapters_story_id ON chapters(story_id);
CREATE INDEX idx_chapters_story_chapter ON chapters(story_id, chapter_number);
CREATE INDEX idx_chapters_previous ON chapters(previous_chapter_id);
```

#### 4. choices表 - 用户选择记录
```sql
CREATE TABLE choices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    next_chapter_id UUID REFERENCES chapters(id),
    choice_text TEXT NOT NULL,
    user_input TEXT,
    is_custom BOOLEAN DEFAULT FALSE,
    impact_score FLOAT DEFAULT 0.0,
    choice_type VARCHAR(50) DEFAULT 'predefined',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_choices_chapter_id ON choices(chapter_id);
CREATE INDEX idx_choices_next_chapter ON choices(next_chapter_id);
```

#### 5. story_contexts表 - 故事上下文
```sql
CREATE TABLE story_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    story_id UUID REFERENCES stories(id) ON DELETE CASCADE UNIQUE,
    character_profiles JSONB DEFAULT '{}',
    world_building JSONB DEFAULT '{}',
    plot_threads JSONB DEFAULT '{}',
    user_preferences JSONB DEFAULT '{}',
    context_summary TEXT,
    coherence_score FLOAT DEFAULT 0.0,
    last_analysis_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引优化
CREATE INDEX idx_story_contexts_story_id ON story_contexts(story_id);
CREATE INDEX idx_story_contexts_coherence ON story_contexts(coherence_score);
```

### ChromaDB集合设计详解

#### 1. story_memory集合配置
```python
# 集合创建和配置
collection_config = {
    "name": "story_memory",
    "metadata": {
        "description": "故事情节记忆向量存储",
        "embedding_model": "jina-embeddings-v2-base-en",
        "dimension": 768,
        "distance_metric": "cosine"
    }
}

# 数据结构标准
memory_schema = {
    "id": "string",  # 格式: story_{story_id}_memory_{sequence}
    "document": "string",  # 记忆文本内容
    "embedding": "vector[768]",  # Jina AI生成的向量
    "metadata": {
        "story_id": "string",
        "chapter_number": "integer",
        "memory_type": "enum",  # ability_discovery, character_interaction, plot_development, etc.
        "importance_score": "float",  # 0.0-1.0
        "characters": "array[string]",
        "emotions": "array[string]",
        "keywords": "array[string]",
        "timestamp": "datetime",
        "related_memories": "array[string]"  # 关联记忆ID
    }
}
```

#### 2. character_profiles集合配置
```python
character_collection_config = {
    "name": "character_profiles",
    "metadata": {
        "description": "角色档案向量存储",
        "embedding_model": "jina-embeddings-v2-base-en",
        "dimension": 768
    }
}

character_schema = {
    "id": "string",  # 格式: char_{story_id}_{character_name}
    "document": "string",  # 角色描述文本
    "embedding": "vector[768]",
    "metadata": {
        "story_id": "string",
        "character_name": "string",
        "character_role": "enum",  # protagonist, supporting, antagonist, mentor
        "personality_traits": "array[string]",
        "relationships": "object",
        "current_status": "string",
        "appearance_chapters": "array[integer]",
        "development_arc": "string",
        "last_updated_chapter": "integer"
    }
}
```

#### 3. world_building集合配置
```python
world_collection_config = {
    "name": "world_building",
    "metadata": {
        "description": "世界观设定向量存储",
        "embedding_model": "jina-embeddings-v2-base-en",
        "dimension": 768
    }
}

world_schema = {
    "id": "string",  # 格式: world_{story_id}_{element_type}_{sequence}
    "document": "string",  # 世界观描述文本
    "embedding": "vector[768]",
    "metadata": {
        "story_id": "string",
        "world_element": "string",
        "category": "enum",  # power_system, social_structure, geography, history
        "importance": "enum",  # core, important, supplementary
        "related_concepts": "array[string]",
        "consistency_rules": "array[string]",
        "introduced_chapter": "integer"
    }
}
```

## 🔧 核心服务实现

### 记忆管理服务
```python
class MemoryService:
    def __init__(self, chroma_client, embedding_service):
        self.chroma = chroma_client
        self.embedding = embedding_service
        self.collections = {
            "story_memory": None,
            "character_profiles": None,
            "world_building": None
        }
    
    async def initialize_collections(self):
        """初始化ChromaDB集合"""
        for name, config in collection_configs.items():
            self.collections[name] = await self.chroma.get_or_create_collection(
                name=name,
                metadata=config["metadata"]
            )
    
    async def store_memory(self, story_id: str, content: str, memory_type: str, 
                          chapter_number: int, **metadata):
        """存储新记忆"""
        # 生成向量嵌入
        embedding = await self.embedding.embed_text(content)
        
        # 构建记忆ID
        memory_id = f"story_{story_id}_memory_{chapter_number}_{memory_type}"
        
        # 准备元数据
        full_metadata = {
            "story_id": story_id,
            "chapter_number": chapter_number,
            "memory_type": memory_type,
            "timestamp": datetime.now().isoformat(),
            **metadata
        }
        
        # 存储到ChromaDB
        await self.collections["story_memory"].add(
            ids=[memory_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[full_metadata]
        )
        
        return memory_id
    
    async def search_relevant_memories(self, story_id: str, query: str, 
                                     memory_types: list = None, top_k: int = 10):
        """搜索相关记忆"""
        # 构建查询条件
        where_clause = {"story_id": story_id}
        if memory_types:
            where_clause["memory_type"] = {"$in": memory_types}
        
        # 执行向量搜索
        results = await self.collections["story_memory"].query(
            query_texts=[query],
            where=where_clause,
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        return self._format_search_results(results)
    
    def _format_search_results(self, results):
        """格式化搜索结果"""
        formatted_results = []
        for i, doc in enumerate(results["documents"][0]):
            formatted_results.append({
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "similarity": 1 - results["distances"][0][i],  # 转换为相似度
                "relevance_score": self._calculate_relevance_score(
                    results["metadatas"][0][i], 
                    1 - results["distances"][0][i]
                )
            })
        
        return sorted(formatted_results, key=lambda x: x["relevance_score"], reverse=True)
    
    def _calculate_relevance_score(self, metadata, similarity):
        """计算综合相关性评分"""
        importance_weight = metadata.get("importance_score", 0.5)
        recency_weight = self._calculate_recency_weight(metadata.get("chapter_number", 0))
        
        return similarity * 0.6 + importance_weight * 0.3 + recency_weight * 0.1
    
    def _calculate_recency_weight(self, chapter_number):
        """计算时间近期性权重"""
        # 越近的章节权重越高，但不会完全压倒重要性
        max_chapters = 100  # 假设最大章节数
        return min(chapter_number / max_chapters, 1.0)
```

### 上下文聚合服务
```python
class ContextAggregationService:
    def __init__(self, db_service, memory_service):
        self.db = db_service
        self.memory = memory_service
    
    async def build_generation_context(self, story_id: str, user_choice: str):
        """构建AI生成所需的完整上下文"""
        
        # 并行获取各类上下文数据
        tasks = [
            self._get_recent_context(story_id),
            self._get_core_context(story_id),
            self._get_relevant_memories(story_id, user_choice),
            self._get_character_context(story_id, user_choice),
            self._get_world_context(story_id, user_choice)
        ]
        
        recent, core, memories, characters, world = await asyncio.gather(*tasks)
        
        # 聚合上下文
        context = {
            "story_info": core,
            "recent_chapters": recent,
            "relevant_memories": memories,
            "character_info": characters,
            "world_info": world,
            "user_choice": user_choice,
            "generation_metadata": {
                "context_quality_score": self._assess_context_quality(
                    recent, memories, characters, world
                ),
                "memory_coverage": len(memories),
                "character_coverage": len(characters),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        return context
    
    async def _get_recent_context(self, story_id: str):
        """获取最近章节上下文"""
        return await self.db.execute("""
            SELECT chapter_number, title, content, user_choice_made, choices_offered
            FROM chapters 
            WHERE story_id = ?
            ORDER BY chapter_number DESC 
            LIMIT 5
        """, story_id)
    
    async def _get_core_context(self, story_id: str):
        """获取故事核心信息"""
        return await self.db.execute("""
            SELECT s.theme, s.protagonist_info, s.metadata,
                   sc.character_profiles, sc.world_building, sc.plot_threads
            FROM stories s
            LEFT JOIN story_contexts sc ON s.id = sc.story_id
            WHERE s.id = ?
        """, story_id)
    
    async def _get_relevant_memories(self, story_id: str, user_choice: str):
        """获取相关记忆"""
        return await self.memory.search_relevant_memories(
            story_id=story_id,
            query=user_choice,
            top_k=8
        )
    
    async def _get_character_context(self, story_id: str, query: str):
        """获取相关角色信息"""
        return await self.memory.collections["character_profiles"].query(
            query_texts=[query],
            where={"story_id": story_id},
            n_results=5
        )
    
    async def _get_world_context(self, story_id: str, query: str):
        """获取相关世界观信息"""
        return await self.memory.collections["world_building"].query(
            query_texts=[query],
            where={"story_id": story_id},
            n_results=3
        )
    
    def _assess_context_quality(self, recent, memories, characters, world):
        """评估上下文质量"""
        quality_factors = {
            "recent_coverage": min(len(recent) / 3, 1.0),  # 至少3章
            "memory_relevance": sum(m["similarity"] for m in memories[:5]) / 5,
            "character_coverage": min(len(characters) / 3, 1.0),
            "world_coverage": min(len(world) / 2, 1.0)
        }
        
        weights = {"recent_coverage": 0.3, "memory_relevance": 0.4, 
                  "character_coverage": 0.2, "world_coverage": 0.1}
        
        return sum(quality_factors[k] * weights[k] for k in quality_factors)
```

## 📊 性能监控和优化

### 性能指标收集
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    async def track_generation_performance(self, story_id: str, operation: str):
        """跟踪生成性能指标"""
        start_time = time.time()
        
        try:
            yield  # 执行被监控的操作
        finally:
            duration = time.time() - start_time
            await self._record_metric(story_id, operation, duration)
    
    async def _record_metric(self, story_id: str, operation: str, duration: float):
        """记录性能指标"""
        metric_key = f"{operation}_{story_id}"
        if metric_key not in self.metrics:
            self.metrics[metric_key] = []
        
        self.metrics[metric_key].append({
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持最近100条记录
        if len(self.metrics[metric_key]) > 100:
            self.metrics[metric_key] = self.metrics[metric_key][-100:]
```

---

**文档状态**: ✅ 完成  
**最后更新**: 2024-01-10  
**相关文档**: [前后关联技术方案](./story-coherence-design.md)
