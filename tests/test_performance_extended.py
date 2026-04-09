"""Extended tests for performance utilities covering remaining gaps."""

import time
from unittest.mock import patch

import pytest

from lingflow.utils.performance import (
    ContextTimer,
    PerformanceMetric,
    PerformanceMonitor,
    cached_with_monitor,
    get_cache_stats,
    performance_monitor,
    track_performance,
)


class TestPerformanceMonitorPrintReport:
    def test_print_report_with_data(self, caplog):
        import logging

        monitor = PerformanceMonitor()

        @monitor.track("test_op")
        def op():
            return 1

        op()
        with caplog.at_level(logging.INFO, logger="lingflow.utils.performance"):
            monitor.print_report()
        assert any("Performance Report" in r.message for r in caplog.records)

    def test_print_report_empty(self, caplog):
        import logging

        monitor = PerformanceMonitor()
        with caplog.at_level(logging.INFO, logger="lingflow.utils.performance"):
            monitor.print_report()
        assert any("No performance metrics" in r.message for r in caplog.records)


class TestContextTimerEdgeCases:
    def test_start_time_none(self):
        timer = ContextTimer("test", monitor=PerformanceMonitor())
        timer.start_time = None
        result = timer.__exit__(None, None, None)
        assert result is None

    def test_with_custom_monitor(self):
        monitor = PerformanceMonitor()
        with ContextTimer("custom_op", monitor=monitor) as t:
            time.sleep(0.01)

        assert "custom_op" in monitor.metrics
        assert len(monitor.metrics["custom_op"]) == 1
        assert monitor.metrics["custom_op"][0].success is True

    def test_default_monitor(self):
        saved = performance_monitor
        import lingflow.utils.performance as perf_mod

        test_monitor = PerformanceMonitor()
        perf_mod.performance_monitor = test_monitor
        try:
            with ContextTimer("global_op"):
                time.sleep(0.01)
            assert "global_op" in test_monitor.metrics
        finally:
            perf_mod.performance_monitor = saved

    def test_exception_in_context(self):
        monitor = PerformanceMonitor()
        with pytest.raises(ValueError):
            with ContextTimer("failing_op", monitor=monitor):
                raise ValueError("test error")

        assert "failing_op" in monitor.metrics
        metric = monitor.metrics["failing_op"][0]
        assert metric.success is False
        assert "ValueError" in metric.error_message
        assert "test error" in metric.error_message

    def test_slow_operation_warning(self, caplog):
        import logging

        monitor = PerformanceMonitor()
        with caplog.at_level(logging.WARNING, logger="lingflow.utils.performance"):
            with patch("time.perf_counter", side_effect=[0.0, 1.5]):
                with ContextTimer("slow_op", monitor=monitor):
                    pass
        assert any("Slow operation" in r.message for r in caplog.records)


class TestCachedWithMonitorExtended:
    def test_cache_clear(self):
        @cached_with_monitor(maxsize=10)
        def func(x):
            return x * 2

        func(1)
        func(2)
        func(1)
        func.cache_clear()
        func(1)
        stats = get_cache_stats(func)
        assert stats["total_requests"] == 4

    def test_custom_metric_name(self):
        @cached_with_monitor(maxsize=10, metric_name="my_cache")
        def func(x):
            return x + 1

        func(5)
        func(5)
        stats = get_cache_stats(func)
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(50.0)

    def test_maxsize_eviction(self):
        call_count = [0]

        @cached_with_monitor(maxsize=2)
        def func(x):
            call_count[0] += 1
            return x

        func(1)
        func(2)
        func(3)
        func(1)
        stats = get_cache_stats(func)
        assert stats["total_requests"] == 4

    def test_zero_total_requests(self):
        @cached_with_monitor()
        def func(x):
            return x

        stats = get_cache_stats(func)
        assert stats["total_requests"] == 0
        assert stats["hit_rate"] == 0.0


class TestPerformanceMonitorDisabled:
    def test_track_disabled_still_executes(self):
        monitor = PerformanceMonitor()
        monitor.disable()

        @monitor.track("disabled_op")
        def op():
            return 42

        result = op()
        assert result == 42
        assert "disabled_op" not in monitor.metrics

    def test_enable_disable_cycle(self):
        monitor = PerformanceMonitor()

        @monitor.track("cycled")
        def op():
            return 1

        monitor.disable()
        op()
        assert "cycled" not in monitor.metrics

        monitor.enable()
        op()
        assert "cycled" in monitor.metrics
        assert len(monitor.metrics["cycled"]) == 1


class TestTrackPerformanceGlobal:
    def test_global_decorator_records(self):
        import lingflow.utils.performance as perf_mod

        saved = perf_mod.performance_monitor
        test_monitor = PerformanceMonitor()
        perf_mod.performance_monitor = test_monitor
        try:

            @track_performance("global_test")
            def op():
                return "done"

            op()
            assert "global_test" in test_monitor.metrics
        finally:
            perf_mod.performance_monitor = saved


class TestGetStatsEdgeCases:
    def test_get_stats_empty_metrics_list(self):
        monitor = PerformanceMonitor()
        monitor.metrics["empty_key"] = []
        result = monitor.get_stats("empty_key")
        assert result == {}

    def test_get_stats_nonexistent_key(self):
        monitor = PerformanceMonitor()
        result = monitor.get_stats("nonexistent")
        assert result == {}


class TestTrimMetricsEdge:
    def test_trim_with_exact_limit(self):
        monitor = PerformanceMonitor(max_metrics_per_key=3)
        for i in range(5):
            monitor.metrics["op"].append(PerformanceMetric(name="op", execution_time=float(i), timestamp=None))
            monitor._total_metrics_count += 1
        monitor._trim_metrics("op")
        assert len(monitor.metrics["op"]) == 3
        assert monitor._total_metrics_count == 3
