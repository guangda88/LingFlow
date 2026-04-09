"""Tests for lingflow.monitoring.default_checks module"""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from lingflow.monitoring.default_checks import (
    MonitoringLoop,
    check_cpu_usage,
    check_disk_usage,
    check_memory_usage,
    check_skill_loader,
    console_notification_handler,
    log_notification_handler,
    register_default_checks,
    register_default_handlers,
    setup_default_monitoring,
    start_monitoring,
    stop_monitoring,
)
from lingflow.monitoring.metrics.models import Alert, AlertSeverity, HealthCheckResult


class TestDefaultHealthChecks:
    """Test default health check functions"""

    @patch("lingflow.monitoring.default_checks.get_layered_loader")
    @patch("lingflow.monitoring.default_checks.get_memory_usage")
    def test_check_skill_loader_healthy(self, mock_get_memory, mock_get_loader):
        """Test skill loader check when healthy"""
        mock_loader = MagicMock()
        mock_loader.get_layer_stats.return_value = {"l1": 10, "l2": 5, "l3": 10}
        mock_get_loader.return_value = mock_loader
        mock_get_memory.return_value = {"l3_active": 10, "target_l3_max": 15, "total_cached": 20}

        result = check_skill_loader()

        assert isinstance(result, HealthCheckResult)
        assert result.component == "skill_loader"
        assert result.healthy is True

    @patch("lingflow.monitoring.default_checks.get_layered_loader")
    @patch("lingflow.monitoring.default_checks.get_memory_usage")
    def test_check_skill_loader_l3_exceeded(self, mock_get_memory, mock_get_loader):
        """Test skill loader check when L3 exceeded"""
        mock_loader = MagicMock()
        mock_loader.get_layer_stats.return_value = {"l1": 10, "l2": 5, "l3": 10}
        mock_get_loader.return_value = mock_loader
        mock_get_memory.return_value = {"l3_active": 20, "target_l3_max": 15, "total_cached": 20}

        result = check_skill_loader()

        assert result.healthy is False
        assert "L3 活跃技能超限" in result.message

    @patch("lingflow.monitoring.default_checks.get_layered_loader")
    @patch("lingflow.monitoring.default_checks.get_memory_usage")
    def test_check_skill_loader_cache_exceeded(self, mock_get_memory, mock_get_loader):
        """Test skill loader check when cache exceeded"""
        mock_loader = MagicMock()
        mock_loader.get_layer_stats.return_value = {"l1": 10, "l2": 5, "l3": 10}
        mock_get_loader.return_value = mock_loader
        mock_get_memory.return_value = {"l3_active": 10, "target_l3_max": 15, "total_cached": 60}

        result = check_skill_loader()

        assert result.healthy is False
        assert "缓存技能过多" in result.message

    @patch("lingflow.monitoring.default_checks.get_layered_loader")
    def test_check_skill_loader_exception(self, mock_get_loader):
        """Test skill loader check with exception"""
        mock_get_loader.side_effect = Exception("Test error")

        result = check_skill_loader()

        assert result.healthy is False
        assert "检查失败" in result.message

    @patch("lingflow.monitoring.default_checks.psutil.Process")
    def test_check_memory_usage_healthy(self, mock_process):
        """Test memory usage check when healthy"""
        mock_proc = MagicMock()
        mock_proc.memory_percent.return_value = 50.0
        mock_proc.memory_info.return_value = MagicMock(rss=1024 * 1024 * 512)  # 512 MB
        mock_process.return_value = mock_proc

        result = check_memory_usage()

        assert isinstance(result, HealthCheckResult)
        assert result.component == "memory"
        assert result.healthy is True

    @patch("lingflow.monitoring.default_checks.psutil.Process")
    def test_check_memory_usage_high(self, mock_process):
        """Test memory usage check when high"""
        mock_proc = MagicMock()
        mock_proc.memory_percent.return_value = 85.0
        mock_proc.memory_info.return_value = MagicMock(rss=1024 * 1024 * 1024)  # 1 GB
        mock_process.return_value = mock_proc

        result = check_memory_usage()

        assert result.healthy is False
        assert "内存使用率过高" in result.message

    @patch("lingflow.monitoring.default_checks.psutil.Process")
    def test_check_memory_usage_exception(self, mock_process):
        """Test memory usage check with exception"""
        mock_process.side_effect = Exception("Process error")

        result = check_memory_usage()

        assert result.healthy is False
        assert "检查失败" in result.message

    @patch("lingflow.monitoring.default_checks.psutil.disk_usage")
    def test_check_disk_usage_healthy(self, mock_disk_usage):
        """Test disk usage check when healthy"""
        mock_disk = MagicMock()
        mock_disk.total = 1000
        mock_disk.used = 500
        mock_disk.free = 500
        mock_disk_usage.return_value = mock_disk

        result = check_disk_usage()

        assert isinstance(result, HealthCheckResult)
        assert result.component == "disk"
        assert result.healthy is True

    @patch("lingflow.monitoring.default_checks.psutil.disk_usage")
    def test_check_disk_usage_high(self, mock_disk_usage):
        """Test disk usage check when high"""
        mock_disk = MagicMock()
        mock_disk.total = 1000
        mock_disk.used = 950
        mock_disk.free = 50
        mock_disk_usage.return_value = mock_disk

        result = check_disk_usage()

        assert result.healthy is False
        assert "磁盘空间不足" in result.message

    @patch("lingflow.monitoring.default_checks.psutil.disk_usage")
    def test_check_disk_usage_exception(self, mock_disk_usage):
        """Test disk usage check with exception"""
        mock_disk_usage.side_effect = Exception("Disk error")

        result = check_disk_usage()

        assert result.healthy is False
        assert "检查失败" in result.message

    @patch("lingflow.monitoring.default_checks.psutil.cpu_percent")
    def test_check_cpu_usage_healthy(self, mock_cpu):
        """Test CPU usage check when healthy"""
        mock_cpu.return_value = 50.0

        result = check_cpu_usage()

        assert isinstance(result, HealthCheckResult)
        assert result.component == "cpu"
        assert result.healthy is True

    @patch("lingflow.monitoring.default_checks.psutil.cpu_percent")
    def test_check_cpu_usage_high(self, mock_cpu):
        """Test CPU usage check when high"""
        mock_cpu.return_value = 95.0

        result = check_cpu_usage()

        assert result.healthy is False
        assert "CPU 使用率过高" in result.message

    @patch("lingflow.monitoring.default_checks.psutil.cpu_percent")
    def test_check_cpu_usage_exception(self, mock_cpu):
        """Test CPU usage check with exception"""
        mock_cpu.side_effect = Exception("CPU error")

        result = check_cpu_usage()

        assert result.healthy is False
        assert "检查失败" in result.message


