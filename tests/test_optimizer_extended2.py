"""Extended optimizer module tests for additional coverage."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lingflow.self_optimizer.optimizer import (
    OptimizationRequest,
    OptimizationResult,
    ProcessIsolatedOptimizer,
    SimpleSearchSpace,
    SynchronousOptimizer,
    _create_search_space,
    _grid_search,
)


class TestOptimizationRequest:
    def test_defaults(self):
        r = OptimizationRequest(target="/tmp", goal="structure", params={}, config={})
        assert r.target == "/tmp"
        assert r.goal == "structure"

    def test_custom(self):
        r = OptimizationRequest(
            target="/path",
            goal="performance",
            params={"a": 1},
            config={"max_experiments": 10},
        )
        assert r.params == {"a": 1}
        assert r.config["max_experiments"] == 10


class TestOptimizationResult:
    def test_defaults(self):
        r = OptimizationResult(success=True, best_params={}, best_score=0.5, experiments=10, duration=1.0)
        assert r.error == ""
        assert r.history == []

    def test_with_error(self):
        r = OptimizationResult(
            success=False, best_params={}, best_score=0, experiments=0, duration=0, error="something failed"
        )
        assert r.success is False


class TestSimpleSearchSpace:
    def test_discrete_sampling(self):
        space = SimpleSearchSpace()
        space.add_discrete("x", [1, 2, 3])
        sample = space.sample()
        assert sample["x"] in [1, 2, 3]

    def test_continuous_sampling(self):
        space = SimpleSearchSpace()
        space.add_continuous("y", 0.0, 1.0)
        sample = space.sample()
        assert 0.0 <= sample["y"] <= 1.0

    def test_mixed_params(self):
        space = SimpleSearchSpace()
        space.add_discrete("x", [10, 20])
        space.add_continuous("y", 0.0, 5.0)
        sample = space.sample()
        assert sample["x"] in [10, 20]
        assert 0.0 <= sample["y"] <= 5.0


class TestCreateSearchSpace:
    def test_structure_space(self):
        space = _create_search_space("structure")
        assert "max_class_size" in space.parameters
        assert "coupling_limit" in space.parameters

    def test_performance_space(self):
        space = _create_search_space("performance")
        assert "cache_size" in space.parameters
        assert "parallelism" in space.parameters

    def test_simplicity_space(self):
        space = _create_search_space("simplicity")
        assert "complexity_threshold" in space.parameters
        assert "max_line_length" in space.parameters


class TestGridSearch:
    def test_basic_grid_search(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "sample.py").write_text("x = 1\n")
            space = _create_search_space("structure")
            result = _grid_search(space, tmpdir, 3)
            assert result.success is True
            assert result.experiments == 3
            assert isinstance(result.best_params, dict)
            assert result.best_score >= 0


class TestProcessIsolatedOptimizer:
    def test_start_and_complete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "sample.py").write_text("x = 1\n")
            opt = ProcessIsolatedOptimizer()
            request = OptimizationRequest(
                target=tmpdir,
                goal="structure",
                params={},
                config={"max_experiments": 2},
            )
            started = opt.start_optimization(request)
            assert started is True
            result = opt.wait_for_completion(timeout=120)
            assert result is not None
            assert result.success is True

    def test_cannot_start_twice(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "sample.py").write_text("x = 1\n")
            opt = ProcessIsolatedOptimizer()
            request = OptimizationRequest(target=tmpdir, goal="structure", params={}, config={"max_experiments": 2})
            opt.start_optimization(request)
            assert opt.start_optimization(request) is False
            opt.wait_for_completion(timeout=120)

    def test_is_running(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "sample.py").write_text("x = 1\n")
            opt = ProcessIsolatedOptimizer()
            assert opt.is_running() is False
            request = OptimizationRequest(target=tmpdir, goal="structure", params={}, config={"max_experiments": 2})
            opt.start_optimization(request)
            assert opt.is_running() is True
            opt.wait_for_completion(timeout=120)
            assert opt.is_running() is False

    def test_get_progress(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "sample.py").write_text("x = 1\n")
            opt = ProcessIsolatedOptimizer()
            assert opt.get_progress() is None
            request = OptimizationRequest(target=tmpdir, goal="structure", params={}, config={"max_experiments": 2})
            opt.start_optimization(request)
            progress = opt.get_progress()
            assert progress is not None
            assert progress["running"] is True
            opt.wait_for_completion(timeout=120)

    def test_get_result_before_completion(self):
        opt = ProcessIsolatedOptimizer()
        assert opt.get_result() is None

    def test_cancel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "sample.py").write_text("x = 1\n")
            opt = ProcessIsolatedOptimizer()
            request = OptimizationRequest(target=tmpdir, goal="structure", params={}, config={"max_experiments": 2})
            opt.start_optimization(request)
            opt.cancel()
            assert opt.is_running() is False


class TestSynchronousOptimizer:
    def test_structure_optimize(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "sample.py").write_text("x = 1\n")
            opt = SynchronousOptimizer()
            request = OptimizationRequest(target=tmpdir, goal="structure", params={}, config={"max_experiments": 2})
            result = opt.optimize(request)
            assert result.success is True
            assert result.experiments == 2

    def test_simplicity_optimize(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "sample.py").write_text("x = 1\n")
            opt = SynchronousOptimizer()
            request = OptimizationRequest(target=tmpdir, goal="simplicity", params={}, config={"max_experiments": 2})
            result = opt.optimize(request)
            assert result.success is True

    def test_unknown_goal_uses_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "sample.py").write_text("x = 1\n")
            opt = SynchronousOptimizer()
            request = OptimizationRequest(target=tmpdir, goal="unknown_goal", params={}, config={"max_experiments": 2})
            result = opt.optimize(request)
            assert result.success is True
