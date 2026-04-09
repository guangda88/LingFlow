import threading
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from lingflow.monitoring.alerts.rules import AlertRule
from lingflow.monitoring.metrics.models import Alert, AlertSeverity, HealthCheckResult, SystemMetrics
from lingflow.monitoring.operations_monitor import (
    OperationsMonitor,
    add_alert_rule,
    add_notification_handler,
    evaluate_all_metrics,
    get_active_alerts,
    get_global_monitor,
    get_monitoring_summary,
    get_operations_monitor,
    register_health_check,
    run_health_checks,
)


def _make_metrics(cpu=50.0, mem=60.0, disk=70.0):
    return SystemMetrics(
        cpu_percent=cpu,
        memory_percent=mem,
        memory_used_mb=1000.0,
        memory_available_mb=2000.0,
        disk_usage_percent=disk,
        disk_used_gb=50.0,
        disk_free_gb=100.0,
    )


def _make_alert(aid="a1", severity=AlertSeverity.WARNING, msg="test", resolved=False):
    alert = Alert(
        id=aid,
        severity=severity,
        source="test",
        message=msg,
        timestamp=datetime.now(),
    )
    if resolved:
        alert.resolve()
    return alert


def _make_rule(name="test_rule", condition=None, severity=AlertSeverity.WARNING):
    return AlertRule(
        name=name,
        condition=condition or (lambda m: m.get("cpu_percent", 0) > 90),
        severity=severity,
        message_template="Test alert: {cpu_percent}",
    )


class TestOperationsMonitorInit:
    def test_init_no_auto_collect(self):
        m = OperationsMonitor(auto_collect=False)
        assert m.auto_collect is False
        assert m._collect_thread is None
        m.stop_collection()

    def test_init_with_auto_collect(self):
        m = OperationsMonitor(auto_collect=True, collect_interval=1)
        assert m._collect_thread is not None
        assert m._collect_thread.daemon is True
        m.stop_collection()

    def test_default_components_initialized(self):
        m = OperationsMonitor(auto_collect=False)
        assert m.metric_collector is not None
        assert m.health_collector is not None
        assert m.rule_registry is not None
        assert m.perf_monitor is None
        assert m.alerts == []
        assert m.metrics_history == []

    def test_default_health_checks_registered(self):
        m = OperationsMonitor(auto_collect=False)
        assert "disk_space" in m.health_collector.checks
        assert "memory" in m.health_collector.checks

    def test_default_alert_rules_registered(self):
        m = OperationsMonitor(auto_collect=False)
        rules = m.rule_registry.get_all()
        assert "high_cpu" in rules
        assert "high_memory" in rules
        assert "high_disk" in rules
        assert "critical_cpu" in rules
        assert "critical_memory" in rules


