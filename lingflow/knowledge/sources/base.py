"""
Base Knowledge Source

Defines the abstract interface that all knowledge sources must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from lingflow.knowledge.query import KnowledgeQuery, KnowledgeResult, ResultSource


@dataclass
class SearchContext:
    """Context for a search operation"""

    query_id: str = field(default_factory=lambda: uuid4().hex)
    start_time: datetime = field(default_factory=datetime.now)
    timeout_seconds: Optional[float] = None

    # Tracking
    sources_contacted: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def elapsed_ms(self) -> float:
        """Elapsed time in milliseconds"""
        return (datetime.now() - self.start_time).total_seconds() * 1000

    def is_timeout(self) -> bool:
        """Check if timeout has been exceeded"""
        if self.timeout_seconds is None:
            return False
        return self.elapsed_ms / 1000 > self.timeout_seconds

    def add_source(self, source: str) -> None:
        """Add a contacted source"""
        if source not in self.sources_contacted:
            self.sources_contacted.append(source)

    def add_error(self, error: str) -> None:
        """Add an error"""
        self.errors.append(error)


@dataclass
class SearchResult:
    """Result from a single knowledge source"""

    source_name: str
    result: KnowledgeResult
    success: bool = True
    error_message: Optional[str] = None

    @classmethod
    def from_result(cls, source_name: str, result: KnowledgeResult) -> "SearchResult":
        """Create from a KnowledgeResult"""
        return cls(
            source_name=source_name,
            result=result,
            success=result.success,
            error_message=result.error_message,
        )

    @classmethod
    def error(cls, source_name: str, error_message: str) -> "SearchResult":
        """Create an error result"""
        return cls(
            source_name=source_name,
            result=KnowledgeResult(success=False, error_message=error_message),
            success=False,
            error_message=error_message,
        )


class KnowledgeSource(ABC):
    """
    Abstract base class for all knowledge sources.

    All knowledge sources must implement the search method and
    provide metadata about themselves.
    """

    def __init__(self):
        self._initialized = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the source"""
        pass

    @property
    @abstractmethod
    def source_type(self) -> ResultSource:
        """Type identifier of the source"""
        pass

    @property
    @abstractmethod
    def project(self) -> str:
        """Project identifier (e.g., 'lingflow', 'lingtongask')"""
        pass

    @property
    def is_available(self) -> bool:
        """Check if the source is available"""
        return self._initialized

    @property
    def description(self) -> str:
        """Description of the source"""
        return f"{self.name} ({self.project})"

    async def initialize(self) -> bool:
        """
        Initialize the knowledge source.

        Returns True if initialization was successful.
        """
        self._initialized = await self._on_initialize()
        return self._initialized

    async def _on_initialize(self) -> bool:
        """
        Override this method to perform source-specific initialization.

        Default implementation always returns True.
        """
        return True

    @abstractmethod
    async def search(self, query: KnowledgeQuery, context: Optional[SearchContext] = None) -> KnowledgeResult:
        """
        Search the knowledge source for relevant items.

        Args:
            query: The knowledge query to execute
            context: Optional search context for tracking

        Returns:
            A KnowledgeResult containing matching items
        """
        pass

    async def get_categories(self) -> List[str]:
        """
        Get available categories in this source.

        Returns a list of category identifiers.
        """
        return []

    async def get_tags(self) -> List[str]:
        """
        Get available tags in this source.

        Returns a list of tag identifiers.
        """
        return []

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about this knowledge source.

        Returns a dictionary with source-specific statistics.
        """
        return {
            "name": self.name,
            "source_type": self.source_type.value,
            "project": self.project,
            "available": self.is_available,
        }

    def should_query(self, query: KnowledgeQuery) -> bool:
        """
        Check if this source should be queried for the given query.

        Considers project and source filters in the query.
        """
        # Check source filter
        if query.sources and self.source_type not in query.sources:
            return False

        # Check project filter
        if query.projects and not query.should_search_project(self.project):
            return False

        return True

    def _build_result(self, query: KnowledgeQuery, items: List, context: Optional[SearchContext] = None) -> KnowledgeResult:
        """Build a KnowledgeResult from items"""
        result = KnowledgeResult(
            sources_queried=[self.name],
            query_time_ms=context.elapsed_ms if context else 0.0,
        )

        # Apply quality filter
        min_quality = query.options.min_quality
        for item in items:
            if hasattr(item, "quality_score") and item.quality_score >= min_quality:
                result.add_item(item)

        result.total_found = len(result.items)

        # Apply limit
        if result.total_found > query.options.max_results:
            result = result.limit(query.options.max_results)

        return result
