"""Tests for Operations Monitor Module

Tests the integrated operations monitoring system.
"""

import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from lingflow.monitoring.operations_monitor import (
    Alert,
    AlertRule,
    AlertSeverity,
    HealthCheckResult,
    OperationsMonitor,
    get_operations_monitor,
    register_health_check,
    add_alert_rule,
    run_health_checks,
    evaluate_all_metrics,
    get_active_alerts,
    get_monitoring_summary,
)
from lingflow.monitoring.default_checks import (
    check_skill_loader,
    check_memory_usage,
    check_disk_usage,
    check_cpu_usage,
    register_default_checks,
    register_default_handlers,
    setup_default_monitoring,
)


class TestHealthCheckResult(unittest.TestCase):
    """Tests for HealthCheckResult"""

    def test_creation(self):
        """Test creating a health check result"""
        result = HealthCheckResult(
            component="test",
            healthy=True,
            message="OK",
            timestamp=None,
            metrics={"key": "value"},
        )
        self.assertEqual(result.component, "test")
        self.assertTrue(result.healthy)
        self.assertEqual(result.message, "OK")
        self.assertEqual(result.metrics, {"key": "value"})


class TestAlert(unittest.TestCase):
    """Tests for Alert"""

    def test_creation(self):
        """Test creating an alert"""
        alert = Alert(
            id="test-1",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Test alert",
            timestamp=None,
        )
        self.assertEqual(alert.id, "test-1")
        self.assertEqual(alert.severity, AlertSeverity.WARNING)
        self.assertFalse(alert.resolved)

    def test_resolve(self):
        """Test resolving an alert"""
        alert = Alert(
            id="test-1",
            severity=AlertSeverity.ERROR,
            source="test",
            message="Test alert",
            timestamp=None,
        )
        alert.resolved = True
        alert.resolved_at = time.time()

        self.assertTrue(alert.resolved)
        self.assertIsNotNone(alert.resolved_at)


