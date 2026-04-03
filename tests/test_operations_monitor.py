from datetime import datetime

from lingflow.monitoring.operations_monitor import OperationsMonitor
from lingflow.monitoring.metrics.models import Alert, AlertSeverity, SystemMetrics


def _make_metrics(cpu=50.0, mem=60.0):
    return SystemMetrics(
        cpu_percent=cpu,
        memory_percent=mem,
        memory_used_mb=1000.0,
        memory_available_mb=2000.0,
        disk_usage_percent=70.0,
        disk_used_gb=50.0,
        disk_free_gb=100.0,
    )


def _make_alert(aid="a1", severity=AlertSeverity.WARNING, msg="test"):
    return Alert(
        id=aid,
        severity=severity,
        source="test",
        message=msg,
        timestamp=datetime.now(),
    )


class TestOperationsMonitorInit:
    def test_init_no_auto_collect(self):
        m = OperationsMonitor(auto_collect=False)
        assert m.auto_collect is False
        m.stop_collection()

    def test_init_with_auto_collect(self):
        m = OperationsMonitor(auto_collect=True, collect_interval=1)
        assert m._collect_thread is not None
        m.stop_collection()


class TestMetrics:
    def test_add_metrics(self):
        m = OperationsMonitor(auto_collect=False)
        m.add_metrics(_make_metrics())
        current = m.get_current_metrics()
        assert current is not None
        assert current.cpu_percent == 50.0

    def test_get_current_metrics_empty(self):
        m = OperationsMonitor(auto_collect=False)
        assert m.get_current_metrics() is None

    def test_get_metrics_history(self):
        m = OperationsMonitor(auto_collect=False)
        for i in range(5):
            m.add_metrics(_make_metrics(cpu=float(i)))
        history = m.get_metrics_history(limit=3)
        assert len(history) == 3


class TestAlerts:
    def test_add_and_get_alerts(self):
        m = OperationsMonitor(auto_collect=False)
        with m._alerts_lock:
            m.alerts.append(_make_alert())
        alerts = m.get_alerts()
        assert len(alerts) == 1

    def test_get_alerts_by_severity(self):
        m = OperationsMonitor(auto_collect=False)
        with m._alerts_lock:
            m.alerts.extend([
                _make_alert(aid="a1", severity=AlertSeverity.WARNING),
                _make_alert(aid="a2", severity=AlertSeverity.CRITICAL),
            ])
        warnings = m.get_alerts(severity=AlertSeverity.WARNING)
        assert len(warnings) == 1

    def test_resolve_alert(self):
        m = OperationsMonitor(auto_collect=False)
        with m._alerts_lock:
            m.alerts.append(_make_alert(aid="a1"))
        assert m.resolve_alert("a1") is True
        assert m.resolve_alert("nonexistent") is False

    def test_get_active_alerts(self):
        m = OperationsMonitor(auto_collect=False)
        a1 = _make_alert(aid="a1")
        a2 = _make_alert(aid="a2")
        a2.resolve()
        with m._alerts_lock:
            m.alerts.extend([a1, a2])
        active = m.get_active_alerts()
        assert len(active) == 1

    def test_evaluate_metrics(self):
        m = OperationsMonitor(auto_collect=False)
        metrics = {"cpu_percent": 99.0, "memory_percent": 50.0}
        alerts = m.evaluate_metrics(metrics)
        assert isinstance(alerts, list)


class TestHealthChecks:
    def test_register_and_run(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check("test_check", lambda: True)
        assert "test_check" in m.health_collector.checks

    def test_unregister(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check("test_check", lambda: True)
        m.unregister_health_check("test_check")
        assert "test_check" not in m.health_collector.checks


class TestStatistics:
    def test_get_statistics(self):
        m = OperationsMonitor(auto_collect=False)
        stats = m.get_statistics()
        assert "total_alerts" in stats
        assert "active_alerts" in stats
        assert "metrics_count" in stats

    def test_get_monitoring_summary(self):
        m = OperationsMonitor(auto_collect=False)
        summary = m.get_monitoring_summary()
        assert "timestamp" in summary
        assert "overall_healthy" in summary
        assert "alerts" in summary
