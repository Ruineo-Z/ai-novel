from typing import List, Optional

from app.schemas.base import NovelStyle
from app.schemas.agent_outputs import WorldSettingOutput, ChapterOutput, ProtagonistGenerationOutput


class PromptManager:
    def __init__(self, novel_style: NovelStyle):
        self.novel_style = novel_style
        self.style_value = novel_style.value

    def get_world_setting_prompt(self) -> str:
        """获取世界观设置提示词"""
        base_prompt = f"""
请为{self.style_value}类型的小说创建一个完整的世界观设定，包括：
1. 世界名称和背景描述
2. 力量体系（如修仙境界、科技等级、武功体系等）
3. 主要地点和地理环境
4. 重要势力和组织
5. 世界运行规则和法则

请确保世界观设定符合{self.style_value}小说的特点和读者期待。
        
禁止生成任何人物
        """

        # 根据不同小说类型添加特定要求
        if self.novel_style == NovelStyle.XIANXIA:
            base_prompt += """
特别要求：
- 设计完整的修仙境界体系（如练气、筑基、金丹等）
- 包含仙门、魔道、散修等势力
- 设定灵气、法宝、丹药等修仙元素
- 创造适合修仙的地理环境（如灵山、秘境等）
            """
        elif self.novel_style == NovelStyle.SCIFI:
            base_prompt += """
特别要求：
- 设计科技发展水平和未来社会结构
- 包含星际文明、AI技术、基因改造等元素
- 设定宇宙背景和星际政治格局
- 创造科幻色彩的地点和设施
            """
        elif self.novel_style == NovelStyle.URBAN:
            base_prompt += """
特别要求：
- 基于现代都市背景，可加入超自然元素
- 包含商业、政治、娱乐等现代社会要素
- 设定都市中的隐秘世界或特殊能力
- 创造现代都市的特色地点
            """
        elif self.novel_style == NovelStyle.ROMANCE:
            base_prompt += """
特别要求：
- 创造浪漫的背景环境
- 设定有利于情感发展的社交场所
- 包含能够推动感情线的社会背景
- 营造适合爱情故事的氛围
            """
        elif self.novel_style == NovelStyle.WUXIA:
            base_prompt += """
特别要求：
- 设计武功体系和江湖门派
- 包含正派、邪派、中立势力
- 设定江湖规则和武林秘籍
- 创造经典的武侠场景（如客栈、山庄、秘洞等）
            """

        return base_prompt

    def get_protagonist_generation_prompt(self, world_setting: WorldSettingOutput) -> str:
        """获取主人公生成提示词"""
        prompt = f"""
请为{self.style_value}类型的小说创建一个主人公，要求：
1. 符合{self.style_value}小说的主人公特点
2. 具有成长潜力和鲜明个性
3. 拥有合理的背景故事和动机
4. 设定初始能力和成长方向
5. 包含弱点和缺陷，使角色更真实

请提供详细的角色信息，包括姓名、年龄、性别、外貌、性格、背景、初始能力、目标和弱点。
        """

        if world_setting:
            prompt += f"""

世界观背景：
{world_setting}

请确保主人公设定与上述世界观相符合。
            """

        return prompt

    def get_start_chapter_prompt(self, world_setting: WorldSettingOutput,
                                 protagonist_info: ProtagonistGenerationOutput) -> str:
        """生成小说开场章节的提示词"""
        prompt = f"""
    你是一名专业的{self.style_value}小说作家，你特别擅长创作小说的开场内容。

    请根据以下要求，创作小说开场内容：
    1. 情节紧凑，符合{self.style_value}小说的风格特点
    2. 包含适当的冲突和悬念
    3. 在章节结尾提供3个不同故事走向的选项
    4. 字数控制在1500字左右（汉字）
    5. 围绕主人公的信息创作

    章节应该包括：
    - 引人入胜的章节标题
    - 生动的场景描写
    - 角色对话和心理活动
    - 情节推进和转折
    - 为读者提供的选择项

    主人公信息：
    {protagonist_info}

    世界观设定：
    {world_setting}
    """

        return prompt

    def get_next_chapter_prompt(self, protagonist_info: ProtagonistGenerationOutput,
                                world_setting: WorldSettingOutput,
                                story_history: Optional[ChapterOutput] = None,
                                current_chapter: int = 1) -> str:
        """获取后续章节内容生成提示词"""
        prompt = f"""
你是一名优秀的{self.style_value}小说作家，擅长创作引人入胜的章节内容。

请创作第{current_chapter}章的内容，要求：
1. 情节紧凑，符合{self.style_value}小说的风格特点
2. 推进主线剧情，展现角色成长
3. 包含适当的冲突和悬念
4. 在章节结尾提供3个不同故事走向的选择项
5. 字数控制在1500字左右（汉字）

章节应该包括：
- 引人入胜的章节标题
- 生动的场景描写
- 角色对话和心理活动
- 情节推进和转折
- 为读者提供的选择项

注意：
- 必须参考上一章结尾，主角的选择进行创作，内容必须有关联性
- 如果主角的选择会导致故事结束，你必须巧妙的安排故事结束，此时，不再提供选项
        """

        if protagonist_info:
            prompt += f"""

主人公信息：
{protagonist_info}
            """

        if world_setting:
            prompt += f"""

世界观设定：
{world_setting}
            """

        if story_history:
            prompt += f"""

前情回顾：
{chr(10).join(story_history[-3:])}
            """

        return prompt

    def get_ending_generation_prompt(self, story_history: List[str],
                                     protagonist_info: Optional[str] = None,
                                     chosen_ending_type: str = "圆满结局") -> str:
        """获取结局生成提示词"""
        prompt = f"""
你是一名擅长创作{self.style_value}小说结局的作家，能够为故事创造令人满意的结尾。

请为这个故事创作一个{chosen_ending_type}：

故事历程：
{chr(10).join(story_history)}
        """

        if protagonist_info:
            prompt += f"""

主人公信息：
{protagonist_info}
            """

        prompt += f"""

结局要求：
1. 符合{self.style_value}小说的结局特点
2. 与前面的剧情发展逻辑一致
3. 给主人公一个合理的归宿
4. 解决主要的故事线和冲突
5. 给读者留下深刻印象

请创作一个完整的结局章节，包括标题和内容。
        """
        return prompt
