"""
Knowledge Federation

Implements the cross-project knowledge federation that coordinates
queries across multiple knowledge sources.
"""

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from lingflow.knowledge.query import (
    KnowledgeItem,
    KnowledgeQuery,
    KnowledgeResult,
    ResultSource,
)
from lingflow.knowledge.sources.base import (
    KnowledgeSource,
    SearchContext,
    SearchResult,
)
from lingflow.knowledge.sources.external import ExternalIntelligenceSource
from lingflow.knowledge.sources.lingflow import LingFlowKnowledgeSource
from lingflow.knowledge.sources.lingtongask import LingTongAskKnowledgeSource


@dataclass(frozen=True)
class FederationConfig:
    """Configuration for knowledge federation"""

    # Query timeout
    query_timeout_seconds: float = 30.0

    # Result limits
    max_results_per_source: int = 20
    max_total_results: int = 50

    # Quality thresholds
    min_quality_score: float = 0.3
    min_relevance_score: float = 0.3

    # Parallel query settings
    enable_parallel: bool = True

    # Source priorities (higher = more priority)
    source_priorities: Dict[ResultSource, float] = field(
        default_factory=lambda: {
            ResultSource.LINGFLOW: 1.0,
            ResultSource.LINGTONGASK: 1.0,
            ResultSource.LINGCLAUDE: 0.9,
            ResultSource.LINGYI: 0.8,
            ResultSource.RESEARCH: 0.7,
            ResultSource.EXTERNAL_INTELLIGENCE: 0.6,
            ResultSource.MEMORY: 0.5,
        }
    )


@dataclass
class FederationStats:
    """Statistics for federation operations"""

    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    total_results: int = 0
    average_query_time_ms: float = 0.0
    sources_used: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_queries": self.total_queries,
            "successful_queries": self.successful_queries,
            "failed_queries": self.failed_queries,
            "total_results": self.total_results,
            "average_query_time_ms": self.average_query_time_ms,
            "sources_used": list(self.sources_used),
        }


