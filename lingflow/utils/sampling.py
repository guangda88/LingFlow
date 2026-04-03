"""
采样监控模块 - 用于高负载场景下的性能数据采集

当系统负载较高时，通过采样减少监控数据的收集量，防止监控本身成为性能瓶颈。

Features:
- 自适应采样率
- 基于负载的动态调整
- 保留关键指标的完整记录
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from lingflow.utils.performance import PerformanceMonitor, performance_monitor

logger = logging.getLogger(__name__)


@dataclass
class SamplingConfig:
    """采样配置"""

    # 默认采样率
    default_rate: float = 0.1  # 10%
    # 低负载采样率阈值
    low_load_threshold: float = 0.5  # CPU < 50%
    low_load_rate: float = 1.0  # 100% 采样
    # 高负载采样率阈值
    high_load_threshold: float = 0.8  # CPU > 80%
    high_load_rate: float = 0.05  # 5% 采样
    # 关键指标（不采样）
    critical_metrics: set = field(
        default_factory=lambda: {
            "skill_load",
            "workflow_execution",
            "error_handler",
        }
    )


class SamplingMonitor:
    """采样监控器

    根据系统负载动态调整监控数据的采样率，
    在保证关键指标可观测性的同时减少性能开销。
    """

    def __init__(self, config: SamplingConfig = None, base_monitor: PerformanceMonitor = None):
        self._config = config or SamplingConfig()
        self._base_monitor = base_monitor or performance_monitor
        self._current_rate = self._config.default_rate
        self._last_adjustment = time.time()
        self._adjustment_interval = 60  # 每分钟调整一次

    def should_record(self, metric_name: str = None) -> bool:
        """判断是否应该记录当前指标

        Args:
            metric_name: 指标名称，关键指标总是记录

        Returns:
            True 如果应该记录，False 如果应该跳过
        """
        # 关键指标总是记录
        if metric_name and metric_name in self._config.critical_metrics:
            return True

        # 根据当前采样率决定
        return random.random() < self._current_rate

    def adjust_sampling_rate(self, system_load: float):
        """根据系统负载调整采样率

        Args:
            system_load: 系统负载 (0.0 - 1.0)
        """
        now = time.time()
        if now - self._last_adjustment < self._adjustment_interval:
            return  # 避免频繁调整

        self._last_adjustment = now

        if system_load < self._config.low_load_threshold:
            self._current_rate = self._config.low_load_rate
            logger.debug(f"低负载，采样率设置为 {self._current_rate:.0%}")
        elif system_load > self._config.high_load_threshold:
            self._current_rate = self._config.high_load_rate
            logger.debug(f"高负载，采样率降低至 {self._current_rate:.0%}")
        else:
            # 中等负载，线性插值
            ratio = (system_load - self._config.low_load_threshold) / (
                self._config.high_load_threshold - self._config.low_load_threshold
            )
            self._current_rate = self._config.low_load_rate * (1 - ratio) + self._config.high_load_rate * ratio
            logger.debug(f"中等负载，采样率设置为 {self._current_rate:.0%}")

    def track(self, metric_name: Optional[str] = None) -> Callable[[Callable], Callable]:
        """带采样的性能追踪装饰器

        Args:
            metric_name: 指标名称

        Returns:
            装饰器函数
        """

        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # 检查是否应该记录
                if not self.should_record(metric_name):
                    return func(*args, **kwargs)

                # 使用基础监控器记录
                return self._base_monitor.track(metric_name)(func)(*args, **kwargs)

            return wrapper

        return decorator

    def get_sampling_rate(self) -> float:
        """获取当前采样率"""
        return self._current_rate

    def set_sampling_rate(self, rate: float):
        """手动设置采样率

        Args:
            rate: 采样率 (0.0 - 1.0)
        """
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"采样率必须在 0.0 到 1.0 之间，收到 {rate}")
        self._current_rate = rate
        logger.info(f"采样率手动设置为 {rate:.0%}")


# 全局采样监控器实例
sampling_monitor = SamplingMonitor()


# 便捷装饰器
def track_with_sampling(metric_name: Optional[str] = None) -> Callable[[Callable], Callable]:
    """带采样的性能追踪装饰器（使用全局监控器）

    Args:
        metric_name: 指标名称

    Returns:
        装饰器函数
    """
    return sampling_monitor.track(metric_name)


def get_sampling_stats() -> Dict[str, Any]:
    """获取采样统计信息

    Returns:
        包含当前采样率和配置的字典
    """
    return {
        "current_rate": sampling_monitor.get_sampling_rate(),
        "config": {
            "default_rate": sampling_monitor._config.default_rate,
            "low_load_threshold": sampling_monitor._config.low_load_threshold,
            "low_load_rate": sampling_monitor._config.low_load_rate,
            "high_load_threshold": sampling_monitor._config.high_load_threshold,
            "high_load_rate": sampling_monitor._config.high_load_rate,
            "critical_metrics": list(sampling_monitor._config.critical_metrics),
        },
    }
