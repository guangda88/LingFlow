#!/usr/bin/env python3
"""
LingFlow 自优化系统演示脚本

展示自优化系统的核心功能
"""

import sys
import time
from pathlib import Path


def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f" {title}".center(60))
    print("="*60 + "\n")


def demo_trigger():
    """演示触发器"""
    print_header("1. 触发条件检测")

    from lingflow.self_optimizer import OptimizationTrigger

    trigger = OptimizationTrigger()

    # 测试场景
    contexts = [
        {"review_score": 85, "name": "正常状态"},
        {"review_score": 60, "name": "质量下降"},
        {"avg_complexity": 20, "name": "复杂度高"},
        {"execution_time": 3.0, "baseline_time": 1.5, "name": "性能下降"},
        {"user_triggered": True, "name": "用户主动"},
    ]

    for context in contexts:
        name = context.pop("name", "")
        should_trigger, info = trigger.check_all_conditions(context)

        status = "✓ 需要优化" if should_trigger else "✗ 无需优化"
        print(f"{name}: {status}")
        if should_trigger:
            print(f"  原因: {info.reason}")
            print(f"  优先级: {info.priority}")
        print()


def demo_evaluator():
    """演示评估器"""
    print_header("2. 结构质量评估")

    from lingflow.self_optimizer import StructureEvaluator

    # 评估LingFlow自身的代码
    evaluator = StructureEvaluator("lingflow/self_optimizer")

    print("正在分析代码结构...")
    metrics = evaluator.get_current_metrics()

    print("📊 当前代码指标:")
    print(f"  总类数: {metrics['total_classes']}")
    print(f"  总方法数: {metrics['total_methods']}")
    print(f"  结构违规: {metrics['structure_violations']}")
    print(f"  大型类: {metrics['large_classes_count']}")
    print(f"  复杂方法: {metrics['complex_methods_count']}")
    print(f"  平均类大小: {metrics['avg_class_size']:.0f}行")
    print(f"  平均复杂度: {metrics['avg_complexity']:.1f}")
    print(f"  平均方法数: {metrics['avg_method_count']:.1f}")


def demo_optimizer():
    """演示优化器"""
    print_header("3. 自优化运行")

    from lingflow.self_optimizer import SynchronousOptimizer, OptimizationRequest

    # 创建优化请求（只运行5次实验以加快演示）
    request = OptimizationRequest(
        target="lingflow/self_optimizer",
        goal="structure",
        params={},
        config={
            "max_experiments": 5,
            "time_budget": 60,
        }
    )

    print("🔍 启动结构优化...")
    print(f"目标: {request.target}")
    print(f"实验次数: {request.config['max_experiments']}")
    print()

    optimizer = SynchronousOptimizer()

    start_time = time.time()
    result = optimizer.optimize(request)
    duration = time.time() - start_time

    if result.success:
        print("✓ 优化完成!")
        print(f"  耗时: {duration:.2f}秒")
        print(f"  实验次数: {result.experiments}")
        print(f"  最佳分数: {result.best_score:.2f}")
        print()
        print("🎯 最佳参数:")
        for key, value in sorted(result.best_params.items()):
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
    else:
        print(f"✗ 优化失败: {result.error}")


def demo_report_generation():
    """演示报告生成"""
    print_header("4. 优化报告生成")

    from lingflow.self_optimizer import (
        StructureEvaluator,
        OptimizationAdvisor,
        OptimizationResult
    )

    # 获取当前指标
    evaluator = StructureEvaluator("lingflow/self_optimizer")
    current_metrics = evaluator.get_current_metrics()

    # 模拟优化结果
    result = OptimizationResult(
        success=True,
        best_params={
            "max_class_size": 200,
            "max_complexity": 10,
            "max_method_count": 15,
        },
        best_score=3.0,
        experiments=20,
        duration=42.3
    )

    # 生成报告
    advisor = OptimizationAdvisor()
    report = advisor.generate_report(
        goal="structure",
        target="lingflow/self_optimizer",
        current_metrics=current_metrics,
        optimization_result=result
    )

    print("📄 报告预览（前30行）:")
    print("-"*60)
    lines = report.split('\n')
    for i, line in enumerate(lines[:30], 1):
        print(f"{i:2d}. {line}")

    print()
    print("...（省略）")
    print()
    print("💡 完整报告已保存到: LINGFLOW_OPTIMIZATION_REPORT_DEMO.md")

    # 保存演示报告
    advisor.save_report(report, "LINGFLOW_OPTIMIZATION_REPORT_DEMO.md")


def demo_cli_commands():
    """演示CLI命令"""
    print_header("5. CLI命令示例")

    commands = [
        ("检查是否需要优化", "lingflow optimize check"),
        ("运行结构优化", "lingflow optimize structure"),
        ("异步运行优化", "lingflow optimize structure --async"),
        ("查看优化状态", "lingflow optimize status"),
        ("等待优化完成", "lingflow optimize wait"),
        ("取消优化", "lingflow optimize cancel"),
        ("应用优化建议", "lingflow optimize apply -r REPORT.md"),
        ("生成配置文件", "lingflow optimize generate-config -r REPORT.md"),
    ]

    print("可用命令:")
    for desc, cmd in commands:
        print(f"  {desc:20s} {cmd}")

    print()
    print("💡 使用 'lingflow optimize --help' 查看所有选项")


def demo_hooks():
    """演示钩子系统"""
    print_header("6. 钩子系统")

    print("自动触发场景:")
    print()
    print("1️⃣  代码审查后")
    print("   hook.on_code_review_complete(review_result)")
    print()
    print("2️⃣  测试完成后")
    print("   hook.on_test_complete(test_result)")
    print()
    print("3️⃣  Git提交时")
    print("   hook.on_git_commit(commit_info)")
    print()
    print("4️⃣  性能测量时")
    print("   hook.on_performance_measure(metrics)")
    print()
    print("💡 如果检测到问题，会自动提示是否启动优化")


def main():
    """主函数"""
    print("\n")
    print("█" * 60)
    print("█" + " " * 58 + "█")
    print("█" + "  LingFlow 自优化系统 - 功能演示".center(58) + "█")
    print("█" + " " * 58 + "█")
    print("█" * 60)

    try:
        # 演示各个功能
        demo_trigger()
        time.sleep(1)

        demo_evaluator()
        time.sleep(1)

        demo_optimizer()
        time.sleep(1)

        demo_report_generation()
        time.sleep(1)

        demo_cli_commands()
        time.sleep(1)

        demo_hooks()

        # 总结
        print_header("✅ 演示完成")
        print("📚 更多信息:")
        print("  - 完整报告: SELFOPTIMIZATION_PHASE1_IMPLEMENTATION_REPORT.md")
        print("  - 快速指南: SELFOPTIMIZATION_QUICKSTART.md")
        print("  - 测试用例: tests/test_self_optimizer/")
        print()
        print("🚀 开始使用:")
        print("  lingflow optimize check")
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  演示被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ 演示出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
