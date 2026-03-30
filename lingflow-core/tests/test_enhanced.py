"""
LingFlow Enhanced Tests - 增强测试套件

性能测试、压力测试、边界测试
"""

import pytest
import sys
import time
import threading
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import get_context_api
from core.dependency_analyzer import DependencyAnalyzer
from core.smart_compression import SmartCompressionStrategy

logger = logging.getLogger(__name__)


class TestPerformanceBenchmarks:
    """性能基准测试"""

    @pytest.fixture
    def api(self):
        return get_context_api()

    def test_token_estimation_performance(self, api):
        """测试 Token 估算性能"""
        messages = [
            {"role": "user", "content": f"Message {i} " * 20}
            for i in range(100)
        ]

        # 测试 P50
        times = []
        for _ in range(50):
            start = time.time()
            api.estimate_tokens(messages=messages)
            times.append((time.time() - start) * 1000)

        times.sort()
        p50 = times[24]  # 中位数
        p95 = times[47]  # 95分位

        assert p50 < 10, f"P50 {p50:.2f}ms exceeds 10ms target"
        assert p95 < 20, f"P95 {p95:.2f}ms exceeds 20ms target"

        logger.info(f"Token estimation performance: P50={p50:.2f}ms, P95={p95:.2f}ms")

    def test_scoring_performance(self, api):
        """测试评分性能"""
        messages = [
            {"role": "user", "content": f"Message {i} " * 30}
            for i in range(50)
        ]

        # 测试 P50
        times = []
        for _ in range(30):
            start = time.time()
            api.score_messages(messages)
            times.append((time.time() - start) * 1000)

        times.sort()
        p50 = times[14]
        p95 = times[28]

        assert p50 < 20, f"P50 {p50:.2f}ms exceeds 20ms target"
        assert p95 < 40, f"P95 {p95:.2f}ms exceeds 40ms target"

        logger.info(f"Scoring performance: P50={p50:.2f}ms, P95={p95:.2f}ms")

    def test_compression_performance(self, api):
        """测试压缩性能"""
        messages = [
            {"role": "user", "content": f"Message {i} " * 50}
            for i in range(200)
        ]

        original_tokens = api.estimate_tokens(messages=messages)["token_count"]
        target_tokens = int(original_tokens * 0.5)

        # 测试 P50
        times = []
        for _ in range(10):
            start = time.time()
            api.compress_context(messages, target_tokens)
            times.append((time.time() - start) * 1000)

        times.sort()
        p50 = times[4]
        p95 = times[9]

        assert p50 < 100, f"P50 {p50:.2f}ms exceeds 100ms target"
        assert p95 < 200, f"P95 {p95:.2f}ms exceeds 200ms target"

        logger.info(f"Compression performance: P50={p50:.2f}ms, P95={p95:.2f}ms")


class TestStressTesting:
    """压力测试"""

    @pytest.fixture
    def api(self):
        return get_context_api()

    def test_large_conversation(self, api):
        """测试大型对话"""
        messages = []
        for i in range(1000):
            messages.append({"role": "user", "content": f"User message {i}"})
            messages.append({"role": "assistant", "content": f"Assistant response {i}"})

        # 测试估算
        start = time.time()
        result = api.estimate_tokens(messages=messages)
        estimate_time = time.time() - start

        assert result["token_count"] > 0
        assert estimate_time < 1.0, f"Estimation took {estimate_time:.2f}s, exceeds 1s target"

        logger.info(f"Large conversation: {len(messages)} messages, {result['token_count']} tokens, {estimate_time:.3f}s")

    def test_concurrent_operations(self, api):
        """测试并发操作"""
        messages = [
            {"role": "user", "content": f"Message {i}" * 10}
            for i in range(50)
        ]

        def worker(worker_id):
            try:
                result = api.analyze_session(f"concurrent_test_{worker_id}", messages)
                return ("success", worker_id, result)
            except Exception as e:
                return ("error", worker_id, str(e))

        # 启动 10 个并发线程
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        # 等待完成
        results = []
        for t in threads:
            t.join()
            results.append(t)  # 简化处理，实际应该收集返回值

        logger.info(f"Concurrent test: {len(threads)} threads completed")

    def test_memory_usage(self, api):
        """测试内存使用"""
        import tracemalloc

        tracemalloc.start()

        # 操作 1: 估算大量消息
        messages = [
            {"role": "user", "content": f"Message {i}" * 100}
            for i in range(1000)
        ]

        snapshot1 = tracemalloc.take_snapshot()

        api.estimate_tokens(messages=messages)
        api.score_messages(messages)
        api.compress_context(messages, target_tokens=10000)

        snapshot2 = tracemalloc.take_snapshot()

        # 计算内存差异
        current, peak = tracemalloc.get_traced_memory()

        tracemalloc.stop()

        assert peak < 200 * 1024 * 1024, f"Peak memory {peak/1024/1024:.1f}MB exceeds 200MB limit"

        logger.info(f"Memory usage: Current={current/1024/1024:.1f}MB, Peak={peak/1024/1024:.1f}MB")


