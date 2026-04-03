"""数据收集器模块

提供系统指标数据的收集功能。
"""

import logging
import shutil
from datetime import datetime
from typing import Dict, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from ..metrics.models import HealthCheckResult, SystemMetrics

logger = logging.getLogger(__name__)


class MetricCollector:
    """指标收集器

    收集系统级指标数据。
    """

    def __init__(self):
        """初始化收集器"""
        self.available = PSUTIL_AVAILABLE

        if not self.available:
            logger.warning("psutil不可用，系统指标收集功能受限")

    def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标

        Returns:
            系统指标对象
        """
        if not self.available:
            # 返回默认值
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                timestamp=datetime.now(),
            )

        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存指标
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)

            # 磁盘指标
            disk = psutil.disk_usage("/")
            disk_usage_percent = disk.percent
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)

            # 网络IO
            net_io = psutil.net_io_counters()
            network_io = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
            }

            # 进程数
            process_count = len(psutil.pids())

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_io=network_io,
                process_count=process_count,
                timestamp=datetime.now(),
            )

        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return SystemMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                disk_used_gb=0.0,
                disk_free_gb=0.0,
                timestamp=datetime.now(),
            )

    def collect_process_metrics(self, pid: Optional[int] = None) -> Dict[str, float]:
        """收集进程指标

        Args:
            pid: 进程ID，默认为当前进程

        Returns:
            进程指标字典
        """
        if not self.available:
            return {}

        try:
            import os

            process = psutil.Process(pid or os.getpid())

            return {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / (1024 * 1024),
                "num_threads": process.num_threads(),
                "num_fds": process.num_fds() if hasattr(process, "num_fds") else 0,
                "connections": len(process.connections()),
            }

        except Exception as e:
            logger.error(f"收集进程指标失败: {e}")
            return {}


class HealthCheckCollector:
    """健康检查收集器

    执行各种健康检查。
    """

    def __init__(self):
        """初始化健康检查收集器"""
        self.checks: Dict[str, callable] = {}

    def register_check(self, name: str, check_func: callable) -> None:
        """注册健康检查

        Args:
            name: 检查名称
            check_func: 检查函数，返回HealthCheckResult
        """
        self.checks[name] = check_func
        logger.debug(f"注册健康检查: {name}")

    def run_check(self, name: str) -> Optional["HealthCheckResult"]:
        """运行单个健康检查

        Args:
            name: 检查名称

        Returns:
            检查结果，检查不存在返回None
        """
        if name not in self.checks:
            logger.warning(f"健康检查不存在: {name}")
            return None

        try:
            return self.checks[name]()
        except Exception as e:
            logger.error(f"健康检查失败 {name}: {e}")
            return None

    def run_all_checks(self) -> Dict[str, "HealthCheckResult"]:
        """运行所有健康检查

        Returns:
            检查结果字典
        """
        results = {}

        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = result
            except Exception as e:
                logger.error(f"健康检查失败 {name}: {e}")

        return results

    def check_disk_space(self, path: str = "/", threshold: float = 90.0) -> "HealthCheckResult":
        """检查磁盘空间

        Args:
            path: 检查路径
            threshold: 告警阈值（百分比）

        Returns:
            检查结果
        """
        from ..metrics.models import HealthCheckResult
        import time

        start = time.time()
        usage = shutil.disk_usage(path)
        percent = (usage.used / usage.total) * 100
        elapsed = (time.time() - start) * 1000

        healthy = percent < threshold

        return HealthCheckResult(
            component=f"disk_{path.replace('/', '_')}",
            healthy=healthy,
            message=f"磁盘使用率: {percent:.1f}%" + (" (正常)" if healthy else " (告警)"),
            timestamp=datetime.now(),
            metrics={
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3),
                "percent": percent,
            },
            response_time_ms=elapsed,
        )

    def check_memory(self, threshold: float = 90.0) -> "HealthCheckResult":
        """检查内存使用

        Args:
            threshold: 告警阈值（百分比）

        Returns:
            检查结果
        """
        from ..metrics.models import HealthCheckResult
        import time

        start = time.time()

        if not PSUTIL_AVAILABLE:
            return HealthCheckResult(
                component="memory",
                healthy=True,
                message="psutil不可用，无法检查",
                timestamp=datetime.now(),
                response_time_ms=(time.time() - start) * 1000,
            )

        memory = psutil.virtual_memory()
        percent = memory.percent
        elapsed = (time.time() - start) * 1000

        healthy = percent < threshold

        return HealthCheckResult(
            component="memory",
            healthy=healthy,
            message=f"内存使用率: {percent:.1f}%" + (" (正常)" if healthy else " (告警)"),
            timestamp=datetime.now(),
            metrics={"total_gb": memory.total / (1024**3), "available_gb": memory.available / (1024**3), "percent": percent},
            response_time_ms=elapsed,
        )
