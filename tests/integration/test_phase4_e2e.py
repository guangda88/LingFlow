"""
Phase 4 端到端集成测试

测试贝叶斯优化系统的完整工作流，包括：
- 贝叶斯优化器
- 参数存储和检索
- 缓存机制
- 多目标优化
- 敏感性分析
"""

import time
from pathlib import Path
from typing import Any, Dict

import pytest

from lingflow.self_optimizer.phase4.bayesian_optimizer import (
    BayesianOptimizer,
    GridSearchOptimizer,
    OptimizationState,
    OptimizationTrial,
    create_optimizer,
)
from lingflow.self_optimizer.phase4.cache import ParameterCache
from lingflow.self_optimizer.phase4.engine import OptimizationEngine
from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore


@pytest.mark.phase4
class TestBayesianOptimizer:
    """测试贝叶斯优化器"""

    def test_initialization(self, sample_search_space, sample_objective):
        """测试优化器初始化"""
        optimizer = BayesianOptimizer(sample_search_space, sample_objective, config={"n_trials": 5, "timeout": 10})

        assert optimizer.search_space == sample_search_space
        assert optimizer.objective == sample_objective
        assert optimizer.n_trials == 5
        assert optimizer.timeout == 10

    def test_suggest_parameters(self, sample_search_space, sample_objective):
        """测试参数建议"""
        optimizer = BayesianOptimizer(sample_search_space, sample_objective)

        params = optimizer.suggest()

        assert isinstance(params, dict)
        assert "max_class_size" in params
        assert "max_method_count" in params
        assert "max_complexity" in params

        # 验证参数范围
        assert 100 <= params["max_class_size"] <= 500
        assert params["max_method_count"] in [10, 15, 20]
        assert 5 <= params["max_complexity"] <= 20

    def test_observe_results(self, sample_search_space, sample_objective):
        """测试结果观察"""
        optimizer = BayesianOptimizer(sample_search_space, sample_objective)

        params = {"max_class_size": 300, "max_method_count": 15, "max_complexity": 10}
        score = 0.5

        optimizer.observe(params, score, duration=1.0)

        assert optimizer.trial_count == 1
        assert len(optimizer.history) == 1
        assert optimizer.best_score == 0.5
        assert optimizer.best_params == params

    def test_optimization_convergence(self, sample_search_space, sample_objective):
        """测试优化收敛"""
        optimizer = BayesianOptimizer(sample_search_space, sample_objective, config={"n_trials": 20, "timeout": 30})

        state = optimizer.optimize()

        assert isinstance(state, OptimizationState)
        assert state.current_trial > 0
        assert state.should_stop is True
        assert state.best_trial is not None
        assert len(state.history) > 0

    def test_should_stop_conditions(self, sample_search_space, sample_objective):
        """测试停止条件"""
        optimizer = BayesianOptimizer(sample_search_space, sample_objective, config={"n_trials": 3, "timeout": 60})

        # 初始不应该停止
        assert not optimizer.should_stop()

        # 运行几次后应该停止
        for _ in range(3):
            params = optimizer.suggest()
            optimizer.observe(params, 1.0)

        assert optimizer.should_stop()

    def test_timeout_stopping(self, sample_search_space):
        """测试超时停止"""
        import time

        # 创建一个会延迟的目标函数
        def slow_objective(params):
            time.sleep(0.2)  # 每次评估耗时200ms
            x = params.get("max_class_size", 100)
            y = params.get("max_method_count", 10)
            return ((x - 300) ** 2 + (y - 15) ** 2) / 10000

        optimizer = BayesianOptimizer(
            sample_search_space, slow_objective, config={"n_trials": 100, "timeout": 0.5}  # 0.5秒超时
        )

        start = time.time()
        state = optimizer.optimize()
        elapsed = time.time() - start

        # 应该因为超时而停止
        assert state.should_stop is True
        # 由于每次评估需要0.2秒，最多执行2次就超时
        assert elapsed >= 0.4  # 至少执行了两次
        assert elapsed < 1.0  # 但不应该太久


