"""Tests for lingflow.monitoring.collectors.base module"""

import time
from datetime import datetime

import pytest

from lingflow.monitoring.collectors.base import HealthCheckCollector, MetricCollector
from lingflow.monitoring.metrics.models import HealthCheckResult, SystemMetrics


class TestMetricCollector:
    """Test MetricCollector class"""

    def test_init(self):
        """Test initialization"""
        collector = MetricCollector()
        assert collector.available is True or collector.available is False

    def test_collect_system_metrics(self):
        """Test collecting system metrics"""
        collector = MetricCollector()
        metrics = collector.collect_system_metrics()

        assert isinstance(metrics, SystemMetrics)
        assert isinstance(metrics.cpu_percent, float)
        assert isinstance(metrics.memory_percent, float)
        assert isinstance(metrics.disk_usage_percent, float)
        assert isinstance(metrics.timestamp, datetime)

    def test_collect_system_metrics_returns_valid_ranges(self):
        """Test that collected metrics are within valid ranges"""
        collector = MetricCollector()
        metrics = collector.collect_system_metrics()

        # CPU and memory should be between 0 and 100
        assert 0 <= metrics.cpu_percent <= 100
        assert 0 <= metrics.memory_percent <= 100
        assert 0 <= metrics.disk_usage_percent <= 100

        # Memory and disk values should be positive
        assert metrics.memory_used_mb >= 0
        assert metrics.memory_available_mb >= 0
        assert metrics.disk_used_gb >= 0
        assert metrics.disk_free_gb >= 0

    def test_collect_process_metrics(self):
        """Test collecting process metrics"""
        collector = MetricCollector()
        metrics = collector.collect_process_metrics()

        assert isinstance(metrics, dict)

    def test_collect_process_metrics_with_specific_pid(self):
        """Test collecting metrics for specific PID"""
        collector = MetricCollector()
        import os

        current_pid = os.getpid()

        metrics = collector.collect_process_metrics(pid=current_pid)

        assert isinstance(metrics, dict)

    def test_collect_system_metrics_structure(self):
        """Test structure of collected system metrics"""
        collector = MetricCollector()
        metrics = collector.collect_system_metrics()

        # Check that all expected fields exist
        assert hasattr(metrics, "cpu_percent")
        assert hasattr(metrics, "memory_percent")
        assert hasattr(metrics, "memory_used_mb")
        assert hasattr(metrics, "memory_available_mb")
        assert hasattr(metrics, "disk_usage_percent")
        assert hasattr(metrics, "disk_used_gb")
        assert hasattr(metrics, "disk_free_gb")
        assert hasattr(metrics, "network_io")
        assert hasattr(metrics, "process_count")
        assert hasattr(metrics, "timestamp")


