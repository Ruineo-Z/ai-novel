from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
from pathlib import Path
from app.schemas.base import NovelStyle
from app.schemas.agent_outputs import WorldSettingOutput, ProtagonistGenerationOutput, ChapterOutput
from app.core.logger import get_logger

logger = get_logger(__name__)

class NovelCrewMemory:
    """CrewAI小说创作记忆管理器
    
    提供简单易用的记忆存储和检索功能，替代LangGraph的复杂记忆系统
    """
    
    def __init__(self, memory_dir: str = "crew_memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        self.sessions_dir = self.memory_dir / "sessions"
        self.templates_dir = self.memory_dir / "templates"
        self.sessions_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
    
    def save_session(self, session_id: str, novel_style: NovelStyle, 
                    world_setting: Optional[WorldSettingOutput] = None,
                    protagonist_info: Optional[ProtagonistGenerationOutput] = None,
                    chapters: Optional[List[ChapterOutput]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> bool:
        """保存会话数据"""
        try:
            session_data = {
                "session_id": session_id,
                "novel_style": novel_style.value,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "world_setting": world_setting.dict() if world_setting else None,
                "protagonist_info": protagonist_info.dict() if protagonist_info else None,
                "chapters": [chapter.dict() for chapter in chapters] if chapters else [],
                "metadata": metadata or {}
            }
            
            session_file = self.sessions_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"会话 {session_id} 保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存会话 {session_id} 失败: {str(e)}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if not session_file.exists():
                logger.warning(f"会话 {session_id} 不存在")
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # 转换回对象
            if session_data.get("world_setting"):
                session_data["world_setting"] = WorldSettingOutput(**session_data["world_setting"])
            
            if session_data.get("protagonist_info"):
                session_data["protagonist_info"] = ProtagonistGenerationOutput(**session_data["protagonist_info"])
            
            if session_data.get("chapters"):
                session_data["chapters"] = [ChapterOutput(**chapter) for chapter in session_data["chapters"]]
            
            session_data["novel_style"] = NovelStyle(session_data["novel_style"])
            
            logger.info(f"会话 {session_id} 加载成功")
            return session_data
            
        except Exception as e:
            logger.error(f"加载会话 {session_id} 失败: {str(e)}")
            return None
    
    def update_session(self, session_id: str, **updates) -> bool:
        """更新会话数据"""
        try:
            session_data = self.load_session(session_id)
            if not session_data:
                return False
            
            # 更新数据
            for key, value in updates.items():
                if key in session_data:
                    if hasattr(value, 'dict'):  # Pydantic模型
                        session_data[key] = value.dict()
                    else:
                        session_data[key] = value
            
            session_data["updated_at"] = datetime.now().isoformat()
            
            # 保存更新后的数据
            session_file = self.sessions_dir / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"会话 {session_id} 更新成功")
            return True
            
        except Exception as e:
            logger.error(f"更新会话 {session_id} 失败: {str(e)}")
            return False
    
    def add_chapter(self, session_id: str, chapter: ChapterOutput) -> bool:
        """向会话添加新章节"""
        try:
            session_data = self.load_session(session_id)
            if not session_data:
                return False
            
            chapters = session_data.get("chapters", [])
            chapters.append(chapter.dict())
            
            return self.update_session(session_id, chapters=chapters)
            
        except Exception as e:
            logger.error(f"添加章节到会话 {session_id} 失败: {str(e)}")
            return False
    
    def get_chapters(self, session_id: str) -> List[ChapterOutput]:
        """获取会话的所有章节"""
        try:
            session_data = self.load_session(session_id)
            if not session_data:
                return []
            
            return session_data.get("chapters", [])
            
        except Exception as e:
            logger.error(f"获取会话 {session_id} 章节失败: {str(e)}")
            return []
    
    def get_latest_chapter(self, session_id: str) -> Optional[ChapterOutput]:
        """获取最新章节"""
        chapters = self.get_chapters(session_id)
        return chapters[-1] if chapters else None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = []
        try:
            for session_file in self.sessions_dir.glob("*.json"):
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                sessions.append({
                    "session_id": session_data["session_id"],
                    "novel_style": session_data["novel_style"],
                    "created_at": session_data["created_at"],
                    "updated_at": session_data["updated_at"],
                    "chapter_count": len(session_data.get("chapters", []))
                })
            
            return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"列出会话失败: {str(e)}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                logger.info(f"会话 {session_id} 删除成功")
                return True
            else:
                logger.warning(f"会话 {session_id} 不存在")
                return False
                
        except Exception as e:
            logger.error(f"删除会话 {session_id} 失败: {str(e)}")
            return False
    
    def save_template(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """保存模板数据"""
        try:
            template_file = self.templates_dir / f"{template_name}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"模板 {template_name} 保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存模板 {template_name} 失败: {str(e)}")
            return False
    
    def load_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """加载模板数据"""
        try:
            template_file = self.templates_dir / f"{template_name}.json"
            if not template_file.exists():
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"加载模板 {template_name} 失败: {str(e)}")
            return None
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """获取会话上下文信息，用于Agent记忆"""
        session_data = self.load_session(session_id)
        if not session_data:
            return {}
        
        context = {
            "novel_style": session_data["novel_style"],
            "world_setting": session_data.get("world_setting"),
            "protagonist_info": session_data.get("protagonist_info"),
            "chapter_count": len(session_data.get("chapters", [])),
            "latest_chapter": session_data.get("chapters", [])[-1] if session_data.get("chapters") else None
        }
        
        return context
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """清理旧会话"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    updated_at = datetime.fromisoformat(session_data["updated_at"])
                    if updated_at < cutoff_date:
                        session_file.unlink()
                        deleted_count += 1
                        logger.info(f"删除旧会话: {session_data['session_id']}")
                        
                except Exception as e:
                    logger.error(f"处理会话文件 {session_file} 时出错: {str(e)}")
            
            logger.info(f"清理完成，删除了 {deleted_count} 个旧会话")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理旧会话失败: {str(e)}")
            return 0

# 全局记忆管理器实例
_memory_manager = None

def get_memory_manager() -> NovelCrewMemory:
    """获取全局记忆管理器实例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = NovelCrewMemory()
    return _memory_manager