class TestStartStopCollection:
    def test_start_creates_daemon_thread(self):
        m = OperationsMonitor(auto_collect=False)
        m.start_collection()
        assert m._collect_thread is not None
        assert m._collect_thread.daemon is True
        m.stop_collection()

    def test_start_twice_logs_warning(self):
        m = OperationsMonitor(auto_collect=False)
        m.start_collection()
        old_thread = m._collect_thread
        m.start_collection()
        assert m._collect_thread is old_thread
        m.stop_collection()

    def test_stop_sets_thread_none(self):
        m = OperationsMonitor(auto_collect=False)
        m.start_collection()
        m.stop_collection()
        assert m._collect_thread is None

    def test_stop_without_start_is_noop(self):
        m = OperationsMonitor(auto_collect=False)
        m.stop_collection()
        assert m._collect_thread is None

    def test_collect_loop_collects_metrics(self):
        m = OperationsMonitor(auto_collect=False)
        m.start_collection()
        time.sleep(0.3)
        m.stop_collection()
        assert len(m.metrics_history) >= 1


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

    def test_get_current_metrics_returns_last(self):
        m = OperationsMonitor(auto_collect=False)
        m.add_metrics(_make_metrics(cpu=10.0))
        m.add_metrics(_make_metrics(cpu=20.0))
        assert m.get_current_metrics().cpu_percent == 20.0

    def test_get_metrics_history_default_limit(self):
        m = OperationsMonitor(auto_collect=False)
        for i in range(5):
            m.add_metrics(_make_metrics(cpu=float(i)))
        history = m.get_metrics_history()
        assert len(history) == 5

    def test_get_metrics_history_custom_limit(self):
        m = OperationsMonitor(auto_collect=False)
        for i in range(10):
            m.add_metrics(_make_metrics(cpu=float(i)))
        history = m.get_metrics_history(limit=3)
        assert len(history) == 3
        assert history[0].cpu_percent == 7.0
        assert history[2].cpu_percent == 9.0

    def test_get_metrics_history_empty(self):
        m = OperationsMonitor(auto_collect=False)
        assert m.get_metrics_history() == []

    def test_metrics_history_eviction_at_1000(self):
        m = OperationsMonitor(auto_collect=False)
        for i in range(1100):
            m.add_metrics(_make_metrics(cpu=float(i)))
        assert len(m.metrics_history) == 1000
        assert m.metrics_history[0].cpu_percent == 100.0

    def test_add_metrics_thread_safety(self):
        m = OperationsMonitor(auto_collect=False)
        errors = []

        def add_many():
            try:
                for i in range(100):
                    m.add_metrics(_make_metrics(cpu=float(i)))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_many) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(m.metrics_history) == 500


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
            m.alerts.extend(
                [
                    _make_alert(aid="a1", severity=AlertSeverity.WARNING),
                    _make_alert(aid="a2", severity=AlertSeverity.CRITICAL),
                ]
            )
        warnings = m.get_alerts(severity=AlertSeverity.WARNING)
        assert len(warnings) == 1
        critical = m.get_alerts(severity=AlertSeverity.CRITICAL)
        assert len(critical) == 1

    def test_get_alerts_by_resolved(self):
        m = OperationsMonitor(auto_collect=False)
        with m._alerts_lock:
            m.alerts.extend(
                [
                    _make_alert(aid="a1", resolved=False),
                    _make_alert(aid="a2", resolved=True),
                ]
            )
        active = m.get_alerts(resolved=False)
        assert len(active) == 1
        assert active[0].id == "a1"
        resolved = m.get_alerts(resolved=True)
        assert len(resolved) == 1
        assert resolved[0].id == "a2"

    def test_get_alerts_with_limit(self):
        m = OperationsMonitor(auto_collect=False)
        with m._alerts_lock:
            for i in range(10):
                m.alerts.append(_make_alert(aid=f"a{i}"))
        limited = m.get_alerts(limit=3)
        assert len(limited) == 3

    def test_get_alerts_combined_filters(self):
        m = OperationsMonitor(auto_collect=False)
        with m._alerts_lock:
            m.alerts.extend(
                [
                    _make_alert(aid="a1", severity=AlertSeverity.WARNING, resolved=False),
                    _make_alert(aid="a2", severity=AlertSeverity.WARNING, resolved=True),
                    _make_alert(aid="a3", severity=AlertSeverity.CRITICAL, resolved=False),
                ]
            )
        result = m.get_alerts(severity=AlertSeverity.WARNING, resolved=False)
        assert len(result) == 1
        assert result[0].id == "a1"

    def test_resolve_alert(self):
        m = OperationsMonitor(auto_collect=False)
        with m._alerts_lock:
            m.alerts.append(_make_alert(aid="a1"))
        assert m.resolve_alert("a1") is True
        assert m.resolve_alert("nonexistent") is False

    def test_resolve_already_resolved_alert(self):
        m = OperationsMonitor(auto_collect=False)
        a = _make_alert(aid="a1")
        a.resolve()
        with m._alerts_lock:
            m.alerts.append(a)
        assert m.resolve_alert("a1") is False

    def test_get_active_alerts(self):
        m = OperationsMonitor(auto_collect=False)
        a1 = _make_alert(aid="a1")
        a2 = _make_alert(aid="a2")
        a2.resolve()
        with m._alerts_lock:
            m.alerts.extend([a1, a2])
        active = m.get_active_alerts()
        assert len(active) == 1
        assert active[0].id == "a1"

    def test_evaluate_metrics_with_high_cpu(self):
        m = OperationsMonitor(auto_collect=False)
        alerts = m.evaluate_metrics({"cpu_percent": 96.0, "memory_percent": 50.0, "disk_usage_percent": 50.0})
        assert len(alerts) >= 1
        assert any("cpu" in a.message.lower() or "CPU" in a.message for a in alerts)

    def test_evaluate_metrics_healthy(self):
        m = OperationsMonitor(auto_collect=False)
        alerts = m.evaluate_metrics({"cpu_percent": 10.0, "memory_percent": 20.0, "disk_usage_percent": 30.0})
        assert len(alerts) == 0

    def test_evaluate_metrics_adds_to_alerts_list(self):
        m = OperationsMonitor(auto_collect=False)
        m.evaluate_metrics({"cpu_percent": 96.0, "memory_percent": 50.0, "disk_usage_percent": 50.0})
        assert len(m.alerts) >= 1


