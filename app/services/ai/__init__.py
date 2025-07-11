"""
AI服务模块 - 提供AI相关的服务功能
"""
from app.services.ai.base import ai_service_manager, AIServiceError, AIServiceTimeoutError, AIServiceQuotaError
from app.services.ai.story_generator import StoryGeneratorService, StoryGenerationRequest, ChapterGenerationRequest
from app.services.ai.choice_generator import ChoiceGeneratorService, ChoiceGenerationRequest, ChoiceOption
from app.services.ai.memory_manager import MemoryManagerService, MemoryItem, MemoryQuery, MemorySearchResult

# 导出主要类和函数
__all__ = [
    # 基础类
    "ai_service_manager",
    "AIServiceError",
    "AIServiceTimeoutError",
    "AIServiceQuotaError",

    # 故事生成
    "StoryGeneratorService",
    "StoryGenerationRequest",
    "ChapterGenerationRequest",

    # 选择生成
    "ChoiceGeneratorService",
    "ChoiceGenerationRequest",
    "ChoiceOption",

    # 记忆管理
    "MemoryManagerService",
    "MemoryItem",
    "MemoryQuery",
    "MemorySearchResult",

    # 初始化函数
    "init_ai_services",
    "get_story_generator",
    "get_choice_generator",
    "get_memory_manager"
]

# 全局服务实例
_story_generator = None
_choice_generator = None
_memory_manager = None


def init_ai_services():
    """初始化AI服务"""
    global _story_generator, _choice_generator, _memory_manager

    try:
        # 创建服务实例
        _story_generator = StoryGeneratorService()
        _choice_generator = ChoiceGeneratorService()
        _memory_manager = MemoryManagerService()

        # 注册到管理器
        ai_service_manager.register_service("story_generator", _story_generator)
        ai_service_manager.register_service("choice_generator", _choice_generator)
        ai_service_manager.register_service("memory_manager", _memory_manager)

        return True

    except Exception as e:
        print(f"AI服务初始化失败: {e}")
        return False


def get_story_generator() -> StoryGeneratorService:
    """获取故事生成服务"""
    if _story_generator is None:
        raise RuntimeError("AI服务未初始化，请先调用init_ai_services()")
    return _story_generator


def get_choice_generator() -> ChoiceGeneratorService:
    """获取选择生成服务"""
    if _choice_generator is None:
        raise RuntimeError("AI服务未初始化，请先调用init_ai_services()")
    return _choice_generator


def get_memory_manager() -> MemoryManagerService:
    """获取记忆管理服务"""
    if _memory_manager is None:
        raise RuntimeError("AI服务未初始化，请先调用init_ai_services()")
    return _memory_manager