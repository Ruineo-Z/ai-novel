import os
from typing import Optional, List

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # AI Model Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-2.5-flash-preview-05-20")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-05-20")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # FastAPI Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001
    DEBUG: bool = True

    # Application Settings
    MAX_CHAPTER_LENGTH: int = 2000
    MAX_CHOICES: int = 4
    DEFAULT_NOVEL_STYLE: str = "修仙"

    # Novel Styles
    NOVEL_STYLES: List[str] = [
        "修仙",
        "科幻",
        "都市",
        "言情",
        "武侠"
    ]

    # DataStore
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Neo4j Configuration
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
    AURA_INSTANCEID: str = os.getenv("AURA_INSTANCEID", "")
    AURA_INSTANCENAME: str = os.getenv("AURA_INSTANCENAME", "")

    def validate_config(self) -> bool:
        """验证关键配置是否正确设置"""
        required_fields = []

        # 检查AI模型配置
        if not self.GEMINI_API_KEY and not self.GOOGLE_API_KEY:
            required_fields.append("GEMINI_API_KEY or GOOGLE_API_KEY")

        # 检查Neo4j配置
        if self.NEO4J_URI and not self.NEO4J_PASSWORD:
            required_fields.append("NEO4J_PASSWORD")

        if required_fields:
            print(f"⚠️  Missing required configuration: {', '.join(required_fields)}")
            return False

        print("✅ Configuration validation passed")
        return True

    class Config:
        env_file = ".env"
        case_sensitive = True
        # 允许额外字段，避免验证错误
        extra = "ignore"  # 或者使用 "allow" 如果需要访问额外字段


settings = Settings()