class KnowledgeFederation:
    """
    Cross-project knowledge federation.

    Coordinates queries across multiple knowledge sources and
    merges results according to quality and relevance scores.
    """

    def __init__(
        self,
        config: Optional[FederationConfig] = None,
        project_root: Optional[Path] = None,
    ):
        self._config = config or FederationConfig()
        self._project_root = project_root or Path.cwd()
        self._sources: Dict[str, KnowledgeSource] = {}
        self._stats = FederationStats()
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Initialize all knowledge sources.

        Returns True if initialization was successful.
        """
        if self._initialized:
            return True

        # Create sources
        self._sources = {
            "lingflow": LingFlowKnowledgeSource(self._project_root),
            "lingtongask": LingTongAskKnowledgeSource(self._project_root),
            "external": ExternalIntelligenceSource(self._project_root),
        }

        # Initialize all sources
        init_tasks = [source.initialize() for source in self._sources.values()]
        results = await asyncio.gather(*init_tasks, return_exceptions=True)

        # Filter successful sources
        available_sources = {}
        for name, result in zip(self._sources.keys(), results):
            if result is True and not isinstance(result, Exception):
                available_sources[name] = self._sources[name]
                self._stats.sources_used.add(name)

        self._sources = available_sources
        self._initialized = True

        return len(self._sources) > 0

    async def query(self, query: KnowledgeQuery, context: Optional[SearchContext] = None) -> KnowledgeResult:
        """
        Execute a cross-source knowledge query.

        Args:
            query: The knowledge query to execute
            context: Optional search context

        Returns:
            A merged KnowledgeResult from all sources
        """
        # Initialize if needed
        if not self._initialized:
            await self.initialize()

        # Update stats
        self._stats.total_queries += 1

        # Create context if needed
        if context is None:
            context = SearchContext(timeout_seconds=self._config.query_timeout_seconds)

        # Select sources to query
        sources_to_query = [source for source in self._sources.values() if source.should_query(query)]

        if not sources_to_query:
            return KnowledgeResult(
                success=False,
                error_message="No available sources for this query",
            )

        # Query sources
        if self._config.enable_parallel:
            results = await self._query_parallel(sources_to_query, query, context)
        else:
            results = await self._query_sequential(sources_to_query, query, context)

        # Merge results
        merged = self._merge_results(results, query)

        # Update stats
        if merged.success:
            self._stats.successful_queries += 1
        else:
            self._stats.failed_queries += 1
        self._stats.total_results += merged.total_found

        return merged

    async def _query_parallel(
        self,
        sources: List[KnowledgeSource],
        query: KnowledgeQuery,
        context: SearchContext,
    ) -> List[SearchResult]:
        """Query multiple sources in parallel"""
        tasks = [self._query_single(source, query, context) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                final_results.append(SearchResult.error(source.name, str(result)))
            else:
                final_results.append(result)

        return final_results

    async def _query_sequential(
        self,
        sources: List[KnowledgeSource],
        query: KnowledgeQuery,
        context: SearchContext,
    ) -> List[SearchResult]:
        """Query multiple sources sequentially"""
        results = []

        for source in sources:
            if context.is_timeout():
                break

            result = await self._query_single(source, query, context)
            results.append(result)

        return results

    async def _query_single(
        self,
        source: KnowledgeSource,
        query: KnowledgeQuery,
        context: SearchContext,
    ) -> SearchResult:
        """Query a single source"""
        context.add_source(source.name)

        try:
            result = await source.search(query, context)
            return SearchResult.from_result(source.name, result)
        except Exception as e:
            return SearchResult.error(source.name, str(e))

    def _merge_results(
        self,
        results: List[SearchResult],
        query: KnowledgeQuery,
    ) -> KnowledgeResult:
        """Merge results from multiple sources"""
        merged = KnowledgeResult(
            sources_queried=[r.source_name for r in results],
            query_time_ms=sum(r.result.query_time_ms for r in results),
        )

        # Collect all items
        all_items: List[tuple[KnowledgeItem, float]] = []

        for search_result in results:
            if not search_result.success:
                continue

            for item in search_result.result.items:
                # Calculate priority score
                priority = self._config.source_priorities.get(item.source, 0.5)

                # Combined score: relevance * quality * priority
                combined_score = item.relevance_score * item.quality_score * priority

                all_items.append((item, combined_score))

        # Sort by combined score
        all_items.sort(key=lambda x: x[1], reverse=True)

        # Filter by thresholds
        for item, score in all_items:
            if (
                item.quality_score >= self._config.min_quality_score
                and item.relevance_score >= self._config.min_relevance_score
            ):
                merged.add_item(item)

        # Apply limits
        merged.total_found = len(merged.items)
        if merged.total_found > self._config.max_total_results:
            merged = merged.limit(self._config.max_total_results)

        merged.success = True

        return merged

    async def query_by_keywords(self, keywords: List[str], **kwargs) -> KnowledgeResult:
        """
        Convenience method: Query by keywords.

        Args:
            keywords: List of keywords to search for
            **kwargs: Additional query parameters

        Returns:
            A KnowledgeResult with matching items
        """
        query = KnowledgeQuery.from_keywords(keywords, **kwargs)
        return await self.query(query)

    async def query_by_context(self, context: str, **kwargs) -> KnowledgeResult:
        """
        Convenience method: Query by context text.

        Args:
            context: Context text to extract keywords from
            **kwargs: Additional query parameters

        Returns:
            A KnowledgeResult with matching items
        """
        query = KnowledgeQuery.from_context(context, **kwargs)
        return await self.query(query)

    def get_available_sources(self) -> List[str]:
        """Get list of available source names"""
        return list(self._sources.keys())

    async def get_source_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all sources"""
        stats = {}

        for name, source in self._sources.items():
            try:
                stats[name] = await source.get_stats()
            except Exception:
                stats[name] = {"error": "Failed to get stats"}

        return stats

    def get_stats(self) -> FederationStats:
        """Get federation statistics"""
        return self._stats

    def reset_stats(self) -> None:
        """Reset federation statistics"""
        self._stats = FederationStats()

    async def close(self) -> None:
        """Close all sources and release resources"""
        for source in self._sources.values():
            if hasattr(source, "close"):
                source.close()

        self._sources.clear()
        self._initialized = False