class TestAlertRules:
    def test_add_alert_rule(self):
        m = OperationsMonitor(auto_collect=False)
        rule = _make_rule("custom_rule")
        m.add_alert_rule(rule)
        assert m.rule_registry.get("custom_rule") is not None

    def test_remove_alert_rule(self):
        m = OperationsMonitor(auto_collect=False)
        rule = _make_rule("custom_rule")
        m.add_alert_rule(rule)
        assert m.remove_alert_rule("custom_rule") is True
        assert m.remove_alert_rule("nonexistent") is False

    def test_register_alert_rule_alias(self):
        m = OperationsMonitor(auto_collect=False)
        rule = _make_rule("alias_rule")
        m.register_alert_rule(rule)
        assert m.rule_registry.get("alias_rule") is not None

    def test_unregister_alert_rule_alias(self):
        m = OperationsMonitor(auto_collect=False)
        rule = _make_rule("alias_rule")
        m.register_alert_rule(rule)
        assert m.unregister_alert_rule("alias_rule") is True
        assert m.unregister_alert_rule("nonexistent") is False


class TestHealthChecks:
    def test_register_and_run(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check(
            "test_check", lambda: HealthCheckResult(component="test", healthy=True, message="ok", timestamp=datetime.now())
        )
        assert "test_check" in m.health_collector.checks

    def test_unregister(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check("test_check", lambda: True)
        m.unregister_health_check("test_check")
        assert "test_check" not in m.health_collector.checks

    def test_run_single_health_check(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check(
            "test_check", lambda: HealthCheckResult(component="test", healthy=True, message="ok", timestamp=datetime.now())
        )
        result = m.run_health_check("test_check")
        assert result is not None
        assert result.healthy is True

    def test_run_nonexistent_health_check(self):
        m = OperationsMonitor(auto_collect=False)
        assert m.run_health_check("nonexistent") is None

    def test_run_all_health_checks(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check(
            "check1", lambda: HealthCheckResult(component="c1", healthy=True, message="ok", timestamp=datetime.now())
        )
        m.register_health_check(
            "check2", lambda: HealthCheckResult(component="c2", healthy=False, message="bad", timestamp=datetime.now())
        )
        results = m.run_health_checks()
        assert len(results) == 4
        assert results["check1"].healthy is True
        assert results["check2"].healthy is False

    def test_run_all_health_checks_alias(self):
        m = OperationsMonitor(auto_collect=False)
        results = m.run_all_health_checks()
        assert isinstance(results, dict)

    def test_failing_check_handled(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check("bad_check", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
        results = m.run_health_checks()
        assert "bad_check" not in results

    def test_get_component_status(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check(
            "c1", lambda: HealthCheckResult(component="c1", healthy=True, message="ok", timestamp=datetime.now())
        )
        m.register_health_check(
            "c2", lambda: HealthCheckResult(component="c2", healthy=False, message="bad", timestamp=datetime.now())
        )
        status = m.get_component_status()
        assert status["c1"] is True
        assert status["c2"] is False

    def test_get_overall_health_all_healthy(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check(
            "c1", lambda: HealthCheckResult(component="c1", healthy=True, message="ok", timestamp=datetime.now())
        )
        assert m.get_overall_health() is True

    def test_get_overall_health_unhealthy(self):
        m = OperationsMonitor(auto_collect=False)
        m.register_health_check(
            "c1", lambda: HealthCheckResult(component="c1", healthy=False, message="bad", timestamp=datetime.now())
        )
        assert m.get_overall_health() is False

    def test_get_overall_health_no_checks(self):
        m = OperationsMonitor(auto_collect=False)
        m.health_collector.checks.clear()
        assert m.get_overall_health() is True


class TestStatistics:
    def test_get_statistics(self):
        m = OperationsMonitor(auto_collect=False)
        stats = m.get_statistics()
        assert "total_alerts" in stats
        assert "active_alerts" in stats
        assert "metrics_count" in stats
        assert "auto_collecting" in stats

    def test_statistics_counts(self):
        m = OperationsMonitor(auto_collect=False)
        m.add_metrics(_make_metrics())
        with m._alerts_lock:
            m.alerts.append(_make_alert(aid="a1"))
        stats = m.get_statistics()
        assert stats["metrics_count"] == 1
        assert stats["total_alerts"] == 1
        assert stats["active_alerts"] == 1
        assert stats["auto_collecting"] is False

    def test_statistics_with_auto_collect(self):
        m = OperationsMonitor(auto_collect=True, collect_interval=60)
        stats = m.get_statistics()
        assert stats["auto_collecting"] is True
        m.stop_collection()

    def test_get_monitoring_summary(self):
        m = OperationsMonitor(auto_collect=False)
        summary = m.get_monitoring_summary()
        assert "timestamp" in summary
        assert "overall_healthy" in summary
        assert "alerts" in summary
        assert "components" in summary
        assert "health_checks" in summary
        assert isinstance(summary["alerts"], dict)
        assert "total" in summary["alerts"]
        assert "active" in summary["alerts"]

    def test_monitoring_summary_with_alerts(self):
        m = OperationsMonitor(auto_collect=False)
        with m._alerts_lock:
            m.alerts.append(_make_alert(aid="a1"))
        summary = m.get_monitoring_summary()
        assert summary["alerts"]["total"] == 1
        assert summary["alerts"]["active"] == 1


class TestBackwardCompatProperties:
    def test_health_checks_property(self):
        m = OperationsMonitor(auto_collect=False)
        assert m._health_checks is m.health_collector.checks

    def test_alert_rules_property(self):
        m = OperationsMonitor(auto_collect=False)
        rules = m._alert_rules
        assert isinstance(rules, list)
        assert len(rules) >= 5


class TestPerformanceMonitor:
    def test_set_performance_monitor(self):
        m = OperationsMonitor(auto_collect=False)
        mock = MagicMock()
        m.set_performance_monitor(mock)
        assert m.perf_monitor is mock

    def test_integrate_with_performance_monitor_no_existing(self):
        m = OperationsMonitor(auto_collect=False)
        with patch("lingflow.monitoring.operations_monitor.performance_monitor", "mock_perf"):
            m.integrate_with_performance_monitor()
            assert m.perf_monitor == "mock_perf"

    def test_integrate_with_performance_monitor_existing(self):
        m = OperationsMonitor(auto_collect=False)
        existing = MagicMock()
        m.perf_monitor = existing
        m.integrate_with_performance_monitor()
        assert m.perf_monitor is existing


class TestEvaluateAlertsPrivate:
    def test_evaluate_alerts_from_metrics(self):
        m = OperationsMonitor(auto_collect=False)
        metrics = _make_metrics(cpu=96.0, mem=50.0, disk=50.0)
        m._evaluate_alerts(metrics)
        assert len(m.alerts) >= 1


class TestModuleFunctions:
    def test_get_global_monitor(self):
        m = get_global_monitor()
        assert isinstance(m, OperationsMonitor)

    def test_get_operations_monitor(self):
        m = get_operations_monitor()
        assert isinstance(m, OperationsMonitor)

    def test_register_health_check_module(self):
        register_health_check(
            "module_test",
            lambda: HealthCheckResult(component="module_test", healthy=True, message="ok", timestamp=datetime.now()),
        )
        m = get_global_monitor()
        assert "module_test" in m.health_collector.checks

    def test_add_alert_rule_module(self):
        rule = _make_rule("module_rule")
        add_alert_rule(rule)
        m = get_global_monitor()
        assert m.rule_registry.get("module_rule") is not None

    def test_run_health_checks_module(self):
        results = run_health_checks()
        assert isinstance(results, dict)

    def test_evaluate_all_metrics_no_data(self):
        evaluate_all_metrics()

    def test_get_active_alerts_module(self):
        alerts = get_active_alerts()
        assert isinstance(alerts, list)

    def test_get_monitoring_summary_module(self):
        summary = get_monitoring_summary()
        assert isinstance(summary, dict)

    def test_add_notification_handler(self):
        handler = MagicMock()
        add_notification_handler(handler)
        m = get_global_monitor()
        assert m.perf_monitor is handler
