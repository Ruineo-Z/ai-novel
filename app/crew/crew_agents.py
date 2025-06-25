from crewai import Agent

from app.crew import crew_llm
from app.crew.prompt_manager import PromptManager
from app.schemas.agent_outputs import (
    WorldSettingOutput,
    ProtagonistGenerationOutput,
    ChapterOutput,
)
from app.schemas.base import NovelStyle
from app.core.logger import get_logger

logger = get_logger(__name__)


class NovelCrewAgents:
    """小说创作CrewAI代理集合"""

    def __init__(self, novel_style: NovelStyle):
        self.novel_style = novel_style
        self.style_value = novel_style.value
        self.prompt_manager = PromptManager(novel_style=novel_style)
        self.llm = crew_llm.ollama_llm()

    def world_setting_agent(self) -> Agent:
        """世界观设定代理"""
        return Agent(
            role="世界观设计师",
            goal=f"为{self.style_value}类型的小说创建完整且引人入胜的世界观设定",
            backstory="你是一名经验丰富的小说世界观设计师，擅长创建引人入胜且逻辑一致的小说世界观。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def protagonist_agent(self) -> Agent:
        """主人公生成代理"""
        return Agent(
            role="角色设计师",
            goal=f"基于世界观设定，创造符合{self.style_value}小说特点的主人公角色",
            backstory="你是一名专业的小说角色设计师。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def chapter_writer_agent(self) -> Agent:
        """开场章节创作代理"""
        return Agent(
            role="章节作家",
            goal=f"创作引人入胜的{self.style_value}小说章节内容",
            backstory=f"你是一名专业的{self.style_value}小说作家，你特别擅长创作小说各个章节的内容。",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
        )

    def story_coordinator_agent(self) -> Agent:
        """故事协调代理"""
        return Agent(
            role="故事协调员",
            goal="协调整个小说创作流程，确保各部分内容的一致性和连贯性",
            backstory="""
            你是一名经验丰富的故事协调员，
            负责监督整个小说创作过程。
            你能够确保世界观、角色和情节之间的逻辑一致性，
            协调各个创作环节，保证最终作品的质量和连贯性。
            """,
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
        )
