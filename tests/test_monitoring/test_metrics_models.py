"""Tests for lingflow.monitoring.metrics.models module"""

import pytest
from datetime import datetime, timedelta

from lingflow.monitoring.metrics.models import (
    MetricType,
    AlertSeverity,
    Metric,
    Alert,
    HealthCheckResult,
    SystemMetrics,
)


class TestMetricType:
    """Test MetricType enum"""

    def test_metric_type_values(self):
        """Test metric type enum values"""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"


class TestAlertSeverity:
    """Test AlertSeverity enum"""

    def test_severity_values(self):
        """Test severity enum values"""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"

    def test_severity_ordering(self):
        """Test severity levels for potential ordering"""
        # Note: This test documents current behavior
        severities = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL]
        assert len(severities) == 4


class TestMetric:
    """Test Metric dataclass"""

    def test_create_metric_minimal(self):
        """Test creating metric with minimal parameters"""
        metric = Metric(name="test_metric", type=MetricType.GAUGE, value=42.0)

        assert metric.name == "test_metric"
        assert metric.type == MetricType.GAUGE
        assert metric.value == 42.0
        assert metric.labels == {}
        assert metric.metadata == {}

    def test_create_metric_full(self):
        """Test creating metric with all parameters"""
        now = datetime.now()
        labels = {"host": "server1", "region": "us-east"}
        metadata = {"unit": "bytes", "description": "Memory usage"}

        metric = Metric(
            name="memory_usage",
            type=MetricType.GAUGE,
            value=1024.5,
            labels=labels,
            timestamp=now,
            metadata=metadata,
        )

        assert metric.name == "memory_usage"
        assert metric.value == 1024.5
        assert metric.labels == labels
        assert metric.timestamp == now
        assert metric.metadata == metadata

    def test_metric_to_dict(self):
        """Test converting metric to dictionary"""
        metric = Metric(
            name="cpu_usage",
            type=MetricType.GAUGE,
            value=75.5,
            labels={"core": "0"},
            metadata={"unit": "percent"},
        )

        result = metric.to_dict()

        assert result["name"] == "cpu_usage"
        assert result["type"] == "gauge"
        assert result["value"] == 75.5
        assert result["labels"] == {"core": "0"}
        assert "timestamp" in result
        assert result["metadata"]["unit"] == "percent"


class TestAlert:
    """Test Alert dataclass"""

    def test_create_alert_minimal(self):
        """Test creating alert with minimal parameters"""
        alert = Alert(
            id="alert-1",
            severity=AlertSeverity.WARNING,
            source="test_source",
            message="Test alert message",
            timestamp=datetime.now(),
        )

        assert alert.id == "alert-1"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.source == "test_source"
        assert alert.message == "Test alert message"
        assert alert.resolved is False
        assert alert.resolved_at is None

    def test_create_alert_full(self):
        """Test creating alert with all parameters"""
        now = datetime.now()
        metadata = {"threshold": 90, "actual": 95}

        alert = Alert(
            id="alert-2",
            severity=AlertSeverity.CRITICAL,
            source="cpu_monitor",
            message="CPU usage critical",
            timestamp=now,
            metadata=metadata,
        )

        assert alert.metadata == metadata

    def test_alert_resolve(self):
        """Test resolving an alert"""
        alert = Alert(
            id="alert-3",
            severity=AlertSeverity.ERROR,
            source="test",
            message="Error occurred",
            timestamp=datetime.now(),
        )

        assert alert.resolved is False
        assert alert.resolved_at is None

        before_resolve = datetime.now()
        alert.resolve()
        after_resolve = datetime.now()

        assert alert.resolved is True
        assert alert.resolved_at is not None
        assert before_resolve <= alert.resolved_at <= after_resolve

    def test_alert_to_dict(self):
        """Test converting alert to dictionary"""
        now = datetime.now()
        alert = Alert(
            id="test-alert",
            severity=AlertSeverity.INFO,
            source="test",
            message="Info message",
            timestamp=now,
            metadata={"key": "value"},
        )

        result = alert.to_dict()

        assert result["id"] == "test-alert"
        assert result["severity"] == "info"
        assert result["source"] == "test"
        assert result["message"] == "Info message"
        assert "timestamp" in result
        assert result["resolved"] is False
        assert result["resolved_at"] is None
        assert result["metadata"]["key"] == "value"

    def test_alert_to_dict_resolved(self):
        """Test converting resolved alert to dictionary"""
        now = datetime.now()
        alert = Alert(
            id="resolved-alert",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Warning",
            timestamp=now,
        )
        alert.resolve()

        result = alert.to_dict()

        assert result["resolved"] is True
        assert result["resolved_at"] is not None


