"""
Knowledge Synchronization

Implements synchronization mechanisms to keep the knowledge
federation up-to-date with various sources.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from lingflow.knowledge.query import KnowledgeItem, ResultSource


@dataclass
class SyncResult:
    """Result of a synchronization operation"""

    sync_id: str = field(default_factory=lambda: uuid4().hex)
    source: str = ""
    items_added: int = 0
    items_updated: int = 0
    items_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    @property
    def duration_ms(self) -> float:
        if not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds() * 1000

    @property
    def total_items(self) -> int:
        return self.items_added + self.items_updated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sync_id": self.sync_id,
            "source": self.source,
            "items_added": self.items_added,
            "items_updated": self.items_updated,
            "items_skipped": self.items_skipped,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
        }


@dataclass
class SyncStats:
    """Aggregated synchronization statistics"""

    total_syncs: int = 0
    last_sync_time: Optional[datetime] = None
    total_items_synced: int = 0
    last_source_synced: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_syncs": self.total_syncs,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "total_items_synced": self.total_items_synced,
            "last_source_synced": self.last_source_synced,
        }


class KnowledgeSync:
    """
    Knowledge synchronization manager.

    Handles synchronization from various sources including
    research reports, intelligence data, and project memory.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self._project_root = project_root or Path.cwd()
        self._reports_dir = self._project_root / ".lingflow" / "reports"
        self._research_dir = self._reports_dir / "research"
        self._github_dir = self._reports_dir / "github_trends"
        self._memory_file = self._project_root / ".claude" / "projects" / "-home-ai-LingFlow" / "memory" / "MEMORY.md"
        self._stats = SyncStats()

    async def sync_from_research(self) -> SyncResult:
        """
        Synchronize knowledge from research reports.

        Reads reports from .lingflow/reports/research/ and
        extracts key patterns and best practices.
        """
        result = SyncResult(source="research")

        if not self._research_dir.exists():
            result.errors.append("Research directory not found")
            result.end_time = datetime.now()
            return result

        for report_file in self._research_dir.glob("*.md"):
            try:
                content = report_file.read_text(encoding="utf-8")

                # Extract knowledge items from report
                items = self._extract_items_from_report(
                    content,
                    report_file.name
                )

                for item in items:
                    # In a real implementation, this would store in the knowledge DB
                    result.items_added += 1

            except Exception as e:
                result.errors.append(f"Error processing {report_file.name}: {e}")

        result.end_time = datetime.now()
        self._update_stats(result)

        return result

    async def sync_from_intelligence(self) -> SyncResult:
        """
        Synchronize knowledge from intelligence system.

        Reads from GitHub trends, NPM trends, and competitive
        analysis reports.
        """
        result = SyncResult(source="intelligence")

        # Sync GitHub trends
        if self._github_dir.exists():
            for trend_file in self._github_dir.glob("*.json"):
                try:
                    content = trend_file.read_text(encoding="utf-8")
                    data = json.loads(content)

                    # Extract high-value repos
                    repos = data.get("repos", [])
                    for repo in repos:
                        if repo.get("relevance_score", 0) >= 70:
                            # In a real implementation, store as knowledge item
                            result.items_added += 1

                except (json.JSONDecodeError, Exception) as e:
                    result.errors.append(f"Error processing {trend_file.name}: {e}")

        result.end_time = datetime.now()
        self._update_stats(result)

        return result

    async def sync_from_memory(self) -> SyncResult:
        """
        Synchronize knowledge from project memory.

        Reads MEMORY.md and extracts architecture decisions
        and conventions.
        """
        result = SyncResult(source="memory")

        if not self._memory_file.exists():
            result.errors.append("Memory file not found")
            result.end_time = datetime.now()
            return result

        try:
            content = self._memory_file.read_text(encoding="utf-8")

            # Extract sections as knowledge items
            sections = self._parse_memory_sections(content)

            for section_title, section_content in sections.items():
                # Extract key decisions and patterns
                items = self._extract_items_from_section(
                    section_title,
                    section_content
                )
                result.items_added += len(items)

        except Exception as e:
            result.errors.append(f"Error reading memory: {e}")

        result.end_time = datetime.now()
        self._update_stats(result)

        return result

    async def sync_all(self) -> List[SyncResult]:
        """
        Synchronize from all sources.

        Returns a list of sync results, one for each source.
        """
        results = []

        results.append(await self.sync_from_research())
        results.append(await self.sync_from_intelligence())
        results.append(await self.sync_from_memory())

        return results

    def _extract_items_from_report(
        self,
        content: str,
        source_file: str
    ) -> List[KnowledgeItem]:
        """Extract knowledge items from a research report"""
        items = []

        # Look for code blocks with patterns
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)

        for lang, code in code_blocks:
            if len(code) > 50:  # Filter out trivial blocks
                item = KnowledgeItem(
                    title=f"Code Pattern from {source_file}",
                    content=code,
                    summary=code[:200] + "..." if len(code) > 200 else code,
                    category="code_pattern",
                    quality_score=0.7,
                    source=ResultSource.RESEARCH,
                    project="research",
                    tags={"code", "pattern", "research"},
                    metadata={"source_file": source_file, "language": lang},
                )
                items.append(item)

        # Look for TODO/FIXME items
        todos = re.findall(r'(?:TODO|FIXME):?\s*(.+)', content)
        for todo in todos:
            item = KnowledgeItem(
                title=f"Action Item from {source_file}",
                content=todo,
                summary=todo,
                category="action_item",
                quality_score=0.5,
                source=ResultSource.RESEARCH,
                project="research",
                tags={"todo", "action", "research"},
                metadata={"source_file": source_file},
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
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        if current_content:
            sections[current_section] = "\n".join(current_content)

        return sections

    def _extract_items_from_section(
        self,
        title: str,
        content: str
    ) -> List[KnowledgeItem]:
        """Extract knowledge items from a memory section"""
        items = []

        # Extract key-value pairs
        patterns = [
            r'###?\s*\*\*(.+?)\*\*:\s*(.+)',  # **Key**: Value
            r'###?\s*(.+?):\s*(.+)',           # Key: Value
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for key, value in matches:
                if len(value) > 20:  # Filter out trivial values
                    item = KnowledgeItem(
                        title=f"Memory: {key.strip()}",
                        content=value.strip(),
                        summary=value.strip()[:200],
                        category="memory",
                        quality_score=0.8,
                        source=ResultSource.MEMORY,
                        project="lingflow",
                        tags={"memory", "decision"},
                        metadata={"section": title},
                    )
                    items.append(item)

        return items

    def _update_stats(self, result: SyncResult) -> None:
        """Update sync statistics"""
        self._stats.total_syncs += 1
        self._stats.last_sync_time = result.end_time or datetime.now()
        self._stats.total_items_synced += result.total_items
        self._stats.last_source_synced = result.source

    def get_stats(self) -> SyncStats:
        """Get synchronization statistics"""
        return self._stats

    def reset_stats(self) -> None:
        """Reset synchronization statistics"""
        self._stats = SyncStats()
