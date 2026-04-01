#!/usr/bin/env python3
"""
LingFlow Session v2 - 实际项目使用示例

展示如何在LingFlow项目的不同模块中使用Session v2进行：
1. API调用追踪和Token统计
2. 工作流会话管理
3. 测试会话追踪
4. 多线程安全会话处理
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# 导入Session v2
from lingflow.core import SessionManager, SessionSnapshot

print("=" * 70)
print("🌟 LingFlow Session v2 - 实际项目使用示例")
print("=" * 70)
print()

# ============================================================================
# 示例1: API调用追踪和Token统计
# ============================================================================

print("📱 示例1: API调用追踪和Token统计")
print("-" * 70)

class APIClient:
    """模拟API客户端，使用Session v2追踪Token使用"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session_manager = SessionManager(
            session_dir=Path(".lingflow/sessions/api_calls")
        )

    def call_api(self, prompt: str, model: str = "claude-3-opus") -> dict:
        """调用API并追踪Token使用"""

        # 模拟API调用
        print(f"  调用API: {model}")
        print(f"  提示词: {prompt[:50]}...")

        # 模拟Token使用（实际中从API响应获取）
        input_tokens = len(prompt.split()) * 2  # 估算
        output_tokens = 150  # 模拟输出

        # 记录到Session
        self.session_manager.add_message(
            f"API调用: {prompt[:100]}",
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        return {
            "response": f"这是对'{prompt[:30]}...'的响应",
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

    def get_usage_summary(self) -> dict:
        """获取使用摘要"""
        return self.session_manager.get_usage_summary()

    def save_session(self) -> Path:
        """保存会话"""
        return self.session_manager.save_session()

# 使用示例
api_client = APIClient("sk-test-key")

# 模拟多次API调用
api_client.call_api("请帮我优化这段Python代码")
api_client.call_api("解释一下什么是贝叶斯优化")
api_client.call_api("创建一个RESTful API")

# 查看统计
summary = api_client.get_usage_summary()
print(f"\n  📊 API调用统计:")
print(f"    总调用次数: {summary['message_count']}")
print(f"    输入Tokens: {summary['input_tokens']}")
print(f"    输出Tokens: {summary['output_tokens']}")
print(f"    总Tokens: {summary['total_tokens']}")

# 保存会话
session_path = api_client.save_session()
print(f"\n  ✅ 会话已保存: {session_path}")

print()

# ============================================================================
# 示例2: 工作流会话管理
# ============================================================================

print("🔧 示例2: 工作流会话管理")
print("-" * 70)

class WorkflowOrchestrator:
    """工作流协调器，使用Session v2追踪工作流执行"""

    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        self.session = SessionManager(
            session_dir=Path(".lingflow/sessions/workflows")
        )
        self.session_id = None

    def start_workflow(self, params: dict) -> str:
        """启动工作流"""
        self.session_id = f"{self.workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session.add_message(
            f"启动工作流: {self.workflow_name}",
            input_tokens=0,
            output_tokens=0
        )
        return self.session_id

    def execute_step(self, step_name: str, input_tokens: int = 0, output_tokens: int = 0):
        """执行工作流步骤"""
        message = f"执行步骤: {step_name}"
        self.session.add_message(message, input_tokens, output_tokens)
        print(f"  ✓ {step_name}")

    def complete_workflow(self):
        """完成工作流"""
        snapshot = self.session.create_snapshot(self.session_id)
        print(f"\n  📊 工作流统计:")
        print(f"    步骤数: {len(snapshot.messages)}")
        print(f"    总Tokens: {snapshot.input_tokens + snapshot.output_tokens}")

        # 保存工作流会话
        path = self.session.save_session(self.session_id)
        print(f"  ✅ 工作流会话已保存: {path}")

        return snapshot

# 使用示例
orchestrator = WorkflowOrchestrator("code_review_workflow")

orchestrator.start_workflow({"target": "lingflow/core"})
print("  执行代码审查工作流...")

orchestrator.execute_step("代码分析", input_tokens=100, output_tokens=50)
orchestrator.execute_step("问题检测", input_tokens=80, output_tokens=120)
orchestrator.execute_step("生成报告", input_tokens=60, output_tokens=200)
orchestrator.execute_step("保存结果", input_tokens=40, output_tokens=30)

snapshot = orchestrator.complete_workflow()

print()

# ============================================================================
# 示例3: 测试会话追踪
# ============================================================================

print("🧪 示例3: 测试会话追踪")
print("-" * 70)

class TestSessionTracker:
    """测试会话追踪器"""

    def __init__(self, test_suite: str):
        self.test_suite = test_suite
        self.session = SessionManager(
            session_dir=Path(".lingflow/sessions/tests")
        )
        self.passed = 0
        self.failed = 0

    def start_test(self, test_name: str):
        """开始测试"""
        print(f"  运行测试: {test_name}...")

    def record_test(self, test_name: str, passed: bool, tokens: int = 0):
        """记录测试结果"""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.session.add_message(
            f"{status}: {test_name}",
            input_tokens=tokens if passed else 0,
            output_tokens=0 if passed else tokens
        )

        if passed:
            self.passed += 1
        else:
            self.failed += 1

        print(f"    {status}")

    def get_summary(self) -> dict:
        """获取测试摘要"""
        return self.session.get_usage_summary()

# 使用示例
tracker = TestSessionTracker("session_v2_tests")

print("  运行Session v2测试套件...")

# 模拟测试
tests = [
    ("test_import", True),
    ("test_create_manager", True),
    ("test_add_message", True),
    ("test_token_tracking", True),
    ("test_save_session", True),
    ("test_load_session", False),  # 模拟失败的测试
]

for test_name, passed in tests:
    tracker.start_test(test_name)
    tracker.record_test(test_name, passed, tokens=50)

summary = tracker.get_summary()
print(f"\n  📊 测试统计:")
print(f"    总测试数: {tracker.passed + tracker.failed}")
print(f"    通过: {tracker.passed}")
print(f"    失败: {tracker.failed}")
print(f"    成功率: {tracker.passed / (tracker.passed + tracker.failed) * 100:.1f}%")

print()

# ============================================================================
# 示例4: 多线程安全会话处理
# ============================================================================

print("⚡ 示例4: 多线程安全会话处理")
print("-" * 70)

import threading

class ConcurrentSessionProcessor:
    """并发Session处理器 - 利用不可变快照的线程安全特性"""

    def __init__(self):
        self.session = SessionManager()
        self.results = []
        self.lock = threading.Lock()

    def add_data(self, data: str):
        """添加数据到会话"""
        import random
        tokens = random.randint(10, 100)
        self.session.add_message(data, input_tokens=tokens, output_tokens=tokens//2)

    def process_snapshot_concurrent(self, snapshot: SessionSnapshot, worker_id: int):
        """并发处理快照（线程安全）"""
        # 模拟处理
        time.sleep(0.1)

        # 由于快照是不可变的，可以安全地并发读取
        result = {
            'worker_id': worker_id,
            'message_count': len(snapshot.messages),
            'total_tokens': snapshot.input_tokens + snapshot.output_tokens
        }

        with self.lock:
            self.results.append(result)

        print(f"  Worker {worker_id}: 处理了 {result['message_count']} 条消息")

    def run_concurrent_processing(self):
        """运行并发处理"""
        # 添加数据
        for i in range(5):
            self.add_data(f"消息 {i}")

        # 创建快照（不可变）
        snapshot = self.session.create_snapshot()
        print(f"  创建快照: {snapshot.session_id}")
        print(f"  消息数: {len(snapshot.messages)}")

        # 创建多个线程并发处理同一个快照
        threads = []
        for i in range(3):
            t = threading.Thread(
                target=self.process_snapshot_concurrent,
                args=(snapshot, i)
            )
            threads.append(t)
            t.start()

        # 等待所有线程完成
        for t in threads:
            t.join()

        print(f"\n  📊 并发处理结果:")
        for result in self.results:
            print(f"    Worker {result['worker_id']}: {result['message_count']} 消息, {result['total_tokens']} tokens")

# 使用示例
processor = ConcurrentSessionProcessor()
processor.run_concurrent_processing()

print()

# ============================================================================
# 示例5: Token预算管理
# ============================================================================

print("💰 示例5: Token预算管理")
print("-" * 70)

class TokenBudgetManager:
    """Token预算管理器"""

    def __init__(self, daily_budget: int = 100000):
        self.daily_budget = daily_budget
        self.session = SessionManager()

    def track_api_call(self, prompt: str, response: str) -> dict:
        """追踪API调用并检查预算"""

        # 估算Token（实际中应该使用tokenizer）
        input_tokens = len(prompt.split())
        output_tokens = len(response.split())

        # 添加到会话
        self.session.add_message(
            f"API调用: {prompt[:50]}...",
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

        # 获取当前使用量
        summary = self.session.get_usage_summary()
        total_used = summary['total_tokens']

        # 检查预算
        remaining = self.daily_budget - total_used
        usage_percent = (total_used / self.daily_budget) * 100

        result = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_used': total_used,
            'remaining': remaining,
            'usage_percent': usage_percent
        }

        # 警告
        if usage_percent > 90:
            print(f"  ⚠️  警告: 已使用 {usage_percent:.1f}% 的预算")
        elif usage_percent > 75:
            print(f"  ⚠️  注意: 已使用 {usage_percent:.1f}% 的预算")

        return result

    def get_budget_status(self) -> dict:
        """获取预算状态"""
        summary = self.session.get_usage_summary()
        return {
            'budget': self.daily_budget,
            'used': summary['total_tokens'],
            'remaining': self.daily_budget - summary['total_tokens'],
            'usage_percent': (summary['total_tokens'] / self.daily_budget) * 100
        }

# 使用示例
budget_manager = TokenBudgetManager(daily_budget=10000)

print("  模拟API调用...")
api_calls = [
    ("优化这段代码", "代码已优化，减少了30%的执行时间"),
    ("解释REST API", "REST API是 Representational State Transfer 的缩写..."),
    ("创建单元测试", "这是你的单元测试代码..."),
]

for prompt, response in api_calls:
    result = budget_manager.track_api_call(prompt, response)
    print(f"  - 本次调用: {result['input_tokens']} + {result['output_tokens']} = {result['input_tokens'] + result['output_tokens']} tokens")

status = budget_manager.get_budget_status()
print(f"\n  📊 预算状态:")
print(f"    预算: {status['budget']:,} tokens")
print(f"    已用: {status['used']:,} tokens ({status['usage_percent']:.1f}%)")
print(f"    剩余: {status['remaining']:,} tokens")

print()

# ============================================================================
# 总结
# ============================================================================

print("=" * 70)
print("✅ 所有示例运行完成！")
print("=" * 70)

print("""
🎯 Session v2 实际应用场景:

1. API调用追踪
   • 自动记录每次API调用的Token使用
   • 生成使用报告和成本分析
   • 设置预算和警告阈值

2. 工作流管理
   • 追踪工作流执行的每个步骤
   • 记录每步的Token消耗
   • 保存完整的执行历史

3. 测试追踪
   • 记录测试执行历史
   • 统计通过率和Token使用
   • 生成测试报告

4. 并发处理
   • 利用不可变快照实现线程安全
   • 多个worker并发处理同一会话
   • 无锁并发，提高性能

5. 成本管理
   • 实时追踪Token使用
   • 预算控制和警告
   • 使用趋势分析

💡 最佳实践:

✅ 在API客户端中使用Session v2追踪所有调用
✅ 在工作流中记录关键步骤的Token消耗
✅ 定期保存会话以供后续分析
✅ 利用不可变快照实现并发处理
✅ 设置Token预算并监控使用量

📚 相关文档:
  • SESSION_V2_INTEGRATION_GUIDE.md - 完整集成指南
  • test_session_v2_integration.py - 集成测试

🎯 开始在您的项目中使用Session v2吧！
""")

print("=" * 70)
