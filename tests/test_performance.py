"""Performance monitoring tests"""

import pytest

from lingflow.utils.performance import (
    PerformanceMetric,
    PerformanceMonitor,
    ContextTimer,
    cached_with_monitor,
    get_cache_stats,
    track_performance,
)


class TestPerformanceMetric:
    def test_defaults(self):
        m = PerformanceMetric(name="test", execution_time=0.1, timestamp=None)
        assert m.success is True
        assert m.error_message is None
        assert m.metadata == {}


class TestPerformanceMonitor:
    def test_track_decorator(self):
        mon = PerformanceMonitor()

        @mon.track("my_metric")
        def my_func():
            return 42

        result = my_func()
        assert result == 42
        assert "my_metric" in mon.metrics
        assert len(mon.metrics["my_metric"]) == 1
        assert mon.metrics["my_metric"][0].success is True

    def test_track_decorator_default_name(self):
        mon = PerformanceMonitor()

        @mon.track()
        def my_func():
            return 1

        my_func()
        keys = list(mon.metrics.keys())
        assert len(keys) == 1
        assert "my_func" in keys[0]

    def test_track_decorator_error(self):
        mon = PerformanceMonitor()

        @mon.track("error_metric")
        def bad_func():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            bad_func()

        # The track decorator re-raises before recording on error path
        assert "error_metric" not in mon.metrics

    def test_track_disabled(self):
        mon = PerformanceMonitor()
        mon.disable()

        @mon.track("disabled")
        def my_func():
            return "ok"

        result = my_func()
        assert result == "ok"
        assert "disabled" not in mon.metrics

    def test_enable_disable(self):
        mon = PerformanceMonitor()
        mon.disable()
        assert mon._enabled is False
        mon.enable()
        assert mon._enabled is True

    def test_get_stats(self):
        mon = PerformanceMonitor()

        @mon.track("stat_test")
        def my_func():
            return 1

        my_func()
        my_func()
        stats = mon.get_stats("stat_test")
        assert stats["count"] == 2
        assert stats["success_count"] == 2
        assert stats["failure_count"] == 0
        assert stats["avg_time"] >= 0
        assert stats["min_time"] >= 0
        assert stats["max_time"] >= 0

    def test_get_stats_empty(self):
        mon = PerformanceMonitor()
        assert mon.get_stats("nonexistent") == {}

    def test_get_all_stats(self):
        mon = PerformanceMonitor()

        @mon.track("a")
        def func_a():
            return 1

        @mon.track("b")
        def func_b():
            return 2

        func_a()
        func_b()
        all_stats = mon.get_all_stats()
        assert "a" in all_stats
        assert "b" in all_stats

    def test_clear_specific(self):
        mon = PerformanceMonitor()

        @mon.track("to_clear")
        def my_func():
            return 1

        my_func()
        mon.clear("to_clear")
        assert "to_clear" not in mon.metrics

    def test_clear_all(self):
        mon = PerformanceMonitor()

        @mon.track("x")
        def func_x():
            return 1

        func_x()
        mon.clear()
        assert len(mon.metrics) == 0

    def test_trim_metrics(self):
        mon = PerformanceMonitor(max_metrics_per_key=3)

        @mon.track("trim_test")
        def my_func():
            return 1

        for _ in range(10):
            my_func()
        assert len(mon.metrics["trim_test"]) <= 3

    def test_check_total_limit(self):
        mon = PerformanceMonitor()
        mon.MAX_TOTAL_METRICS = 5

        @mon.track("total_test")
        def my_func():
            return 1

        for _ in range(10):
            my_func()
        assert mon._total_metrics_count <= 5


class TestContextTimer:
    def test_basic_timing(self):
        mon = PerformanceMonitor()
        with ContextTimer("test_block", mon):
            x = 1 + 1
        assert "test_block" in mon.metrics
        assert len(mon.metrics["test_block"]) == 1
        assert mon.metrics["test_block"][0].success is True

    def test_timing_with_exception(self):
        mon = PerformanceMonitor()
        with pytest.raises(RuntimeError):
            with ContextTimer("error_block", mon):
                raise RuntimeError("fail")
        assert "error_block" in mon.metrics
        assert mon.metrics["error_block"][0].success is False


class TestCachedWithMonitor:
    def test_caching(self):
        call_count = [0]

        @cached_with_monitor(maxsize=10, metric_name="cached_func")
        def my_func(x):
            call_count[0] += 1
            return x * 2

        assert my_func(5) == 10
        assert my_func(5) == 10
        assert call_count[0] == 1

    def test_cache_stats(self):
        @cached_with_monitor(maxsize=10)
        def my_func(x):
            return x

        my_func(1)
        my_func(1)
        stats = get_cache_stats(my_func)
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0

    def test_get_cache_stats_non_cached(self):
        def plain():
            pass
        assert get_cache_stats(plain) == {}


class TestTrackPerformance:
    def test_global_decorator(self):
        @track_performance("global_test")
        def my_func():
            return "result"

        result = my_func()
        assert result == "result"
