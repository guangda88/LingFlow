"""
AI学习系统演示

展示如何使用AI学习引擎从外部工具反馈中学习规则。
"""

import json
import logging
from pathlib import Path

from ai_learning_engine import (
    RuleLearningEngine,
    FeedbackProcessor,
    FeedbackPriorityCalculator,
    LearnedRule,
    LearningStatus
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """演示AI学习系统的主要功能"""
    print("=== LingFlow AI学习系统演示 ===\n")

    # 1. 创建学习引擎
    engine = RuleLearningEngine()
    processor = FeedbackProcessor()
    calculator = FeedbackPriorityCalculator()

    print("1. 初始化学习引擎完成")

    # 2. 模拟来自SonarQube的反馈数据
    sonar_feedback_data = {
        'issues': [
            {
                'rule': 'S1481',
                'message': 'Remove this unused private method',
                'type': 'CODE_SMELL',
                'severity': 'MAJOR',
                'component': 'src/main.py',
                'line': 45,
                'column': 5,
                'context': {'snippet': 'def calculateComplexity(self):'},
                'effort': '30min'
            },
            {
                'rule': 'S1481',
                'message': 'Remove this unused private method',
                'type': 'CODE_SMELL',
                'severity': 'MAJOR',
                'component': 'src/utils.py',
                'line': 78,
                'column': 3,
                'context': {'snippet': 'def helperFunction():'},
                'effort': '15min'
            },
            {
                'rule': 'S1118',
                'message': 'Utility classes should not have public constructors',
                'type': 'CODE_SMELL',
                'severity': 'MAJOR',
                'component': 'src/models/User.py',
                'line': 12,
                'column': 1,
                'context': {'snippet': 'def __init__(self):'},
                'effort': '45min'
            }
        ]
    }

    # 3. 模拟来自Pylint的反馈数据
    pylint_feedback_data = {
        'messages': [
            {
                'type': 'convention',
                'symbol': 'C0111',
                'message': 'Missing module docstring',
                'category': 'convention',
                'module': 'main',
                'obj': '',
                'line': 1,
                'column': 0,
                'path': 'src/main.py',
                'text': '# No docstring'
            },
            {
                'type': 'warning',
                'symbol': 'W0613',
                'message': 'Unused argument',
                'category': 'warning',
                'module': 'utils',
                'obj': 'process_data',
                'line': 45,
                'column': 20,
                'path': 'src/utils.py',
                'text': 'def process_data(data, unused_arg):'
            }
        ]
    }

    # 4. 处理反馈数据
    print("\n2. 处理AI工具反馈数据...")

    # 处理SonarQube反馈
    sonar_items = processor.process_feedback('SonarQube', sonar_feedback_data)
    print(f"SonarQube反馈项数: {len(sonar_items)}")

    # 处理Pylint反馈
    pylint_items = processor.process_feedback('Pylint', pylint_feedback_data)
    print(f"Pylint反馈项数: {len(pylint_items)}")

    # 合并所有反馈
    all_feedback = sonar_items + pylint_items
    print(f"总反馈项数: {len(all_feedback)}")

    # 5. 学习规则
    print("\n3. 从反馈中学习规则...")
    learned_rules = engine.learn_from_feedback(all_feedback)

    print(f"\n学习到的规则数: {len(learned_rules)}")
    for rule in learned_rules:
        print(f"\n规则ID: {rule.id}")
        print(f"名称: {rule.name}")
        print(f"类别: {rule.category.value}")
        print(f"质量分数: {rule.quality_score:.2f}")
        print(f"来源工具: {', '.join(rule.tools)}")
        print(f"出现频率: {rule.frequency}")
        print(f"状态: {rule.status.value}")
        print(f"示例数量: {len(rule.examples)}")

    # 6. 保存规则
    output_dir = Path("examples/output")
    output_dir.mkdir(exist_ok=True)

    rules_file = output_dir / "learned_rules.json"
    engine.save_rules(learned_rules, str(rules_file))
    print(f"\n规则已保存到: {rules_file}")

    # 7. 计算反馈优先级
    print("\n4. 计算反馈优先级...")
    for item in all_feedback[:5]:  # 只显示前5个
        priority = calculator.calculate_priority(item, len([i for i in all_feedback if i.rule_id == item.rule_id]))
        print(f"规则 {item.rule_id}: 优先级 = {priority:.2f}")

    # 8. 展示规则统计
    print("\n5. 学习统计:")
    print(f"- 总反馈项: {len(all_feedback)}")
    print(f"- 学习规则: {len(learned_rules)}")
    print(f"- 平均质量分数: {sum(r.quality_score for r in learned_rules)/len(learned_rules):.2f}")
    print(f"- 安全规则: {len([r for r in learned_rules if r.category.value == 'security'])}")
    print(f"- 代码质量规则: {len([r for r in learned_rules if r.category.value == 'code_quality'])}")
    print(f"- 性能规则: {len([r for r in learned_rules if r.category.value == 'performance'])}")

    # 9. 展示学习趋势
    print("\n6. 工具贡献分析:")
    tool_contributions = {}
    for item in all_feedback:
        tool = item.tool_name
        if tool not in tool_contributions:
            tool_contributions[tool] = 0
        tool_contributions[tool] += 1

    for tool, count in sorted(tool_contributions.items(), key=lambda x: x[1], reverse=True):
        weight = calculator.get_tool_weight(tool)
        print(f"- {tool}: {count} 项反馈 (权重: {weight:.2f})")

    print("\n=== 演示完成 ===")


if __name__ == '__main__':
    main()