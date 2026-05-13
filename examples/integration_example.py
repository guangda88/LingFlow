#!/usr/bin/env python3
"""
lingflow CLI 集成示例

展示如何在Python代码中使用lingflow的CLI功能
"""

import sys
from pathlib import Path
from typing import Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lingflow import lingflow
from lingflow.self_optimizer.phase4 import (
    quick_optimize,
    OptimizationEngine,
)
from lingflow.self_optimizer.phase5 import (
    RuleExtractor,
    InMemoryKnowledgeBase,
    PatternRecognizer,
)
from lingflow.self_optimizer.phase5.adapters import (
    SemgrepAdapter,
    RuffAdapter,
)


def example_optimize(target: str = "."):
    """参数优化示例"""
    print(f"\n{'='*60}")
    print("示例 1: 参数优化")
    print(f"{'='*60}\n")

    print(f"目标: {target}")
    print("运行结构优化...")

    try:
        result = quick_optimize(
            target_path=target,
            goal="structure",
            config={
                "max_experiments": 10,
                "timeout": 300
            }
        )

        if result and result.get("success"):
            print(f"✓ 优化成功!")
            print(f"  最佳分数: {result.get('best_score', 0):.2f}")
            print(f"  实验次数: {result.get('n_trials', 0)}")

            if 'best_params' in result:
                print(f"\n最佳参数:")
                for key, value in result['best_params'].items():
                    print(f"  {key}: {value}")
        else:
            print("✗ 优化失败")

    except Exception as e:
        print(f"✗ 错误: {e}")


def example_learn(target: str = "."):
    """AI工具学习示例"""
    print(f"\n{'='*60}")
    print("示例 2: AI工具学习")
    print(f"{'='*60}\n")

    print(f"目标: {target}")
    print("从Ruff学习规则...")

    try:
        # 创建适配器
        adapter = RuffAdapter({})

        if not adapter.check_available():
            print("⚠️  Ruff不可用，跳过此示例")
            return

        # 运行扫描
        feedback = adapter.run_scan(target)
        print(f"✓ 收集了 {len(feedback)} 条反馈")

        # 提取规则
        extractor = RuleExtractor(
            min_frequency=2,
            min_confidence=0.6
        )
        rules = extractor.extract_rules(feedback)
        print(f"✓ 提取了 {len(rules)} 条规则")

        # 显示前5条规则
        print("\n前5条规则:")
        for i, rule in enumerate(rules[:5], 1):
            print(f"  {i}. {rule.title}")
            print(f"     类别: {rule.category.value}")
            print(f"     严重性: {rule.severity.value}")

    except Exception as e:
        print(f"✗ 错误: {e}")


def example_analyze(target: str = "."):
    """代码分析示例"""
    print(f"\n{'='*60}")
    print("示例 3: 代码分析")
    print(f"{'='*60}\n")

    print(f"目标: {target}")
    print("分析代码结构...")

    try:
        from lingflow.self_optimizer.evaluator import StructureEvaluator

        evaluator = StructureEvaluator(target)
        metrics = evaluator.get_current_metrics()

        print("✓ 分析完成!")
        print(f"\n指标:")
        print(f"  结构违规: {metrics.get('structure_violations', 0)}")
        print(f"  平均类大小: {metrics.get('avg_class_size', 0):.0f} 行")
        print(f"  平均复杂度: {metrics.get('avg_complexity', 0):.1f}")
        print(f"  大型类数量: {metrics.get('large_classes_count', 0)}")
        print(f"  长方法数量: {metrics.get('long_methods_count', 0)}")

    except Exception as e:
        print(f"✗ 错误: {e}")