class TestNotificationHandlers:
    """Test notification handler functions"""

    @patch("lingflow.monitoring.default_checks.logger")
    def test_log_notification_handler_info(self, mock_logger):
        """Test log notification handler for info severity"""
        alert = Alert(
            id="test-1",
            severity=AlertSeverity.INFO,
            source="test",
            message="Info message",
            timestamp=datetime.now(),
        )

        log_notification_handler(alert)

        mock_logger.info.assert_called_once()

    @patch("lingflow.monitoring.default_checks.logger")
    def test_log_notification_handler_warning(self, mock_logger):
        """Test log notification handler for warning severity"""
        alert = Alert(
            id="test-2",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Warning message",
            timestamp=datetime.now(),
        )

        log_notification_handler(alert)

        mock_logger.warning.assert_called_once()

    @patch("lingflow.monitoring.default_checks.logger")
    def test_log_notification_handler_error(self, mock_logger):
        """Test log notification handler for error severity"""
        alert = Alert(
            id="test-3",
            severity=AlertSeverity.ERROR,
            source="test",
            message="Error message",
            timestamp=datetime.now(),
        )

        log_notification_handler(alert)

        mock_logger.error.assert_called_once()

    @patch("lingflow.monitoring.default_checks.logger")
    def test_log_notification_handler_critical(self, mock_logger):
        """Test log notification handler for critical severity"""
        alert = Alert(
            id="test-4",
            severity=AlertSeverity.CRITICAL,
            source="test",
            message="Critical message",
            timestamp=datetime.now(),
        )

        log_notification_handler(alert)

        mock_logger.critical.assert_called_once()

    @patch("builtins.print")
    def test_console_notification_handler(self, mock_print):
        """Test console notification handler"""
        alert = Alert(
            id="console-1",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Console warning",
            timestamp=datetime.now(),
        )

        console_notification_handler(alert)

        mock_print.assert_called_once()
        # Should contain ANSI color codes
        call_args = str(mock_print.call_args)
        assert "[WARNING]" in call_args

    @patch("builtins.print")
    def test_console_notification_handler_all_severities(self, mock_print):
        """Test console handler for all severities"""
        severities = [
            AlertSeverity.INFO,
            AlertSeverity.WARNING,
            AlertSeverity.ERROR,
            AlertSeverity.CRITICAL,
        ]

        for severity in severities:
            alert = Alert(
                id=f"test-{severity.value}",
                severity=severity,
                source="test",
                message=f"{severity.value} message",
                timestamp=datetime.now(),
            )

            console_notification_handler(alert)

        assert mock_print.call_count == 4


