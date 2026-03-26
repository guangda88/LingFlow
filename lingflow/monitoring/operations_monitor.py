"""LingFlow Operations Monitoring Module

Integrates application-level monitoring with system-level performance tracking.
Bridges the gap between skill-analytics and performance monitoring.

Version: 1.0
Date: 2026-03-26
"""

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from lingflow.utils.performance import PerformanceMonitor, performance_monitor

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """告警严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警信息"""
    id: str
    severity: AlertSeverity
    source: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    component: str
    healthy: bool
    message: str
    timestamp: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: float = 0


class AlertRule:
    """告警规则"""

    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        severity: AlertSeverity,
        message_template: str,
        cooldown_seconds: int = 300,
    ):
        self.name = name
        self.condition = condition
        self.severity = severity
        self.message_template = message_template
        self.cooldown_seconds = cooldown_seconds
        self.last_triggered: Optional[datetime] = None

    def should_trigger(self, metrics: Dict[str, Any]) -> bool:
        """检查是否应该触发告警"""
        now = datetime.now()

        # 检查冷却期
        if self.last_triggered:
            elapsed = (now - self.last_triggered).total_seconds()
            if elapsed < self.cooldown_seconds:
                return False

        # 检查条件
        if self.condition(metrics):
            self.last_triggered = now
            return True

        return False

    def format_message(self, metrics: Dict[str, Any]) -> str:
        """格式化告警消息"""
        return self.message_template.format(**metrics)


