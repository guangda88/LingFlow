"""
规则验证系统演示

展示如何验证从AI工具学习到的规则。
"""

import logging
from pathlib import Path

from ai_learning_engine import (
    RuleLearningEngine,
    FeedbackProcessor,
    LearnedRule,
    LearningStatus,
    FeedbackCategory
)

from ai_learning_engine.rule_validation_system import (
    ValidationManager,
    ValidationType
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_rules():
    """创建测试规则"""
    rules = [
        LearnedRule(
            id="SEC001",
            name="Remove eval Usage",
            description="Replace eval() with ast.literal_eval() for security",
            category=FeedbackCategory.SECURITY,
            pattern=None,  # 简化演示
            tools=["SonarQube", "Bandit"],
            frequency=15,
            confidence=0.95,
            status=LearningStatus.VALIDATED,
            quality_score=0.9
        ),
        LearnedRule(
            id="QUAL001",
            name="Remove Unused Functions",
            description="Remove empty or unused functions",
            category=FeedbackCategory.CODE_QUALITY,
            pattern=None,  # 简化演示
            tools=["SonarQube", "Pylint"],
            frequency=20,
            confidence=0.85,
            status=LearningStatus.VALIDATED,
            quality_score=0.8
        ),
        LearnedRule(
            id="PERF001",
            name="Optimize String Concatenation",
            description="Use str.join() instead of + in loops",
            category=FeedbackCategory.PERFORMANCE,
            pattern=None,  # 简化演示
            tools=["SonarQube"],
            frequency=8,
            confidence=0.75,
            status=LearningStatus.VALIDATED,
            quality_score=0.7
        )
    ]
    return rules


def main():
    """验证系统演示"""
    print("=== 规则验证系统演示 ===\n")

    # 1. 创建验证管理器
    validation_manager = ValidationManager()
    print("1. 初始化验证管理器")

    # 2. 创建测试规则
    rules = create_test_rules()
    print(f"\n2. 创建了 {len(rules)} 个测试规则")

    # 3. 验证规则
    print("\n3. 开始验证规则...")

    for rule in rules:
        print(f"\n验证规则: {rule.name}")
        print("-" * 50)

        # 执行多种验证
        validation_types = [ValidationType.SAFETY, ValidationType.EFFECTIVENESS]
        validation_results = validation_manager.validate_rule(rule, validation_types)

        # 显示验证结果
        for validation_type, report in validation_results.items():
            print(f"\n验证类型: {validation_type.value}")
            print(f"状态: {report.status.value}")
            print(f"是否安全: {'是' if report.is_safe else '否'}")
            print(f"测试数量: {report.test_count}")
            print(f"通过测试: {report.passed_tests}")
            print(f"执行时间: {report.execution_time:.2f}秒")

            if report.notes:
                print(f"备注: {report.notes}")

            if report.violations:
                print("违规项:")
                for violation in report.violations[:3]:  # 只显示前3个
                    print(f"  - {violation.get('message', 'Unknown violation')}")

    # 4. 获取验证摘要
    print("\n4. 验证摘要:")
    print("-" * 50)

    for rule in rules:
        summary = validation_manager.get_validation_summary(rule.id)
        print(f"\n规则 {rule.id}:")
        print(f"  总体验证: {'通过' if summary['overall_safe'] else '失败'}")
        print(f"  验证项目: {summary['validation_count']}")
        print(f"  通过项目: {summary['passed_count']}")
        print(f"  失败项目: {summary['failed_count']}")

    # 5. 保存验证结果
    output_dir = Path("examples/output")
    output_dir.mkdir(exist_ok=True)

    validation_file = output_dir / "validation_results.json"
    validation_manager.save_validation_results(str(validation_file))
    print(f"\n验证结果已保存到: {validation_file}")

    print("\n=== 验证演示完成 ===")


if __name__ == '__main__':
    main()