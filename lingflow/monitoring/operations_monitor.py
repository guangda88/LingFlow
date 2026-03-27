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
    - 性能趋势分析
    - 异常检测
    """

    # 默认配置
    DEFAULT_TRETND_WINDOW = 100  # 趋势分析窗口大小
    DEFAULT_ANOMALY_THRESHOLD = 2.0  # 异常检测阈值（标准差倍数）

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

        # === 新增：性能趋势跟踪 ===
        self._metric_history: Dict[str, List[float]] = defaultdict(list)
        self._trend_window = self.DEFAULT_TRETND_WINDOW

        # === 新增：异常检测 ===
        self._anomaly_threshold = self.DEFAULT_ANOMALY_THRESHOLD
        self._anomaly_history: List[Dict[str, Any]] = []

        # === 新增：系统资源监控 ===
        self._system_metrics: Dict[str, float] = {}

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

        # === 新增扩展告警规则 ===

        # 技能加载时间告警
        self.add_alert_rule(
            AlertRule(
                name="slow_skill_load",
                condition=lambda m: m.get("skill_load_time", 0) > 1.0,
                severity=AlertSeverity.WARNING,
                message_template="技能 {name} 加载时间过长: {skill_load_time:.2f}s",
                cooldown_seconds=600,
            )
        )

        # 技能错误率告警
        self.add_alert_rule(
            AlertRule(
                name="high_skill_error_rate",
                condition=lambda m: m.get("error_rate", 0) > 10,
                severity=AlertSeverity.ERROR,
                message_template="技能 {name} 错误率过高: {error_rate:.1f}%",
                cooldown_seconds=300,
            )
        )

        # 上下文 Token 使用率告警
        self.add_alert_rule(
            AlertRule(
                name="high_context_usage",
                condition=lambda m: m.get("context_usage_percent", 0) > 85,
                severity=AlertSeverity.WARNING,
                message_template="上下文使用率过高: {context_usage_percent:.1f}%",
                cooldown_seconds=300,
            )
        )

        # CPU 使用率告警
        self.add_alert_rule(
            AlertRule(
                name="high_cpu_usage",
                condition=lambda m: m.get("cpu_usage_percent", 0) > 90,
                severity=AlertSeverity.WARNING,
                message_template="CPU 使用率过高: {cpu_usage_percent:.1f}%",
                cooldown_seconds=300,
            )
        )

        # 磁盘空间告警
        self.add_alert_rule(
            AlertRule(
                name="low_disk_space",
                condition=lambda m: m.get("disk_available_percent", 100) < 10,
                severity=AlertSeverity.CRITICAL,
                message_template="磁盘空间不足: 仅剩 {disk_available_percent:.1f}%",
                cooldown_seconds=600,
            )
        )

        # 并发任务数告警
        self.add_alert_rule(
            AlertRule(
                name="high_concurrent_tasks",
                condition=lambda m: m.get("concurrent_tasks", 0) > 50,
                severity=AlertSeverity.WARNING,
                message_template="并发任务数过多: {concurrent_tasks} 个",
                cooldown_seconds=180,
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

    # === 新增：性能趋势分析 ===

    def record_metric(self, name: str, value: float):
        """记录指标值用于趋势分析

        Args:
            name: 指标名称
            value: 指标值
        """
        with self._lock:
            self._metric_history[name].append(value)
            # 保持窗口大小
            if len(self._metric_history[name]) > self._trend_window:
                self._metric_history[name].pop(0)

    def get_metric_trend(self, name: str) -> Dict[str, Any]:
        """获取指标趋势

        Args:
            name: 指标名称

        Returns:
            趋势分析结果
        """
        with self._lock:
            if name not in self._metric_history or len(self._metric_history[name]) < 2:
                return {"status": "insufficient_data"}

            values = self._metric_history[name]

            # 计算基本统计
            import statistics as stats
            mean = stats.mean(values)
            median = stats.median(values)
            stdev = stats.stdev(values) if len(values) > 1 else 0

            # 计算趋势
            recent_avg = stats.mean(values[-10:]) if len(values) >= 10 else mean
            older_avg = stats.mean(values[:-10]) if len(values) >= 20 else mean
            trend_percent = ((recent_avg - older_avg) / older_avg * 100) if older_avg != 0 else 0

            # 判断趋势方向
            if trend_percent > 10:
                direction = "increasing"
            elif trend_percent < -10:
                direction = "decreasing"
            else:
                direction = "stable"

            return {
                "name": name,
                "current": values[-1],
                "mean": mean,
                "median": median,
                "stdev": stdev,
                "min": min(values),
                "max": max(values),
                "trend_direction": direction,
                "trend_percent": trend_percent,
                "sample_count": len(values),
            }

    def get_all_trends(self) -> Dict[str, Dict[str, Any]]:
        """获取所有指标趋势"""
        with self._lock:
            return {name: self.get_metric_trend(name) for name in self._metric_history}

    # === 新增：异常检测 ===

    def detect_anomaly(self, name: str, value: float) -> Optional[Dict[str, Any]]:
        """检测指标异常

        Args:
            name: 指标名称
            value: 当前值

        Returns:
            异常信息，如果没有异常则返回 None
        """
        with self._lock:
            if name not in self._metric_history or len(self._metric_history[name]) < 10:
                return None

            values = self._metric_history[name]
            import statistics as stats

            mean = stats.mean(values)
            stdev = stats.stdev(values) if len(values) > 1 else 0

            if stdev == 0:
                return None

            # 计算 Z-score
            z_score = abs((value - mean) / stdev)

            if z_score > self._anomaly_threshold:
                anomaly = {
                    "metric": name,
                    "value": value,
                    "expected_range": (mean - self._anomaly_threshold * stdev,
                                     mean + self._anomaly_threshold * stdev),
                    "z_score": z_score,
                    "timestamp": datetime.now().isoformat(),
                }
                self._anomaly_history.append(anomaly)
                return anomaly

            return None

    def get_anomaly_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取异常检测历史"""
        with self._lock:
            return self._anomaly_history[-limit:]

    # === 新增：系统资源监控 ===

    def update_system_metrics(self):
        """更新系统资源指标"""
        try:
            import psutil

            self._system_metrics = {
                "cpu_usage_percent": psutil.cpu_percent(interval=0.1),
                "memory_usage_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "disk_available_percent": 100 - psutil.disk_usage('/').percent,
            }

            # 记录指标用于趋势分析
            for name, value in self._system_metrics.items():
                self.record_metric(f"system.{name}", value)

        except ImportError:
            # psutil 不可用，跳过系统指标采集
            pass
        except Exception as e:
            logger.warning(f"更新系统指标失败: {e}")

    def get_system_metrics(self) -> Dict[str, float]:
        """获取系统资源指标"""
        return self._system_metrics.copy()

    # === 新增：增强通知处理 ===

    def setup_default_notification_handlers(self):
        """设置默认通知处理器"""
        # 控制台通知
        def console_handler(alert: Alert):
            severity_icons = {
                AlertSeverity.INFO: "ℹ️",
                AlertSeverity.WARNING: "⚠️",
                AlertSeverity.ERROR: "❌",
                AlertSeverity.CRITICAL: "🚨",
            }
            icon = severity_icons.get(alert.severity, "📊")
            print(f"{icon} [{alert.severity.value.upper()}] {alert.message}")

        self.add_notification_handler(console_handler)

        # 日志通知
        def log_handler(alert: Alert):
            log_func = {
                AlertSeverity.INFO: logger.info,
                AlertSeverity.WARNING: logger.warning,
                AlertSeverity.ERROR: logger.error,
                AlertSeverity.CRITICAL: logger.critical,
            }.get(alert.severity, logger.info)
            log_func(f"告警 [{alert.source}]: {alert.message}")

        self.add_notification_handler(log_handler)


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


# === 新增：扩展便捷函数 ===

def record_metric(name: str, value: float):
    """记录指标用于趋势分析"""
    return get_operations_monitor().record_metric(name, value)


def get_metric_trend(name: str) -> Dict[str, Any]:
    """获取指标趋势"""
    return get_operations_monitor().get_metric_trend(name)


def detect_anomaly(name: str, value: float) -> Optional[Dict[str, Any]]:
    """检测指标异常"""
    return get_operations_monitor().detect_anomaly(name, value)


def update_system_metrics():
    """更新系统资源指标"""
    return get_operations_monitor().update_system_metrics()


def get_system_metrics() -> Dict[str, float]:
    """获取系统资源指标"""
    return get_operations_monitor().get_system_metrics()
