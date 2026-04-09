"""情报采集器基类

定义采集器接口和通用功能。
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger
from ..models.common import MentionData, Platform

logger = get_logger(__name__)


@dataclass
class CollectorConfig:
    """采集器配置"""

    enabled: bool = True
    rate_limit: int = 100  # 每分钟请求数
    cache_ttl: int = 3600  # 缓存时间(秒)
    max_results: int = 1000  # 最大结果数
    data_dir: Path = Path(".lingflow/intelligence/raw")


class BaseCollector(ABC):
    """采集器基类

    所有采集器必须继承此类并实现collect方法。
    """

    # 平台标识
    PLATFORM: Platform = Platform.GITHUB  # 默认值，子类应覆盖

    # 采集器名称
    NAME: str = "base"

    # 描述
    DESCRIPTION: str = ""

    def __init__(self, config: Optional[CollectorConfig] = None):
        """初始化采集器

        Args:
            config: 采集器配置
        """
        self.config = config or CollectorConfig()
        self.data_dir = self.config.data_dir / self.PLATFORM.value
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 缓存目录
        self.cache_dir = self.data_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True)

    @abstractmethod
    def collect(self, **kwargs) -> List[MentionData]:
        """采集数据

        Args:
            **kwargs: 采集参数

        Returns:
            MentionData列表
        """
        pass

    def save_data(self, mentions: List[MentionData]) -> Path:
        """保存采集的数据

        Args:
            mentions: 提及数据列表

        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.NAME}_{timestamp}.json"
        filepath = self.data_dir / filename

        data = {
            "collector": self.NAME,
            "platform": self.PLATFORM.value,
            "timestamp": datetime.now().isoformat(),
            "count": len(mentions),
            "mentions": [m.to_dict() for m in mentions],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def load_data(self, filepath: Path) -> List[MentionData]:
        """加载保存的数据

        Args:
            filepath: 数据文件路径

        Returns:
            MentionData列表
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [MentionData.from_dict(m) for m in data.get("mentions", [])]

    def get_recent_files(self, days: int = 7) -> List[Path]:
        """获取最近的数据文件

        Args:
            days: 最近N天

        Returns:
            文件路径列表
        """
        cutoff = datetime.now() - timedelta(days=days)
        files = []

        for filepath in self.data_dir.glob(f"{self.NAME}_*.json"):
            if filepath.is_file():
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                if mtime > cutoff:
                    files.append(filepath)

        return sorted(files, reverse=True)

    def get_cache_key(self, **kwargs) -> str:
        """生成缓存键

        Args:
            **kwargs: 参数

        Returns:
            缓存键
        """
        parts = [self.NAME]
        for key in sorted(kwargs.keys()):
            parts.append(f"{key}={kwargs[key]}")
        return "_".join(parts)

    def load_cache(self, cache_key: str) -> Optional[List[MentionData]]:
        """加载缓存

        Args:
            cache_key: 缓存键

        Returns:
            缓存的数据，如果不存在或过期则返回None
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        # 检查缓存是否过期
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = (datetime.now() - mtime).total_seconds()
        if age > self.config.cache_ttl:
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [MentionData.from_dict(m) for m in data.get("mentions", [])]
        except Exception:
            return None

    def save_cache(self, cache_key: str, mentions: List[MentionData]):
        """保存缓存

        Args:
            cache_key: 缓存键
            mentions: 数据
        """
        cache_file = self.cache_dir / f"{cache_key}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "mentions": [m.to_dict() for m in mentions],
        }

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def clean_old_cache(self, days: int = 7):
        """清理旧缓存

        Args:
            days: 保留最近N天的缓存
        """
        cutoff = datetime.now() - timedelta(days=days)

        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file.is_file():
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mtime < cutoff:
                    cache_file.unlink()

    def generate_summary(self, mentions: List[MentionData]) -> Dict[str, Any]:
        """生成汇总统计

        Args:
            mentions: 提及数据列表

        Returns:
            汇总统计字典
        """
        if not mentions:
            return {
                "total": 0,
                "platform": self.PLATFORM.value,
            }

        # 按类型统计
        by_type: Dict[str, int] = {}
        for m in mentions:
            source_type = m.source_type.value if hasattr(m.source_type, "value") else str(m.source_type)
            by_type[source_type] = by_type.get(source_type, 0) + 1

        # 按作者统计
        authors: Dict[str, int] = {}
        for m in mentions:
            authors[m.author] = authors.get(m.author, 0) + 1

        # 按状态统计
        by_state: Dict[str, int] = {}
        for m in mentions:
            if m.state:
                by_state[m.state] = by_state.get(m.state, 0) + 1

        return {
            "total": len(mentions),
            "platform": self.PLATFORM.value,
            "by_type": by_type,
            "by_state": by_state,
            "unique_authors": len(authors),
            "top_authors": sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5],
            "total_comments": sum(m.comments for m in mentions),
            "date_range": {
                "earliest": min(m.published_at for m in mentions),
                "latest": max(m.published_at for m in mentions),
            },
        }


class CollectorManager:
    """采集器管理器

    管理多个采集器，统一调度。
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """初始化管理器

        Args:
            data_dir: 数据目录
        """
        self.data_dir = data_dir or Path(".lingflow/intelligence")
        self.collectors: Dict[str, BaseCollector] = {}

    def register(self, name: str, collector: BaseCollector):
        """注册采集器

        Args:
            name: 采集器名称
            collector: 采集器实例
        """
        self.collectors[name] = collector

    def get(self, name: str) -> Optional[BaseCollector]:
        """获取采集器

        Args:
            name: 采集器名称

        Returns:
            采集器实例，不存在则返回None
        """
        return self.collectors.get(name)

    def list_collectors(self) -> List[str]:
        """列出所有采集器

        Returns:
            采集器名称列表
        """
        return list(self.collectors.keys())

    def collect_all(self, **kwargs) -> Dict[str, List[MentionData]]:
        """运行所有采集器

        Args:
            **kwargs: 传递给各采集器的参数

        Returns:
            各采集器的结果
        """
        results = {}

        for name, collector in self.collectors.items():
            if collector.config.enabled:
                try:
                    results[name] = collector.collect(**kwargs)
                except Exception as e:
                    logger.error(f"{name} 采集失败: {e}")
                    results[name] = []

        return results

    def get_summary(self) -> Dict[str, Any]:
        """获取所有采集器的汇总

        Returns:
            汇总信息
        """
        summary = {
            "total_collectors": len(self.collectors),
            "enabled_collectors": sum(1 for c in self.collectors.values() if c.config.enabled),
            "collectors": {},
        }

        for name, collector in self.collectors.items():
            summary["collectors"][name] = {
                "platform": collector.PLATFORM.value,
                "enabled": collector.config.enabled,
                "data_dir": str(collector.data_dir),
            }

        return summary
