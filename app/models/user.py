"""
AI互动小说 - 用户模型
用户认证、个人信息和偏好设置
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, Index
from sqlalchemy.orm import relationship

from app.models.base import FullModel


class User(FullModel):
    """用户模型"""

    __tablename__ = "users"

    # 基本信息
    username = Column(
        String(50), unique=True, nullable=False, index=True, comment="用户名"
    )

    email = Column(
        String(255), unique=True, nullable=False, index=True, comment="邮箱地址"
    )

    hashed_password = Column(String(255), nullable=False, comment="加密密码")

    # 个人信息
    nickname = Column(String(100), nullable=True, comment="昵称")

    avatar_url = Column(String(500), nullable=True, comment="头像URL")

    bio = Column(Text, nullable=True, comment="个人简介")

    # 账户状态
    is_active = Column(Boolean, default=True, nullable=False, comment="账户是否激活")

    is_verified = Column(Boolean, default=False, nullable=False, comment="邮箱是否验证")

    is_premium = Column(
        Boolean, default=False, nullable=False, comment="是否为高级用户"
    )

    # 时间记录
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")

    email_verified_at = Column(DateTime, nullable=True, comment="邮箱验证时间")

    premium_expires_at = Column(DateTime, nullable=True, comment="高级会员过期时间")

    # 用户偏好设置
    preferred_language = Column(
        String(10), default="zh-CN", nullable=False, comment="首选语言"
    )

    preferred_theme = Column(
        String(20), default="light", nullable=False, comment="首选主题"
    )

    # 统计信息
    stories_created = Column(
        Integer, default=0, nullable=False, comment="创建的故事数量"
    )

    stories_read = Column(Integer, default=0, nullable=False, comment="阅读的故事数量")

    total_reading_time = Column(
        Integer, default=0, nullable=False, comment="总阅读时间(分钟)"
    )

    # 关系
    stories = relationship(
        "Story", back_populates="author", cascade="all, delete-orphan", lazy="dynamic"
    )

    story_progress = relationship(
        "UserStoryProgress",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    # 索引
    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_username_active", "username", "is_active"),
        Index("idx_user_created_at", "created_at"),
        Index("idx_user_last_login", "last_login_at"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.nickname:
            self.nickname = self.username

    @property
    def display_name(self) -> str:
        """显示名称"""
        return self.nickname or self.username

    @property
    def is_premium_active(self) -> bool:
        """高级会员是否有效"""
        if not self.is_premium:
            return False
        if not self.premium_expires_at:
            return True
        try:
            expire_time = datetime.fromisoformat(self.premium_expires_at)
            return expire_time > datetime.utcnow()
        except (ValueError, TypeError):
            return False

    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login_at = datetime.utcnow()

    def verify_email(self):
        """验证邮箱"""
        self.is_verified = True
        self.email_verified_at = datetime.utcnow()

    def activate_premium(self, days: int = 30):
        """激活高级会员"""
        from datetime import timedelta

        self.is_premium = True
        if self.premium_expires_at and self.premium_expires_at > datetime.utcnow():
            # 如果还有剩余时间，在现有基础上延长
            self.premium_expires_at += timedelta(days=days)
        else:
            # 否则从现在开始计算
            self.premium_expires_at = datetime.utcnow() + timedelta(days=days)

    def deactivate_premium(self):
        """取消高级会员"""
        self.is_premium = False
        self.premium_expires_at = None

    def increment_stories_created(self):
        """增加创建故事数量"""
        self.stories_created += 1

    def increment_stories_read(self):
        """增加阅读故事数量"""
        self.stories_read += 1

    def add_reading_time(self, minutes: int):
        """增加阅读时间"""
        self.total_reading_time += minutes

    def get_reading_stats(self) -> dict:
        """获取阅读统计"""
        stories_created = self.stories_created or 0
        stories_read = self.stories_read or 0
        total_reading_time = self.total_reading_time or 0

        return {
            "stories_created": stories_created,
            "stories_read": stories_read,
            "total_reading_time": total_reading_time,
            "average_reading_time": (
                total_reading_time / stories_read if stories_read > 0 else 0
            ),
        }

    def to_dict(self, exclude: Optional[List[str]] = None) -> dict:
        """转换为字典，排除敏感信息"""
        exclude = exclude or ["hashed_password"]
        return super().to_dict(exclude=exclude)

    def to_public_dict(self) -> dict:
        """转换为公开信息字典"""
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "is_premium": self.is_premium_active,
            "stories_created": self.stories_created,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