class OperationsMonitor:
    """运维监控器 - 整合应用级和系统级监控

    功能：
    - 健康检查
    - 告警规则
    - 指标聚合
    - 通知集成
    """

    def __init__(self, performance_monitor: PerformanceMonitor = None):
        self.performance_monitor = performance_monitor or performance_monitor

        # 健康检查注册表
        self._health_checks: Dict[str, Callable[[], HealthCheckResult]] = {}

        # 告警规则
        self._alert_rules: List[AlertRule] = []

        # 活跃告警
        self._active_alerts: Dict[str, Alert] = {}

        # 告警历史
        self._alert_history: List[Alert] = []

        # 通知处理器
        self._notification_handlers: List[Callable[[Alert], None]] = []

        # 组件状态
        self._component_status: Dict[str, bool] = {}

        # 锁
        self._lock = threading.RLock()

        # 配置默认告警规则
        self._setup_default_alert_rules()

    def _setup_default_alert_rules(self):
        """配置默认告警规则"""
        # 执行时间告警
        self.add_alert_rule(
            AlertRule(
                name="slow_execution",
                condition=lambda m: m.get("avg_time", 0) > 5.0,
                severity=AlertSeverity.WARNING,
                message_template="组件 {name} 执行缓慢: 平均 {avg_time:.2f}s",
                cooldown_seconds=300,
            )
        )

        # 成功率告警
        self.add_alert_rule(
            AlertRule(
                name="low_success_rate",
                condition=lambda m: m.get("success_rate", 100) < 90,
                severity=AlertSeverity.ERROR,
                message_template="组件 {name} 成功率低: {success_rate:.1f}%",
                cooldown_seconds=600,
            )
        )

        # 失败计数告警
        self.add_alert_rule(
            AlertRule(
                name="high_failure_count",
                condition=lambda m: m.get("failure_count", 0) > 10,
                severity=AlertSeverity.CRITICAL,
                message_template="组件 {name} 失败次数过多: {failure_count} 次",
                cooldown_seconds=180,
            )
        )

        # 内存使用告警
        self.add_alert_rule(
            AlertRule(
                name="high_memory_usage",
                condition=lambda m: m.get("memory_usage_percent", 0) > 80,
                severity=AlertSeverity.WARNING,
                message_template="内存使用率过高: {memory_usage_percent:.1f}%",
                cooldown_seconds=300,
            )
        )

    def register_health_check(
        self, component: str, check_func: Callable[[], HealthCheckResult]
    ):
        """注册健康检查

        Args:
            component: 组件名称
            check_func: 健康检查函数
        """
        with self._lock:
            self._health_checks[component] = check_func
            logger.info(f"注册健康检查: {component}")

    def unregister_health_check(self, component: str):
        """注销健康检查"""
        with self._lock:
            if component in self._health_checks:
                del self._health_checks[component]
                logger.info(f"注销健康检查: {component}")

    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        with self._lock:
            self._alert_rules.append(rule)
            logger.info(f"添加告警规则: {rule.name}")

    def remove_alert_rule(self, rule_name: str):
        """移除告警规则"""
        with self._lock:
            self._alert_rules = [r for r in self._alert_rules if r.name != rule_name]
            logger.info(f"移除告警规则: {rule_name}")

    def add_notification_handler(self, handler: Callable[[Alert], None]):
        """添加通知处理器"""
        with self._lock:
            self._notification_handlers.append(handler)
            logger.info(f"添加通知处理器: {handler.__name__}")

    def run_health_checks(self) -> Dict[str, HealthCheckResult]:
        """运行所有健康检查

        Returns:
            各组件的健康检查结果
        """
        results = {}

        with self._lock:
            checks = dict(self._health_checks)

        for component, check_func in checks.items():
            try:
                start_time = time.perf_counter()
                result = check_func()
                result.response_time_ms = (time.perf_counter() - start_time) * 1000
                results[component] = result

                # 更新组件状态
                self._component_status[component] = result.healthy

            except Exception as e:
                logger.error(f"健康检查失败 {component}: {e}")
                results[component] = HealthCheckResult(
                    component=component,
                    healthy=False,
                    message=f"检查失败: {str(e)}",
                    timestamp=datetime.now(),
                    response_time_ms=0,
                )
                self._component_status[component] = False

        return results

    def evaluate_metrics(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估指标并生成告警

        Args:
            metrics: 性能指标

        Returns:
            触发的告警列表
        """
        alerts = []

        for rule in self._alert_rules:
            try:
                if rule.should_trigger(metrics):
                    alert = Alert(
                        id=f"{rule.name}_{int(time.time())}",
                        severity=rule.severity,
                        source=rule.name,
                        message=rule.format_message(metrics),
                        timestamp=datetime.now(),
                        metadata={"metrics": metrics},
                    )

                    alerts.append(alert)
                    self._active_alerts[alert.id] = alert
                    self._alert_history.append(alert)

                    # 发送通知
                    self._send_notification(alert)

            except Exception as e:
                logger.error(f"评估告警规则失败 {rule.name}: {e}")

        return alerts

    def evaluate_all_metrics(self) -> List[Alert]:
        """评估所有性能指标并生成告警

        Returns:
            触发的告警列表
        """
        all_alerts = []

        # 获取所有性能指标
        all_stats = self.performance_monitor.get_all_stats()

        # 评估每个指标
        for metric_name, stats in all_stats.items():
            metrics_with_name = {**stats, "name": metric_name}
            alerts = self.evaluate_metrics(metrics_with_name)
            all_alerts.extend(alerts)

        return all_alerts

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警

        Args:
            alert_id: 告警 ID

        Returns:
            True 如果告警存在并被解决
        """
        with self._lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                del self._active_alerts[alert_id]
                logger.info(f"解决告警: {alert_id}")
                return True
            return False

    def _send_notification(self, alert: Alert):
        """发送告警通知"""
        for handler in self._notification_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"发送通知失败: {e}")

    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        with self._lock:
            return list(self._active_alerts.values())

    def get_alert_history(
        self, limit: int = 100, severity: AlertSeverity = None
    ) -> List[Alert]:
        """获取告警历史

        Args:
            limit: 返回数量限制
            severity: 过滤严重级别

        Returns:
            告警历史列表
        """
        with self._lock:
            history = self._alert_history.copy()

            if severity:
                history = [a for a in history if a.severity == severity]

            # 按时间倒序
            history.sort(key=lambda a: a.timestamp, reverse=True)

            return history[:limit]

    def get_component_status(self) -> Dict[str, bool]:
        """获取所有组件状态"""
        with self._lock:
            return self._component_status.copy()

    def get_overall_health(self) -> bool:
        """获取整体健康状态"""
        return all(self._component_status.values()) if self._component_status else True

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        health_results = self.run_health_checks()
        active_alerts = self.get_active_alerts()

        # 统计健康状态
        healthy_count = sum(1 for r in health_results.values() if r.healthy)
        total_count = len(health_results)

        # 统计告警
        alert_counts = defaultdict(int)
        for alert in active_alerts:
            alert_counts[alert.severity.value] += 1

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_healthy": self.get_overall_health(),
            "components": {
                "total": total_count,
                "healthy": healthy_count,
                "unhealthy": total_count - healthy_count,
            },
            "alerts": {
                "active": len(active_alerts),
                "by_severity": dict(alert_counts),
            },
            "health_checks": {
                name: {
                    "healthy": result.healthy,
                    "message": result.message,
                    "response_time_ms": result.response_time_ms,
                }
                for name, result in health_results.items()
            },
        }


# 全局单例
_operations_monitor: Optional[OperationsMonitor] = None
_monitor_lock = threading.Lock()


def get_operations_monitor() -> OperationsMonitor:
    """获取运维监控器单例"""
    global _operations_monitor
    if _operations_monitor is None:
        with _monitor_lock:
            if _operations_monitor is None:
                _operations_monitor = OperationsMonitor()
    return _operations_monitor


# 便捷函数
def register_health_check(component: str, check_func: Callable[[], HealthCheckResult]):
    """注册健康检查"""
    return get_operations_monitor().register_health_check(component, check_func)


def add_alert_rule(rule: AlertRule):
    """添加告警规则"""
    return get_operations_monitor().add_alert_rule(rule)


def add_notification_handler(handler: Callable[[Alert], None]):
    """添加通知处理器"""
    return get_operations_monitor().add_notification_handler(handler)


def run_health_checks() -> Dict[str, HealthCheckResult]:
    """运行所有健康检查"""
    return get_operations_monitor().run_health_checks()


def evaluate_all_metrics() -> List[Alert]:
    """评估所有指标"""
    return get_operations_monitor().evaluate_all_metrics()


def get_active_alerts() -> List[Alert]:
    """获取活跃告警"""
    return get_operations_monitor().get_active_alerts()


def get_monitoring_summary() -> Dict[str, Any]:
    """获取监控摘要"""
    return get_operations_monitor().get_monitoring_summary()
