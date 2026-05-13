"""lingflow 日志模块"""

import logging
import os
from datetime import datetime

# 日志配置
LOG_LEVEL = os.environ.get("LINGFLOW_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 创建日志目录
log_dir = os.environ.get("LINGFLOW_LOG_DIR", os.path.join(os.path.expanduser("~"), ".lingflow", "logs"))
os.makedirs(log_dir, exist_ok=True)

# 创建日志文件
log_file = os.path.join(log_dir, f'lingflow_{datetime.now().strftime("%Y%m%d")}.log')

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
)


# 创建日志器
def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)


# 日志装饰器
def log_function(func):
    """日志装饰器

    记录函数的执行开始、成功和失败状态。

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数，带有日志记录功能
    """
    logger = get_logger(func.__module__)

    def wrapper(*args, **kwargs):
        logger.info(f"开始执行函数: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"函数执行成功: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"函数执行失败: {func.__name__}, 错误: {str(e)}")
            raise

    return wrapper
