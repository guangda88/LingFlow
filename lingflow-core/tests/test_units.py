"""
LingFlow Unit Tests - 单元测试

测试各个核心模块的功能
"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    get_token_estimator,
    get_message_scorer,
    get_compression_strategy
)


class TestTokenEstimator:
    """Token 估算器测试"""

    @pytest.fixture
    def estimator(self):
        return get_token_estimator()

    def test_estimate_short_text(self, estimator):
        """测试短文本估算"""
        text = "Hello, world!"
        result = estimator.estimate(text)

        assert result.token_count > 0
        assert result.token_count < 10
        assert result.model == "default"
        assert result.estimated == False

    def test_estimate_long_text(self, estimator):
        """测试长文本估算"""
        text = "This is a longer text. " * 100
        result = estimator.estimate(text)

        assert result.token_count > 100
        assert result.estimated == False

    def test_estimate_empty_text(self, estimator):
        """测试空文本"""
        result = estimator.estimate("")

        assert result.token_count == 0

    def test_estimate_messages(self, estimator):
        """测试消息列表估算"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        result = estimator.estimate_messages(messages)

        assert result.token_count > 0
        assert result.estimated == False

    def test_estimate_code(self, estimator):
        """测试代码估算"""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        result = estimator.estimate(code)

        assert result.token_count > 0
        assert result.estimated == False


class TestMessageScorer:
    """消息评分器测试"""

    @pytest.fixture
    def scorer(self):
        return get_message_scorer()

    def test_score_user_message(self, scorer):
        """测试用户消息评分"""
        content = "I need help with a critical bug in production"
        result = scorer.score(content, role="user")

        assert 0 <= result.importance_score <= 1
        assert 0 <= result.relevance_score <= 1
        assert 0 <= result.time_score <= 1
        assert 0 <= result.quality_score <= 1
        assert result.reasoning

        # 用户消息应该有较高相关性
        assert result.relevance_score > 0.5

    def test_score_assistant_message(self, scorer):
        """测试助手消息评分"""
        content = "Here's the solution to your problem"
        result = scorer.score(content, role="assistant")

        assert 0 <= result.importance_score <= 1
        assert result.reasoning

    def test_score_code_message(self, scorer):
        """测试代码消息评分"""
        content = """
```python
def critical_function():
    pass
```
"""
        result = scorer.score(content, role="user")

        # 包含代码的消息应该有较高质量分
        assert result.quality_score > 0.5

    def test_score_short_message(self, scorer):
        """测试短消息评分"""
        content = "ok"
        result = scorer.score(content, role="user")

        # 短消息应该有较低质量分
        assert result.quality_score < 0.7

    def test_score_important_keywords(self, scorer):
        """测试重要关键词"""
        content = "This is a critical error that needs urgent fixing"
        result = scorer.score(content, role="user")

        # 包含重要关键词的消息应该有较高分
        assert result.importance_score > 0.6

    def test_batch_score(self, scorer):
        """测试批量评分"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Help me with this critical bug"}
        ]

        results = scorer.batch_score(messages)

        assert len(results) == 3
        assert all(isinstance(r, type(results[0])) for r in results)


class TestCompressionStrategy:
    """压缩策略测试"""

    @pytest.fixture
    def strategy(self):
        return get_compression_strategy()

    @pytest.fixture
    def sample_messages(self):
        """示例消息"""
        return [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "ok"},  # 低重要性
            {"role": "assistant", "content": "Great!"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"},
        ]

    def test_should_compress(self, strategy):
        """测试压缩判断"""
        # 大量消息
        large_messages = [
            {"role": "user", "content": f"Message {i} " * 100}
            for i in range(200)
        ]

        result = strategy.should_compress(large_messages, threshold=10000)

        assert result == True

    def test_should_not_compress(self, strategy):
        """测试不需要压缩"""
        small_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]

        result = strategy.should_compress(small_messages, threshold=10000)

        assert result == False

    def test_light_compression(self, strategy, sample_messages):
        """测试轻度压缩"""
        # 扩展消息使其更长
        long_messages = [
            {**msg, "content": msg["content"] * 50}  # 扩展内容
            for msg in sample_messages
        ]

        result = strategy.compress(long_messages, target_tokens=100, strategy="light")

        assert result.original_tokens > 0
        assert result.compressed_messages is not None
        # 确保确实需要压缩
        if result.original_tokens > 100:
            assert len(result.compressed_messages) <= len(long_messages)

    def test_aggressive_compression(self, strategy, sample_messages):
        """测试激进压缩"""
        # 扩展消息使其更长
        long_messages = [
            {**msg, "content": msg["content"] * 50}  # 扩展内容
            for msg in sample_messages
        ]

        result = strategy.compress(long_messages, target_tokens=50, strategy="aggressive")

        assert result.original_tokens > 0
        # 确保确实需要压缩
        if result.original_tokens > 50:
            assert len(result.compressed_messages) < len(long_messages)

    def test_auto_compression(self, strategy):
        """测试自动压缩策略"""
        # 创建一个中等大小的消息列表
        messages = [
            {"role": "user", "content": f"Message {i} " * 50}
            for i in range(50)
        ]

        result = strategy.compress(messages, target_tokens=1000, strategy="auto")

        assert result.original_tokens > result.compressed_tokens
        assert result.reduction_ratio > 0

    def test_compression_recommendation(self, strategy):
        """测试压缩建议"""
        messages = [
            {"role": "user", "content": f"Message {i} " * 100}
            for i in range(100)
        ]

        result = strategy.get_compression_recommendation(messages, target_tokens=5000)

        assert "should_compress" in result
        assert "recommended_strategy" in result
        assert "current_tokens" in result
        assert "target_tokens" in result


def run_unit_tests():
    """运行所有单元测试"""
    print("\n" + "=" * 70)
    print("🧪 Starting LingFlow Unit Tests")
    print("=" * 70 + "\n")

    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    print("\n" + "=" * 70)
    print("✅ Unit Tests Completed")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_unit_tests()