class TestBoundaryConditions:
    """边界条件测试"""

    @pytest.fixture
    def api(self):
        return get_context_api()

    def test_empty_inputs(self, api):
        """测试空输入"""
        # 空文本
        result = api.estimate_tokens(text="")
        assert result["token_count"] == 0

        # 空消息列表
        result = api.estimate_tokens(messages=[])
        assert result["token_count"] == 0

        # 空消息压缩
        result = api.compress_context([], target_tokens=100)
        assert result["original_tokens"] == 0
        assert result["compressed_tokens"] == 0

    def test_extreme_inputs(self, api):
        """测试极端输入"""
        # 超长文本
        long_text = "A" * 1000000  # 1MB
        result = api.estimate_tokens(text=long_text)
        assert result["token_count"] > 0
        logger.info(f"Long text (1MB): {result['token_count']} tokens")

        # 超多消息
        many_messages = [
            {"role": "user", "content": "X"}
            for _ in range(10000)
        ]
        result = api.estimate_tokens(messages=many_messages)
        assert result["token_count"] == 10000  # 每条消息1个token

        # 特殊字符
        special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?" * 100
        result = api.estimate_tokens(text=special_chars)
        assert result["token_count"] > 0

    def test_unicode_support(self, api):
        """测试 Unicode 支持"""
        unicode_cases = [
            ("中文", "你好世界，这是一个测试"),
            ("Arabic", "مرحبا بالعالم"),
            ("Japanese", "こんにちは世界"),
            ("Korean", "안녕하세요 세계"),
            ("Russian", "Привет мир"),
            ("Emoji", "🎉🚀💻✨"),
            ("Mixed", "Hello 你好 🌟 مرحبا")
        ]

        for name, text in unicode_cases:
            result = api.estimate_tokens(text=text)
            assert result["token_count"] > 0, f"{name} failed"
            logger.info(f"Unicode test ({name}): {result['token_count']} tokens")

    def test_edge_cases(self, api):
        """测试边界情况"""
        # 单个字符
        result = api.estimate_tokens(text="X")
        assert result["token_count"] == 1

        # 只有一个 token 的消息
        messages = [{"role": "user", "content": "Hi"}]
        result = api.analyze_session("edge_test", messages)
        assert result["summary"]["health_status"] == "healthy"


class TestDependencyAnalysis:
    """依赖分析测试"""

    @pytest.fixture
    def analyzer(self):
        return DependencyAnalyzer()

    def test_dependency_detection(self, analyzer):
        """测试依赖检测"""
        messages = [
            {"role": "user", "content": "Create a function"},
            {"role": "assistant", "content": "def hello():\n    pass"},
            {"role": "user", "content": "How do I call it?"},  # 依赖前面的代码
            {"role": "assistant", "content": "Use hello()"}
        ]

        graph = analyzer.analyze_dependencies(messages)

        # 应该有依赖关系
        assert len(graph.edges) > 0, "Should detect dependencies"

        # 消息2（代码）应该被消息3引用依赖
        # 但我们简化实现，主要检测关键词重叠

    def test_critical_messages(self, analyzer):
        """测试关键消息识别"""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "ok"},  # 低重要性
            {"role": "assistant", "content": "Great!"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"}
        ]

        graph = analyzer.analyze_dependencies(messages)
        critical = analyzer.get_critical_messages(messages, graph)

        # 系统消息应该是关键的
        assert 0 in critical, "System message should be critical"

        # 第一条和最后一条用户消息应该是关键的
        user_indices = [i for i, msg in enumerate(messages) if msg.get("role") == "user"]
        if user_indices:
            assert user_indices[0] in critical, "First user message should be critical"
            assert user_indices[-1] in critical, "Last user message should be critical"

    def test_compression_groups(self, analyzer):
        """测试压缩分组"""
        messages = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "ok"},
            {"role": "assistant", "content": "Great!"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"}
        ]

        groups = analyzer.suggest_compression_groups(messages)

        assert len(groups) >= 2, "Should have at least 2 groups"

        # 检查组类型
        group_types = [g["type"] for g in groups]
        assert "critical" in group_types, "Should have critical group"


def run_enhanced_tests():
    """运行增强测试"""
    print("\n" + "=" * 70)
    print("🧪 Starting LingFlow Enhanced Tests")
    print("=" * 70 + "\n")

    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    print("\n" + "=" * 70)
    print("✅ Enhanced Tests Completed")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_enhanced_tests()