class TestAlertRule(unittest.TestCase):
    """Tests for AlertRule"""

    def test_should_trigger(self):
        """Test alert rule triggering"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 10,
            severity=AlertSeverity.WARNING,
            message_template="Value {value} exceeded",
            cooldown_seconds=0,
        )

        # Should trigger
        self.assertTrue(rule.should_trigger({"value": 15}))

        # Should not trigger
        self.assertFalse(rule.should_trigger({"value": 5}))

    def test_cooldown(self):
        """Test alert rule cooldown"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 10,
            severity=AlertSeverity.WARNING,
            message_template="Value {value} exceeded",
            cooldown_seconds=10,  # 10 seconds cooldown
        )

        # First trigger
        self.assertTrue(rule.should_trigger({"value": 15}))
        self.assertIsNotNone(rule.last_triggered)

        # Second trigger within cooldown (should not trigger)
        self.assertFalse(rule.should_trigger({"value": 15}))

    def test_format_message(self):
        """Test message formatting"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            severity=AlertSeverity.WARNING,
            message_template="Component {name} has value {value}",
            cooldown_seconds=0,
        )

        message = rule.format_message({"name": "test", "value": 42})
        self.assertEqual(message, "Component test has value 42")


class TestOperationsMonitor(unittest.TestCase):
    """Tests for OperationsMonitor"""

    def setUp(self):
        """Create a fresh monitor for each test"""
        self.monitor = OperationsMonitor()

    def test_singleton(self):
        """Test that get_operations_monitor returns a singleton"""
        monitor1 = get_operations_monitor()
        monitor2 = get_operations_monitor()
        self.assertIs(monitor1, monitor2)

    def test_register_health_check(self):
        """Test registering a health check"""
        def check_func():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="OK",
                timestamp=None,
            )

        self.monitor.register_health_check("test", check_func)
        self.assertIn("test", self.monitor._health_checks)

    def test_unregister_health_check(self):
        """Test unregistering a health check"""
        def check_func():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="OK",
                timestamp=None,
            )

        self.monitor.register_health_check("test", check_func)
        self.assertIn("test", self.monitor._health_checks)

        self.monitor.unregister_health_check("test")
        self.assertNotIn("test", self.monitor._health_checks)

    def test_run_health_checks(self):
        """Test running all health checks"""
        def check_func():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="OK",
                timestamp=None,
            )

        self.monitor.register_health_check("test", check_func)
        results = self.monitor.run_health_checks()

        self.assertIn("test", results)
        self.assertTrue(results["test"].healthy)

    def test_add_alert_rule(self):
        """Test adding an alert rule"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            severity=AlertSeverity.WARNING,
            message_template="Test",
            cooldown_seconds=0,
        )

        self.monitor.add_alert_rule(rule)
        self.assertEqual(len(self.monitor._alert_rules), 5)  # 4 default + 1 new

    def test_remove_alert_rule(self):
        """Test removing an alert rule"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            severity=AlertSeverity.WARNING,
            message_template="Test",
            cooldown_seconds=0,
        )

        self.monitor.add_alert_rule(rule)
        self.assertIn("test_rule", [r.name for r in self.monitor._alert_rules])

        self.monitor.remove_alert_rule("test_rule")
        self.assertNotIn("test_rule", [r.name for r in self.monitor._alert_rules])

    def test_evaluate_metrics_no_alert(self):
        """Test evaluating metrics that don't trigger alerts"""
        alerts = self.monitor.evaluate_metrics({"value": 5})
        self.assertEqual(len(alerts), 0)

    def test_evaluate_metrics_with_alert(self):
        """Test evaluating metrics that trigger an alert"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 10,
            severity=AlertSeverity.WARNING,
            message_template="Value {value} exceeded",
            cooldown_seconds=0,
        )

        self.monitor.add_alert_rule(rule)
        alerts = self.monitor.evaluate_metrics({"value": 15})

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, AlertSeverity.WARNING)

    def test_resolve_alert(self):
        """Test resolving an alert"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 10,
            severity=AlertSeverity.WARNING,
            message_template="Value {value} exceeded",
            cooldown_seconds=0,
        )

        self.monitor.add_alert_rule(rule)
        self.monitor.evaluate_metrics({"value": 15})

        active_alerts = self.monitor.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)

        alert_id = active_alerts[0].id
        self.assertTrue(self.monitor.resolve_alert(alert_id))

        # Alert should no longer be active
        active_alerts = self.monitor.get_active_alerts()
        self.assertEqual(len(active_alerts), 0)

    def test_get_active_alerts(self):
        """Test getting active alerts"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 10,
            severity=AlertSeverity.WARNING,
            message_template="Value {value} exceeded",
            cooldown_seconds=0,
        )

        self.monitor.add_alert_rule(rule)
        self.monitor.evaluate_metrics({"value": 15})

        active_alerts = self.monitor.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)

    def test_get_component_status(self):
        """Test getting component status"""
        def check_func():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="OK",
                timestamp=None,
            )

        self.monitor.register_health_check("test", check_func)
        self.monitor.run_health_checks()

        status = self.monitor.get_component_status()
        self.assertTrue(status.get("test", False))

    def test_get_overall_health(self):
        """Test getting overall health status"""
        # No components = healthy
        self.assertTrue(self.monitor.get_overall_health())

        # Add healthy component
        def check_func():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="OK",
                timestamp=None,
            )

        self.monitor.register_health_check("test", check_func)
        self.monitor.run_health_checks()
        self.assertTrue(self.monitor.get_overall_health())

    def test_get_monitoring_summary(self):
        """Test getting monitoring summary"""
        summary = self.monitor.get_monitoring_summary()

        self.assertIn("timestamp", summary)
        self.assertIn("overall_healthy", summary)
        self.assertIn("components", summary)
        self.assertIn("alerts", summary)
        self.assertIn("health_checks", summary)


class TestDefaultChecks(unittest.TestCase):
    """Tests for default health checks"""

    @patch('lingflow.monitoring.default_checks.get_layered_loader')
    @patch('lingflow.monitoring.default_checks.get_memory_usage')
    def test_check_skill_loader(self, mock_memory, mock_loader):
        """Test skill loader health check"""
        mock_loader.return_value.get_layer_stats.return_value = {
            "L1": {"total": 5, "loaded": 5},
            "L2": {"total": 12, "loaded": 12},
            "L3": {"total": 16, "loaded": 2},
        }
        mock_memory.return_value = {
            "total_cached": 20,
            "l3_active": 5,
            "target_l3_max": 15,
        }

        result = check_skill_loader()

        self.assertEqual(result.component, "skill_loader")
        self.assertTrue(result.healthy)
        self.assertIn("正常", result.message)

    @patch('lingflow.monitoring.default_checks.psutil.Process')
    def test_check_memory_usage(self, mock_process):
        """Test memory usage health check"""
        mock_proc = Mock()
        mock_proc.memory_percent.return_value = 50
        mock_proc.memory_info.return_value.rss = 1024 * 1024 * 100  # 100MB
        mock_process.return_value = mock_proc

        result = check_memory_usage()

        self.assertEqual(result.component, "memory")
        self.assertTrue(result.healthy)
        self.assertIn("正常", result.message)

    @patch('lingflow.monitoring.default_checks.psutil.disk_usage')
    def test_check_disk_usage(self, mock_disk):
        """Test disk usage health check"""
        mock_usage = Mock()
        mock_usage.used = 100 * 1024 * 1024 * 1024  # 100GB
        mock_usage.total = 500 * 1024 * 1024 * 1024  # 500GB
        mock_usage.free = 400 * 1024 * 1024 * 1024  # 400GB
        mock_disk.return_value = mock_usage

        result = check_disk_usage()

        self.assertEqual(result.component, "disk")
        self.assertTrue(result.healthy)

    @patch('lingflow.monitoring.default_checks.psutil.cpu_percent')
    def test_check_cpu_usage(self, mock_cpu):
        """Test CPU usage health check"""
        mock_cpu.return_value = 30

        result = check_cpu_usage()

        self.assertEqual(result.component, "cpu")
        self.assertTrue(result.healthy)


class TestGlobalFunctions(unittest.TestCase):
    """Tests for global convenience functions"""

    def test_register_health_check(self):
        """Test global register_health_check function"""
        def check_func():
            return HealthCheckResult(
                component="test_global",
                healthy=True,
                message="OK",
                timestamp=None,
            )

        register_health_check("test_global", check_func)
        monitor = get_operations_monitor()
        self.assertIn("test_global", monitor._health_checks)

    def test_run_health_checks(self):
        """Test global run_health_checks function"""
        results = run_health_checks()
        self.assertIsInstance(results, dict)


if __name__ == "__main__":
    unittest.main()