def example_pattern_recognition(target: str = "."):
    """模式识别示例"""
    print(f"\n{'='*60}")
    print("示例 4: 模式识别")
    print(f"{'='*60}\n")

    print(f"目标: {target}")
    print("识别代码模式...")

    try:
        recognizer = PatternRecognizer()
        all_patterns = []

        for detector in recognizer.detectors:
            patterns = detector.detect(target)
            all_patterns.extend(patterns)
            print(f"✓ {detector.name}: 发现 {len(patterns)} 个模式")

        print(f"\n总计: {len(all_patterns)} 个模式")

        # 显示前3个模式
        print("\n前3个模式:")
        for i, pattern in enumerate(all_patterns[:3], 1):
            print(f"  {i}. {pattern.description}")
            print(f"     类型: {pattern.pattern_type}")
            print(f"     位置: {pattern.location}")

    except Exception as e:
        print(f"✗ 错误: {e}")


def example_knowledge_base():
    """知识库示例"""
    print(f"\n{'='*60}")
    print("示例 5: 知识库管理")
    print(f"{'='*60}\n")

    try:
        from lingflow.self_optimizer.phase5.models import (
            LearnedRule,
            Pattern,
            FeedbackCategory,
            SeverityLevel,
        )

        # 创建知识库
        kb = InMemoryKnowledgeBase()

        # 添加示例规则
        rule = LearnedRule(
            id="example-rule-1",
            title="示例规则",
            category=FeedbackCategory.CODE_QUALITY,
            severity=SeverityLevel.MEDIUM,
            description="这是一个示例规则",
            suggestion="改进建议",
            confidence=0.8,
            quality_score=0.75
        )
        kb.add_rule(rule)

        # 添加示例模式
        pattern = Pattern(
            pattern_type="long_method",
            description="长方法模式",
            location="example.py:10",
            suggestion="重构此方法",
            context="def long_method():\n    ..."
        )
        kb.add_pattern(pattern)

        print("✓ 知识库创建成功!")
        print(f"  规则数: {len(kb.get_all_rules())}")
        print(f"  模式数: {len(kb.get_all_patterns())}")

        # 搜索规则
        print(f"\n搜索结果:")
        rules = kb.search_rules("example")
        print(f"  找到 {len(rules)} 条规则")

    except Exception as e:
        print(f"✗ 错误: {e}")


def example_multi_objective(target: str = "."):
    """多目标优化示例"""
    print(f"\n{'='*60}")
    print("示例 6: 多目标优化")
    print(f"{'='*60}\n")

    print(f"目标: {target}")
    print("运行多目标优化...")

    try:
        from lingflow.self_optimizer.phase4 import optimize_multiple_objectives

        result = optimize_multiple_objectives(
            target_path=target,
            goals=["structure", "performance"],
            config={
                "n_trials": 20,
                "timeout": 300
            }
        )

        if result:
            print(f"✓ 多目标优化完成!")
            print(f"  Pareto前沿点数: {len(result.pareto_front)}")

            print(f"\n前3个Pareto解:")
            for i, point in enumerate(result.pareto_front[:3], 1):
                print(f"  {i}. 分数: {point.scores}")
                print(f"     参数: {point.params}")
        else:
            print("⚠️  多目标优化跳过")

    except Exception as e:
        print(f"⚠️  多目标优化未完全实现: {e}")


def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("lingflow CLI 集成示例")
    print("="*60)

    # 获取目标路径
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = str(Path(__file__).parent.parent / "lingflow")

    print(f"\n目标路径: {target}")
    print(f"路径存在: {Path(target).exists()}")

    # 运行示例
    example_analyze(target)
    example_pattern_recognition(target)
    example_learn(target)
    example_knowledge_base()
    example_optimize(target)
    example_multi_objective(target)

    print("\n" + "="*60)
    print("示例运行完成!")
    print("="*60 + "\n")

    print("更多信息:")
    print("  - 文档: docs/CLI_GUIDE.md")
    print("  - 快速参考: docs/CLI_EXAMPLES.md")
    print("  - GitHub: https://github.com/guangda88/lingflow")


if __name__ == "__main__":
    main()
