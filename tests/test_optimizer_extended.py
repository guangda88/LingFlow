import tempfile

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
    def test_init(self):
        r = OptimizationRequest(target="/tmp", goal="structure", params={"x": 1}, config={"max_experiments": 5})
        assert r.target == "/tmp"
        assert r.goal == "structure"
        assert r.params == {"x": 1}
        assert r.config == {"max_experiments": 5}

    def test_defaults(self):
        r = OptimizationRequest(target=".", goal="performance", params={}, config={})
        assert r.params == {}
        assert r.config == {}


class TestOptimizationResultExtended:
    def test_with_history(self):
        r = OptimizationResult(
            success=True,
            best_params={"x": 1},
            best_score=0.5,
            experiments=10,
            duration=1.0,
            history=[{"a": 1}],
        )
        assert r.history == [{"a": 1}]

    def test_error_result(self):
        r = OptimizationResult(
            success=False,
            best_params={},
            best_score=0,
            experiments=0,
            duration=0,
            error="test error",
        )
        assert r.success is False
        assert r.error == "test error"


class TestSimpleSearchSpaceExtended:
    def test_empty_sample(self):
        ss = SimpleSearchSpace()
        assert ss.sample() == {}

    def test_multiple_discrete(self):
        ss = SimpleSearchSpace()
        ss.add_discrete("x", [1, 2])
        ss.add_discrete("y", [3, 4])
        s = ss.sample()
        assert s["x"] in [1, 2]
        assert s["y"] in [3, 4]

    def test_continuous_range(self):
        ss = SimpleSearchSpace()
        ss.add_continuous("z", 10.0, 20.0)
        for _ in range(20):
            s = ss.sample()
            assert 10.0 <= s["z"] <= 20.0

    def test_mixed_types(self):
        ss = SimpleSearchSpace()
        ss.add_discrete("d", [1, 2, 3])
        ss.add_continuous("c", 0.0, 1.0)
        s = ss.sample()
        assert isinstance(s["d"], int)
        assert isinstance(s["c"], float)


class TestCreateSearchSpaceExtended:
    def test_structure_has_all_params(self):
        ss = _create_search_space("structure")
        names = list(ss.parameters.keys())
        assert "max_class_size" in names
        assert "max_method_count" in names
        assert "max_complexity" in names
        assert "max_nesting_depth" in names
        assert "coupling_limit" in names

    def test_performance_has_all_params(self):
        ss = _create_search_space("performance")
        names = list(ss.parameters.keys())
        assert "cache_size" in names
        assert "parallelism" in names
        assert "timeout" in names

    def test_simplicity_has_all_params(self):
        ss = _create_search_space("simplicity")
        names = list(ss.parameters.keys())
        assert "complexity_threshold" in names
        assert "duplication_penalty" in names
        assert "max_line_length" in names


class TestGridSearchExtended:
    def test_with_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ss = SimpleSearchSpace()
            ss.add_discrete("x", [1, 2])
            result = _grid_search(ss, tmpdir, max_experiments=3)
            assert result.success is True
            assert result.experiments == 3
            assert isinstance(result.best_params, dict)

    def test_finds_best_params(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ss = SimpleSearchSpace()
            ss.add_discrete("max_class_size", [100, 200])
            result = _grid_search(ss, tmpdir, max_experiments=4)
            assert result.best_score >= 0


class TestProcessIsolatedOptimizerExtended:
    def test_is_running_false(self):
        opt = ProcessIsolatedOptimizer()
        assert opt.is_running() is False

    def test_get_progress_not_running(self):
        opt = ProcessIsolatedOptimizer()
        assert opt.get_progress() is None

    def test_get_result_no_queue(self):
        opt = ProcessIsolatedOptimizer()
        assert opt.get_result() is None

    def test_cancel_not_running(self):
        opt = ProcessIsolatedOptimizer()
        opt.cancel()


class TestSynchronousOptimizerExtended:
    def test_optimize_with_params(self):
        opt = SynchronousOptimizer()
        req = OptimizationRequest(
            target="/tmp",
            goal="structure",
            params={"max_class_size": 200},
            config={"max_experiments": 2},
        )
        result = opt.optimize(req)
        assert result.success is True

    def test_optimize_with_history(self):
        opt = SynchronousOptimizer()
        req = OptimizationRequest(
            target="/tmp",
            goal="simplicity",
            params={},
            config={"max_experiments": 3},
        )
        result = opt.optimize(req)
        assert result.experiments == 3

    def test_optimize_with_time_budget(self):
        opt = SynchronousOptimizer()
        req = OptimizationRequest(
            target="/tmp",
            goal="performance",
            params={},
            config={"max_experiments": 2, "time_budget": 60},
        )
        result = opt.optimize(req)
        assert result.success is True
