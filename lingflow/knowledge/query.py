"""
Knowledge Query Models

Defines the unified query interface and result structures
for the knowledge federation system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4


class ResultSource(Enum):
    """Knowledge source identifiers"""

    LINGFLOW = "lingflow"
    LINGTONGASK = "lingtongask"
    LINGCLAUDE = "lingclaude"
    LINGYI = "lingyi"
    EXTERNAL_INTELLIGENCE = "external_intelligence"
    RESEARCH = "research"
    MEMORY = "memory"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class QueryOptions:
    """Options for knowledge queries"""

    min_quality: float = 0.5
    max_results: int = 20
    include_metadata: bool = True
    include_source: bool = True
    fuzzy_match: bool = True
    case_sensitive: bool = False
    timeout_seconds: Optional[float] = 30.0


@dataclass(frozen=True)
class KnowledgeItem:
    """A single knowledge item"""

    id: str = field(default_factory=lambda: uuid4().hex)
    title: str = ""
    content: str = ""
    summary: Optional[str] = None
    category: str = "general"

    # Quality metrics
    quality_score: float = 0.5
    relevance_score: float = 0.5

    # Metadata
    source: ResultSource = ResultSource.UNKNOWN
    project: str = ""
    tags: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # References
    references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "category": self.category,
            "quality_score": self.quality_score,
            "relevance_score": self.relevance_score,
            "source": self.source.value,
            "project": self.project,
            "tags": list(self.tags),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
            "references": self.references,
        }


@dataclass
class KnowledgeResult:
    """Result from a knowledge query"""

    query_id: str = field(default_factory=lambda: uuid4().hex)
    items: List[KnowledgeItem] = field(default_factory=list)

    # Query metadata
    sources_queried: List[str] = field(default_factory=list)
    total_found: int = 0
    query_time_ms: float = 0.0

    # Status
    success: bool = True
    error_message: Optional[str] = None

    def add_item(self, item: KnowledgeItem) -> None:
        """Add an item to the result"""
        self.items.append(item)

    def sort_by_relevance(self) -> None:
        """Sort items by relevance score"""
        self.items.sort(key=lambda x: x.relevance_score, reverse=True)

    def sort_by_quality(self) -> None:
        """Sort items by quality score"""
        self.items.sort(key=lambda x: x.quality_score, reverse=True)

    def filter_by_quality(self, min_quality: float) -> "KnowledgeResult":
        """Filter items by minimum quality"""
        filtered = KnowledgeResult(
            query_id=self.query_id,
            sources_queried=self.sources_queried.copy(),
            total_found=0,
            query_time_ms=self.query_time_ms,
            success=self.success,
            error_message=self.error_message,
        )
        for item in self.items:
            if item.quality_score >= min_quality:
                filtered.add_item(item)
        filtered.total_found = len(filtered.items)
        return filtered

    def limit(self, max_items: int) -> "KnowledgeResult":
        """Limit the number of results"""
        limited = KnowledgeResult(
            query_id=self.query_id,
            items=self.items[:max_items],
            sources_queried=self.sources_queried.copy(),
            total_found=min(self.total_found, max_items),
            query_time_ms=self.query_time_ms,
            success=self.success,
            error_message=self.error_message,
        )
        return limited

    def merge(self, other: "KnowledgeResult") -> "KnowledgeResult":
        """Merge another result into this one"""
        merged = KnowledgeResult(
            query_id=self.query_id,
            items=self.items.copy(),
            sources_queried=list(set(self.sources_queried + other.sources_queried)),
            total_found=self.total_found + other.total_found,
            query_time_ms=max(self.query_time_ms, other.query_time_ms),
            success=self.success and other.success,
            error_message=self.error_message or other.error_message,
        )
        merged.items.extend(other.items)
        return merged

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query_id": self.query_id,
            "items": [item.to_dict() for item in self.items],
            "sources_queried": self.sources_queried,
            "total_found": self.total_found,
            "query_time_ms": self.query_time_ms,
            "success": self.success,
            "error_message": self.error_message,
        }


@dataclass
class KnowledgeQuery:
    """Unified knowledge query"""

    keywords: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)

    # Query options
    options: QueryOptions = field(default_factory=QueryOptions)

    # Query context
    context: Optional[str] = None
    user_intent: Optional[str] = None

    # Filters
    sources: List[ResultSource] = field(default_factory=list)
    date_range: Optional[tuple[datetime, datetime]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "keywords": self.keywords,
            "categories": self.categories,
            "projects": self.projects,
            "tags": list(self.tags),
            "context": self.context,
            "user_intent": self.user_intent,
            "sources": [s.value for s in self.sources],
            "min_quality": self.options.min_quality,
            "max_results": self.options.max_results,
        }

    def matches_source(self, source: ResultSource) -> bool:
        """Check if a source should be queried"""
        if not self.sources:
            return True
        return source in self.sources

    def should_search_project(self, project: str) -> bool:
        """Check if a project should be searched"""
        if not self.projects:
            return True
        return project in self.projects or "all" in self.projects

    @classmethod
    def from_keywords(cls, keywords: List[str], **kwargs) -> "KnowledgeQuery":
        """Create a query from keywords"""
        return cls(keywords=keywords, **kwargs)

    @classmethod
    def from_context(cls, context: str, **kwargs) -> "KnowledgeQuery":
        """Create a query from context text"""
        # Simple keyword extraction
        words = context.lower().split()
        keywords = [w for w in words if len(w) > 3]
        return cls(keywords=keywords, context=context, **kwargs)
