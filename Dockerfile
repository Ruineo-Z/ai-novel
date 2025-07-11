# AI互动小说API - Dockerfile
# 多阶段构建，支持开发和生产环境

# ===== 基础镜像 =====
FROM python:3.12-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装uv包管理器
RUN pip install uv

# 设置工作目录
WORKDIR /app

# ===== 开发环境 =====
FROM base as development

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装依赖（包括开发依赖）
RUN uv sync --dev

# 复制源代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs uploads chroma_db

# 设置权限
RUN chmod +x scripts/*.sh

# 暴露端口
EXPOSE 20000

# 开发环境启动命令（支持热重载）
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "20000", "--reload"]

# ===== 生产环境 =====
FROM base as production

# 复制依赖文件
COPY pyproject.toml uv.lock ./

# 安装生产依赖
RUN uv sync --no-dev

# 复制源代码
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# 创建必要的目录
RUN mkdir -p logs uploads chroma_db

# 创建非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 20000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:20000/health || exit 1

# 生产环境启动命令
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "20000", "--workers", "4"]
