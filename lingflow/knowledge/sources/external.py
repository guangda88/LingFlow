"""
External Intelligence Source

Provides access to external intelligence including:
- GitHub trends
- NPM trends
- Competitive analysis
- Research reports
"""

import json
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


class ExternalIntelligenceSource(KnowledgeSource):
    """
    Knowledge source for external intelligence.

    Reads from:
    - .lingflow/reports/github_trends/
    - .lingflow/reports/npm_trends/
    - .lingflow/reports/research/
    - .lingflow/reports/competitive/
    """

    def __init__(self, project_root: Optional[Path] = None):
        super().__init__()
        self._project_root = project_root or Path.cwd()
        self._reports_dir = self._project_root / ".lingflow" / "reports"
        self._github_dir = self._reports_dir / "github_trends"
        self._npm_dir = self._reports_dir / "npm_trends"
        self._research_dir = self._reports_dir / "research"
        self._competitive_dir = self._reports_dir / "competitive"
        self._cache: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "ExternalIntelligence"

    @property
    def source_type(self) -> ResultSource:
        return ResultSource.EXTERNAL_INTELLIGENCE

    @property
    def project(self) -> str:
        return "external"

    async def _on_initialize(self) -> bool:
        """Initialize the knowledge source"""
        if not self._reports_dir.exists():
            return False

        # Load recent intelligence reports
        await self._load_github_trends()
        await self._load_npm_trends()
        await self._load_research()

        return True

    async def _load_github_trends(self) -> None:
        """Load GitHub trend reports"""
        self._cache["github"] = []

        if not self._github_dir.exists():
            return

        for report_file in sorted(self._github_dir.glob("*.json"), reverse=True)[:10]:
            try:
                content = report_file.read_text(encoding="utf-8")
                data = json.loads(content)
                self._cache["github"].append({
                    "file": report_file.name,
                    "data": data,
                    "loaded_at": datetime.now().isoformat(),
                })
            except (json.JSONDecodeError, Exception):
                pass

    async def _load_npm_trends(self) -> None:
        """Load NPM trend reports"""
        self._cache["npm"] = []

        if not self._npm_dir.exists():
            return

        for report_file in sorted(self._npm_dir.glob("*.json"), reverse=True)[:10]:
            try:
                content = report_file.read_text(encoding="utf-8")
                data = json.loads(content)
                self._cache["npm"].append({
                    "file": report_file.name,
                    "data": data,
                    "loaded_at": datetime.now().isoformat(),
                })
            except (json.JSONDecodeError, Exception):
                pass

    async def _load_research(self) -> None:
        """Load research reports"""
        self._cache["research"] = []

        if not self._research_dir.exists():
            return

        for report_file in sorted(self._research_dir.glob("*.md"), reverse=True)[:20]:
            try:
                content = report_file.read_text(encoding="utf-8")
                self._cache["research"].append({
                    "file": report_file.name,
                    "content": content,
                    "loaded_at": datetime.now().isoformat(),
                })
            except Exception:
                pass

    async def search(
        self,
        query: KnowledgeQuery,
        context: Optional[SearchContext] = None
    ) -> KnowledgeResult:
        """Search external intelligence"""
        items = []

        # Search GitHub trends
        items.extend(await self._search_github(query))

        # Search NPM trends
        items.extend(await self._search_npm(query))

        # Search research reports
        items.extend(await self._search_reports(query))

        # Search competitive analysis
        items.extend(await self._search_competitive(query))

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

    async def _search_github(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search GitHub trends"""
        items = []

        for report in self._cache.get("github", []):
            data = report["data"]
            repos = data.get("repos", [])

            for repo in repos:
                # Check relevance
                text = f"{repo.get('name', '')} {repo.get('description', '')}"
                score = self._calculate_relevance(text, query.keywords)

                if score >= query.options.min_quality:
                    item = KnowledgeItem(
                        title=f"GitHub: {repo.get('name', 'Unknown')}",
                        content=repo.get("description", ""),
                        summary=repo.get("description", ""),
                        category="github_trend",
                        quality_score=repo.get("relevance_score", 0.5) / 100,
                        relevance_score=score,
                        source=self.source_type,
                        project=self.project,
                        tags={"github", "trend", "repository"},
                        metadata={
                            "stars": repo.get("stars", 0),
                            "url": repo.get("url", ""),
                            "language": repo.get("language", ""),
                            "relevance_score": repo.get("relevance_score", 0),
                        },
                        references=[repo.get("url", "")] if repo.get("url") else [],
                    )
                    items.append(item)

        return items

    async def _search_npm(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search NPM trends"""
        items = []

        for report in self._cache.get("npm", []):
            data = report["data"]
            packages = data.get("packages", [])

            for pkg in packages:
                text = f"{pkg.get('name', '')} {pkg.get('description', '')}"
                score = self._calculate_relevance(text, query.keywords)

                if score >= query.options.min_quality:
                    item = KnowledgeItem(
                        title=f"NPM: {pkg.get('name', 'Unknown')}",
                        content=pkg.get("description", ""),
                        summary=pkg.get("description", ""),
                        category="npm_trend",
                        quality_score=pkg.get("relevance_score", 0.5) / 100,
                        relevance_score=score,
                        source=self.source_type,
                        project=self.project,
                        tags={"npm", "trend", "package"},
                        metadata={
                            "downloads": pkg.get("downloads", 0),
                            "url": pkg.get("url", ""),
                            "version": pkg.get("version", ""),
                        },
                        references=[pkg.get("url", "")] if pkg.get("url") else [],
                    )
                    items.append(item)

        return items

    async def _search_reports(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search research reports"""
        items = []

        for report in self._cache.get("research", []):
            content = report["content"]
            score = self._calculate_relevance(content, query.keywords)

            if score >= query.options.min_quality:
                # Extract title
                title = report["file"].replace(".md", "").replace("_", " ").title()

                item = KnowledgeItem(
                    title=f"Research: {title}",
                    content=content,
                    summary=content[:300] + "..." if len(content) > 300 else content,
                    category="research",
                    quality_score=0.8,
                    relevance_score=score,
                    source=self.source_type,
                    project=self.project,
                    tags={"research", "report"},
                    metadata={"file": report["file"]},
                )
                items.append(item)

        return items

    async def _search_competitive(self, query: KnowledgeQuery) -> List[KnowledgeItem]:
        """Search competitive analysis"""
        items = []

        if not self._competitive_dir.exists():
            return items

        for report_file in self._competitive_dir.glob("*.md"):
            try:
                content = report_file.read_text(encoding="utf-8")
                score = self._calculate_relevance(content, query.keywords)

                if score >= query.options.min_quality:
                    title = report_file.stem.replace("_", " ").title()

                    item = KnowledgeItem(
                        title=f"Competitive: {title}",
                        content=content,
                        summary=content[:300] + "..." if len(content) > 300 else content,
                        category="competitive",
                        quality_score=0.7,
                        relevance_score=score,
                        source=self.source_type,
                        project=self.project,
                        tags={"competitive", "analysis"},
                        metadata={"file_path": str(report_file)},
                    )
                    items.append(item)

            except Exception:
                pass

        return items

    def _score_item(self, item: KnowledgeItem, query: KnowledgeQuery) -> KnowledgeItem:
        """Score an item's relevance"""
        score = self._calculate_relevance(
            f"{item.title} {item.content}",
            query.keywords
        )
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

        stats.update({
            "github_reports": len(self._cache.get("github", [])),
            "npm_reports": len(self._cache.get("npm", [])),
            "research_reports": len(self._cache.get("research", [])),
            "github_dir_exists": self._github_dir.exists(),
            "npm_dir_exists": self._npm_dir.exists(),
            "research_dir_exists": self._research_dir.exists(),
        })

        return stats

    async def get_categories(self) -> List[str]:
        """Get available categories"""
        return ["github_trend", "npm_trend", "research", "competitive", "general"]
