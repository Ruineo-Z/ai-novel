from app.schemas.base import AIModel
from app.services.ai_service import AIService
from app.services.gemini_service import GeminiService
from app.services.ollama_service import OllamaService


class AIServiceFactory:
    """AI服务工厂类"""

    @staticmethod
    def create_service(ai_model: AIModel) -> AIService:
        """根据模型类型创建对应的AI服务"""
        if ai_model == AIModel.GEMINI:
            return GeminiService()
        elif ai_model == AIModel.OLLAMA:
            return OllamaService()
        else:
            raise ValueError(f"Unsupported AI model: {ai_model}")

    @staticmethod
    def get_available_models() -> list[AIModel]:
        """获取可用的AI模型列表"""
        return [AIModel.GEMINI, AIModel.OLLAMA]
