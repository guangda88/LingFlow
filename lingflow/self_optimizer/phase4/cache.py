"""
LingFlow Phase 4: 参数缓存机制

YOLO实现：LRU缓存，快速访问
"""

from collections import OrderedDict
from typing import Dict, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import time
import json

from lingflow.self_optimizer.phase4.data_types import ParameterVersion


def _make_hashable(obj: Union[str, Dict[str, Any]]) -> str:
    """将对象转换为可hash的字符串

    Args:
        obj: 字符串或字典

    Returns:
        可hash的字符串
    """
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        # 按key排序后序列化，确保相同内容产生相同hash
        return json.dumps(obj, sort_keys=True)
    return str(obj)


class ParameterCache:
    """参数缓存 - LRU策略"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """初始化缓存

        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存过期时间（秒）
        """
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)

        # OrderedDict实现LRU
        self._cache: OrderedDict[str, Tuple[ParameterVersion, datetime]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _is_expired(self, timestamp: datetime) -> bool:
        """检查是否过期"""
        return datetime.now() - timestamp > self.ttl

    def get(self, key: Union[str, Dict[str, Any]]) -> Optional[ParameterVersion]:
        """获取缓存"""
        hashable_key = _make_hashable(key)
        if hashable_key not in self._cache:
            self._misses += 1
            return None

        version, timestamp = self._cache[hashable_key]

        # 检查过期
        if self._is_expired(timestamp):
            del self._cache[hashable_key]
            self._misses += 1
            return None

        # LRU：移到末尾
        self._cache.move_to_end(hashable_key)
        self._hits += 1
        return version

    def put(self, key: Union[str, Dict[str, Any]], version: ParameterVersion):
        """放入缓存"""
        hashable_key = _make_hashable(key)
        now = datetime.now()

        # 如果已存在，更新并移到末尾
        if hashable_key in self._cache:
            self._cache[hashable_key] = (version, now)
            self._cache.move_to_end(hashable_key)
            return

        # 检查容量
        if len(self._cache) >= self.max_size:
            # 移除最旧的（第一个）
            self._cache.popitem(last=False)

        # 添加新条目
        self._cache[hashable_key] = (version, now)

    def invalidate(self, key: Union[str, Dict[str, Any]]):
        """使缓存失效"""
        hashable_key = _make_hashable(key)
        if hashable_key in self._cache:
            del self._cache[hashable_key]

    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_keys = [
            k for k, (_, ts) in self._cache.items()
            if self._is_expired(ts)
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl.total_seconds()
        }

    def get_hit_rate(self) -> float:
        """获取命中率"""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0

    def warm_up(self, items: Dict[str, ParameterVersion]):
        """预热缓存"""
        for key, version in items.items():
            self.put(key, version)

    def keys(self) -> list:
        """获取所有缓存键"""
        return list(self._cache.keys())

    def __contains__(self, key: Union[str, Dict[str, Any]]) -> bool:
        """检查键是否存在"""
        return _make_hashable(key) in self._cache

    def __len__(self) -> int:
        """获取缓存大小"""
        return len(self._cache)


class CachedParameterStore:
    """带缓存的参数存储"""

    def __init__(self, store, cache_size: int = 1000, cache_ttl: int = 3600):
        """初始化

        Args:
            store: 底层存储实例
            cache_size: 缓存大小
            cache_ttl: 缓存过期时间（秒）
        """
        self.store = store
        self.cache = ParameterCache(max_size=cache_size, ttl_seconds=cache_ttl)

    def save(self, params: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None,
             project: str = "default", parent: Optional[str] = None) -> ParameterVersion:
        """保存参数"""
        version = self.store.save(params, metadata, project, parent)

        # 更新缓存
        cache_key = f"{project}:{version.version_id}"
        self.cache.put(cache_key, version)

        return version

    def load(self, version_id: str, project: str = "default") -> Optional[ParameterVersion]:
        """加载参数（带缓存）"""
        cache_key = f"{project}:{version_id}"

        # 先查缓存
        version = self.cache.get(cache_key)
        if version:
            return version

        # 缓存未命中，查存储
        version = self.store.load(version_id)
        if version:
            self.cache.put(cache_key, version)

        return version

    def find_by_params(self, params: Dict[str, Any]) -> Optional[ParameterVersion]:
        """根据参数查找"""
        return self.store.find_by_params(params)

    def get_latest(self, project: str = "default") -> Optional[ParameterVersion]:
        """获取最新版本"""
        return self.store.get_latest(project)

    def invalidate(self, version_id: str, project: str = "default"):
        """使缓存失效"""
        cache_key = f"{project}:{version_id}"
        self.cache.invalidate(cache_key)

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return self.cache.get_stats()

    def cleanup_cache(self) -> int:
        """清理过期缓存"""
        return self.cache.cleanup_expired()


# 默认缓存实例
_default_cache: Optional[ParameterCache] = None


def get_default_cache() -> ParameterCache:
    """获取默认缓存实例"""
    global _default_cache
    if _default_cache is None:
        _default_cache = ParameterCache()
    return _default_cache
