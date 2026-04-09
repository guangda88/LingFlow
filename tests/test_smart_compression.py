#!/usr/bin/env python3
"""智能上下文压缩器测试

测试 SmartContextCompressor 的各项功能:
1. TokenEstimator - 精确计数
2. MessageScorer - 重要性评分
3. TieredCompressionStrategy - 分层压缩
4. ConversationSummarizer - 对话摘要
5. SmartContextCompressor - 集成测试
"""

from datetime import datetime, timedelta

import pytest

from lingflow.compression.scoring import MessageRole, MessageScorer
from lingflow.compression.smart_compressor import (
    SmartContextCompressor,
    compress_messages,
    get_default_compressor,
)
from lingflow.compression.strategies.base import CompressionTier, TieredCompressionStrategy
from lingflow.compression.summarizer import ConversationSummarizer
from lingflow.compression.token_estimator import TokenEstimator


def estimate_tokens(text_or_messages) -> int:
    if isinstance(text_or_messages, str):
        return TokenEstimator().count_tokens(text_or_messages)
    return TokenEstimator().count_messages_tokens(text_or_messages)


class TestTokenEstimator:
    """Token 估算器测试"""

    def test_estimate_empty_string(self):
        estimator = TokenEstimator()
        assert estimator.count_tokens("") == 0

    def test_estimate_simple_text(self):
        estimator = TokenEstimator()
        tokens = estimator.count_tokens("Hello, world!")
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_estimate_longer_text(self):
        estimator = TokenEstimator()
        text = "This is a longer text with more words. " * 10
        tokens = estimator.count_tokens(text)
        assert tokens > 50

    def test_count_messages_tokens(self):
        estimator = TokenEstimator()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        tokens = estimator.count_messages_tokens(messages)
        assert tokens > 0


class TestMessageScorer:
    """消息评分器测试"""

    def test_score_system_message(self):
        scorer = MessageScorer()
        msg = {"role": "system", "content": "You are a helpful assistant."}
        score = scorer.score_message(msg)
        assert score.score > 0

    def test_score_user_message(self):
        scorer = MessageScorer()
        msg = {"role": "user", "content": "Hello!"}
        score = scorer.score_message(msg)
        assert score.score > 0

    def test_score_critical_keywords(self):
        scorer = MessageScorer()
        msg = {"role": "user", "content": "This is CRITICAL and must be fixed."}
        score = scorer.score_message(msg)
        assert score.score > 0

    def test_score_with_recency(self):
        scorer = MessageScorer()
        recent_msg = {"role": "user", "content": "Recent message", "timestamp": datetime.now().isoformat()}
        old_msg = {"role": "user", "content": "Recent message", "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()}
        recent_score = scorer.score_message(recent_msg)
        old_score = scorer.score_message(old_msg)
        assert recent_score.score > old_score.score

    def test_score_messages_list(self):
        scorer = MessageScorer()
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "CRITICAL task"},
            {"role": "assistant", "content": "OK"},
        ]
        scores = scorer.score_messages(messages)
        assert len(scores) == 3


class TestTieredCompressionStrategy:
    """分层压缩策略测试"""

    def test_create_plan(self):
        strategy = TieredCompressionStrategy()
        scorer = MessageScorer()
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Critical task here"},
            {"role": "assistant", "content": "OK " * 100},
        ]
        scores = scorer.score_messages(messages)
        plan = strategy.create_plan(
            messages=messages,
            current_tokens=500,
            target_tokens=50,
            scores=scores,
        )
        assert plan is not None
        assert isinstance(plan.tier, CompressionTier)

    def test_plan_identifies_tier(self):
        strategy = TieredCompressionStrategy()
        scorer = MessageScorer()
        messages = [
            {"role": "system", "content": "Important system instruction"},
        ]
        scores = scorer.score_messages(messages)
        plan = strategy.create_plan(
            messages=messages,
            current_tokens=100,
            target_tokens=50,
            scores=scores,
        )
        assert isinstance(plan.tier, CompressionTier)


