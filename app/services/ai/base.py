"""
AI服务基础模块 - 提供通用的AI服务功能
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

import httpx
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.jinaai import JinaEmbedding

from app.core.config import settings


logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """AI服务异常基类"""
    pass


class AIServiceTimeoutError(AIServiceError):
    """AI服务超时异常"""
    pass


class AIServiceQuotaError(AIServiceError):
    """AI服务配额异常"""
    pass


class StoryTheme(str, Enum):
    """故事主题枚举"""
    URBAN = "urban"          # 都市
    SCIFI = "scifi"          # 科幻
    CULTIVATION = "cultivation"  # 修仙
    MARTIAL_ARTS = "martial_arts"  # 武侠
    FANTASY = "fantasy"      # 奇幻
    ROMANCE = "romance"      # 言情
    MYSTERY = "mystery"      # 悬疑
    HISTORICAL = "historical"  # 历史


class ContentType(str, Enum):
    """内容类型枚举"""
    STORY_OPENING = "story_opening"    # 故事开头
    CHAPTER_CONTENT = "chapter_content"  # 章节内容
    CHOICE_OPTIONS = "choice_options"   # 选择选项
    CHARACTER_DESCRIPTION = "character_description"  # 角色描述


@dataclass
class AIRequest:
    """AI请求数据结构"""
    content_type: ContentType
    theme: StoryTheme
    prompt: str
    context: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.max_tokens is None:
            self.max_tokens = settings.MAX_TOKENS_PER_REQUEST
        if self.temperature is None:
            self.temperature = 0.7


@dataclass
class AIResponse:
    """AI响应数据结构"""
    content: str
    tokens_used: int
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def is_valid(self) -> bool:
        """检查响应是否有效"""
        return bool(self.content and self.content.strip())


class BaseAIService(ABC):
    """AI服务基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_clients()
    
    def _setup_clients(self):
        """设置AI客户端"""
        try:
            # 配置LlamaIndex Gemini LLM
            if settings.GOOGLE_API_KEY:
                self.gemini_llm = Gemini(
                    model=settings.GEMINI_MODEL,
                    api_key=settings.GOOGLE_API_KEY,
                    temperature=0.7
                )
                self.logger.info(f"LlamaIndex Gemini LLM初始化成功: {settings.GEMINI_MODEL}")
            else:
                self.gemini_llm = None
                self.logger.warning("Gemini API密钥未配置")

            # 配置LlamaIndex Jina AI Embedding
            if settings.JINA_API_KEY:
                self.jina_embedding = JinaEmbedding(
                    api_key=settings.JINA_API_KEY,
                    model=settings.JINA_EMBEDDING_MODEL,
                    task="retrieval.passage"  # 默认用于文档嵌入
                )
                self.logger.info(f"LlamaIndex Jina AI Embedding初始化成功: {settings.JINA_EMBEDDING_MODEL}")
            else:
                self.jina_embedding = None
                self.logger.warning("Jina AI API密钥未配置")
                
        except Exception as e:
            self.logger.error(f"AI客户端初始化失败: {e}")
            raise AIServiceError(f"AI服务初始化失败: {e}")
    
    async def _call_gemini(self, prompt: str, **kwargs) -> str:
        """调用LlamaIndex Gemini LLM"""
        if not self.gemini_llm:
            raise AIServiceError("Gemini LLM未初始化")

        try:
            # 使用LlamaIndex的异步complete方法
            response = await self.gemini_llm.acomplete(prompt)

            if not response.text:
                raise AIServiceError("Gemini返回空内容")

            self.logger.debug(f"Gemini响应: {response.text[:100]}...")
            return response.text

        except Exception as e:
            self.logger.error(f"Gemini LLM调用失败: {e}")
            if "quota" in str(e).lower() or "rate" in str(e).lower():
                raise AIServiceQuotaError(f"Gemini API配额不足: {e}")
            raise AIServiceError(f"Gemini LLM调用失败: {e}")
    
    async def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本向量"""
        if not self.jina_embedding:
            raise AIServiceError("Jina AI Embedding未初始化")

        try:
            # 使用LlamaIndex的异步get_text_embedding_batch方法
            embeddings = await self.jina_embedding.aget_text_embedding_batch(texts)

            self.logger.debug(f"获取到{len(embeddings)}个向量，维度: {len(embeddings[0]) if embeddings else 0}")
            return embeddings

        except Exception as e:
            self.logger.error(f"Jina AI向量化失败: {e}")
            raise AIServiceError(f"向量化服务调用失败: {e}")
    
    def _validate_request(self, request: AIRequest) -> None:
        """验证AI请求"""
        if not request.prompt or not request.prompt.strip():
            raise ValueError("提示词不能为空")
        
        if len(request.prompt) > 10000:
            raise ValueError("提示词过长，最大支持10000字符")
        
        if request.max_tokens and request.max_tokens > settings.MAX_TOKENS_PER_REQUEST:
            raise ValueError(f"最大token数不能超过{settings.MAX_TOKENS_PER_REQUEST}")
    
    @abstractmethod
    async def process(self, request: AIRequest) -> AIResponse:
        """处理AI请求 - 子类必须实现"""
        pass
    
    def get_theme_prompt_prefix(self, theme: StoryTheme) -> str:
        """获取主题相关的提示词前缀"""
        theme_prompts = {
            StoryTheme.URBAN: "现代都市背景，现实主义风格，关注都市生活和人际关系",
            StoryTheme.SCIFI: "科幻背景，未来科技，太空探索，人工智能等元素",
            StoryTheme.CULTIVATION: "修仙世界，灵气修炼，法宝丹药，仙侠风格",
            StoryTheme.MARTIAL_ARTS: "武侠江湖，武功秘籍，侠义精神，古代背景",
            StoryTheme.FANTASY: "奇幻世界，魔法元素，神话生物，冒险故事",
            StoryTheme.ROMANCE: "爱情故事，情感描写，浪漫情节，人物关系",
            StoryTheme.MYSTERY: "悬疑推理，谜团解密，紧张氛围，逻辑推演",
            StoryTheme.HISTORICAL: "历史背景，真实历史事件，古代文化，历史人物"
        }
        return theme_prompts.get(theme, "通用故事背景")


class AIServiceManager:
    """AI服务管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._services: Dict[str, BaseAIService] = {}
    
    def register_service(self, name: str, service: BaseAIService):
        """注册AI服务"""
        self._services[name] = service
        self.logger.info(f"注册AI服务: {name}")
    
    def get_service(self, name: str) -> Optional[BaseAIService]:
        """获取AI服务"""
        return self._services.get(name)
    
    def list_services(self) -> List[str]:
        """列出所有服务"""
        return list(self._services.keys())
    
    async def health_check(self) -> Dict[str, bool]:
        """健康检查"""
        results = {}
        for name, service in self._services.items():
            try:
                # 简单的健康检查 - 检查LLM和Embedding是否初始化
                if hasattr(service, 'gemini_llm') and service.gemini_llm:
                    # 测试简单的LLM调用
                    test_response = await service.gemini_llm.acomplete("Hello")
                    if test_response.text:
                        results[name] = True
                    else:
                        results[name] = False
                else:
                    results[name] = False
            except Exception as e:
                self.logger.error(f"服务{name}健康检查失败: {e}")
                results[name] = False

        return results


# 全局AI服务管理器实例
ai_service_manager = AIServiceManager()
