#!/usr/bin/env python3
"""
Knowledge Federation Usage Example

Demonstrates how to use the KnowledgeFederation to query
across multiple knowledge sources.
"""

import asyncio

from lingflow.knowledge import (
    KnowledgeFederation,
    KnowledgeQuery,
    FederationConfig,
)


async def main():
    """Main example function"""

    print("=" * 60)
    print("Knowledge Federation Example")
    print("=" * 60)

    # 1. Create federation with custom config
    config = FederationConfig(
        query_timeout_seconds=10.0,
        max_results_per_source=10,
        max_total_results=30,
        min_quality_score=0.4,
        enable_parallel=True,
    )

    federation = KnowledgeFederation(config=config)

    # 2. Initialize
    print("\n[1] Initializing knowledge federation...")
    await federation.initialize()

    sources = federation.get_available_sources()
    print(f"    Available sources: {', '.join(sources)}")

    # 3. Get source statistics
    print("\n[2] Source statistics:")
    stats = await federation.get_source_stats()
    for name, stat in stats.items():
        print(f"    {name}:")
        for key, value in stat.items():
            print(f"      - {key}: {value}")

    # 4. Query by keywords
    print("\n[3] Querying by keywords: 'session', 'workflow'")
    result = await federation.query_by_keywords(
        keywords=["session", "workflow"],
        options=KnowledgeQuery.Options(
            min_quality=0.3,
            max_results=10,
        )
    )

    print(f"    Sources queried: {', '.join(result.sources_queried)}")
    print(f"    Total found: {result.total_found}")
    print(f"    Query time: {result.query_time_ms:.0f}ms")

    if result.items:
        print("\n    Top results:")
        for i, item in enumerate(result.items[:3], 1):
            print(f"      {i}. [{item.source.value}] {item.title}")
            print(f"         Quality: {item.quality_score:.2f}, Relevance: {item.relevance_score:.2f}")

    # 5. Query by context
    print("\n[4] Querying by context text...")
    context = "How does the session management work in lingflow?"
    result = await federation.query_by_context(
        context=context,
        options=KnowledgeQuery.Options(
            min_quality=0.2,
            max_results=5,
        )
    )

    print(f"    Context: {context}")
    print(f"    Results found: {result.total_found}")

    # 6. Query with filters
    print("\n[5] Querying with project filter...")
    query = KnowledgeQuery(
        keywords=["agent"],
        projects=["lingflow"],
        options=KnowledgeQuery.Options(
            min_quality=0.3,
            max_results=5,
        )
    )

    result = await federation.query(query)
    print("    Project filter: lingflow")
    print(f"    Results found: {result.total_found}")

    # 7. Get federation statistics
    print("\n[6] Federation statistics:")
    fed_stats = federation.get_stats()
    stats_dict = fed_stats.to_dict()
    for key, value in stats_dict.items():
        print(f"    {key}: {value}")

    # 8. Demonstrate knowledge synchronization
    print("\n[7] Knowledge synchronization:")
    from lingflow.knowledge.sync import KnowledgeSync

    sync = KnowledgeSync()

    # Sync from memory
    print("    Syncing from project memory...")
    mem_result = await sync.sync_from_memory()
    print(f"      Items added: {mem_result.items_added}")

    # Sync from research
    print("    Syncing from research reports...")
    res_result = await sync.sync_from_research()
    print(f"      Items added: {res_result.items_added}")

    # Sync stats
    sync_stats = sync.get_stats()
    print(f"    Total syncs: {sync_stats.total_syncs}")
    print(f"    Total items synced: {sync_stats.total_items_synced}")

    # 9. Close
    print("\n[8] Closing federation...")
    await federation.close()

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


class QueryOptions:
    """Helper for query options"""
    def __init__(self, min_quality=0.5, max_results=20, include_metadata=True,
                 include_source=True, fuzzy_match=True, case_sensitive=False,
                 timeout_seconds=30.0):
        from lingflow.knowledge.query import QueryOptions as QO
        self._options = QO(
            min_quality=min_quality,
            max_results=max_results,
            include_metadata=include_metadata,
            include_source=include_source,
            fuzzy_match=fuzzy_match,
            case_sensitive=case_sensitive,
            timeout_seconds=timeout_seconds,
        )


# Patch KnowledgeQuery to use the helper
KnowledgeQuery.Options = QueryOptions


if __name__ == "__main__":
    asyncio.run(main())
