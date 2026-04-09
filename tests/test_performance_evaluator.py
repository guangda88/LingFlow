import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lingflow.self_optimizer.performance_evaluator import PerformanceEvaluator, PerformanceMetrics, fallback_evaluate


class TestPerformanceMetrics:
    def test_init(self):
        m = PerformanceMetrics(
            execution_time=1.5,
            memory_usage_mb=100.0,
            cpu_percent=50.0,
            io_operations=10,
            cache_hit_rate=0.8,
        )
        assert m.execution_time == 1.5
        assert m.memory_usage_mb == 100.0
        assert m.cpu_percent == 50.0
        assert m.io_operations == 10
        assert m.cache_hit_rate == 0.8


class TestPerformanceEvaluatorInit:
    def test_default_path(self):
        with patch("lingflow.self_optimizer.performance_evaluator.psutil") as mock_psutil:
            e = PerformanceEvaluator()
            assert e.target_path == Path(".")

    def test_custom_path(self):
        with patch("lingflow.self_optimizer.performance_evaluator.psutil") as mock_psutil:
            e = PerformanceEvaluator("/tmp")
            assert e.target_path == Path("/tmp")


class TestEvaluate:
    def test_evaluate_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch("lingflow.self_optimizer.performance_evaluator.psutil"):
            e = PerformanceEvaluator(tmpdir)
            score = e.evaluate({})
            assert isinstance(score, float)
            assert score >= 0

    def test_evaluate_returns_score(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch("lingflow.self_optimizer.performance_evaluator.psutil"):
            e = PerformanceEvaluator(tmpdir)
            score = e.evaluate({"cache_size": 100, "parallelism": 2})
            assert isinstance(score, float)


class TestMeasureImportTime:
    def test_no_init_py(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch("lingflow.self_optimizer.performance_evaluator.psutil"):
            e = PerformanceEvaluator(tmpdir)
            t = e._measure_import_time()
            assert isinstance(t, float)
            assert t >= 0

    def test_with_init_py(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch("lingflow.self_optimizer.performance_evaluator.psutil"):
            (Path(tmpdir) / "__init__.py").write_text("x = 1\n")
            e = PerformanceEvaluator(tmpdir)
            t = e._measure_import_time()
            assert isinstance(t, float)


class TestMeasureMemoryUsage:
    def test_normal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = PerformanceEvaluator(tmpdir)
            mem = e._measure_memory_usage()
            assert isinstance(mem, float)
            assert mem > 0

    def test_exception_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = PerformanceEvaluator(tmpdir)
            e.process = MagicMock()
            e.process.memory_info.side_effect = Exception("fail")
            mem = e._measure_memory_usage()
            assert mem == 0.0


class TestGetCpuPercent:
    def test_normal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = PerformanceEvaluator(tmpdir)
            cpu = e._get_cpu_percent()
            assert isinstance(cpu, float)

    def test_exception_returns_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = PerformanceEvaluator(tmpdir)
            e.process = MagicMock()
            e.process.cpu_percent.side_effect = Exception("fail")
            cpu = e._get_cpu_percent()
            assert cpu == 0.0


class TestGetCurrentMetrics:
    def test_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = PerformanceEvaluator(tmpdir)
            metrics = e.get_current_metrics()
            assert "execution_time" in metrics
            assert "memory_usage_mb" in metrics
            assert "cpu_percent" in metrics
            assert "python_files" in metrics
            assert metrics["python_files"] == 0

    def test_with_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("x = 1\n")
            e = PerformanceEvaluator(tmpdir)
            metrics = e.get_current_metrics()
            assert metrics["python_files"] == 1


class TestBenchmarkFunction:
    def test_simple_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = PerformanceEvaluator(tmpdir)
            result = e.benchmark_function(lambda: 1 + 1)
            assert "execution_time_mean" in result
            assert "execution_time_median" in result
            assert "execution_time_std" in result
            assert "memory_usage_mb_mean" in result
            assert "memory_usage_mb_max" in result
            assert result["samples"] == 10

    def test_failing_function(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            e = PerformanceEvaluator(tmpdir)

            def fail():
                raise ValueError("boom")

            result = e.benchmark_function(fail)
            assert result["samples"] == 10


class TestFallbackEvaluate:
    def test_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch("lingflow.self_optimizer.performance_evaluator.psutil"):
            score = fallback_evaluate({}, target_path=tmpdir)
            assert isinstance(score, float)
