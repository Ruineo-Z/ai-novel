from typing import List, Optional

from langgraph.prebuilt import create_react_agent
from langgraph.graph.graph import CompiledGraph
from langchain.chat_models import init_chat_model

from app.schemas.agent_outputs import WorldSettingOutput, ChapterOutput, ProtagonistGenerationOutput, \
    ChoiceConsequenceOutput, StoryAnalysisOutput
from app.schemas.base import NovelStyle
from app.agent.agent_prompt import PromptManager
from app.core.config import settings


class AgentInit:
    def __init__(self, novel_style: NovelStyle):
        self.novel_style = novel_style
        self.style_value = novel_style.value

        self.llm = init_chat_model(model=settings.GEMINI_MODEL, model_provider="google_genai",
                                   google_api_key=settings.GEMINI_API_KEY)

        self.prompt_manager = PromptManager(novel_style=self.novel_style)

    def init_world_setting_agent(self) -> CompiledGraph:
        """生成世界观Agent"""
        agent = create_react_agent(
            model=self.llm,
            prompt=self.prompt_manager.get_world_setting_prompt(),
            tools=[],
            response_format=WorldSettingOutput,
        )
        return agent

    def init_protagonist_generation_agent(self, world_setting: WorldSettingOutput) -> CompiledGraph:
        """生成主人公Agent"""
        agent = create_react_agent(
            model=self.llm,
            prompt=self.prompt_manager.get_protagonist_generation_prompt(
                world_setting=world_setting),
            tools=[],
            response_format=ProtagonistGenerationOutput
        )
        return agent

    def init_chapter_output_agent(self, protagonist_info: ProtagonistGenerationOutput, world_setting: WorldSettingOutput, story_history: StoryAnalysisOutput = None, current_chapter: int = 1) -> CompiledGraph:
        """生成章节内容Agent"""
        agent = create_react_agent(
            model=self.llm,
            prompt=self.prompt_manager.get_chapter_generation_prompt(protagonist_info=protagonist_info,
                                                                     world_setting=world_setting,
                                                                     story_history=story_history,
                                                                     current_chapter=current_chapter),
            tools=[],
            response_format=ChapterOutput
        )
        return agent

    def init_story_analysis_agent(self, story_history: List[StoryAnalysisOutput], protagonist_info: ProtagonistGenerationOutput, current_chapter: int) -> CompiledGraph:
        """分析章节内容，是否合理正确"""
        agent = create_react_agent(
            model=self.llm,
            prompt=self.prompt_manager.get_story_analysis_prompt(story_history=story_history,
                                                                 current_chapter=current_chapter,
                                                                 protagonist_info=protagonist_info),
            tools=[],
            response_format=StoryAnalysisOutput
        )
        return agent
