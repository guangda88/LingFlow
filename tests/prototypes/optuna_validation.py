"""
Optuna贝叶斯优化原型验证

验证目标：
1. Optuna基本功能是否正常工作
2. 对比网格搜索 vs 贝叶斯优化的性能
3. 测试收敛检测和早停机制
4. 评估内存占用

优化问题：Rastrigin函数 (经典多峰优化测试函数)
f(x,y) = 20 + x² - 10cos(2πx) + y² - 10cos(2πy)
全局最优解：x=0, y=0, f=0
"""

import time
import tracemalloc
from typing import Callable, Dict, List, Tuple

import numpy as np


class GridSearchOptimizer:
    """网格搜索优化器（基准对比）"""

    def __init__(self, bounds: Dict[str, Tuple[float, float]], n_points: int = 21):
        self.bounds = bounds
        self.n_points = n_points
        self.results = []

    def optimize(self, objective: Callable, max_evaluations: int = 500) -> Dict:
        """执行网格搜索"""
        start_time = time.time()
        tracemalloc.start()

        param_names = list(self.bounds.keys())
        evaluations = 0
        best_value = float("inf")
        best_params = {}

        # 生成网格点
        grids = {}
        for name, (low, high) in self.bounds.items():
            grids[name] = np.linspace(low, high, self.n_points)

        # 遍历网格
        for i, x in enumerate(grids[param_names[0]]):
            for j, y in enumerate(grids[param_names[1]]):
                if evaluations >= max_evaluations:
                    break

                params = {param_names[0]: x, param_names[1]: y}
                value = objective(params)

                if value < best_value:
                    best_value = value
                    best_params = params.copy()

                self.results.append({"params": params, "value": value, "iteration": evaluations})
                evaluations += 1

        # 清理内存
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        elapsed = time.time() - start_time

        return {
            "best_params": best_params,
            "best_value": best_value,
            "n_evaluations": evaluations,
            "elapsed_time": elapsed,
            "peak_memory_mb": peak / 1024 / 1024,
            "history": self.results,
        }


class BayesianOptimizer:
    """Optuna贝叶斯优化器"""

    def __init__(self, bounds: Dict[str, Tuple[float, float]]):
        self.bounds = bounds
        self.study = None
        self.results = []

    def optimize(
        self, objective: Callable, max_evaluations: int = 500, timeout: int = None, early_stopping: bool = True
    ) -> Dict:
        """执行贝叶斯优化"""
        try:
            import optuna
        except ImportError:
            raise ImportError("Optuna未安装。请运行: pip install optuna")

        start_time = time.time()
        tracemalloc.start()

        # 创建研究对象
        self.study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))

        # 早停回调
        def early_stopping_callback(study, trial):
            if early_stopping and len(study.trials) >= 20:
                # 检查最近10次试验的改进
                recent_trials = study.trials[-10:]
                if len(recent_trials) >= 10:
                    improvements = [recent_trials[i].value - recent_trials[i - 1].value for i in range(1, len(recent_trials))]
                    avg_improvement = sum(improvements) / len(improvements)
                    # 如果平均改进小于阈值，提前停止
                    if avg_improvement > -0.01:
                        study.stop()
            return False

        # 包装目标函数
        def trial_objective(trial):
            params = {}
            for name, (low, high) in self.bounds.items():
                params[name] = trial.suggest_float(name, low, high)

            value = objective(params)
            self.results.append({"params": params.copy(), "value": value, "iteration": len(self.results)})
            return value

        # 运行优化
        self.study.optimize(
            trial_objective,
            n_trials=max_evaluations,
            timeout=timeout,
            callbacks=[early_stopping_callback] if early_stopping else None,
            show_progress_bar=False,
        )

        # 清理内存
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        elapsed = time.time() - start_time

        return {
            "best_params": self.study.best_params,
            "best_value": self.study.best_value,
            "n_evaluations": len(self.study.trials),
            "elapsed_time": elapsed,
            "peak_memory_mb": peak / 1024 / 1024,
            "history": self.results,
            "converged": len(self.study.trials) < max_evaluations,
        }


def rastrigin_function(params: Dict[str, float]) -> float:
    """Rastrigin函数 - 多峰优化测试函数"""
    x = params["x"]
    y = params["y"]
    n = 2
    result = 10 * n + (x**2 - 10 * np.cos(2 * np.pi * x))
    result += y**2 - 10 * np.cos(2 * np.pi * y)
    return result


def sphere_function(params: Dict[str, float]) -> float:
    """Sphere函数 - 简单凸函数"""
    x = params["x"]
    y = params["y"]
    return x**2 + y**2


def simulated_costly_objective(base_func: Callable) -> Callable:
    """模拟昂贵的目标函数（如模型训练）"""

    def wrapper(params):
        # 添加计算延迟，模拟真实场景
        time.sleep(0.01)  # 10ms延迟
        return base_func(params)

    return wrapper


