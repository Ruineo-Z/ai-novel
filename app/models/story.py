from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class StorySession(Base):
    """故事会话，记录用户的阅读进度和选择历史"""
    __tablename__ = "story_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    novel_id = Column(Integer, ForeignKey("novels.id"), nullable=False)
    current_chapter = Column(Integer, default=1)
    session_data = Column(JSON)  # 存储会话状态和历史选择
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user = relationship("User")
    novel = relationship("Novel")

class GenerationLog(Base):
    """生成日志，记录AI生成的内容和质量评分"""
    __tablename__ = "generation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    model_used = Column(String(50), nullable=False)  # openai, gemini, ollama
    prompt_template = Column(Text)
    generated_content = Column(Text)
    quality_score = Column(Float)  # 内容质量评分
    generation_time = Column(Float)  # 生成耗时（秒）
    token_usage = Column(JSON)  # token使用情况
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    chapter = relationship("Chapter")