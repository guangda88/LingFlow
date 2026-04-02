import numpy as np
from lingflow.self_optimizer.phase4.search_space import Parameter, ParameterType, SearchSpace


class TestParameter:
    def test_validate_discrete_valid(self):
        p = Parameter(name="depth", type=ParameterType.DISCRETE, choices=[5, 10, 15, 20])
        assert p.validate(10) is True
        assert p.validate(5) is True

    def test_validate_discrete_invalid(self):
        p = Parameter(name="depth", type=ParameterType.DISCRETE, choices=[5, 10, 15, 20])
        assert p.validate(7) is False

    def test_validate_continuous_valid(self):
        p = Parameter(name="lr", type=ParameterType.CONTINUOUS, min_value=0.001, max_value=0.1)
        assert p.validate(0.05) is True
        assert p.validate(0.001) is True
        assert p.validate(0.1) is True

    def test_validate_continuous_invalid(self):
        p = Parameter(name="lr", type=ParameterType.CONTINUOUS, min_value=0.001, max_value=0.1)
        assert p.validate(0.0) is False
        assert p.validate(0.2) is False

    def test_validate_categorical_valid(self):
        p = Parameter(name="opt", type=ParameterType.CATEGORICAL, choices=["adam", "sgd"])
        assert p.validate("adam") is True
        assert p.validate("sgd") is True

    def test_validate_categorical_invalid(self):
        p = Parameter(name="opt", type=ParameterType.CATEGORICAL, choices=["adam", "sgd"])
        assert p.validate("rmsprop") is False


class TestSearchSpace:
    def test_add_discrete(self):
        ss = SearchSpace()
        ss.add_discrete("depth", [5, 10, 15])
        assert "depth" in ss.parameters
        assert ss.parameters["depth"].type == ParameterType.DISCRETE
        assert ss.parameters["depth"].choices == [5, 10, 15]

    def test_add_continuous(self):
        ss = SearchSpace()
        ss.add_continuous("lr", 0.001, 0.1)
        assert "lr" in ss.parameters
        assert ss.parameters["lr"].type == ParameterType.CONTINUOUS
        assert ss.parameters["lr"].min_value == 0.001
        assert ss.parameters["lr"].max_value == 0.1

    def test_add_categorical(self):
        ss = SearchSpace()
        ss.add_categorical("optimizer", ["adam", "sgd", "rmsprop"])
        assert "optimizer" in ss.parameters
        assert ss.parameters["optimizer"].type == ParameterType.CATEGORICAL

    def test_sample_returns_valid_values(self):
        ss = SearchSpace()
        ss.add_discrete("depth", [5, 10, 15])
        ss.add_continuous("lr", 0.001, 0.1)
        ss.add_categorical("opt", ["adam", "sgd"])
        sample = ss.sample()
        assert sample["depth"] in [5, 10, 15]
        assert 0.001 <= sample["lr"] <= 0.1
        assert sample["opt"] in ["adam", "sgd"]

    def test_map_to_vector_and_back(self):
        ss = SearchSpace()
        ss.add_discrete("depth", [5, 10, 15])
        ss.add_continuous("lr", 0.0, 1.0)
        params = {"depth": 10, "lr": 0.5}
        vector = ss.map_to_vector(params)
        recovered = ss.map_to_params(vector)
        assert recovered["depth"] == 10
        assert abs(recovered["lr"] - 0.5) < 0.01

    def test_map_to_vector_discrete_one_hot(self):
        ss = SearchSpace()
        ss.add_discrete("x", [1, 2, 3])
        v = ss.map_to_vector({"x": 2})
        np.testing.assert_array_equal(v, [0.0, 1.0, 0.0])

    def test_map_to_vector_categorical_one_hot(self):
        ss = SearchSpace()
        ss.add_categorical("opt", ["a", "b", "c"])
        v = ss.map_to_vector({"opt": "c"})
        np.testing.assert_array_equal(v, [0.0, 0.0, 1.0])

    def test_map_to_vector_continuous_normalized(self):
        ss = SearchSpace()
        ss.add_continuous("x", 0.0, 10.0)
        v = ss.map_to_vector({"x": 5.0})
        assert abs(v[0] - 0.5) < 1e-10

    def test_dimension_mixed(self):
        ss = SearchSpace()
        ss.add_discrete("depth", [5, 10, 15])
        ss.add_continuous("lr", 0.0, 1.0)
        ss.add_categorical("opt", ["adam", "sgd"])
        assert ss.dimension == 3 + 1 + 2

    def test_dimension_empty(self):
        ss = SearchSpace()
        assert ss.dimension == 0

    def test_summary(self):
        ss = SearchSpace()
        ss.add_discrete("depth", [5, 10])
        ss.add_continuous("lr", 0.0, 1.0)
        s = ss.summary()
        assert "depth" in s
        assert "continuous" in s
        assert "Total parameters: 2" in s

    def test_map_to_params_roundtrip_categorical(self):
        ss = SearchSpace()
        ss.add_categorical("opt", ["adam", "sgd", "rmsprop"])
        original = {"opt": "adam"}
        vector = ss.map_to_vector(original)
        recovered = ss.map_to_params(vector)
        assert recovered["opt"] == "adam"

    def test_map_to_vector_multi_param(self):
        ss = SearchSpace()
        ss.add_discrete("d", [1, 2])
        ss.add_continuous("c", 0.0, 1.0)
        ss.add_categorical("k", ["a", "b"])
        v = ss.map_to_vector({"d": 1, "c": 0.5, "k": "b"})
        assert len(v) == 2 + 1 + 2
        assert v[0] == 1.0
        assert v[1] == 0.0
        assert abs(v[2] - 0.5) < 1e-10
        assert v[3] == 0.0
        assert v[4] == 1.0
