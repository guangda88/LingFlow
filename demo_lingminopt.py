#!/usr/bin/env python3
"""
LingMinOpt 灵极优框架 - 演示程序
展示贝叶斯优化和多目标优化的使用
"""

import time
import numpy as np
from pathlib import Path

# 导入LingMinOpt
from lingflow.self_optimizer.phase4 import (
    SearchSpace,
    OptimizationEngine,
    OptimizationConfig,
    MultiObjectiveOptimizer
)

# 导入评估器
from lingflow.self_optimizer.evaluator import StructureEvaluator

print("=" * 60)
print("LingMinOpt 灵极优框架 - 演示程序")
print("=" * 60)

# ============================================================================
# Demo 1: 基础搜索空间
# ============================================================================
print("\n📊 Demo 1: 创建搜索空间")
print("-" * 60)

search_space = SearchSpace()
search_space.add_discrete("max_class_size", [100, 200, 300, 500])
search_space.add_discrete("max_method_count", [10, 15, 20, 25])
search_space.add_discrete("max_complexity", [5, 10, 15, 20])
search_space.add_continuous("coupling_limit", 5.0, 15.0)

print(search_space.summary())

# 测试参数映射
test_params = search_space.sample()
print(f"\n随机采样参数: {test_params}")

vector = search_space.map_to_vector(test_params)
print(f"编码向量: {vector}")

recovered_params = search_space.map_to_params(vector)
print(f"解码参数: {recovered_params}")

# ============================================================================
# Demo 2: 贝叶斯优化（模拟目标函数）
# ============================================================================
print("\n🎯 Demo 2: 贝叶斯优化")
print("-" * 60)

# 定义一个简单的测试函数（Rastrigin函数）
def rastrigin_function(params):
    """Rastrigin函数（多峰优化测试函数）"""
    x = params["x"]
    y = params["y"]
    A = 10
    return A * 2 + (x**2 - A * np.cos(2 * np.pi * x)) + (y**2 - A * np.cos(2 * np.pi * y))

# 创建搜索空间
rastrigin_space = SearchSpace()
rastrigin_space.add_continuous("x", -5.12, 5.12)
rastrigin_space.add_continuous("y", -5.12, 5.12)

# 配置优化器
config = OptimizationConfig(
    max_experiments=30,
    time_budget=60,
    early_stopping_patience=10,
    acquisition_function="EI",
    n_initial_points=10
)

# 创建优化器
optimizer = OptimizationEngine(
    search_space=rastrigin_space,
    evaluate=rastrigin_function,
    config=config
)

# 运行优化
print(f"运行优化（最多{config.max_experiments}次实验）...")
start_time = time.time()

result = optimizer.run()

elapsed = time.time() - start_time

# 显示结果
print(f"\n✅ 优化完成！")
print(f"总实验次数: {result.total_experiments}")
print(f"总耗时: {result.total_time:.2f}秒")
print(f"\n最佳参数:")
for key, value in result.best_params.items():
    print(f"  {key}: {value:.4f}")
print(f"最佳目标值: {result.best_objective:.4f}")
print(f"理论最优值: 0.0000 (在x=0, y=0)")
print(f"误差: {abs(result.best_objective):.4f}")

# ============================================================================
# Demo 3: 多目标优化
# ============================================================================
print("\n🎯 Demo 3: 多目标优化 (Pareto前沿)")
print("-" * 60)

def multi_objective_test(params):
    """多目标测试函数"""
    x = params["x"]
    y = params["y"]

    # 两个冲突的目标
    f1 = x**2 + y**2  # 最小化
    f2 = (x - 2)**2 + (y - 2)**2  # 最小化

    return {
        "f1": f1,
        "f2": f2
    }

# 创建搜索空间
multi_space = SearchSpace()
multi_space.add_continuous("x", -5, 5)
multi_space.add_continuous("y", -5, 5)

# 创建多目标优化器
multi_opt = MultiObjectiveOptimizer(
    search_space=multi_space,
    evaluate=multi_objective_test,
    objectives=["f1", "f2"],
    directions=["minimize", "minimize"]
)

print(f"运行多目标优化...")
pareto_front = multi_opt.run(max_iterations=50)

print(f"\n✅ 找到 {len(pareto_front)} 个Pareto最优解")
print(f"\n前5个Pareto解:")
for i, point in enumerate(pareto_front[:5]):
    print(f"  解 {i+1}:")
    print(f"    参数: x={point.params['x']:.3f}, y={point.params['y']:.3f}")
    print(f"    目标: f1={point.objectives['f1']:.3f}, f2={point.objectives['f2']:.3f}")

# ============================================================================
# Demo 4: 实际代码优化（如果LingFlow代码存在）
# ============================================================================
print("\n🎯 Demo 4: 实际代码结构优化")
print("-" * 60)

lingflow_path = Path("/home/ai/LingFlow/lingflow")
if lingflow_path.exists():
    # 创建代码结构评估器
    evaluator = StructureEvaluator(target_path=str(lingflow_path))

    # 定义代码优化搜索空间
    code_space = SearchSpace()
    code_space.add_discrete("max_class_size", [100, 200, 300, 500])
    code_space.add_discrete("max_method_count", [10, 15, 20, 25])
    code_space.add_discrete("max_complexity", [5, 10, 15, 20])
    code_space.add_continuous("coupling_limit", 5.0, 15.0)

    # 配置优化器（较少实验次数）
    code_config = OptimizationConfig(
        max_experiments=15,
        time_budget=120,
        early_stopping_patience=5,
        acquisition_function="EI"
    )

    # 创建优化器
    code_optimizer = OptimizationEngine(
        search_space=code_space,
        evaluate=evaluator.evaluate,
        config=code_config
    )

    print(f"分析LingFlow代码结构...")
    print(f"目标: 最小化结构违规数量")
    print(f"运行优化（最多{code_config.max_experiments}次实验）...")

    # 运行优化
    code_result = code_optimizer.run()

    # 显示结果
    print(f"\n✅ 代码结构优化完成！")
    print(f"总实验次数: {code_result.total_experiments}")
    print(f"总耗时: {code_result.total_time:.2f}秒")
    print(f"\n最佳参数:")
    for key, value in code_result.best_params.items():
        print(f"  {key}: {value}")
    print(f"最小违规数: {int(code_result.best_objective)}")

    if code_result.improvement_percentage > 0:
        print(f"改进: {code_result.improvement_percentage:.1f}%")
else:
    print("⚠️  LingFlow代码路径不存在，跳过此demo")

# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 60)
print("🎉 演示完成！")
print("=" * 60)
print("\nLingMinOpt 核心特性:")
print("  ✓ 灵活的搜索空间定义")
print("  ✓ 高效的贝叶斯优化")
print("  ✓ 多目标优化支持")
print("  ✓ 实际代码结构优化")
print("\n下一步:")
print("  1. 在你的项目中使用 SearchSpace 定义优化参数")
print("  2. 实现你的评估函数")
print("  3. 运行 OptimizationEngine 进行优化")
print("  4. 查看优化结果并应用最佳参数")
print("\n文档: LINGMINOPT_SELF_OPTIMIZATION_MASTER_PLAN.md")
print("示例: python demo_lingminopt.py")
print("=" * 60)