class TestConversationSummarizer:
    """对话摘要生成器测试"""

    def test_summarize_empty_messages(self):
        summarizer = ConversationSummarizer()
        result = summarizer.summarize([])
        assert isinstance(result, str)

    def test_summarize_simple_conversation(self):
        summarizer = ConversationSummarizer()
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        summary = summarizer.summarize(messages)
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_create_summary_message(self):
        summarizer = ConversationSummarizer()
        messages = [
            {"role": "user", "content": "- [ ] Task 1\n- [x] Task 2"},
        ]
        msg = summarizer.create_summary_message(messages)
        assert isinstance(msg, dict)
        assert "role" in msg
        assert "content" in msg


class TestSmartContextCompressor:
    """智能上下文压缩器集成测试"""

    def test_init(self):
        from lingflow.compression.smart_compressor import CompressionConfig

        config = CompressionConfig(max_tokens=1000)
        compressor = SmartContextCompressor(config=config)
        assert compressor.config.max_tokens == 1000

    def test_count_tokens(self):
        compressor = SmartContextCompressor()
        messages = [{"role": "user", "content": "Hi"}]
        tokens = compressor.count_tokens(messages)
        assert tokens > 0

    def test_compress_no_op(self):
        from lingflow.compression.smart_compressor import CompressionConfig

        config = CompressionConfig(max_tokens=100000)
        compressor = SmartContextCompressor(config=config)
        messages = [{"role": "user", "content": "Hi"}]
        result = compressor.compress(messages, target_tokens=100000)
        assert result.compressed_messages == messages

    def test_compress_reduces_tokens(self):
        from lingflow.compression.smart_compressor import CompressionConfig

        config = CompressionConfig(max_tokens=50)
        compressor = SmartContextCompressor(config=config)
        messages = [
            {"role": "system", "content": "CRITICAL: Always follow these rules"},
            {"role": "user", "content": "Hello " * 200},
        ]
        result = compressor.compress(messages, target_tokens=50)
        assert result.compressed_tokens <= result.original_tokens

    def test_compress_keeps_system_messages(self):
        from lingflow.compression.smart_compressor import CompressionConfig

        config = CompressionConfig(max_tokens=20)
        compressor = SmartContextCompressor(config=config)
        messages = [
            {"role": "system", "content": "CRITICAL: Always follow these rules"},
            {"role": "user", "content": "Hello " * 100},
        ]
        result = compressor.compress(messages, target_tokens=20)
        system_msgs = [m for m in result.compressed_messages if m.get("role") == "system"]
        assert len(system_msgs) >= 1

    def test_compress_if_needed(self):
        from lingflow.compression.smart_compressor import CompressionConfig

        config = CompressionConfig(max_tokens=10)
        compressor = SmartContextCompressor(config=config)
        messages = [
            {"role": "user", "content": "Hello world, this is a long message " * 50},
        ]
        result = compressor.compress_if_needed(messages, target_tokens=10)
        assert isinstance(result, list)

    def test_get_stats(self):
        compressor = SmartContextCompressor()
        messages = [{"role": "user", "content": "Hello"}]
        stats = compressor.get_stats(messages)
        assert "token_count" in stats
        assert "max_tokens" in stats


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_get_default_compressor_singleton(self):
        c1 = get_default_compressor()
        c2 = get_default_compressor()
        assert c1 is c2

    def test_compress_messages_convenience(self):
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello " * 1000},
        ]
        compressed = compress_messages(messages, target_tokens=100)
        assert isinstance(compressed, list)


class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        from lingflow.compression.smart_compressor import CompressionConfig

        config = CompressionConfig(max_tokens=50)
        compressor = SmartContextCompressor(config=config)
        messages = [
            {"role": "system", "content": "You are a coding assistant."},
            {"role": "user", "content": "Help me with Python " * 20},
            {"role": "assistant", "content": "Sure! Here's how... " * 20},
            {"role": "user", "content": "CRITICAL: Must implement auth " * 10},
        ]
        result = compressor.compress(messages, target_tokens=50)
        assert len(result.compressed_messages) > 0
        assert result.original_tokens >= result.compressed_tokens
        roles = [m.get("role") for m in result.compressed_messages]
        assert "system" in roles

    def test_token_accuracy(self):
        estimator = TokenEstimator()
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
