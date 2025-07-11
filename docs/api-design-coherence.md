# 前后关联API设计文档

## 📋 文档信息

- **文档标题**: AI互动小说前后关联API设计
- **版本**: v1.0
- **创建日期**: 2024-01-10
- **关联文档**: [前后关联技术方案](./story-coherence-design.md)

## 🚀 核心API端点

### 1. 章节生成API

#### POST /api/v1/stories/{story_id}/chapters/generate
生成新章节，保证前后关联性。

**请求参数**:
```json
{
    "user_choice": "去找神秘老人",
    "custom_input": null,
    "generation_options": {
        "style": "detailed",
        "length": "medium",
        "focus": ["character_development", "plot_advancement"]
    }
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "chapter": {
            "id": "chapter_016",
            "chapter_number": 16,
            "title": "师父现身",
            "content": "李明按照梦中的指引，悄悄来到东山脚下...",
            "word_count": 486,
            "choices": [
                {
                    "id": "choice_1",
                    "text": "立即开始学习敛息术",
                    "impact_level": "high",
                    "risk_level": "low"
                },
                {
                    "id": "choice_2", 
                    "text": "询问暗影组织的详细信息",
                    "impact_level": "medium",
                    "risk_level": "medium"
                }
            ]
        },
        "coherence_info": {
            "memories_used": [
                {
                    "content": "第8章：师父给了古玉，说时机到了自然明白",
                    "relevance_score": 0.89,
                    "chapter_reference": 8
                }
            ],
            "character_consistency_score": 0.92,
            "plot_continuity_score": 0.88,
            "overall_coherence_score": 0.90
        },
        "generation_metadata": {
            "ai_model": "gemini-pro",
            "generation_time_ms": 2340,
            "context_quality_score": 0.85,
            "prompt_tokens": 1250,
            "completion_tokens": 486
        }
    }
}
```

### 2. 记忆检索API

#### GET /api/v1/stories/{story_id}/memories/search
搜索故事相关记忆。

**查询参数**:
- `query`: 搜索关键词
- `memory_types`: 记忆类型过滤 (可选)
- `limit`: 返回数量限制 (默认10)
- `min_relevance`: 最小相关度阈值 (默认0.7)

**响应示例**:
```json
{
    "success": true,
    "data": {
        "memories": [
            {
                "id": "memory_008_001",
                "content": "神秘师父警告李明要隐藏真气波动",
                "relevance_score": 0.89,
                "metadata": {
                    "chapter_number": 8,
                    "memory_type": "warning",
                    "characters": ["李明", "神秘师父"],
                    "importance_score": 0.95
                }
            }
        ],
        "search_metadata": {
            "total_found": 15,
            "search_time_ms": 45,
            "query_embedding_time_ms": 12
        }
    }
}
```

### 3. 故事上下文API

#### GET /api/v1/stories/{story_id}/context
获取故事完整上下文信息。

**响应示例**:
```json
{
    "success": true,
    "data": {
        "story_info": {
            "id": "story_001",
            "title": "都市修仙传奇",
            "theme": "urban_cultivation",
            "current_chapter": 15,
            "protagonist": {
                "name": "李明",
                "age": 25,
                "current_level": "练气初期"
            }
        },
        "character_profiles": {
            "李明": {
                "role": "protagonist",
                "personality": ["理性", "谨慎", "好奇"],
                "current_status": "面临暗影组织威胁",
                "relationships": {
                    "小雨": "childhood_friend_complicated",
                    "神秘师父": "mentor"
                }
            }
        },
        "plot_threads": {
            "main": {
                "name": "修仙成长",
                "status": "active",
                "progress": 0.3
            },
            "romance": {
                "name": "与小雨的感情线",
                "status": "complicated",
                "progress": 0.2
            },
            "danger": {
                "name": "暗影组织威胁",
                "status": "escalating",
                "progress": 0.6
            }
        },
        "world_building": {
            "power_system": "修仙境界体系",
            "social_structure": "现代都市隐藏修仙者",
            "main_conflicts": ["修仙者vs普通世界", "暗影组织追捕"]
        },
        "coherence_metrics": {
            "overall_score": 0.87,
            "character_consistency": 0.92,
            "plot_continuity": 0.85,
            "world_consistency": 0.84
        }
    }
}
```

### 4. 连贯性分析API

#### POST /api/v1/stories/{story_id}/analyze/coherence
分析故事连贯性并提供改进建议。

