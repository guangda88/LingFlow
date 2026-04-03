"""情报系统日志配置

统一的日志配置，替换print语句。
"""

import logging
import sys
from pathlib import Path

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SIMPLE_FORMAT = "%(levelname)s: %(message)s"

# 日志级别
LOG_LEVEL = logging.INFO


def get_logger(name: str) -> logging.Logger:
    """获取logger实例

    Args:
        name: logger名称，通常使用__name__

    Returns:
        Logger实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(SIMPLE_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)

    return logger


def setup_file_logging(log_dir: Path, level: int = LOG_LEVEL) -> None:
    """设置文件日志

    Args:
        log_dir: 日志目录
        level: 日志级别
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "intelligence.log"

    # 配置根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 文件handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    file_handler.setLevel(level)

    root_logger.addHandler(file_handler)

    return log_file