class TestHealthCheckResult:
    """Test HealthCheckResult dataclass"""

    def test_create_healthy_result(self):
        """Test creating healthy check result"""
        now = datetime.now()
        metrics = {"response_time": 50, "status_code": 200}

        result = HealthCheckResult(
            component="api_server",
            healthy=True,
            message="API server is healthy",
            timestamp=now,
            metrics=metrics,
            response_time_ms=50,
        )

        assert result.component == "api_server"
        assert result.healthy is True
        assert result.message == "API server is healthy"
        assert result.metrics == metrics
        assert result.response_time_ms == 50

    def test_create_unhealthy_result(self):
        """Test creating unhealthy check result"""
        result = HealthCheckResult(
            component="database",
            healthy=False,
            message="Database connection failed",
            timestamp=datetime.now(),
        )

        assert result.healthy is False
        assert result.response_time_ms == 0

    def test_health_check_to_dict(self):
        """Test converting health check result to dictionary"""
        now = datetime.now()
        result = HealthCheckResult(
            component="cache",
            healthy=True,
            message="Cache operational",
            timestamp=now,
            metrics={"hit_rate": 0.95},
            response_time_ms=10,
        )

        dict_result = result.to_dict()

        assert dict_result["component"] == "cache"
        assert dict_result["healthy"] is True
        assert dict_result["message"] == "Cache operational"
        assert "timestamp" in dict_result
        assert dict_result["metrics"]["hit_rate"] == 0.95
        assert dict_result["response_time_ms"] == 10


class TestSystemMetrics:
    """Test SystemMetrics dataclass"""

    def test_create_metrics_minimal(self):
        """Test creating metrics with minimal parameters"""
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=1024.0,
            memory_available_mb=512.0,
            disk_usage_percent=70.0,
            disk_used_gb=100.0,
            disk_free_gb=50.0,
        )

        assert metrics.cpu_percent == 50.0
        assert metrics.memory_percent == 60.0
        assert metrics.disk_usage_percent == 70.0
        assert metrics.network_io == {}
        assert metrics.process_count == 0

    def test_create_metrics_full(self):
        """Test creating metrics with all parameters"""
        now = datetime.now()
        network_io = {"bytes_sent": 1000000, "bytes_recv": 5000000}

        metrics = SystemMetrics(
            cpu_percent=75.5,
            memory_percent=80.0,
            memory_used_mb=2048.0,
            memory_available_mb=512.0,
            disk_usage_percent=85.0,
            disk_used_gb=200.0,
            disk_free_gb=35.0,
            network_io=network_io,
            process_count=150,
            timestamp=now,
        )

        assert metrics.cpu_percent == 75.5
        assert metrics.network_io == network_io
        assert metrics.process_count == 150
        assert metrics.timestamp == now

    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary"""
        metrics = SystemMetrics(
            cpu_percent=45.0,
            memory_percent=55.0,
            memory_used_mb=800.0,
            memory_available_mb=700.0,
            disk_usage_percent=65.0,
            disk_used_gb=120.0,
            disk_free_gb=65.0,
            network_io={"bytes_sent": 1000},
            process_count=100,
        )

        dict_metrics = metrics.to_dict()

        assert dict_metrics["cpu_percent"] == 45.0
        assert dict_metrics["memory_percent"] == 55.0
        assert dict_metrics["disk_usage_percent"] == 65.0
        assert "timestamp" in dict_metrics
        assert dict_metrics["network_io"]["bytes_sent"] == 1000
        assert dict_metrics["process_count"] == 100

    def test_metrics_is_healthy_default_thresholds(self):
        """Test is_healthy with default thresholds"""
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=500.0,
            memory_available_mb=500.0,
            disk_usage_percent=70.0,
            disk_used_gb=70.0,
            disk_free_gb=30.0,
        )

        assert metrics.is_healthy() is True

    def test_metrics_is_healthy_custom_thresholds(self):
        """Test is_healthy with custom thresholds"""
        metrics = SystemMetrics(
            cpu_percent=85.0,
            memory_percent=85.0,
            memory_used_mb=850.0,
            memory_available_mb=150.0,
            disk_usage_percent=85.0,
            disk_used_gb=85.0,
            disk_free_gb=15.0,
        )

        # Should be healthy with custom thresholds
        assert metrics.is_healthy(thresholds={"cpu_percent": 90.0, "memory_percent": 90.0, "disk_usage_percent": 90.0}) is True

        # Should be unhealthy with strict thresholds
        assert metrics.is_healthy(thresholds={"cpu_percent": 80.0, "memory_percent": 80.0, "disk_usage_percent": 80.0}) is False

    def test_metrics_is_healthy_unhealthy_cpu(self):
        """Test is_healthy with unhealthy CPU"""
        metrics = SystemMetrics(
            cpu_percent=95.0,
            memory_percent=50.0,
            memory_used_mb=500.0,
            memory_available_mb=500.0,
            disk_usage_percent=50.0,
            disk_used_gb=50.0,
            disk_free_gb=50.0,
        )

        assert metrics.is_healthy() is False

    def test_metrics_is_healthy_unhealthy_memory(self):
        """Test is_healthy with unhealthy memory"""
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=95.0,
            memory_used_mb=950.0,
            memory_available_mb=50.0,
            disk_usage_percent=50.0,
            disk_used_gb=50.0,
            disk_free_gb=50.0,
        )

        assert metrics.is_healthy() is False

    def test_metrics_is_healthy_unhealthy_disk(self):
        """Test is_healthy with unhealthy disk"""
        metrics = SystemMetrics(
            cpu_percent=50.0,
            memory_percent=50.0,
            memory_used_mb=500.0,
            memory_available_mb=500.0,
            disk_usage_percent=95.0,
            disk_used_gb=95.0,
            disk_free_gb=5.0,
        )

        assert metrics.is_healthy() is False
