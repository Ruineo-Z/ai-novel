# AI互动小说前后关联技术方案

## 📋 文档信息

- **文档标题**: AI互动小说前后关联保证技术方案
- **版本**: v1.0
- **创建日期**: 2024-01-10
- **作者**: AI互动小说开发团队
- **技术栈**: Python + FastAPI + LlamaIndex + PostgreSQL + ChromaDB

## 🎯 核心挑战与解决方案

### 传统AI的问题
- **健忘症**: AI无法记住之前的情节
- **矛盾性**: 前后描述不一致
- **断裂感**: 缺乏连贯的故事线

### 我们的解决方案
**多层次记忆管理 + 智能上下文聚合**

## 🧠 多层次记忆架构

### 1. 短期记忆 (PostgreSQL)
存储最近3-5章的详细内容，提供即时上下文。

```python
async def get_recent_context(story_id: str, current_chapter: int):
    recent_chapters = await db.execute("""
        SELECT chapter_number, title, content, user_choice_made
        FROM chapters 
        WHERE story_id = ? AND chapter_number >= ?
        ORDER BY chapter_number DESC
        LIMIT 5
    """, story_id, current_chapter - 4)
    
    return {
        "recent_plot": recent_chapters,
        "immediate_context": recent_chapters[0] if recent_chapters else None
    }
```

### 2. 中期记忆 (ChromaDB语义检索)
基于向量相似度检索相关历史情节。

```python
async def get_relevant_memories(story_id: str, current_situation: str):
    relevant_memories = await chroma_db.query(
        query_texts=[current_situation],
        where={
            "story_id": story_id,
            "importance_score": {"$gte": 0.7}
        },
        n_results=10
    )
    return relevant_memories
```

### 3. 长期记忆 (PostgreSQL结构化存储)
维护故事核心设定和角色关系。

```python
async def get_core_context(story_id: str):
    context = await db.execute("""
        SELECT 
            s.theme, s.protagonist_info,
            sc.character_profiles, sc.world_building, sc.plot_threads
        FROM stories s
        JOIN story_contexts sc ON s.id = sc.story_id
        WHERE s.id = ?
    """, story_id)
    return context
```

## 🔄 智能上下文聚合流程

### 完整的章节生成算法

```python
async def generate_next_chapter(story_id: str, user_choice: str):
    """
    智能章节生成 - 保持前后关联的核心算法
    """
    
    # === 第1步：收集多层次记忆 ===
    recent_context = await get_recent_context(story_id, current_chapter)
    core_context = await get_core_context(story_id)
    relevant_memories = await get_relevant_memories(story_id, user_choice)
    
    # === 第2步：构建智能提示词 ===
    prompt = build_contextual_prompt(
        recent_context=recent_context,
        core_context=core_context, 
        relevant_memories=relevant_memories,
        user_choice=user_choice
    )
    
    # === 第3步：AI生成新内容 ===
    new_chapter = await ai_service.generate_with_context(prompt)
    
    # === 第4步：更新记忆系统 ===
    chapter = await save_chapter(story_id, new_chapter)
    await extract_and_store_memories(story_id, new_chapter, chapter.chapter_number)
    await update_character_states(story_id, new_chapter)
    
    return chapter
```

## 📊 数据库设计

### PostgreSQL表结构 (5张核心表)

1. **users表** - 用户管理
2. **stories表** - 故事主体信息
3. **chapters表** - 章节内容存储
4. **choices表** - 用户选择记录
5. **story_contexts表** - 故事上下文管理

### ChromaDB集合设计 (3个核心集合)

1. **story_memory** - 故事记忆向量化存储
2. **character_profiles** - 角色档案向量化管理
3. **world_building** - 世界观设定向量化存储

## 🎭 关联性保证机制

### 1. 角色一致性检查
```python
async def validate_character_consistency(story_id: str, new_content: str):
    character_profiles = await get_character_profiles(story_id)
    consistency_check = await ai_service.validate_consistency(
        character_profiles=character_profiles,
        new_content=new_content
    )
    
    if consistency_check.score < 0.8:
        return await regenerate_with_consistency_fix(new_content, consistency_check.issues)
    
    return new_content
```

### 2. 情节线追踪
```python
class PlotThreadTracker:
    async def update_plot_threads(self, story_id: str, new_chapter: dict):
        current_threads = await self.get_active_threads(story_id)
        thread_impacts = await self.analyze_thread_impacts(new_chapter, current_threads)
        
        for thread_id, impact in thread_impacts.items():
            await self.update_thread_status(story_id, thread_id, impact)
```

