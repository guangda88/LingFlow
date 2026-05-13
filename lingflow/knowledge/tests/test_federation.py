"""
Tests for Knowledge Federation
"""

import pytest

from lingflow.knowledge import (
    FederationConfig,
    KnowledgeFederation,
    KnowledgeItem,
    KnowledgeQuery,
    ResultSource,
)
from lingflow.knowledge.sources.base import KnowledgeSource


class MockKnowledgeSource(KnowledgeSource):
    """Mock knowledge source for testing"""

    def __init__(self, name: str, items: list = None):
        super().__init__()
        self._name = name
        self._items = items or []

    @property
    def name(self) -> str:
        return self._name

    @property
    def source_type(self) -> ResultSource:
        return ResultSource.LINGFLOW

    @property
    def project(self) -> str:
        return "test"

    async def search(self, query, context=None):
        from lingflow.knowledge.query import KnowledgeResult

        result = KnowledgeResult(sources_queried=[self._name])

        for item in self._items:
            # Simple keyword matching
            if not query.keywords or any(
                kw.lower() in item.title.lower() or kw.lower() in item.content.lower() for kw in query.keywords
            ):
                result.add_item(item)

        result.total_found = len(result.items)
        return result


class TestKnowledgeQuery:
    """Test KnowledgeQuery"""

    def test_from_keywords(self):
        query = KnowledgeQuery.from_keywords(["agent", "workflow"])
        assert query.keywords == ["agent", "workflow"]
        assert query.projects == []

    def test_from_context(self):
        query = KnowledgeQuery.from_context("This is about agents and workflows")
        assert len(query.keywords) > 0
        # Check that "agents" was extracted (plural form)
        assert "agents" in [kw.lower() for kw in query.keywords]

    def test_matches_source(self):
        query = KnowledgeQuery(keywords=["test"], sources=[ResultSource.LINGFLOW])
        assert query.matches_source(ResultSource.LINGFLOW)
        assert not query.matches_source(ResultSource.EXTERNAL_INTELLIGENCE)


class TestKnowledgeItem:
    """Test KnowledgeItem"""

    def test_to_dict(self):
        item = KnowledgeItem(
            title="Test Item",
            content="Test content",
            category="test",
            quality_score=0.8,
            source=ResultSource.LINGFLOW,
            project="lingflow",
            tags={"test", "sample"},
        )

        data = item.to_dict()
        assert data["title"] == "Test Item"
        assert data["quality_score"] == 0.8
        assert set(data["tags"]) == {"test", "sample"}


class TestKnowledgeResult:
    """Test KnowledgeResult"""

    def test_add_item(self):
        from lingflow.knowledge.query import KnowledgeResult

        result = KnowledgeResult()
        item = KnowledgeItem(title="Test", content="Content")
        result.add_item(item)

        assert len(result.items) == 1
        assert result.total_found == 0  # Not updated automatically

    def test_sort_by_relevance(self):
        from lingflow.knowledge.query import KnowledgeResult

        result = KnowledgeResult()
        result.add_item(KnowledgeItem(title="Low", content="Low", relevance_score=0.3))
        result.add_item(KnowledgeItem(title="High", content="High", relevance_score=0.9))
        result.add_item(KnowledgeItem(title="Mid", content="Mid", relevance_score=0.6))

        result.sort_by_relevance()

        assert result.items[0].title == "High"
        assert result.items[1].title == "Mid"
        assert result.items[2].title == "Low"

    def test_filter_by_quality(self):
        from lingflow.knowledge.query import KnowledgeResult

        result = KnowledgeResult()
        result.add_item(KnowledgeItem(title="Low", content="Low", quality_score=0.3))
        result.add_item(KnowledgeItem(title="High", content="High", quality_score=0.9))
        result.total_found = 2

        filtered = result.filter_by_quality(0.5)

        assert len(filtered.items) == 1
        assert filtered.items[0].title == "High"

    def test_limit(self):
        from lingflow.knowledge.query import KnowledgeResult

        result = KnowledgeResult()
        for i in range(10):
            result.add_item(KnowledgeItem(title=f"Item {i}", content=f"Content {i}"))
        result.total_found = 10

        limited = result.limit(5)

        assert len(limited.items) == 5
        assert limited.total_found == 5

    def test_merge(self):
        from lingflow.knowledge.query import KnowledgeResult

        result1 = KnowledgeResult(
            query_id="q1",
            sources_queried=["source1"],
            total_found=1,
        )
        result1.add_item(KnowledgeItem(title="Item 1", content="Content 1"))

        result2 = KnowledgeResult(
            query_id="q1",
            sources_queried=["source2"],
            total_found=1,
        )
        result2.add_item(KnowledgeItem(title="Item 2", content="Content 2"))

        merged = result1.merge(result2)

        assert len(merged.items) == 2
        assert set(merged.sources_queried) == {"source1", "source2"}
        assert merged.total_found == 2


