"""Tests for lingflow.monitoring.operations_monitor module"""

import pytest
import time
from datetime import datetime
from unittest.mock import patch, MagicMock

from lingflow.monitoring.operations_monitor import (
    OperationsMonitor,
    get_global_monitor,
    get_operations_monitor,
    register_health_check,
    add_alert_rule,
    run_health_checks,
    evaluate_all_metrics,
    get_active_alerts,
    get_monitoring_summary,
)
from lingflow.monitoring.metrics.models import AlertSeverity, Alert, HealthCheckResult
from lingflow.monitoring.alerts.rules import AlertRule


class TestOperationsMonitor:
    """Test OperationsMonitor class"""

    def test_init_default(self):
        """Test initialization with defaults"""
        monitor = OperationsMonitor()

        assert monitor.auto_collect is True
        assert monitor.collect_interval == 60
        assert monitor.metric_collector is not None
        assert monitor.health_collector is not None
        assert monitor.rule_registry is not None
        assert monitor.alerts == []
        assert monitor.metrics_history == []

    def test_init_no_auto_collect(self):
        """Test initialization without auto collect"""
        monitor = OperationsMonitor(auto_collect=False)

        assert monitor.auto_collect is False

    def test_init_custom_interval(self):
        """Test initialization with custom interval"""
        monitor = OperationsMonitor(collect_interval=120)

        assert monitor.collect_interval == 120

    def test_add_metrics(self):
        """Test adding metrics to history"""
        monitor = OperationsMonitor(auto_collect=False)

        from lingflow.monitoring.metrics.models import SystemMetrics
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=1024.0,
            memory_available_mb=512.0,
            disk_usage_percent=70.0,
            disk_used_gb=100.0,
            disk_free_gb=50.0,
        )

        monitor.add_metrics(metrics)

        assert len(monitor.metrics_history) == 1
        assert monitor.metrics_history[0] == metrics

    def test_add_metrics_limit_history(self):
        """Test that metrics history is limited"""
        monitor = OperationsMonitor(auto_collect=False)

        from lingflow.monitoring.metrics.models import SystemMetrics

        # Add more than the limit (1000)
        for i in range(1100):
            metrics = SystemMetrics(
                cpu_percent=float(i % 100),
                memory_percent=50.0,
                memory_used_mb=1000.0,
                memory_available_mb=500.0,
                disk_usage_percent=70.0,
                disk_used_gb=100.0,
                disk_free_gb=50.0,
            )
            monitor.add_metrics(metrics)

        # Should be limited to 1000
        assert len(monitor.metrics_history) == 1000

    def test_get_current_metrics_empty(self):
        """Test getting current metrics when empty"""
        monitor = OperationsMonitor(auto_collect=False)
        metrics = monitor.get_current_metrics()

        assert metrics is None

    def test_get_current_metrics_with_data(self):
        """Test getting current metrics with data"""
        monitor = OperationsMonitor(auto_collect=False)

        from lingflow.monitoring.metrics.models import SystemMetrics
        test_metrics = SystemMetrics(
            cpu_percent=75.0,
            memory_percent=55.0,
            memory_used_mb=1100.0,
            memory_available_mb=900.0,
            disk_usage_percent=65.0,
            disk_used_gb=130.0,
            disk_free_gb=70.0,
        )

        monitor.add_metrics(test_metrics)
        current = monitor.get_current_metrics()

        assert current is not None
        assert current.cpu_percent == 75.0

    def test_get_metrics_history_with_limit(self):
        """Test getting metrics history with limit"""
        monitor = OperationsMonitor(auto_collect=False)

        from lingflow.monitoring.metrics.models import SystemMetrics

        for i in range(10):
            metrics = SystemMetrics(
                cpu_percent=float(i * 10),
                memory_percent=50.0,
                memory_used_mb=1000.0,
                memory_available_mb=500.0,
                disk_usage_percent=70.0,
                disk_used_gb=100.0,
                disk_free_gb=50.0,
            )
            monitor.add_metrics(metrics)

        history = monitor.get_metrics_history(limit=5)

        assert len(history) == 5
        # Should get the most recent 5
        assert history[0].cpu_percent == 50.0

    def test_register_health_check(self):
        """Test registering a health check"""
        monitor = OperationsMonitor(auto_collect=False)

        def test_check():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="OK",
                timestamp=datetime.now(),
            )

        monitor.register_health_check("test_check", test_check)

        assert "test_check" in monitor.health_collector.checks

    def test_unregister_health_check(self):
        """Test unregistering a health check"""
        monitor = OperationsMonitor(auto_collect=False)

        def test_check():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="OK",
                timestamp=datetime.now(),
            )

        monitor.register_health_check("test_check", test_check)
        assert "test_check" in monitor.health_collector.checks

        monitor.unregister_health_check("test_check")
        assert "test_check" not in monitor.health_collector.checks

    def test_run_health_check(self):
        """Test running a single health check"""
        monitor = OperationsMonitor(auto_collect=False)

        def test_check():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="Test passed",
                timestamp=datetime.now(),
            )

        monitor.register_health_check("test", test_check)
        result = monitor.run_health_check("test")

        assert isinstance(result, HealthCheckResult)
        assert result.healthy is True

    def test_run_health_checks(self):
        """Test running all health checks"""
        monitor = OperationsMonitor(auto_collect=False)

        monitor.register_health_check("check1", lambda: HealthCheckResult(
            component="c1", healthy=True, message="OK", timestamp=datetime.now()
        ))
        monitor.register_health_check("check2", lambda: HealthCheckResult(
            component="c2", healthy=False, message="Failed", timestamp=datetime.now()
        ))

        results = monitor.run_health_checks()

        # Note: OperationsMonitor registers default checks (disk_space, memory)
        assert len(results) >= 2
        assert "check1" in results
        assert "check2" in results

    def test_add_alert_rule(self):
        """Test adding an alert rule"""
        monitor = OperationsMonitor(auto_collect=False)

        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 100,
            severity=AlertSeverity.WARNING,
            message_template="Value {value} high",
        )

        monitor.add_alert_rule(rule)

        assert "test_rule" in monitor.rule_registry._rules

    def test_remove_alert_rule(self):
        """Test removing an alert rule"""
        monitor = OperationsMonitor(auto_collect=False)

        rule = AlertRule(
            name="to_remove",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Test",
        )

        monitor.add_alert_rule(rule)
        assert "to_remove" in monitor.rule_registry._rules

        result = monitor.remove_alert_rule("to_remove")

        assert result is True
        assert "to_remove" not in monitor.rule_registry._rules

    def test_get_alerts_all(self):
        """Test getting all alerts"""
        monitor = OperationsMonitor(auto_collect=False)

        alert1 = Alert(
            id="alert-1",
            severity=AlertSeverity.INFO,
            source="test",
            message="Info",
            timestamp=datetime.now(),
        )
        alert2 = Alert(
            id="alert-2",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Warning",
            timestamp=datetime.now(),
        )

        monitor.alerts.extend([alert1, alert2])

        alerts = monitor.get_alerts()
        assert len(alerts) == 2

    def test_get_alerts_with_severity_filter(self):
        """Test getting alerts with severity filter"""
        monitor = OperationsMonitor(auto_collect=False)

        alert1 = Alert(
            id="alert-1",
            severity=AlertSeverity.INFO,
            source="test",
            message="Info",
            timestamp=datetime.now(),
        )
        alert2 = Alert(
            id="alert-2",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Warning",
            timestamp=datetime.now(),
        )

        monitor.alerts.extend([alert1, alert2])

        warnings = monitor.get_alerts(severity=AlertSeverity.WARNING)
        assert len(warnings) == 1
        assert warnings[0].id == "alert-2"

    def test_get_alerts_with_resolved_filter(self):
        """Test getting alerts with resolved filter"""
        monitor = OperationsMonitor(auto_collect=False)

        alert1 = Alert(
            id="alert-1",
            severity=AlertSeverity.INFO,
            source="test",
            message="Active",
            timestamp=datetime.now(),
        )
        alert2 = Alert(
            id="alert-2",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Resolved",
            timestamp=datetime.now(),
        )
        alert2.resolve()

        monitor.alerts.extend([alert1, alert2])

        active = monitor.get_alerts(resolved=False)
        resolved = monitor.get_alerts(resolved=True)

        assert len(active) == 1
        assert len(resolved) == 1

    def test_get_alerts_with_limit(self):
        """Test getting alerts with limit"""
        monitor = OperationsMonitor(auto_collect=False)

        for i in range(10):
            alert = Alert(
                id=f"alert-{i}",
                severity=AlertSeverity.INFO,
                source="test",
                message=f"Alert {i}",
                timestamp=datetime.now(),
            )
            monitor.alerts.append(alert)

        alerts = monitor.get_alerts(limit=5)
        assert len(alerts) == 5

    def test_resolve_alert(self):
        """Test resolving an alert"""
        monitor = OperationsMonitor(auto_collect=False)

        alert = Alert(
            id="to-resolve",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Warning",
            timestamp=datetime.now(),
        )
        monitor.alerts.append(alert)

        assert alert.resolved is False

        result = monitor.resolve_alert("to-resolve")

        assert result is True
        assert alert.resolved is True

    def test_resolve_nonexistent_alert(self):
        """Test resolving non-existent alert"""
        monitor = OperationsMonitor(auto_collect=False)
        result = monitor.resolve_alert("nonexistent")

        assert result is False

    def test_evaluate_metrics(self):
        """Test evaluating metrics against rules"""
        monitor = OperationsMonitor(auto_collect=False)

        rule = AlertRule(
            name="high_cpu",
            condition=lambda m: m.get("cpu_percent", 0) > 90,
            severity=AlertSeverity.WARNING,
            message_template="High CPU: {cpu_percent}%",
        )
        monitor.add_alert_rule(rule)

        metrics = {"cpu_percent": 95}
        alerts = monitor.evaluate_metrics(metrics)

        assert len(alerts) == 1
        assert alerts[0].metadata["rule"] == "high_cpu"

    def test_get_active_alerts(self):
        """Test getting active alerts"""
        monitor = OperationsMonitor(auto_collect=False)

        active_alert = Alert(
            id="active",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Active",
            timestamp=datetime.now(),
        )
        resolved_alert = Alert(
            id="resolved",
            severity=AlertSeverity.INFO,
            source="test",
            message="Resolved",
            timestamp=datetime.now(),
        )
        resolved_alert.resolve()

        monitor.alerts.extend([active_alert, resolved_alert])

        active = monitor.get_active_alerts()
        assert len(active) == 1
        assert active[0].id == "active"

    def test_get_overall_health(self):
        """Test getting overall health status"""
        monitor = OperationsMonitor(auto_collect=False)

        monitor.register_health_check("healthy", lambda: HealthCheckResult(
            component="healthy", healthy=True, message="OK", timestamp=datetime.now()
        ))

        health = monitor.get_overall_health()
        assert health is True

    def test_get_overall_health_with_failure(self):
        """Test overall health with failing check"""
        monitor = OperationsMonitor(auto_collect=False)

        monitor.register_health_check("failing", lambda: HealthCheckResult(
            component="failing", healthy=False, message="Failed", timestamp=datetime.now()
        ))

        health = monitor.get_overall_health()
        assert health is False

    def test_get_monitoring_summary(self):
        """Test getting monitoring summary"""
        monitor = OperationsMonitor(auto_collect=False)

        monitor.register_health_check("check1", lambda: HealthCheckResult(
            component="c1", healthy=True, message="OK", timestamp=datetime.now()
        ))

        summary = monitor.get_monitoring_summary()

        assert isinstance(summary, dict)
        assert "timestamp" in summary
        assert "overall_healthy" in summary
        assert "components" in summary
        assert "alerts" in summary
        assert "health_checks" in summary

    def test_get_statistics(self):
        """Test getting monitoring statistics"""
        monitor = OperationsMonitor(auto_collect=False)

        stats = monitor.get_statistics()

        assert isinstance(stats, dict)
        assert "total_alerts" in stats
        assert "active_alerts" in stats
        assert "resolved_alerts" in stats
        assert "metrics_count" in stats
        assert "auto_collecting" in stats

    def test_start_and_stop_collection(self):
        """Test starting and stopping collection"""
        monitor = OperationsMonitor(auto_collect=False)

        monitor.start_collection()
        # Give thread time to start
        time.sleep(0.1)

        assert monitor._collect_thread is not None

        monitor.stop_collection()
        # Thread should be stopped
        assert monitor._collect_thread is None


