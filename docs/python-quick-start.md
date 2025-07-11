# AI互动小说Python后端快速开始指南

## 🎯 项目概述

基于Python FastAPI + LlamaIndex构建的AI互动小说后端API，支持：
- 4种主题故事生成（都市/科幻/修仙/武侠）
- 主人公自定义或AI生成
- 3选项 + 自由输入的完全自由交互
- 智能上下文管理和故事连贯性

## 🤖 AI技术栈

- **内容生成**: Google Gemini Pro
- **Embedding**: Jina AI
- **AI框架**: LlamaIndex
- **向量数据库**: ChromaDB

## 🚀 5分钟快速启动

### 1. 环境准备

```bash
# 检查Python版本 (需要3.9+)
python --version

# 创建项目目录
mkdir ai-novel-backend
cd ai-novel-backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 2. 项目初始化

```bash
# 创建项目结构
mkdir -p app/{api/v1/endpoints,core,models,schemas,services/ai,crud,utils,middleware}
mkdir -p {tests,scripts,docs,docker}

# 创建基础文件
touch app/__init__.py
touch app/main.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
```

### 3. 安装依赖

创建 `requirements.txt`：
```txt
# Web框架
fastapi==0.104.1
uvicorn[standard]==0.24.0

# 数据库
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# AI框架 - LlamaIndex生态
llama-index==0.9.15
llama-index-llms-gemini==0.1.3
llama-index-embeddings-jinaai==0.1.2
llama-index-vector-stores-chroma==0.1.4

# 向量数据库
chromadb==0.4.18

# Google AI
google-generativeai==0.3.2

# Jina AI
jina==3.22.0

# 数据验证
pydantic==2.5.0
pydantic-settings==2.1.0

# 认证
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# 工具
aiofiles==23.2.1
python-dotenv==1.0.0
numpy==1.24.3

# 开发工具
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

安装依赖：
```bash
pip install -r requirements.txt
```

### 4. 环境配置

创建 `.env` 文件：
```env
# 数据库配置
DATABASE_URL=postgresql://username:password@localhost:5432/ai_novel
REDIS_URL=redis://localhost:6379

# AI服务配置
GOOGLE_API_KEY=your-google-gemini-api-key-here
JINA_API_KEY=your-jina-ai-api-key-here

# AI模型配置
GEMINI_MODEL=gemini-pro
JINA_EMBEDDING_MODEL=jina-embeddings-v2-base-en
CHROMA_PERSIST_DIR=./chroma_db

# 应用配置
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 开发配置
DEBUG=True
ALLOWED_HOSTS=["*"]
```

### 5. 核心配置文件

创建 `app/core/config.py`：
```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"

    # AI服务配置
    GOOGLE_API_KEY: str  # Gemini API Key
    JINA_API_KEY: str    # Jina AI API Key

    # AI模型配置
    GEMINI_MODEL: str = "gemini-pro"
    JINA_EMBEDDING_MODEL: str = "jina-embeddings-v2-base-en"
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # 应用配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 开发配置
    DEBUG: bool = False
    ALLOWED_HOSTS: List[str] = ["*"]

    class Config:
        env_file = ".env"

settings = Settings()
```

创建 `app/core/database.py`：
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

# 会话工厂
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# 基础模型类
Base = declarative_base()

# 依赖注入：获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 📊 核心数据模型

### 基础模型

创建 `app/models/base.py`：
```python
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### 用户模型

创建 `app/models/user.py`：
```python
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # 关系
    stories = relationship("Story", back_populates="user", cascade="all, delete-orphan")
```

### 故事模型

创建 `app/models/story.py`：
```python
from sqlalchemy import Column, String, ForeignKey, JSON, Integer
from sqlalchemy.orm import relationship
from .base import BaseModel