class TestRegistrationFunctions:
    """Test registration functions"""

    @patch("lingflow.monitoring.default_checks.register_health_check")
    def test_register_default_checks(self, mock_register):
        """Test registering default checks"""
        register_default_checks()

        assert mock_register.call_count == 4

    @patch("lingflow.monitoring.default_checks.get_operations_monitor")
    def test_register_default_handlers(self, mock_get_monitor):
        """Test registering default handlers"""
        mock_monitor = MagicMock()
        mock_get_monitor.return_value = mock_monitor

        register_default_handlers()

        # Should add console handler
        mock_monitor.add_notification_handler.assert_called()

    @patch("lingflow.monitoring.default_checks.register_default_handlers")
    @patch("lingflow.monitoring.default_checks.register_default_checks")
    @patch("lingflow.monitoring.default_checks.get_operations_monitor")
    def test_setup_default_monitoring(self, mock_get_monitor, mock_reg_checks, mock_reg_handlers):
        """Test setting up default monitoring"""
        mock_monitor = MagicMock()
        mock_get_monitor.return_value = mock_monitor

        result = setup_default_monitoring()

        mock_reg_checks.assert_called_once()
        mock_reg_handlers.assert_called_once()
        assert result == mock_monitor


class TestMonitoringLoop:
    """Test MonitoringLoop class"""

    def test_init(self):
        """Test initialization"""
        loop = MonitoringLoop(check_interval=30, alert_interval=15)

        assert loop.check_interval == 30
        assert loop.alert_interval == 15
        assert loop._running is False
        assert loop._thread is None

    def test_start(self):
        """Test starting monitoring loop"""
        loop = MonitoringLoop(check_interval=1, alert_interval=1)

        loop.start()
        time.sleep(0.1)  # Give thread time to start

        assert loop._running is True
        assert loop._thread is not None

        loop.stop()

    def test_stop(self):
        """Test stopping monitoring loop"""
        loop = MonitoringLoop(check_interval=1, alert_interval=1)

        loop.start()
        time.sleep(0.1)
        assert loop._running is True

        loop.stop()
        assert loop._running is False

    def test_double_start(self):
        """Test that starting twice doesn't create extra threads"""
        loop = MonitoringLoop(check_interval=1, alert_interval=1)

        loop.start()
        time.sleep(0.1)
        first_thread = loop._thread

        loop.start()  # Should not start another thread
        time.sleep(0.1)

        assert loop._thread == first_thread

        loop.stop()

    def test_stop_without_start(self):
        """Test stopping without starting doesn't crash"""
        loop = MonitoringLoop()
        loop.stop()  # Should not crash

        assert loop._running is False


class TestGlobalMonitoringControl:
    """Test global monitoring control functions"""

    @patch("lingflow.monitoring.default_checks.setup_default_monitoring")
    @patch("lingflow.monitoring.default_checks.MonitoringLoop")
    def test_start_monitoring(self, mock_loop_class, mock_setup):
        """Test starting global monitoring"""
        mock_loop = MagicMock()
        mock_loop_class.return_value = mock_loop

        result = start_monitoring(check_interval=30, alert_interval=15)

        mock_setup.assert_called_once()
        mock_loop_class.assert_called_once_with(30, 15)
        mock_loop.start.assert_called_once()
        assert result == mock_loop

    def test_stop_monitoring(self):
        """Test stopping global monitoring"""
        # Start monitoring first, then stop it
        loop = MonitoringLoop(check_interval=1, alert_interval=1)
        loop.start()
        time.sleep(0.05)  # Let it start

        assert loop._running is True

        loop.stop()
        time.sleep(0.05)  # Let it stop

        assert loop._running is False
