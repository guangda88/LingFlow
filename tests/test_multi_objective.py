import pytest
from lingflow.self_optimizer.phase4.multi_objective import (
    ParetoPoint,
    MultiObjectiveResult,
    MultiObjectiveOptimizer,
    NSGA2Optimizer,
)


def _make_point(params=None, objectives=None, score=0.0, dominated=False):
    return ParetoPoint(
        params=params or {},
        objectives=objectives or {"quality": 1.0, "performance": 1.0},
        aggregated_score=score,
        dominated=dominated,
    )


class TestParetoPoint:
    def test_dominates_better_in_one(self):
        a = _make_point(objectives={"q": 1.0, "p": 2.0})
        b = _make_point(objectives={"q": 2.0, "p": 2.0})
        assert a.dominates(b) is True

    def test_dominates_better_in_all(self):
        a = _make_point(objectives={"q": 1.0, "p": 1.0})
        b = _make_point(objectives={"q": 2.0, "p": 2.0})
        assert a.dominates(b) is True

    def test_does_not_dominate_equal(self):
        a = _make_point(objectives={"q": 1.0, "p": 1.0})
        b = _make_point(objectives={"q": 1.0, "p": 1.0})
        assert a.dominates(b) is False

    def test_does_not_dominate_worse_in_one(self):
        a = _make_point(objectives={"q": 1.0, "p": 3.0})
        b = _make_point(objectives={"q": 2.0, "p": 2.0})
        assert a.dominates(b) is False

    def test_dominates_missing_objective(self):
        a = _make_point(objectives={"q": 1.0})
        b = _make_point(objectives={"q": 2.0})
        assert a.dominates(b) is True

    def test_to_dict(self):
        p = _make_point(params={"x": 1}, objectives={"q": 0.5}, score=0.5, dominated=False)
        d = p.to_dict()
        assert d["params"] == {"x": 1}
        assert d["aggregated_score"] == 0.5
        assert d["dominated"] is False


class TestMultiObjectiveResult:
    @pytest.fixture
    def result(self):
        front = [
            _make_point(params={"x": 1}, objectives={"q": 0.1, "p": 0.2}, score=0.15),
            _make_point(params={"x": 2}, objectives={"q": 0.2, "p": 0.1}, score=0.15),
            _make_point(params={"x": 3}, objectives={"q": 0.5, "p": 0.5}, score=0.5, dominated=True),
        ]
        return MultiObjectiveResult(
            pareto_front=front,
            all_evaluated=front,
            n_evaluations=3,
            total_time=1.0,
            converged=True,
        )

    def test_get_pareto_front(self, result):
        front = result.get_pareto_front()
        assert len(front) == 2
        assert all(not p.dominated for p in front)

    def test_get_best_by_objective(self, result):
        best_q = result.get_best_by_objective("q")
        assert best_q is not None
        assert best_q.objectives["q"] == 0.1

    def test_get_best_by_objective_empty(self):
        r = MultiObjectiveResult(
            pareto_front=[_make_point(dominated=True)],
            all_evaluated=[],
            n_evaluations=0,
            total_time=0.0,
            converged=False,
        )
        assert r.get_best_by_objective("q") is None

    def test_get_balanced_solution(self, result):
        balanced = result.get_balanced_solution()
        assert balanced is not None
        assert balanced.aggregated_score == 0.15

    def test_get_balanced_solution_empty(self):
        r = MultiObjectiveResult(
            pareto_front=[_make_point(dominated=True)],
            all_evaluated=[],
            n_evaluations=0,
            total_time=0.0,
            converged=False,
        )
        assert r.get_balanced_solution() is None

    def test_get_summary(self, result):
        summary = result.get_summary()
        assert "评估次数: 3" in summary
        assert "Pareto前沿解数: 2" in summary
        assert "收敛状态: 是" in summary


