"""
LingFlow Knowledge Source

Provides access to LingFlow's internal knowledge including:
- Project memory (MEMORY.md)
- Architecture decisions
- Design patterns
- Code conventions
"""

import json
import sqlite3
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


class LingFlowKnowledgeSource(KnowledgeSource):
    """
    Knowledge source for LingFlow project.

    Reads from:
    - .lingflow/knowledge.db (SQLite knowledge base)
    - memory/MEMORY.md (project memory)
    - .lingflow/reports/ (research reports)
    """

    def __init__(self, project_root: Optional[Path] = None):
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._knowledge_db = self._project_root / ".lingflow" / "knowledge.db"
        self._memory_file = self._project_root / ".claude" / "projects" / "-home-ai-LingFlow" / "memory" / "MEMORY.md"
        self._reports_dir = self._project_root / ".lingflow" / "reports"
        self._conn: Optional[sqlite3.Connection] = None
        self._memory_cache: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "LingFlow"

    @property
    def source_type(self) -> ResultSource:
        return ResultSource.LINGFLOW

    @property
    def project(self) -> str:
        return "lingflow"

    async def _on_initialize(self) -> bool:
        """Initialize the knowledge source"""
        # Try to connect to knowledge database
        if self._knowledge_db.exists():
            try:
                self._conn = sqlite3.connect(str(self._knowledge_db))
                self._conn.row_factory = sqlite3.Row
            except sqlite3.Error:
                pass

        # Load memory cache
        await self._load_memory()

        return True

    async def _load_memory(self) -> None:
        """Load project memory into cache"""
        if not self._memory_file.exists():
            return

        try:
            content = self._memory_file.read_text(encoding="utf-8")
            self._memory_cache = {
                "raw_content": content,
                "last_updated": datetime.now().isoformat(),
            }
        except Exception:
            pass

    async def search(
        self,
        query: KnowledgeQuery,
        context: Optional[SearchContext] = None
    ) -> KnowledgeResult:
        """Search LingFlow knowledge"""
        items = []

        # Search in database if available
        if self._conn:
            items.extend(await self._search_database(query))

        # Search in memory
        items.extend(await self._search_memory(query))

        # Search in reports
        items.extend(await self._search_reports(query))

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

    async def _search_database(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search the knowledge database"""
        items = []

        if not self._conn:
            return items

        try:
            cursor = self._conn.cursor()

            # Build search query
            sql = """
                SELECT id, title, content, category, quality_score,
                       tags, metadata, created_at, updated_at
                FROM knowledge_items
                WHERE 1=1
            """
            params = []

            # Add keyword filter
            if query.keywords:
                keyword_conditions = []
                for keyword in query.keywords:
                    keyword_conditions.append("(title LIKE ? OR content LIKE ?)")
                    params.extend([f"%{keyword}%", f"%{keyword}%"])
                sql += " AND (" + " OR ".join(keyword_conditions) + ")"

            # Add category filter
            if query.categories:
                placeholders = ",".join("?" * len(query.categories))
                sql += f" AND category IN ({placeholders})"
                params.extend(query.categories)

            # Add quality filter
            sql += " AND quality_score >= ?"
            params.append(query.options.min_quality)

            # Add limit
            sql += " LIMIT ?"
            params.append(query.options.max_results)

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            for row in rows:
                tags = set(json.loads(row["tags"]) if row["tags"] else "[]")
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}

                item = KnowledgeItem(
                    id=row["id"],
                    title=row["title"],
                    content=row["content"],
                    category=row["category"],
                    quality_score=row["quality_score"],
                    source=self.source_type,
                    project=self.project,
                    tags=tags,
                    metadata=metadata,
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
                )
                items.append(item)

        except sqlite3.Error:
            pass

        return items

    async def _search_memory(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search project memory"""
        items = []

        if not self._memory_cache.get("raw_content"):
            return items

        content = self._memory_cache["raw_content"]
        sections = self._parse_memory_sections(content)

        for section_title, section_content in sections.items():
            # Check relevance
            score = self._calculate_relevance(section_content, query.keywords)
            if score < query.options.min_quality:
                continue

            # Extract summary
            summary = section_content[:200] + "..." if len(section_content) > 200 else section_content

            item = KnowledgeItem(
                title=f"Memory: {section_title}",
                content=section_content,
                summary=summary,
                category="memory",
                quality_score=0.8,
                relevance_score=score,
                source=self.source_type,
                project=self.project,
                tags={"memory", "project-knowledge"},
            )
            items.append(item)

        return items

    def _parse_memory_sections(self, content: str) -> Dict[str, str]:
        """Parse memory file into sections"""
        sections = {}
        current_section = "General"
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content)

                # Start new section
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = "\n".join(current_content)

        return sections

    async def _search_reports(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search research reports"""
        items = []

        if not self._reports_dir.exists():
            return items

        # Search markdown reports
        for report_file in self._reports_dir.glob("*.md"):
            try:
                content = report_file.read_text(encoding="utf-8")

                # Check relevance
                score = self._calculate_relevance(content, query.keywords)
                if score < query.options.min_quality:
                    continue

                # Extract title from first heading
                title = report_file.stem
                for line in content.split("\n")[:10]:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                item = KnowledgeItem(
                    title=f"Report: {title}",
                    content=content,
                    summary=content[:300] + "..." if len(content) > 300 else content,
                    category="report",
                    quality_score=0.7,
                    relevance_score=score,
                    source=self.source_type,
                    project=self.project,
                    tags={"report", "research"},
                    metadata={"file_path": str(report_file)},
                    references=[str(report_file)],
                )
                items.append(item)

            except Exception:
                pass

        return items

    def _score_item(self, item: KnowledgeItem, query: KnowledgeQuery) -> KnowledgeItem:
        """Score an item's relevance to the query"""
        score = self._calculate_relevance(
            f"{item.title} {item.content}",
            query.keywords
        )
        return replace(item, relevance_score=score)

    def _calculate_relevance(self, text: str, keywords: List[str]) -> float:
        """Calculate relevance score based on keyword matches"""
        if not keywords:
            return 0.5

        text_lower = text.lower()
        matches = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches += 1

        return matches / len(keywords)

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about this source"""
        stats = await super().get_stats()

        # Count database items
        db_count = 0
        if self._conn:
            try:
                cursor = self._conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM knowledge_items")
                row = cursor.fetchone()
                db_count = row["count"] if row else 0
            except sqlite3.Error:
                pass

        # Count reports
        report_count = 0
        if self._reports_dir.exists():
            report_count = len(list(self._reports_dir.glob("*.md")))

        stats.update({
            "database_items": db_count,
            "report_count": report_count,
            "memory_available": bool(self._memory_cache),
        })

        return stats

    async def get_categories(self) -> List[str]:
        """Get available categories"""
        categories = ["memory", "report", "general"]

        if self._conn:
            try:
                cursor = self._conn.cursor()
                cursor.execute("SELECT DISTINCT category FROM knowledge_items")
                categories.extend([row["category"] for row in cursor.fetchall()])
            except sqlite3.Error:
                pass

        return list(set(categories))

    def close(self) -> None:
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None
