"""
规则应用框架演示

展示如何应用学习到的规则，包括自动应用和人工审核。
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

from ai_learning_engine.rule_application_framework import (
    RuleApplicationManager,
    ApplicationMode,
    ValidationType,
    LearnedRule as LearnedRuleFromFramework
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
        )
    ]
    return rules


def create_test_files():
    """创建测试文件"""
    test_files = []
    test_dir = Path("examples/test_files")
    test_dir.mkdir(exist_ok=True)

    # 创建包含潜在问题的文件
    test_code1 = '''
# Test file 1 - contains security issue
def evaluate_code(code):
    # Security risk: eval usage
    result = eval(code)
    return result

def empty_function():
    # Empty function should be removed
    pass

def process_data(data):
    # Good function
    return data.upper()
'''

    test_code2 = '''
# Test file 2 - contains quality issues
def helper_function():
    # Empty function
    pass

def main():
    # Main function
    print("Hello World")

def another_empty():
    # Another empty function
    pass
'''

    files = [
        (test_dir / "test1.py", test_code1),
        (test_dir / "test2.py", test_code2)
    ]

    for file_path, content in files:
        with open(file_path, 'w') as f:
            f.write(content)
        test_files.append(str(file_path))

    return test_files


def main():
    """应用框架演示"""
    print("=== 规则应用框架演示 ===\n")

    # 1. 创建应用管理器
    manager = RuleApplicationManager(auto_apply_threshold=0.75)
    print("1. 初始化应用管理器")

    # 2. 创建测试规则和文件
    rules = create_test_rules()
    test_files = create_test_files()
    print(f"\n2. 创建了 {len(rules)} 个测试规则和 {len(test_files)} 个测试文件")

    # 3. 提交应用请求
    print("\n3. 提交应用请求...")

    for rule in rules:
        # 根据规则质量选择应用模式
        if rule.quality_score >= 0.85:
            mode = ApplicationMode.AUTO
        else:
            mode = ApplicationMode.MANUAL_REVIEW

        request_id = manager.submit_application_request(
            rule,
            test_files,
            mode=mode,
            requested_by="developer"
        )

        print(f"\n规则 {rule.name} 应用请求ID: {request_id}")

        # 获取请求状态
        request = manager.get_application_status(request_id)
        if request:
            print(f"  状态: {request.status.value}")
            print(f"  模式: {request.mode.value}")
            print(f"  优先级: {request.priority}")

    # 4. 模拟人工审核
    print("\n4. 模拟人工审核...")
    time.sleep(2)  # 等待处理

    # 获取待审核请求
    pending_requests = manager.manual_review_system.get_pending_requests()
    for request in pending_requests:
        print(f"\n审核请求 {request.request.id}:")
        print(f"  规则: {request.request.rule_id}")
        print(f"  目标文件: {len(request.request.target_files)} 个")

        # 批准请求
        request.request.status = ApplicationStatus.QUEUED
        manager.scheduler.schedule_application(request.request)
        print(f"  已批准并加入队列")

    # 5. 监控应用进度
    print("\n5. 监控应用进度...")
    time.sleep(3)  # 等待处理完成

    # 获取应用历史
    history = manager.get_application_history(limit=5)
    print("\n应用历史:")
    print("-" * 50)

    for item in history:
        print(f"\n请求ID: {item['id']}")
        print(f"规则ID: {item['rule_id']}")
        print(f"状态: {item['status']}")
        print(f"执行日志数: {len(item['execution_log'])}")

        if item['execution_log']:
            print("最新日志:")
            for log in item['execution_log'][-2:]:  # 显示最后2条
                print(f"  - {log}")

    # 6. 获取系统统计
    print("\n6. 系统统计:")
    stats = manager.get_system_statistics()
    print(f"- 总请求数: {stats['total_requests']}")
    print(f"- 已完成: {stats['completed_requests']}")
    print(f"- 失败: {stats['failed_requests']}")
    print(f"- 成功率: {stats['success_rate']:.2%}")
    print(f"- 队列长度: {stats['queue_length']}")

    review_stats = stats['review_statistics']
    print(f"\n审核统计:")
    print(f"- 总请求数: {review_stats['total_requests']}")
    print(f"- 已批准: {review_stats['approved']}")
    print(f"- 已拒绝: {review_stats['rejected']}")
    print(f"- 待处理: {review_stats['pending']}")
    print(f"- 批准率: {review_stats['approval_rate']:.2%}")

    # 7. 检查应用结果
    print("\n7. 检查应用结果...")
    for file_path in test_files:
        print(f"\n文件: {file_path}")
        with open(file_path, 'r') as f:
            content = f.read()

        # 检查是否应用了规则
        if 'empty_function' not in content:
            print("  ✓ QUAL001规则已应用（移除了空函数）")
        else:
            print("  ✗ QUAL001规则未应用")

        if 'eval(' not in content:
            print("  ✓ SEC001规则已应用（替换了eval）")
        else:
            print("  ✗ SEC001规则未应用")

    # 8. 清理
    print("\n8. 清理测试文件...")
    for file_path in test_files:
        try:
            Path(file_path).unlink()
        except:
            pass

    print("\n=== 应用演示完成 ===")


if __name__ == '__main__':
    main()