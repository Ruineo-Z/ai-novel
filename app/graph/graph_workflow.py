from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

from app.schemas.base import NovelStyle
from app.schemas.agent_outputs import WorldSettingOutput, ProtagonistGenerationOutput, ChapterOutput
from app.graph.graph_node import GraphNode
from app.core.logger import get_logger

logger = get_logger(__name__)

# 定义状态
class NovelState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    novel_style: NovelStyle
    world_setting: WorldSettingOutput
    protagonist_info: ProtagonistGenerationOutput
    chapter_info: ChapterOutput
    current_step: int

class NovelWorkflow:
    def __init__(self, novel_style: NovelStyle):
        self.novel_style = novel_style
        self.graph_node = GraphNode(novel_style)
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        # 创建状态图
        workflow = StateGraph(NovelState)
        
        # 添加节点
        workflow.add_node("world_setting_node", self._world_setting_node)
        workflow.add_node("protagonist_generation_node", self._protagonist_node)
        workflow.add_node("chapter_generation_node", self._chapter_node)
        
        # 定义边（执行顺序）
        workflow.add_edge(START, "world_setting_node")
        workflow.add_edge("world_setting_node", "protagonist_generation_node")
        workflow.add_edge("protagonist_generation_node", "chapter_generation_node")
        workflow.add_edge("chapter_generation_node", END)
        
        return workflow.compile()
    
    def _world_setting_node(self, state: NovelState) -> NovelState:
        """世界观设定节点"""
        logger.info("开始生成世界观设定...")
        world_setting = self.graph_node.create_world_setting_node()
        
        return {
            **state,
            "world_setting": world_setting,
            "current_step": "world_setting_completed"
        }
    
    def _protagonist_node(self, state: NovelState) -> NovelState:
        """主人公生成节点"""
        logger.info("开始生成主人公信息...")
        # 这里可以访问前一个节点的输出
        world_setting = state["world_setting"]
        logger.debug(f"使用世界观: {world_setting.world_name}")
        
        protagonist_info = self.graph_node.create_protagonist_node(world_setting=world_setting)
        
        return {
            **state,
            "protagonist_info": protagonist_info,
            "current_step": "protagonist_completed"
        }
    
    def _chapter_node(self, state: NovelState) -> NovelState:
        """章节生成节点"""
        logger.info("开始生成章节内容...")
        # 可以同时访问世界观和主人公信息
        world_setting = state["world_setting"]
        protagonist_info = state["protagonist_info"]
        
        logger.debug(f"使用世界观: {world_setting.world_name}")
        logger.debug(f"使用主人公: {protagonist_info.name}")
        
        chapter_info = self.graph_node.create_chapter_node(world_setting=world_setting, protagonist_info=protagonist_info, story_history=None, current_chapter=state["current_step"])
        
        return {
            **state,
            "chapter_info": chapter_info,
            "current_step": "chapter_completed"
        }
    
    def run_workflow(self):
        """运行完整的工作流"""
        initial_state = {
            "messages": [],
            "novel_style": self.novel_style,
            "world_setting": None,
            "protagonist_info": None,
            "chapter_info": None,
            "current_step": "started"
        }
        
        # 执行工作流
        result = self.workflow.invoke(initial_state)
        
        return {
            "world_setting": result["world_setting"],
            "protagonist_info": result["protagonist_info"],
            "chapter_info": result["chapter_info"]
        }

# 使用示例
if __name__ == '__main__':
    workflow = NovelWorkflow(NovelStyle.XIANXIA)
    result = workflow.run_workflow()
    
    print(f"世界观: {result['world_setting'].world_name}")
    print(f"主人公: {result['protagonist_info'].name}")
    print(f"章节标题: {result['chapter_info'].chapter_title}")