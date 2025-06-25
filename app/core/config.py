import os
from typing import Optional, List

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # AI Model Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-preview-05-20")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "")

    # FastAPI Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
