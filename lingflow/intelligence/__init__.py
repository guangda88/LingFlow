"""LingFlow 情报系统

智能采集、分析、报告LingFlow相关的网络情报。
"""

__version__ = "2.0.0"
__author__ = "LingFlow Team"

from .collectors.base import BaseCollector, CollectorManager
from .collectors.hackernews import HNCollector
from .collectors.reddit import RedditCollector
from .constants import (
    APILimits,
    AuthorTiers,
    DataRetention,
    InfluenceThresholds,
    PlatformWeights,
    RecencyDecay,
    ReportLimits,
    ScoreWeights,
    SentimentThresholds,
)
from .logging_config import get_logger
from .models.common import (
    DailyReport,
    InfluenceScore,
    MentionData,
    Platform,
    ReputationMetrics,
    SentimentLabel,
    SentimentResult,
    SourceType,
    TrendDirection,
    TrendMetrics,
)

__all__ = [
    # 版本
    "__version__",
    # 日志
    "get_logger",
    # 采集器
    "BaseCollector",
    "CollectorManager",
    "RedditCollector",
    "HNCollector",
    # 模型
    "MentionData",
    "Platform",
    "SourceType",
    "SentimentLabel",
    "TrendDirection",
    "SentimentResult",
    "InfluenceScore",
    "TrendMetrics",
    "ReputationMetrics",
    "DailyReport",
    # 常量
    "PlatformWeights",
    "APILimits",
    "InfluenceThresholds",
    "SentimentThresholds",
    "DataRetention",
    "ReportLimits",
    "ScoreWeights",
    "AuthorTiers",
    "RecencyDecay",
]


def create_collector_manager(
    enable_github: bool = True,
    enable_reddit: bool = True,
    enable_hn: bool = True,
    data_dir: str = ".lingflow/intelligence/raw",
) -> CollectorManager:
    """创建采集器管理器

    Args:
        enable_github: 启用GitHub采集
        enable_reddit: 启用Reddit采集
        enable_hn: 启用HN采集
        data_dir: 数据目录

    Returns:
        CollectorManager实例
    """
    from pathlib import Path

    from .collectors.base import CollectorConfig

    manager = CollectorManager(data_dir=Path(data_dir))
    config = CollectorConfig(data_dir=Path(data_dir))

    if enable_reddit:
        manager.register("reddit", RedditCollector(config))

    if enable_hn:
        manager.register("hackernews", HNCollector(config))

    # GitHub采集器需要单独导入
    # 目前暂不集成，因为LingFlowMonitor不是BaseCollector子类
    # if enable_github:
    #     from .collectors.lingflow_monitor import LingFlowMonitor

    return manager
