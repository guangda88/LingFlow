#!/usr/bin/env python3
"""
LingMinOpt 灵极优框架 - 简化演示程序
使用现有的API展示功能
"""

import time
from pathlib import Path

print("=" * 60)
print("LingMinOpt 灵极优框架 - 演示程序（简化版）")
print("=" * 60)

# ============================================================================
# Demo 1: 搜索空间
# ============================================================================
print("\n📊 Demo 1: 创建搜索空间")
print("-" * 60)

try:
    from lingflow.self_optimizer.phase4 import SearchSpace

    search_space = SearchSpace()
    search_space.add_discrete("max_class_size", [100, 200, 300, 500])
    search_space.add_discrete("max_method_count", [10, 15, 20, 25])
    search_space.add_discrete("max_complexity", [5, 10, 15, 20])
    search_space.add_continuous("coupling_limit", 5.0, 15.0)

    print(search_space.summary())

    test_params = search_space.sample()
    print(f"\n随机采样参数: {test_params}")

except Exception as e:
    print(f"⚠️  搜索空间Demo失败: {e}")

# ============================================================================
# Demo 2: 使用现有的优化器
# ============================================================================
print("\n🎯 Demo 2: 使用现有的贝叶斯优化器")
print("-" * 60)

try:
    from lingflow.self_optimizer.phase4 import BayesianOptimizer, get_default_search_space

    # 获取默认搜索空间
    space = get_default_search_space()

    print(f"搜索空间维度: {len(space.parameters)}")

    # 定义简单的测试函数
    def test_function(params):
        # 简单的二次函数
        x = params.get("max_class_size", 200) / 100
        y = params.get("max_method_count", 15) / 10

        return x**2 + y**2  # 越小越好

    # 创建优化器
    optimizer = BayesianOptimizer(
        objective_function=test_function,
        search_space=space,
        n_trials=10
    )

    print("运行优化...")
    start_time = time.time()

    result = optimizer.run()

    elapsed = time.time() - start_time

    print(f"\n✅ 优化完成！")
    print(f"总耗时: {elapsed:.2f}秒")
    print(f"最佳参数: {result.best_params}")
    print(f"最佳分数: {result.best_score:.4f}")

except Exception as e:
    print(f"⚠️  贝叶斯优化Demo失败: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Demo 3: 多目标优化
# ============================================================================
print("\n🎯 Demo 3: 多目标优化")
print("-" * 60)

try:
    from lingflow.self_optimizer.phase4 import optimize_multiple_objectives

    def multi_objective_func(params):
        x = params.get("max_class_size", 200)
        y = params.get("max_method_count", 15)

        return {
            "f1": (x - 200)**2 / 10000,  # 最小化
            "f2": (y - 15)**2 / 100     # 最小化
        }

    result = optimize_multiple_objectives(
        objective_function=multi_objective_func,
        search_space=space,
        objectives=["f1", "f2"],
        directions=["minimize", "minimize"],
        n_iterations=20
    )

    print(f"✅ 多目标优化完成！")
    print(f"Pareto前沿点数: {len(result.pareto_front)}")

    print(f"\n前3个Pareto解:")
    for i, point in enumerate(result.pareto_front[:3]):
        print(f"  解 {i+1}:")
        print(f"    参数: {point.params}")
        print(f"    目标: f1={point.objectives['f1']:.4f}, f2={point.objectives['f2']:.4f}")

except Exception as e:
    print(f"⚠️  多目标优化Demo失败: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# Demo 4: 快速优化代码
# ============================================================================
print("\n🎯 Demo 4: 快速优化LingFlow代码结构")
print("-" * 60)

try:
    from lingflow.self_optimizer import quick_optimize

    lingflow_path = Path("/home/ai/LingFlow/lingflow")
    if lingflow_path.exists():
        print(f"分析LingFlow代码结构...")

        result = quick_optimize(
            target=str(lingflow_path),
            goal="structure",
            async_mode=False
        )

        print(f"\n✅ 代码结构优化完成！")
        print(f"最佳参数: {result.best_params}")
        print(f"最佳分数: {result.best_score:.4f}")
        print(f"实验次数: {result.experiments}")
        print(f"耗时: {result.duration:.2f}秒")

        if hasattr(result, 'improvement_percentage') and result.improvement_percentage > 0:
            print(f"改进: {result.improvement_percentage:.1f}%")
    else:
        print("⚠️  LingFlow代码路径不存在")

except Exception as e:
    print(f"⚠️  代码优化Demo失败: {e}")
    import traceback
    traceback.print_exc()

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
print("  ✓ 快速代码优化")

print("\n下一步:")
print("  1. 在你的项目中使用 SearchSpace 定义优化参数")
print("  2. 使用 BayesianOptimizer 进行参数优化")
print("  3. 使用 quick_optimize() 快速优化代码结构")
print("\n文档: LINGMINOPT_QUICK_START.md")
print("完整方案: LINGMINOPT_SELF_OPTIMIZATION_MASTER_PLAN.md")
print("=" * 60)
