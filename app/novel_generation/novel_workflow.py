import json

from pydantic import BaseModel
from llama_index.core.workflow import (
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
    Context
)

from app.novel_generation.novel_agents import NovelAgentTools
from app.schemas.base import NovelStyle
from app.schemas.agent_outputs import WorldSettingOutput, ProtagonistGenerationOutput, ChapterOutput
from app.core.logger import get_logger

logger = get_logger(__name__)


class WorldSettingEvent(Event):
    world_setting: WorldSettingOutput


class ProtagonistEvent(Event):
    protagonist: ProtagonistGenerationOutput


class NovelStartState(BaseModel):
    world_setting: WorldSettingOutput = None
    protagonist_info: ProtagonistGenerationOutput = None
    start_chapter: ChapterOutput = None
    if_finished: bool = False


class NovelStartFlow(Workflow):
    def __init__(self, novel_style: NovelStyle):
        super().__init__()
        self.novel_style = novel_style
        self.style_value = novel_style.value
        self.tools = NovelAgentTools(novel_style)
        self.state = NovelStartState()

    @step
    async def generate_world_setting(self, ctx: Context, ev: StartEvent) -> WorldSettingEvent:
        """生成世界观设定"""
        logger.info("开始生成世界观设定")
        
        try:
            world_setting = await self.tools.generate_world_setting()
            logger.info(f"世界观设定生成完成: {world_setting}")
            
            self.state.world_setting = world_setting
            return WorldSettingEvent(world_setting=world_setting)
        except Exception as e:
            logger.error(f"生成世界观设定时出错: {e}")
            raise

    @step
    async def generate_protagonist(self, ctx: Context, ev: WorldSettingEvent) -> ProtagonistEvent:
        """生成主人公信息"""
        logger.info("开始生成主人公信息")
        
        try:
            protagonist_info = await self.tools.generate_protagonist(ev.world_setting)
            logger.info(f"主人公信息生成完成: {protagonist_info}")
            
            self.state.protagonist_info = protagonist_info
            return ProtagonistEvent(protagonist=protagonist_info)
        except Exception as e:
            logger.error(f"生成主人公信息时出错: {e}")
            raise

    @step
    async def generate_start_chapter(self, ctx: Context, ev: ProtagonistEvent) -> StopEvent:
        """生成开始章节"""
        logger.info("开始生成第一章内容")
        
        try:
            start_chapter = await self.tools.generate_chapter(
                self.state.world_setting, 
                ev.protagonist
            )
            logger.info(f"第一章内容生成完成: {start_chapter}")
            
            self.state.start_chapter = start_chapter
            self.state.if_finished = True
            return StopEvent(result=start_chapter)
        except Exception as e:
            logger.error(f"生成第一章内容时出错: {e}")
            raise


# 使用示例
if __name__ == "__main__":
    flow = NovelStartFlow(novel_style=NovelStyle.WUXIA)
    logger.debug(f"Start...")
    result = flow.kickoff()
