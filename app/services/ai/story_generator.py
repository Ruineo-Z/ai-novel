"""
故事生成服务 - 负责生成故事开头和章节内容
"""
import time
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.services.ai.base import (
    BaseAIService, AIRequest, AIResponse, 
    StoryTheme, ContentType, AIServiceError
)
from app.models.story import Story
from app.models.chapter import Chapter


@dataclass
class StoryGenerationRequest:
    """故事生成请求"""
    theme: StoryTheme
    title: str
    protagonist_name: str
    protagonist_description: str
    story_background: str
    user_preferences: Optional[Dict[str, Any]] = None
    
    def to_ai_request(self) -> AIRequest:
        """转换为AI请求"""
        prompt = self._build_story_prompt()
        return AIRequest(
            content_type=ContentType.STORY_OPENING,
            theme=self.theme,
            prompt=prompt,
            context={
                "title": self.title,
                "protagonist": {
                    "name": self.protagonist_name,
                    "description": self.protagonist_description
                },
                "background": self.story_background,
                "preferences": self.user_preferences or {}
            }
        )
    
    def _build_story_prompt(self) -> str:
        """构建故事生成提示词"""
        return f"""
你是一位专业的互动小说作家，请根据以下信息创作一个引人入胜的故事开头。

## 故事设定
- **主题风格**: {self.theme.value}
- **故事标题**: {self.title}
- **主角姓名**: {self.protagonist_name}
- **主角描述**: {self.protagonist_description}
- **故事背景**: {self.story_background}

## 创作要求
1. **字数控制**: 800-1200字
2. **情节设置**: 创造一个引人入胜的开头，设置悬念或冲突
3. **人物塑造**: 突出主角的特点和性格
4. **环境描写**: 生动描绘故事发生的环境和氛围
5. **互动设计**: 在故事结尾设置一个关键选择点，为后续剧情发展做铺垫

## 输出格式
请按以下JSON格式输出：
```json
{{
    "content": "故事正文内容",
    "summary": "本章节摘要（50字以内）",
    "key_elements": ["关键情节元素1", "关键情节元素2", "关键情节元素3"],
    "mood": "整体氛围（如：紧张、轻松、神秘等）",
    "choice_setup": "为下一个选择点设置的情境描述"
}}
```

请开始创作：
"""


@dataclass
class ChapterGenerationRequest:
    """章节生成请求"""
    story_id: str
    previous_chapters: List[Dict[str, Any]]
    user_choice: str
    choice_description: str
    story_context: Dict[str, Any]
    
    def to_ai_request(self) -> AIRequest:
        """转换为AI请求"""
        prompt = self._build_chapter_prompt()
        theme = StoryTheme(self.story_context.get("theme", "urban"))
        
        return AIRequest(
            content_type=ContentType.CHAPTER_CONTENT,
            theme=theme,
            prompt=prompt,
            context={
                "story_id": self.story_id,
                "previous_chapters": self.previous_chapters,
                "user_choice": self.user_choice,
                "story_context": self.story_context
            }
        )
    
    def _build_chapter_prompt(self) -> str:
        """构建章节生成提示词"""
        # 构建前情回顾
        previous_summary = self._build_previous_summary()
        
        return f"""
你是一位专业的互动小说作家，请根据用户的选择继续创作故事。

## 故事背景
{self.story_context.get('background', '')}

## 前情回顾
{previous_summary}

## 用户选择
用户选择了：{self.user_choice}
选择说明：{self.choice_description}

## 创作要求
1. **承接自然**: 根据用户选择自然地继续故事情节
2. **字数控制**: 600-1000字
3. **情节推进**: 推动故事情节发展，增加新的冲突或转折
4. **人物发展**: 深化角色性格，展现人物成长
5. **保持一致**: 与前面章节的风格和设定保持一致
6. **设置悬念**: 为下一个选择点做好铺垫

## 输出格式
请按以下JSON格式输出：
```json
{{
    "content": "章节正文内容",
    "summary": "本章节摘要（50字以内）",
    "key_elements": ["关键情节元素1", "关键情节元素2", "关键情节元素3"],
    "mood": "整体氛围",
    "character_development": "主角在本章的成长或变化",
    "choice_setup": "为下一个选择点设置的情境描述"
}}
```

请开始创作：
"""
    
    def _build_previous_summary(self) -> str:
        """构建前情回顾"""
        if not self.previous_chapters:
            return "这是故事的开始。"
        
        summaries = []
        for i, chapter in enumerate(self.previous_chapters[-3:], 1):  # 只回顾最近3章
            summary = chapter.get('summary', '')
            if summary:
                summaries.append(f"第{i}章：{summary}")
        
        return "\n".join(summaries) if summaries else "前面的故事情节..."


