# AI Interactive Novel System

一个基于AI的互动式小说系统，支持多种小说风格和AI模型。

## 功能特性

- 🎭 **多种小说风格**：支持修仙、科幻、都市、言情、武侠五种风格
- 🤖 **多AI模型支持**：支持Gemini和Ollama模型
- 👤 **自定义主人公**：可选择自定义主人公信息或AI生成
- 🌍 **动态世界观**：根据选择的风格和主人公信息生成独特世界观
- 📖 **互动式剧情**：在关键节点提供选择，影响故事发展
- 🔧 **结构化输出**：使用Pydantic确保数据结构化和类型安全
- 🚀 **现代技术栈**：基于FastAPI、CrewAI、UV包管理

## 技术架构

- **后端框架**：FastAPI
- **AI框架**：CrewAI
- **数据验证**：Pydantic
- **包管理**：UV
- **AI模型**：Google Gemini、Ollama
- **API文档**：自动生成的OpenAPI/Swagger文档

## 快速开始

### 1. 环境准备

确保已安装Python 3.12+和UV包管理器：

```bash
# 安装UV（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd ai-novel

# 使用UV安装依赖
uv sync
```

### 3. 配置环境变量

复制环境变量模板并配置：

```bash
cp .env.example .env
```

编辑`.env`文件，配置API密钥：

```env
# Gemini API配置
GEMINI_API_KEY=your_gemini_api_key_here

# Ollama配置（如果使用本地Ollama）
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# 服务配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### 4. 启动服务

```bash
# 使用UV运行
uv run python main.py

# 或者使用uvicorn直接运行
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. 访问API文档

启动后访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API使用示例

### 创建新小说

```bash
curl -X POST "http://localhost:8000/api/v1/novel/create" \
  -H "Content-Type: application/json" \
  -d '{
    "novel_style": "修仙",
    "ai_model": "gemini",
    "use_custom_protagonist": false
  }'
```

### 做出选择

```bash
curl -X POST "http://localhost:8000/api/v1/novel/choice" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "choice_id": 1
  }'
```

### 获取小说状态

```bash
curl "http://localhost:8000/api/v1/novel/{session_id}/status"
```

## 项目结构

```
ai-novel/
├── app/
│   ├── agents/          # CrewAI代理
│   │   ├── __init__.py
│   │   └── agent_init.py
│   ├── api/             # FastAPI路由
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── core/            # 核心配置
│   │   ├── __init__.py
│   │   └── config.py
│   ├── schemas/         # Pydantic模型
│   │   ├── __init__.py
│   │   ├── agent_outputs.py
│   │   ├── api.py
│   │   └── base.py
│   ├── services/        # 业务逻辑服务
│   │   ├── __init__.py
│   │   ├── ai_factory.py
│   │   ├── ai_service.py
│   │   ├── gemini_service.py
│   │   ├── novel_service.py
│   │   └── ollama_service.py
│   └── __init__.py
├── .env.example         # 环境变量模板
├── .python-version      # Python版本
├── main.py             # 应用入口
├── pyproject.toml      # 项目配置
└── README.md           # 项目说明
```

## 开发指南

### 添加新的小说风格

1. 在`app/schemas/base.py`中的`NovelStyle`枚举添加新风格
2. 在`app/api/routes.py`中更新风格描述
3. 在AI服务中添加对应的提示词模板

### 添加新的AI模型

1. 在`app/schemas/base.py`中的`AIModel`枚举添加新模型
2. 创建新的AI服务类继承`AIService`
3. 在`AIServiceFactory`中注册新服务

### 自定义CrewAI代理

在`app/agents/agent_init.py`中可以自定义代理的角色、目标和背景故事。

## 部署

### Docker部署（推荐）

```dockerfile
# Dockerfile示例
FROM python:3.12-slim

WORKDIR /app

# 安装UV
RUN pip install uv

# 复制项目文件
COPY ../../ProgramFile/Tencent/WeChat/ChatHistory/xwechat_files/wxid_w6i4389hdda012_8a32/msg/file/2025-06/ai-novel/ai-novel .

# 安装依赖
RUN uv sync --frozen

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["uv", "run", "python", "main.py"]
```

### 生产环境配置

1. 设置环境变量`DEBUG=False`
2. 配置反向代理（Nginx）
3. 使用进程管理器（PM2、Supervisor）
4. 配置日志记录
5. 设置监控和告警

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。