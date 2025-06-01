from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.auth import get_password_hash, verify_password
from typing import Optional

class UserService:
    async def create_user(self, db: Session, user_data: UserCreate) -> User:
        """创建新用户"""
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    async def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    async def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    async def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()
    
    async def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """验证用户登录"""
        user = await self.get_user_by_username(db, username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def update_user(self, db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """更新用户信息"""
        user = await self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        
        # 如果更新密码，需要加密
        if 'password' in update_data:
            update_data['hashed_password'] = get_password_hash(update_data.pop('password'))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    async def delete_user(self, db: Session, user_id: int) -> bool:
        """删除用户"""
        user = await self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        
        return True
    
    async def check_username_exists(self, db: Session, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """检查用户名是否已存在"""
        query = db.query(User).filter(User.username == username)
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is not None
    
    async def check_email_exists(self, db: Session, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """检查邮箱是否已存在"""
        query = db.query(User).filter(User.email == email)
        
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        
        return query.first() is not None