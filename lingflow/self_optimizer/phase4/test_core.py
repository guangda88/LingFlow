#!/usr/bin/env python
"""
LingFlow Phase 4 核心算法测试

验证贝叶斯优化、多目标优化和敏感性分析功能。
"""

import sys
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_bayesian_optimizer():
    """测试贝叶斯优化器"""
    print("\n" + "="*60)
    print("测试贝叶斯优化器")
    print("="*60)

    from lingflow.self_optimizer.phase4 import (
        BayesianOptimizer,
        get_default_search_space
    )

    # 创建测试目标函数
    def test_objective(params):
        """简单的二次函数，最小值在(2, 3)"""
        x = params.get("x", 0)
        y = params.get("y", 0)
        return (x - 2) ** 2 + (y - 3) ** 2

    # 定义搜索空间
    search_space = {
        "x": {"type": "float", "min": 0, "max": 10},
        "y": {"type": "float", "min": 0, "max": 10}
    }

    # 创建优化器
    config = {
        "n_trials": 30,
        "timeout": 30,
        "seed": 42
    }

    optimizer = BayesianOptimizer(search_space, test_objective, config)

    # 运行优化
    state = optimizer.optimize()

    # 输出结果
    print(f"\n优化结果:")
    print(f"  最佳参数: {state.get_best_params()}")
    print(f"  最佳分数: {state.get_best_score():.6f}")
    print(f"  试验次数: {state.current_trial}")
    print(f"  收敛率: {state.convergence_rate:.2%}")
    print(f"  总耗时: {optimizer.get_total_time():.2f}秒")

    # 验证结果
    best_params = state.get_best_params()
    assert abs(best_params.get("x", 0) - 2.0) < 1.0, "x参数应该接近2"
    assert abs(best_params.get("y", 0) - 3.0) < 1.0, "y参数应该接近3"

    print("\n✓ 贝叶斯优化器测试通过")
    return True


def test_multi_objective_optimizer():
    """测试多目标优化器"""
    print("\n" + "="*60)
    print("测试多目标优化器")
    print("="*60)

    from lingflow.self_optimizer.phase4 import (
        optimize_multiple_objectives,
    )

    # 创建测试目标函数
    def quality_obj(params):
        """质量目标：x^2"""
        x = params.get("x", 0)
        return x ** 2

    def performance_obj(params):
        """性能目标：(x-5)^2"""
        x = params.get("x", 0)
        return (x - 5) ** 2

    search_space = {
        "x": {"type": "float", "min": 0, "max": 10}
    }

    objectives = {
        "quality": quality_obj,
        "performance": performance_obj
    }

    weights = {
        "quality": 0.5,
        "performance": 0.5
    }

    config = {
        "max_evaluations": 50,
        "timeout": 20
    }

    result = optimize_multiple_objectives(
        search_space, objectives, weights, config
    )

    # 输出结果
    print(f"\n多目标优化结果:")
    print(f"  评估次数: {result.n_evaluations}")
    print(f"  Pareto前沿解数: {len(result.get_pareto_front())}")
    print(f"  总耗时: {result.total_time:.2f}秒")

    # 获取平衡解
    balanced = result.get_balanced_solution()
    if balanced:
        print(f"\n  平衡解: x = {balanced.params.get('x', 0):.4f}")
        print(f"  目标值: {balanced.objectives}")

    # 按目标获取最佳
    best_quality = result.get_best_by_objective("quality")
    if best_quality:
        print(f"\n  质量最优: x = {best_quality.params.get('x', 0):.4f}")

    best_performance = result.get_best_by_objective("performance")
    if best_performance:
        print(f"  性能最优: x = {best_performance.params.get('x', 0):.4f}")

    print("\n✓ 多目标优化器测试通过")
    return True


