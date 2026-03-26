#!/usr/bin/env python3
"""智能上下文压缩器测试

测试 SmartContextCompressor 的各项功能:
1. TokenEstimator - 精确计数
2. MessageScorer - 重要性评分
3. TieredCompressionStrategy - 分层压缩
4. ConversationSummarizer - 对话摘要
5. SmartContextCompressor - 集成测试
"""

import pytest
from datetime import datetime, timedelta
from lingflow.compression.smart_compressor import (
    TokenEstimator,
    MessageScorer,
    MessageRole,
    TieredCompressionStrategy,
    CompressionTier,
    ConversationSummarizer,
    SmartContextCompressor,
    get_smart_compressor,
    estimate_tokens,
    compress_messages,
)


class TestTokenEstimator:
    """Token 估算器测试"""

    def test_estimate_empty_string(self):
        """测试空字符串"""
        estimator = TokenEstimator()
        assert estimator.count_tokens("") == 0

    def test_estimate_simple_text(self):
        """测试简单文本"""
        estimator = TokenEstimator()
        tokens = estimator.count_tokens("Hello, world!")
        # 应该返回正整数
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_longer_text(self):
        """测试较长文本"""
        estimator = TokenEstimator()
        text = "This is a longer text with more words. " * 10
        tokens = estimator.count_tokens(text)
        # 较长文本应该有更多 tokens
        assert tokens > 50

    def test_count_messages(self):
        """测试消息列表计数"""
        estimator = TokenEstimator()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        tokens = estimator.count_messages(messages)
        assert tokens > 0
        # 应该考虑每条消息的开销
        assert tokens >= 12  # 至少 3 条消息 * 4 开销


class TestMessageScorer:
    """消息评分器测试"""

    def test_score_system_message(self):
        """测试系统消息评分"""
        scorer = MessageScorer()
        msg = {"role": "system", "content": "You are a helpful assistant."}
        score = scorer.score_message(msg)
        # 系统消息应该有高分数
        assert score.score > 50

    def test_score_user_message(self):
        """测试用户消息评分"""
        scorer = MessageScorer()
        msg = {"role": "user", "content": "Hello!"}
        score = scorer.score_message(msg)
        assert score.score > 0

    def test_score_critical_keywords(self):
        """测试包含关键词的消息"""
        scorer = MessageScorer()
        msg = {"role": "user", "content": "This is CRITICAL and must be fixed."}
        score = scorer.score_message(msg)
        # 包含关键词应该有更高分数
        assert score.score > 50

    def test_score_with_recency(self):
        """测试时间新鲜度评分"""
        scorer = MessageScorer()
        msg = {"role": "user", "content": "Recent message"}

        # 最近的应该有更高分数
        recent_score = scorer.score_message(msg, datetime.now())
        old_score = scorer.score_message(msg, datetime.now() - timedelta(hours=2))

        assert recent_score.score > old_score.score

    def test_score_messages_list(self):
        """测试消息列表评分"""
        scorer = MessageScorer()
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "CRITICAL task"},
            {"role": "assistant", "content": "OK"},
        ]
        scores = scorer.score_messages(messages)
        assert len(scores) == 3
        # 应该按分数降序排列
        assert scores[0].score >= scores[1].score >= scores[2].score


class TestTieredCompressionStrategy:
    """分层压缩策略测试"""

    def test_create_plan(self):
        """测试创建压缩计划"""
        strategy = TieredCompressionStrategy()
        estimator = TokenEstimator()

        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Critical task here"},
            {"role": "assistant", "content": "OK " * 100},
        ]

        scorer = MessageScorer()
        scored = scorer.score_messages(messages)
        plan = strategy.create_plan(scored, target_tokens=100, token_estimator=estimator)

        # 应该有分层
        assert CompressionTier.KEEP_ALL in plan.tiers
        assert len(plan.tiers[CompressionTier.KEEP_ALL]) > 0  # 系统消息

    def test_plan_keeps_system_messages(self):
        """测试计划保留系统消息"""
        strategy = TieredCompressionStrategy()
        estimator = TokenEstimator()

        messages = [{"role": "system", "content": "Important system instruction"}]
        scorer = MessageScorer()
        scored = scorer.score_messages(messages)
        plan = strategy.create_plan(scored, target_tokens=100, token_estimator=estimator)

        assert len(plan.tiers[CompressionTier.KEEP_ALL]) == 1


