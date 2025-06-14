from app.agent.agent_init import AgentInit
from app.schemas.base import NovelStyle, ProtagonistInfo
from langchain_core.messages import HumanMessage


class GraphNode:
    def create_world_setting_node(self, novel_style: NovelStyle):
        agent_client = AgentInit(novel_style=novel_style)
        agent = agent_client.init_world_setting_agent()
        message = f"生成一份{agent_client.style_value}为背景的小说世界观"
        for chunk in agent.stream({"messages": [HumanMessage(content=message)]}):
            print(chunk)


if __name__ == '__main__':
    client = GraphNode()
    style = NovelStyle.XIANXIA
    client.create_world_setting_node(novel_style=style)
