"""
AI互动小说 - 配置管理模块
基于Pydantic Settings的统一配置管理
"""

import os
from typing import List, Optional, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pydantic.networks import PostgresDsn, RedisDsn
from enum import Enum


class Environment(str, Enum):
    """环境类型枚举"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """应用配置类"""

    # === 基础应用配置 ===
    APP_NAME: str = Field(default="AI互动小说API", description="应用名称")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本")
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT, description="运行环境"
    )
    DEBUG: bool = Field(default=True, description="调试模式")

    # === 服务器配置 ===
    HOST: str = Field(default="0.0.0.0", description="服务器主机")
    PORT: int = Field(default=20000, description="服务器端口")
    RELOAD: bool = Field(default=True, description="热重载")

    # === 安全配置 ===
    SECRET_KEY: str = Field(
        default="your-super-secret-key-here-change-in-production-at-least-32-chars",
        description="JWT密钥",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT算法")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="访问令牌过期时间(分钟)"
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="允许的主机列表")

    # === 数据库配置 ===
    DATABASE_URL: Optional[str] = Field(None, description="数据库连接字符串")
    DATABASE_ECHO: bool = Field(default=False, description="数据库SQL日志")
    DATABASE_POOL_SIZE: int = Field(default=5, description="数据库连接池大小")
    DATABASE_MAX_OVERFLOW: int = Field(default=10, description="数据库连接池最大溢出")

    # === Redis配置 ===
    REDIS_URL: Optional[str] = Field(None, description="Redis连接字符串")
    REDIS_EXPIRE_TIME: int = Field(default=3600, description="Redis默认过期时间(秒)")

    # === AI服务配置 ===
    GOOGLE_API_KEY: str = Field(
        default="your-google-gemini-api-key-here", description="Google Gemini API密钥"
    )
    JINA_API_KEY: str = Field(
        default="your-jina-ai-api-key-here", description="Jina AI API密钥"
    )
    GEMINI_MODEL: str = Field(default="gemini-pro", description="Gemini模型名称")
    JINA_EMBEDDING_MODEL: str = Field(
        default="jina-embeddings-v2-base-en", description="Jina嵌入模型"
    )

    # === ChromaDB配置 ===
    CHROMA_HOST: str = Field(default="localhost", description="ChromaDB主机地址")
    CHROMA_PORT: int = Field(default=8000, description="ChromaDB端口")
    CHROMA_PERSIST_DIR: str = Field(
        default="./chroma_db", description="ChromaDB持久化目录"
    )
    CHROMA_COLLECTION_NAME: str = Field(
        default="story_memory", description="ChromaDB集合名称"
    )
    VECTOR_DIMENSION: int = Field(default=768, description="向量维度")
    MAX_SEARCH_RESULTS: int = Field(default=10, description="最大搜索结果数")

    # === AI服务限制 ===
    MAX_TOKENS_PER_REQUEST: int = Field(default=4000, description="每次请求最大token数")
    MAX_REQUESTS_PER_MINUTE: int = Field(default=60, description="每分钟最大请求数")
    AI_TIMEOUT_SECONDS: int = Field(default=30, description="AI服务超时时间(秒)")

    # === 日志配置 ===
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="日志级别")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式",
    )
    LOG_FILE: Optional[str] = Field(None, description="日志文件路径")

    # === CORS配置 ===
    CORS_ORIGINS: List[str] = Field(default=["*"], description="CORS允许的源")
    CORS_METHODS: List[str] = Field(default=["*"], description="CORS允许的方法")
    CORS_HEADERS: List[str] = Field(default=["*"], description="CORS允许的头部")

    # === 文件上传配置 ===
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024, description="最大文件大小(字节)"
    )
    UPLOAD_DIR: str = Field(default="./uploads", description="文件上传目录")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: Optional[str]) -> Optional[str]:
        """验证数据库URL"""
        if v is None:
            # 开发环境使用SQLite
            return "sqlite:///./ai_novel.db"
        return v

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """验证密钥强度"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("CHROMA_PERSIST_DIR", mode="before")
    @classmethod
    def create_chroma_dir(cls, v: str) -> str:
        """确保ChromaDB目录存在"""
        os.makedirs(v, exist_ok=True)
        return v

    @field_validator("UPLOAD_DIR", mode="before")
    @classmethod
    def create_upload_dir(cls, v: str) -> str:
        """确保上传目录存在"""
        os.makedirs(v, exist_ok=True)
        return v

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.ENVIRONMENT == Environment.TESTING

    @property
    def chroma_url(self) -> str:
        """ChromaDB连接URL"""
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def database_url_sync(self) -> str:
        """同步数据库URL"""
        if self.DATABASE_URL:
            return str(self.DATABASE_URL).replace(
                "postgresql://", "postgresql+psycopg2://"
            )
        return "sqlite:///./ai_novel.db"

    @property
    def database_url_async(self) -> str:
        """异步数据库URL"""
        if self.DATABASE_URL:
            db_url = str(self.DATABASE_URL)
            if db_url.startswith("postgresql://"):
                return db_url.replace("postgresql://", "postgresql+asyncpg://")
            if db_url.startswith("sqlite://"):
                return db_url.replace("sqlite://", "sqlite+aiosqlite://")
            return db_url
        return "sqlite+aiosqlite:///./ai_novel.db"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例 - 用于依赖注入"""
    return settings


# 配置验证函数
def validate_ai_services() -> bool:
    """验证AI服务配置"""
    try:
        if (
            not settings.GOOGLE_API_KEY
            or settings.GOOGLE_API_KEY == "your-google-gemini-api-key-here"
        ):
            return False
        if (
            not settings.JINA_API_KEY
            or settings.JINA_API_KEY == "your-jina-ai-api-key-here"
        ):
            return False
        return True
    except Exception:
        return False


def validate_database_connection() -> bool:
    """验证数据库连接配置"""
    try:
        if settings.DATABASE_URL:
            # 验证PostgreSQL连接格式
            return str(settings.DATABASE_URL).startswith(("postgresql://", "sqlite://"))
        return True  # SQLite默认配置
    except Exception:
        return False


def get_cors_config() -> dict:
    """获取CORS配置"""
    return {
        "allow_origins": settings.CORS_ORIGINS,
        "allow_credentials": True,
        "allow_methods": settings.CORS_METHODS,
        "allow_headers": settings.CORS_HEADERS,
    }


def get_logging_config() -> dict:
    """获取日志配置"""
    # 获取日志级别字符串
    log_level = str(settings.LOG_LEVEL)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": log_level,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }

    # 如果指定了日志文件，添加文件处理器
    if settings.LOG_FILE:
        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": settings.LOG_FILE,
            "formatter": "default",
            "level": log_level,
        }
        config["root"]["handlers"].append("file")

    return config
