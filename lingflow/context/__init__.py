"""
Context Management and Cleanup System

This module implements context compression, code cleanup, and documentation optimization,
based on the Context Management research findings.

Key Features:
- 30-50% token savings through priority-based compression
- Automatic detection of unused code
- Documentation optimization
- External context file management
"""

import ast
import re
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class ContextPriority(Enum):
    """Priority level for context items"""
    CRITICAL = 100  # Permanent retention (constitution, compliance matrix)
    HIGH = 90       # Long-term retention
    MEDIUM = 70     # Medium-term retention
    LOW = 50        # Short-term retention
    OBSOLETE = 10   # Should be removed


@dataclass
class ContextItem:
    """An item in the context"""
    type: str
    content: str
    priority: ContextPriority
    retention: str  # "permanent", "until_completion", "until_cleanup"
    file_path: Optional[str] = None
    size_tokens: int = 0
    last_accessed: Optional[str] = None

    def calculate_size(self):
        """Estimate token size"""
        # Rough estimate: ~4 characters per token
        self.size_tokens = len(self.content) // 4


@dataclass
class CleanupItem:
    """An item marked for cleanup"""
    type: str  # "unused_code", "duplicate_comment", "obsolete_doc", "unused_import"
    location: str
    description: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    estimated_savings: int = 0  # Estimated token savings


@dataclass
class CleanupReport:
    """Report of cleanup operations"""
    total_items_cleaned: int
    tokens_saved: int
    files_cleaned: int
    cleanup_items: List[CleanupItem] = field(default_factory=list)
    compression_ratio: float = 0.0  # tokens_before / tokens_after

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "total_items_cleaned": self.total_items_cleaned,
            "tokens_saved": self.tokens_saved,
            "files_cleaned": self.files_cleaned,
            "cleanup_items_by_type": self._count_by_type(),
            "compression_ratio": f"{self.compression_ratio:.2%}"
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count cleanup items by type"""
        counts = defaultdict(int)
        for item in self.cleanup_items:
            counts[item.type] += 1
        return dict(counts)


class ContextManager:
    """
    Context management system with priority-based compression

    Achieves 30-50% token savings through intelligent compression.
    """

    def __init__(self, context_dir: str = ".lingflow/context"):
        """
        Initialize context manager

        Args:
            context_dir: Directory for context files
        """
        self.context_dir = Path(context_dir)
        self.context_dir.mkdir(parents=True, exist_ok=True)

        self.memory_file = self.context_dir / "memory.yaml"
        self.progress_file = self.context_dir / "progress.yaml"
        self.recovery_file = self.context_dir / "recovery.yaml"

        self.context_items: List[ContextItem] = []

    def load_context(self) -> List[ContextItem]:
        """Load context from external files"""
        items = []

        # Load from memory file
        if self.memory_file.exists():
            try:
                import yaml
                with open(self.memory_file, 'r') as f:
                    data = yaml.safe_load(f)

                if data and 'items' in data:
                    for item_data in data['items']:
                        item = ContextItem(
                            type=item_data['type'],
                            content=item_data['content'],
                            priority=ContextPriority(item_data['priority']),
                            retention=item_data['retention'],
                            file_path=item_data.get('file_path')
                        )
                        item.calculate_size()
                        items.append(item)
            except Exception as e:
                logger.error(f"Error loading context: {e}")

        self.context_items = items
        return items

    def save_context(self, items: Optional[List[ContextItem]] = None):
        """Save context to external files"""
        items = items or self.context_items

        try:
            import yaml
            data = {
                "version": "1.0.0",
                "last_updated": "2026-03-22",
                "items": [
                    {
                        "type": item.type,
                        "content": item.content,
                        "priority": item.priority.value,
                        "retention": item.retention,
                        "file_path": item.file_path
                    }
                    for item in items
                ]
            }

            with open(self.memory_file, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error saving context: {e}")

    def add_context_item(
        self,
        content: str,
        item_type: str,
        priority: ContextPriority,
        retention: str = "until_completion",
        file_path: Optional[str] = None
    ):
        """Add a context item"""
        item = ContextItem(
            type=item_type,
            content=content,
            priority=priority,
            retention=retention,
            file_path=file_path
        )
        item.calculate_size()
        self.context_items.append(item)

    def compress_context(self, target_reduction: float = 0.4) -> Tuple[List[ContextItem], int]:
        """
        Compress context based on priority

        Args:
            target_reduction: Target reduction percentage (0.0-1.0)

        Returns:
            Tuple of (compressed_items, tokens_saved)
        """
        total_tokens = sum(item.size_tokens for item in self.context_items)
        target_tokens = total_tokens * (1.0 - target_reduction)

        # Sort by priority (highest first)
        sorted_items = sorted(self.context_items, key=lambda x: x.priority.value, reverse=True)

        compressed_items = []
        current_tokens = 0
        tokens_saved = 0

        for item in sorted_items:
            if current_tokens + item.size_tokens <= target_tokens:
                compressed_items.append(item)
                current_tokens += item.size_tokens
            else:
                # Skip low-priority items
                tokens_saved += item.size_tokens

        self.context_items = compressed_items

        return compressed_items, tokens_saved

    def cleanup_obsolete_context(self) -> int:
        """Remove obsolete context items"""
        items_to_remove = [
            item for item in self.context_items
            if item.priority == ContextPriority.OBSOLETE
        ]

        tokens_saved = sum(item.size_tokens for item in items_to_remove)
        self.context_items = [
            item for item in self.context_items
            if item.priority != ContextPriority.OBSOLETE
        ]

        return tokens_saved

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context"""
        total_items = len(self.context_items)
        total_tokens = sum(item.size_tokens for item in self.context_items)

        priority_counts = defaultdict(int)
        for item in self.context_items:
            priority_counts[item.priority.name] += 1

        return {
            "total_items": total_items,
            "total_tokens": total_tokens,
            "priority_distribution": dict(priority_counts)
        }


