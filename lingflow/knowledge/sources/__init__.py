"""
Knowledge Sources Module

This module provides the base class and implementations
for various knowledge sources in the federation.
"""

from lingflow.knowledge.sources.base import (
    KnowledgeSource,
    SearchContext,
    SearchResult
)

from lingflow.knowledge.sources.lingflow import LingFlowKnowledgeSource

from lingflow.knowledge.sources.lingtongask import LingTongAskKnowledgeSource

from lingflow.knowledge.sources.external import ExternalIntelligenceSource

__all__ = [
    "KnowledgeSource",
    "SearchContext",
    "SearchResult",
    "LingFlowKnowledgeSource",
    "LingTongAskKnowledgeSource",
    "ExternalIntelligenceSource",
]
