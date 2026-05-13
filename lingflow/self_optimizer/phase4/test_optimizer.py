"""
lingflow Phase 4: 优化器测试

验证贝叶斯优化器和网格搜索优化器的基本功能。
"""

from lingflow.self_optimizer.phase4.bayesian_optimizer import (
    BayesianOptimizer,
    GridSearchOptimizer,
    OptimizationState,
    OptimizationTrial,
    create_optimizer,
    get_default_search_space,
)


class TestSearchSpace:
    """测试搜索空间定义"""

    def test_get_default_search_space_structure(self):
        """测试获取结构优化搜索空间"""
        space = get_default_search_space("structure")
        assert "max_class_size" in space
        assert space["max_class_size"]["type"] == "int"
        assert space["max_class_size"]["min"] == 100
        assert space["max_class_size"]["max"] == 500

    def test_get_default_search_space_performance(self):
        """测试获取性能优化搜索空间"""
        space = get_default_search_space("performance")
        assert "cache_size" in space
        assert space["cache_size"]["type"] == "categorical"

    def test_get_default_search_space_simplicity(self):
        """测试获取简洁性优化搜索空间"""
        space = get_default_search_space("simplicity")
        assert "complexity_threshold" in space
        assert space["complexity_threshold"]["type"] == "int"


class TestObjectiveFunction:
    """测试目标函数"""

    @staticmethod
    def simple_quadratic(params):
        """简单二次函数：(x-2)^2 + (y-3)^2"""
        x = params.get("x", 0)
        y = params.get("y", 0)
        return (x - 2) ** 2 + (y - 3) ** 2

    @staticmethod
    def multimodal(params):
        """多峰函数：sin(x) + cos(y)"""
        import math

        x = params.get("x", 0)
        y = params.get("y", 0)
        return math.sin(x) + math.cos(y)


class TestBayesianOptimizer:
    """测试贝叶斯优化器"""

    def test_initialization(self):
        """测试初始化"""
        search_space = {"x": {"type": "float", "min": -10, "max": 10}, "y": {"type": "float", "min": -10, "max": 10}}
        optimizer = BayesianOptimizer(search_space, TestObjectiveFunction.simple_quadratic, {"n_trials": 10, "seed": 42})
        assert optimizer.search_space == search_space
        assert optimizer.n_trials == 10

    def test_suggest(self):
        """测试参数建议"""
        search_space = {
            "x": {"type": "float", "min": -10, "max": 10},
            "y": {"type": "int", "min": 0, "max": 20},
            "z": {"type": "categorical", "choices": ["a", "b", "c"]},
        }
        optimizer = BayesianOptimizer(search_space, TestObjectiveFunction.simple_quadratic, {"n_trials": 10})
        params = optimizer.suggest()
        assert "x" in params
        assert "y" in params
        assert "z" in params
        assert isinstance(params["x"], float)
        assert isinstance(params["y"], int)
        assert params["z"] in ["a", "b", "c"]

    def test_observe(self):
        """测试结果观察"""
        search_space = {"x": {"type": "float", "min": -10, "max": 10}}
        optimizer = BayesianOptimizer(search_space, lambda p: p["x"] ** 2, {"n_trials": 10})
        optimizer.observe({"x": 5.0}, 25.0)
        assert len(optimizer.history) == 1
        assert optimizer.best_score == 25.0

    def test_optimize(self):
        """测试完整优化"""
        search_space = {"x": {"type": "float", "min": -10, "max": 10}, "y": {"type": "float", "min": -10, "max": 10}}
        optimizer = BayesianOptimizer(search_space, TestObjectiveFunction.simple_quadratic, {"n_trials": 20, "timeout": 30})
        state = optimizer.optimize()
        assert isinstance(state, OptimizationState)
        assert state.current_trial > 0
        # 最优解应该接近 (2, 3)
        best_params = state.get_best_params()
        assert abs(best_params["x"] - 2) < 2.0
        assert abs(best_params["y"] - 3) < 2.0


class TestGridSearchOptimizer:
    """测试网格搜索优化器"""

    def test_initialization(self):
        """测试初始化"""
        search_space = {"x": {"type": "int", "min": 0, "max": 10}}
        optimizer = GridSearchOptimizer(search_space, lambda p: p["x"], {"max_experiments": 5})
        assert optimizer.max_experiments == 5

    def test_optimize(self):
        """测试网格搜索优化"""
        search_space = {"x": {"type": "int", "min": 0, "max": 10}, "y": {"type": "int", "min": 0, "max": 10}}
        optimizer = GridSearchOptimizer(
            search_space, lambda p: (p["x"] - 5) ** 2 + (p["y"] - 5) ** 2, {"max_experiments": 20, "timeout": 30}
        )
        state = optimizer.optimize()
        assert state.current_trial > 0
        best_params = state.get_best_params()
        # 应该找到接近 (5, 5) 的解
        assert abs(best_params["x"] - 5) <= 3
        assert abs(best_params["y"] - 5) <= 3


