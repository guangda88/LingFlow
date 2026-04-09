#!/usr/bin/env python3
"""LingFlow 新模块单元测试

测试覆盖:
- Session v2
- QueryEngine
- PromptRouter
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from lingflow.core import (
    PromptRouter,
    QueryEngine,
    QueryEngineConfig,
    RouteRule,
    RouteStrategy,
    RouteTarget,
    SessionManager,
    SessionSnapshot,
    StopReason,
    TurnResult,
    UsageSummary,
    create_default_engine,
)

# ============================================================================
# Session v2 测试
# ============================================================================


class TestSessionV2(unittest.TestCase):
    """Session v2单元测试"""

    def setUp(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SessionManager(session_dir=Path(self.temp_dir))

    def tearDown(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)

    def test_add_message(self):
        """测试添加消息"""
        self.manager.add_message("测试消息", input_tokens=10, output_tokens=5)
        summary = self.manager.get_usage_summary()

        self.assertEqual(summary["message_count"], 1)
        self.assertEqual(summary["input_tokens"], 10)
        self.assertEqual(summary["output_tokens"], 5)
        self.assertEqual(summary["total_tokens"], 15)

    def test_multiple_messages(self):
        """测试多条消息"""
        for i in range(5):
            self.manager.add_message(f"消息{i}", input_tokens=10, output_tokens=5)

        summary = self.manager.get_usage_summary()
        self.assertEqual(summary["message_count"], 5)
        self.assertEqual(summary["total_tokens"], 75)

    def test_create_snapshot(self):
        """测试创建快照"""
        self.manager.add_message("消息1", input_tokens=10, output_tokens=5)
        self.manager.add_message("消息2", input_tokens=20, output_tokens=10)

        snapshot = self.manager.create_snapshot()

        self.assertIsInstance(snapshot, SessionSnapshot)
        self.assertEqual(len(snapshot.messages), 2)
        self.assertEqual(snapshot.input_tokens, 30)
        self.assertEqual(snapshot.output_tokens, 15)

    def test_snapshot_immutability(self):
        """测试快照不可变性"""
        self.manager.add_message("测试")
        snapshot = self.manager.create_snapshot()

        # 尝试修改快照应该失败
        with self.assertRaises(Exception):
            snapshot.messages = ("新消息",)

    def test_save_session(self):
        """测试保存会话"""
        self.manager.add_message("消息1", input_tokens=10, output_tokens=5)
        self.manager.add_message("消息2", input_tokens=20, output_tokens=10)

        session_path = self.manager.save_session()

        self.assertTrue(session_path.exists())
        self.assertGreater(session_path.stat().st_size, 0)

    def test_get_usage_summary(self):
        """测试获取使用摘要"""
        self.manager.add_message("消息1", input_tokens=10, output_tokens=5)
        self.manager.add_message("消息2", input_tokens=20, output_tokens=10)

        summary = self.manager.get_usage_summary()

        self.assertIn("message_count", summary)
        self.assertIn("input_tokens", summary)
        self.assertIn("output_tokens", summary)
        self.assertIn("total_tokens", summary)


# ============================================================================
# QueryEngine 测试
# ============================================================================


class TestQueryEngine(unittest.TestCase):
    """QueryEngine单元测试"""

    def setUp(self):
        """测试设置"""
        self.config = QueryEngineConfig(max_turns=5, max_budget_tokens=1000, auto_compact=True)
        self.engine = QueryEngine(self.config)

    def test_basic_query(self):
        """测试基本查询"""
        result = self.engine.submit("测试查询")

        self.assertIsInstance(result, TurnResult)
        self.assertEqual(result.prompt, "测试查询")
        self.assertGreater(result.input_tokens, 0)
        self.assertGreater(result.output_tokens, 0)
        self.assertEqual(result.stop_reason, StopReason.COMPLETED)

    def test_multi_turn_conversation(self):
        """测试多轮对话"""
        for i in range(3):
            result = self.engine.submit(f"查询{i+1}")
            self.assertEqual(result.stop_reason, StopReason.COMPLETED)

        stats = self.engine.get_stats()
        self.assertEqual(stats["turn_count"], 3)
        self.assertEqual(stats["message_count"], 6)  # 每轮2条消息

    def test_max_turns_limit(self):
        """测试最大轮数限制"""
        config = QueryEngineConfig(max_turns=3)
        engine = QueryEngine(config)

        # 前2轮应该正常（第3次会触发限制）
        for i in range(2):
            result = engine.submit(f"查询{i+1}")
            self.assertEqual(result.stop_reason, StopReason.COMPLETED)

        # 第3轮会触发限制（因为turn_count会递增到max_turns）
        result = engine.submit("查询3")
        self.assertEqual(result.stop_reason, StopReason.MAX_TURNS_REACHED)

    def test_budget_tracking(self):
        """测试Token预算追踪"""
        result1 = self.engine.submit("查询1")
        result2 = self.engine.submit("查询2")

        usage = self.engine.usage_summary
        self.assertEqual(usage.total_input_tokens, result1.input_tokens + result2.input_tokens)
        self.assertEqual(usage.total_output_tokens, result1.output_tokens + result2.output_tokens)

    def test_tool_matching(self):
        """测试工具匹配"""
        tools = ["code_analyzer", "file_reader", "test_runner"]
        result = self.engine.submit("请使用code_analyzer工具分析代码", tools=tools)

        self.assertIn("code_analyzer", result.matched_tools)

    def test_agent_matching(self):
        """测试Agent匹配"""
        agents = ["code_reviewer", "optimizer", "documenter"]
        result = self.engine.submit("请让code_reviewer审查代码", agents=agents)

        self.assertIn("code_reviewer", result.matched_agents)

    def test_custom_processor(self):
        """测试自定义处理函数"""

        def custom_func(prompt: str) -> str:
            return f"处理结果: {prompt.upper()}"

        result = self.engine.submit("测试", process_func=custom_func)

        self.assertEqual(result.output, "处理结果: 测试")

    def test_state_persistence(self):
        """测试状态持久化"""
        self.engine.submit("查询1")
        self.engine.submit("查询2")

        # 保存状态
        temp_dir = tempfile.mkdtemp()
        try:
            state_path = Path(temp_dir) / "test_state.json"
            self.engine.save_state(state_path)

            # 加载状态
            loaded_engine = QueryEngine.load_state(state_path)

            stats = loaded_engine.get_stats()
            self.assertEqual(stats["turn_count"], 2)

        finally:
            shutil.rmtree(temp_dir)

    def test_reset(self):
        """测试重置"""
        self.engine.submit("查询1")
        self.engine.submit("查询2")

        self.engine.reset()

        stats = self.engine.get_stats()
        self.assertEqual(stats["turn_count"], 0)
        self.assertEqual(stats["message_count"], 0)

    def test_get_history(self):
        """测试获取历史"""
        self.engine.submit("查询1")
        self.engine.submit("查询2")

        history = self.engine.get_history()

        self.assertEqual(len(history), 2)
        self.assertIsInstance(history[0], TurnResult)


# ============================================================================
# PromptRouter 测试
# ============================================================================


class TestPromptRouter(unittest.TestCase):
    """PromptRouter单元测试"""

    def setUp(self):
        """测试设置"""
        self.router = PromptRouter()

        # 添加测试目标
        self.target1 = RouteTarget(name="test_agent1", agent_type="TestAgent1", description="测试Agent 1")
        self.target2 = RouteTarget(name="test_agent2", agent_type="TestAgent2", description="测试Agent 2")

        self.router.add_target(self.target1)
        self.router.add_target(self.target2)

        # 添加测试规则
        self.rule1 = RouteRule(name="test_rule1", keywords=["测试", "test"], metadata={"target_name": "test_agent1"})
        self.rule2 = RouteRule(name="test_rule2", keywords=["代码", "code"], metadata={"target_name": "test_agent2"})

        self.router.add_rule(self.rule1)
        self.router.add_rule(self.rule2)

        self.router.set_default_target(self.target1)

    def test_basic_routing(self):
        """测试基本路由"""
        result = self.router.route("这是一个测试请求")

        self.assertIsNotNone(result.selected_target)
        self.assertEqual(result.selected_target.name, "test_agent1")
        self.assertGreater(result.confidence, 0)

    def test_keyword_matching(self):
        """测试关键词匹配"""
        result1 = self.router.route("测试代码")
        result2 = self.router.route("分析代码")

        # "测试代码"应该匹配test_rule1
        self.assertTrue(any("test_rule1" in match[0] for match in result1.matched_rules))

        # "分析代码"应该匹配test_rule2
        self.assertTrue(any("test_rule2" in match[0] for match in result2.matched_rules))

    def test_no_match_default(self):
        """测试无匹配时使用默认目标"""
        result = self.router.route("完全不相关的请求")

        self.assertEqual(result.selected_target.name, "test_agent1")

    def test_top_k_matching(self):
        """测试Top-K匹配"""
        # 添加一个同时包含多个关键词的提示词
        result = self.router.route("这是测试代码的请求", top_k=5)

        self.assertLessEqual(len(result.matched_rules), 5)
        self.assertGreater(len(result.matched_rules), 0)

    def test_confidence_calculation(self):
        """测试置信度计算"""
        result = self.router.route("测试")

        self.assertGreaterEqual(result.confidence, 0)
        self.assertLessEqual(result.confidence, 1)

    def test_route_statistics(self):
        """测试路由统计"""
        # 执行多次路由
        prompts = ["测试请求1", "测试请求2", "代码请求1", "测试请求3"]

        for prompt in prompts:
            self.router.route(prompt)

        stats = self.router.get_statistics()

        self.assertEqual(stats["total_routes"], 4)
        self.assertGreater(stats["avg_confidence"], 0)
        self.assertGreater(len(stats["most_used_targets"]), 0)

    def test_config_persistence(self):
        """测试配置持久化"""
        temp_dir = tempfile.mkdtemp()
        try:
            config_path = Path(temp_dir) / "router_config.json"

            # 保存配置
            self.router.save_config(config_path)
            self.assertTrue(config_path.exists())

            # 加载配置
            loaded_router = PromptRouter.load_config(config_path)

            # 验证加载
            result = loaded_router.route("测试")
            self.assertIsNotNone(result.selected_target)

        finally:
            shutil.rmtree(temp_dir)

    def test_clear_history(self):
        """测试清除历史"""
        self.router.route("测试1")
        self.router.route("测试2")

        stats_before = self.router.get_statistics()
        self.assertEqual(stats_before["total_routes"], 2)

        self.router.clear_history()

        stats_after = self.router.get_statistics()
        self.assertEqual(stats_after["total_routes"], 0)

    def test_pattern_matching(self):
        """测试模式匹配"""
        router = PromptRouter()

        router.add_target(RouteTarget(name="email_agent", agent_type="EmailAgent", description="邮件处理"))

        # 添加正则表达式规则
        rule = RouteRule(
            name="email_pattern",
            patterns=[r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"],
            strategy=RouteStrategy.PATTERN_MATCH,
            metadata={"target_name": "email_agent"},
        )
        router.add_rule(rule)

        result = router.route("发送邮件到 user@example.com")

        self.assertTrue(len(result.matched_rules) > 0)

    def test_priority_system(self):
        """测试优先级系统"""
        router = PromptRouter()

        router.add_target(RouteTarget(name="test_agent", agent_type="TestAgent", description="测试"))

        # 添加不同优先级的规则
        rule1 = RouteRule(name="low_priority", keywords=["帮助"], priority=0, metadata={"target_name": "test_agent"})

        rule2 = RouteRule(name="high_priority", keywords=["帮助"], priority=5, metadata={"target_name": "test_agent"})

        router.add_rule(rule1)
        router.add_rule(rule2)

        result = router.route("帮助")

        # 高优先级规则应该排在前面
        best_match = result.best_match
        self.assertEqual(best_match[0], "high_priority")


# ============================================================================
# 测试运行器
# ============================================================================


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试
    suite.addTests(loader.loadTestsFromTestCase(TestSessionV2))
    suite.addTests(loader.loadTestsFromTestCase(TestQueryEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestPromptRouter))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 LingFlow 新模块单元测试")
    print("=" * 70)
    print()

    success = run_tests()

    print()
    print("=" * 70)
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 70)

    sys.exit(0 if success else 1)
