import time
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from lingflow.monitoring.default_checks import (
    check_skill_loader,
    check_memory_usage,
    check_cpu_usage,
    MonitoringLoop,
    start_monitoring,
    stop_monitoring,
    setup_default_monitoring,
)


class TestCheckSkillLoader:
    @patch("lingflow.monitoring.default_checks.get_layered_loader")
    @patch("lingflow.monitoring.default_checks.get_memory_usage")
    def test_healthy(self, mock_memory, mock_loader):
        mock_loader.return_value.get_layer_stats.return_value = {"L1": {"total": 5, "loaded": 5}}
        mock_memory.return_value = {"l3_active": 3, "target_l3_max": 15, "total_cached": 10}
        result = check_skill_loader()
        assert result.healthy is True
        assert "skill_loader" == result.component

    @patch("lingflow.monitoring.default_checks.get_layered_loader")
    @patch("lingflow.monitoring.default_checks.get_memory_usage")
    def test_l3_over_limit(self, mock_memory, mock_loader):
        mock_loader.return_value.get_layer_stats.return_value = {}
        mock_memory.return_value = {"l3_active": 20, "target_l3_max": 15, "total_cached": 10}
        result = check_skill_loader()
        assert result.healthy is False
        assert "超限" in result.message

    @patch("lingflow.monitoring.default_checks.get_layered_loader")
    @patch("lingflow.monitoring.default_checks.get_memory_usage")
    def test_too_many_cached(self, mock_memory, mock_loader):
        mock_loader.return_value.get_layer_stats.return_value = {}
        mock_memory.return_value = {"l3_active": 3, "target_l3_max": 15, "total_cached": 60}
        result = check_skill_loader()
        assert result.healthy is False
        assert "缓存" in result.message

    @patch("lingflow.monitoring.default_checks.get_layered_loader")
    def test_exception_handling(self, mock_loader):
        mock_loader.side_effect = RuntimeError("boom")
        result = check_skill_loader()
        assert result.healthy is False
        assert "boom" in result.message


class TestCheckMemoryUsage:
    @patch("lingflow.monitoring.default_checks.psutil")
    def test_healthy(self, mock_psutil):
        mock_process = MagicMock()
        mock_process.memory_percent.return_value = 50.0
        mock_process.memory_info.return_value = MagicMock(rss=500 * 1024 * 1024)
        mock_psutil.Process.return_value = mock_process
        result = check_memory_usage()
        assert result.healthy is True

    @patch("lingflow.monitoring.default_checks.psutil")
    def test_unhealthy_high_memory(self, mock_psutil):
        mock_process = MagicMock()
        mock_process.memory_percent.return_value = 85.0
        mock_process.memory_info.return_value = MagicMock(rss=2 * 1024 * 1024 * 1024)
        mock_psutil.Process.return_value = mock_process
        result = check_memory_usage()
        assert result.healthy is False
        assert "内存" in result.message

    @patch("lingflow.monitoring.default_checks.psutil")
    def test_exception_handling(self, mock_psutil):
        mock_psutil.Process.side_effect = RuntimeError("boom")
        result = check_memory_usage()
        assert result.healthy is False


class TestCheckCpuUsage:
    @patch("lingflow.monitoring.default_checks.psutil")
    def test_healthy(self, mock_psutil):
        mock_psutil.cpu_percent.return_value = 50.0
        result = check_cpu_usage()
        assert result.healthy is True

    @patch("lingflow.monitoring.default_checks.psutil")
    def test_unhealthy(self, mock_psutil):
        mock_psutil.cpu_percent.return_value = 95.0
        result = check_cpu_usage()
        assert result.healthy is False
        assert "CPU" in result.message

    @patch("lingflow.monitoring.default_checks.psutil")
    def test_exception_handling(self, mock_psutil):
        mock_psutil.cpu_percent.side_effect = RuntimeError("boom")
        result = check_cpu_usage()
        assert result.healthy is False


class TestMonitoringLoop:
    def test_init(self):
        loop = MonitoringLoop(check_interval=10, alert_interval=5)
        assert loop.check_interval == 10
        assert loop.alert_interval == 5
        assert loop._running is False

    def test_start_and_stop(self):
        loop = MonitoringLoop(check_interval=60, alert_interval=30)
        loop.start()
        assert loop._running is True
        assert loop._thread is not None
        loop.stop()
        assert loop._running is False

    def test_start_idempotent(self):
        loop = MonitoringLoop(check_interval=60, alert_interval=30)
        loop.start()
        thread1 = loop._thread
        loop.start()
        assert loop._thread is thread1
        loop.stop()

    def test_stop_without_start(self):
        loop = MonitoringLoop(check_interval=60, alert_interval=30)
        loop.stop()
        assert loop._running is False


class TestSetupDefaultMonitoring:
    @patch("lingflow.monitoring.default_checks.get_operations_monitor")
    @patch("lingflow.monitoring.default_checks.register_health_check")
    def test_registers_checks(self, mock_reg, mock_get_mon):
        mock_monitor = MagicMock()
        mock_get_mon.return_value = mock_monitor
        setup_default_monitoring()
        assert mock_reg.call_count >= 3
        mock_monitor.add_notification_handler.assert_called_once()

    @patch("lingflow.monitoring.default_checks.get_operations_monitor")
    @patch("lingflow.monitoring.default_checks.register_health_check")
    def test_idempotent(self, mock_reg, mock_get_mon):
        mock_monitor = MagicMock()
        mock_get_mon.return_value = mock_monitor
        setup_default_monitoring()
        setup_default_monitoring()
        assert mock_reg.call_count >= 6


class TestStartStopMonitoring:
    @patch("lingflow.monitoring.default_checks.setup_default_monitoring")
    def test_start_monitoring(self, mock_setup):
        loop = start_monitoring(check_interval=60, alert_interval=30)
        assert isinstance(loop, MonitoringLoop)
        assert loop._running is True
        mock_setup.assert_called_once()
        stop_monitoring()

    def test_stop_monitoring_without_start(self):
        import lingflow.monitoring.default_checks as mod
        mod._monitoring_loop = None
        stop_monitoring()