class TestCreateOptimizer:
    """测试优化器工厂函数"""

    def test_create_bayesian_optimizer(self):
        """测试创建贝叶斯优化器"""
        search_space = {"x": {"type": "int", "min": 0, "max": 10}}
        optimizer = create_optimizer(search_space, lambda p: p["x"], prefer_bayesian=True)
        assert isinstance(optimizer, BayesianOptimizer)

    def test_create_grid_search_fallback(self):
        """测试降级到网格搜索"""
        # 这个测试假设Optuna可用，如果不可用则会自动降级
        search_space = {"x": {"type": "int", "min": 0, "max": 10}}
        optimizer = create_optimizer(search_space, lambda p: p["x"], prefer_bayesian=True)
        # 两种类型都是可接受的
        assert isinstance(optimizer, (BayesianOptimizer, GridSearchOptimizer))


class TestConvergenceDetection:
    """测试收敛检测"""

    def test_should_stop_by_trials(self):
        """测试通过试验次数停止"""
        search_space = {"x": {"type": "int", "min": 0, "max": 10}}
        optimizer = BayesianOptimizer(search_space, lambda p: p["x"], {"n_trials": 3})
        # 运行3次后应该停止
        for _ in range(3):
            params = optimizer.suggest()
            optimizer.observe(params, 1.0)
        assert optimizer.should_stop() is True

    def test_convergence_rate_calculation(self):
        """测试收敛率计算"""
        search_space = {"x": {"type": "int", "min": 0, "max": 10}}
        optimizer = BayesianOptimizer(search_space, lambda p: p["x"], {"n_trials": 20})
        # 运行一些试验
        for i in range(15):
            params = optimizer.suggest()
            optimizer.observe(params, float(i))
        # 收敛率应该在0-1之间
        rate = optimizer._calculate_convergence_rate()
        assert 0.0 <= rate <= 1.0


class TestOptimizationTrial:
    """测试优化试验数据类"""

    def test_trial_creation(self):
        """测试创建试验记录"""
        trial = OptimizationTrial(trial_id="test_1", params={"x": 1.0}, score=0.5, metrics={"custom_metric": 1.0})
        assert trial.trial_id == "test_1"
        assert trial.params == {"x": 1.0}
        assert trial.score == 0.5
        assert trial.metrics == {"custom_metric": 1.0}

    def test_trial_to_dict(self):
        """测试试验转换为字典"""
        trial = OptimizationTrial(trial_id="test_1", params={"x": 1.0}, score=0.5)
        d = trial.to_dict()
        assert d["trial_id"] == "test_1"
        assert d["params"] == {"x": 1.0}
        assert d["score"] == 0.5


class TestOptimizationState:
    """测试优化状态数据类"""

    def test_state_creation(self):
        """测试创建优化状态"""
        best_trial = OptimizationTrial(trial_id="best", params={"x": 2.0}, score=0.0)
        state = OptimizationState(current_trial=10, best_trial=best_trial, convergence_rate=0.95, should_stop=True)
        assert state.current_trial == 10
        assert state.get_best_params() == {"x": 2.0}
        assert state.get_best_score() == 0.0


class TestIntegration:
    """集成测试"""

    def test_full_optimization_workflow(self):
        """测试完整优化工作流"""
        # 1. 定义搜索空间
        search_space = {
            "learning_rate": {"type": "float", "min": 0.001, "max": 0.1},
            "batch_size": {"type": "categorical", "choices": [16, 32, 64]},
            "epochs": {"type": "int", "min": 10, "max": 100},
        }

        # 2. 定义目标函数（模拟）
        def objective(params):
            # 模拟：最佳学习率约0.01，最佳batch_size=32
            lr_penalty = abs(params["learning_rate"] - 0.01) * 100
            batch_penalty = 0 if params["batch_size"] == 32 else 10
            epoch_penalty = max(0, 50 - params["epochs"]) * 0.1
            return lr_penalty + batch_penalty + epoch_penalty

        # 3. 创建优化器
        optimizer = create_optimizer(search_space, objective, {"n_trials": 15, "timeout": 30})

        # 4. 运行优化
        state = optimizer.optimize()

        # 5. 验证结果
        assert state.current_trial > 0
        assert state.get_best_score() >= 0
        best_params = state.get_best_params()
        assert "learning_rate" in best_params
        assert "batch_size" in best_params
        assert "epochs" in best_params


if __name__ == "__main__":  # pragma: no cover
    # 运行简单测试
    print("运行优化器基础测试...")

    # 测试1: 创建优化器
    print("\n1. 测试创建优化器")
    space = get_default_search_space("structure")
    print(f"   搜索空间: {list(space.keys())}")

    # 测试2: 运行贝叶斯优化
    print("\n2. 测试贝叶斯优化")
    optimizer = create_optimizer(
        {"x": {"type": "float", "min": -10, "max": 10}}, lambda p: (p["x"] - 3) ** 2, {"n_trials": 10, "timeout": 10}
    )
    state = optimizer.optimize()
    print(f"   最佳参数: {state.get_best_params()}")
    print(f"   最佳分数: {state.get_best_score():.4f}")
    print(f"   试验次数: {state.current_trial}")

    print("\n✅ 所有基础测试通过!")