@pytest.mark.phase4
class TestGridSearchOptimizer:
    """测试网格搜索优化器（降级方案）"""

    def test_grid_search_fallback(self, sample_search_space, sample_objective):
        """测试网格搜索降级"""
        optimizer = GridSearchOptimizer(sample_search_space, sample_objective, config={"max_experiments": 10, "timeout": 30})

        state = optimizer.optimize()

        assert isinstance(state, OptimizationState)
        assert state.current_trial > 0
        assert state.best_trial is not None

    def test_grid_search_parameter_generation(self, sample_search_space, sample_objective):
        """测试网格搜索参数生成"""
        optimizer = GridSearchOptimizer(sample_search_space, sample_objective, config={"max_experiments": 5})

        points = optimizer._generate_grid_points()

        assert len(points) == 5
        for point in points:
            assert "max_class_size" in point
            assert "max_method_count" in point


@pytest.mark.phase4
class TestParameterStorage:
    """测试参数存储"""

    def test_store_and_retrieve(self, tmp_path):
        """测试存储和检索"""
        store = FileSystemParameterStore(base_path=str(tmp_path / "params"))

        params = {"max_class_size": 300, "max_method_count": 15}
        metadata = {"goal": "structure", "timestamp": "2024-01-01"}

        # 存储
        version = store.save(params, metadata=metadata)

        # 检索
        retrieved = store.load(version.version_id)

        assert retrieved is not None
        assert retrieved.params == params

    def test_storage_persistence(self, tmp_path):
        """测试持久化"""
        storage_path = tmp_path / "params"

        # 第一次存储
        store1 = FileSystemParameterStore(base_path=str(storage_path))
        version1 = store1.save({"param": "value1"}, {})

        # 第二次读取
        store2 = FileSystemParameterStore(base_path=str(storage_path))
        retrieved = store2.load(version1.version_id)

        assert retrieved is not None
        assert retrieved.params["param"] == "value1"

    def test_get_latest_params(self, tmp_path):
        """测试获取最新参数"""
        store = FileSystemParameterStore(base_path=str(tmp_path / "params"))

        # 存储多个版本
        store.save({"param": "value1"}, {"iteration": 1})
        store.save({"param": "value2"}, {"iteration": 2})
        store.save({"param": "value3"}, {"iteration": 3})

        # 获取最新版本
        latest = store.get_latest()

        assert latest is not None
        assert latest.params["param"] == "value3"


@pytest.mark.phase4
class TestOptimizationCache:
    """测试优化缓存"""

    def test_cache_hit(self):
        """测试缓存命中"""
        cache = ParameterCache(max_size=10)

        params = {"max_class_size": 300, "max_method_count": 15}
        result = {"score": 0.5, "metrics": {}}

        cache.put(params, result)

        cached = cache.get(params)

        assert cached is not None
        assert cached["score"] == 0.5

    def test_cache_miss(self):
        """测试缓存未命中"""
        cache = ParameterCache()

        params = {"max_class_size": 300}

        cached = cache.get(params)

        assert cached is None

    def test_cache_size_limit(self):
        """测试缓存大小限制"""
        cache = ParameterCache(max_size=3)

        # 添加超过限制的项
        for i in range(5):
            params = {"param": i}
            cache.put(params, {"value": i})

        # 应该只保留最近的项
        assert cache.get({"param": 0}) is None
        assert cache.get({"param": 4}) is not None

    def test_cache_clear(self):
        """测试缓存清理"""
        cache = ParameterCache()

        cache.put({"param": 1}, {"value": 1})
        assert cache.get({"param": 1}) is not None

        cache.clear()
        assert cache.get({"param": 1}) is None


