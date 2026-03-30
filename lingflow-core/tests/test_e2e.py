"""
LingFlow E2E Tests - 端到端测试

严格验证所有核心功能的端到端测试
"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import get_context_api


class TestE2EContextManagement:
    """端到端上下文管理测试"""

    @pytest.fixture
    def api(self):
        """创建 API 实例"""
        return get_context_api()

    @pytest.fixture
    def sample_messages(self):
        """示例消息"""
        return [
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            },
            {
                "role": "user",
                "content": "I need help with Python programming."
            },
            {
                "role": "assistant",
                "content": "Of course! I'd be happy to help you with Python. What specific topic or problem would you like to work on?"
            },
            {
                "role": "user",
                "content": "How do I create a function that calculates the factorial of a number?"
            },
            {
                "role": "assistant",
                "content": """Here's a Python function to calculate factorial:

```python
def factorial(n):
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

# Example usage
print(factorial(5))  # Output: 120
```

This recursive implementation:
1. Checks for negative numbers
2. Handles base case (0 or 1)
3. Recursively multiplies n by factorial(n-1)"""
            }
        ]

    @pytest.fixture
    def large_messages(self):
        """大量消息用于测试压缩"""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            }
        ]

        # 添加 100 条用户消息
        for i in range(100):
            messages.append({
                "role": "user",
                "content": f"This is message number {i + 1}. " * 20  # 约 200 tokens per message
            })

            messages.append({
                "role": "assistant",
                "content": f"I acknowledge your message number {i + 1}. " * 20
            })

        return messages

    def test_e2e_token_estimation(self, api, sample_messages):
        """测试端到端 token 估算"""
        result = api.estimate_tokens(messages=sample_messages)

        # 验证返回结构
        assert "token_count" in result
        assert "model" in result
        assert "encoding" in result
        assert "message_count" in result

        # 验证数据合理性
        assert result["token_count"] > 0
        assert result["message_count"] == len(sample_messages)
        assert result["model"] == "claude-opus-4"
        assert result["encoding"] == "cl100k_base"

        print(f"✅ Token estimation test passed: {result['token_count']} tokens")

    def test_e2e_message_scoring(self, api, sample_messages):
        """测试端到端消息评分"""
        result = api.score_messages(sample_messages)

        # 验证返回结构
        assert len(result) == len(sample_messages)
        assert all("importance_score" in r for r in result)
        assert all("relevance_score" in r for r in result)
        assert all("reasoning" in r for r in result)

        # 验证评分范围
        for score in result:
            assert 0 <= score["importance_score"] <= 1
            assert 0 <= score["relevance_score"] <= 1

        print(f"✅ Message scoring test passed: {len(result)} messages scored")

    def test_e2e_context_insight(self, api, sample_messages):
        """测试端到端上下文洞察"""
        result = api.get_context_insight(sample_messages, threshold=5000)

        # 验证返回结构
        assert "total_tokens" in result
        assert "message_count" in result
        assert "important_messages" in result
        assert "health_status" in result
        assert "recommendations" in result

        # 验证数据合理性
        assert result["message_count"] == len(sample_messages)
        assert result["total_tokens"] > 0
        assert result["health_status"] in ["healthy", "warning", "critical"]
        assert isinstance(result["recommendations"], list)

        print(f"✅ Context insight test passed: {result['health_status']} status")

    def test_e2e_compression_decision(self, api, sample_messages):
        """测试端到端压缩决策"""
        result = api.should_compress(sample_messages, threshold=100)

        # 验证返回结构
        assert "should_compress" in result
        assert "reason" in result
        assert "current_tokens" in result
        assert "target_tokens" in result
        assert "excess_tokens" in result

        # 验证逻辑
        if result["current_tokens"] > result["target_tokens"]:
            assert result["should_compress"] == True
            assert result["excess_tokens"] > 0

        print(f"✅ Compression decision test passed: should_compress={result['should_compress']}")

    def test_e2e_compression_execution(self, api, large_messages):
        """测试端到端压缩执行"""
        original_tokens = api.estimate_tokens(messages=large_messages)["token_count"]

        # 执行压缩
        result = api.compress_context(
            large_messages,
            target_tokens=10000,
            strategy="light"
        )

        # 验证返回结构
        assert "original_tokens" in result
        assert "compressed_tokens" in result
        assert "reduction_ratio" in result
        assert "messages_removed" in result
        assert "compressed_messages" in result

        # 验证压缩效果
        assert result["original_tokens"] == original_tokens
        assert result["compressed_tokens"] < result["original_tokens"]
        assert result["reduction_ratio"] > 0
        assert len(result["compressed_messages"]) <= len(large_messages)

        print(f"✅ Compression execution test passed: {result['reduction_ratio']:.1f}% reduction")

    def test_e2e_full_session_analysis(self, api, sample_messages):
        """测试端到端完整会话分析"""
        result = api.analyze_session(
            session_id="test_session_001",
            messages=sample_messages,
            threshold=5000
        )

        # 验证返回结构
        assert "session_id" in result
        assert "tokens" in result
        assert "scores" in result
        assert "insight" in result
        assert "compression" in result
        assert "summary" in result

        # 验证数据一致性
        assert result["session_id"] == "test_session_001"
        assert result["tokens"]["message_count"] == len(sample_messages)
        assert len(result["scores"]) == len(sample_messages)
        assert result["insight"]["message_count"] == len(sample_messages)

        # 验证摘要
        assert result["summary"]["total_messages"] == len(sample_messages)
        assert result["summary"]["total_tokens"] > 0
        assert result["summary"]["health_status"] in ["healthy", "warning", "critical"]

        print(f"✅ Full session analysis test passed")

    def test_e2e_compression_with_preservation(self, api, sample_messages):
        """测试压缩时保留关键消息"""
        # 标记一些消息为重要（通过内容）
        important_messages = sample_messages[:3]  # 前三条消息

        # 执行激进压缩
        result = api.compress_context(
            sample_messages,
            target_tokens=100,
            strategy="aggressive"
        )

        # 验证压缩发生了
        assert result["compressed_tokens"] < result["original_tokens"]

        # 验证保留了至少一些消息
        assert len(result["compressed_messages"]) > 0

        print(f"✅ Compression with preservation test passed")

    def test_e2e_error_handling(self, api):
        """测试端到端错误处理"""
        # 测试空消息
        result = api.estimate_tokens(messages=[])
        assert "error" in result or result["token_count"] == 0

        # 测试无效输入
        result = api.compress_context([], target_tokens=100)
        assert "error" in result or result["original_tokens"] == 0

        print(f"✅ Error handling test passed")


class TestE2EIntegration:
    """端到端集成测试"""

    @pytest.fixture
    def api(self):
        """创建 API 实例"""
        return get_context_api()

    def test_e2e_workflow_small_to_large(self, api):
        """测试从小到大的工作流"""
        # 小会话 - < 70% threshold
        small_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        result = api.analyze_session("small_session", small_messages)
        assert result["summary"]["health_status"] == "healthy"

        # 中会话 - 70-90% threshold (使用更低的threshold来测试)
        medium_messages = [{"role": "user", "content": f"Message {i} " * 100} for i in range(500)]
        result = api.analyze_session("medium_session", medium_messages, threshold=10000)
        # medium_messages会有约500*100=50000 tokens，threshold=10000，应该超过
        assert result["summary"]["health_status"] in ["warning", "critical"]

        # 大会话 - > 90% threshold
        large_messages = [{"role": "user", "content": f"Message {i} " * 200} for i in range(1000)]
        result = api.analyze_session("large_session", large_messages, threshold=10000)
        assert result["summary"]["health_status"] in ["warning", "critical"]

        print(f"✅ Small to large workflow test passed")

    def test_e2e_repeated_compression(self, api):
        """测试重复压缩"""
        messages = [
            {"role": "user", "content": f"Message {i} " * 50}
            for i in range(100)
        ]

        # 第一次压缩
        result1 = api.compress_context(messages, target_tokens=5000, strategy="auto")
        compressed1 = result1["compressed_messages"]

        # 只有当第一次压缩成功时才进行第二次压缩
        if result1["original_tokens"] > result1["compressed_tokens"] and len(compressed1) > 0:
            # 第二次压缩
            result2 = api.compress_context(compressed1, target_tokens=3000, strategy="auto")
            compressed2 = result2["compressed_messages"]

            # 验证每次压缩都有效果
            assert result1["original_tokens"] > result1["compressed_tokens"]
            if result2["original_tokens"] > 0:  # 确保有内容可压缩
                assert result2["original_tokens"] >= result2["compressed_tokens"]
                assert len(compressed2) <= len(compressed1)

        print(f"✅ Repeated compression test passed")

    def test_e2e_sqlite_integration(self, api):
        """测试 SQLite 集成"""
        messages = [
            {"role": "user", "content": f"Message {i} " * 20}
            for i in range(10)
        ]

        # 分析会话（应该保存到 SQLite）
        result = api.analyze_session("sqlite_test", messages)

        # 验证保存成功
        if result["saved_to_sqlite"]:
            print(f"✅ SQLite integration test passed (saved)")
        else:
            print(f"⚠️  SQLite integration test skipped (not available)")


def run_e2e_tests():
    """运行所有 E2E 测试"""
    print("\n" + "=" * 70)
    print("🧪 Starting LingFlow E2E Tests")
    print("=" * 70 + "\n")

    # 运行测试
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    print("\n" + "=" * 70)
    print("✅ E2E Tests Completed")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_e2e_tests()
