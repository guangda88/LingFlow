"""
Performance Monitoring and Metrics System

This module provides performance monitoring, metrics collection, and caching mechanisms
for LingFlow components.

Key Features:
- Execution time tracking
- Memory usage monitoring
- Cache management with @lru_cache
- Performance statistics and reporting
"""

import time
import logging
import functools
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
import traceback

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    name: str
    execution_time: float  # seconds
    timestamp: datetime
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Performance monitoring system"""

    def __init__(self):
        self.metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self._enabled = True

    def track(self, metric_name: str = None):
        """
        Decorator to track function performance

        Args:
            metric_name: Name for the metric (defaults to function name)
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self._enabled:
                    return func(*args, **kwargs)

                name = metric_name or f"{func.__module__}.{func.__name__}"
                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    success = True
                    error_message = None
                except Exception as e:
                    success = False
                    error_message = str(e)
                    logger.error(f"Error in {name}: {e}")
                    raise

                end_time = time.perf_counter()
                execution_time = end_time - start_time

                metric = PerformanceMetric(
                    name=name,
                    execution_time=execution_time,
                    timestamp=datetime.utcnow(),
                    success=success,
                    error_message=error_message
                )

                self.metrics[name].append(metric)

                # Log slow operations (>1 second)
                if execution_time > 1.0:
                    logger.warning(f"Slow operation {name}: {execution_time:.2f}s")

                return result

            return wrapper
        return decorator

    def get_stats(self, metric_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific metric

        Args:
            metric_name: Name of the metric

        Returns:
            Dictionary with statistics (count, avg, min, max, success_rate)
        """
        if metric_name not in self.metrics:
            return {}

        metrics = self.metrics[metric_name]

        if not metrics:
            return {}

        execution_times = [m.execution_time for m in metrics]
        successful_metrics = [m for m in metrics if m.success]

        return {
            "name": metric_name,
            "count": len(metrics),
            "success_count": len(successful_metrics),
            "failure_count": len(metrics) - len(successful_metrics),
            "success_rate": len(successful_metrics) / len(metrics) * 100,
            "avg_time": sum(execution_times) / len(execution_times),
            "min_time": min(execution_times),
            "max_time": max(execution_times),
            "total_time": sum(execution_times),
            "last_execution": metrics[-1].timestamp.isoformat() if metrics else None
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all metrics

        Returns:
            Dictionary mapping metric names to their statistics
        """
        return {name: self.get_stats(name) for name in self.metrics.keys()}

    def print_report(self):
        """Print a formatted performance report"""
        stats = self.get_all_stats()

        if not stats:
            logger.info("No performance metrics available")
            return

        logger.info("=" * 60)
        logger.info("Performance Report")
        logger.info("=" * 60)

        for name, stat in sorted(stats.items()):
            logger.info(f"\n{name}:")
            logger.info(f"  Count: {stat['count']}")
            logger.info(f"  Success Rate: {stat['success_rate']:.1f}%")
            logger.info(f"  Avg Time: {stat['avg_time']:.4f}s")
            logger.info(f"  Min Time: {stat['min_time']:.4f}s")
            logger.info(f"  Max Time: {stat['max_time']:.4f}s")
            logger.info(f"  Total Time: {stat['total_time']:.4f}s")

        logger.info("=" * 60)

    def clear(self, metric_name: Optional[str] = None):
        """
        Clear metrics

        Args:
            metric_name: Name of metric to clear, or None to clear all
        """
        if metric_name:
            if metric_name in self.metrics:
                del self.metrics[metric_name]
                logger.info(f"Cleared metrics for {metric_name}")
        else:
            self.metrics.clear()
            logger.info("Cleared all metrics")

    def enable(self):
        """Enable performance monitoring"""
        self._enabled = True
        logger.info("Performance monitoring enabled")

    def disable(self):
        """Disable performance monitoring"""
        self._enabled = False
        logger.info("Performance monitoring disabled")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Convenience decorator
def track_performance(metric_name: str = None):
    """
    Convenience decorator for tracking performance using the global monitor

    Args:
        metric_name: Name for the metric (defaults to function name)
    """
    return performance_monitor.track(metric_name)


# Cache decorator with monitoring
def cached_with_monitor(maxsize: int = 128, metric_name: str = None):
    """
    LRU cache decorator with performance monitoring

    Args:
        maxsize: Maximum cache size
        metric_name: Name for cache hit/miss metrics
    """
    def decorator(func: Callable) -> Callable:
        # Apply LRU cache
        cached_func = lru_cache(maxsize=maxsize)(func)

        # Track cache statistics
        cache_stats = {
            "hits": 0,
            "misses": 0
        }

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check cache_info before and after to detect hits/misses
            before_info = cached_func.cache_info()

            result = cached_func(*args, **kwargs)

            after_info = cached_func.cache_info()

            # Update hit/miss counters
            hits_delta = after_info.hits - before_info.hits
            misses_delta = after_info.misses - before_info.misses

            cache_stats["hits"] += hits_delta
            cache_stats["misses"] += misses_delta

            return result

        # Add cache info method
        wrapper.cache_info = cached_func.cache_info
        wrapper.cache_clear = cached_func.cache_clear

        # Add cache statistics
        wrapper._cache_stats = cache_stats

        return wrapper
    return decorator


def get_cache_stats(func: Callable) -> Dict[str, Any]:
    """
    Get cache statistics for a cached function

    Args:
        func: Function decorated with cached_with_monitor

    Returns:
        Dictionary with cache statistics
    """
    if not hasattr(func, '_cache_stats'):
        return {}

    stats = func._cache_stats
    total = stats['hits'] + stats['misses']

    return {
        "hits": stats['hits'],
        "misses": stats['misses'],
        "total_requests": total,
        "hit_rate": stats['hits'] / total * 100 if total > 0 else 0.0
    }


class ContextTimer:
    """Context manager for timing code blocks"""

    def __init__(self, name: str, monitor: PerformanceMonitor = None):
        """
        Initialize timer

        Args:
            name: Name for the timed operation
            monitor: Performance monitor instance (defaults to global)
        """
        self.name = name
        self.monitor = monitor or performance_monitor
        self.start_time = None
        self.success = True
        self.error_message = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is None:
            return

        end_time = time.perf_counter()
        execution_time = end_time - self.start_time

        if exc_type is not None:
            self.success = False
            self.error_message = f"{exc_type.__name__}: {exc_val}"

        metric = PerformanceMetric(
            name=self.name,
            execution_time=execution_time,
            timestamp=datetime.utcnow(),
            success=self.success,
            error_message=self.error_message
        )

        self.monitor.metrics[self.name].append(metric)

        # Log slow operations
        if execution_time > 1.0:
            logger.warning(f"Slow operation {self.name}: {execution_time:.2f}s")

        return False  # Don't suppress exceptions


# Example usage
if __name__ == "__main__":
    # Enable logging
    logging.basicConfig(level=logging.INFO)

    @track_performance()
    def example_function(n: int) -> int:
        """Example function to track"""
        time.sleep(0.1)
        return sum(range(n))

    @cached_with_monitor(maxsize=100)
    def cached_function(x: int) -> int:
        """Example cached function"""
        time.sleep(0.05)
        return x * x

    # Test tracking
    for i in range(3):
        result = example_function(100)

    # Test caching
    for i in range(5):
        result = cached_function(42)

    # Print stats
    performance_monitor.print_report()

    # Print cache stats
    cache_stats = get_cache_stats(cached_function)
    logger.info(f"Cache stats: {cache_stats}")
