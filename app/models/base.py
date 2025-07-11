"""
AI互动小说 - 基础数据模型
包含所有模型的通用字段和方法
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base

from app.core.database import Base


class TimestampMixin:
    """时间戳混入类"""
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="创建时间"
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="更新时间"
    )


class UUIDMixin:
    """UUID主键混入类"""
    
    @declared_attr
    def id(cls):
        return Column(
            String(36),
            primary_key=True,
            default=lambda: str(uuid.uuid4()),
            comment="主键ID"
        )


class SoftDeleteMixin:
    """软删除混入类"""
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否已删除"
    )
    
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment="删除时间"
    )
    
    def soft_delete(self):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """恢复删除"""
        self.is_deleted = False
        self.deleted_at = None


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """基础模型类"""
    
    __abstract__ = True
    
    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        """转换为字典"""
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[list] = None):
        """从字典更新属性"""
        exclude = exclude or ['id', 'created_at', 'updated_at']
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def get_table_name(cls) -> str:
        """获取表名"""
        return cls.__tablename__
    
    def __repr__(self):
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={self.id})>"


class MetadataMixin:
    """元数据混入类 - 用于存储额外的JSON数据"""
    
    metadata = Column(
        Text,
        nullable=True,
        comment="元数据JSON"
    )
    
    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        import json
        
        if self.metadata:
            data = json.loads(self.metadata)
        else:
            data = {}
        
        data[key] = value
        self.metadata = json.dumps(data, ensure_ascii=False)
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        import json
        
        if not self.metadata:
            return default
        
        try:
            data = json.loads(self.metadata)
            return data.get(key, default)
        except (json.JSONDecodeError, TypeError):
            return default
    
    def get_all_metadata(self) -> Dict[str, Any]:
        """获取所有元数据"""
        import json
        
        if not self.metadata:
            return {}
        
        try:
            return json.loads(self.metadata)
        except (json.JSONDecodeError, TypeError):
            return {}


class VersionMixin:
    """版本控制混入类"""
    
    version = Column(
        String(20),
        default="1.0.0",
        nullable=False,
        comment="版本号"
    )
    
    def increment_version(self):
        """递增版本号"""
        try:
            major, minor, patch = map(int, self.version.split('.'))
            patch += 1
            self.version = f"{major}.{minor}.{patch}"
        except (ValueError, AttributeError):
            self.version = "1.0.1"


class StatusMixin:
    """状态混入类"""
    
    @declared_attr
    def status(cls):
        return Column(
            String(20),
            default="active",
            nullable=False,
            comment="状态"
        )
    
    def activate(self):
        """激活"""
        self.status = "active"
    
    def deactivate(self):
        """停用"""
        self.status = "inactive"
    
    def is_active(self) -> bool:
        """是否激活"""
        return self.status == "active"


# 常用的组合基类
class StandardModel(BaseModel, MetadataMixin):
    """标准模型 - 包含基础字段和元数据"""
    __abstract__ = True


class VersionedModel(BaseModel, VersionMixin):
    """版本化模型 - 包含版本控制"""
    __abstract__ = True


class StatusModel(BaseModel, StatusMixin):
    """状态模型 - 包含状态管理"""
    __abstract__ = True


class FullModel(BaseModel, MetadataMixin, VersionMixin, StatusMixin):
    """完整模型 - 包含所有功能"""
    __abstract__ = True