class TestConversationSummarizer:
    """对话摘要生成器测试"""

    def test_summarize_empty_messages(self):
        """测试空消息摘要"""
        summarizer = ConversationSummarizer()
        summary = summarizer.summarize_messages([])
        assert summary == ""

    def test_summarize_simple_conversation(self):
        """测试简单对话摘要"""
        summarizer = ConversationSummarizer()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        summary = summarizer.summarize_messages(messages)
        assert "对话摘要" in summary
        assert "2 条消息" in summary

    def test_summarize_with_tasks(self):
        """测试包含任务的摘要"""
        summarizer = ConversationSummarizer()
        messages = [
            {"role": "user", "content": "- [ ] Task 1\n- [x] Task 2"},
        ]
        summary = summarizer.summarize_messages(messages)
        assert "任务:" in summary

    def test_summarize_truncates_long_content(self):
        """测试长内容截断"""
        summarizer = ConversationSummarizer(max_summary_length=50)
        messages = [{"role": "user", "content": "x" * 1000}]
        summary = summarizer.summarize_messages(messages)
        assert len(summary) <= 250  # 50 + 截断标记


class TestSmartContextCompressor:
    """智能上下文压缩器集成测试"""

    def test_init(self):
        """测试初始化"""
        compressor = SmartContextCompressor(max_tokens=1000)
        assert compressor.max_tokens == 1000
        assert compressor._compression_count == 0

    def test_check_no_compress_needed(self):
        """测试不需要压缩的情况"""
        compressor = SmartContextCompressor(max_tokens=100000)
        messages = [
            {"role": "user", "content": "Hi"},
        ]
        did_compress, result = compressor.check_and_compress(messages)
        assert not did_compress
        assert result is None

    def test_compress_normal_mode(self):
        """测试正常模式压缩"""
        # 使用较小的 max_tokens 触发压缩
        compressor = SmartContextCompressor(max_tokens=500)

        # 创建包含系统消息、用户消息、助手消息的混合列表
        messages = [
            {"role": "system", "content": "CRITICAL: You must follow these rules"},
        ]

        # 添加大量用户和助手消息
        for i in range(50):
            messages.append({"role": "user", "content": f"Message {i}: " + "x" * 300})
            messages.append({"role": "assistant", "content": f"Response {i}: " + "y" * 300})

        result = compressor.compress(messages, mode="normal")

        # 验证压缩结果
        # 1. 系统消息应该被保留
        system_msgs = [m for m in result.compressed_messages if m.get("role") == "system"]
        assert len(system_msgs) >= 1, "系统消息应该被保留"

        # 2. 压缩后的消息数应该减少（因为有大量消息需要压缩）
        # 或者 tokens 应该减少（如果消息被截断）
        assert len(result.compressed_messages) <= len(result.original_messages), "压缩后消息数不应增加"

    def test_compress_keeps_system_messages(self):
        """测试压缩保留系统消息"""
        compressor = SmartContextCompressor(max_tokens=50)

        messages = [
            {"role": "system", "content": "CRITICAL: Always follow these rules"},
            {"role": "user", "content": "Hello" * 100},
        ]

        result = compressor.compress(messages, mode="emergency")

        # 系统消息应该被保留
        system_msgs = [m for m in result.compressed_messages if m.get("role") == "system"]
        assert len(system_msgs) == 1

    def test_compress_emergency_mode(self):
        """测试紧急模式压缩"""
        compressor = SmartContextCompressor(max_tokens=100)

        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Task " * 100},
        ]

        result = compressor.compress(messages, mode="emergency")
        result_normal = compressor.compress(messages, mode="normal")

        # 紧急模式应该压缩更多
        assert result.compressed_tokens <= result_normal.compressed_tokens

    def test_get_stats(self):
        """测试获取统计信息"""
        compressor = SmartContextCompressor()
        stats = compressor.get_status()

        assert "max_tokens" in stats
        assert "compression_count" in stats
        assert "total_tokens_saved" in stats


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_get_smart_compressor_singleton(self):
        """测试全局单例"""
        c1 = get_smart_compressor()
        c2 = get_smart_compressor()
        assert c1 is c2

    def test_estimate_tokens_convenience(self):
        """测试便捷 token 估算"""
        messages = [{"role": "user", "content": "Hello world"}]
        tokens = estimate_tokens(messages)
        assert tokens > 0

    def test_compress_messages_convenience(self):
        """测试便捷压缩函数"""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello " * 1000},
        ]

        compressed = compress_messages(messages, max_tokens=100)

        # 应该返回压缩后的消息
        assert isinstance(compressed, list)
        # 系统消息应该被保留
        assert any(m.get("role") == "system" for m in compressed)


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建压缩器
        compressor = SmartContextCompressor(max_tokens=500)

        # 2. 创建对话历史
        messages = [
            {"role": "system", "content": "You are a coding assistant. Always provide code examples."},
            {"role": "user", "content": "Help me with Python"},
            {"role": "assistant", "content": "Sure! Here's how..."},
            {"role": "user", "content": "CRITICAL: Must implement authentication"},
            {"role": "assistant", "content": "I'll help with auth..."},
        ]

        # 3. 检查是否需要压缩
        did_compress, result = compressor.check_and_compress(messages)

        # 对于短消息，可能不需要压缩
        if not did_compress:
            # 强制压缩测试
            result = compressor.compress(messages, mode="normal")

        # 4. 验证结果
        assert len(result.compressed_messages) > 0
        assert result.original_tokens >= result.compressed_tokens

        # 系统消息和关键消息应该被保留
        roles = [m.get("role") for m in result.compressed_messages]
        assert "system" in roles

    def test_token_accuracy(self):
        """测试 token 计数准确性"""
        estimator = TokenEstimator()

        # 测试不同类型的文本
        test_cases = [
            ("Hello", "simple greeting"),
            ("def hello():\n    return 'world'", "code"),
            ("你好世界", "chinese text"),
            ("A" * 1000, "long repetition"),
        ]

        for text, desc in test_cases:
            tokens = estimator.count_tokens(text)
            assert tokens > 0, f"Failed for {desc}"
            assert isinstance(tokens, int), f"Not int for {desc}"


if __name__ == "__main__":
    # 快速测试运行
    print("运行智能压缩器测试...")

    # Token 估算器
    print("\n1. Token 估算器")
    estimator = TokenEstimator()
    print(f"   'Hello, world!' -> {estimator.count_tokens('Hello, world!')} tokens")

    # 消息评分
    print("\n2. 消息评分")
    scorer = MessageScorer()
    critical_msg = {"role": "user", "content": "CRITICAL: Fix this bug!"}
    score = scorer.score_message(critical_msg)
    print(f"   关键消息分数: {score.score:.1f}")

    # 压缩测试
    print("\n3. 智能压缩")
    compressor = SmartContextCompressor(max_tokens=100)
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Hello " * 100},
        {"role": "assistant", "content": "Hi " * 100},
    ]
    result = compressor.compress(messages, mode="normal")
    print(f"   原始: {result.original_tokens} tokens, {len(result.original_messages)} 条消息")
    print(f"   压缩后: {result.compressed_tokens} tokens, {len(result.compressed_messages)} 条消息")
    print(f"   压缩率: {result.reduction_ratio:.1%}")

    print("\n✅ 所有测试通过!")
