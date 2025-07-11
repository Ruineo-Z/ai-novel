"""
模拟AI服务 - 用于演示和测试AI服务架构
"""
import time
import json
import random
from typing import Dict, List, Optional, Any

from app.services.ai.base import (
    BaseAIService, AIRequest, AIResponse, 
    StoryTheme, ContentType, AIServiceError
)


class MockAIService(BaseAIService):
    """模拟AI服务 - 生成预设的响应内容"""
    
    def __init__(self):
        # 跳过真实的AI客户端初始化
        self.logger = self._get_logger()
        self.logger.info("模拟AI服务初始化完成")
    
    def _get_logger(self):
        import logging
        return logging.getLogger(self.__class__.__name__)
    
    def _setup_clients(self):
        """跳过客户端设置"""
        pass
    
    async def process(self, request: AIRequest) -> AIResponse:
        """处理AI请求 - 返回模拟响应"""
        self._validate_request(request)
        
        start_time = time.time()
        
        # 模拟处理延迟
        await self._simulate_processing_delay()
        
        # 根据内容类型生成不同的模拟响应
        if request.content_type == ContentType.STORY_OPENING:
            content = self._generate_mock_story_opening(request)
        elif request.content_type == ContentType.CHAPTER_CONTENT:
            content = self._generate_mock_chapter(request)
        elif request.content_type == ContentType.CHOICE_OPTIONS:
            content = self._generate_mock_choices(request)
        else:
            content = self._generate_generic_content(request)
        
        processing_time = time.time() - start_time
        
        return AIResponse(
            content=content["content"],
            tokens_used=len(content["content"].split()),
            processing_time=processing_time,
            metadata=content.get("metadata", {})
        )
    
    async def _simulate_processing_delay(self):
        """模拟AI处理延迟"""
        import asyncio
        # 随机延迟0.5-2秒
        delay = random.uniform(0.5, 2.0)
        await asyncio.sleep(delay)
    
    def _generate_mock_story_opening(self, request: AIRequest) -> Dict[str, Any]:
        """生成模拟故事开头"""
        theme = request.theme
        context = request.context or {}
        
        # 根据主题生成不同的故事开头
        story_templates = {
            StoryTheme.URBAN: {
                "content": f"""
{context.get('protagonist', {}).get('name', '主角')}站在繁华都市的十字路口，霓虹灯闪烁着五彩斑斓的光芒。
作为一名{context.get('protagonist', {}).get('description', '普通上班族')}，他从未想过自己的生活会发生如此戏剧性的变化。

就在昨天，一个神秘的包裹出现在他的门前，里面装着一张古老的地图和一把奇特的钥匙。
地图上标记着城市中一个他从未注意过的地点——一家隐藏在小巷深处的古董店。

现在，他站在这家店铺面前，手中紧握着那把钥匙。店铺看起来已经关闭多年，但奇怪的是，
从门缝中透出微弱的光芒，仿佛在召唤着他进入。

他深吸一口气，伸出手准备推开那扇厚重的木门...
""",
                "summary": "主角在都市中发现神秘古董店",
                "key_elements": ["都市", "神秘包裹", "古董店", "钥匙", "选择"],
                "mood": "神秘而紧张",
                "choice_setup": "面对神秘的古董店，主角需要决定是否进入"
            },
            StoryTheme.SCIFI: {
                "content": f"""
2157年，新东京。{context.get('protagonist', {}).get('name', '主角')}从冷冻睡眠中醒来，
发现自己身处一个完全陌生的世界。作为{context.get('protagonist', {}).get('description', '太空探索员')}，
他原本只是参与一次短期的火星任务，但现在...

全息显示屏显示着令人震惊的信息：他已经沉睡了整整50年。地球已经发生了翻天覆地的变化，
人工智能统治着大部分城市，而人类则生活在被严格管制的区域内。

更令人不安的是，他的记忆中出现了一些不属于自己的片段——关于一个名为"觉醒者"的组织，
以及一项可能改变人类命运的秘密计划。

突然，房间的门被打开了，一个身穿银色制服的机器人走了进来...
""",
                "summary": "主角在未来世界中觉醒，发现世界已经改变",
                "key_elements": ["未来世界", "冷冻睡眠", "AI统治", "觉醒者", "记忆"],
                "mood": "科幻而紧张",
                "choice_setup": "面对机器人的到来，主角需要决定如何应对"
            }
        }
        
        template = story_templates.get(theme, story_templates[StoryTheme.URBAN])
        
        return {
            "content": template["content"].strip(),
            "metadata": {
                "summary": template["summary"],
                "key_elements": template["key_elements"],
                "mood": template["mood"],
                "choice_setup": template["choice_setup"]
            }
        }
    
    def _generate_mock_chapter(self, request: AIRequest) -> Dict[str, Any]:
        """生成模拟章节内容"""
        context = request.context or {}
        user_choice = context.get("user_choice", "未知选择")
        
        content = f"""
基于用户的选择"{user_choice}"，故事继续发展...

主角做出了这个决定后，周围的环境开始发生微妙的变化。空气中弥漫着一种奇特的能量，
仿佛整个世界都在回应着他的选择。

远处传来了脚步声，越来越近。主角意识到，他的决定已经触发了一系列连锁反应，
现在已经没有回头路了。

一个神秘的身影出现在视野中，对方似乎早就在等待着这一刻的到来...

"你终于做出了选择，"那个身影说道，"现在，真正的冒险才刚刚开始。"
"""
        
        return {
            "content": content.strip(),
            "metadata": {
                "summary": f"主角选择了{user_choice}，故事进入新阶段",
                "key_elements": ["选择后果", "神秘身影", "新阶段"],
                "mood": "紧张而期待",
                "character_development": "主角变得更加坚定",
                "choice_setup": "面对神秘身影，主角需要决定下一步行动"
            }
        }
    
    def _generate_mock_choices(self, request: AIRequest) -> Dict[str, Any]:
        """生成模拟选择选项"""
        choice_templates = [
            {
                "text": "谨慎观察",
                "description": "仔细观察周围环境，寻找更多线索和信息",
                "consequence_hint": "可能发现重要细节，但也可能错过行动时机",
                "difficulty": "easy",
                "type": "action"
            },
            {
                "text": "主动交流",
                "description": "直接与对方进行对话，了解他们的意图",
                "consequence_hint": "可能获得关键信息，但也可能暴露自己",
                "difficulty": "medium",
                "type": "dialogue"
            },
            {
                "text": "果断行动",
                "description": "采取积极的行动来改变当前局面",
                "consequence_hint": "可能取得突破性进展，但风险较高",
                "difficulty": "hard",
                "type": "action"
            }
        ]
        
        # 随机调整选择内容
        choices = []
        for template in choice_templates:
            choice = template.copy()
            # 可以根据上下文调整选择内容
            choices.append(choice)
        
        return {
            "content": json.dumps({"choices": choices}, ensure_ascii=False, indent=2),
            "metadata": {
                "choices": choices,
                "context_analysis": "当前情境提供了多种不同风险和收益的选择路径",
                "balance_note": "选择涵盖了观察、交流和行动三种不同类型"
            }
        }
    
    def _generate_generic_content(self, request: AIRequest) -> Dict[str, Any]:
        """生成通用模拟内容"""
        return {
            "content": f"这是一个模拟的AI响应，针对{request.content_type.value}类型的请求。",
            "metadata": {
                "type": request.content_type.value,
                "theme": request.theme.value,
                "generated_by": "MockAIService"
            }
        }


