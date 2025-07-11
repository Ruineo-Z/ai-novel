"""
AI互动小说 - 故事Schema
故事相关的Pydantic模型定义
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

from app.schemas.common import BaseSchema, TimestampMixin, IDMixin, PaginationMixin


class StoryTheme(str, Enum):
    """故事主题枚举"""
    URBAN = "urban"
    SCIFI = "scifi"
    CULTIVATION = "cultivation"
    MARTIAL_ARTS = "martial_arts"


class StoryStatus(str, Enum):
    """故事状态枚举"""
    DRAFT = "draft"
    PUBLISHED = "published"
    COMPLETED = "completed"
    SUSPENDED = "suspended"


class StoryBase(BaseModel):
    """故事基础Schema"""
    title: str = Field(..., min_length=1, max_length=200, description="故事标题")
    description: Optional[str] = Field(None, max_length=1000, description="故事描述")
    theme: StoryTheme = Field(..., description="故事主题")
    protagonist_name: str = Field(..., min_length=1, max_length=100, description="主角姓名")
    protagonist_description: Optional[str] = Field(None, max_length=500, description="主角描述")
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    
    @validator('tags')
    def validate_tags(cls, v):
        """验证标签"""
        if v and len(v) > 10:
            raise ValueError('标签数量不能超过10个')
        if v:
            for tag in v:
                if len(tag) > 20:
                    raise ValueError('单个标签长度不能超过20个字符')
        return v


class StoryCreate(StoryBase):
    """创建故事Schema"""
    author_id: str = Field(..., description="作者ID")
    story_background: Optional[str] = Field(None, max_length=1000, description="故事背景")
    initial_settings: Optional[Dict[str, Any]] = Field(None, description="初始设置")


class StoryUpdate(BaseModel):
    """更新故事Schema"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="故事标题")
    description: Optional[str] = Field(None, max_length=1000, description="故事描述")
    protagonist_name: Optional[str] = Field(None, min_length=1, max_length=100, description="主角姓名")
    protagonist_description: Optional[str] = Field(None, max_length=500, description="主角描述")
    cover_image_url: Optional[str] = Field(None, description="封面图片URL")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    story_status: Optional[StoryStatus] = Field(None, description="故事状态")
    
    @validator('tags')
    def validate_tags(cls, v):
        """验证标签"""
        if v and len(v) > 10:
            raise ValueError('标签数量不能超过10个')
        if v:
            for tag in v:
                if len(tag) > 20:
                    raise ValueError('单个标签长度不能超过20个字符')
        return v


class StoryResponse(StoryBase, IDMixin, TimestampMixin):
    """故事响应Schema"""
    author_id: str = Field(..., description="作者ID")
    story_status: StoryStatus = Field(..., description="故事状态")
    total_chapters: int = Field(..., description="总章节数")
    total_words: int = Field(..., description="总字数")
    total_readers: int = Field(..., description="总读者数")
    total_reads: int = Field(..., description="总阅读次数")
    average_rating: float = Field(..., description="平均评分")
    published_at: Optional[datetime] = Field(None, description="发布时间")
    completed_at: Optional[datetime] = Field(None, description="完结时间")
    last_chapter_at: Optional[datetime] = Field(None, description="最后更新章节时间")
    
    class Config:
        from_attributes = True


