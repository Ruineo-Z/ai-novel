"""
AI互动小说 - 用户Schema
用户相关的Pydantic模型定义
"""
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, validator
from datetime import datetime

from app.schemas.common import BaseSchema, TimestampMixin, IDMixin, PaginationMixin


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class UserCreate(UserBase):
    """创建用户Schema"""
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v


class UserUpdate(BaseModel):
    """更新用户Schema"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class UserPasswordUpdate(BaseModel):
    """更新密码Schema"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    
    @validator('new_password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v


class UserResponse(UserBase, IDMixin, TimestampMixin):
    """用户响应Schema"""
    is_active: bool = Field(..., description="是否激活")
    is_verified: bool = Field(..., description="是否已验证邮箱")
    is_premium: bool = Field(..., description="是否为高级用户")
    premium_expires_at: Optional[datetime] = Field(None, description="高级会员过期时间")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    stories_created: int = Field(..., description="创建的故事数")
    stories_read: int = Field(..., description="阅读的故事数")
    total_reading_time: int = Field(..., description="总阅读时间（分钟）")
    
    class Config:
        from_attributes = True


class UserPublicResponse(BaseModel):
    """用户公开信息Schema"""
    id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    stories_created: int = Field(..., description="创建的故事数")
    is_premium: bool = Field(..., description="是否为高级用户")
    created_at: datetime = Field(..., description="注册时间")
    
    class Config:
        from_attributes = True


class UserList(PaginationMixin):
    """用户列表Schema"""
    users: List[UserResponse] = Field(..., description="用户列表")


class UserStats(BaseModel):
    """用户统计Schema"""
    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    verified_users: int = Field(..., description="已验证用户数")
    premium_users: int = Field(..., description="高级用户数")
    inactive_users: int = Field(..., description="非活跃用户数")
    unverified_users: int = Field(..., description="未验证用户数")
    free_users: int = Field(..., description="免费用户数")
    
    # 增长统计
    new_users_today: Optional[int] = Field(None, description="今日新增用户")
    new_users_this_week: Optional[int] = Field(None, description="本周新增用户")
    new_users_this_month: Optional[int] = Field(None, description="本月新增用户")
    
    # 活跃度统计
    daily_active_users: Optional[int] = Field(None, description="日活跃用户")
    weekly_active_users: Optional[int] = Field(None, description="周活跃用户")
    monthly_active_users: Optional[int] = Field(None, description="月活跃用户")


class UserLogin(BaseModel):
    """用户登录Schema"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")


class UserLoginResponse(BaseModel):
    """用户登录响应Schema"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: UserResponse = Field(..., description="用户信息")


class UserRegister(UserCreate):
    """用户注册Schema"""
    confirm_password: str = Field(..., description="确认密码")
    agree_terms: bool = Field(..., description="同意服务条款")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """验证密码确认"""
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v
    
    @validator('agree_terms')
    def must_agree_terms(cls, v):
        """必须同意条款"""
        if not v:
            raise ValueError('必须同意服务条款')
        return v


class UserEmailVerification(BaseModel):
    """邮箱验证Schema"""
    email: EmailStr = Field(..., description="邮箱地址")
    verification_code: str = Field(..., min_length=6, max_length=6, description="验证码")


class UserPasswordReset(BaseModel):
    """密码重置Schema"""
    email: EmailStr = Field(..., description="邮箱地址")


class UserPasswordResetConfirm(BaseModel):
    """密码重置确认Schema"""
    email: EmailStr = Field(..., description="邮箱地址")
    reset_code: str = Field(..., min_length=6, max_length=6, description="重置码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    
    @validator('new_password')
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('密码必须包含大写字母、小写字母和数字')
        
        return v


class UserPreferences(BaseModel):
    """用户偏好设置Schema"""
    theme: Optional[str] = Field("light", description="主题设置")
    language: Optional[str] = Field("zh-CN", description="语言设置")
    notifications_enabled: bool = Field(True, description="是否启用通知")
    email_notifications: bool = Field(True, description="是否启用邮件通知")
    reading_speed: Optional[int] = Field(200, ge=50, le=1000, description="阅读速度（字/分钟）")
    auto_save: bool = Field(True, description="是否自动保存进度")
    privacy_level: Optional[str] = Field("public", description="隐私级别")


class UserActivity(BaseModel):
    """用户活动Schema"""
    activity_type: str = Field(..., description="活动类型")
    activity_data: dict = Field(..., description="活动数据")
    timestamp: datetime = Field(..., description="活动时间")
    ip_address: Optional[str] = Field(None, description="IP地址")
    user_agent: Optional[str] = Field(None, description="用户代理")
