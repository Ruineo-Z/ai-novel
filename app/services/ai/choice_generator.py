"""
选择生成服务 - 负责为故事章节生成选择选项
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


@dataclass
class ChoiceOption:
    """选择选项数据结构"""
    text: str
    description: str
    consequence_hint: str
    difficulty: str  # easy, medium, hard
    type: str  # action, dialogue, decision
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "text": self.text,
            "description": self.description,
            "consequence_hint": self.consequence_hint,
            "difficulty": self.difficulty,
            "type": self.type
        }


@dataclass
class ChoiceGenerationRequest:
    """选择生成请求"""
    story_context: Dict[str, Any]
    current_chapter: Dict[str, Any]
    choice_setup: str
    previous_choices: List[Dict[str, Any]]
    character_state: Dict[str, Any]
    
    def to_ai_request(self) -> AIRequest:
        """转换为AI请求"""
        prompt = self._build_choice_prompt()
        theme = StoryTheme(self.story_context.get("theme", "urban"))
        
        return AIRequest(
            content_type=ContentType.CHOICE_OPTIONS,
            theme=theme,
            prompt=prompt,
            context={
                "story_context": self.story_context,
                "current_chapter": self.current_chapter,
                "choice_setup": self.choice_setup,
                "previous_choices": self.previous_choices,
                "character_state": self.character_state
            },
            temperature=0.8  # 选择生成需要更多创意
        )
    
    def _build_choice_prompt(self) -> str:
        """构建选择生成提示词"""
        # 构建角色状态描述
        character_info = self._build_character_info()
        
        # 构建前置选择历史
        choice_history = self._build_choice_history()
        
        return f"""
你是一位专业的互动小说设计师，请为当前故事情境设计3个有趣且有意义的选择选项。

## 故事背景
主题：{self.story_context.get('theme', '未知')}
背景：{self.story_context.get('background', '')}

## 当前情境
{self.choice_setup}

## 角色状态
{character_info}

## 选择历史
{choice_history}

## 设计要求
1. **多样性**: 3个选择应该代表不同的解决方案或发展方向
2. **平衡性**: 包含不同难度和风险的选项
3. **合理性**: 选择必须符合当前情境和角色设定
4. **影响性**: 每个选择都应该对后续情节产生不同影响
5. **吸引性**: 选择描述要生动有趣，激发读者兴趣

## 选择类型
- **行动类**: 直接的行为选择
- **对话类**: 与其他角色的交流方式
- **决策类**: 重要的判断和决定

## 输出格式
请按以下JSON格式输出：
```json
{{
    "choices": [
        {{
            "text": "选择选项的简短描述（20字以内）",
            "description": "选择的详细说明（50字以内）",
            "consequence_hint": "可能的后果提示（30字以内）",
            "difficulty": "easy/medium/hard",
            "type": "action/dialogue/decision"
        }},
        {{
            "text": "第二个选择...",
            "description": "...",
            "consequence_hint": "...",
            "difficulty": "...",
            "type": "..."
        }},
        {{
            "text": "第三个选择...",
            "description": "...",
            "consequence_hint": "...",
            "difficulty": "...",
            "type": "..."
        }}
    ],
    "context_analysis": "当前情境的分析和选择设计思路",
    "balance_note": "选择平衡性说明"
}}
```

