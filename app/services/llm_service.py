from langchain.llms import OpenAI, Ollama
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from app.core.config import settings
from app.core.redis_client import redis_client
import json
import time
import asyncio

class LLMService:
    def __init__(self):
        self.models = {}
        self._initialize_models()
        
    def _initialize_models(self):
        """初始化各种LLM模型"""
        # OpenAI
        if settings.OPENAI_API_KEY:
            self.models['openai'] = ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
                model_name="gpt-3.5-turbo",
                temperature=0.7
            )
        
        # Gemini
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.models['gemini'] = genai.GenerativeModel('gemini-pro')
        
        # Ollama
        try:
            self.models['ollama'] = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model="llama2"
            )
        except Exception as e:
            print(f"Failed to initialize Ollama: {e}")
    
    async def generate_outline(self, genre: str, world_setting: str, 
                             protagonist_info: Dict) -> str:
        """生成小说大纲"""
        cache_key = f"outline:{hash(f'{genre}_{world_setting}_{str(protagonist_info)}')}"
        # 检查缓存
        cached_outline = await redis_client.get(cache_key)
        if cached_outline:
            return cached_outline
        
        prompt = f"""
        请为以下设定生成一个详细的小说大纲：
        
        类型：{genre}
        世界观：{world_setting}
        主人公信息：{protagonist_info}
        
        要求：
        1. 大纲应包含5-8个主要章节
        2. 每个章节都有明确的冲突和转折点
        3. 整体故事结构完整，有起承转合
        4. 适合互动式阅读，留有用户选择的空间
        5. 字数控制在800-1200字
        
        请直接返回大纲内容，不要包含其他说明文字。
        """
        
        outline = await self._call_llm('openai', prompt)
        
        # 缓存结果
        await redis_client.set(cache_key, outline, expire=3600*24)  # 缓存24小时
        
        return outline
    
    async def generate_chapter(self, novel_context: str, previous_chapters: List[str],
                             user_choice: Optional[str] = None, 
                             temperature: float = 0.7,
                             max_tokens: int = 1500,
                             model_name: str = 'openai') -> Dict:
        """生成章节内容"""
        context = "\n\n".join(previous_chapters[-3:])  # 只保留最近3章的上下文
        
        prompt = f"""
        基于以下小说背景和前文，生成下一章节的内容：
        
        小说背景：
        {novel_context}
        
        前文内容：
        {context}
        
        用户选择：{user_choice or '无特定选择，请自然发展剧情'}
        
        要求：
        1. 章节长度800-1200字
        2. 情节紧凑，有足够的戏剧冲突
        3. 在章节结尾提供3个不同的选择选项
        4. 选择选项应该影响后续剧情发展
        5. 保持角色性格一致性
        6. 语言生动，富有画面感
        
        请以JSON格式返回，格式如下：
        {{
            "content": "章节正文内容",
            "choices": [
                "选择1：具体描述",
                "选择2：具体描述", 
                "选择3：具体描述"
            ]
        }}
        
        注意：只返回JSON，不要包含其他文字。
        """
        
        start_time = time.time()
        response = await self._call_llm(model_name, prompt, temperature, max_tokens)
        generation_time = time.time() - start_time
        
        result = self._parse_json_response(response)
        result['generation_time'] = generation_time
        result['model_used'] = model_name
        
        return result
    
    async def evaluate_content_quality(self, content: str) -> float:
        """评估内容质量"""
        prompt = f"""
        请评估以下小说章节的质量，从以下几个维度打分（1-10分）：
        1. 情节连贯性
        2. 语言表达质量
        3. 人物刻画
        4. 戏剧冲突
        5. 阅读体验
        
        章节内容：
        {content}
        
        请只返回一个0-10之间的数字，表示综合质量评分。
        """
        
        try:
            response = await self._call_llm('openai', prompt, temperature=0.3)
            # 提取数字
            import re
            score_match = re.search(r'\b([0-9](?:\.[0-9])?|10(?:\.0)?)\b', response)
            if score_match:
                return float(score_match.group(1))
            return 5.0  # 默认分数
        except Exception:
            return 5.0
    
    async def _call_llm(self, model_name: str, prompt: str, 
                       temperature: float = 0.7, max_tokens: int = 1500) -> str:
        """调用指定的LLM模型"""
        if model_name not in self.models:
            # 如果指定模型不可用，使用默认模型
            available_models = list(self.models.keys())
            if not available_models:
                raise ValueError("No LLM models available")
            model_name = available_models[0]
        
        model = self.models[model_name]
        
        try:
            if model_name == 'openai':
                model.temperature = temperature
                model.max_tokens = max_tokens
                messages = [HumanMessage(content=prompt)]
                response = await model.agenerate([messages])
                return response.generations[0][0].text
            
            elif model_name == 'gemini':
                response = await asyncio.to_thread(model.generate_content, prompt)
                return response.text
            
            elif model_name == 'ollama':
                response = await model.agenerate([prompt])
                return response.generations[0][0].text
                
        except Exception as e:
            print(f"Error calling {model_name}: {e}")
            # 尝试使用备用模型
            available_models = [m for m in self.models.keys() if m != model_name]
            if available_models:
                return await self._call_llm(available_models[0], prompt, temperature, max_tokens)
            raise e
    
    def _parse_json_response(self, response: str) -> Dict:
        """解析LLM返回的JSON响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                # 尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
            
            # 如果解析失败，返回默认结构
            return {
                "content": response,
                "choices": ["继续阅读", "查看详情", "做出决定"]
            }
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        return list(self.models.keys())
    
    async def test_model_connection(self, model_name: str) -> bool:
        """测试模型连接"""
        try:
            test_prompt = "请回复'连接成功'"
            response = await self._call_llm(model_name, test_prompt)
            return "成功" in response or "success" in response.lower()
        except Exception:
            return False