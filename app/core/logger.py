import os
from pathlib import Path
from loguru import logger
from typing import Optional


class Logger:
    """日志管理器，基于loguru实现"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志文件保存目录，默认为"logs"
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self._loggers = {}
    
    def get_logger(self, name: str, level: str = "DEBUG", 
                   rotation: str = "1 day", retention: str = "30 days",
                   format_str: Optional[str] = None) -> logger:
        """
        获取指定名称的日志器
        
        Args:
            name: 日志器名称，也是日志文件名（不含扩展名）
            level: 日志级别，默认INFO
            rotation: 日志轮转规则，默认每天轮转
            retention: 日志保留时间，默认30天
            format_str: 自定义日志格式
            
        Returns:
            配置好的loguru logger实例
        """
        if name in self._loggers:
            return self._loggers[name]
        
        # 创建新的logger实例
        new_logger = logger.bind(name=name)
        
        # 移除默认的控制台输出（可选）
        new_logger.remove()
        
        # 添加控制台输出
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
        new_logger.add(
            sink=lambda msg: print(msg, end=""),
            format=console_format,
            level=level,
            colorize=True
        )
        
        # 设置日志文件格式
        if format_str is None:
            format_str = (
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} - {message}"
            )
        
        # 添加文件输出
        log_file = self.log_dir / f"{name}.log"
        new_logger.add(
            sink=str(log_file),
            format=format_str,
            level=level,
            rotation=rotation,
            retention=retention,
            encoding="utf-8",
            enqueue=True  # 异步写入，提高性能
        )
        
        self._loggers[name] = new_logger
        return new_logger
    
    def get_default_logger(self) -> logger:
        """
        获取默认日志器
        
        Returns:
            默认的logger实例
        """
        return self.get_logger("default")
    
    def remove_logger(self, name: str):
        """
        移除指定名称的日志器
        
        Args:
            name: 日志器名称
        """
        if name in self._loggers:
            self._loggers[name].remove()
            del self._loggers[name]
    
    def list_loggers(self) -> list:
        """
        列出所有已创建的日志器名称
        
        Returns:
            日志器名称列表
        """
        return list(self._loggers.keys())


# 全局日志管理器实例
log_manager = Logger()

# 便捷函数
def get_logger(name: str, **kwargs) -> logger:
    """
    便捷函数：获取指定名称的日志器
    
    Args:
        name: 日志器名称
        **kwargs: 其他参数传递给Logger.get_logger
        
    Returns:
        配置好的logger实例
    """
    return log_manager.get_logger(name, **kwargs)


def get_default_logger() -> logger:
    """
    便捷函数：获取默认日志器
    
    Returns:
        默认的logger实例
    """
    return log_manager.get_default_logger()


# 导出主要接口
__all__ = ["Logger", "log_manager", "get_logger", "get_default_logger"]