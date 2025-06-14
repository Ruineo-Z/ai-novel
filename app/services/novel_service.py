import uuid
from typing import Dict, Optional, List
from app.schemas.base import NovelStyle, NovelSession, ProtagonistInfo, AIModel
from app.schemas.agent_outputs import WorldSettingOutput, ChapterOutput, ProtagonistGenerationOutput
from app.agents.agent_init import NovelCrewManager
from app.services.ai_factory import AIServiceFactory


class NovelService:
    """小说服务管理类"""

    def __init__(self):
        self.sessions: Dict[str, NovelSession] = {}
        self.world_settings: Dict[str, WorldSettingOutput] = {}
        self.chapters: Dict[str, List[ChapterOutput]] = {}

    async def create_novel(
            self,
            novel_style: NovelStyle,
            ai_model: AIModel = AIModel.GEMINI,
            use_custom_protagonist: bool = False,
            protagonist_info: Optional[ProtagonistInfo] = None
    ) -> tuple[str, WorldSettingOutput, ChapterOutput, ProtagonistInfo]:
        """创建新小说"""

        # 生成会话ID
        session_id = str(uuid.uuid4())

        # 创建AI服务和CrewAI管理器
        ai_service = AIServiceFactory.create_service(ai_model)
        crew_manager = NovelCrewManager(ai_service)

        # 生成世界观
        world_setting = await crew_manager.create_world_setting(
            novel_style=novel_style,
            protagonist=protagonist_info if use_custom_protagonist else None
        )

        # 生成或使用主人公信息
        if use_custom_protagonist and protagonist_info:
            final_protagonist = protagonist_info
        else:
            # 生成主人公
            generated_protagonist = await crew_manager.create_protagonist(
                novel_style=novel_style,
                world_setting=world_setting.world_description
            )
            final_protagonist = ProtagonistInfo(
                name=generated_protagonist.name,
                age=generated_protagonist.age,
                gender=generated_protagonist.gender,
                background=generated_protagonist.background,
                personality=generated_protagonist.personality,
                special_abilities=", ".join(generated_protagonist.initial_abilities)
            )

        # 生成第一章
        first_chapter = await crew_manager.write_chapter(
            novel_style=novel_style,
            world_setting=world_setting.world_description,
            protagonist=final_protagonist,
            story_history=[],
            choice_history=[],
            chapter_number=1
        )

        # 创建会话
        session = NovelSession(
            session_id=session_id,
            novel_style=novel_style,
            protagonist=final_protagonist,
            world_setting=world_setting.world_description,
            current_chapter=1,
            story_history=[first_chapter.story_summary],
            choice_history=[],
            ai_model=ai_model
        )

        # 保存会话数据
        self.sessions[session_id] = session
        self.world_settings[session_id] = world_setting
        self.chapters[session_id] = [first_chapter]

        return session_id, world_setting, first_chapter, final_protagonist

    async def make_choice(
            self,
            session_id: str,
            choice_id: int,
            custom_action: Optional[str] = None
    ) -> ChapterOutput:
        """做出选择并生成下一章"""

        if session_id not in self.sessions:
            raise ValueError("Session not found")

        session = self.sessions[session_id]
        current_chapters = self.chapters[session_id]

        if not current_chapters:
            raise ValueError("No chapters found for this session")

        current_chapter = current_chapters[-1]

        # 找到选择的内容
        selected_choice = None
        for choice in current_chapter.choices:
            if choice.id == choice_id:
                selected_choice = choice
                break

        if not selected_choice and not custom_action:
            raise ValueError("Invalid choice ID")

        choice_text = custom_action if custom_action else selected_choice.text

        # 记录选择
        choice_record = {
            "chapter_number": session.current_chapter,
            "choice_id": choice_id,
            "choice_text": choice_text,
            "custom_action": custom_action
        }
        session.choice_history.append(choice_record)

        # 创建AI服务和CrewAI管理器
        ai_service = AIServiceFactory.create_service(session.ai_model)
        crew_manager = NovelCrewManager(ai_service)

        # 生成下一章
        next_chapter_number = session.current_chapter + 1
        next_chapter = await crew_manager.write_chapter(
            novel_style=session.novel_style,
            world_setting=session.world_setting,
            protagonist=session.protagonist,
            story_history=session.story_history,
            choice_history=session.choice_history,
            chapter_number=next_chapter_number
        )

        # 更新会话
        session.current_chapter = next_chapter_number
        session.story_history.append(next_chapter.story_summary)

        # 保存新章节
        self.chapters[session_id].append(next_chapter)

        return next_chapter

    def get_session(self, session_id: str) -> Optional[NovelSession]:
        """获取会话信息"""
        return self.sessions.get(session_id)

    def get_world_setting(self, session_id: str) -> Optional[WorldSettingOutput]:
        """获取世界观设置"""
        return self.world_settings.get(session_id)

    def get_chapters(self, session_id: str) -> List[ChapterOutput]:
        """获取所有章节"""
        return self.chapters.get(session_id, [])

    def get_current_chapter(self, session_id: str) -> Optional[ChapterOutput]:
        """获取当前章节"""
        chapters = self.get_chapters(session_id)
        return chapters[-1] if chapters else None

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.world_settings.pop(session_id, None)
            self.chapters.pop(session_id, None)
            return True
        return False

    def list_sessions(self) -> List[Dict]:
        """列出所有会话"""
        result = []
        for session_id, session in self.sessions.items():
            result.append({
                "session_id": session_id,
                "novel_style": session.novel_style,
                "protagonist_name": session.protagonist.name if session.protagonist else None,
                "current_chapter": session.current_chapter,
                "ai_model": session.ai_model
            })
        return result


# 全局小说服务实例
novel_service = NovelService()