### 3. 伏笔管理系统
```python
class ForeshadowingManager:
    async def track_foreshadowing(self, story_id: str, content: str):
        foreshadows = await ai_service.identify_foreshadowing(content)
        for foreshadow in foreshadows:
            await self.store_foreshadowing(story_id, foreshadow)
    
    async def check_payoff_opportunities(self, story_id: str, current_situation: str):
        pending_foreshadows = await self.get_pending_foreshadows(story_id)
        for foreshadow in pending_foreshadows:
            relevance = await self.calculate_payoff_relevance(foreshadow, current_situation)
            if relevance > 0.8:
                return foreshadow
        return None
```

## 📈 质量评估指标

### 连贯性评分系统
```python
class CoherenceScorer:
    def calculate_coherence_score(self, story_data: dict) -> float:
        scores = {
            "character_consistency": self.score_character_consistency(story_data),
            "plot_continuity": self.score_plot_continuity(story_data), 
            "world_consistency": self.score_world_consistency(story_data),
            "temporal_logic": self.score_temporal_logic(story_data)
        }
        
        weights = {"character_consistency": 0.3, "plot_continuity": 0.4, 
                  "world_consistency": 0.2, "temporal_logic": 0.1}
        
        return sum(scores[key] * weights[key] for key in scores)
```

## 🔧 实际应用示例

### 场景：用户选择"去找神秘老人"

#### 记忆检索结果
```python
relevant_memories = [
    {
        "content": "第3章：茶馆遇到白胡子老人，老人说了神秘的话",
        "similarity": 0.89,
        "metadata": {"chapter": 3, "type": "character_introduction"}
    },
    {
        "content": "第8章：老人给了李明一块古玉，说'时机到了自然明白'", 
        "similarity": 0.85,
        "metadata": {"chapter": 8, "type": "item_giving"}
    },
    {
        "content": "第12章：李明梦到老人指向东方，似有深意",
        "similarity": 0.78,
        "metadata": {"chapter": 12, "type": "prophetic_dream"}
    }
]
```

#### 生成的连贯内容
```
第16章：师父现身

李明按照梦中的指引，悄悄来到东山脚下。刚才的黑衣人让他意识到，
自己的修炼可能已经暴露，必须寻求师父的帮助。

远远地，他看到了那个熟悉的身影——正是几个月前在茶馆遇到的白胡子老人。

"小友，终于来了。"老人转身，眼中闪过一丝欣慰，"看来那块古玉起作用了。"

李明摸了摸怀中的玉佩，果然感受到了温热的气息。原来这就是老人说的"时机"。
```

## 💡 技术优势

1. **多层次记忆架构** - 短期、中期、长期记忆协同工作
2. **智能语义检索** - 基于向量相似度找到相关情节
3. **结构化上下文管理** - 维护角色、世界观、情节线的一致性
4. **动态伏笔追踪** - 自动识别和回收故事伏笔
5. **质量评估机制** - 实时监控和修正连贯性问题

## 🚀 实施计划

### Phase 1: 基础记忆系统 (1周)
- PostgreSQL数据库设计和实现
- ChromaDB向量存储配置
- 基础记忆存储和检索功能

### Phase 2: 智能上下文聚合 (1周)
- 多层次记忆检索算法
- 智能提示词构建系统
- AI生成内容质量验证

### Phase 3: 高级关联功能 (1周)
- 角色一致性检查机制
- 情节线追踪系统
- 伏笔管理和回收功能

### Phase 4: 优化和测试 (3-5天)
- 性能优化和缓存策略
- 连贯性评估指标实现
- 完整的测试覆盖

## 📚 相关文档

- [技术架构设计](./technical-design.md)
- [数据库设计文档](./database-design.md)
- [API接口文档](./api-documentation.md)
- [部署指南](./deployment-guide.md)

## 📝 详细实现示例

### 完整的记忆数据结构

#### PostgreSQL数据示例
```sql
-- stories表数据
{
    "id": "story_001",
    "title": "都市修仙传奇",
    "theme": "urban_cultivation",
    "protagonist_info": {
        "name": "李明",
        "age": 25,
        "occupation": "程序员",
        "personality": ["理性", "谨慎", "好奇"],
        "current_level": "练气初期"
    }
}

-- chapters表数据
{
    "id": "chapter_015",
    "chapter_number": 15,
    "title": "深夜异响",
    "content": "李明在公司加班到深夜，突然听到楼下传来奇怪的声音...",
    "choices_offered": [
        {"text": "悄悄下楼查看", "impact": "high"},
        {"text": "继续观察", "impact": "medium"}
    ]
}
```