**请求参数**:
```json
{
    "analysis_scope": "full",  // "recent", "full", "custom"
    "chapter_range": null,     // 自定义范围时使用
    "focus_areas": ["character_consistency", "plot_continuity"]
}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "analysis_results": {
            "overall_coherence_score": 0.87,
            "detailed_scores": {
                "character_consistency": 0.92,
                "plot_continuity": 0.85,
                "world_consistency": 0.84,
                "temporal_logic": 0.88
            },
            "issues_found": [
                {
                    "type": "character_inconsistency",
                    "severity": "medium",
                    "description": "李明在第12章表现过于冲动，与其谨慎性格不符",
                    "affected_chapters": [12],
                    "suggestions": [
                        "在第13章中解释李明冲动的原因",
                        "通过内心独白体现其内在挣扎"
                    ]
                }
            ],
            "strengths": [
                "师父角色的神秘感保持一致",
                "修仙体系设定前后呼应良好",
                "主要情节线发展自然"
            ]
        },
        "improvement_suggestions": [
            {
                "priority": "high",
                "area": "character_development",
                "suggestion": "加强李明性格转变的过渡描写"
            }
        ],
        "analysis_metadata": {
            "chapters_analyzed": 15,
            "memories_reviewed": 45,
            "analysis_time_ms": 1250
        }
    }
}
```

## 🔧 内部服务API

### 1. 记忆存储服务

#### POST /internal/memory/store
存储新的故事记忆。

```python
# 内部调用示例
await memory_service.store_memory(
    story_id="story_001",
    content="李明第一次使用古玉的力量",
    memory_type="ability_usage",
    chapter_number=16,
    importance_score=0.9,
    characters=["李明"],
    keywords=["古玉", "力量", "觉醒"]
)
```

### 2. 上下文聚合服务

#### POST /internal/context/aggregate
聚合生成所需的完整上下文。

```python
# 内部调用示例
context = await context_service.build_generation_context(
    story_id="story_001",
    user_choice="使用古玉的力量"
)
```

### 3. 连贯性验证服务

#### POST /internal/coherence/validate
验证生成内容的连贯性。

```python
# 内部调用示例
validation_result = await coherence_service.validate_content(
    story_id="story_001",
    new_content="生成的章节内容...",
    context=generation_context
)
```

## 📊 监控和分析API

### 1. 性能监控API

#### GET /api/v1/admin/performance/stories/{story_id}
获取故事生成性能指标。

**响应示例**:
```json
{
    "success": true,
    "data": {
        "performance_metrics": {
            "average_generation_time_ms": 2150,
            "memory_retrieval_time_ms": 45,
            "context_building_time_ms": 120,
            "ai_generation_time_ms": 1985
        },
        "quality_metrics": {
            "average_coherence_score": 0.87,
            "user_satisfaction_score": 4.2,
            "story_completion_rate": 0.78
        },
        "resource_usage": {
            "total_memories_stored": 156,
            "average_memories_per_chapter": 3.2,
            "database_size_mb": 12.5,
            "vector_db_size_mb": 45.8
        }
    }
}
```

### 2. 质量分析API

#### GET /api/v1/admin/quality/analysis
获取系统整体质量分析。

**响应示例**:
```json
{
    "success": true,
    "data": {
        "system_quality": {
            "overall_coherence_score": 0.85,
            "stories_analyzed": 1250,
            "common_issues": [
                {
                    "issue": "character_inconsistency",
                    "frequency": 0.12,
                    "impact": "medium"
                }
            ]
        },
        "improvement_trends": {
            "coherence_improvement_rate": 0.05,
            "user_satisfaction_trend": "increasing",
            "generation_speed_improvement": 0.15
        }
    }
}
```

## 🔒 错误处理

### 标准错误响应格式
```json
{
    "success": false,
    "error": {
        "code": "COHERENCE_VALIDATION_FAILED",
        "message": "生成的内容与故事背景不一致",
        "details": {
            "validation_score": 0.45,
            "failed_checks": ["character_consistency", "world_rules"],
            "suggestions": ["重新生成", "调整提示词"]
        }
    },
    "request_id": "req_123456789"
}
```

### 常见错误代码
- `STORY_NOT_FOUND`: 故事不存在
- `INSUFFICIENT_CONTEXT`: 上下文信息不足
- `MEMORY_RETRIEVAL_FAILED`: 记忆检索失败
- `COHERENCE_VALIDATION_FAILED`: 连贯性验证失败
- `AI_GENERATION_TIMEOUT`: AI生成超时
- `RATE_LIMIT_EXCEEDED`: 请求频率超限

## 🚀 使用示例

### 完整的章节生成流程
```python
# 1. 用户做出选择
user_choice = "去找神秘老人"

# 2. 调用章节生成API
response = await api_client.post(
    f"/api/v1/stories/{story_id}/chapters/generate",
    json={"user_choice": user_choice}
)

# 3. 检查生成质量
if response.data.coherence_info.overall_coherence_score < 0.8:
    # 如果质量不够，可以重新生成或调整
    pass

# 4. 展示给用户
chapter = response.data.chapter
print(f"第{chapter.chapter_number}章：{chapter.title}")
print(chapter.content)
```

---

**文档状态**: ✅ 完成  
**最后更新**: 2024-01-10  
**相关文档**: [前后关联技术方案](./story-coherence-design.md), [记忆系统实现](./memory-system-implementation.md)
