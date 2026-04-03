"""LingFlow 情报系统 - 采集器模块

扩展情报收集能力，增加对LingFlow自身的监控和评价收集。
"""

from .lingflow_monitor import LingFlowMonitor, MentionData
from .star_tracker import StarTracker, StargazerData
from .base import (
    BaseCollector,
    CollectorManager,
    CollectorConfig,
)
from .reddit import RedditCollector
from .hackernews import HNCollector

__all__ = [
    # 原有采集器
    "LingFlowMonitor",
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
