from langchain_core.messages import HumanMessage

from app.agent.agent_init import AgentInit
from app.schemas.base import NovelStyle
from app.schemas.agent_outputs import WorldSettingOutput, ProtagonistGenerationOutput, StoryAnalysisOutput
from app.core.logger import get_logger

logger = get_logger(__name__)


class GraphNode:
    def __init__(self, novel_style: NovelStyle):
        self.novel_style = novel_style
        self.agent_client = AgentInit(novel_style=novel_style)

    def create_world_setting_node(self):
        agent = self.agent_client.init_world_setting_agent()
        message = f"生成一份{self.agent_client.style_value}为背景的小说世界观"

        response = agent.invoke({"messages": [HumanMessage(content=message)]})
        structured_data = response["structured_response"]

        logger.debug(f"世界观设定: {structured_data}")
        self.agent_client.world_setting = structured_data

        return structured_data

    def create_protagonist_node(self, world_setting: WorldSettingOutput):
        agent = self.agent_client.init_protagonist_generation_agent(world_setting=world_setting)
        message = f"根据世界观和起始场景，生成一个主人公"

        response = agent.invoke({"messages": [HumanMessage(content=message)]})
        structured_data = response["structured_response"]

        logger.debug(f"主人公信息：{structured_data}")
        self.agent_client.protagonist_info = structured_data

        return structured_data

    def create_chapter_node(self, protagonist_info: ProtagonistGenerationOutput, world_setting: WorldSettingOutput, story_history: StoryAnalysisOutput = None, current_chapter: int =1):
        agent = self.agent_client.init_chapter_output_agent(protagonist_info=protagonist_info, world_setting=world_setting, story_history=story_history, current_chapter=current_chapter)
        message = f"根据世界观、主人公信息、章节主题，生成一个章节"
        response = agent.invoke({"messages": [HumanMessage(content=message)]})
        structured_data = response["structured_response"]
        logger.debug(f"章节信息：{structured_data}")
        return structured_data

