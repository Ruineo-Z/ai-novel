"""
AI互动小说 - 数据库配置模块
SQLAlchemy配置和会话管理
"""
import logging
from typing import AsyncGenerator, Optional
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# 数据库元数据
metadata = MetaData()

# 声明式基类
Base = declarative_base(metadata=metadata)

# 数据库引擎
engine: Optional[object] = None
async_engine: Optional[object] = None

# 会话工厂
SessionLocal: Optional[sessionmaker] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None


def create_database_engines():
    """创建数据库引擎"""
    global engine, async_engine, SessionLocal, AsyncSessionLocal
    
    try:
        # 同步引擎配置
        sync_engine_kwargs = {
            "echo": settings.DATABASE_ECHO,
            "pool_pre_ping": True,
        }
        
        # 异步引擎配置
        async_engine_kwargs = {
            "echo": settings.DATABASE_ECHO,
            "pool_pre_ping": True,
        }
        
        # SQLite特殊配置
        if settings.database_url_sync.startswith("sqlite"):
            sync_engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False}
            })
            async_engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False}
            })
        else:
            # PostgreSQL配置
            sync_engine_kwargs.update({
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            })
            async_engine_kwargs.update({
                "pool_size": settings.DATABASE_POOL_SIZE,
                "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            })
        
        # 创建引擎
        engine = create_engine(settings.database_url_sync, **sync_engine_kwargs)
        async_engine = create_async_engine(settings.database_url_async, **async_engine_kwargs)
        
        # 创建会话工厂
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        AsyncSessionLocal = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info(f"数据库引擎创建成功: {settings.database_url_sync}")
        
    except Exception as e:
        logger.error(f"数据库引擎创建失败: {e}")
        raise


def get_db() -> Session:
    """获取同步数据库会话 - 用于依赖注入"""
    if SessionLocal is None:
        create_database_engines()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话 - 用于依赖注入"""
    if AsyncSessionLocal is None:
        create_database_engines()
    
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """创建数据库表"""
    if async_engine is None:
        create_database_engines()
    
    try:
        async with async_engine.begin() as conn:
            # 导入所有模型以确保表被创建
            from app.models import (  # noqa
                User, Story, Chapter, Choice,
                UserStoryProgress, StoryMemory
            )

            await conn.run_sync(Base.metadata.create_all)
            logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        raise


async def drop_tables():
    """删除数据库表 - 仅用于测试"""
    if async_engine is None:
        create_database_engines()
    
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("数据库表删除成功")
    except Exception as e:
        logger.error(f"数据库表删除失败: {e}")
        raise


async def check_database_connection() -> bool:
    """检查数据库连接"""
    if async_engine is None:
        create_database_engines()
    
    try:
        async with async_engine.begin() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        logger.info("数据库连接检查成功")
        return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.session_local = None
        self.async_session_local = None
    
    async def initialize(self):
        """初始化数据库"""
        create_database_engines()
        await self.check_connection()
        await create_tables()
    
    async def check_connection(self) -> bool:
        """检查数据库连接"""
        return await check_database_connection()
    
    async def close(self):
        """关闭数据库连接"""
        global engine, async_engine
        
        if async_engine:
            await async_engine.dispose()
            logger.info("异步数据库引擎已关闭")
        
        if engine:
            engine.dispose()
            logger.info("同步数据库引擎已关闭")
    
    async def reset_database(self):
        """重置数据库 - 仅用于测试"""
        if not settings.is_testing:
            raise RuntimeError("重置数据库仅允许在测试环境中执行")
        
        await drop_tables()
        await create_tables()
        logger.info("数据库重置完成")


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 数据库健康检查
async def health_check() -> dict:
    """数据库健康检查"""
    try:
        connection_ok = await check_database_connection()
        
        # 获取数据库信息
        db_info = {
            "status": "healthy" if connection_ok else "unhealthy",
            "database_type": "sqlite" if "sqlite" in settings.database_url_sync else "postgresql",
            "connection_url": settings.database_url_sync.split("@")[-1] if "@" in settings.database_url_sync else "local",
            "pool_size": settings.DATABASE_POOL_SIZE,
            "echo_enabled": settings.DATABASE_ECHO
        }
        
        if connection_ok:
            # 尝试获取更多数据库统计信息
            try:
                async with AsyncSessionLocal() as session:
                    # 这里可以添加更多的健康检查查询
                    pass
            except Exception as e:
                logger.warning(f"数据库统计信息获取失败: {e}")
        
        return db_info
        
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# 数据库事务装饰器
def db_transaction(func):
    """数据库事务装饰器 - 用于同步函数"""
    def wrapper(*args, **kwargs):
        db = SessionLocal()
        try:
            result = func(db, *args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"数据库事务失败: {e}")
            raise
        finally:
            db.close()
    return wrapper


def async_db_transaction(func):
    """异步数据库事务装饰器"""
    async def wrapper(*args, **kwargs):
        async with AsyncSessionLocal() as session:
            try:
                result = await func(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                logger.error(f"异步数据库事务失败: {e}")
                raise
    return wrapper


# 初始化函数
async def init_database():
    """初始化数据库 - 应用启动时调用"""
    try:
        await db_manager.initialize()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


# 清理函数
async def cleanup_database():
    """清理数据库连接 - 应用关闭时调用"""
    try:
        await db_manager.close()
        logger.info("数据库连接清理完成")
    except Exception as e:
        logger.error(f"数据库连接清理失败: {e}")
        raise