class StoryGeneratorService(BaseAIService):
    """故事生成服务"""
    
    def __init__(self):
        super().__init__()
        self.logger.info("故事生成服务初始化完成")
    
    async def process(self, request: AIRequest) -> AIResponse:
        """处理故事生成请求"""
        self._validate_request(request)
        
        start_time = time.time()
        
        try:
            # 调用Gemini生成内容
            raw_content = await self._call_gemini(
                request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # 解析生成的内容
            parsed_content = self._parse_generated_content(raw_content)
            
            processing_time = time.time() - start_time
            
            return AIResponse(
                content=parsed_content["content"],
                tokens_used=len(raw_content.split()),  # 简单估算
                processing_time=processing_time,
                metadata={
                    "summary": parsed_content.get("summary"),
                    "key_elements": parsed_content.get("key_elements", []),
                    "mood": parsed_content.get("mood"),
                    "choice_setup": parsed_content.get("choice_setup"),
                    "character_development": parsed_content.get("character_development"),
                    "raw_response": raw_content
                }
            )
            
        except Exception as e:
            self.logger.error(f"故事生成失败: {e}")
            raise AIServiceError(f"故事生成失败: {e}")
    
    def _parse_generated_content(self, raw_content: str) -> Dict[str, Any]:
        """解析生成的内容"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                return json.loads(json_str)
            
            # 如果没有找到JSON格式，尝试直接解析
            if raw_content.strip().startswith('{'):
                return json.loads(raw_content)
            
            # 如果都失败了，返回原始内容
            self.logger.warning("无法解析JSON格式，使用原始内容")
            return {
                "content": raw_content,
                "summary": "AI生成的故事内容",
                "key_elements": [],
                "mood": "未知",
                "choice_setup": "故事继续..."
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            return {
                "content": raw_content,
                "summary": "AI生成的故事内容",
                "key_elements": [],
                "mood": "未知",
                "choice_setup": "故事继续..."
            }
    
    async def generate_story_opening(self, request: StoryGenerationRequest) -> AIResponse:
        """生成故事开头"""
        ai_request = request.to_ai_request()
        return await self.process(ai_request)
    
    async def generate_chapter(self, request: ChapterGenerationRequest) -> AIResponse:
        """生成章节内容"""
        ai_request = request.to_ai_request()
        return await self.process(ai_request)
    
    async def generate_story_summary(self, chapters: List[Dict[str, Any]]) -> str:
        """生成故事摘要"""
        if not chapters:
            return "暂无故事内容"
        
        # 构建摘要生成提示词
        chapter_summaries = []
        for i, chapter in enumerate(chapters, 1):
            summary = chapter.get('summary', chapter.get('content', '')[:100])
            chapter_summaries.append(f"第{i}章：{summary}")
        
        prompt = f"""
请为以下故事章节生成一个简洁的整体摘要（100字以内）：

{chr(10).join(chapter_summaries)}

要求：
1. 概括主要情节线
2. 突出关键转折点
3. 保持简洁明了
4. 不要剧透后续情节

摘要：
"""
        
        try:
            summary = await self._call_gemini(prompt, max_tokens=200, temperature=0.3)
            return summary.strip()
        except Exception as e:
            self.logger.error(f"生成故事摘要失败: {e}")
            return "故事摘要生成失败"