def run_comparison_test(n_trials: int = 100) -> Dict:
    """运行对比测试"""
    print(f"\n{'='*60}")
    print(f"Optuna原型验证测试 - {n_trials}次评估")
    print(f"{'='*60}\n")

    # 定义搜索空间
    bounds = {"x": (-5.12, 5.12), "y": (-5.12, 5.12)}

    # 测试1: Rastrigin函数（多峰）
    print("测试1: Rastrigin函数（多峰优化）")
    print("-" * 40)

    grid_optimizer = GridSearchOptimizer(bounds, n_points=int(np.sqrt(n_trials)))
    costly_rastrigin = simulated_costly_objective(rastrigin_function)
    grid_result = grid_optimizer.optimize(costly_rastrigin, n_trials)

    bayesian_optimizer = BayesianOptimizer(bounds)
    bayesian_result = bayesian_optimizer.optimize(costly_rastrigin, max_evaluations=n_trials, early_stopping=True)

    # 测试2: Sphere函数（简单凸函数）
    print("\n测试2: Sphere函数（简单凸优化）")
    print("-" * 40)

    grid_optimizer2 = GridSearchOptimizer(bounds, n_points=int(np.sqrt(n_trials)))
    costly_sphere = simulated_costly_objective(sphere_function)
    grid_result2 = grid_optimizer2.optimize(costly_sphere, n_trials)

    bayesian_optimizer2 = BayesianOptimizer(bounds)
    bayesian_result2 = bayesian_optimizer2.optimize(costly_sphere, max_evaluations=n_trials, early_stopping=True)

    return {
        "rastrigin": {"grid": grid_result, "bayesian": bayesian_result},
        "sphere": {"grid": grid_result2, "bayesian": bayesian_result2},
    }


def print_results(results: Dict):
    """打印测试结果"""
    print(f"\n{'='*80}")
    print(f"测试结果汇总")
    print(f"{'='*80}\n")

    for func_name, data in results.items():
        print(f"\n{func_name.upper()}函数测试结果:")
        print("-" * 60)

        grid = data["grid"]
        bayesian = data["bayesian"]

        print(f"\n网格搜索:")
        print(f"  最优值: {grid['best_value']:.6f}")
        print(f"  最优参数: x={grid['best_params']['x']:.4f}, y={grid['best_params']['y']:.4f}")
        print(f"  评估次数: {grid['n_evaluations']}")
        print(f"  总耗时: {grid['elapsed_time']:.4f}秒")
        print(f"  峰值内存: {grid['peak_memory_mb']:.2f} MB")

        print(f"\n贝叶斯优化 (Optuna):")
        print(f"  最优值: {bayesian['best_value']:.6f}")
        print(f"  最优参数: x={bayesian['best_params']['x']:.4f}, y={bayesian['best_params']['y']:.4f}")
        print(f"  评估次数: {bayesian['n_evaluations']}")
        print(f"  总耗时: {bayesian['elapsed_time']:.4f}秒")
        print(f"  峰值内存: {bayesian['peak_memory_mb']:.2f} MB")
        print(f"  提前收敛: {'是' if bayesian.get('converged', False) else '否'}")

        # 性能对比
        time_reduction = (1 - bayesian["elapsed_time"] / grid["elapsed_time"]) * 100
        eval_reduction = (1 - bayesian["n_evaluations"] / grid["n_evaluations"]) * 100
        quality_diff = (
            ((bayesian["best_value"] - grid["best_value"]) / abs(grid["best_value"]) * 100) if grid["best_value"] != 0 else 0
        )

        print(f"\n性能提升:")
        print(f"  时间减少: {time_reduction:.1f}%")
        print(f"  评估次数减少: {eval_reduction:.1f}%")
        print(f"  解质量差异: {quality_diff:+.1f}%")

    # 验证结论
    print(f"\n{'='*80}")
    print(f"验证结论")
    print(f"{'='*80}")

    rastrigin_bayes = results["rastrigin"]["bayesian"]
    sphere_bayes = results["sphere"]["bayesian"]
    rastrigin_grid = results["rastrigin"]["grid"]
    sphere_grid = results["sphere"]["grid"]

    checks = {
        "Optuna正常运行": True,
        f"优化时间减少>40%": any(
            (1 - results[k]["bayesian"]["elapsed_time"] / results[k]["grid"]["elapsed_time"]) * 100 > 40
            for k in ["rastrigin", "sphere"]
        ),
        f"内存占用<200MB": all(r["bayesian"]["peak_memory_mb"] < 200 for r in results.values()),
        f"参数质量不降低（更好或相当）": rastrigin_bayes["best_value"] <= rastrigin_grid["best_value"] * 1.1
        and sphere_bayes["best_value"] <= sphere_grid["best_value"] * 1.1,
    }

    for check, passed in checks.items():
        status = "✓ 通过" if passed else "✗ 未通过"
        print(f"  [{status}] {check}")

    all_passed = all(checks.values())
    print(f"\n总体结论: {'✓ 验证通过 - Optuna可用于生产' if all_passed else '✗ 验证失败 - 需要进一步调查'}")


if __name__ == "__main__":
    # 运行验证测试
    results = run_comparison_test(n_trials=100)
    print_results(results)
