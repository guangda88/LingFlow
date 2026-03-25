"""Tests for ContextCompressor"""

import asyncio
import pytest

from lingflow.compression.compressor import ContextCompressor


class TestContextCompressorInitialization:
    """Test compressor initialization"""

    def test_initialization_default(self):
        """Test initialization with default target"""
        compressor = ContextCompressor()
        assert compressor.target_tokens == 4000
        assert compressor.compressions_count == 0
        assert compressor.tokens_saved == 0

    def test_initialization_custom_target(self):
        """Test initialization with custom target"""
        compressor = ContextCompressor(target_tokens=8000)
        assert compressor.target_tokens == 8000


class TestCompress:
    """Test context compression"""

    def test_compress_empty_context(self):
        """Test compressing empty context"""
        compressor = ContextCompressor()
        result = compressor.compress({})
        assert result == {}

    def test_compress_none_context(self):
        """Test compressing None context"""
        compressor = ContextCompressor()
        result = compressor.compress(None)
        assert result is None

    def test_compress_preserves_priority_keys(self):
        """Test that priority keys are preserved"""
        compressor = ContextCompressor()
        context = {
            "requirements": "Must be secure",
            "specification": "API spec",
            "description": "Project description",
            "other": "Should be excluded if full",
        }
        result = compressor.compress(context)
        assert "requirements" in result
        assert "specification" in result
        assert "description" in result

    def test_compress_truncates_long_priority_text(self):
        """Test that long text in priority keys is truncated"""
        compressor = ContextCompressor()
        long_text = "a" * 1500
        context = {"requirements": long_text}
        result = compressor.compress(context)
        assert len(result["requirements"]) <= 1000 + len("... [truncated]")
        assert "... [truncated]" in result["requirements"]

    def test_compress_limits_other_fields(self):
        """Test that other fields are limited to 3 items"""
        compressor = ContextCompressor()
        context = {
            "field1": "value1",
            "field2": "value2",
            "field3": "value3",
            "field4": "value4",  # Should be excluded
            "field5": "value5",  # Should be excluded
        }
        result = compressor.compress(context)
        assert len([k for k in result.keys() if not k in ["requirements", "specification", "description"]]) <= 3
        assert "field4" not in result
        assert "field5" not in result

    def test_compress_truncates_other_fields(self):
        """Test that other fields are truncated to 500 chars"""
        compressor = ContextCompressor()
        long_value = "b" * 600
        context = {"field1": long_value}
        result = compressor.compress(context)
        assert len(result["field1"]) <= 500

    def test_compress_updates_stats(self):
        """Test that compression updates statistics"""
        compressor = ContextCompressor()
        # Use long text that will be truncated to ensure tokens are saved
        long_text = "x" * 2000
        context = {"requirements": long_text, "field1": "y" * 1000}
        result = compressor.compress(context)
        assert compressor.compressions_count == 1
        # Verify actual truncation happened
        assert len(result["requirements"]) < len(long_text)
        assert len(result["field1"]) < 1000
        assert compressor.tokens_saved > 0

    def test_compress_non_string_values(self):
        """Test that non-string values are converted to strings"""
        compressor = ContextCompressor()
        context = {"requirements": 123, "field1": [1, 2, 3]}
        result = compressor.compress(context)
        assert isinstance(result["requirements"], str)
        assert isinstance(result["field1"], str)


class TestEstimateTokens:
    """Test token estimation"""

    def test_estimate_tokens_text(self):
        """Test estimating tokens from text"""
        compressor = ContextCompressor()
        tokens = compressor._estimate_tokens("hello world")
        # Simple estimation: 4 characters per token
        # "hello world" is 11 characters
        assert tokens == 11 // 4

    def test_estimate_tokens_empty_string(self):
        """Test estimating tokens from empty string"""
        compressor = ContextCompressor()
        tokens = compressor._estimate_tokens("")
        assert tokens == 0

    def test_estimate_tokens_long_text(self):
        """Test estimating tokens from long text"""
        compressor = ContextCompressor()
        long_text = "a" * 4000
        tokens = compressor._estimate_tokens(long_text)
        assert tokens == 1000  # 4000 chars / 4

    def test_estimate_tokens_non_string(self):
        """Test estimating tokens from non-string input"""
        compressor = ContextCompressor()
        tokens = compressor._estimate_tokens(12345)
        assert tokens == len("12345") // 4


class TestGetStats:
    """Test statistics retrieval"""

    def test_get_stats_initial(self):
        """Test getting initial statistics"""
        compressor = ContextCompressor()
        stats = compressor.get_stats()
        assert stats["total_compressions"] == 0
        assert stats["tokens_saved"] == 0

    def test_get_stats_after_compression(self):
        """Test getting statistics after compression"""
        compressor = ContextCompressor()
        long_text = "x" * 2000
        compressor.compress({"requirements": long_text, "field1": "value"})
        stats = compressor.get_stats()
        assert stats["total_compressions"] == 1
        assert stats["tokens_saved"] > 0

    def test_get_stats_multiple_compressions(self):
        """Test getting statistics after multiple compressions"""
        compressor = ContextCompressor()
        long_text = "x" * 2000
        for i in range(5):
            compressor.compress({"requirements": f"{long_text}{i}", "field1": f"value{i}"})
        stats = compressor.get_stats()
        assert stats["total_compressions"] == 5
        assert stats["tokens_saved"] > 0


