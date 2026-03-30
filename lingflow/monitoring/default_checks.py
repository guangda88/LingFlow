"""Default Health Checks and Notification Handlers for Operations Monitor

Provides pre-configured health checks for common LingFlow components
and notification handlers for alerts.
"""

import logging
import psutil
import threading
import time
from datetime import datetime
from typing import Optional

from lingflow.core.layered_skill_loader import get_layered_loader, get_memory_usage
from lingflow.monitoring.operations_monitor import (
    Alert,
    HealthCheckResult,
    register_health_check,
    add_notification_handler,
    get_operations_monitor,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Default Health Checks
# ============================================================================

def check_skill_loader() -> HealthCheckResult:
    """检查技能加载器健康状态"""
    try:
        loader = get_layered_loader()
        stats = loader.get_layer_stats()
        memory = get_memory_usage()

        # 检查 L3 活跃技能是否超过限制
        l3_active = memory.get("l3_active", 0)
        l3_max = memory.get("target_l3_max", 15)

        if l3_active > l3_max:
            return HealthCheckResult(
                component="skill_loader",
                healthy=False,
                message=f"L3 活跃技能超限: {l3_active}/{l3_max}",
                timestamp=datetime.now(),
                metrics=stats,
            )

        # 检查总缓存大小
        total_cached = memory.get("total_cached", 0)
        if total_cached > 50:
            return HealthCheckResult(
                component="skill_loader",
                healthy=False,
                message=f"缓存技能过多: {total_cached}",
                timestamp=datetime.now(),
                metrics=memory,
            )

        return HealthCheckResult(
            component="skill_loader",
            healthy=True,
            message="技能加载器正常",
            timestamp=datetime.now(),
            metrics={**stats, **memory},
        )

    except Exception as e:
        return HealthCheckResult(
            component="skill_loader",
            healthy=False,
            message=f"检查失败: {str(e)}",
            timestamp=datetime.now(),
        )


def check_memory_usage() -> HealthCheckResult:
    """检查内存使用情况"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()

        # 计算内存使用百分比
        memory_percent = process.memory_percent()
        memory_mb = memory_info.rss / 1024 / 1024

        # 内存使用超过 80% 为不健康
        if memory_percent > 80:
            return HealthCheckResult(
                component="memory",
                healthy=False,
                message=f"内存使用率过高: {memory_percent:.1f}%",
                timestamp=datetime.now(),
                metrics={
                    "memory_mb": memory_mb,
                    "memory_percent": memory_percent,
                },
            )

        return HealthCheckResult(
            component="memory",
            healthy=True,
            message=f"内存使用正常: {memory_mb:.1f}MB ({memory_percent:.1f}%)",
            timestamp=datetime.now(),
            metrics={
                "memory_mb": memory_mb,
                "memory_percent": memory_percent,
            },
        )

    except Exception as e:
        return HealthCheckResult(
            component="memory",
            healthy=False,
            message=f"检查失败: {str(e)}",
            timestamp=datetime.now(),
        )


def check_disk_usage() -> HealthCheckResult:
    """检查磁盘使用情况"""
    try:
        disk = psutil.disk_usage("/")
        usage_percent = disk.used / disk.total * 100
        free_gb = disk.free / 1024 / 1024 / 1024

        # 磁盘使用超过 90% 为不健康
        if usage_percent > 90:
            return HealthCheckResult(
                component="disk",
                healthy=False,
                message=f"磁盘空间不足: {usage_percent:.1f}% 使用",
                timestamp=datetime.now(),
                metrics={
                    "usage_percent": usage_percent,
                    "free_gb": free_gb,
                },
            )

        return HealthCheckResult(
            component="disk",
            healthy=True,
            message=f"磁盘空间正常: {free_gb:.1f}GB 可用 ({usage_percent:.1f}% 使用)",
            timestamp=datetime.now(),
            metrics={
                "usage_percent": usage_percent,
                "free_gb": free_gb,
            },
        )

    except Exception as e:
        return HealthCheckResult(
            component="disk",
            healthy=False,
            message=f"检查失败: {str(e)}",
            timestamp=datetime.now(),
        )


def check_cpu_usage() -> HealthCheckResult:
    """检查 CPU 使用情况"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)

        # CPU 使用超过 90% 为不健康
        if cpu_percent > 90:
            return HealthCheckResult(
                component="cpu",
                healthy=False,
                message=f"CPU 使用率过高: {cpu_percent:.1f}%",
                timestamp=datetime.now(),
                metrics={"cpu_percent": cpu_percent},
            )

        return HealthCheckResult(
            component="cpu",
            healthy=True,
            message=f"CPU 使用正常: {cpu_percent:.1f}%",
            timestamp=datetime.now(),
            metrics={"cpu_percent": cpu_percent},
        )

    except Exception as e:
        return HealthCheckResult(
            component="cpu",
            healthy=False,
            message=f"检查失败: {str(e)}",
            timestamp=datetime.now(),
        )


# ============================================================================
# Default Notification Handlers
# ============================================================================

def log_notification_handler(alert: Alert):
    """日志通知处理器"""
    log_func = {
        AlertSeverity.INFO: logger.info,
        AlertSeverity.WARNING: logger.warning,
        AlertSeverity.ERROR: logger.error,
        AlertSeverity.CRITICAL: logger.critical,
    }.get(alert.severity, logger.info)

    log_func(
        f"[{alert.severity.value.upper()}] {alert.source}: {alert.message}"
    )


def console_notification_handler(alert: Alert):
    """控制台通知处理器 (带颜色)"""
    colors = {
        AlertSeverity.INFO: "\033[36m",     # Cyan
        AlertSeverity.WARNING: "\033[33m",  # Yellow
        AlertSeverity.ERROR: "\033[31m",    # Red
        AlertSeverity.CRITICAL: "\033[35m", # Magenta
    }
    reset = "\033[0m"

    color = colors.get(alert.severity, "")
    print(f"{color}[{alert.severity.value.upper()}] {alert.source}: {alert.message}{reset}")


# ============================================================================
# Registration Function
# ============================================================================

def register_default_checks():
    """注册默认健康检查"""
    register_health_check("skill_loader", check_skill_loader)
    register_health_check("memory", check_memory_usage)
    register_health_check("disk", check_disk_usage)
    register_health_check("cpu", check_cpu_usage)
    logger.info("已注册默认健康检查")


def register_default_handlers():
    """注册默认通知处理器"""
    monitor = get_operations_monitor()

    # 添加日志处理器 (默认已添加)
    # 添加控制台处理器
    monitor.add_notification_handler(console_notification_handler)

    logger.info("已注册默认通知处理器")


def setup_default_monitoring():
    """设置默认监控"""
    register_default_checks()
    register_default_handlers()
    return get_operations_monitor()


# ============================================================================
# Monitoring Loop
# ============================================================================

class MonitoringLoop:
    """监控循环 - 定期运行健康检查和告警评估"""

    def __init__(
        self,
        check_interval: int = 60,  # 健康检查间隔 (秒)
        alert_interval: int = 30,  # 告警评估间隔 (秒)
    ):
        self.check_interval = check_interval
        self.alert_interval = alert_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """启动监控循环"""
        import threading

        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("监控循环已启动")

    def stop(self):
        """停止监控循环"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("监控循环已停止")

    def _run_loop(self):
        """运行监控循环"""
        monitor = get_operations_monitor()
        last_check_time = 0
        last_alert_time = 0

        while self._running:
            now = time.time()

            # 运行健康检查
            if now - last_check_time >= self.check_interval:
                try:
                    results = monitor.run_health_checks()
                    logger.debug(f"健康检查完成: {len(results)} 个组件")
                except Exception as e:
                    logger.error(f"健康检查失败: {e}")
                last_check_time = now

            # 评估告警
            if now - last_alert_time >= self.alert_interval:
                try:
                    alerts = monitor.evaluate_all_metrics()
                    if alerts:
                        logger.info(f"生成 {len(alerts)} 个新告警")
                except Exception as e:
                    logger.error(f"告警评估失败: {e}")
                last_alert_time = now

            # 等待下次循环
            time.sleep(min(self.check_interval, self.alert_interval))


# 全局监控循环实例
_monitoring_loop: Optional[MonitoringLoop] = None


def start_monitoring(check_interval: int = 60, alert_interval: int = 30):
    """启动默认监控

    Args:
        check_interval: 健康检查间隔 (秒)
        alert_interval: 告警评估间隔 (秒)
    """
    global _monitoring_loop

    # 设置默认监控
    setup_default_monitoring()

    # 启动监控循环
    _monitoring_loop = MonitoringLoop(check_interval, alert_interval)
    _monitoring_loop.start()

    return _monitoring_loop


def stop_monitoring():
    """停止默认监控"""
    global _monitoring_loop

    if _monitoring_loop:
        _monitoring_loop.stop()
        _monitoring_loop = None