#### ChromaDB向量数据示例
```python
# story_memory集合
{
    "id": "memory_001",
    "document": "李明第一次感受到真气涌动的神奇体验",
    "embedding": [0.123, -0.456, 0.789, ...],  # 768维向量
    "metadata": {
        "story_id": "story_001",
        "chapter_number": 3,
        "memory_type": "ability_discovery",
        "importance_score": 0.9,
        "characters": ["李明"],
        "keywords": ["真气", "修炼", "觉醒"]
    }
}

# character_profiles集合
{
    "id": "char_001",
    "document": "李明：25岁程序员转修仙者，理性谨慎，目前练气初期",
    "embedding": [0.567, -0.890, 0.234, ...],
    "metadata": {
        "story_id": "story_001",
        "character_name": "李明",
        "character_role": "protagonist",
        "personality_traits": ["理性", "谨慎", "好奇"],
        "relationships": {
            "小雨": "childhood_friend",
            "神秘师父": "mentor"
        }
    }
}
```

### 智能提示词构建示例

```python
def build_contextual_prompt(recent_context, core_context, relevant_memories, user_choice):
    prompt = f"""
【故事设定】
主人公：{core_context['protagonist']}
世界观：{core_context['theme']} - {core_context['world_rules']}

【前情回顾】
{format_recent_chapters(recent_context)}

【相关记忆】（AI需要考虑的重要情节）
{format_relevant_memories(relevant_memories)}

【当前选择】
用户选择：{user_choice}

【生成要求】
1. 必须与相关记忆保持一致
2. 考虑最近章节的情况发展
3. 体现主人公的性格特点
4. 推进主要情节线发展
5. 为后续章节埋下伏笔

请生成下一章节内容...
"""
    return prompt
```

## 🔍 故障排除和优化

### 常见问题及解决方案

1. **记忆检索不准确**
   - 优化向量嵌入模型
   - 调整相似度阈值
   - 增加元数据过滤条件

2. **生成内容不连贯**
   - 增加上下文窗口大小
   - 优化提示词模板
   - 加强一致性验证机制

3. **性能问题**
   - 实现记忆缓存策略
   - 优化数据库查询
   - 使用异步处理

### 性能优化策略

```python
# 记忆缓存机制
class MemoryCache:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 3600  # 1小时过期

    async def get_cached_memories(self, story_id: str, query: str):
        cache_key = f"{story_id}:{hash(query)}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        memories = await self.fetch_memories(story_id, query)
        self.cache[cache_key] = memories
        return memories
```

## 📊 监控和分析

### 关键指标监控

1. **连贯性指标**
   - 角色一致性评分
   - 情节连续性评分
   - 世界观一致性评分

2. **用户体验指标**
   - 章节生成时间
   - 用户满意度评分
   - 故事完成率

3. **系统性能指标**
   - 记忆检索响应时间
   - 数据库查询性能
   - AI生成响应时间

### 数据分析Dashboard

```python
class CoherenceAnalytics:
    async def generate_story_report(self, story_id: str):
        return {
            "coherence_score": await self.calculate_overall_coherence(story_id),
            "character_consistency": await self.analyze_character_consistency(story_id),
            "plot_development": await self.analyze_plot_development(story_id),
            "memory_utilization": await self.analyze_memory_usage(story_id)
        }
```

## 🧪 测试策略

### 单元测试
```python
class TestMemoryRetrieval:
    async def test_relevant_memory_search(self):
        # 测试基于查询的记忆检索
        memories = await get_relevant_memories("story_001", "神秘老人")
        assert len(memories) > 0
        assert memories[0]['similarity'] > 0.7

    async def test_character_consistency(self):
        # 测试角色一致性检查
        result = await validate_character_consistency("story_001", test_content)
        assert result.score > 0.8
```

### 集成测试
```python
class TestStoryGeneration:
    async def test_full_chapter_generation(self):
        # 测试完整的章节生成流程
        chapter = await generate_next_chapter("story_001", "寻找师父")

        # 验证生成质量
        assert chapter.content is not None
        assert len(chapter.content) > 100
        assert "师父" in chapter.content  # 确保响应了用户选择
```

---

**文档状态**: ✅ 完成
**最后更新**: 2024-01-10
**下次审查**: 2024-01-17
