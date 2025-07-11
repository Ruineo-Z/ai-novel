"""
AI互动小说 FastAPI 应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导入配置模块
from app.core.config import settings, get_cors_config, validate_ai_services, validate_database_connection
from app.core.logging import init_logging, get_logger
from app.core.database import init_database, cleanup_database
from app.core.security import init_security

# 初始化日志系统
init_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("🚀 AI互动小说API启动中...")

    try:
        # 初始化安全模块
        init_security()
        logger.info("✅ 安全模块初始化完成")

        # 验证配置
        if not validate_ai_services():
            logger.warning("⚠️ AI服务配置验证失败，请检查API密钥")
        else:
            logger.info("✅ AI服务配置验证通过")

        if not validate_database_connection():
            logger.warning("⚠️ 数据库连接配置验证失败")
        else:
            logger.info("✅ 数据库配置验证通过")

        # 初始化数据库
        await init_database()
        logger.info("✅ 数据库初始化完成")

        logger.info(f"📚 文档地址: http://localhost:{settings.PORT}/docs")
        logger.info(f"🔍 ReDoc地址: http://localhost:{settings.PORT}/redoc")
        logger.info("🎉 AI互动小说API启动完成")

    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        raise

    yield  # 应用运行期间

    # 关闭时的清理
    logger.info("🛑 AI互动小说API正在关闭...")
    try:
        await cleanup_database()
        logger.info("✅ 数据库连接清理完成")
    except Exception as e:
        logger.error(f"❌ 清理过程出错: {e}")

    logger.info("👋 AI互动小说API已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="基于Python FastAPI + LlamaIndex的AI互动小说后端服务",
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS中间件
cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# 根路径
@app.get("/")
async def root():
    """根路径 - 返回API基本信息"""
    return {
        "message": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT.value,
        "docs": "/docs" if settings.is_development else None,
        "redoc": "/redoc" if settings.is_development else None
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查端点"""
    from app.core.database import health_check as db_health_check
    from app.core.logging import log_health_check

    # 获取各模块健康状态
    db_status = await db_health_check()
    log_status = log_health_check()

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "service": "ai-novel-api",
        "environment": settings.ENVIRONMENT.value,
        "components": {
            "database": db_status,
            "logging": log_status,
            "ai_services": {
                "status": "configured" if validate_ai_services() else "not_configured"
            }
        }
    }


def main():
    """主函数 - 用于命令行启动"""
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD and settings.is_development,
        log_level=settings.LOG_LEVEL.value.lower()
    )


if __name__ == "__main__":
    main()
