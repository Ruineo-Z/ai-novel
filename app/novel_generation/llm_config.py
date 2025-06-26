import json

from llama_index.llms.gemini import Gemini
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from app.core.config import settings


def gemini_llm() -> Gemini:
    """创建Gemini LLM实例"""
    llm = Gemini(
        model=settings.GEMINI_MODEL,
        api_key=settings.GEMINI_API_KEY,
    )
    return llm


def ollama_llm() -> Ollama:
    """创建Ollama LLM实例"""
    llm = Ollama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
    )
    return llm


def openai_llm() -> OpenAI:
    """创建OpenAI LLM实例"""
    llm = OpenAI(
        model="gpt-4o-mini",
        api_key=settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else None,
    )
    return llm
