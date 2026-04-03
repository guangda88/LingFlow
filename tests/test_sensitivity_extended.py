"""Extended tests for sensitivity analysis covering remaining gaps."""
import numpy as np
import pytest

from lingflow.self_optimizer.phase4.sensitivity import (
    SensitivityResult,
    SobolResult,
    SensitivityAnalyzer,
    analyze_sensitivity,
)


def simple_objective(params):
    return params.get("x", 0) ** 2 + params.get("y", 0)


SIMPLE_SPACE = {
    "x": {"type": "float", "min": -5.0, "max": 5.0},
    "y": {"type": "float", "min": -10.0, "max": 10.0},
}


class TestSensitivityResultDefaults:
    def test_default_timestamp(self):
        import time
        before = time.time()
        r = SensitivityResult(parameter_name="x", sensitivity_score=0.5, method="local", baseline_value=1.0)
        after = time.time()
        assert before <= r.timestamp <= after

    def test_default_empty_lists(self):
        r = SensitivityResult(parameter_name="x", sensitivity_score=0.5, method="local", baseline_value=1.0)
        assert r.variations == []
        assert r.variation_impacts == []


class TestSobolResultDefaults:
    def test_default_timestamp(self):
        import time
        before = time.time()
        r = SobolResult(first_order={}, total_order={}, parameters=[])
        after = time.time()
        assert before <= r.timestamp <= after

    def test_get_most_sensitive_with_n(self):
        r = SobolResult(
            first_order={"a": 0.1, "b": 0.2, "c": 0.3},
            total_order={"a": 0.3, "b": 0.5, "c": 0.1},
            parameters=["a", "b", "c"],
        )
        top = r.get_most_sensitive(n=2)
        assert len(top) == 2
        assert top[0][0] == "b"
        assert top[1][0] == "a"

    def test_to_dict(self):
        r = SobolResult(
            first_order={"x": 0.5},
            total_order={"x": 0.7},
            parameters=["x"],
        )
        d = r.to_dict()
        assert d["first_order"] == {"x": 0.5}
        assert d["total_order"] == {"x": 0.7}
        assert d["parameters"] == ["x"]


class TestGetDefaultParamsLog:
    def test_log_type_midpoint(self):
        space = {
            "lr": {"type": "log", "min": 0.001, "max": 1.0},
        }
        analyzer = SensitivityAnalyzer(space, simple_objective)
        import math
        expected = math.sqrt(0.001 * 1.0)
        assert abs(analyzer.base_params["lr"] - expected) < 1e-10


class TestAnalyzeLocalEdgeCases:
    def test_zero_impact_all(self):
        constant_obj = lambda p: 42.0
        space = {"x": {"type": "float", "min": 0.0, "max": 1.0}}
        analyzer = SensitivityAnalyzer(space, constant_obj, base_params={"x": 0.5})
        results = analyzer.analyze_local(n_samples=3)
        assert results["x"].sensitivity_score == 0.0

    def test_exception_in_objective(self):
        def failing_obj(params):
            if params["x"] > 0.6:
                raise ValueError("bad")
            return params["x"]

        space = {"x": {"type": "float", "min": 0.0, "max": 1.0}}
        analyzer = SensitivityAnalyzer(space, failing_obj, base_params={"x": 0.5})
        results = analyzer.analyze_local(n_samples=3)
        assert results["x"].sensitivity_score >= 0.0

    def test_int_parameter(self):
        def obj(params):
            return params.get("n", 0) * 2

        space = {"n": {"type": "int", "min": 1, "max": 10}}
        analyzer = SensitivityAnalyzer(space, obj, base_params={"n": 5})
        results = analyzer.analyze_local(n_samples=3)
        assert "n" in results
        assert results["n"].method == "local_perturbation"

    def test_categorical_with_two_choices(self):
        def obj(params):
            return 10.0 if params["mode"] == "fast" else 1.0

        space = {"mode": {"type": "categorical", "choices": ["fast", "slow"]}}
        analyzer = SensitivityAnalyzer(space, obj, base_params={"mode": "fast"})
        results = analyzer.analyze_local()
        assert "mode" in results
        assert len(results["mode"].variations) == 2


class TestAnalyzeGlobalSimpleExtended:
    def test_simple_with_categorical(self):
        def obj(params):
            return params.get("x", 0) + (5 if params.get("mode") == "a" else 0)

        space = {
            "x": {"type": "float", "min": 0, "max": 10},
            "mode": {"type": "categorical", "choices": ["a", "b"]},
        }
        analyzer = SensitivityAnalyzer(space, obj, base_params={"x": 5, "mode": "a"})
        result = analyzer._analyze_global_simple(5)
        assert "x" in result.first_order
        assert "mode" in result.first_order

    def test_simple_partial_exceptions(self):
        call_count = [0]
        def sometimes_failing(params):
            call_count[0] += 1
            if call_count[0] > 2:
                raise RuntimeError("fail")
            return params.get("x", 0) ** 2

        space = {"x": {"type": "float", "min": 0, "max": 1}}
        analyzer = SensitivityAnalyzer(space, sometimes_failing, base_params={"x": 0.5})
        result = analyzer._analyze_global_simple(3)
        assert isinstance(result.first_order.get("x"), float)


class TestConvertSamplesToDicts:
    def test_categorical_index_clamping(self):
        space = {"m": {"type": "categorical", "choices": ["a", "b", "c"]}}
        analyzer = SensitivityAnalyzer(space, simple_objective, base_params={"m": "a"})
        samples = np.array([[0.0], [1.0], [5.0], [-1.0]])
        dicts = analyzer._convert_samples_to_dicts(samples)
        assert dicts[0]["m"] == "a"
        assert dicts[1]["m"] == "b"
        assert dicts[2]["m"] == "c"
        assert dicts[3]["m"] == "a"

    def test_int_rounding(self):
        space = {"n": {"type": "int", "min": 0, "max": 10}}
        analyzer = SensitivityAnalyzer(space, simple_objective, base_params={"n": 5})
        samples = np.array([[1.7], [2.3]])
        dicts = analyzer._convert_samples_to_dicts(samples)
        assert dicts[0]["n"] == 2
        assert dicts[1]["n"] == 2

    def test_float_passthrough(self):
        space = {"x": {"type": "float", "min": 0, "max": 1}}
        analyzer = SensitivityAnalyzer(space, simple_objective, base_params={"x": 0.5})
        samples = np.array([[0.3], [0.7]])
        dicts = analyzer._convert_samples_to_dicts(samples)
        assert isinstance(dicts[0]["x"], float)
        assert abs(dicts[0]["x"] - 0.3) < 1e-10


class TestAnalyzeSensitivityMorris:
    def test_morris_method_no_salib(self):
        result = analyze_sensitivity(
            SIMPLE_SPACE, simple_objective, {"x": 0, "y": 0},
            method="morris", n_samples=20,
        )
        assert result == {}


class TestAnalyzeSensitivityDispatch:
    def test_local_dispatch(self):
        result = analyze_sensitivity(SIMPLE_SPACE, simple_objective, {"x": 0, "y": 0}, method="local", n_samples=3)
        assert "x" in result

    def test_sobol_dispatch_no_salib(self):
        result = analyze_sensitivity(SIMPLE_SPACE, simple_objective, {"x": 0, "y": 0}, method="sobol", n_samples=5)
        assert isinstance(result, SobolResult)

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="未知"):
            analyze_sensitivity(SIMPLE_SPACE, simple_objective, method="invalid")
