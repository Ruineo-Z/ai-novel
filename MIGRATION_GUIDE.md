# LangGraph 到 CrewAI 迁移指南

本文档详细说明了如何将项目从 LangGraph 框架迁移到 CrewAI 框架。

## 迁移概述

### 原 LangGraph 架构
- **状态图管理**: 使用 `langgraph.graph.StateGraph` 管理工作流
- **检查点保存**: 使用 `langgraph-checkpoint-redis` 进行状态持久化
- **Agent 创建**: 使用 `langgraph.prebuilt.create_react_agent`
- **记忆管理**: 通过 Redis 和 InMemorySaver 管理状态

### 新 CrewAI 架构
- **Crew 管理**: 使用 CrewAI 的 Crew 和 Process 管理工作流
- **简化记忆**: 基于文件的简单记忆系统
- **Agent 定义**: 使用 CrewAI 的 Agent 类
- **任务驱动**: 通过 Task 定义具体的执行任务

## 文件对应关系

| LangGraph 文件 | CrewAI 文件 | 说明 |
|---|---|---|
| `app/langgraph/graph_workflow.py` | `app/crew/crew_workflow.py` | 工作流管理 |
| `app/langgraph/agent_init.py` | `app/crew/crew_agents.py` | Agent 定义 |
| `app/langgraph/graph_node.py` | `app/crew/crew_tasks.py` | 任务/节点定义 |
| `app/langgraph/short_memory.py` | `app/crew/crew_memory.py` | 记忆管理 |
| - | `app/crew/crew_manager.py` | 统一管理器 |
| - | `app/api/crew_routes.py` | API 路由 |

## 核心变化

### 1. 依赖变更

**移除的依赖**:
```toml
"langgraph"
"langgraph-supervisor"
"langgraph-checkpoint-redis"
"langchain"
"langchain-core"
```

**新增的依赖**:
```toml
"crewai>=0.70.0"
"crewai-tools>=0.12.0"
"chromadb>=0.4.0"
```

### 2. Agent 定义变化

**LangGraph 方式**:
```python
from langgraph.prebuilt import create_react_agent

world_agent = create_react_agent(
    llm=llm,
    tools=[],
    state_modifier=prompt
)
```

**CrewAI 方式**:
```python
from crewai import Agent

world_designer = Agent(
    role="世界观设计师",
    goal="创建丰富详细的小说世界观",
    backstory="专业的奇幻世界构建师...",
    llm=llm,
    memory=True,
    verbose=True
)
```

### 3. 工作流管理变化

**LangGraph 方式**:
```python
from langgraph.graph import StateGraph

workflow = StateGraph(NovelState)
workflow.add_node("world_setting", world_setting_node)
workflow.add_node("protagonist_generation", protagonist_node)
workflow.add_edge("world_setting", "protagonist_generation")
```

**CrewAI 方式**:
```python
from crewai import Crew, Process

crew = Crew(
    agents=[world_designer, character_designer],
    tasks=[world_task, character_task],
    process=Process.sequential,
    memory=True
)
```

### 4. 记忆管理变化

**LangGraph 方式**:
```python
from langgraph.checkpoint.redis import RedisSaver

checkpointer = RedisSaver.from_conn_info(
    host="localhost",
    port=6379,
    db=0
)
```

**CrewAI 方式**:
```python
class NovelCrewMemory:
    def save_session(self, session_id, data):
        # 基于文件的简单存储
        with open(f"sessions/{session_id}.json", 'w') as f:
            json.dump(data, f)
```

## 迁移步骤

### 第一步：更新依赖

1. 更新 `pyproject.toml` 文件
2. 重新安装依赖：
   ```bash
   pip install -e .
   ```

### 第二步：创建 CrewAI 模块

1. 创建 `app/crew/` 目录
2. 实现以下文件：
   - `crew_agents.py` - Agent 定义
   - `crew_tasks.py` - 任务定义
   - `crew_workflow.py` - 工作流管理
   - `crew_memory.py` - 记忆管理
   - `crew_manager.py` - 统一管理器

### 第三步：更新 API 路由

1. 创建 `app/api/crew_routes.py`
2. 在 `main.py` 中注册新路由

### 第四步：测试迁移

1. 启动应用：
   ```bash
   python main.py
   ```

2. 测试 CrewAI 接口：
   ```bash
   curl -X POST "http://localhost:8000/api/v1/crew/sessions" \
        -H "Content-Type: application/json" \
        -d '{"novel_style": "仙侠"}'
   ```

### 第五步：清理旧代码

1. 备份 `app/langgraph/` 目录
2. 移除 LangGraph 相关导入
3. 更新配置文件

## API 接口变化

### 新增的 CrewAI 接口

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/v1/crew/sessions` | POST | 创建会话 |
| `/api/v1/crew/sessions/{id}` | GET | 获取会话状态 |
| `/api/v1/crew/sessions/{id}/world-setting` | POST | 生成世界观 |
| `/api/v1/crew/sessions/{id}/protagonist` | POST | 生成主人公 |
| `/api/v1/crew/sessions/{id}/first-chapter` | POST | 生成第一章 |
| `/api/v1/crew/sessions/{id}/next-chapter` | POST | 生成下一章 |
| `/api/v1/crew/generate-complete` | POST | 生成完整小说 |

## 优势对比

### CrewAI 的优势

1. **简化的记忆管理**: 不需要复杂的 Redis 配置
2. **更直观的 Agent 定义**: 角色、目标、背景故事更清晰
3. **内置协作机制**: Agent 之间的协作更自然
4. **更好的任务管理**: 任务定义更灵活
5. **简化的部署**: 减少外部依赖

### 注意事项

1. **记忆持久化**: CrewAI 的记忆系统相对简单，适合大多数场景
2. **性能考虑**: 文件存储在高并发场景下可能需要优化
3. **扩展性**: 可以根据需要集成更复杂的存储系统

## 故障排除

### 常见问题

1. **导入错误**: 确保所有 CrewAI 依赖已正确安装
2. **记忆问题**: 检查文件权限和存储目录
3. **Agent 响应**: 确保 LLM 配置正确

### 调试建议

1. 启用详细日志：`verbose=True`
2. 检查会话状态接口
3. 查看 CrewAI 的执行日志

## 总结

通过本次迁移，项目从复杂的 LangGraph 状态图管理转向了更简洁的 CrewAI 框架。新架构提供了：

- 更简单的记忆管理
- 更直观的 Agent 协作
- 更清晰的任务定义
- 更容易的部署和维护

迁移完成后，原有的小说生成功能将通过 CrewAI 框架实现，同时保持相同的 API 接口和功能特性。