class TestGlobalMonitorFunctions:
    """Test global monitor functions"""

    def test_get_global_monitor_singleton(self):
        """Test that get_global_monitor returns singleton"""
        monitor1 = get_global_monitor()
        monitor2 = get_global_monitor()

        assert monitor1 is monitor2

    def test_get_operations_monitor_alias(self):
        """Test that get_operations_monitor is an alias"""
        monitor1 = get_operations_monitor()
        monitor2 = get_global_monitor()

        assert monitor1 is monitor2

    def test_register_health_check_global(self):
        """Test global register_health_check function"""
        # Clear any existing instance
        import lingflow.monitoring.operations_monitor as ops
        ops._global_monitor = None

        def test_check():
            return HealthCheckResult(
                component="test", healthy=True, message="OK", timestamp=datetime.now()
            )

        register_health_check("global_test", test_check)

        monitor = get_global_monitor()
        assert "global_test" in monitor.health_collector.checks

    def test_add_alert_rule_global(self):
        """Test global add_alert_rule function"""
        # Clear instance
        import lingflow.monitoring.operations_monitor as ops
        ops._global_monitor = None

        rule = AlertRule(
            name="global_rule",
            condition=lambda m: True,
            severity=AlertSeverity.INFO,
            message_template="Test",
        )

        add_alert_rule(rule)

        monitor = get_global_monitor()
        assert "global_rule" in monitor.rule_registry._rules

    def test_run_health_checks_global(self):
        """Test global run_health_checks function"""
        # Clear instance
        import lingflow.monitoring.operations_monitor as ops
        ops._global_monitor = None

        results = run_health_checks()
        assert isinstance(results, dict)

    def test_get_active_alerts_global(self):
        """Test global get_active_alerts function"""
        # Clear instance
        import lingflow.monitoring.operations_monitor as ops
        ops._global_monitor = None

        alerts = get_active_alerts()
        assert isinstance(alerts, list)

    def test_get_monitoring_summary_global(self):
        """Test global get_monitoring_summary function"""
        # Clear instance
        import lingflow.monitoring.operations_monitor as ops
        ops._global_monitor = None

        summary = get_monitoring_summary()
        assert isinstance(summary, dict)
