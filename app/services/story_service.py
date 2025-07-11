"""
故事服务层 - 处理故事的业务逻辑和数据持久化
"""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.story import Story
from app.models.chapter import Chapter
from app.models.choice import Choice
from app.crud.story import story_crud
from app.crud.chapter import chapter_crud
from app.crud.choice import choice_crud
from app.services.ai import (
    get_story_generator,
    get_choice_generator,
    get_memory_manager,
    StoryGenerationRequest,
    ChapterGenerationRequest,
    ChoiceGenerationRequest,
    MemoryItem
)
from app.services.ai.base import StoryTheme
from app.core.logging import get_logger

logger = get_logger(__name__)


class StoryService:
    """故事服务 - 整合AI生成和数据持久化"""
    
    def __init__(self):
        self.story_generator = get_story_generator()
        self.choice_generator = get_choice_generator()
        self.memory_manager = get_memory_manager()
    
    async def create_story_with_ai(
        self,
        user_id: str,
        title: str,
        theme: StoryTheme,
        protagonist_name: str,
        protagonist_description: str,
        story_background: str
    ) -> Dict[str, Any]:
        """使用AI创建新故事并保存到数据库"""
        try:
            logger.info(f"开始为用户 {user_id} 创建故事: {title}")
            
            # 1. 使用AI生成故事开头
            ai_request = StoryGenerationRequest(
                theme=theme,
                title=title,
                protagonist_name=protagonist_name,
                protagonist_description=protagonist_description,
                story_background=story_background
            )
            
            ai_response = await self.story_generator.generate_story_opening(ai_request)
            
            # 2. 创建故事记录
            story_data = {
                "title": title,
                "theme": theme.value,
                "description": story_background,
                "user_id": user_id,
                "protagonist_name": protagonist_name,
                "protagonist_description": protagonist_description,
                "status": "active",
                "metadata": {
                    "ai_model": "gemini-1.5-flash",
                    "generation_time": ai_response.processing_time,
                    "tokens_used": ai_response.tokens_used
                }
            }
            
            story = await story_crud.create(story_data)
            logger.info(f"故事创建成功: {story.id}")
            
            # 3. 创建第一章
            chapter_data = {
                "story_id": story.id,
                "chapter_number": 1,
                "title": "开始",
                "content": ai_response.content,
                "summary": ai_response.metadata.get("summary", ""),
                "metadata": {
                    "key_elements": ai_response.metadata.get("key_elements", []),
                    "mood": ai_response.metadata.get("mood", ""),
                    "choice_setup": ai_response.metadata.get("choice_setup", "")
                }
            }
            
            chapter = await chapter_crud.create(chapter_data)
            logger.info(f"第一章创建成功: {chapter.id}")
            
            # 4. 生成选择选项
            choice_request = ChoiceGenerationRequest(
                story_context={
                    "theme": theme.value,
                    "background": story_background,
                    "protagonist": protagonist_name
                },
                current_chapter={
                    "content": ai_response.content,
                    "summary": ai_response.metadata.get("summary", "")
                },
                choice_setup=ai_response.metadata.get("choice_setup", "请选择下一步行动"),
                previous_choices=[],
                character_state={
                    "name": protagonist_name,
                    "health": "良好",
                    "skills": [],
                    "relationships": "独自一人"
                }
            )
            
            choice_options = await self.choice_generator.generate_choices(choice_request)
            
            # 5. 保存选择选项
            choices = []
            for i, option in enumerate(choice_options, 1):
                choice_data = {
                    "chapter_id": chapter.id,
                    "choice_number": i,
                    "text": option.text,
                    "description": option.description,
                    "consequence_hint": option.consequence_hint,
                    "metadata": {
                        "difficulty": option.difficulty,
                        "type": option.type
                    }
                }
                choice = await choice_crud.create(choice_data)
                choices.append(choice)
            
            logger.info(f"创建了 {len(choices)} 个选择选项")
            
            # 6. 存储AI记忆
            await self._store_story_memories(story.id, chapter.id, ai_response, story_data)
            
            return {
                "story": story,
                "first_chapter": chapter,
                "choices": choices,
                "ai_metadata": {
                    "processing_time": ai_response.processing_time,
                    "tokens_used": ai_response.tokens_used,
                    "summary": ai_response.metadata.get("summary", ""),
                    "mood": ai_response.metadata.get("mood", "")
                }
            }
            
        except Exception as e:
            logger.error(f"创建故事失败: {e}")
            raise
    
    async def continue_story_with_choice(
        self,
        story_id: str,
        chapter_id: str,
        choice_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """基于用户选择继续故事"""
        try:
            logger.info(f"用户 {user_id} 在故事 {story_id} 中做出选择 {choice_id}")
            
            # 1. 获取故事和章节信息
            story = await story_crud.get(story_id)
            if not story or story.user_id != user_id:
                raise ValueError("故事不存在或无权限")
            
            current_chapter = await chapter_crud.get(chapter_id)
            if not current_chapter or current_chapter.story_id != story_id:
                raise ValueError("章节不存在")
            
            choice = await choice_crud.get(choice_id)
            if not choice or choice.chapter_id != chapter_id:
                raise ValueError("选择不存在")
            
            # 2. 获取前面的章节历史
            previous_chapters = await chapter_crud.get_by_story_id(story_id)
            chapter_history = []
            for ch in previous_chapters:
                chapter_history.append({
                    "content": ch.content,
                    "summary": ch.summary,
                    "key_elements": ch.metadata.get("key_elements", [])
                })
            
            # 3. 使用AI生成新章节
            chapter_request = ChapterGenerationRequest(
                story_id=story_id,
                previous_chapters=chapter_history,
                user_choice=choice.text,
                choice_description=choice.description,
                story_context={
                    "theme": story.theme,
                    "background": story.description,
                    "protagonist": story.protagonist_name
                }
            )
            
            ai_response = await self.story_generator.generate_chapter(chapter_request)
            
            # 4. 创建新章节
            next_chapter_number = len(previous_chapters) + 1
            new_chapter_data = {
                "story_id": story_id,
                "chapter_number": next_chapter_number,
                "title": f"第{next_chapter_number}章",
                "content": ai_response.content,
                "summary": ai_response.metadata.get("summary", ""),
                "metadata": {
                    "key_elements": ai_response.metadata.get("key_elements", []),
                    "mood": ai_response.metadata.get("mood", ""),
                    "choice_setup": ai_response.metadata.get("choice_setup", ""),
                    "character_development": ai_response.metadata.get("character_development", ""),
                    "previous_choice": {
                        "choice_id": choice_id,
                        "text": choice.text,
                        "description": choice.description
                    }
                }
            }
            
            new_chapter = await chapter_crud.create(new_chapter_data)
            logger.info(f"新章节创建成功: {new_chapter.id}")
            
            # 5. 生成新的选择选项
            new_choice_request = ChoiceGenerationRequest(
                story_context={
                    "theme": story.theme,
                    "background": story.description,
                    "protagonist": story.protagonist_name
                },
                current_chapter={
                    "content": ai_response.content,
                    "summary": ai_response.metadata.get("summary", "")
                },
                choice_setup=ai_response.metadata.get("choice_setup", "请选择下一步行动"),
                previous_choices=[{
                    "text": choice.text,
                    "result": "已执行"
                }],
                character_state={
                    "name": story.protagonist_name,
                    "health": "良好"
                }
            )
            
            new_choice_options = await self.choice_generator.generate_choices(new_choice_request)
            
            # 6. 保存新选择选项
            new_choices = []
            for i, option in enumerate(new_choice_options, 1):
                choice_data = {
                    "chapter_id": new_chapter.id,
                    "choice_number": i,
                    "text": option.text,
                    "description": option.description,
                    "consequence_hint": option.consequence_hint,
                    "metadata": {
                        "difficulty": option.difficulty,
                        "type": option.type
                    }
                }
                new_choice = await choice_crud.create(choice_data)
                new_choices.append(new_choice)
            
            # 7. 更新故事统计
            await story_crud.update(story_id, {
                "updated_at": datetime.utcnow(),
                "metadata": {
                    **story.metadata,
                    "total_chapters": next_chapter_number,
                    "last_choice": choice.text,
                    "total_tokens": story.metadata.get("total_tokens", 0) + ai_response.tokens_used
                }
            })
            
            # 8. 存储新的AI记忆
            await self._store_chapter_memories(story_id, new_chapter.id, ai_response, choice)
            
            return {
                "new_chapter": new_chapter,
                "new_choices": new_choices,
                "story": story,
                "ai_metadata": {
                    "processing_time": ai_response.processing_time,
                    "tokens_used": ai_response.tokens_used,
                    "summary": ai_response.metadata.get("summary", ""),
                    "character_development": ai_response.metadata.get("character_development", "")
                }
            }
            
        except Exception as e:
            logger.error(f"继续故事失败: {e}")
            raise
    
    async def _store_story_memories(
        self,
        story_id: str,
        chapter_id: str,
        ai_response,
        story_data: Dict[str, Any]
    ):
        """存储故事相关的AI记忆"""
        try:
            # 角色记忆
            character_memory = MemoryItem(
                id=str(uuid.uuid4()),
                content=f"{story_data['protagonist_name']}: {story_data['protagonist_description']}",
                memory_type="character",
                importance=0.9,
                timestamp=datetime.now(),
                story_id=story_id,
                chapter_id=chapter_id,
                tags=["主角", "角色设定"],
                metadata={"character_name": story_data['protagonist_name']}
            )
            await self.memory_manager.store_memory(character_memory)
            
            # 设定记忆
            setting_memory = MemoryItem(
                id=str(uuid.uuid4()),
                content=f"故事背景: {story_data['description']}",
                memory_type="setting",
                importance=0.8,
                timestamp=datetime.now(),
                story_id=story_id,
                chapter_id=chapter_id,
                tags=["背景", "设定"],
                metadata={"theme": story_data['theme']}
            )
            await self.memory_manager.store_memory(setting_memory)
            
            # 情节记忆
            plot_memory = MemoryItem(
                id=str(uuid.uuid4()),
                content=ai_response.metadata.get("summary", ""),
                memory_type="plot",
                importance=0.7,
                timestamp=datetime.now(),
                story_id=story_id,
                chapter_id=chapter_id,
                tags=["开头", "情节"],
                metadata={"chapter_number": 1}
            )
            await self.memory_manager.store_memory(plot_memory)
            
            logger.info(f"故事记忆存储完成: {story_id}")
            
        except Exception as e:
            logger.error(f"存储故事记忆失败: {e}")
    
    async def _store_chapter_memories(
        self,
        story_id: str,
        chapter_id: str,
        ai_response,
        choice
    ):
        """存储章节相关的AI记忆"""
        try:
            # 选择记忆
            choice_memory = MemoryItem(
                id=str(uuid.uuid4()),
                content=f"用户选择: {choice.text} - {choice.description}",
                memory_type="choice",
                importance=0.6,
                timestamp=datetime.now(),
                story_id=story_id,
                chapter_id=chapter_id,
                tags=["选择", "决策"],
                metadata={"choice_id": choice.id}
            )
            await self.memory_manager.store_memory(choice_memory)
            
            # 情节发展记忆
            if ai_response.metadata.get("summary"):
                plot_memory = MemoryItem(
                    id=str(uuid.uuid4()),
                    content=ai_response.metadata.get("summary"),
                    memory_type="plot",
                    importance=0.7,
                    timestamp=datetime.now(),
                    story_id=story_id,
                    chapter_id=chapter_id,
                    tags=["情节发展"],
                    metadata={"chapter_id": chapter_id}
                )
                await self.memory_manager.store_memory(plot_memory)
            
            logger.info(f"章节记忆存储完成: {chapter_id}")
            
        except Exception as e:
            logger.error(f"存储章节记忆失败: {e}")


# 全局故事服务实例
story_service = StoryService()
