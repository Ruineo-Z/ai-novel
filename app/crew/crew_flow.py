import json

from pydantic import BaseModel
from crewai import Crew, Process
from crewai.flow.flow import Flow, listen, start
from crewai.utilities.events import LLMStreamChunkEvent
from crewai.utilities.events.base_event_listener import BaseEventListener

from app.crew.crew_agents import NovelCrewAgents
from app.crew.crew_tasks import NovelCrewTasks
from app.schemas.base import NovelStyle
from app.schemas.agent_outputs import WorldSettingOutput, ProtagonistGenerationOutput, ChapterOutput
from app.core.logger import get_logger

logger = get_logger(__name__)


class NovelStartState(BaseModel):
    world_setting: WorldSettingOutput = None
    protagonist_info: ProtagonistGenerationOutput = None
    start_chapter: ChapterOutput = None
    if_finished: bool = False


class NovelStartFlow(Flow[NovelStartState]):
    def __init__(self, novel_style: NovelStyle):
        super().__init__()
        self.novel_style = novel_style
        self.style_value = novel_style.value
        self.agents = NovelCrewAgents(novel_style)
        self.tasks = NovelCrewTasks(novel_style)

    @start()
    def generate_world_setting(self):
        """生成世界观设定"""

        # 创建世界观生成crew
        world_agent = self.agents.world_setting_agent()
        world_task = self.tasks.world_setting_task(agent=world_agent)

        crew = Crew(
            agents=[world_agent],
            tasks=[world_task],
            process=Process.sequential,
            verbose=True,
            # memory=True
        )

        # 执行任务
        result = crew.kickoff()
        dict_result = result.to_dict()
        logger.debug(f"世界观生成结果: {result}")

        # 解析结果
        try:
            logger.debug(f"Type Result: {type(dict_result)}")
            world_setting = WorldSettingOutput(**dict_result)
            logger.info(f"世界观生成成功: {world_setting.world_name}")
            self.state.world_setting = world_setting
            return world_setting

        except Exception as e:
            logger.error(f"世界观数据解析失败: {str(e)}")
            # 返回默认值
            return WorldSettingOutput(
                world_setting=f"默认{self.novel_style.value}世界观",
                world_name=f"{self.novel_style.value}世界",
                world_description="一个充满奇幻色彩的世界",
                power_system="基础力量体系",
                main_locations=["主城", "野外"],
                key_factions=["正义联盟", "邪恶势力"],
                world_rules=["基本规则1", "基本规则2"]
            )

    @listen(generate_world_setting)
    def generate_protagonist(self):
        """生成主人公信息"""
        world_setting = self.state.world_setting
        if not world_setting:
            raise ValueError("世界观设定未完成，无法生成主人公")

        # 创建主人公生成crew
        protagonist_agent = self.agents.protagonist_agent()
        protagonist_task = self.tasks.protagonist_task(world_setting=world_setting, agent=protagonist_agent)

        crew = Crew(
            agents=[protagonist_agent],
            tasks=[protagonist_task],
            process=Process.sequential,
            verbose=True,
            # memory=True
        )

        # 执行任务
        result = crew.kickoff()
        dict_result = result.to_dict()
        logger.debug(f"主人公生成结果: {result}")

        # 解析结果
        try:
            protagonist = ProtagonistGenerationOutput(**dict_result)
            self.state.protagonist_info = protagonist
            logger.info(f"主人公生成成功: {protagonist.name}")
            return protagonist

        except Exception as e:
            logger.error(f"主人公数据解析失败: {str(e)}")
            # 返回默认值
            return ProtagonistGenerationOutput(
                name="主角",
                age=20,
                gender="未知",
                appearance="普通外貌",
                personality="勇敢、善良",
                background="普通出身",
                initial_abilities=["基础能力"],
                goals=["成长", "冒险"],
                weaknesses=["经验不足"],
                special_traits="潜力无限",
                starting_scenario="在一个平凡的日子里，主角的命运即将发生改变"
            )

    @listen(generate_protagonist)
    def generate_start_chapter(self):
        """生成第一章内容"""
        world_setting = self.state.world_setting
        protagonist_info = self.state.protagonist_info
        if not world_setting or not protagonist_info:
            raise ValueError("世界观或主人公信息未完成，无法生成章节")

        # 创建章节生成crew
        chapter_agent = self.agents.chapter_writer_agent()
        chapter_task = self.tasks.start_chapter_task(world_setting=world_setting, protagonist=protagonist_info,
                                                     agent=chapter_agent)

        crew = Crew(
            agents=[chapter_agent],
            tasks=[chapter_task],
            process=Process.sequential,
            verbose=True,
            # memory=True
        )

        # 执行任务
        result = crew.kickoff()
        dict_result = result.to_dict()
        logger.debug(f"第一章生成结果: {result}")

        # 解析结果
        try:
            chapter = ChapterOutput(**dict_result)
            self.state.start_chapter = chapter
            self.state.if_finished = True
            logger.info(f"第一章生成成功: {chapter.chapter_title}")
            return chapter

        except Exception as e:
            logger.error(f"章节数据解析失败: {str(e)}")
            # 返回默认值
            from app.schemas.base import Choice
            return ChapterOutput(
                chapter_title="第一章：命运的开始",
                chapter_content="这是一个关于冒险的故事...",
                story_summary="主角开始了他的冒险之旅",
                character_development="主角初次展现潜力",
                world_expansion="介绍了基本的世界设定",
                choices=[
                    Choice(text="选择A", description="描述A", id=1),
                    Choice(text="选择B", description="描述B", id=2)
                ],
                is_critical_moment=False,
                is_ending=False
            )


# 使用示例
if __name__ == "__main__":
    flow = NovelStartFlow(novel_style=NovelStyle.WUXIA)
    logger.debug(f"Start...")
    result = flow.kickoff()
