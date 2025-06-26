# CrewAI 小说创作框架

本模块提供基于 CrewAI 的小说创作功能，替代原有的 LangGraph 框架实现。

## 模块结构

```
app/crew/
├── __init__.py              # 模块初始化
├── crew_agents.py           # Agent 定义
├── crew_tasks.py            # 任务定义
├── crew_workflow.py         # 工作流管理
├── crew_memory.py           # 记忆管理
├── crew_manager.py          # 统一管理器
└── README.md               # 本文档
```

## 核心组件

### 1. NovelCrewAgents (crew_agents.py)

定义了四个专业的 AI Agent：

- **世界观设计师 (world_designer)**: 负责创建小说的世界观设定
- **角色设计师 (character_designer)**: 负责设计主人公和其他角色
- **章节作家 (chapter_writer)**: 负责撰写小说章节内容
- **故事协调员 (story_coordinator)**: 负责协调整体故事结构

### 2. NovelCrewTasks (crew_tasks.py)

定义了创作过程中的各种任务：

- **世界观设定任务**: 根据小说风格创建世界观
- **主人公生成任务**: 基于世界观设计主人公
- **第一章创作任务**: 撰写小说开篇
- **后续章节任务**: 基于前文继续创作

### 3. NovelCrewWorkflow (crew_workflow.py)

提供工作流管理功能：

- 顺序执行创作流程
- 错误处理和重试机制
- 状态跟踪和日志记录

### 4. NovelCrewMemory (crew_memory.py)

简化的记忆管理系统：

- 基于文件的会话存储
- 支持会话的增删改查
- 提供上下文检索功能
- 自动清理过期数据

### 5. NovelCrewManager (crew_manager.py)

统一的管理接口：

- 整合所有组件
- 提供高级 API
- 处理复杂的创作流程

## 使用方法

### 基本使用

```python
from app.crew import get_crew_manager
from app.schemas.base import NovelStyle

# 获取管理器
crew_manager = get_crew_manager()

# 创建会话
session_id = crew_manager.create_session(NovelStyle.仙侠)

# 生成世界观
world_setting = crew_manager.generate_world_setting(session_id)

# 生成主人公
protagonist = crew_manager.generate_protagonist(session_id)

# 生成第一章
first_chapter = crew_manager.generate_first_chapter(session_id)
```

### 完整小说创作

```python
# 一次性生成完整小说
result = crew_manager.generate_complete_novel(
    session_id=None,  # 自动创建会话
    max_chapters=10
)

print(f"生成了 {result['total_chapters']} 章")
```

### 记忆管理

```python
from app.crew import get_memory_manager

# 获取记忆管理器
memory = get_memory_manager()

# 列出所有会话
sessions = memory.list_sessions()

# 加载特定会话
session_data = memory.load_session(session_id)

# 获取会话上下文
context = memory.get_session_context(session_id)
```

## API 接口

### HTTP 接口

通过 `app/api/novel_routes.py` 提供的 REST API：

```bash
# 创建会话
POST /api/v1/crew/sessions
{
  "novel_style": "仙侠"
}

# 生成世界观
POST /api/v1/crew/sessions/{session_id}/world-setting

# 生成主人公
POST /api/v1/crew/sessions/{session_id}/protagonist

# 生成章节
POST /api/v1/crew/sessions/{session_id}/first-chapter
POST /api/v1/crew/sessions/{session_id}/next-chapter

# 生成完整小说
POST /api/v1/crew/generate-complete
{
  "novel_style": "科幻",
  "max_chapters": 5
}
```

## 配置说明

### Agent 配置

每个 Agent 都可以配置：

- **role**: Agent 的角色定义
- **goal**: Agent 的目标
- **backstory**: Agent 的背景故事
- **llm**: 使用的语言模型
- **memory**: 是否启用记忆
- **verbose**: 是否输出详细日志

### 记忆配置

记忆系统支持：

- **存储目录**: 默认为 `crew_memory/`
- **会话存储**: `crew_memory/sessions/`
- **模板存储**: `crew_memory/templates/`
- **自动清理**: 可配置清理周期

## 与 LangGraph 的对比

| 特性 | LangGraph | CrewAI |
|------|-----------|--------|
| 工作流管理 | StateGraph | Crew + Process |
| 状态管理 | 复杂状态图 | 简化的任务流 |
| 记忆系统 | Redis + 检查点 | 文件存储 |
| Agent 定义 | create_react_agent | Agent 类 |
| 协作机制 | 状态传递 | 内置协作 |
| 部署复杂度 | 高（需要 Redis） | 低（文件存储） |
| 学习曲线 | 陡峭 | 平缓 |

## 优势

1. **简化部署**: 无需外部依赖（如 Redis）
2. **直观设计**: Agent 角色和任务定义更清晰
3. **内置协作**: Agent 之间的协作更自然
4. **易于扩展**: 可以轻松添加新的 Agent 和任务
5. **调试友好**: 提供详细的执行日志

## 注意事项

1. **文件存储**: 在高并发场景下可能需要优化
2. **记忆容量**: 长期使用需要定期清理
3. **LLM 配置**: 确保语言模型配置正确
4. **错误处理**: 注意处理 Agent 执行失败的情况

## 示例代码

查看 `examples/crew_example.py` 获取完整的使用示例。

## 故障排除

### 常见问题

1. **导入错误**: 确保 CrewAI 依赖已安装
2. **记忆问题**: 检查文件权限和存储目录
3. **Agent 无响应**: 检查 LLM 配置和网络连接
4. **任务失败**: 查看详细日志定位问题

### 调试技巧

1. 启用详细日志: `verbose=True`
2. 检查会话状态: 使用状态查询接口
3. 查看记忆内容: 直接检查存储文件
4. 单步执行: 分步骤测试各个功能

## 扩展开发

### 添加新 Agent

```python
class CustomAgent(Agent):
    def __init__(self):
        super().__init__(
            role="自定义角色",
            goal="自定义目标",
            backstory="自定义背景",
            llm=get_llm(),
            memory=True
        )
```

### 添加新任务

```python
def create_custom_task(self, context):
    return Task(
        description="自定义任务描述",
        expected_output="期望输出格式",
        agent=self.custom_agent
    )
```

### 扩展记忆系统

```python
class ExtendedMemory(NovelCrewMemory):
    def save_to_database(self, data):
        # 集成数据库存储
        pass
```

通过这种方式，可以根据具体需求扩展框架功能。