请开始设计选择：
"""
    
    def _build_character_info(self) -> str:
        """构建角色信息"""
        if not self.character_state:
            return "角色状态：未知"
        
        info_parts = []
        if "name" in self.character_state:
            info_parts.append(f"姓名：{self.character_state['name']}")
        if "health" in self.character_state:
            info_parts.append(f"状态：{self.character_state['health']}")
        if "skills" in self.character_state:
            skills = ", ".join(self.character_state['skills'])
            info_parts.append(f"技能：{skills}")
        if "relationships" in self.character_state:
            info_parts.append(f"人际关系：{self.character_state['relationships']}")
        
        return "\n".join(info_parts) if info_parts else "角色状态：基本状态"
    
    def _build_choice_history(self) -> str:
        """构建选择历史"""
        if not self.previous_choices:
            return "这是第一个选择点。"
        
        history_parts = []
        for i, choice in enumerate(self.previous_choices[-3:], 1):  # 只显示最近3个选择
            choice_text = choice.get('text', '未知选择')
            result = choice.get('result', '结果未知')
            history_parts.append(f"选择{i}：{choice_text} → {result}")
        
        return "\n".join(history_parts)


class ChoiceGeneratorService(BaseAIService):
    """选择生成服务"""
    
    def __init__(self):
        super().__init__()
        self.logger.info("选择生成服务初始化完成")
    
    async def process(self, request: AIRequest) -> AIResponse:
        """处理选择生成请求"""
        self._validate_request(request)
        
        start_time = time.time()
        
        try:
            # 调用Gemini生成选择
            raw_content = await self._call_gemini(
                request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # 解析生成的选择
            parsed_choices = self._parse_generated_choices(raw_content)
            
            processing_time = time.time() - start_time
            
            return AIResponse(
                content=json.dumps(parsed_choices, ensure_ascii=False, indent=2),
                tokens_used=len(raw_content.split()),
                processing_time=processing_time,
                metadata={
                    "choices": parsed_choices.get("choices", []),
                    "context_analysis": parsed_choices.get("context_analysis"),
                    "balance_note": parsed_choices.get("balance_note"),
                    "raw_response": raw_content
                }
            )
            
        except Exception as e:
            self.logger.error(f"选择生成失败: {e}")
            raise AIServiceError(f"选择生成失败: {e}")
    
    def _parse_generated_choices(self, raw_content: str) -> Dict[str, Any]:
        """解析生成的选择"""
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)
            elif raw_content.strip().startswith('{'):
                parsed = json.loads(raw_content)
            else:
                # 如果无法解析，生成默认选择
                self.logger.warning("无法解析选择JSON，生成默认选择")
                return self._generate_default_choices()
            
            # 验证选择格式
            if "choices" not in parsed or not isinstance(parsed["choices"], list):
                self.logger.warning("选择格式不正确，生成默认选择")
                return self._generate_default_choices()
            
            # 确保有3个选择
            choices = parsed["choices"]
            if len(choices) < 3:
                self.logger.warning(f"选择数量不足（{len(choices)}），补充默认选择")
                while len(choices) < 3:
                    choices.append(self._create_default_choice(len(choices) + 1))
            
            # 验证每个选择的必需字段
            for i, choice in enumerate(choices):
                if not isinstance(choice, dict):
                    choices[i] = self._create_default_choice(i + 1)
                    continue
                
                # 确保必需字段存在
                required_fields = ["text", "description", "consequence_hint", "difficulty", "type"]
                for field in required_fields:
                    if field not in choice or not choice[field]:
                        if field == "difficulty":
                            choice[field] = "medium"
                        elif field == "type":
                            choice[field] = "action"
                        else:
                            choice[field] = f"选择{i + 1}"
            
            return parsed
            
        except json.JSONDecodeError as e:
            self.logger.error(f"选择JSON解析失败: {e}")
            return self._generate_default_choices()
    
    def _generate_default_choices(self) -> Dict[str, Any]:
        """生成默认选择"""
        return {
            "choices": [
                self._create_default_choice(1),
                self._create_default_choice(2),
                self._create_default_choice(3)
            ],
            "context_analysis": "由于AI生成失败，提供了默认选择选项",
            "balance_note": "默认选择包含不同类型和难度的选项"
        }
    
    def _create_default_choice(self, index: int) -> Dict[str, Any]:
        """创建默认选择"""
        default_choices = [
            {
                "text": "谨慎观察",
                "description": "仔细观察周围环境，寻找更多线索",
                "consequence_hint": "可能发现重要信息",
                "difficulty": "easy",
                "type": "action"
            },
            {
                "text": "主动行动",
                "description": "采取积极的行动来改变现状",
                "consequence_hint": "风险与机遇并存",
                "difficulty": "medium",
                "type": "action"
            },
            {
                "text": "寻求帮助",
                "description": "向他人寻求建议或协助",
                "consequence_hint": "可能获得支持或承担人情债",
                "difficulty": "medium",
                "type": "dialogue"
            }
        ]
        
        return default_choices[(index - 1) % len(default_choices)]
    
    async def generate_choices(self, request: ChoiceGenerationRequest) -> List[ChoiceOption]:
        """生成选择选项"""
        ai_request = request.to_ai_request()
        response = await self.process(ai_request)
        
        # 从响应中提取选择
        choices_data = response.metadata.get("choices", [])
        
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
    
    async def evaluate_choice_impact(self, choice: Dict[str, Any], story_context: Dict[str, Any]) -> Dict[str, Any]:
        """评估选择的影响"""
        prompt = f"""
请分析以下选择在故事中的潜在影响：

选择：{choice.get('text', '')}
描述：{choice.get('description', '')}
故事背景：{story_context.get('background', '')}

请从以下维度分析：
1. 对主角发展的影响
2. 对故事情节的影响
3. 对人际关系的影响
4. 风险评估
5. 机遇评估

输出格式：
```json
{{
    "character_impact": "对主角的影响",
    "plot_impact": "对情节的影响",
    "relationship_impact": "对人际关系的影响",
    "risk_level": "low/medium/high",
    "opportunity_level": "low/medium/high",
    "long_term_consequences": "长期后果预测"
}}
```
"""
        
        try:
            response = await self._call_gemini(prompt, max_tokens=500, temperature=0.3)
            
            # 解析影响分析
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            return {"error": "无法解析影响分析"}
            
        except Exception as e:
            self.logger.error(f"选择影响评估失败: {e}")
            return {"error": f"影响评估失败: {e}"}