class TestCompressionIntegration:
    """Integration tests for compression"""

    def test_compression_saves_tokens(self):
        """Test that compression actually saves tokens"""
        compressor = ContextCompressor()
        original_context = {
            "requirements": "a" * 2000,  # Long text
            "specification": "b" * 2000,  # Long text
            "field1": "c" * 600,  # Will be truncated
            "field2": "d" * 600,  # Will be truncated
            "field3": "e" * 600,  # Will be truncated
            "field4": "f" * 600,  # Will be excluded
        }
        original_tokens = compressor._estimate_tokens(original_context)
        compressed = compressor.compress(original_context)
        compressed_tokens = compressor._estimate_tokens(compressed)
        assert compressed_tokens < original_tokens
        assert compressor.tokens_saved > 0

    def test_compression_preserves_data(self):
        """Test that compression preserves important data"""
        compressor = ContextCompressor()
        context = {
            "requirements": "Security is paramount",
            "specification": "REST API v1",
            "description": "Secure banking app",
        }
        compressed = compressor.compress(context)
        assert "Security is paramount" in compressed["requirements"]
        assert "REST API v1" in compressed["specification"]
        assert "Secure banking app" in compressed["description"]


class TestCompressorConcurrentSafety:
    """Test concurrent safety of the compressor"""

    @pytest.mark.asyncio
    async def test_concurrent_compression_no_data_corruption(self):
        """Test that concurrent compressions don't corrupt data"""
        compressor = ContextCompressor()

        async def compress_context(context_id):
            """Compress a unique context"""
            long_text = "a" * 1000
            context = {
                "requirements": f"Req {context_id}: {long_text}",
                "specification": f"Spec {context_id}: {long_text}",
                f"field_{context_id}": f"Value {context_id}: " + "b" * 600,
            }
            result = compressor.compress(context)
            # Verify that our data is preserved
            assert f"Req {context_id}:" in result["requirements"]
            assert f"Spec {context_id}:" in result["specification"]
            return context_id

        # Run 50 concurrent compressions
        tasks = [compress_context(i) for i in range(50)]
        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 50
        assert set(results) == set(range(50))

    @pytest.mark.asyncio
    async def test_concurrent_compression_stats_consistency(self):
        """Test that stats are consistent after concurrent compressions"""
        compressor = ContextCompressor()

        async def compress_one():
            """Perform one compression"""
            long_text = "x" * 2000
            return compressor.compress({"requirements": long_text})

        # Run 20 concurrent compressions
        tasks = [compress_one() for _ in range(20)]
        await asyncio.gather(*tasks)

        # Stats should be accurate
        stats = compressor.get_stats()
        assert stats["total_compressions"] == 20
        assert stats["tokens_saved"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_mixed_contexts(self):
        """Test concurrent compression with different context types"""
        compressor = ContextCompressor()

        async def compress_small():
            """Compress small context"""
            return compressor.compress({"requirements": "Small req"})

        async def compress_large():
            """Compress large context"""
            long_text = "a" * 5000
            return compressor.compress({
                "requirements": long_text,
                "specification": "b" * 5000,
                "description": "c" * 3000,
                "field1": "d" * 700,
                "field2": "e" * 700,
                "field3": "f" * 700,
                "field4": "g" * 700,
            })

        async def compress_medium():
            """Compress medium context"""
            return compressor.compress({
                "requirements": "Medium req",
                "description": "Medium desc",
            })

        # Mix different types of compressions (note: empty dicts return early, so not counted)
        tasks = [
            *[compress_small() for _ in range(10)],
            *[compress_large() for _ in range(10)],
            *[compress_medium() for _ in range(10)],
        ]

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 30

        # Stats should reflect all compressions (all 30 have content)
        stats = compressor.get_stats()
        assert stats["total_compressions"] == 30

    @pytest.mark.asyncio
    async def test_concurrent_compression_with_none(self):
        """Test concurrent compression including None values"""
        compressor = ContextCompressor()

        async def compress_variant(value):
            """Compress with different input types"""
            return compressor.compress(value)

        # Mix of None, empty, and valid contexts
        tasks = [
            compress_variant(None),
            compress_variant({}),
            compress_variant({"requirements": "valid"}),
            compress_variant(None),
            compress_variant({"requirements": "x" * 2000}),
            *[compress_variant({}) for _ in range(5)],
        ]

        results = await asyncio.gather(*tasks)

        # None should return None
        none_count = sum(1 for r in results if r is None)
        assert none_count == 2

        # Empty dicts should return empty dicts
        empty_count = sum(1 for r in results if r == {})
        assert empty_count == 6

    @pytest.mark.asyncio
    async def test_concurrent_compression_high_concurrency(self):
        """Test compressor under high concurrency"""
        compressor = ContextCompressor()

        async def compress_batch(batch_id):
            """Compress a batch of contexts"""
            batch_results = []
            for i in range(10):
                context = {
                    "requirements": f"Batch {batch_id} Item {i}: " + "a" * 500,
                    "specification": f"Spec {batch_id}",
                }
                result = compressor.compress(context)
                batch_results.append(result)
            return batch_id

        # Create 20 batches, each with 10 compressions = 200 total compressions
        tasks = [compress_batch(i) for i in range(20)]
        results = await asyncio.gather(*tasks)

        # All batches should complete
        assert len(results) == 20
        assert set(results) == set(range(20))

        # Stats should reflect all compressions
        stats = compressor.get_stats()
        assert stats["total_compressions"] == 200