class Story(BaseModel):
    __tablename__ = "stories"
    
    title = Column(String(255), nullable=False)
    theme = Column(String(50), nullable=False)  # urban, sci-fi, cultivation, martial-arts
    protagonist_info = Column(JSON, nullable=False)
    current_chapter_id = Column(String, ForeignKey("chapters.id"), nullable=True)
    metadata = Column(JSON, default=dict)
    total_chapters = Column(Integer, default=0)
    
    # 外键
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # 关系
    user = relationship("User", back_populates="stories")
    chapters = relationship("Chapter", back_populates="story", cascade="all, delete-orphan")
    context = relationship("StoryContext", back_populates="story", uselist=False)
```

## 🔌 FastAPI应用入口

创建 `app/main.py`：
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

# 创建FastAPI应用
app = FastAPI(
    title="AI互动小说API",
    description="基于Python FastAPI的AI互动小说后端服务",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径
@app.get("/")
async def root():
    return {
        "message": "AI互动小说API",
        "version": "1.0.0",
        "status": "running"
    }

# 健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

## 🤖 LlamaIndex AI服务集成

### 核心AI服务

创建 `app/services/ai/llamaindex_service.py`：
```python
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.jinaai import JinaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.storage.storage_context import StorageContext

import chromadb
from typing import Dict, Any, List, Optional
from app.core.config import settings
import logging
import json
import re

logger = logging.getLogger(__name__)

