"""Sampling monitor tests"""

import time
from unittest.mock import MagicMock, patch

import pytest

from lingflow.utils.performance import PerformanceMonitor
from lingflow.utils.sampling import (
    SamplingConfig,
    SamplingMonitor,
    get_sampling_stats,
    sampling_monitor,
    track_with_sampling,
)


class TestSamplingConfig:
    def test_defaults(self):
        cfg = SamplingConfig()
        assert cfg.default_rate == 0.1
        assert cfg.low_load_threshold == 0.5
        assert cfg.low_load_rate == 1.0
        assert cfg.high_load_threshold == 0.8
        assert cfg.high_load_rate == 0.05
        assert "skill_load" in cfg.critical_metrics


class TestSamplingMonitor:
    def test_should_record_critical_metric(self):
        mon = SamplingMonitor()
        assert mon.should_record("skill_load") is True
        assert mon.should_record("workflow_execution") is True
        assert mon.should_record("error_handler") is True

    def test_should_record_rate_100(self):
        mon = SamplingMonitor()
        mon.set_sampling_rate(1.0)
        assert mon.should_record("any_metric") is True

    def test_should_record_rate_0(self):
        mon = SamplingMonitor()
        mon.set_sampling_rate(0.0)
        assert mon.should_record("any_metric") is False

    def test_adjust_low_load(self):
        mon = SamplingMonitor()
        mon._last_adjustment = 0
        mon.adjust_sampling_rate(0.3)
        assert mon.get_sampling_rate() == SamplingConfig().low_load_rate

    def test_adjust_high_load(self):
        mon = SamplingMonitor()
        mon._last_adjustment = 0
        mon.adjust_sampling_rate(0.9)
        assert mon.get_sampling_rate() == SamplingConfig().high_load_rate

    def test_adjust_medium_load(self):
        mon = SamplingMonitor()
        mon._last_adjustment = 0
        mon.adjust_sampling_rate(0.65)
        rate = mon.get_sampling_rate()
        assert SamplingConfig().high_load_rate < rate < SamplingConfig().low_load_rate

    def test_adjust_throttled(self):
        mon = SamplingMonitor()
        mon.adjust_sampling_rate(0.3)
        first_rate = mon.get_sampling_rate()
        mon.adjust_sampling_rate(0.9)
        assert mon.get_sampling_rate() == first_rate

    def test_set_sampling_rate(self):
        mon = SamplingMonitor()
        mon.set_sampling_rate(0.5)
        assert mon.get_sampling_rate() == 0.5

    def test_set_sampling_rate_invalid(self):
        mon = SamplingMonitor()
        with pytest.raises(ValueError):
            mon.set_sampling_rate(1.5)
        with pytest.raises(ValueError):
            mon.set_sampling_rate(-0.1)

    def test_track_decorator_skips(self):
        base = PerformanceMonitor()
        mon = SamplingMonitor(base_monitor=base)
        mon.set_sampling_rate(0.0)
        call_count = [0]

        @mon.track("test")
        def my_func():
            call_count[0] += 1
            return "result"

        result = my_func()
        assert result == "result"
        assert call_count[0] == 1
        assert "test" not in base.metrics

    def test_track_decorator_records(self):
        base = PerformanceMonitor()
        mon = SamplingMonitor(base_monitor=base)
        mon.set_sampling_rate(1.0)

        @mon.track("test_metric")
        def my_func():
            return 42

        result = my_func()
        assert result == 42
        assert "test_metric" in base.metrics

    def test_default_config(self):
        mon = SamplingMonitor()
        assert mon._config.default_rate == 0.1


class TestGetSamplingStats:
    def test_returns_dict(self):
        stats = get_sampling_stats()
        assert "current_rate" in stats
        assert "config" in stats
        assert "default_rate" in stats["config"]
        assert "critical_metrics" in stats["config"]


class TestTrackWithSampling:
    def test_decorator(self):
        base = PerformanceMonitor()
        mon = SamplingMonitor(base_monitor=base)
        mon.set_sampling_rate(1.0)

        @track_with_sampling("custom")
        def my_func():
            return "tracked"

        result = my_func()
        assert result == "tracked"
