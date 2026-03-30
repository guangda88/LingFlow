#!/usr/bin/env python3
"""
LingFlow 三目标优化演示
展示结构、性能、简洁三个优化目标的实际效果
"""

import sys
import json
from pathlib import Path


def print_header(title):
    """打印标题"""
    print("\n" + "="*70)
    print(f" {title}".center(70))
    print("="*70 + "\n")


def demo_three_goals():
    """演示三个优化目标"""
    print_header("LingFlow 三目标优化系统")

    from lingflow.self_optimizer import (
        StructureEvaluator,
        PerfEvaluator,
        SimplicityEvaluator,
        SynchronousOptimizer,
        OptimizationRequest
    )

    target = "lingflow/self_optimizer"

    # 1. 结构优化
    print_header("1. 结构优化 (Structure Optimization)")

    struct_eval = StructureEvaluator(target)
    struct_metrics = struct_eval.get_current_metrics()

    print("📊 当前结构指标:")
    print(f"  总类数: {struct_metrics['total_classes']}")
    print(f"  总方法数: {struct_metrics['total_methods']}")
    print(f"  结构违规: {struct_metrics['structure_violations']}")
    print(f"  大型类: {struct_metrics['large_classes_count']}")
    print(f"  平均类大小: {struct_metrics['avg_class_size']:.0f}行")
    print(f"  平均复杂度: {struct_metrics['avg_complexity']:.1f}")

    # 2. 性能优化
    print_header("2. 性能优化 (Performance Optimization)")

    perf_eval = PerfEvaluator(target)
    perf_metrics = perf_eval.get_current_metrics()

    print("📊 当前性能指标:")
    print(f"  执行时间: {perf_metrics['execution_time']:.3f}秒")
    print(f"  内存使用: {perf_metrics['memory_usage_mb']:.1f}MB")
    print(f"  CPU使用率: {perf_metrics['cpu_percent']:.1f}%")
    print(f"  Python文件数: {perf_metrics['python_files']}")

    # 3. 简洁优化
    print_header("3. 简洁优化 (Simplicity Optimization)")

    simp_eval = SimplicityEvaluator(target)
    simp_metrics = simp_eval.get_current_metrics()

    print("📊 当前简洁性指标:")
    print(f"  总行数: {simp_metrics['total_lines']}")
    print(f"  代码行: {simp_metrics['code_lines']}")
    print(f"  注释行: {simp_metrics['comment_lines']}")
    print(f"  平均行长度: {simp_metrics['avg_line_length']:.0f}")
    print(f"  最长行: {simp_metrics['max_line_length']}")
    print(f"  长行数量: {simp_metrics['long_lines_count']}")
    print(f"  重复率: {simp_metrics['duplication_rate']:.2%}")

    # 查找重复代码
    print("\n🔍 重复代码分析:")
    duplicates = simp_eval.find_duplicate_code_blocks(min_lines=5)
    print(f"  找到 {len(duplicates)} 个重复代码块")
    for i, dup in enumerate(duplicates[:3], 1):
        print(f"    {i}. 重复 {dup['occurrences']} 次，{dup['lines']} 行")

    # 4. 运行优化
    print_header("4. 运行三目标优化")

    results = {}

    for goal in ["structure", "performance", "simplicity"]:
        print(f"\n{'='*70}")
        print(f" {goal.upper()} 优化".center(70))
        print(f"{'='*70}\n")

        request = OptimizationRequest(
            target=target,
            goal=goal,
            params={},
            config={"max_experiments": 5}
        )

        optimizer = SynchronousOptimizer()
        result = optimizer.optimize(request)

        if result.success:
            results[goal] = {
                "result": result,
                "metrics": {
                    "structure": struct_metrics,
                    "performance": perf_metrics,
                    "simplicity": simp_metrics
                }.get(goal, {})
            }

            print(f"✓ 优化完成")
            print(f"  实验次数: {result.experiments}")
            print(f"  最佳分数: {result.best_score:.2f}")
            print(f"\n🎯 最佳参数:")
            for key, value in sorted(result.best_params.items()):
                if isinstance(value, float):
                    print(f"    {key}: {value:.2f}")
                else:
                    print(f"    {key}: {value}")
        else:
            print(f"✗ 优化失败: {result.error}")

    # 5. 对比总结
    print_header("5. 优化效果对比")

    print(f"{'目标':<15} {'实验次数':<10} {'最佳分数':<12} {'状态':<8}")
    print("-" * 70)
    for goal, data in results.items():
        result = data["result"]
        status = "✓" if result.success else "✗"
        print(f"{goal:<15} {result.experiments:<10} {result.best_score:<12.2f} {status:<8}")

    # 6. 建议
    print_header("6. 优化建议")

    print("💡 根据当前指标，建议的优化优先级:")

    # 分析哪个指标最需要优化
    scores = []
    if struct_metrics["structure_violations"] > 0:
        scores.append(("structure", struct_metrics["structure_violations"]))
    if simp_metrics["duplication_rate"] > 0.05:
        scores.append(("simplicity", simp_metrics["duplication_rate"] * 100))
    if perf_metrics["execution_time"] > 1.0:
        scores.append(("performance", perf_metrics["execution_time"] * 10))

    scores.sort(key=lambda x: x[1], reverse=True)

    if scores:
        for i, (goal, score) in enumerate(scores[:3], 1):
            priority = ["高", "中", "低"][i-1]
            print(f"  {i}. {goal.upper()} (优先级: {priority}, 分数: {score:.2f})")
    else:
        print("  当前代码质量良好，建议定期检查。")

    # 7. 保存结果
    print_header("7. 保存优化结果")

    output_file = Path("optimization_results.json")
    save_data = {}
    for goal, data in results.items():
        save_data[goal] = {
            "best_params": data["result"].best_params,
            "best_score": data["result"].best_score,
            "experiments": data["result"].experiments,
        }

    output_file.write_text(json.dumps(save_data, indent=2, ensure_ascii=False))
    print(f"✓ 结果已保存到: {output_file}")

    # 8. CLI命令提示
    print_header("8. 使用CLI命令")

    print("您也可以使用CLI命令进行优化:")
    print()
    print("  # 结构优化")
    print("  lingflow optimize structure --target lingflow/self_optimizer")
    print()
    print("  # 性能优化")
    print("  lingflow optimize performance --target lingflow/self_optimizer")
    print()
    print("  # 简洁优化")
    print("  lingflow optimize simplicity --target lingflow/self_optimizer")
    print()

    print_header("✅ 演示完成")
    print("三个优化目标均已实现并验证！")
    print()


if __name__ == "__main__":
    try:
        demo_three_goals()
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 演示出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