@pytest.mark.phase4
class TestOptimizationEngine:
    """测试优化引擎"""

    def test_single_objective_optimization(self, temp_project):
        """测试单目标优化"""
        engine = OptimizationEngine(config={"n_trials": 5, "timeout": 30, "generate_reports": False})

        result = engine.optimize_single_objective(target_path=temp_project, goal="structure")

        assert "goal" in result
        assert "best_params" in result
        assert "best_score" in result
        assert "n_trials" in result
        assert result["goal"] == "structure"

    def test_multi_objective_optimization(self, temp_project):
        """测试多目标优化"""
        engine = OptimizationEngine(config={"generate_reports": False, "max_evaluations": 20})

        result = engine.optimize_multi_objective(
            target_path=temp_project, goals=["structure", "simplicity"], weights={"structure": 0.6, "simplicity": 0.4}
        )

        assert result["type"] == "multi_objective"
        assert "goals" in result
        assert "pareto_front_size" in result
        assert "balanced_solution" in result

    def test_sensitivity_analysis(self, temp_project):
        """测试敏感性分析"""
        engine = OptimizationEngine(config={"generate_reports": False})

        result = engine.analyze_sensitivity(target_path=temp_project, goal="structure", method="local", n_samples=10)

        assert "method" in result
        assert "parameters" in result
        assert result["method"] == "local"

    def test_optimization_history(self, temp_project):
        """测试优化历史"""
        engine = OptimizationEngine(config={"generate_reports": False})

        # 运行多次优化
        engine.optimize_single_objective(temp_project, "structure")
        engine.optimize_single_objective(temp_project, "simplicity")

        history = engine.get_optimization_history()

        assert len(history) == 2
        assert history[0]["goal"] == "structure"
        assert history[1]["goal"] == "simplicity"

    def test_clear_history(self, temp_project):
        """测试清空历史"""
        engine = OptimizationEngine(config={"generate_reports": False})

        engine.optimize_single_objective(temp_project, "structure")
        assert len(engine.get_optimization_history()) > 0

        engine.clear_history()
        assert len(engine.get_optimization_history()) == 0


@pytest.mark.phase4
class TestOptimizerFactory:
    """测试优化器工厂函数"""

    def test_create_bayesian_optimizer(self, sample_search_space, sample_objective):
        """测试创建贝叶斯优化器"""
        optimizer = create_optimizer(sample_search_space, sample_objective, config={"n_trials": 5}, prefer_bayesian=True)

        # 可能返回贝叶斯或网格搜索（取决于Optuna是否可用）
        assert isinstance(optimizer, (BayesianOptimizer, GridSearchOptimizer))

    def test_create_grid_search_optimizer(self, sample_search_space, sample_objective):
        """测试创建网格搜索优化器"""
        optimizer = create_optimizer(
            sample_search_space, sample_objective, config={"max_experiments": 5}, prefer_bayesian=False
        )

        assert isinstance(optimizer, GridSearchOptimizer)


@pytest.mark.phase4
@pytest.mark.slow
class TestOptimizationWorkflows:
    """测试完整优化工作流"""

    def test_complete_optimization_workflow(self, temp_project):
        """测试完整优化工作流：存储 -> 优化 -> 缓存"""
        # 1. 初始化
        storage_path = Path(temp_project) / "storage"
        store = FileSystemParameterStore(base_path=str(storage_path))
        cache = ParameterCache()

        # 2. 运行优化
        engine = OptimizationEngine(config={"n_trials": 5, "timeout": 30, "generate_reports": False})

        result = engine.optimize_single_objective(target_path=temp_project, goal="structure")

        # 3. 存储结果
        version = store.save(result["best_params"], metadata=result)

        # 4. 验证存储
        retrieved = store.load(version.version_id)
        assert retrieved is not None
        assert retrieved.params == result["best_params"]

        # 5. 测试缓存
        cache.put(result["best_params"], result)
        cached = cache.get(result["best_params"])
        assert cached is not None

    def test_cached_optimization(self, temp_project):
        """测试使用缓存的优化"""
        cache = ParameterCache()

        params = {"max_class_size": 300, "max_method_count": 15}
        result = {"score": 0.5, "metrics": {}}

        # 预填充缓存
        cache.put(params, result)

        # 验证缓存命中
        cached = cache.get(params)
        assert cached == result

    def test_concurrent_optimizations(self, temp_project):
        """测试并发优化（模拟）"""
        engine = OptimizationEngine(config={"n_trials": 3, "timeout": 15, "generate_reports": False})

        # 顺序运行多个优化
        results = []
        for goal in ["structure", "simplicity"]:
            result = engine.optimize_single_objective(temp_project, goal)
            results.append(result)

        assert len(results) == 2
        assert all(r["goal"] in ["structure", "simplicity"] for r in results)


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    pytest.main([__file__, "-v", "-s"])
