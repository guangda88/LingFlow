"""
LingFlow Knowledge Federation Module

This module implements a cross-project knowledge federation system
that enables unified querying across multiple knowledge sources.

Architecture:
    - KnowledgeQuery: Unified query interface
    - KnowledgeSource: Base class for all knowledge sources
    - KnowledgeFederation: Cross-source query coordinator
    - KnowledgeSync: Synchronization mechanisms

Example:
    >>> from lingflow.knowledge import KnowledgeFederation, KnowledgeQuery
    >>> federation = KnowledgeFederation()
    >>> query = KnowledgeQuery(keywords=["agent", "workflow"])
    >>> results = await federation.query(query)
"""

from lingflow.knowledge.query import (
    KnowledgeQuery,
    KnowledgeResult,
    KnowledgeItem,
    QueryOptions,
    ResultSource
)

from lingflow.knowledge.federation import (
    KnowledgeFederation,
    FederationConfig
)

from lingflow.knowledge.sync import (
    KnowledgeSync,
    SyncResult,
    SyncStats
)

__all__ = [
    # Query models
    "KnowledgeQuery",
    "KnowledgeResult",
    "KnowledgeItem",
    "QueryOptions",
    "ResultSource",
    # Federation
    "KnowledgeFederation",
    "FederationConfig",
    # Sync
    "KnowledgeSync",
    "SyncResult",
    "SyncStats",
]

__version__ = "1.0.0"