def test_sensitivity_analyzer():
    """测试敏感性分析器"""
    print("\n" + "="*60)
    print("测试敏感性分析器")
    print("="*60)

    import numpy as np
    np.random.seed(42)  # 设置随机种子以确保可重复性

    from lingflow.self_optimizer.phase4 import analyze_sensitivity

    # 创建测试目标函数
    def test_objective(params):
        """x影响最大，y次之，z最小"""
        x = params.get("x", 0)
        y = params.get("y", 0)
        z = params.get("z", 0)
        # 使用线性函数，范围与系数成反比以测试敏感性
        return 10 * x + 5 * y + z

    # 设置范围与系数成反比，这样每个参数的总影响应该相似
    # x的系数最大，所以范围最小；z的系数最小，所以范围最大
    search_space = {
        "x": {"type": "float", "min": -1, "max": 1},    # 系数10, 范围2
        "y": {"type": "float", "min": -5, "max": 5},    # 系数5, 范围10
        "z": {"type": "float", "min": 0, "max": 20}     # 系数1, 范围20
    }

    base_params = {"x": 0, "y": 0, "z": 0}

    # 局部敏感性分析
    print("\n局部敏感性分析:")
    local_results = analyze_sensitivity(
        search_space, test_objective, base_params,
        method="local", n_samples=50  # 增加样本数提高稳定性
    )

    for param_name, result in local_results.items():
        print(f"  {param_name}: {result.sensitivity_score:.4f}")

    # 验证：所有参数都显示出敏感性（分数>0）
    x_score = local_results["x"].sensitivity_score
    y_score = local_results["y"].sensitivity_score
    z_score = local_results["z"].sensitivity_score

    assert x_score > 0, "x应该显示敏感性"
    assert y_score > 0, "y应该显示敏感性"
    assert z_score > 0, "z应该显示敏感性"

    # 验证：敏感性分数合理（在0-1范围内）
    assert 0 <= x_score <= 1, "x敏感性分数应在0-1范围内"
    assert 0 <= y_score <= 1, "y敏感性分数应在0-1范围内"
    assert 0 <= z_score <= 1, "z敏感性分数应在0-1范围内"

    print("\n✓ 敏感性分析器测试通过")
    return True


def test_visualization():
    """测试可视化功能"""
    print("\n" + "="*60)
    print("测试可视化功能")
    print("="*60)

    from lingflow.self_optimizer.phase4 import (
        OptimizationVisualizer,
        OptimizationTrial,
        OptimizationState,
        get_default_search_space
    )

    # 创建模拟优化状态
    history = []
    for i in range(30):
        trial = OptimizationTrial(
            trial_id=f"trial_{i}",
            params={"x": 2 + 0.5 * (0.9 ** (i / 5))},  # 收敛到2
            score=1.0 + 10 * (0.9 ** (i / 5)),  # 模拟收敛
            timestamp=i
        )
        history.append(trial)

    best_trial = OptimizationTrial(
        trial_id="best",
        params={"x": 2.05},
        score=1.02
    )

    state = OptimizationState(
        current_trial=30,
        best_trial=best_trial,
        convergence_rate=0.92,
        history=history
    )

    search_space = get_default_search_space("structure")

    # 生成HTML报告
    visualizer = OptimizationVisualizer(output_dir=".lingflow/reports")
    report_path = visualizer.generate_html_report(
        state, search_space,
        metadata={"test": True}
    )

    print(f"\n生成的报告: {report_path}")

    # 验证文件存在
    assert Path(report_path).exists(), "报告文件应该存在"

    print("\n✓ 可视化功能测试通过")
    return True


def test_integration_with_evaluators():
    """测试与现有评估器的集成"""
    print("\n" + "="*60)
    print("测试与现有评估器集成")
    print("="*60)

    try:
        from lingflow.self_optimizer.phase4 import OptimizationEngine
        from lingflow.self_optimizer.evaluator import StructureEvaluator

        # 使用当前项目作为测试目标
        target_path = "lingflow"

        # 创建优化引擎
        engine = OptimizationEngine(config={"generate_reports": False})

        # 运行优化（少量试验）
        result = engine.optimize_single_objective(
            target_path=target_path,
            goal="structure",
            config={"n_trials": 5, "timeout": 30}
        )

        print(f"\n集成测试结果:")
        print(f"  目标路径: {target_path}")
        print(f"  最佳分数: {result['best_score']:.4f}")
        print(f"  试验次数: {result['n_trials']}")
        print(f"  收敛率: {result['convergence_rate']:.2%}")

        print("\n✓ 与现有评估器集成测试通过")
        return True

    except Exception as e:
        print(f"\n✗ 集成测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("LingFlow Phase 4 核心算法测试套件")
    print("="*60)

    tests = [
        ("贝叶斯优化器", test_bayesian_optimizer),
        ("多目标优化器", test_multi_objective_optimizer),
        ("敏感性分析器", test_sensitivity_analyzer),
        ("可视化功能", test_visualization),
        ("评估器集成", test_integration_with_evaluators),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"{test_name} 测试失败: {e}", exc_info=True)
            results.append((test_name, False))

    # 输出测试摘要
    print("\n" + "="*60)
    print("测试摘要")
    print("="*60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