class TestMultiObjectiveOptimizer:
    def test_evaluate_all_objectives(self):
        opt = MultiObjectiveOptimizer(
            search_space={},
            objectives={"q": lambda p: p.get("x", 0) ** 2},
        )
        results = opt.evaluate_all_objectives({"x": 3})
        assert results["q"] == 9.0

    def test_evaluate_all_objectives_error(self):
        def failing_fn(params):
            raise ValueError("boom")

        opt = MultiObjectiveOptimizer(
            search_space={},
            objectives={"q": failing_fn},
        )
        results = opt.evaluate_all_objectives({"x": 1})
        assert results["q"] == float('inf')

    def test_calculate_aggregated_score(self):
        opt = MultiObjectiveOptimizer(
            search_space={},
            objectives={"q": lambda p: 0, "p": lambda p: 0},
            weights={"q": 2.0, "p": 1.0},
        )
        score = opt.calculate_aggregated_score({"q": 3.0, "p": 6.0})
        assert score == pytest.approx(4.0, abs=0.01)

    def test_calculate_aggregated_score_empty(self):
        opt = MultiObjectiveOptimizer(search_space={}, objectives={})
        score = opt.calculate_aggregated_score({})
        assert score == 0.0

    def test_update_pareto_front_adds_new(self):
        opt = MultiObjectiveOptimizer(search_space={}, objectives={})
        p = _make_point(objectives={"q": 1.0}, score=1.0)
        opt.update_pareto_front(p)
        assert len(opt.pareto_front) == 1

    def test_update_pareto_front_dominated_not_added(self):
        opt = MultiObjectiveOptimizer(search_space={}, objectives={})
        good = _make_point(objectives={"q": 0.5}, score=0.5)
        opt.update_pareto_front(good)
        bad = _make_point(objectives={"q": 1.5}, score=1.5)
        opt.update_pareto_front(bad)
        assert len(opt.pareto_front) == 1
        assert bad.dominated is True

    def test_update_pareto_front_replaces_dominated(self):
        opt = MultiObjectiveOptimizer(search_space={}, objectives={})
        worse = _make_point(objectives={"q": 2.0}, score=2.0)
        opt.update_pareto_front(worse)
        better = _make_point(objectives={"q": 0.5}, score=0.5)
        opt.update_pareto_front(better)
        assert len(opt.pareto_front) == 1
        assert opt.pareto_front[0].objectives["q"] == 0.5


class TestNSGA2Optimizer:
    def test_fast_non_dominated_sort(self):
        opt = NSGA2Optimizer(search_space={}, objectives={})
        points = [
            _make_point(objectives={"q": 0.1, "p": 0.1}),
            _make_point(objectives={"q": 0.5, "p": 0.5}),
            _make_point(objectives={"q": 0.9, "p": 0.9}),
        ]
        fronts = opt._fast_non_dominated_sort(points)
        assert len(fronts) >= 1
        assert points[0] in fronts[0]

    def test_calculate_crowding_distance(self):
        opt = NSGA2Optimizer(search_space={}, objectives={})
        points = [
            _make_point(objectives={"q": 0.1}),
            _make_point(objectives={"q": 0.5}),
            _make_point(objectives={"q": 0.9}),
        ]
        opt._calculate_crowding_distance(points)
        assert points[0].crowding_distance == float('inf')
        assert points[-1].crowding_distance == float('inf')
        assert points[1].crowding_distance > 0

    def test_calculate_crowding_distance_empty(self):
        opt = NSGA2Optimizer(search_space={}, objectives={})
        opt._calculate_crowding_distance([])

    def test_random_sample_categorical(self):
        opt = NSGA2Optimizer(
            search_space={"x": {"type": "categorical", "choices": ["a", "b", "c"]}},
            objectives={},
        )
        sample = opt._random_sample()
        assert sample["x"] in ["a", "b", "c"]

    def test_random_sample_int(self):
        opt = NSGA2Optimizer(
            search_space={"n": {"type": "int", "min": 1, "max": 10}},
            objectives={},
        )
        sample = opt._random_sample()
        assert 1 <= sample["n"] <= 10

    def test_random_sample_float(self):
        opt = NSGA2Optimizer(
            search_space={"r": {"type": "float", "min": 0.0, "max": 1.0}},
            objectives={},
        )
        sample = opt._random_sample()
        assert 0.0 <= sample["r"] <= 1.0

    def test_evaluate_all_objectives(self):
        opt = NSGA2Optimizer(
            search_space={},
            objectives={"q": lambda p: p.get("x", 0) ** 2},
        )
        results = opt.evaluate_all_objectives({"x": 3})
        assert results["q"] == 9.0

    def test_update_pareto_front(self):
        opt = NSGA2Optimizer(search_space={}, objectives={})
        front = []
        good = _make_point(objectives={"q": 0.5}, score=0.5)
        opt.update_pareto_front(good, front)
        assert len(front) == 1

        bad = _make_point(objectives={"q": 1.0}, score=1.0)
        opt.update_pareto_front(bad, front)
        assert len(front) == 1

    def test_optimize(self):
        opt = NSGA2Optimizer(
            search_space={"x": {"type": "float", "min": 0, "max": 10}},
            objectives={"q": lambda p: (p.get("x", 5) - 3) ** 2},
            config={"population_size": 5, "max_generations": 2},
        )
        result = opt.optimize()
        assert result.n_evaluations > 0
        assert len(result.all_evaluated) > 0
