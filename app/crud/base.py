"""
AI互动小说 - 基础CRUD操作
提供通用的数据库操作方法
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import and_, or_, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.sql import Select

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """基础CRUD操作类"""
    
    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD对象
        
        Args:
            model: SQLAlchemy模型类
        """
        self.model = model
    
    # 同步操作
    def get(self, db: Session, id: str) -> Optional[ModelType]:
        """根据ID获取单个对象"""
        return db.query(self.model).filter(
            and_(
                self.model.id == id,
                self.model.is_deleted == False
            )
        ).first()
    
    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """获取多个对象"""
        query = db.query(self.model).filter(self.model.is_deleted == False)
        
        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)
        
        # 应用排序
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(self.model.created_at))
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """创建新对象"""
        obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """更新对象"""
        obj_data = db_obj.to_dict()
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: str) -> Optional[ModelType]:
        """软删除对象"""
        obj = self.get(db, id=id)
        if obj:
            obj.soft_delete()
            db.add(obj)
            db.commit()
        return obj
    
    def hard_delete(self, db: Session, *, id: str) -> Optional[ModelType]:
        """硬删除对象"""
        obj = self.get(db, id=id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
    
    def count(self, db: Session, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计对象数量"""
        query = db.query(func.count(self.model.id)).filter(self.model.is_deleted == False)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.scalar()
    
    # 异步操作
    async def get_async(self, db: AsyncSession, id: str) -> Optional[ModelType]:
        """异步根据ID获取单个对象"""
        stmt = select(self.model).where(
            and_(
                self.model.id == id,
                self.model.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_multi_async(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """异步获取多个对象"""
        stmt = select(self.model).where(self.model.is_deleted == False)
        
        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
        
        # 应用排序
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_desc:
                stmt = stmt.order_by(desc(order_column))
            else:
                stmt = stmt.order_by(asc(order_column))
        else:
            stmt = stmt.order_by(desc(self.model.created_at))
        
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    async def create_async(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """异步创建新对象"""
        obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_async(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """异步更新对象"""
        obj_data = db_obj.to_dict()
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def remove_async(self, db: AsyncSession, *, id: str) -> Optional[ModelType]:
        """异步软删除对象"""
        obj = await self.get_async(db, id=id)
        if obj:
            obj.soft_delete()
            db.add(obj)
            await db.commit()
        return obj
    
    async def hard_delete_async(self, db: AsyncSession, *, id: str) -> Optional[ModelType]:
        """异步硬删除对象"""
        obj = await self.get_async(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
    
    async def count_async(self, db: AsyncSession, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """异步统计对象数量"""
        stmt = select(func.count(self.model.id)).where(self.model.is_deleted == False)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await db.execute(stmt)
        return result.scalar()
    
    # 批量操作
    async def bulk_create_async(self, db: AsyncSession, *, objs_in: List[CreateSchemaType]) -> List[ModelType]:
        """异步批量创建对象"""
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            db_obj = self.model(**obj_in_data)
            db_objs.append(db_obj)
        
        db.add_all(db_objs)
        await db.commit()
        
        for db_obj in db_objs:
            await db.refresh(db_obj)
        
        return db_objs
    
    # 搜索操作
    async def search_async(
        self,
        db: AsyncSession,
        *,
        query: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """异步搜索对象"""
        stmt = select(self.model).where(self.model.is_deleted == False)
        
        # 构建搜索条件
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)
                search_conditions.append(field_attr.ilike(f"%{query}%"))
        
        if search_conditions:
            stmt = stmt.where(or_(*search_conditions))
        
        stmt = stmt.order_by(desc(self.model.created_at)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