class CodeCleanup:
    """
    Code cleanup and optimization system

    Detects and removes unused code, duplicates, and obsolete documentation.
    """

    def __init__(self):
        self.cleanup_items: List[CleanupItem] = []

    def analyze_file(self, file_path: str) -> List[CleanupItem]:
        """
        Analyze a file for cleanup opportunities

        Args:
            file_path: Path to file

        Returns:
            List of cleanup items
        """
        cleanup_items = []

        if not Path(file_path).exists():
            return cleanup_items

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for unused imports
            cleanup_items.extend(self._find_unused_imports(content, file_path))

            # Check for unused code (functions, classes, variables)
            cleanup_items.extend(self._find_unused_code(content, file_path))

            # Check for duplicate comments
            cleanup_items.extend(self._find_duplicate_comments(content, file_path))

            # Check for TODO comments that are stale
            cleanup_items.extend(self._find_stale_todos(content, file_path))

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

        return cleanup_items

    def _find_unused_imports(self, content: str, file_path: str) -> List[CleanupItem]:
        """Find unused imports"""
        items = []

        try:
            tree = ast.parse(content)

            # Get all imported names
            imported_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_names.add(alias.asname or alias.name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imported_names.add(alias.asname or alias.name)

            # Find used names
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)

            # Find unused imports
            unused = imported_names - used_names

            for name in unused:
                # Find the import statement
                lines = content.split('\n')
                for i, line in enumerate(lines, 1):
                    if f'import {name}' in line or f'from' in line and name in line:
                        items.append(CleanupItem(
                            type="unused_import",
                            location=file_path,
                            line_number=i,
                            description=f"Unused import: {name}",
                            suggestion=f"Remove 'import {name}'",
                            estimated_savings=len(line) // 4
                        ))
                        break

        except SyntaxError:
            pass

        return items

    def _find_unused_code(self, content: str, file_path: str) -> List[CleanupItem]:
        """Find unused functions and classes"""
        items = []

        try:
            tree = ast.parse(content)

            # Get all function and class definitions
            definitions = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    definitions[f'function:{node.name}'] = {
                        'lineno': node.lineno,
                        'name': node.name,
                        'type': 'function'
                    }
                elif isinstance(node, ast.ClassDef):
                    definitions[f'class:{node.name}'] = {
                        'lineno': node.lineno,
                        'name': node.name,
                        'type': 'class'
                    }

            # Check if definitions are used
            for def_key, def_info in definitions.items():
                # Simple heuristic: if name doesn't appear again in file, might be unused
                name = def_info['name']
                pattern = rf'\b{name}\b'
                occurrences = len(re.findall(pattern, content))

                # If only appears once (at definition), it's likely unused
                if occurrences <= 1:
                    # Skip if it's a special method or test
                    if name.startswith('_') or name.startswith('test_'):
                        continue

                    items.append(CleanupItem(
                        type="unused_code",
                        location=file_path,
                        line_number=def_info['lineno'],
                        description=f"Potentially unused {def_info['type']}: {name}",
                        suggestion=f"Remove or verify if {def_info['type']} {name} is used",
                        estimated_savings=50  # Rough estimate
                    ))

        except SyntaxError:
            pass

        return items

    def _find_duplicate_comments(self, content: str, file_path: str) -> List[CleanupItem]:
        """Find duplicate comments"""
        items = []

        lines = content.split('\n')
        comment_hashes = defaultdict(list)

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                # Remove varying amounts of leading spaces
                comment_content = stripped.lstrip('#').strip()
                if comment_content:
                    # Create hash for comment
                    comment_hash = hashlib.md5(comment_content.encode()).hexdigest()
                    comment_hashes[comment_hash].append((i, line))

        # Find duplicates
        for comment_hash, occurrences in comment_hashes.items():
            if len(occurrences) > 1:
                # Keep the first occurrence, mark others for cleanup
                for lineno, line in occurrences[1:]:
                    items.append(CleanupItem(
                        type="duplicate_comment",
                        location=file_path,
                        line_number=lineno,
                        description="Duplicate comment",
                        suggestion="Remove duplicate comment",
                        estimated_savings=len(line) // 4
                    ))

        return items

    def _find_stale_todos(self, content: str, file_path: str) -> List[CleanupItem]:
        """Find stale TODO comments"""
        items = []

        lines = content.split('\n')

        # Pattern for TODO with date
        todo_date_pattern = r'TODO.*(\d{4}-\d{2}-\d{2})'

        for i, line in enumerate(lines, 1):
            if 'TODO' in line.upper():
                # Check if TODO has a date
                match = re.search(todo_date_pattern, line)
                if match:
                    date_str = match.group(1)
                    try:
                        from datetime import datetime
                        todo_date = datetime.strptime(date_str, '%Y-%m-%d')
                        current_date = datetime.now()

                        # If TODO is older than 30 days, mark as stale
                        if (current_date - todo_date).days > 30:
                            items.append(CleanupItem(
                                type="stale_todo",
                                location=file_path,
                                line_number=i,
                                description=f"Stale TODO from {date_str}",
                                suggestion="Address TODO or remove if no longer applicable",
                                estimated_savings=len(line) // 4
                            ))
                    except ValueError:
                        pass

        return items

    def cleanup_file(self, file_path: str, dry_run: bool = True) -> CleanupReport:
        """
        Cleanup a file

        Args:
            file_path: Path to file
            dry_run: If True, don't actually make changes

        Returns:
            Cleanup report
        """
        report = CleanupReport(
            total_items_cleaned=0,
            tokens_saved=0,
            files_cleaned=1 if not dry_run else 0
        )

        # Analyze file
        cleanup_items = self.analyze_file(file_path)
        report.cleanup_items = cleanup_items

        if not dry_run:
            # Actually perform cleanup
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Process cleanup items in reverse order (to maintain line numbers)
                for item in sorted(cleanup_items, key=lambda x: x.line_number or 0, reverse=True):
                    if item.line_number and item.line_number <= len(lines):
                        # Remove line
                        del lines[item.line_number - 1]
                        report.total_items_cleaned += 1
                        report.tokens_saved += item.estimated_savings

                # Write back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)

            except Exception as e:
                logger.error(f"Error cleaning {file_path}: {e}")

        return report


