from crewai import Task, Agent
from app.schemas.agent_outputs import WorldSettingOutput, ProtagonistGenerationOutput, ChapterOutput
from app.schemas.base import NovelStyle
from app.core.logger import get_logger

logger = get_logger(__name__)


class NovelCrewTasks:
    """小说创作CrewAI任务集合"""

    def __init__(self, novel_style: NovelStyle):
        self.novel_style = novel_style
        self.style_value = novel_style.value

    def world_setting_task(self, agent: Agent) -> Task:
        """世界观设定任务"""
        description = f"""
        为{self.style_value}类型的小说创建创建一个完整且引人入胜的世界观设定。
        
        任务要求：
        1. 创建世界名称和背景描述
        2. 设计力量体系（如修仙境界、科技等级、武功体系等）
        3. 规划主要地点和地理环境
        4. 设定重要势力和组织
        5. 制定世界运行规则和法则
        
        请确保世界观设定符合{self.style_value}小说的特点和读者期待。
        禁止生成任何人物信息。
        """

        # 根据不同小说类型添加特定要求
        if self.novel_style == NovelStyle.XIANXIA:
            description += """
            
            特别要求：
            - 设计完整的修仙境界体系（如练气、筑基、金丹等）
            - 包含仙门、魔道、散修等势力
            - 设定灵气、法宝、丹药等修仙元素
            - 创造适合修仙的地理环境（如灵山、秘境等）
            """
        elif self.novel_style == NovelStyle.SCIFI:
            description += """
            
            特别要求：
            - 设计科技发展水平和未来社会结构
            - 包含星际文明、AI技术、基因改造等元素
            - 设定宇宙背景和星际政治格局
            - 创造科幻色彩的地点和设施
            """
        elif self.novel_style == NovelStyle.URBAN:
            description += """
            
            特别要求：
            - 基于现代都市背景，可加入超自然元素
            - 包含商业、政治、娱乐等现代社会要素
            - 设计都市中的隐秘世界或特殊能力体系
            """

        return Task(
            description=description,
            agent=agent,
            expected_output="""一个完整的世界观设定，包含：
            - world_setting: 完整的世界观描述
            - world_name: 世界名称
            - world_description: 世界背景描述
            - power_system: 力量体系
            - main_locations: 主要地点列表
            - key_factions: 重要势力列表
            - world_rules: 世界规则列表
            """,
            output_pydantic=WorldSettingOutput,
        )

    def protagonist_task(self, world_setting: WorldSettingOutput, agent: Agent) -> Task:
        """主人公生成任务"""
        description = f"""
        基于世界观设定，为{self.style_value}小说创造一个主人公角色：
        
        世界观：
        - 世界名称：{world_setting.world_name}
        - 世界描述：{world_setting.world_description}
        - 力量体系：{world_setting.power_system}
        - 主要地点：{', '.join(world_setting.main_locations)}
        - 重要势力：{', '.join(world_setting.key_factions)}
        
        任务要求：
        1. 创造符合世界观的主人公形象
        2. 设定合理的年龄、性别、外貌
        3. 设计独特的性格特点和背景故事
        4. 规划初始能力和成长目标
        5. 设定角色弱点和特殊特质
        6. 创造引人入胜的开局场景
        
        确保角色与世界观完美融合，具有成长潜力和读者吸引力。
        """

        return Task(
            description=description,
            agent=agent,
            expected_output="""一个完整的主人公角色设定，包含：
            - name: 姓名
            - age: 年龄
            - gender: 性别
            - appearance: 外貌描述
            - personality: 性格特点
            - background: 背景故事
            - initial_abilities: 初始能力列表
            - goals: 目标列表
            - weaknesses: 弱点列表
            - special_traits: 特殊特质
            - starting_scenario: 开局场景
            """,
            output_pydantic=ProtagonistGenerationOutput
        )

    def start_chapter_task(self, world_setting: WorldSettingOutput, protagonist: ProtagonistGenerationOutput,
                           agent: Agent) -> Task:
        """第一章创作任务"""
        description = f"""
        基于世界观设定和主人公信息，创作{self.style_value}小说的第一章内容。
        
        世界观信息：
        - 世界：{world_setting.world_name}
        - 背景：{world_setting.world_description}
        - 力量体系：{world_setting.power_system}
        
        主人公信息：
        - 姓名：{protagonist.name}
        - 年龄：{protagonist.age}
        - 性格：{protagonist.personality}
        - 背景：{protagonist.background}
        - 开局场景：{protagonist.starting_scenario}
        
        任务要求：
        1. 创作引人入胜的章节标题
        2. 编写精彩的章节内容（2000-3000字）
        3. 撰写剧情摘要
        4. 描述角色发展情况
        5. 扩展世界观细节
        6. 设计2-3个有意义的选择分支
        7. 判断是否为关键节点
        
        确保内容符合{self.style_value}小说特色，节奏紧凑，情节吸引人。
        """

        return Task(
            description=description,
            agent=agent,
            expected_output="""一个完整的章节内容，包含：
            - chapter_title: 章节标题
            - chapter_content: 章节内容（2000-3000字）
            - story_summary: 剧情摘要
            - character_development: 角色发展
            - world_expansion: 世界观扩展
            - choices: 选择项列表（每项包含choice_text和description）
            - is_critical_moment: 是否为关键节点（布尔值）
            - is_ending: 是否为结局（默认false）
            """,
            output_pydantic=ChapterOutput,
        )

    def next_chapter_task(self, world_setting: WorldSettingOutput, protagonist: ProtagonistGenerationOutput,
                          story_history: ChapterOutput, current_chapter: int, agent: Agent) -> Task:
        """后续章节创作任务"""
        description = f"""
        基于世界观、主人公信息和故事历史，创作{self.style_value}小说的第{current_chapter}章内容。
        
        世界观信息：
        - 世界：{world_setting.world_name}
        - 背景：{world_setting.world_description}
        
        主人公信息：
        - 姓名：{protagonist.name}
        - 当前状态和能力需要根据故事发展进行更新
        
        故事历史：
        - 前章标题：{story_history.chapter_title}
        - 前章摘要：{story_history.story_summary}
        - 角色发展：{story_history.character_development}
        
        任务要求：
        1. 承接前章剧情，保持故事连贯性
        2. 创作新的章节标题和内容
        3. 推进主线剧情发展
        4. 展现角色成长和变化
        5. 继续扩展世界观
        6. 设计新的选择分支
        7. 评估是否到达关键节点或结局
        
        确保内容质量和{self.style_value}小说特色。
        """

        return Task(
            description=description,
            agent=agent,
            expected_output="""一个完整的章节内容，包含：
            - chapter_title: 章节标题
            - chapter_content: 章节内容（2000-3000字）
            - story_summary: 剧情摘要
            - character_development: 角色发展
            - world_expansion: 世界观扩展
            - choices: 选择项列表
            - is_critical_moment: 是否为关键节点
            - is_ending: 是否为结局
            """,
            output_pydantic=ChapterOutput
        )
