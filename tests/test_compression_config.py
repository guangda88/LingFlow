import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from lingflow.compression.config import (
    CompressionConfig,
    ConversationCompressor,
    get_conversation_compressor,
    compress_if_needed,
    compress_messages,
    enable_auto_compression,
)


class TestCompressionConfig:
    def test_default_config(self):
        cfg = CompressionConfig()
        assert cfg.enabled is True
        assert cfg.target_ratio == 0.4
        assert cfg.threshold_tokens == 50000

    def test_custom_config(self):
        cfg = CompressionConfig({"enabled": False, "target_ratio": 0.5})
        assert cfg.enabled is False
        assert cfg.target_ratio == 0.5

    def test_create_compressor(self):
        cfg = CompressionConfig()
        compressor = cfg.create_compressor()
        assert compressor is not None

    def test_empty_config(self):
        cfg = CompressionConfig({})
        assert cfg.enabled is True

    def test_none_config(self):
        cfg = CompressionConfig(None)
        assert cfg.enabled is True

    def test_strategies(self):
        cfg = CompressionConfig({"strategies": ["density"]})
        compressor = cfg.create_compressor()
        assert compressor is not None


class TestConversationCompressor:
    def test_init_default(self):
        cc = ConversationCompressor()
        assert cc.config is not None

    def test_init_custom_config(self):
        cfg = CompressionConfig({"enabled": False})
        cc = ConversationCompressor(config=cfg)
        assert cc.config.enabled is False

    def test_estimate_tokens(self):
        cc = ConversationCompressor()
        tokens = cc.estimate_tokens("hello world")
        assert tokens > 0

    def test_should_compress_disabled(self):
        cfg = CompressionConfig({"enabled": False})
        cc = ConversationCompressor(config=cfg)
        assert cc.should_compress({"key": "x" * 100000}) is False

    def test_should_compress_below_threshold(self):
        cc = ConversationCompressor()
        assert cc.should_compress({"key": "hello"}) is False

    def test_should_compress_string_values(self):
        cfg = CompressionConfig({"threshold_tokens": 10})
        cc = ConversationCompressor(config=cfg)
        assert cc.should_compress({"key": "x" * 1000}) is True

    def test_should_compress_list_values(self):
        cfg = CompressionConfig({"threshold_tokens": 10})
        cc = ConversationCompressor(config=cfg)
        ctx = {"items": ["x" * 100] * 10}
        assert cc.should_compress(ctx) is True

    def test_should_compress_dict_values(self):
        cfg = CompressionConfig({"threshold_tokens": 10})
        cc = ConversationCompressor(config=cfg)
        ctx = {"data": {"nested": "x" * 1000}}
        assert cc.should_compress(ctx) is True

    def test_compress_context_no_need(self):
        cc = ConversationCompressor()
        ctx = {"key": "small"}
        result = cc.compress_context(ctx)
        assert result == ctx

    def test_compress_context_with_need(self):
        cfg = CompressionConfig({"threshold_tokens": 10})
        cc = ConversationCompressor(config=cfg)
        ctx = {"key": "x" * 10000}
        result = cc.compress_context(ctx)
        assert isinstance(result, (dict, str))

    def test_compress_conversation_history_short(self):
        cc = ConversationCompressor()
        msgs = [{"role": "user", "content": f"msg {i}"} for i in range(5)]
        result = cc.compress_conversation_history(msgs, keep_recent=10)
        assert len(result) == 5

    def test_compress_conversation_history_long(self):
        cc = ConversationCompressor()
        msgs = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        result = cc.compress_conversation_history(msgs, keep_recent=5)
        assert len(result) <= 6

    def test_get_stats_initial(self):
        cc = ConversationCompressor()
        stats = cc.get_stats()
        assert stats["compression_count"] == 0
        assert stats["total_saved_tokens"] == 0
        assert "config" in stats


class TestGetConversationCompressor:
    def test_singleton(self):
        import lingflow.compression.config as mod
        mod._conversation_compressor = None
        c1 = get_conversation_compressor()
        c2 = get_conversation_compressor()
        assert c1 is c2
        mod._conversation_compressor = None

    def test_with_config(self):
        import lingflow.compression.config as mod
        mod._conversation_compressor = None
        cfg = CompressionConfig({"enabled": False})
        c = get_conversation_compressor(config=cfg)
        assert c.config.enabled is False
        mod._conversation_compressor = None


class TestCompressIfNeeded:
    def test_small_context(self):
        import lingflow.compression.config as mod
        mod._conversation_compressor = None
        result = compress_if_needed({"key": "small"})
        assert isinstance(result, dict)
        mod._conversation_compressor = None


class TestCompressMessages:
    def test_short_messages(self):
        import lingflow.compression.config as mod
        mod._conversation_compressor = None
        msgs = [{"role": "user", "content": "hi"}]
        result = compress_messages(msgs)
        assert len(result) >= 1
        mod._conversation_compressor = None


class TestEnableAutoCompression:
    def test_enable(self):
        import lingflow.compression.config as mod
        mod._conversation_compressor = None
        enable_auto_compression(threshold_tokens=1000)
        c = get_conversation_compressor()
        assert c.config.threshold_tokens == 1000
        mod._conversation_compressor = None
