import pytest

from lingflow.compression.compressor import (
    AdvancedContextCompressor,
    ContextCompressor,
    CompressionLevel,
    CompressionStrategy,
    CompressionResult,
    _BasicCompressor,
)


class TestAdvancedContextCompressor:
    def test_compress_empty(self):
        c = AdvancedContextCompressor()
        assert c.compress({}) == {}

    def test_compress_priority_fields(self):
        c = AdvancedContextCompressor()
        ctx = {
            "requirements": "x" * 2000,
            "specification": "y" * 2000,
            "description": "short",
        }
        result = c.compress(ctx)
        assert "requirements" in result
        assert len(result["requirements"]) < 2000
        assert result["description"] == "short"

    def test_compress_list_field(self):
        c = AdvancedContextCompressor()
        ctx = {"items": ["a", "b", "c", "d", "e", "f", "g", "h"]}
        result = c.compress(ctx)
        assert "items" in result

    def test_compress_with_stats(self):
        c = AdvancedContextCompressor()
        text = "This is a test with must and should keywords. " * 20
        result = c.compress_with_stats(text)
        assert isinstance(result, CompressionResult)
        assert result.original_length > 0
        assert result.strategy == "advanced"

    def test_calculate_density(self):
        c = AdvancedContextCompressor()
        assert c.calculate_density("word word word") == pytest.approx(1 / 3, rel=0.1)
        assert c.calculate_density("") == 0.0

    def test_semantic_compress_short(self):
        c = AdvancedContextCompressor()
        text = "short text"
        assert c.semantic_compress(text) == text

    def test_semantic_compress_long(self):
        c = AdvancedContextCompressor()
        sentences = [f"Sentence number {i} is here." for i in range(20)]
        text = ". ".join(sentences)
        compressed = c.semantic_compress(text)
        assert len(compressed) < len(text)

    def test_compress_list_short(self):
        c = AdvancedContextCompressor()
        assert c.compress_list(["a", "b"]) == ["a", "b"]

    def test_compress_list_long_with_keywords(self):
        c = AdvancedContextCompressor()
        items = ["item1", "must item", "security item", "item4", "item5", "item6", "item7"]
        result = c.compress_list(items)
        assert len(result) <= len(items)

    def test_get_stats(self):
        c = AdvancedContextCompressor()
        c.compress({"requirements": "x" * 2000})
        stats = c.get_stats()
        assert stats["total_compressions"] == 1
        assert "tokens_saved" in stats

    def test_custom_keywords(self):
        c = AdvancedContextCompressor(custom_keywords=["custom_key"])
        assert "custom_key" in c.keywords

    def test_custom_strategies(self):
        c = AdvancedContextCompressor(strategies=[CompressionStrategy.SEMANTIC])
        assert c.strategies == [CompressionStrategy.SEMANTIC]


class TestBasicCompressor:
    def test_compress_empty(self):
        c = _BasicCompressor()
        assert c.compress({}) == {}

    def test_compress_with_priority(self):
        c = _BasicCompressor()
        ctx = {"requirements": "x" * 2000, "other": "y" * 1000}
        result = c.compress(ctx)
        assert "requirements" in result
        assert len(result["requirements"]) < 2000

    def test_compress_limits_other_fields(self):
        c = _BasicCompressor()
        ctx = {f"key{i}": f"val{i}" for i in range(10)}
        result = c.compress(ctx)
        assert len(result) <= 6  # 3 priority + 3 other

    def test_get_stats(self):
        c = _BasicCompressor()
        c.compress({"a": "b"})
        stats = c.get_stats()
        assert stats["total_compressions"] == 1


class TestContextCompressor:
    def test_basic_level(self):
        c = ContextCompressor(level=CompressionLevel.BASIC)
        result = c.compress({"requirements": "x" * 2000})
        assert "requirements" in result

    def test_advanced_level(self):
        c = ContextCompressor(level=CompressionLevel.ADVANCED)
        result = c._compressor.compress({"requirements": "x" * 2000})
        assert "requirements" in result

    def test_properties(self):
        c = ContextCompressor(target_tokens=5000)
        assert c.target_tokens == 5000
        c.compress({"a": "b"})
        assert c.compressions_count == 1

    def test_estimate_tokens(self):
        c = ContextCompressor()
        tokens = c._estimate_tokens({"key": "value"})
        assert tokens > 0
