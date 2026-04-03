from lingflow.self_optimizer.optimizer import (
    OptimizationRequest,
    OptimizationResult,
    ProcessIsolatedOptimizer,
    SynchronousOptimizer,
    SimpleSearchSpace,
    _create_search_space,
    _grid_search,
)


class TestOptimizationResult:
    def test_defaults(self):
        r = OptimizationResult(
            success=True, best_params={"x": 1}, best_score=0.5,
            experiments=10, duration=1.0,
        )
        assert r.error == ""
        assert r.history == []

    def test_with_error(self):
        r = OptimizationResult(
            success=False, best_params={}, best_score=0,
            experiments=0, duration=0, error="fail",
        )
        assert r.error == "fail"


class TestSimpleSearchSpace:
    def test_add_discrete(self):
        ss = SimpleSearchSpace()
        ss.add_discrete("x", [1, 2, 3])
        assert "x" in ss.parameters

    def test_add_continuous(self):
        ss = SimpleSearchSpace()
        ss.add_continuous("y", 0.0, 1.0)
        assert "y" in ss.parameters

    def test_sample(self):
        ss = SimpleSearchSpace()
        ss.add_discrete("x", [10, 20, 30])
        ss.add_continuous("y", 0.0, 1.0)
        s = ss.sample()
        assert s["x"] in [10, 20, 30]
        assert 0.0 <= s["y"] <= 1.0


class TestCreateSearchSpace:
    def test_structure(self):
        ss = _create_search_space("structure")
        assert "max_class_size" in ss.parameters

    def test_performance(self):
        ss = _create_search_space("performance")
        assert "cache_size" in ss.parameters

    def test_simplicity(self):
        ss = _create_search_space("simplicity")
        assert "complexity_threshold" in ss.parameters

    def test_unknown(self):
        ss = _create_search_space("unknown")
        assert len(ss.parameters) == 0


class TestGridSearch:
    def test_basic(self):
        ss = SimpleSearchSpace()
        ss.add_discrete("x", [1, 2, 3])
        result = _grid_search(ss, "/tmp", max_experiments=3)
        assert result.success is True
        assert result.experiments == 3


class TestProcessIsolatedOptimizer:
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


class TestSynchronousOptimizer:
    def test_optimize_structure(self):
        opt = SynchronousOptimizer()
        req = OptimizationRequest(
            target="/tmp", goal="structure", params={},
            config={"max_experiments": 2},
        )
        result = opt.optimize(req)
        assert result.success is True
        assert result.experiments == 2

    def test_optimize_performance(self):
        opt = SynchronousOptimizer()
        req = OptimizationRequest(
            target="/tmp", goal="performance", params={},
            config={"max_experiments": 2},
        )
        result = opt.optimize(req)
        assert result.success is True

    def test_optimize_simplicity(self):
        opt = SynchronousOptimizer()
        req = OptimizationRequest(
            target="/tmp", goal="simplicity", params={},
            config={"max_experiments": 2},
        )
        result = opt.optimize(req)
        assert result.success is True

    def test_optimize_unknown_goal(self):
        opt = SynchronousOptimizer()
        req = OptimizationRequest(
            target="/tmp", goal="unknown", params={},
            config={"max_experiments": 2},
        )
        result = opt.optimize(req)
        assert result.success is True
