"""
AI互动小说 - 用户CRUD操作
用户相关的数据库操作
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from app.crud.base import CRUDBase
from app.models.user import User
from app.core.security import get_password_hash, verify_password


class CRUDUser(CRUDBase[User, Dict[str, Any], Dict[str, Any]]):
    """用户CRUD操作类"""
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(
            and_(
                User.email == email,
                User.is_deleted == False
            )
        ).first()
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(
            and_(
                User.username == username,
                User.is_deleted == False
            )
        ).first()
    
    async def get_by_email_async(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """异步根据邮箱获取用户"""
        stmt = select(User).where(
            and_(
                User.email == email,
                User.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username_async(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """异步根据用户名获取用户"""
        stmt = select(User).where(
            and_(
                User.username == username,
                User.is_deleted == False
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    def create_user(self, db: Session, *, user_data: Dict[str, Any]) -> User:
        """创建用户"""
        # 加密密码
        if 'password' in user_data:
            hashed_password = get_password_hash(user_data.pop('password'))
            user_data['hashed_password'] = hashed_password
        
        # 设置默认值
        user_data.setdefault('is_active', True)
        user_data.setdefault('is_verified', False)
        user_data.setdefault('is_premium', False)
        
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    async def create_user_async(self, db: AsyncSession, *, user_data: Dict[str, Any]) -> User:
        """异步创建用户"""
        # 加密密码
        if 'password' in user_data:
            hashed_password = get_password_hash(user_data.pop('password'))
            user_data['hashed_password'] = hashed_password
        
        # 设置默认值
        user_data.setdefault('is_active', True)
        user_data.setdefault('is_verified', False)
        user_data.setdefault('is_premium', False)
        
        db_user = User(**user_data)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def authenticate_async(self, db: AsyncSession, *, email: str, password: str) -> Optional[User]:
        """异步用户认证"""
        user = await self.get_by_email_async(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def is_active(self, user: User) -> bool:
        """检查用户是否激活"""
        return user.is_active and not user.is_deleted
    
    def is_verified(self, user: User) -> bool:
        """检查用户邮箱是否验证"""
        return user.is_verified
    
    def is_premium(self, user: User) -> bool:
        """检查用户是否为高级会员"""
        return user.is_premium_active
    
    def update_password(self, db: Session, *, user: User, new_password: str) -> User:
        """更新用户密码"""
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    async def update_password_async(self, db: AsyncSession, *, user: User, new_password: str) -> User:
        """异步更新用户密码"""
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    def verify_email(self, db: Session, *, user: User) -> User:
        """验证用户邮箱"""
        user.verify_email()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    async def verify_email_async(self, db: AsyncSession, *, user: User) -> User:
        """异步验证用户邮箱"""
        user.verify_email()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    def activate_premium(self, db: Session, *, user: User, days: int = 30) -> User:
        """激活高级会员"""
        user.activate_premium(days)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    async def activate_premium_async(self, db: AsyncSession, *, user: User, days: int = 30) -> User:
        """异步激活高级会员"""
        user.activate_premium(days)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    def update_login_time(self, db: Session, *, user: User) -> User:
        """更新最后登录时间"""
        user.update_last_login()
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    async def update_login_time_async(self, db: AsyncSession, *, user: User) -> User:
        """异步更新最后登录时间"""
        user.update_last_login()
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def search_users_async(
        self,
        db: AsyncSession,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """异步搜索用户"""
        return await self.search_async(
            db,
            query=query,
            search_fields=['username', 'nickname', 'email'],
            skip=skip,
            limit=limit
        )
    
    async def get_active_users_async(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """异步获取活跃用户"""
        return await self.get_multi_async(
            db,
            skip=skip,
            limit=limit,
            filters={'is_active': True},
            order_by='last_login_at',
            order_desc=True
        )
    
    async def get_premium_users_async(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """异步获取高级用户"""
        return await self.get_multi_async(
            db,
            skip=skip,
            limit=limit,
            filters={'is_premium': True},
            order_by='premium_expires_at',
            order_desc=True
        )
    
    async def get_user_stats_async(self, db: AsyncSession) -> Dict[str, Any]:
        """异步获取用户统计信息"""
        total_users = await self.count_async(db)
        active_users = await self.count_async(db, filters={'is_active': True})
        verified_users = await self.count_async(db, filters={'is_verified': True})
        premium_users = await self.count_async(db, filters={'is_premium': True})
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'premium_users': premium_users,
            'inactive_users': total_users - active_users,
            'unverified_users': total_users - verified_users,
            'free_users': total_users - premium_users
        }
    
    def check_email_exists(self, db: Session, *, email: str) -> bool:
        """检查邮箱是否已存在"""
        user = self.get_by_email(db, email=email)
        return user is not None
    
    def check_username_exists(self, db: Session, *, username: str) -> bool:
        """检查用户名是否已存在"""
        user = self.get_by_username(db, username=username)
        return user is not None
    
    async def check_email_exists_async(self, db: AsyncSession, *, email: str) -> bool:
        """异步检查邮箱是否已存在"""
        user = await self.get_by_email_async(db, email=email)
        return user is not None
    
    async def check_username_exists_async(self, db: AsyncSession, *, username: str) -> bool:
        """异步检查用户名是否已存在"""
        user = await self.get_by_username_async(db, username=username)
        return user is not None


# 创建用户CRUD实例
user = CRUDUser(User)
