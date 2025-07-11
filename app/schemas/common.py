"""
AI互动小说 - 通用Schema
通用的Pydantic模型定义
"""
from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str = Field(..., description="响应消息")
    code: Optional[int] = Field(None, description="响应代码")
    data: Optional[Any] = Field(None, description="附加数据")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="错误详情")
    code: Optional[int] = Field(None, description="错误代码")


class PaginationMixin(BaseModel):
    """分页混入"""
    total: int = Field(..., description="总记录数")
    skip: int = Field(..., description="跳过的记录数")
    limit: int = Field(..., description="每页记录数")
    
    @property
    def has_next(self) -> bool:
        """是否有下一页"""
        return self.skip + self.limit < self.total
    
    @property
    def has_prev(self) -> bool:
        """是否有上一页"""
        return self.skip > 0
    
    @property
    def page(self) -> int:
        """当前页码（从1开始）"""
        return (self.skip // self.limit) + 1
    
    @property
    def total_pages(self) -> int:
        """总页数"""
        return (self.total + self.limit - 1) // self.limit


class BaseSchema(BaseModel):
    """基础Schema"""
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TimestampMixin(BaseModel):
    """时间戳混入"""
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class IDMixin(BaseModel):
    """ID混入"""
    id: str = Field(..., description="唯一标识符")


class MetadataMixin(BaseModel):
    """元数据混入"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    skip: int = Field(0, ge=0, description="跳过的记录数")
    limit: int = Field(100, ge=1, le=1000, description="返回的记录数")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_desc: bool = Field(False, description="是否降序排列")


class SearchResponse(PaginationMixin):
    """搜索响应"""
    query: str = Field(..., description="搜索关键词")
    results: List[Any] = Field(..., description="搜索结果")
    took: Optional[float] = Field(None, description="搜索耗时（秒）")


class HealthCheck(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    service: str = Field(..., description="服务名称")
    environment: str = Field(..., description="运行环境")
    components: Dict[str, Any] = Field(..., description="组件状态")


class StatsResponse(BaseModel):
    """统计响应"""
    total: int = Field(..., description="总数")
    active: Optional[int] = Field(None, description="活跃数")
    inactive: Optional[int] = Field(None, description="非活跃数")
    growth_rate: Optional[float] = Field(None, description="增长率")
    period: Optional[str] = Field(None, description="统计周期")
    breakdown: Optional[Dict[str, int]] = Field(None, description="分类统计")


class BulkOperationRequest(BaseModel):
    """批量操作请求"""
    ids: List[str] = Field(..., min_items=1, max_items=1000, description="ID列表")
    operation: str = Field(..., description="操作类型")
    params: Optional[Dict[str, Any]] = Field(None, description="操作参数")


class BulkOperationResponse(BaseModel):
    """批量操作响应"""
    total: int = Field(..., description="总操作数")
    success: int = Field(..., description="成功数")
    failed: int = Field(..., description="失败数")
    errors: Optional[List[str]] = Field(None, description="错误信息列表")
    results: Optional[List[Any]] = Field(None, description="操作结果")


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    filename: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    url: str = Field(..., description="文件访问URL")
    content_type: str = Field(..., description="文件类型")
    upload_time: datetime = Field(..., description="上传时间")


class ExportRequest(BaseModel):
    """导出请求"""
    format: str = Field("json", description="导出格式")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    fields: Optional[List[str]] = Field(None, description="导出字段")
    include_metadata: bool = Field(False, description="是否包含元数据")


class ImportRequest(BaseModel):
    """导入请求"""
    data: List[Dict[str, Any]] = Field(..., description="导入数据")
    mode: str = Field("create", description="导入模式：create/update/upsert")
    validate_only: bool = Field(False, description="仅验证不导入")
    batch_size: int = Field(100, ge=1, le=1000, description="批处理大小")


class ImportResponse(BaseModel):
    """导入响应"""
    total: int = Field(..., description="总记录数")
    created: int = Field(..., description="创建数")
    updated: int = Field(..., description="更新数")
    skipped: int = Field(..., description="跳过数")
    errors: List[str] = Field(..., description="错误信息")
    validation_errors: Optional[List[str]] = Field(None, description="验证错误")


class CacheInfo(BaseModel):
    """缓存信息"""
    key: str = Field(..., description="缓存键")
    ttl: Optional[int] = Field(None, description="剩余生存时间（秒）")
    size: Optional[int] = Field(None, description="缓存大小（字节）")
    hit_count: Optional[int] = Field(None, description="命中次数")
    miss_count: Optional[int] = Field(None, description="未命中次数")


class SystemInfo(BaseModel):
    """系统信息"""
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="内存使用率")
    disk_usage: float = Field(..., description="磁盘使用率")
    uptime: int = Field(..., description="运行时间（秒）")
    connections: int = Field(..., description="当前连接数")
    requests_per_minute: float = Field(..., description="每分钟请求数")
