import asyncio
import json
from math import log
from typing import AsyncGenerator, Dict, Any, List

from pydantic import BaseModel
from llama_index.core.workflow import (
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
    Context
)
from llama_index.core.prompts import PromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from app.novel_generation.prompt_manager import PromptManager
from app.novel_generation.llm_config import gemini_llm
from app.schemas.base import NovelStyle
from app.schemas.agent_outputs import WorldSettingOutput, ProtagonistGenerationOutput, ChapterOutput
from app.core.logger import get_logger

logger = get_logger(__name__)


class WorldSettingEvent(Event):
    world_setting: WorldSettingOutput


class ProtagonistEvent(Event):
    protagonist: ProtagonistGenerationOutput


class StreamEvent(Event):
    """流式输出事件"""
    event_type: str  # 'world_setting', 'protagonist', 'chapter', 'progress', 'error'
    data: Dict[Any, Any]
    message: str = ""


class NovelStartState(BaseModel):
    world_setting: WorldSettingOutput = None
    protagonist_info: ProtagonistGenerationOutput = None
    start_chapter: ChapterOutput = None
    if_finished: bool = False


class NovelStartFlow:
    def __init__(self, novel_style: NovelStyle):
        self.novel_style = novel_style
        self.style_value = novel_style.value
        self.llm = gemini_llm()
        self.prompt_manager = PromptManager(novel_style=novel_style)
        self.state = NovelStartState()

    async def run_with_streaming(self) -> AsyncGenerator[Dict[str, Any], None]:
        """运行工作流并返回流式输出"""
        try:
            # 步骤1: 生成世界观设定
            yield {
                "event_type": "progress",
                "data": {"step": "world_setting", "status": "started"},
                "message": "开始生成世界观设定..."
            }

            world_setting = await self._generate_world_setting_stream()
            logger.debug(f"世界观: {world_setting}")
            yield {
                "event_type": "world_setting",
                "data": world_setting.model_dump(),
                "message": "世界观设定生成完成"
            }

            # 步骤2: 生成主人公信息
            yield {
                "event_type": "progress",
                "data": {"step": "protagonist", "status": "started"},
                "message": "开始生成主人公信息..."
            }

            protagonist = await self._generate_protagonist_stream(world_setting)
            logger.debug(f"主人公: {protagonist}")
            yield {
                "event_type": "protagonist",
                "data": protagonist.model_dump(),
                "message": "主人公信息生成完成"
            }

            # 步骤3: 生成第一章内容
            yield {
                "event_type": "progress",
                "data": {"step": "chapter", "status": "started"},
                "message": "开始生成第一章内容..."
            }

            # 流式生成章节内容
            chapter_content = ""
            async for chunk in self._generate_chapter_stream(world_setting, protagonist):
                chapter_content += chunk
                yield {
                    "event_type": "chapter_chunk",
                    "data": {"chunk": chunk, "accumulated": chapter_content},
                    "message": "正在生成章节内容..."
                }

            # 解析完整的章节内容
            try:
                # 尝试解析为结构化输出
                chapter = await self._parse_chapter_content(chapter_content, world_setting, protagonist)

                yield {
                    "event_type": "chapter",
                    "data": chapter.model_dump(),
                    "message": "第一章内容生成完成"
                }

                # 完成事件
                yield {
                    "event_type": "complete",
                    "data": {
                        "world_setting": world_setting.model_dump(),
                        "protagonist": protagonist.model_dump(),
                        "chapter": chapter.model_dump()
                    },
                    "message": "小说生成完成"
                }
                logger.debug(f"小说: {chapter}")
            except Exception as e:
                logger.error(f"解析章节内容时出错: {e}")
                # 如果解析失败，返回原始内容
                yield {
                    "event_type": "chapter_raw",
                    "data": {"content": chapter_content},
                    "message": "章节内容生成完成（原始格式）"
                }

        except Exception as e:
            logger.error(f"流式生成过程中出错: {e}")
            yield {
                "event_type": "error",
                "data": {"error": str(e)},
                "message": f"生成失败: {str(e)}"
            }

    async def _generate_world_setting_stream(self) -> WorldSettingOutput:
        """生成世界观设定"""
        prompt = self.prompt_manager.get_world_setting_prompt()

        world_setting = self.llm.structured_predict(
            output_cls=WorldSettingOutput,
            prompt=PromptTemplate(prompt)
        )

        self.state.world_setting = world_setting
        return world_setting

    async def _generate_protagonist_stream(self, world_setting: WorldSettingOutput) -> ProtagonistGenerationOutput:
        """生成主人公信息"""
        prompt = self.prompt_manager.get_protagonist_generation_prompt(world_setting=world_setting)

        protagonist = self.llm.structured_predict(
            output_cls=ProtagonistGenerationOutput,
            prompt=PromptTemplate(prompt)
        )

        self.state.protagonist_info = protagonist
        return protagonist

    async def _generate_chapter_stream(self, world_setting: WorldSettingOutput,
                                       protagonist: ProtagonistGenerationOutput) -> AsyncGenerator[str, None]:
        """流式生成章节内容"""
        prompt = self.prompt_manager.get_start_chapter_prompt(
            world_setting=world_setting,
            protagonist_info=protagonist
        )

        # 创建聊天消息
        messages = [ChatMessage(role=MessageRole.USER, content=prompt)]

        # 流式生成
        try:
            stream_response = await self.llm.astream_chat(messages)
            async for chunk in stream_response:
                if hasattr(chunk, 'delta') and chunk.delta:
                    yield chunk.delta
                elif hasattr(chunk, 'message') and chunk.message:
                    yield chunk.message.content
                else:
                    yield str(chunk)
        except Exception as e:
            logger.error(f"流式生成章节时出错: {e}")
            # 降级到非流式生成
            response = await self.llm.achat(messages)
            yield response.message.content

    async def _parse_chapter_content(self, content: str, world_setting: WorldSettingOutput,
                                     protagonist: ProtagonistGenerationOutput) -> ChapterOutput:
        """解析章节内容为结构化输出"""
        # 尝试使用LLM解析内容为结构化格式
        parse_prompt = f"""
    请将以下章节内容解析为结构化格式：

    章节内容：
    {content}

    请提取出：
    1. 章节标题
    2. 章节内容
    3. 关键情节点
    4. 人物发展
    5. 世界观展现

    请严格按照ChapterOutput的格式输出。
    """

        try:
            chapter = self.llm.structured_predict(
                output_cls=ChapterOutput,
                prompt=PromptTemplate(parse_prompt)
            )
            return chapter
        except Exception as e:
            logger.error(f"结构化解析失败，使用默认格式: {e}")
            # 如果解析失败，创建一个基本的ChapterOutput
            return ChapterOutput(
                chapter_title="第一章",
                chapter_content=content,
                key_plot_points=["故事开始"],
                character_development=[f"{protagonist.name}的初次登场"],
                world_building_elements=[world_setting.world_name]
            )


async def run_workflow():
    workflow = NovelStartFlow(novel_style=NovelStyle.XIANXIA)
    async for event in workflow.run_with_streaming():
        logger.info(f"事件类型: {event['event_type']}")
        logger.info(f"消息: {event['message']}")
        if event['event_type'] == 'chapter_chunk':
            logger.info(f"章节片段: {event['data']['chunk']}")
        logger.info("---")


# 使用示例
if __name__ == "__main__":
    # 运行流式工作流
    asyncio.run(run_workflow())
