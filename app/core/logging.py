"""
AI互动小说 - 日志配置模块
统一的日志管理和配置
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    # ANSI颜色代码
    COLORS = {
        "DEBUG": "\033[36m",  # 青色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[35m",  # 紫色
        "RESET": "\033[0m",  # 重置
    }

    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"

        return super().format(record)


class RequestFormatter(logging.Formatter):
    """请求日志格式化器"""

    def format(self, record):
        # 添加请求相关信息
        if hasattr(record, "request_id"):
            record.msg = f"[{record.request_id}] {record.msg}"

        if hasattr(record, "user_id"):
            record.msg = f"[User:{record.user_id}] {record.msg}"

        return super().format(record)


def setup_logging():
    """设置日志配置"""

    # 创建日志目录
    if settings.LOG_FILE:
        log_path = Path(settings.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # 基础配置
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": settings.LOG_FORMAT, "datefmt": "%Y-%m-%d %H:%M:%S"},
            "colored": {
                "()": ColoredFormatter,
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "request": {
                "()": RequestFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL.value,
                "formatter": "colored" if settings.is_development else "default",
                "stream": sys.stdout,
            }
        },
        "loggers": {
            # 应用日志
            "app": {
                "level": settings.LOG_LEVEL.value,
                "handlers": ["console"],
                "propagate": False,
            },
            # FastAPI日志
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            # SQLAlchemy日志
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
            # HTTP客户端日志
            "httpx": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        },
        "root": {"level": settings.LOG_LEVEL.value, "handlers": ["console"]},
    }

    # 添加文件处理器
    if settings.LOG_FILE:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.LOG_LEVEL.value,
            "formatter": "default",
            "filename": settings.LOG_FILE,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        }

        # 为所有logger添加文件处理器
        for logger_name in config["loggers"]:
            config["loggers"][logger_name]["handlers"].append("file")
        config["root"]["handlers"].append("file")

    # 生产环境特殊配置
    if settings.is_production:
        # 生产环境使用JSON格式
        config["handlers"]["console"]["formatter"] = "json"
        if settings.LOG_FILE:
            config["handlers"]["file"]["formatter"] = "json"

        # 降低第三方库日志级别
        config["loggers"]["uvicorn"]["level"] = "WARNING"
        config["loggers"]["sqlalchemy.engine"]["level"] = "ERROR"

    # 应用配置
    logging.config.dictConfig(config)

    # 设置根日志记录器
    logger = logging.getLogger()
    logger.info(f"日志系统初始化完成 - 级别: {settings.LOG_LEVEL.value}")


class LoggerManager:
    """日志管理器"""

    def __init__(self):
        self.loggers = {}

    def get_logger(self, name: str) -> logging.Logger:
        """获取日志记录器"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(f"app.{name}")
        return self.loggers[name]

    def log_request(self, request_id: str, method: str, url: str, user_id: str = None):
        """记录请求日志"""
        logger = self.get_logger("request")
        extra = {"request_id": request_id}
        if user_id:
            extra["user_id"] = user_id

        logger.info(f"{method} {url}", extra=extra)

    def log_response(self, request_id: str, status_code: int, duration_ms: float):
        """记录响应日志"""
        logger = self.get_logger("response")
        logger.info(
            f"Response {status_code} - {duration_ms:.2f}ms",
            extra={"request_id": request_id},
        )

    def log_error(self, request_id: str, error: Exception, context: dict = None):
        """记录错误日志"""
        logger = self.get_logger("error")
        extra = {"request_id": request_id}

        error_msg = f"Error: {type(error).__name__}: {str(error)}"
        if context:
            error_msg += f" - Context: {context}"

        logger.error(error_msg, extra=extra, exc_info=True)

    def log_ai_request(self, model: str, tokens: int, duration_ms: float):
        """记录AI请求日志"""
        logger = self.get_logger("ai")
        logger.info(
            f"AI Request - Model: {model}, Tokens: {tokens}, Duration: {duration_ms:.2f}ms"
        )

    def log_database_query(
        self, query_type: str, duration_ms: float, affected_rows: int = None
    ):
        """记录数据库查询日志"""
        logger = self.get_logger("database")
        msg = f"DB Query - Type: {query_type}, Duration: {duration_ms:.2f}ms"
        if affected_rows is not None:
            msg += f", Rows: {affected_rows}"
        logger.debug(msg)


# 全局日志管理器
logger_manager = LoggerManager()


# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return logger_manager.get_logger(name)


# 性能监控装饰器
def log_performance(operation: str):
    """性能监控装饰器"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger = get_logger("performance")

            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.info(f"{operation} completed in {duration:.2f}ms")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(f"{operation} failed after {duration:.2f}ms: {e}")
                raise

        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger = get_logger("performance")

            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.info(f"{operation} completed in {duration:.2f}ms")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(f"{operation} failed after {duration:.2f}ms: {e}")
                raise

        # 检查是否为异步函数
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 日志过滤器
class SensitiveDataFilter(logging.Filter):
    """敏感数据过滤器"""

    SENSITIVE_FIELDS = ["password", "token", "api_key", "secret"]

    def filter(self, record):
        # 过滤敏感信息
        if hasattr(record, "msg"):
            msg = str(record.msg)
            for field in self.SENSITIVE_FIELDS:
                if field in msg.lower():
                    # 简单的敏感信息遮蔽
                    import re

                    pattern = rf'({field}["\']?\s*[:=]\s*["\']?)([^"\'\s,}}]+)'
                    msg = re.sub(pattern, r"\1***", msg, flags=re.IGNORECASE)
            record.msg = msg

        return True


# 添加敏感数据过滤器到所有处理器
def add_sensitive_filter():
    """添加敏感数据过滤器"""
    filter_instance = SensitiveDataFilter()

    # 获取所有处理器并添加过滤器
    for handler in logging.getLogger().handlers:
        handler.addFilter(filter_instance)


# 日志健康检查
def log_health_check() -> dict:
    """日志系统健康检查"""
    try:
        # 测试日志记录
        test_logger = get_logger("health_check")
        test_logger.info("日志系统健康检查")

        # 检查日志文件
        file_status = "ok"
        if settings.LOG_FILE:
            log_path = Path(settings.LOG_FILE)
            if not log_path.exists():
                file_status = "file_not_found"
            elif not log_path.is_file():
                file_status = "not_a_file"

        return {
            "status": "healthy",
            "log_level": settings.LOG_LEVEL.value,
            "log_file": settings.LOG_FILE,
            "file_status": file_status,
            "handlers_count": len(logging.getLogger().handlers),
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


# 初始化函数
def init_logging():
    """初始化日志系统"""
    try:
        setup_logging()
        add_sensitive_filter()

        logger = get_logger("init")
        logger.info("日志系统初始化完成")
        logger.info(f"日志级别: {settings.LOG_LEVEL.value}")
        logger.info(f"日志文件: {settings.LOG_FILE or '仅控制台输出'}")

    except Exception as e:
        print(f"日志系统初始化失败: {e}")
        raise
