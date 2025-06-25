from crewai.llm import LLM

from app.core.config import settings

def gemini_llm(stream_model=True) -> LLM:
    llm = LLM(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        stream=stream_model
    )
    return llm

def ollama_llm(stream_model=True) -> LLM:
    llm = LLM(
        model=f"ollama/{settings.OLLAMA_MODEL}",
        base_url=settings.OLLAMA_BASE_URL,
        stream=stream_model
    )
    return llm