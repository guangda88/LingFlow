"""
lingtongask Knowledge Source

Provides access to lingtongask project knowledge including:
- Content guidelines
- Project charter
- Qigong knowledge base
- Fan engagement data
"""

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from lingflow.knowledge.query import (
    KnowledgeItem,
    KnowledgeQuery,
    KnowledgeResult,
    ResultSource,
)
from lingflow.knowledge.sources.base import KnowledgeSource, SearchContext


class lingtongaskKnowledgeSource(KnowledgeSource):
    """
    Knowledge source for lingtongask project.

    Reads from:
    - PROJECT_CHARTER.md
    - docs/content_guidelines.md
    - ROADMAP.md
    - Content generation history
    """

    def __init__(self, project_root: Optional[Path] = None):
        super().__init__()
        # Default to lingtongask project location
        self._project_root = project_root or Path("/home/ai/lingtongask")
        self._charter_file = self._project_root / "PROJECT_CHARTER.md"
        self._roadmap_file = self._project_root / "ROADMAP.md"
        self._docs_dir = self._project_root / "docs"
        self._content_dir = self._project_root / "content"
        self._cache: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "lingtongask"

    @property
    def source_type(self) -> ResultSource:
        return ResultSource.LINGTONGASK

    @property
    def project(self) -> str:
        return "lingtongask"

    async def _on_initialize(self) -> bool:
        """Initialize the knowledge source"""
        # Check if project exists
        if not self._project_root.exists():
            return False

        # Load key documents
        await self._load_charter()
        await self._load_roadmap()

        return True

    async def _load_charter(self) -> None:
        """Load project charter"""
        if self._charter_file.exists():
            try:
                content = self._charter_file.read_text(encoding="utf-8")
                self._cache["charter"] = {
                    "content": content,
                    "loaded_at": datetime.now().isoformat(),
                }
            except Exception:
                pass

    async def _load_roadmap(self) -> None:
        """Load roadmap"""
        if self._roadmap_file.exists():
            try:
                content = self._roadmap_file.read_text(encoding="utf-8")
                self._cache["roadmap"] = {
                    "content": content,
                    "loaded_at": datetime.now().isoformat(),
                }
            except Exception:
                pass

    async def search(self, query: KnowledgeQuery, context: Optional[SearchContext] = None) -> KnowledgeResult:
        """Search lingtongask knowledge"""
        items: list[KnowledgeItem] = []

        # Search charter
        items.extend(await self._search_charter(query))

        # Search roadmap
        items.extend(await self._search_roadmap(query))

        # Search docs
        items.extend(await self._search_docs(query))

        # Search content
        items.extend(await self._search_content(query))

        # Build result
        result = KnowledgeResult(
            sources_queried=[self.name],
            query_time_ms=context.elapsed_ms if context else 0.0,
        )

        # Score and filter items
        for item in items:
            item = self._score_item(item, query)
            if item.relevance_score >= query.options.min_quality:
                result.add_item(item)

        result.total_found = len(result.items)
        result.sort_by_relevance()

        return result

    async def _search_charter(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search project charter"""
        items: list[KnowledgeItem] = []

        charter = self._cache.get("charter", {})
        content = charter.get("content", "")
        if not content:
            return items

        score = self._calculate_relevance(content, query.keywords)
        if score < query.options.min_quality:
            return items

        # Extract sections
        sections = self._parse_sections(content)
        for title, section_content in sections.items():
            section_score = self._calculate_relevance(section_content, query.keywords)
            if section_score >= query.options.min_quality:
                item = KnowledgeItem(
                    title=f"Charter: {title}",
                    content=section_content,
                    summary=section_content[:200] + "..." if len(section_content) > 200 else section_content,
                    category="charter",
                    quality_score=0.9,
                    relevance_score=section_score,
                    source=self.source_type,
                    project=self.project,
                    tags={"charter", "project-knowledge", "lingtongask"},
                )
                items.append(item)

        return items

    async def _search_roadmap(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search roadmap"""
        items: list[KnowledgeItem] = []

        roadmap = self._cache.get("roadmap", {})
        content = roadmap.get("content", "")
        if not content:
            return items

        score = self._calculate_relevance(content, query.keywords)
        if score < query.options.min_quality:
            return items

        sections = self._parse_sections(content)
        for title, section_content in sections.items():
            section_score = self._calculate_relevance(section_content, query.keywords)
            if section_score >= query.options.min_quality:
                item = KnowledgeItem(
                    title=f"Roadmap: {title}",
                    content=section_content,
                    summary=section_content[:200] + "..." if len(section_content) > 200 else section_content,
                    category="roadmap",
                    quality_score=0.8,
                    relevance_score=section_score,
                    source=self.source_type,
                    project=self.project,
                    tags={"roadmap", "planning", "lingtongask"},
                )
                items.append(item)

        return items

    async def _search_docs(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search documentation"""
        items: list[KnowledgeItem] = []

        if not self._docs_dir.exists():
            return items

        for doc_file in self._docs_dir.glob("*.md"):
            try:
                content = doc_file.read_text(encoding="utf-8")
                score = self._calculate_relevance(content, query.keywords)

                if score >= query.options.min_quality:
                    title = doc_file.stem.replace("_", " ").title()

                    item = KnowledgeItem(
                        title=f"Doc: {title}",
                        content=content,
                        summary=content[:300] + "..." if len(content) > 300 else content,
                        category="documentation",
                        quality_score=0.7,
                        relevance_score=score,
                        source=self.source_type,
                        project=self.project,
                        tags={"documentation", "lingtongask"},
                        metadata={"file_path": str(doc_file)},
                    )
                    items.append(item)

            except Exception:
                pass

        return items

    async def _search_content(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search generated content"""
        items: list[KnowledgeItem] = []

        if not self._content_dir.exists():
            return items

        for content_file in self._content_dir.glob("**/*.md"):
            try:
                content = content_file.read_text(encoding="utf-8")
                score = self._calculate_relevance(content, query.keywords)

                if score >= query.options.min_quality:
                    title = content_file.stem

                    item = KnowledgeItem(
                        title=f"Content: {title}",
                        content=content,
                        summary=content[:300] + "..." if len(content) > 300 else content,
                        category="content",
                        quality_score=0.6,
                        relevance_score=score,
                        source=self.source_type,
                        project=self.project,
                        tags={"content", "qigong", "generated"},
                        metadata={"file_path": str(content_file)},
                    )
                    items.append(item)

            except Exception:
                pass

        return items

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown sections"""
        sections = {}
        current_section = "Overview"
        current_content: list[str] = []

        for line in content.split("\n"):
            if line.startswith("## "):
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip()
                current_content: list[str] = []
            elif line.startswith("# "):
                continue  # Skip title
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _score_item(self, item: KnowledgeItem, query: KnowledgeQuery) -> KnowledgeItem:
        """Score an item's relevance"""
        score = self._calculate_relevance(f"{item.title} {item.content}", query.keywords)
        return replace(item, relevance_score=score)

    def _calculate_relevance(self, text: str, keywords: List[str]) -> float:
        """Calculate relevance score"""
        if not keywords:
            return 0.5

        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        return matches / len(keywords)

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        stats = await super().get_stats()

        doc_count = 0
        if self._docs_dir.exists():
            doc_count = len(list(self._docs_dir.glob("*.md")))

        content_count = 0
        if self._content_dir.exists():
            content_count = len(list(self._content_dir.glob("**/*.md")))

        stats.update(
            {
                "doc_count": doc_count,
                "content_count": content_count,
                "charter_available": "charter" in self._cache,
                "roadmap_available": "roadmap" in self._cache,
            }
        )

        return stats

    async def get_categories(self) -> List[str]:
        """Get available categories"""
        return ["charter", "roadmap", "documentation", "content", "general"]
