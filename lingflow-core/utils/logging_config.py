"""
LingFlow Logging Configuration - 日志配置

统一的日志配置和记录
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    设置日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件名
        log_dir: 日志目录

    Returns:
        配置好的 logger
    """
    # 创建根 logger
    logger = logging.getLogger("lingflow")
    logger.setLevel(getattr(logging, level.upper()))

    # 清除现有处理器
    logger.handlers = []

    # 创建格式化器
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # 文件处理器（如果指定）
    if log_dir or log_file:
        if log_dir:
            log_path = Path(log_dir) / "lingflow.log"
        else:
            log_path = Path(log_file) if log_file else Path("lingflow.log")

        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


class LingFlowLogger:
    """LingFlow 专用日志记录器"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(f"lingflow.{name}")
        self.name = name

    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        """记录错误日志"""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        self.logger.critical(message, extra=kwargs)

    # 专用日志方法
    def log_token_estimation(self, tokens: int, content_preview: str):
        """记录 Token 估算"""
        self.info(f"Token estimation: {tokens} tokens", preview=content_preview[:50])

    def log_compression(self, before: int, after: int, strategy: str):
        """记录压缩操作"""
        ratio = (before - after) / before * 100 if before > 0 else 0
        self.info(
            f"Compression: {before} -> {after} tokens ({ratio:.1f}% reduction)",
            strategy=strategy
        )

    def log_performance(self, operation: str, duration_ms: float):
        """记录性能"""
        if duration_ms > 100:
            self.warning(f"Slow {operation}: {duration_ms:.2f}ms")
        else:
            self.debug(f"{operation}: {duration_ms:.2f}ms")

    def log_api_call(self, method: str, params: dict):
        """记录 API 调用"""
        self.debug(f"API call: {method}", params=params)

    def log_error_with_context(self, error: Exception, context: dict):
        """记录带上下文的错误"""
        self.error(f"Error: {str(error)}", type=type(error).__name__, context=context)


def get_logger(name: str) -> LingFlowLogger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器实例
    """
    return LingFlowLogger(name)


# 初始化默认日志
setup_logging()