class DocumentationOptimizer:
    """
    Documentation optimization system

    Cleans up and optimizes documentation files.
    """

    def optimize_documentation(self, docs_dir: str, dry_run: bool = True) -> CleanupReport:
        """
        Optimize documentation in directory

        Args:
            docs_dir: Path to documentation directory
            dry_run: If True, don't actually make changes

        Returns:
            Cleanup report
        """
        report = CleanupReport(
            total_items_cleaned=0,
            tokens_saved=0,
            files_cleaned=0
        )

        docs_path = Path(docs_dir)
        if not docs_path.exists():
            return report

        # Find markdown files
        md_files = list(docs_path.glob('**/*.md'))

        for md_file in md_files:
            file_report = self._optimize_md_file(md_file, dry_run)
            report.total_items_cleaned += file_report.total_items_cleaned
            report.tokens_saved += file_report.tokens_saved
            report.files_cleaned += file_report.files_cleaned
            report.cleanup_items.extend(file_report.cleanup_items)

        return report

    def _optimize_md_file(self, file_path: Path, dry_run: bool = True) -> CleanupReport:
        """Optimize a single markdown file"""
        report = CleanupReport(
            total_items_cleaned=0,
            tokens_saved=0,
            files_cleaned=1 if not dry_run else 0
        )

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            new_lines = []
            tokens_saved = 0

            i = 0
            while i < len(lines):
                line = lines[i]

                # Remove empty lines that are followed by empty lines
                if not line.strip() and i < len(lines) - 1 and not lines[i + 1].strip():
                    # Skip this empty line
                    tokens_saved += len(line) // 4
                    report.total_items_cleaned += 1
                    i += 1
                    continue

                # Remove trailing whitespace
                if line != line.rstrip():
                    saved = len(line) - len(line.rstrip())
                    if saved > 0:
                        tokens_saved += saved // 4
                        report.cleanup_items.append(CleanupItem(
                            type="trailing_whitespace",
                            location=str(file_path),
                            line_number=i + 1,
                            description=f"Trailing whitespace ({saved} characters)",
                            suggestion="Strip trailing whitespace",
                            estimated_savings=saved // 4
                        ))

                new_lines.append(line.rstrip())
                i += 1

            report.tokens_saved = tokens_saved

            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))

        except Exception as e:
            logger.error(f"Error optimizing {file_path}: {e}")

        return report
