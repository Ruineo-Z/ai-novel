# AI互动小说项目

基于Python FastAPI + LlamaIndex构建的AI驱动互动小说平台。

## 🎯 项目特色

- **4种主题故事**：都市、科幻、修仙、武侠
- **智能主人公生成**：用户自定义或AI生成
- **完全自由交互**：3选项 + 自由输入
- **上下文感知**：基于历史内容的智能章节生成
- **向量记忆管理**：ChromaDB驱动的故事记忆系统

## 🛠️ 技术栈

- **后端框架**: FastAPI + SQLAlchemy + Alembic
- **AI框架**: LlamaIndex
- **AI服务**: Google Gemini Pro + Jina AI Embedding
- **向量数据库**: ChromaDB
- **关系数据库**: PostgreSQL
- **依赖管理**: uv
- **测试框架**: pytest + httpx

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- PostgreSQL 12+
- uv (Python包管理器)

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd ai-novel

# 安装依赖
uv sync --dev
```

### 3. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
# 需要配置：
# - DATABASE_URL: PostgreSQL连接字符串
# - GOOGLE_API_KEY: Google Gemini API密钥
# - JINA_API_KEY: Jina AI API密钥
```

### 4. 启动应用

```bash
# 开发模式启动
uv run python -m app.main

# 或使用uvicorn
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 20000
```

### 5. 访问应用

- **API文档**: http://localhost:20000/docs
- **ReDoc文档**: http://localhost:20000/redoc
- **健康检查**: http://localhost:20000/health

## 🧪 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行测试并显示覆盖率
uv run pytest --cov=app

# 运行特定测试文件
uv run pytest tests/test_main.py

# 运行异步测试
uv run pytest tests/ -v
```

## 📁 项目结构

```
ai-novel/
├── app/                    # 应用代码
│   ├── core/              # 核心配置
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic模式
│   ├── services/          # 业务逻辑
│   ├── api/               # API路由
│   ├── utils/             # 工具函数
│   └── main.py            # 应用入口
├── tests/                 # 测试文件
├── docs/                  # 项目文档
├── scripts/               # 脚本文件
├── pyproject.toml         # 项目配置
├── .env.example           # 环境变量模板
└── README.md              # 项目说明
```

## 🔧 开发指南

### 代码规范

```bash
# 代码格式化
uv run black app/ tests/
uv run isort app/ tests/

# 类型检查
uv run mypy app/

# 代码质量检查
uv run flake8 app/
```

### 数据库迁移

```bash
# 创建迁移文件
uv run alembic revision --autogenerate -m "描述"

# 执行迁移
uv run alembic upgrade head

# 回滚迁移
uv run alembic downgrade -1
```

## 📚 API文档

启动应用后访问 http://localhost:20000/docs 查看完整的API文档。

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 获取帮助

- 查看 [文档](docs/)
- 提交 [Issue](../../issues)
- 联系维护者

---

**开发状态**: 🚧 开发中

**当前版本**: v0.1.0

**最后更新**: 2024-01-10