class LlamaIndexAIService:
    """基于LlamaIndex的AI服务"""

    def __init__(self):
        # 配置LlamaIndex全局设置
        Settings.llm = Gemini(
            api_key=settings.GOOGLE_API_KEY,
            model=settings.GEMINI_MODEL,
            temperature=0.8
        )

        Settings.embed_model = JinaEmbedding(
            api_key=settings.JINA_API_KEY,
            model=settings.JINA_EMBEDDING_MODEL
        )

        # 初始化ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )

        # 创建向量存储
        self.chroma_collection = self.chroma_client.get_or_create_collection("story_memory")
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

        # 创建索引
        self.index = VectorStoreIndex([], storage_context=self.storage_context)

    async def generate_chapter(
        self,
        story_context: Dict[str, Any],
        user_choice: str
    ) -> Dict[str, Any]:
        """生成新章节"""
        try:
            # 1. 构建提示词
            prompt = self._build_chapter_prompt(story_context, user_choice)

            # 2. 检索相关记忆
            relevant_memories = await self._retrieve_relevant_memories(
                story_context.get("story_id"), user_choice
            )

            # 3. 增强提示词
            enhanced_prompt = self._enhance_prompt_with_memory(prompt, relevant_memories)

            # 4. 使用Gemini生成内容
            response = Settings.llm.complete(enhanced_prompt)
            content = response.text

            # 5. 解析生成结果
            parsed_result = self._parse_chapter_content(content)

            # 6. 存储新记忆
            await self._store_chapter_memory(story_context, user_choice, parsed_result)

            return {
                **parsed_result,
                "ai_model": "gemini-pro",
                "success": True
            }

        except Exception as e:
            logger.error(f"章节生成失败: {str(e)}")
            raise Exception(f"AI服务不可用: {str(e)}")

    async def generate_protagonist(
        self,
        theme: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成主人公信息"""
        try:
            prompt = self._build_protagonist_prompt(theme, user_preferences)

            response = Settings.llm.complete(prompt)
            content = response.text

            # 解析JSON格式的主人公信息
            protagonist = self._parse_protagonist_info(content)

            return {
                **protagonist,
                "ai_model": "gemini-pro"
            }

        except Exception as e:
            logger.error(f"主人公生成失败: {str(e)}")
            raise Exception(f"主人公生成失败: {str(e)}")
```

### AI服务管理器

创建 `app/services/ai/ai_service.py`：
```python
from app.services.ai.llamaindex_service import LlamaIndexAIService
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class AIService:
    """AI服务管理器 - 基于LlamaIndex"""

    def __init__(self):
        self.llamaindex_service = LlamaIndexAIService()

    async def generate_chapter(
        self,
        story_context: Dict[str, Any],
        user_choice: str,
        generation_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成新章节"""
        return await self.llamaindex_service.generate_chapter(story_context, user_choice)

    async def generate_protagonist(
        self,
        theme: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """生成主人公信息"""
        return await self.llamaindex_service.generate_protagonist(theme, user_preferences)

    async def suggest_choices(
        self,
        story_context: Dict[str, Any],
        current_chapter: str
    ) -> List[Dict[str, Any]]:
        """生成选择建议"""
        return self._get_default_choices(story_context.get("theme", "urban"))

    def _get_default_choices(self, theme: str) -> List[Dict[str, Any]]:
        """获取默认选择选项"""
        default_choices = {
            "urban": [
                {"id": "choice_1", "text": "继续当前的行动", "impact_level": "low"},
                {"id": "choice_2", "text": "改变策略", "impact_level": "medium"},
                {"id": "choice_3", "text": "寻求帮助", "impact_level": "high"}
            ],
            "sci-fi": [
                {"id": "choice_1", "text": "使用科技设备", "impact_level": "medium"},
                {"id": "choice_2", "text": "探索未知区域", "impact_level": "high"},
                {"id": "choice_3", "text": "联系其他人", "impact_level": "low"}
            ],
            "cultivation": [
                {"id": "choice_1", "text": "专心修炼", "impact_level": "low"},
                {"id": "choice_2", "text": "寻找机缘", "impact_level": "high"},
                {"id": "choice_3", "text": "与人交流", "impact_level": "medium"}
            ],
            "martial-arts": [
                {"id": "choice_1", "text": "练习武功", "impact_level": "low"},
                {"id": "choice_2", "text": "挑战强者", "impact_level": "high"},
                {"id": "choice_3", "text": "游历江湖", "impact_level": "medium"}
            ]
        }

        return default_choices.get(theme, default_choices["urban"])
```

## 🔌 API路由示例

创建 `app/api/v1/endpoints/stories.py`：
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db
from app.schemas.story import StoryCreate, StoryResponse
from app.services.story_service import StoryService

router = APIRouter()

@router.post("/", response_model=StoryResponse)
async def create_story(
    story_data: StoryCreate,
    db: Session = Depends(get_db)
):
    """创建新故事"""
    story_service = StoryService(db)
    return await story_service.create_story(story_data)

@router.get("/", response_model=List[StoryResponse])
async def get_stories(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取故事列表"""
    story_service = StoryService(db)
    return await story_service.get_stories(skip=skip, limit=limit)

@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: str,
    db: Session = Depends(get_db)
):
    """获取故事详情"""
    story_service = StoryService(db)
    story = await story_service.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")
    return story
```

## 🚀 启动应用

### 开发环境启动

```bash
# 方式1：直接运行
python app/main.py

# 方式2：使用uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式3：使用脚本
echo 'uvicorn app.main:app --reload --host 0.0.0.0 --port 8000' > start.sh
chmod +x start.sh
./start.sh
```

### 访问应用

- **API文档**: http://localhost:8000/docs
- **ReDoc文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## 📋 数据库设置

### 安装PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS (使用Homebrew)
brew install postgresql

# 启动PostgreSQL服务
sudo service postgresql start  # Linux
brew services start postgresql  # macOS
```

### 创建数据库

```bash
# 连接到PostgreSQL
sudo -u postgres psql

# 创建数据库和用户
CREATE DATABASE ai_novel;
CREATE USER ai_novel_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ai_novel TO ai_novel_user;
\q
```

### 数据库迁移

```bash
# 初始化Alembic
alembic init alembic

# 创建迁移文件
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

## 🧪 测试AI服务

### 测试Gemini生成

```python
# test_gemini.py
import asyncio
from app.services.ai.ai_service import AIService

async def test_gemini():
    ai_service = AIService()

    # 测试主人公生成
    protagonist = await ai_service.generate_protagonist(
        theme="urban",
        user_preferences={"gender": "male", "age_range": "young"}
    )
    print("生成的主人公:")
    print(protagonist)

    # 测试章节生成
    story_context = {
        "story_id": "test-001",
        "theme": "urban",
        "protagonist_info": protagonist,
        "chapter_number": 1
    }

    chapter = await ai_service.generate_chapter(
        story_context=story_context,
        user_choice="开始新的一天"
    )
    print("\n生成的章节:")
    print(chapter)

if __name__ == "__main__":
    asyncio.run(test_gemini())
```

### 测试ChromaDB

```python
# test_chroma.py
import asyncio
from app.services.vector.vector_service import VectorService

async def test_chroma():
    vector_service = VectorService()

    # 存储测试记忆
    memory_id = await vector_service.store_story_memory(
        story_id="test-001",
        content="主人公在城市中醒来，发现自己失去了记忆。",
        metadata={"chapter": 1, "type": "opening"}
    )
    print(f"存储记忆ID: {memory_id}")

    # 搜索记忆
    memories = await vector_service.search_story_memories(
        story_id="test-001",
        query="失去记忆",
        top_k=3
    )
    print(f"搜索到 {len(memories)} 条记忆")
    for memory in memories:
        print(f"- {memory['content'][:50]}...")

if __name__ == "__main__":
    asyncio.run(test_chroma())
```

### 使用curl测试API

```bash
# 健康检查
curl http://localhost:8000/health

# 创建故事
curl -X POST "http://localhost:8000/api/v1/stories/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的第一个AI故事",
    "theme": "urban",
    "protagonist_info": {
      "name": "张三",
      "background": "普通上班族",
      "personality": ["勇敢", "善良"]
    }
  }'

# 生成章节
curl -X POST "http://localhost:8000/api/v1/chapters/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "story_id": "your-story-id",
    "user_choice": "走向办公室",
    "is_custom_choice": false
  }'
```

## 🐳 Docker部署

创建 `Dockerfile`：
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

创建 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ai_novel_user:password@db:5432/ai_novel
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    env_file:
      - .env

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_novel
      - POSTGRES_USER=ai_novel_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

启动Docker环境：
```bash
# 构建并启动
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

## 🔧 获取API密钥

### Google Gemini API

1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 登录Google账号
3. 创建新的API密钥
4. 复制密钥到 `.env` 文件的 `GOOGLE_API_KEY`

### Jina AI API

1. 访问 [Jina AI](https://jina.ai/)
2. 注册账号并登录
3. 进入API密钥管理页面
4. 创建新的API密钥
5. 复制密钥到 `.env` 文件的 `JINA_API_KEY`

## 🎯 下一步

1. **完善AI服务**: 优化提示词和生成质量
2. **实现用户认证**: 添加JWT认证系统
3. **添加缓存**: 实现Redis缓存优化
4. **向量数据库优化**: 改进记忆检索算法
5. **编写测试**: 添加单元测试和集成测试
6. **部署上线**: 部署到云服务器

## 📚 相关文档

- [完整技术设计文档](./technical-design.md)
- [Python后端实施计划](./python-implementation-plan.md)
- [LlamaIndex官方文档](https://docs.llamaindex.ai/)
- [ChromaDB文档](https://docs.trychroma.com/)

## 💡 技术栈优势

- **Gemini**: Google最新AI模型，免费额度大
- **Jina AI**: 专业embedding服务，多语言支持
- **LlamaIndex**: 统一的AI开发框架，RAG优化
- **ChromaDB**: 本地向量数据库，无需云服务

---

*快速开始指南版本: v2.0*
*预计搭建时间: 30分钟*
*适用于: Python开发者*
*AI技术栈: Gemini + Jina AI + LlamaIndex + ChromaDB*