# 模拟故事生成服务
class MockStoryGeneratorService(MockAIService):
    """模拟故事生成服务"""
    
    async def generate_story_opening(self, request) -> AIResponse:
        """生成故事开头"""
        ai_request = request.to_ai_request()
        return await self.process(ai_request)
    
    async def generate_chapter(self, request) -> AIResponse:
        """生成章节内容"""
        ai_request = request.to_ai_request()
        return await self.process(ai_request)


# 模拟选择生成服务
class MockChoiceGeneratorService(MockAIService):
    """模拟选择生成服务"""
    
    async def generate_choices(self, request):
        """生成选择选项"""
        ai_request = request.to_ai_request()
        response = await self.process(ai_request)
        
        # 从响应中提取选择
        choices_data = response.metadata.get("choices", [])
        
        # 转换为ChoiceOption对象
        from app.services.ai.choice_generator import ChoiceOption
        choice_options = []
        for choice_data in choices_data:
            choice_option = ChoiceOption(
                text=choice_data.get("text", ""),
                description=choice_data.get("description", ""),
                consequence_hint=choice_data.get("consequence_hint", ""),
                difficulty=choice_data.get("difficulty", "medium"),
                type=choice_data.get("type", "action")
            )
            choice_options.append(choice_option)
        
        return choice_options
