"""
AI互动小说 - 配置管理模块
基于Pydantic Settings的统一配置管理
"""

import os
import json
from typing import List, Optional
from enum import Enum
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# 确保加载.env文件，覆盖现有环境变量
load_dotenv(override=True)


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
    APP_NAME: str = Field(default="AI互动小说API", description="应用名称", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", description="应用版本", env="APP_VERSION")
    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT, description="运行环境", env="ENVIRONMENT"
    )
    DEBUG: bool = Field(default=True, description="调试模式", env="DEBUG")

    # === 服务器配置 ===
    HOST: str = Field(default="0.0.0.0", description="服务器主机", env="HOST")
    PORT: int = Field(default=20000, description="服务器端口", env="PORT")
    RELOAD: bool = Field(default=True, description="热重载", env="RELOAD")

    # === 安全配置 ===
    SECRET_KEY: str = Field(
        default="your-super-secret-key-here-change-in-production-at-least-32-chars",
        description="JWT密钥",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", description="JWT算法", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="访问令牌过期时间(分钟)", env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="允许的主机列表")

    # === 数据库配置 ===
    DATABASE_URL: Optional[str] = Field(None, description="数据库连接字符串", env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(default=False, description="数据库SQL日志", env="DATABASE_ECHO")
    DATABASE_POOL_SIZE: int = Field(
        default=5, description="数据库连接池大小", env="DATABASE_POOL_SIZE"
    )
    DATABASE_MAX_OVERFLOW: int = Field(
        default=10, description="数据库连接池最大溢出", env="DATABASE_MAX_OVERFLOW"
    )

    # === Redis配置 ===
    REDIS_URL: Optional[str] = Field(
        None, description="Redis连接字符串", env="REDIS_URL"
    )
    REDIS_EXPIRE_TIME: int = Field(
        default=3600, description="Redis默认过期时间(秒)", env="REDIS_EXPIRE_TIME"
    )

    # === AI服务配置 ===
    GOOGLE_API_KEY: Optional[str] = Field(
        default="your-google-gemini-api-key-here",
        description="Google Gemini API密钥",
        env="GOOGLE_API_KEY"
    )
    JINA_API_KEY: Optional[str] = Field(
        default="your-jina-ai-api-key-here",
        description="Jina AI API密钥",
        env="JINA_API_KEY"
    )
    GEMINI_MODEL: str = Field(
        default="models/gemini-1.5-flash", description="Gemini模型名称", env="GEMINI_MODEL"
    )
    JINA_EMBEDDING_MODEL: str = Field(
        default="jina-embeddings-v3", description="Jina嵌入模型", env="JINA_EMBEDDING_MODEL"
    )

    # === ChromaDB配置 ===
    CHROMA_HOST: str = Field(
        default="localhost", description="ChromaDB主机地址", env="CHROMA_HOST"
    )
    CHROMA_PORT: int = Field(
        default=8000, description="ChromaDB端口", env="CHROMA_PORT"
    )
    CHROMA_PERSIST_DIR: str = Field(
        default="./chroma_db", description="ChromaDB持久化目录", env="CHROMA_PERSIST_DIR"
    )
    CHROMA_COLLECTION_NAME: str = Field(
        default="story_memory", description="ChromaDB集合名称", env="CHROMA_COLLECTION_NAME"
    )
    VECTOR_DIMENSION: int = Field(
        default=1024, description="向量维度", env="VECTOR_DIMENSION"
    )
    MAX_SEARCH_RESULTS: int = Field(
        default=10, description="最大搜索结果数", env="MAX_SEARCH_RESULTS"
    )

    # === AI服务限制 ===
    MAX_TOKENS_PER_REQUEST: int = Field(
        default=4000, description="每次请求最大token数", env="MAX_TOKENS_PER_REQUEST"
    )
    MAX_REQUESTS_PER_MINUTE: int = Field(
        default=60, description="每分钟最大请求数", env="MAX_REQUESTS_PER_MINUTE"
    )
    AI_TIMEOUT_SECONDS: int = Field(
        default=30, description="AI服务超时时间(秒)", env="AI_TIMEOUT_SECONDS"
    )

    # === 日志配置 ===
    LOG_LEVEL: LogLevel = Field(default=LogLevel.INFO, description="日志级别", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="日志格式",
        env="LOG_FORMAT"
    )
    LOG_FILE: Optional[str] = Field(None, description="日志文件路径", env="LOG_FILE")

    # === CORS配置 ===
    CORS_ORIGINS: List[str] = Field(
        default=["*"], description="CORS允许的源", env="CORS_ORIGINS"
    )
    CORS_METHODS: List[str] = Field(
        default=["*"], description="CORS允许的方法", env="CORS_METHODS"
    )
    CORS_HEADERS: List[str] = Field(
        default=["*"], description="CORS允许的头部", env="CORS_HEADERS"
    )

    # === 文件上传配置 ===
    MAX_FILE_SIZE: int = Field(
        default=10 * 1024 * 1024, description="最大文件大小(字节)", env="MAX_FILE_SIZE"
    )
    UPLOAD_DIR: str = Field(
        default="./uploads", description="文件上传目录", env="UPLOAD_DIR"
    )

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

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """解析CORS源配置"""
        if isinstance(v, str):
            try:
                # 尝试解析JSON字符串
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [v]  # 如果不是列表，作为单个值处理
            except json.JSONDecodeError:
                # 如果不是JSON，按逗号分割
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]  # 默认值

    @field_validator("CORS_METHODS", "CORS_HEADERS", mode="before")
    @classmethod
    def parse_cors_list(cls, v) -> List[str]:
        """解析CORS方法和头部配置"""
        if isinstance(v, str):
            try:
                # 尝试解析JSON字符串
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                return [v]  # 如果不是列表，作为单个值处理
            except json.JSONDecodeError:
                # 如果不是JSON，按逗号分割
                return [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]  # 默认值

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
        "env_file": [".env", "../.env"],
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
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
    except (AttributeError, ValueError, TypeError):
        return False


def validate_database_connection() -> bool:
    """验证数据库连接配置"""
    try:
        if settings.DATABASE_URL:
            # 验证PostgreSQL连接格式
            return str(settings.DATABASE_URL).startswith(("postgresql://", "sqlite://"))
        return True  # SQLite默认配置
    except (AttributeError, ValueError, TypeError):
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
