"""LingFlow Operations Monitoring Module

整合应用级监控和系统级性能追踪。

功能：
- 健康检查管理
- 告警规则评估
- 指标数据收集
- 性能监控集成
"""

import logging
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from lingflow.utils.performance import PerformanceMonitor, performance_monitor

from .alerts.rules import AlertRule, RuleRegistry, create_common_rules
from .collectors.base import HealthCheckCollector, MetricCollector
from .metrics.models import Alert, AlertSeverity, HealthCheckResult, SystemMetrics

logger = logging.getLogger(__name__)


class OperationsMonitor:
    """运维监控器

    整合应用级和系统级监控。

    功能：
    - 健康检查管理
    - 告警规则评估
    - 指标收集和存储
    - 性能监控集成
    """

    def __init__(self, auto_collect: bool = True, collect_interval: int = 60):
        """初始化监控器

        Args:
            auto_collect: 是否自动收集指标
            collect_interval: 收集间隔（秒）
        """
        self.auto_collect = auto_collect
        self.collect_interval = collect_interval

        # 初始化组件
        self.metric_collector = MetricCollector()
        self.health_collector = HealthCheckCollector()
        self.rule_registry = RuleRegistry()

        # 性能监控器
        self.perf_monitor: Optional[PerformanceMonitor] = None

        # 告警历史
        self.alerts: List[Alert] = []
        self._alerts_lock = threading.Lock()

        # 指标历史
        self.metrics_history: List[SystemMetrics] = []
        self._metrics_lock = threading.Lock()

        # 自动收集线程
        self._collect_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # 注册默认健康检查
        self._register_default_health_checks()

        # 注册默认告警规则
        self._register_default_alert_rules()

        # 启动自动收集
        if auto_collect:
            self.start_collection()

    def _register_default_health_checks(self):
        """注册默认健康检查"""
        self.health_collector.register_check("disk_space", lambda: self.health_collector.check_disk_space())
        self.health_collector.register_check("memory", lambda: self.health_collector.check_memory())

    def _register_default_alert_rules(self):
        """注册默认告警规则"""
        for rule in create_common_rules():
            self.rule_registry.register(rule)

    def start_collection(self):
        """启动自动收集"""
        if self._collect_thread is not None:
            logger.warning("自动收集已在运行")
            return

        self._stop_event.clear()
        self._collect_thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._collect_thread.start()
        logger.info("启动自动指标收集")

    def stop_collection(self):
        """停止自动收集"""
        if self._collect_thread is None:
            return

        self._stop_event.set()
        self._collect_thread.join(timeout=5)
        self._collect_thread = None
        logger.info("停止自动指标收集")

    def _collect_loop(self):
        """收集循环"""

        while not self._stop_event.is_set():
            try:
                # 收集系统指标
                metrics = self.metric_collector.collect_system_metrics()
                self.add_metrics(metrics)

                # 评估告警规则
                self._evaluate_alerts(metrics)

            except Exception as e:
                logger.error(f"指标收集失败: {e}")

            # 等待下一次收集
            self._stop_event.wait(self.collect_interval)

    def add_metrics(self, metrics: SystemMetrics) -> None:
        """添加指标到历史

        Args:
            metrics: 系统指标
        """
        with self._metrics_lock:
            self.metrics_history.append(metrics)

            # 保留最近1000条记录
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]

    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """获取当前指标

        Returns:
            最新的系统指标，如果没有则返回None
        """
        with self._metrics_lock:
            return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_history(self, limit: int = 100) -> List[SystemMetrics]:
        """获取指标历史

        Args:
            limit: 返回记录数量

        Returns:
            指标列表
        """
        with self._metrics_lock:
            return self.metrics_history[-limit:] if self.metrics_history else []

    def _evaluate_alerts(self, metrics: SystemMetrics) -> None:
        """评估告警规则

        Args:
            metrics: 系统指标
        """
        metrics_dict = metrics.to_dict()
        source = "operations_monitor"

        new_alerts = self.rule_registry.evaluate_all(metrics_dict, source)

        if new_alerts:
            with self._alerts_lock:
                self.alerts.extend(new_alerts)

            # 触发告警回调
            for alert in new_alerts:
                self._on_alert_triggered(alert)

    def _on_alert_triggered(self, alert: Alert) -> None:
        """告警触发回调

        Args:
            alert: 告警对象
        """
        logger.warning(f"告警触发: [{alert.severity.value}] {alert.message}")

        # 可以在这里添加通知逻辑
        # 例如：发送邮件、Slack通知等

    def add_alert_rule(self, rule: AlertRule) -> None:
        """添加告警规则

        Args:
            rule: 告警规则
        """
        self.rule_registry.register(rule)

    def remove_alert_rule(self, rule_name: str) -> bool:
        """移除告警规则

        Args:
            rule_name: 规则名称

        Returns:
            是否成功
        """
        return self.rule_registry.unregister(rule_name)

    def register_alert_rule(self, rule: AlertRule) -> None:
        """注册告警规则

        Args:
            rule: 告警规则
        """
        self.rule_registry.register(rule)

    def unregister_alert_rule(self, rule_name: str) -> bool:
        """注销告警规则

        Args:
            rule_name: 规则名称

        Returns:
            是否成功
        """
        return self.rule_registry.unregister(rule_name)

    def register_health_check(self, name: str, check_func: Callable, description: str = "") -> None:
        """注册健康检查

        Args:
            name: 检查名称
            check_func: 检查函数
            description: 检查描述
        """
        self.health_collector.register_check(name, check_func)

    def unregister_health_check(self, name: str) -> None:
        """注销健康检查

        Args:
            name: 检查名称
        """
        self.health_collector.checks.pop(name, None)

    @property
    def _health_checks(self) -> Dict:
        """健康检查注册表（向后兼容）"""
        return self.health_collector.checks

    @property
    def _alert_rules(self) -> List:
        """告警规则列表（向后兼容）"""
        return list(self.rule_registry._rules.values())

    def run_health_check(self, name: str) -> Optional[HealthCheckResult]:
        """运行健康检查

        Args:
            name: 检查名称

        Returns:
            检查结果
        """
        return self.health_collector.run_check(name)

    def run_health_checks(self) -> Dict[str, HealthCheckResult]:
        """运行所有健康检查

        Returns:
            检查结果字典
        """
        return self.health_collector.run_all_checks()

    def run_all_health_checks(self) -> Dict[str, HealthCheckResult]:
        """运行所有健康检查（别名）"""
        return self.run_health_checks()

    def get_alerts(
        self, severity: Optional[AlertSeverity] = None, resolved: Optional[bool] = None, limit: int = 100
    ) -> List[Alert]:
        """获取告警列表

        Args:
            severity: 严重级别过滤
            resolved: 是否已解决过滤
            limit: 返回数量

        Returns:
            告警列表
        """
        with self._alerts_lock:
            alerts = self.alerts

            if severity is not None:
                alerts = [a for a in alerts if a.severity == severity]

            if resolved is not None:
                alerts = [a for a in alerts if a.resolved == resolved]

            return alerts[-limit:]

    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警

        Args:
            alert_id: 告警ID

        Returns:
            是否成功
        """
        with self._alerts_lock:
            for alert in self.alerts:
                if alert.id == alert_id and not alert.resolved:
                    alert.resolve()
                    logger.info(f"告警已解决: {alert_id}")
                    return True
        return False

    def evaluate_metrics(self, metrics: Dict[str, Any]) -> List[Alert]:
        """评估指标并返回新告警

        Args:
            metrics: 指标字典

        Returns:
            触发的告警列表
        """
        new_alerts = self.rule_registry.evaluate_all(metrics, "manual_eval")
        if new_alerts:
            with self._alerts_lock:
                self.alerts.extend(new_alerts)
            for alert in new_alerts:
                self._on_alert_triggered(alert)
        return new_alerts

    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警（未解决的）"""
        return self.get_alerts(resolved=False)

    def get_component_status(self) -> Dict[str, bool]:
        """获取组件状态"""
        results = self.run_health_checks()
        return {name: result.healthy for name, result in results.items()}

    def get_overall_health(self) -> bool:
        """获取整体健康状态"""
        results = self.run_health_checks()
        if not results:
            return True
        return all(r.healthy for r in results.values())

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        results = self.run_health_checks()
        active = self.get_active_alerts()
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_healthy": all(r.healthy for r in results.values()) if results else True,
            "components": {name: result.healthy for name, result in results.items()},
            "alerts": {
                "total": len(self.alerts),
                "active": len(active),
                "resolved": len(self.alerts) - len(active),
            },
            "health_checks": {name: {"healthy": r.healthy, "message": r.message} for name, r in results.items()},
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息

        Returns:
            统计字典
        """
        with self._alerts_lock:
            total_alerts = len(self.alerts)
            active_alerts = sum(1 for a in self.alerts if not a.resolved)
            resolved_alerts = total_alerts - active_alerts

        with self._metrics_lock:
            metrics_count = len(self.metrics_history)

        return {
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "resolved_alerts": resolved_alerts,
            "metrics_count": metrics_count,
            "auto_collecting": self._collect_thread is not None,
        }

    def set_performance_monitor(self, monitor: PerformanceMonitor) -> None:
        """设置性能监控器

        Args:
            monitor: 性能监控器实例
        """
        self.perf_monitor = monitor

    def integrate_with_performance_monitor(self) -> None:
        """与性能监控器集成"""
        if not self.perf_monitor:
            self.perf_monitor = performance_monitor

        # 性能监控器已经提供了丰富的功能
        # 这里可以添加额外的集成逻辑
        logger.info("与性能监控器集成完成")


# 全局单例
_global_monitor: Optional[OperationsMonitor] = None


def get_global_monitor() -> OperationsMonitor:
    """获取全局监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = OperationsMonitor()
    return _global_monitor


def get_operations_monitor() -> OperationsMonitor:
    """获取全局监控器实例（别名）"""
    return get_global_monitor()


def register_health_check(name: str, check_func: Callable, description: str = "") -> None:
    """注册健康检查"""
    get_global_monitor().register_health_check(name, check_func)


def add_alert_rule(rule: AlertRule) -> None:
    """添加告警规则"""
    get_global_monitor().register_alert_rule(rule)


def run_health_checks() -> Dict[str, HealthCheckResult]:
    """运行所有健康检查"""
    return get_global_monitor().run_all_health_checks()


def evaluate_all_metrics() -> None:
    """评估所有指标"""
    monitor = get_global_monitor()
    metrics = monitor.get_current_metrics()
    if metrics:
        monitor._evaluate_alerts(metrics)


def get_active_alerts() -> List[Alert]:
    """获取活跃告警"""
    return get_global_monitor().get_active_alerts()


def get_monitoring_summary() -> Dict[str, Any]:
    """获取监控摘要"""
    return get_global_monitor().get_statistics()


def add_notification_handler(handler: Callable) -> None:
    """添加通知处理器"""
    get_global_monitor().set_performance_monitor(handler)