class TestKnowledgeSource:
    """Test KnowledgeSource base class"""

    @pytest.mark.asyncio
    async def test_initialize(self):
        source = MockKnowledgeSource("test")
        assert await source.initialize() is True
        assert source.is_available is True

    def test_should_query(self):
        source = MockKnowledgeSource("test")

        # No filters
        query = KnowledgeQuery(keywords=["test"])
        assert source.should_query(query) is True

        # Source filter
        query = KnowledgeQuery(keywords=["test"], sources=[ResultSource.LINGFLOW])
        assert source.should_query(query) is True

        query = KnowledgeQuery(keywords=["test"], sources=[ResultSource.EXTERNAL_INTELLIGENCE])
        assert source.should_query(query) is False

        # Project filter
        query = KnowledgeQuery(keywords=["test"], projects=["test"])
        assert source.should_query(query) is True

        query = KnowledgeQuery(keywords=["test"], projects=["other"])
        assert source.should_query(query) is False


class TestKnowledgeFederation:
    """Test KnowledgeFederation"""

    @pytest.mark.asyncio
    async def test_initialize(self):
        federation = KnowledgeFederation()
        result = await federation.initialize()

        # Should have at least lingflow source
        assert result is True
        assert len(federation.get_available_sources()) >= 1

    @pytest.mark.asyncio
    async def test_query_by_keywords(self):
        federation = KnowledgeFederation()
        await federation.initialize()

        result = await federation.query_by_keywords(["session", "workflow"])

        assert result is not None
        assert isinstance(result.sources_queried, list)

    @pytest.mark.asyncio
    async def test_query_with_filters(self):
        federation = KnowledgeFederation()
        await federation.initialize()

        query = KnowledgeQuery(
            keywords=["test"],
            projects=["lingflow"],
            sources=[ResultSource.LINGFLOW],
        )

        result = await federation.query(query)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_source_stats(self):
        federation = KnowledgeFederation()
        await federation.initialize()

        stats = await federation.get_source_stats()

        assert isinstance(stats, dict)
        assert len(stats) > 0

    def test_federation_stats(self):
        config = FederationConfig()
        federation = KnowledgeFederation(config=config)

        stats = federation.get_stats()
        assert stats.total_queries == 0

        stats_dict = stats.to_dict()
        assert "total_queries" in stats_dict


class TestKnowledgeSync:
    """Test KnowledgeSync"""

    @pytest.mark.asyncio
    async def test_sync_from_memory(self):
        from lingflow.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync()
        result = await sync.sync_from_memory()

        assert result.source == "memory"
        assert result.sync_id is not None

    @pytest.mark.asyncio
    async def test_sync_from_research(self):
        from lingflow.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync()
        result = await sync.sync_from_research()

        assert result.source == "research"
        assert result.sync_id is not None

    @pytest.mark.asyncio
    async def test_sync_from_intelligence(self):
        from lingflow.knowledge.sync import KnowledgeSync

        sync = KnowledgeSync()
        result = await sync.sync_from_intelligence()

        assert result.source == "intelligence"
        assert result.sync_id is not None

    def test_sync_stats(self):
        from lingflow.knowledge.sync import KnowledgeSync, SyncStats

        sync = KnowledgeSync()
        stats = sync.get_stats()

        assert isinstance(stats, SyncStats)
        assert stats.total_syncs == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
