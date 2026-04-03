"""
工作流缓存模块

提供工作流定义的缓存机制，减少重复的文件 I/O 操作。

Features:
- TTL-based 过期
- 文件变更检测
- 内存使用限制
- 线程安全
"""

import hashlib
import logging
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class CachedWorkflow:
    """缓存的工作流数据"""

    definition: Dict[str, Any]
    file_path: str
    mtime: float  # 文件修改时间
    cached_at: float  # 缓存时间
    checksum: str  # 内容校验和
    access_count: int = 0  # 访问计数


@dataclass
class CacheConfig:
    """缓存配置"""

    ttl_seconds: int = 300  # 5 分钟
    max_size: int = 100  # 最多缓存 100 个工作流
    enable_file_watching: bool = True  # 是否检测文件变更
    checksum_enabled: bool = True  # 是否计算内容校验和


class WorkflowCache:
    """工作流缓存

    缓存工作流定义以减少重复的文件读取和 YAML 解析开销。
    """

    def __init__(self, config: CacheConfig = None):
        self._config = config or CacheConfig()
        self._cache: Dict[str, CachedWorkflow] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0

        # 启动清理线程
        self._start_cleanup_thread()

    def _calculate_checksum(self, file_path: str) -> str:
        """计算文件校验和

        Args:
            file_path: 文件路径

        Returns:
            SHA256 校验和
        """
        if not self._config.checksum_enabled:
            return ""

        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"计算校验和失败 {file_path}: {e}")
            return ""

    def _is_valid(self, cached: CachedWorkflow) -> bool:
        """检查缓存是否有效

        Args:
            cached: 缓存的工作流

        Returns:
            True 如果缓存有效，False 如果需要重新加载
        """
        # 检查 TTL
        if time.time() - cached.cached_at > self._config.ttl_seconds:
            return False

        # 检查文件是否被修改
        if self._config.enable_file_watching:
            try:
                current_mtime = os.path.getmtime(cached.file_path)
                if current_mtime != cached.mtime:
                    logger.debug(f"文件已修改: {cached.file_path}")
                    return False

                # 可选：检查内容校验和
                if self._config.checksum_enabled:
                    current_checksum = self._calculate_checksum(cached.file_path)
                    if current_checksum != cached.checksum:
                        logger.debug(f"内容已变更: {cached.file_path}")
                        return False
            except FileNotFoundError:
                logger.warning(f"文件不存在: {cached.file_path}")
                return False
            except Exception as e:
                logger.warning(f"检查文件状态失败: {e}")
                # 即使检查失败，也认为缓存有效（降级处理）

        return True

    def _cleanup_expired(self):
        """清理过期的缓存条目"""
        now = time.time()
        expired_keys = []

        with self._lock:
            for key, cached in self._cache.items():
                if now - cached.cached_at > self._config.ttl_seconds:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                logger.debug(f"清理过期缓存: {key}")

    def _enforce_size_limit(self):
        """强制执行缓存大小限制（LRU）"""
        if len(self._cache) <= self._config.max_size:
            return

        # 按访问时间和缓存时间排序（最少使用的优先删除）
        items = sorted(self._cache.items(), key=lambda x: (x[1].access_count, x[1].cached_at))

        # 删除最旧的条目
        to_remove = len(self._cache) - self._config.max_size
        for key, _ in items[:to_remove]:
            del self._cache[key]
            logger.debug(f"删除最少使用的缓存: {key}")

    def _start_cleanup_thread(self):
        """启动定期清理线程"""

        def cleanup_worker():
            while True:
                time.sleep(60)  # 每分钟清理一次
                try:
                    self._cleanup_expired()
                except Exception as e:
                    logger.error(f"清理线程出错: {e}")

        thread = threading.Thread(target=cleanup_worker, daemon=True)
        thread.start()
        logger.debug("工作流缓存清理线程已启动")

    def get(self, workflow_path: str) -> Optional[Dict[str, Any]]:
        """获取缓存的工作流定义

        Args:
            workflow_path: 工作流文件路径

        Returns:
            工作流定义字典，如果缓存未命中则返回 None
        """
        abs_path = os.path.abspath(workflow_path)

        with self._lock:
            if abs_path in self._cache:
                cached = self._cache[abs_path]

                if self._is_valid(cached):
                    # 缓存命中
                    cached.access_count += 1
                    self._hits += 1
                    logger.debug(f"缓存命中: {abs_path}")
                    return cached.definition
                else:
                    # 缓存失效，删除
                    del self._cache[abs_path]

            # 缓存未命中
            self._misses += 1
            return None

    def set(self, workflow_path: str, definition: Dict[str, Any]) -> None:
        """设置缓存

        Args:
            workflow_path: 工作流文件路径
            definition: 工作流定义
        """
        abs_path = os.path.abspath(workflow_path)

        try:
            mtime = os.path.getmtime(abs_path)
            checksum = self._calculate_checksum(abs_path)

            cached = CachedWorkflow(
                definition=definition,
                file_path=abs_path,
                mtime=mtime,
                cached_at=time.time(),
                checksum=checksum,
                access_count=1,
            )

            with self._lock:
                self._cache[abs_path] = cached
                self._enforce_size_limit()

                logger.debug(f"缓存已设置: {abs_path}")
        except Exception as e:
            logger.warning(f"设置缓存失败 {abs_path}: {e}")

    def load(self, workflow_path: str) -> Optional[Dict[str, Any]]:
        """加载工作流（使用缓存）

        Args:
            workflow_path: 工作流文件路径

        Returns:
            工作流定义，如果加载失败则返回 None
        """
        # 尝试从缓存获取
        cached = self.get(workflow_path)
        if cached is not None:
            return cached

        # 缓存未命中，从文件加载
        try:
            with open(workflow_path, "r", encoding="utf-8") as f:
                definition = yaml.safe_load(f)

            if definition:
                self.set(workflow_path, definition)
                return definition
        except Exception as e:
            logger.error(f"加载工作流失败 {workflow_path}: {e}")

        return None

    def invalidate(self, workflow_path: str = None):
        """使缓存失效

        Args:
            workflow_path: 工作流路径，如果为 None 则清空所有缓存
        """
        with self._lock:
            if workflow_path:
                abs_path = os.path.abspath(workflow_path)
                if abs_path in self._cache:
                    del self._cache[abs_path]
                    logger.debug(f"缓存已失效: {abs_path}")
            else:
                self._cache.clear()
                logger.debug("所有缓存已清空")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息

        Returns:
            包含缓存统计的字典
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self._config.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "ttl_seconds": self._config.ttl_seconds,
            }

    def preload(self, workflows_dir: str):
        """预加载目录中的所有工作流

        Args:
            workflows_dir: 工作流目录路径
        """
        workflow_dir = Path(workflows_dir)
        if not workflow_dir.exists():
            logger.warning(f"工作流目录不存在: {workflows_dir}")
            return

        count = 0
        for workflow_file in workflow_dir.rglob("*.yaml"):
            if self.load(str(workflow_file)):
                count += 1

        logger.info(f"预加载了 {count} 个工作流定义")


# 全局缓存实例
_global_cache: Optional[WorkflowCache] = None
_cache_lock = threading.Lock()


def get_workflow_cache() -> WorkflowCache:
    """获取全局工作流缓存实例"""
    global _global_cache

    if _global_cache is None:
        with _cache_lock:
            if _global_cache is None:
                _global_cache = WorkflowCache()

    return _global_cache