class StoryDetailResponse(StoryResponse):
    """故事详情响应Schema"""
    story_background: Optional[str] = Field(None, description="故事背景")
    initial_settings: Optional[Dict[str, Any]] = Field(None, description="初始设置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    # 作者信息
    author_username: Optional[str] = Field(None, description="作者用户名")
    author_nickname: Optional[str] = Field(None, description="作者昵称")
    
    # 统计信息
    chapters_published: Optional[int] = Field(None, description="已发布章节数")
    latest_chapter_title: Optional[str] = Field(None, description="最新章节标题")
    reading_time_estimate: Optional[int] = Field(None, description="预估阅读时间（分钟）")


class StoryList(PaginationMixin):
    """故事列表Schema"""
    stories: List[StoryResponse] = Field(..., description="故事列表")


class StoryPublishRequest(BaseModel):
    """故事发布请求Schema"""
    publish_message: Optional[str] = Field(None, max_length=200, description="发布说明")
    schedule_time: Optional[datetime] = Field(None, description="定时发布时间")


class StoryStats(BaseModel):
    """故事统计Schema"""
    total_stories: int = Field(..., description="总故事数")
    published_stories: int = Field(..., description="已发布故事数")
    completed_stories: int = Field(..., description="已完结故事数")
    draft_stories: int = Field(..., description="草稿故事数")
    theme_distribution: Dict[str, int] = Field(..., description="主题分布")
    
    # 增长统计
    new_stories_today: Optional[int] = Field(None, description="今日新增故事")
    new_stories_this_week: Optional[int] = Field(None, description="本周新增故事")
    new_stories_this_month: Optional[int] = Field(None, description="本月新增故事")
    
    # 热门统计
    most_read_stories: Optional[List[Dict[str, Any]]] = Field(None, description="最受欢迎故事")
    trending_stories: Optional[List[Dict[str, Any]]] = Field(None, description="趋势故事")


class StorySearchRequest(BaseModel):
    """故事搜索请求Schema"""
    query: Optional[str] = Field(None, description="搜索关键词")
    theme: Optional[StoryTheme] = Field(None, description="故事主题")
    status: Optional[StoryStatus] = Field(None, description="故事状态")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    author_id: Optional[str] = Field(None, description="作者ID")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="最低评分")
    min_chapters: Optional[int] = Field(None, ge=0, description="最少章节数")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_desc: bool = Field(True, description="是否降序")
    skip: int = Field(0, ge=0, description="跳过记录数")
    limit: int = Field(100, ge=1, le=1000, description="返回记录数")


class StoryRating(BaseModel):
    """故事评分Schema"""
    rating: int = Field(..., ge=1, le=5, description="评分（1-5星）")
    comment: Optional[str] = Field(None, max_length=500, description="评价内容")


class StoryBookmark(BaseModel):
    """故事收藏Schema"""
    is_bookmarked: bool = Field(..., description="是否收藏")
    bookmark_note: Optional[str] = Field(None, max_length=200, description="收藏备注")


class StoryProgress(BaseModel):
    """故事阅读进度Schema"""
    story_id: str = Field(..., description="故事ID")
    current_chapter_id: Optional[str] = Field(None, description="当前章节ID")
    chapters_read: int = Field(..., description="已读章节数")
    total_reading_time: int = Field(..., description="总阅读时间（分钟）")
    progress_percentage: float = Field(..., description="阅读进度百分比")
    last_read_at: datetime = Field(..., description="最后阅读时间")
    is_completed: bool = Field(..., description="是否已完成")
    user_rating: Optional[int] = Field(None, description="用户评分")


class StoryRecommendation(BaseModel):
    """故事推荐Schema"""
    story: StoryResponse = Field(..., description="推荐故事")
    reason: str = Field(..., description="推荐理由")
    similarity_score: float = Field(..., description="相似度分数")
    recommendation_type: str = Field(..., description="推荐类型")


class StoryGeneration(BaseModel):
    """故事生成请求Schema"""
    theme: StoryTheme = Field(..., description="故事主题")
    protagonist_name: str = Field(..., description="主角姓名")
    protagonist_description: str = Field(..., description="主角描述")
    story_background: str = Field(..., description="故事背景")
    initial_situation: Optional[str] = Field(None, description="初始情况")
    style_preferences: Optional[Dict[str, Any]] = Field(None, description="风格偏好")
    length_preference: Optional[str] = Field("medium", description="长度偏好")


class StoryGenerationResponse(BaseModel):
    """故事生成响应Schema"""
    story_id: str = Field(..., description="生成的故事ID")
    title: str = Field(..., description="生成的标题")
    opening_content: str = Field(..., description="开篇内容")
    initial_choices: List[Dict[str, Any]] = Field(..., description="初始选择")
    generation_metadata: Dict[str, Any] = Field(..., description="生成元数据")
    estimated_chapters: Optional[int] = Field(None, description="预估章节数")


class StoryExport(BaseModel):
    """故事导出Schema"""
    format: str = Field("json", description="导出格式")
    include_chapters: bool = Field(True, description="是否包含章节")
    include_choices: bool = Field(True, description="是否包含选择")
    include_metadata: bool = Field(False, description="是否包含元数据")
    chapter_range: Optional[List[int]] = Field(None, description="章节范围")


class StoryImport(BaseModel):
    """故事导入Schema"""
    story_data: Dict[str, Any] = Field(..., description="故事数据")
    import_mode: str = Field("create", description="导入模式")
    preserve_ids: bool = Field(False, description="是否保留原ID")
    validate_only: bool = Field(False, description="仅验证不导入")
