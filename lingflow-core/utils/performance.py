"""
LingFlow Performance Optimizations - 性能优化

添加缓存机制，优化性能
"""

import functools
import logging
from typing import Dict, List, Any, Optional
from functools import wraps
import hashlib
import json
import time

logger = logging.getLogger(__name__)


def log_execution_time(func):
    """记录执行时间的装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000  # 转换为毫秒

        if elapsed > 10:  # 超过10ms记录警告
            logger.warning(f"{func.__name__} took {elapsed:.2f}ms")

        return result
    return wrapper


def cache_result(max_size=128, ttl=300):
    """缓存结果的装饰器"""
    def decorator(func):
        cache = {}
        cache_timestamps = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key_parts = [func.__name__]

            # 处理参数
            if args:
                # 对于不可哈希的参数（如列表），转换为字符串
                for arg in args:
                    if isinstance(arg, (list, dict)):
                        arg = json.dumps(arg, sort_keys=True)
                    key_parts.append(str(arg))

            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                for k, v in sorted_kwargs:
                    if isinstance(v, (list, dict)):
                        v = json.dumps(v, sort_keys=True)
                    key_parts.append(f"{k}={v}")

            cache_key = ":".join(key_parts)
            current_time = time.time()

            # 检查缓存
            if cache_key in cache:
                timestamp = cache_timestamps[cache_key]
                if current_time - timestamp < ttl:
                    logger.debug(f"Cache hit: {func.__name__}")
                    return cache[cache_key]
                else:
                    # 缓存过期
                    del cache[cache_key]
                    del cache_timestamps[cache_key]

            # 调用函数
            result = func(*args, **kwargs)

            # 存储到缓存
            if len(cache) >= max_size:
                # LRU: 删除最旧的
                oldest_key = min(cache_timestamps, key=cache_timestamps.get)
                del cache[oldest_key]
                del cache_timestamps[oldest_key]

            cache[cache_key] = result
            cache_timestamps[cache_key] = current_time

            return result

        return wrapper
    return decorator


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = {}
        self.counters = {}

    def record_execution(self, func_name: str, duration_ms: float):
        """记录执行时间"""
        if func_name not in self.metrics:
            self.metrics[func_name] = {
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0
            }

        self.metrics[func_name]["count"] += 1
        self.metrics[func_name]["total_time"] += duration_ms
        self.metrics[func_name]["min_time"] = min(
            self.metrics[func_name]["min_time"],
            duration_ms
        )
        self.metrics[func_name]["max_time"] = max(
            self.metrics[func_name]["max_time"],
            duration_ms
        )

    def get_stats(self, func_name: str) -> Dict[str, Any]:
        """获取统计信息"""
        if func_name not in self.metrics:
            return None

        stats = self.metrics[func_name]
        count = stats["count"]

        return {
            "count": count,
            "avg_time": stats["total_time"] / count,
            "min_time": stats["min_time"],
            "max_time": stats["max_time"],
            "total_time": stats["total_time"]
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有统计"""
        return {
            name: self.get_stats(name)
            for name in self.metrics
        }

    def reset(self):
        """重置统计"""
        self.metrics = {}
        self.counters = {}


# 全局监控器实例
_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取性能监控器实例"""
    return _monitor
