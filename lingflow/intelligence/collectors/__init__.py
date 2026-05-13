"""lingflow 情报系统 - 采集器模块

扩展情报收集能力，增加对lingflow自身的监控和评价收集。
"""

from .base import (
    BaseCollector,
    CollectorConfig,
    CollectorManager,
)
from .hackernews import HNCollector
from .lingflow_monitor import lingflowMonitor, MentionData
from .reddit import RedditCollector
from .star_tracker import StargazerData, StarTracker

__all__ = [
    # 原有采集器
    "lingflowMonitor",
    "MentionData",
    "StarTracker",
    "StargazerData",
    # 新增基类
    "BaseCollector",
    "CollectorManager",
    "CollectorConfig",
    # 新增采集器
    "RedditCollector",
    "HNCollector",
]