class TestHealthCheckCollector:
    """Test HealthCheckCollector class"""

    def test_init(self):
        """Test initialization"""
        collector = HealthCheckCollector()
        assert collector.checks == {}

    def test_register_check(self):
        """Test registering a health check"""
        collector = HealthCheckCollector()

        def dummy_check():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="OK",
                timestamp=datetime.now(),
            )

        collector.register_check("test_check", dummy_check)

        assert "test_check" in collector.checks
        assert collector.checks["test_check"] == dummy_check

    def test_register_multiple_checks(self):
        """Test registering multiple health checks"""
        collector = HealthCheckCollector()

        for i in range(3):
            collector.register_check(f"check_{i}", lambda: None)

        assert len(collector.checks) == 3

    def test_run_check_exists(self):
        """Test running an existing check"""
        collector = HealthCheckCollector()

        def test_check():
            return HealthCheckResult(
                component="test",
                healthy=True,
                message="Test passed",
                timestamp=datetime.now(),
            )

        collector.register_check("test", test_check)
        result = collector.run_check("test")

        assert isinstance(result, HealthCheckResult)
        assert result.component == "test"
        assert result.healthy is True

    def test_run_check_not_exists(self):
        """Test running a non-existent check"""
        collector = HealthCheckCollector()
        result = collector.run_check("nonexistent")

        assert result is None

    def test_run_check_with_exception(self):
        """Test running a check that raises an exception"""
        collector = HealthCheckCollector()

        def failing_check():
            raise ValueError("Test error")

        collector.register_check("failing", failing_check)
        result = collector.run_check("failing")

        # Should return None on exception
        assert result is None

    def test_run_all_checks_empty(self):
        """Test running all checks when none are registered"""
        collector = HealthCheckCollector()
        results = collector.run_all_checks()

        assert results == {}

    def test_run_all_checks_multiple(self):
        """Test running all registered checks"""
        collector = HealthCheckCollector()

        collector.register_check(
            "check1", lambda: HealthCheckResult(component="c1", healthy=True, message="OK", timestamp=datetime.now())
        )
        collector.register_check(
            "check2", lambda: HealthCheckResult(component="c2", healthy=False, message="Failed", timestamp=datetime.now())
        )

        results = collector.run_all_checks()

        assert len(results) == 2
        assert "check1" in results
        assert "check2" in results
        assert results["check1"].healthy is True
        assert results["check2"].healthy is False

    def test_run_all_checks_with_exception(self):
        """Test running all checks when one raises exception"""
        collector = HealthCheckCollector()

        collector.register_check(
            "good", lambda: HealthCheckResult(component="good", healthy=True, message="OK", timestamp=datetime.now())
        )
        collector.register_check("bad", lambda: (_ for _ in ()).throw(ValueError("Error")))

        results = collector.run_all_checks()

        # Should return results for successful checks
        assert "good" in results
        # Failed check should not be in results
        assert "bad" not in results

    def test_check_disk_space(self):
        """Test disk space health check"""
        collector = HealthCheckCollector()
        result = collector.check_disk_space()

        assert isinstance(result, HealthCheckResult)
        assert "disk" in result.component
        assert isinstance(result.healthy, bool)
        assert isinstance(result.metrics, dict)
        assert "percent" in result.metrics
        assert "total_gb" in result.metrics
        assert "used_gb" in result.metrics
        assert "free_gb" in result.metrics

    def test_check_disk_space_custom_threshold(self):
        """Test disk space check with custom threshold"""
        collector = HealthCheckCollector()
        result = collector.check_disk_space(threshold=50.0)

        assert isinstance(result, HealthCheckResult)
        # Healthy depends on actual disk usage

    def test_check_disk_space_custom_path(self):
        """Test disk space check for custom path"""
        collector = HealthCheckCollector()
        result = collector.check_disk_space(path="/tmp")

        assert isinstance(result, HealthCheckResult)
        assert "/tmp" in result.component or "tmp" in result.component

    def test_check_memory(self):
        """Test memory health check"""
        collector = HealthCheckCollector()
        result = collector.check_memory()

        assert isinstance(result, HealthCheckResult)
        assert result.component == "memory"
        assert isinstance(result.healthy, bool)
        assert isinstance(result.metrics, dict)

    def test_check_memory_custom_threshold(self):
        """Test memory check with custom threshold"""
        collector = HealthCheckCollector()
        result = collector.check_memory(threshold=50.0)

        assert isinstance(result, HealthCheckResult)

    def test_check_response_time(self):
        """Test that health checks measure response time"""
        collector = HealthCheckCollector()

        def slow_check():
            time.sleep(0.01)
            return HealthCheckResult(component="slow", healthy=True, message="OK", timestamp=datetime.now())

        collector.register_check("slow", slow_check)
        result = collector.run_check("slow")

        assert isinstance(result, HealthCheckResult)
        assert result.response_time_ms >= 0

    def test_check_disk_space_response_time(self):
        """Test disk space check includes response time"""
        collector = HealthCheckCollector()
        result = collector.check_disk_space()

        assert isinstance(result.response_time_ms, float)
        assert result.response_time_ms >= 0


class TestHealthCheckCollectorIntegration:
    """Test HealthCheckCollector integration scenarios"""

    def test_comprehensive_health_check(self):
        """Test comprehensive health check scenario"""
        collector = HealthCheckCollector()

        # Register various checks
        collector.register_check("disk", lambda: collector.check_disk_space())
        collector.register_check("memory", lambda: collector.check_memory())

        results = collector.run_all_checks()

        assert len(results) == 2
        assert all(isinstance(r, HealthCheckResult) for r in results.values())

    def test_healthy_overall_assessment(self):
        """Test assessing overall health from checks"""
        collector = HealthCheckCollector()

        collector.register_check(
            "c1", lambda: HealthCheckResult(component="c1", healthy=True, message="OK", timestamp=datetime.now())
        )
        collector.register_check(
            "c2", lambda: HealthCheckResult(component="c2", healthy=True, message="OK", timestamp=datetime.now())
        )

        results = collector.run_all_checks()
        all_healthy = all(r.healthy for r in results.values())

        assert all_healthy is True

    def test_unhealthy_overall_assessment(self):
        """Test overall health when one check fails"""
        collector = HealthCheckCollector()

        collector.register_check(
            "good", lambda: HealthCheckResult(component="good", healthy=True, message="OK", timestamp=datetime.now())
        )
        collector.register_check(
            "bad", lambda: HealthCheckResult(component="bad", healthy=False, message="Failed", timestamp=datetime.now())
        )

        results = collector.run_all_checks()
        all_healthy = all(r.healthy for r in results.values())

        assert all_healthy is False
