import pytest

from lingflow.self_optimizer.phase4.sensitivity import (
    SensitivityResult,
    SobolResult,
    SensitivityAnalyzer,
    analyze_sensitivity,
)


class TestSensitivityResult:
    def test_to_dict(self):
        r = SensitivityResult(
            parameter_name="x",
            sensitivity_score=0.8,
            method="local",
            baseline_value=1.0,
            variations=[1.1, 0.9],
            variation_impacts=[0.1, 0.2],
        )
        d = r.to_dict()
        assert d["parameter"] == "x"
        assert d["sensitivity_score"] == 0.8
        assert d["variations"] == [1.1, 0.9]


class TestSobolResult:
    def test_get_most_sensitive(self):
        r = SobolResult(
            first_order={"x": 0.5, "y": 0.3},
            total_order={"x": 0.6, "y": 0.4},
            parameters=["x", "y"],
        )
        top = r.get_most_sensitive(n=1)
        assert top[0][0] == "x"
        assert top[0][1] == 0.6

    def test_to_dict(self):
        r = SobolResult(
            first_order={"x": 0.5},
            total_order={"x": 0.6},
            parameters=["x"],
        )
        d = r.to_dict()
        assert d["first_order"]["x"] == 0.5


class TestSensitivityAnalyzer:
    @pytest.fixture
    def analyzer(self):
        search_space = {
            "x": {"type": "float", "min": 0.0, "max": 10.0},
            "y": {"type": "int", "min": 1, "max": 5},
            "opt": {"type": "categorical", "choices": ["adam", "sgd"]},
        }

        def objective(params):
            return params.get("x", 0) ** 2

        return SensitivityAnalyzer(search_space, objective, base_params={"x": 5.0, "y": 3, "opt": "adam"})

    def test_get_default_params(self):
        search_space = {
            "x": {"type": "float", "min": 0.0, "max": 10.0},
            "y": {"type": "int", "min": 1, "max": 5},
            "opt": {"type": "categorical", "choices": ["adam", "sgd"]},
        }
        analyzer = SensitivityAnalyzer(search_space, lambda p: 0)
        assert analyzer.base_params["x"] == 5.0
        assert analyzer.base_params["y"] == 3
        assert analyzer.base_params["opt"] == "adam"

    def test_get_default_params_log(self):
        search_space = {"r": {"type": "log", "min": 0.001, "max": 1.0}}
        analyzer = SensitivityAnalyzer(search_space, lambda p: 0)
        assert 0.001 <= analyzer.base_params["r"] <= 1.0

    def test_analyze_local(self, analyzer):
        results = analyzer.analyze_local(n_samples=3, perturbation_ratio=0.2)
        assert "x" in results
        assert "y" in results
        assert "opt" in results
        for r in results.values():
            assert isinstance(r, SensitivityResult)

    def test_analyze_local_categorical(self, analyzer):
        results = analyzer.analyze_local(n_samples=3)
        opt_result = results["opt"]
        assert len(opt_result.variations) == 2
        assert "adam" in opt_result.variations
        assert "sgd" in opt_result.variations

    def test_analyze_local_exception_handling(self):
        search_space = {"x": {"type": "float", "min": 0.0, "max": 10.0}}
        call_count = [0]

        def failing_obj(params):
            call_count[0] += 1
            if call_count[0] > 1:
                raise ValueError("boom")
            return 1.0

        analyzer = SensitivityAnalyzer(search_space, failing_obj, base_params={"x": 5.0})
        results = analyzer.analyze_local(n_samples=3)
        assert "x" in results

    def test_analyze_global_simple(self, analyzer):
        results = analyzer.analyze_global_sobol(n_samples=5)
        assert isinstance(results, SobolResult)
        assert "x" in results.first_order
        assert "y" in results.total_order

    def test_analyze_morris_no_salib(self, analyzer):
        results = analyzer.analyze_morris(n_trajectories=5)
        assert isinstance(results, dict)


class TestAnalyzeSensitivity:
    def test_local_method(self):
        search_space = {"x": {"type": "float", "min": 0.0, "max": 10.0}}
        results = analyze_sensitivity(search_space, lambda p: p["x"] ** 2, {"x": 5.0}, method="local")
        assert "x" in results

    def test_sobol_method(self):
        search_space = {"x": {"type": "float", "min": 0.0, "max": 10.0}}
        results = analyze_sensitivity(search_space, lambda p: p["x"] ** 2, {"x": 5.0}, method="sobol", n_samples=5)
        assert isinstance(results, SobolResult)

    def test_unknown_method(self):
        search_space = {"x": {"type": "float", "min": 0.0, "max": 10.0}}
        try:
            analyze_sensitivity(search_space, lambda p: 0, {"x": 5.0}, method="unknown")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "unknown" in str(e)
