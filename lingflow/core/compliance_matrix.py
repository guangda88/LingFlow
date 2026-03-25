"""
Compliance Matrix System

This module implements traceability for compliance requirements to implementations,
ensuring continuous compliance tracking across the codebase.

Based on Constitutional Spec-Driven Development research:
- 4.3x improvement in compliance documentation
- Continuous compliance tracking
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Verification status for implementation"""

    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"


@dataclass
class Implementation:
    """An implementation of a security principle"""

    file: str
    lines: List[int]
    technique: str
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    notes: Optional[str] = None
    hash: Optional[str] = None

    def calculate_hash(self, content: str):
        """Calculate hash of implementation for change detection"""
        self.hash = hashlib.md5(content.encode()).hexdigest()

    def is_verified(self) -> bool:
        """Check if implementation is verified"""
        return self.status == VerificationStatus.VERIFIED


@dataclass
class ComplianceEntry:
    """A single entry in the compliance matrix"""

    principle_id: str
    cwe: str
    principle_name: str
    level: str  # MUST, SHOULD, MAY
    implementations: List[Implementation] = field(default_factory=list)
    last_verified: Optional[str] = None
    coverage: float = 0.0  # 0.0 to 1.0

    def add_implementation(self, implementation: Implementation):
        """Add an implementation to this principle"""
        self.implementations.append(implementation)
        self.update_coverage()

    def update_coverage(self):
        """Update coverage percentage"""
        if not self.implementations:
            self.coverage = 0.0
        else:
            verified_count = sum(1 for imp in self.implementations if imp.is_verified())
            self.coverage = verified_count / len(self.implementations)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of this compliance entry"""
        return {
            "principle_id": self.principle_id,
            "principle_name": self.principle_name,
            "level": self.level,
            "total_implementations": len(self.implementations),
            "verified_implementations": sum(1 for imp in self.implementations if imp.is_verified()),
            "coverage": f"{self.coverage:.2%}",
            "last_verified": self.last_verified,
        }


class ComplianceMatrix:
    """
    Compliance matrix for tracking implementation of security principles

    This provides traceability from security principles to their implementations
    in the codebase, enabling continuous compliance monitoring.
    """

    def __init__(self, matrix_path: Optional[str] = None):
        """
        Initialize compliance matrix

        Args:
            matrix_path: Path to JSON matrix file
        """
        self.path = matrix_path or ".lingflow/compliance_matrix.json"
        self.entries: Dict[str, ComplianceEntry] = {}
        self._load()

    def _load(self):
        """Load compliance matrix from file"""
        if Path(self.path).exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.entries = {}
                for entry_data in data.get("entries", []):
                    implementations = [
                        Implementation(**imp_data)
                        for imp_data in entry_data.get("implementations", [])
                    ]

                    entry = ComplianceEntry(
                        principle_id=entry_data["principle_id"],
                        cwe=entry_data["cwe"],
                        principle_name=entry_data["principle_name"],
                        level=entry_data["level"],
                        implementations=implementations,
                        last_verified=entry_data.get("last_verified"),
                        coverage=entry_data.get("coverage", 0.0),
                    )
                    self.entries[entry.principle_id] = entry
            except Exception as e:
                logger.error(f"Error loading compliance matrix: {e}")
                self.entries = {}

    def save(self):
        """Save compliance matrix to file"""
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat(),
            "entries": [self._entry_to_dict(entry) for entry in self.entries.values()],
        }

        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _entry_to_dict(self, entry: ComplianceEntry) -> Dict[str, Any]:
        """Convert compliance entry to dictionary"""
        def implementation_to_dict(imp: Implementation) -> Dict[str, Any]:
            """Convert implementation to dictionary with enum serialization"""
            imp_dict = asdict(imp)
            imp_dict["status"] = imp.status.value if isinstance(imp.status, VerificationStatus) else imp.status
            return imp_dict

        return {
            "principle_id": entry.principle_id,
            "cwe": entry.cwe,
            "principle_name": entry.principle_name,
            "level": entry.level,
            "implementations": [implementation_to_dict(imp) for imp in entry.implementations],
            "last_verified": entry.last_verified,
            "coverage": entry.coverage,
        }

    def get_or_create_entry(
        self, principle_id: str, cwe: str, principle_name: str, level: str
    ) -> ComplianceEntry:
        """Get existing entry or create new one"""
        if principle_id not in self.entries:
            self.entries[principle_id] = ComplianceEntry(
                principle_id=principle_id, cwe=cwe, principle_name=principle_name, level=level
            )
        return self.entries[principle_id]

    def add_implementation(
        self,
        principle_id: str,
        cwe: str,
        principle_name: str,
        level: str,
        file_path: str,
        lines: List[int],
        technique: str,
        content: Optional[str] = None,
    ) -> Implementation:
        """
        Add an implementation to the compliance matrix

        Args:
            principle_id: Principle ID
            cwe: CWE identifier
            principle_name: Principle name
            level: Enforcement level
            file_path: File path
            lines: Line numbers where implemented
            technique: Technique used (e.g., "SQLAlchemy ORM")
            content: Code content for hash calculation

        Returns:
            Implementation object
        """
        entry = self.get_or_create_entry(principle_id, cwe, principle_name, level)

        implementation = Implementation(
            file=file_path, lines=lines, technique=technique, status=VerificationStatus.PENDING
        )

        if content:
            implementation.calculate_hash(content)

        entry.add_implementation(implementation)
        self.save()

        return implementation

    def verify_implementation(
        self,
        principle_id: str,
        file_path: str,
        lines: List[int],
        verified_by: str,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Mark an implementation as verified

        Args:
            principle_id: Principle ID
            file_path: File path
            lines: Line numbers
            verified_by: Who verified
            notes: Verification notes

        Returns:
            True if successful
        """
        if principle_id not in self.entries:
            return False

        entry = self.entries[principle_id]

        for imp in entry.implementations:
            if imp.file == file_path and imp.lines == lines:
                imp.status = VerificationStatus.VERIFIED
                imp.verified_at = datetime.utcnow().isoformat()
                imp.verified_by = verified_by
                imp.notes = notes
                entry.last_verified = imp.verified_at
                entry.update_coverage()
                self.save()
                return True

        return False

    def get_compliance_status(self, principle_id: str) -> Optional[Dict[str, Any]]:
        """
        Get compliance status for a specific principle

        Args:
            principle_id: Principle ID

        Returns:
            Compliance status summary
        """
        if principle_id not in self.entries:
            return None

        entry = self.entries[principle_id]
        return entry.get_summary()

    def get_overall_compliance(self) -> Dict[str, Any]:
        """
        Get overall compliance across all principles

        Returns:
            Overall compliance summary
        """
        if not self.entries:
            return {
                "total_principles": 0,
                "principles_with_implementations": 0,
                "average_coverage": "0.00%",
                "verified_principles": 0,
                "verification_rate": "0%",
            }

        total_principles = len(self.entries)
        principles_with_implementations = sum(
            1 for entry in self.entries.values() if entry.implementations
        )

        average_coverage = (
            sum(entry.coverage for entry in self.entries.values()) / total_principles
            if total_principles > 0
            else 0.0
        )

        verified_principles = sum(1 for entry in self.entries.values() if entry.coverage >= 1.0)

        return {
            "total_principles": total_principles,
            "principles_with_implementations": principles_with_implementations,
            "average_coverage": f"{average_coverage:.2%}",
            "verified_principles": verified_principles,
            "verification_rate": (
                f"{verified_principles / total_principles:.2%}" if total_principles > 0 else "0%"
            ),
        }

    def get_unverified_principles(self) -> List[str]:
        """Get list of principles with unverified implementations"""
        return [
            principle_id for principle_id, entry in self.entries.items() if entry.coverage < 1.0
        ]

    def get_violated_principles(self) -> List[str]:
        """Get list of principles with no implementations"""
        return [
            principle_id
            for principle_id, entry in self.entries.items()
            if not entry.implementations
        ]

    def _add_overall_status(self, lines: list):
        """Add overall compliance status to report"""
        overall = self.get_overall_compliance()
        lines.extend(
            [
                "## Overall Status",
                "",
                f"- **Total Principles**: {overall['total_principles']}",
                f"- **Principles with Implementations**: {overall['principles_with_implementations']}",
                f"- **Verified Principles**: {overall['verified_principles']}",
                f"- **Average Coverage**: {overall['average_coverage']}",
                f"- **Verification Rate**: {overall['verification_rate']}",
                "",
            ]
        )

    def _add_violated_principles(self, lines: list):
        """Add violated principles section to report"""
        violated = self.get_violated_principles()
        if violated:
            lines.extend(["## ⚠️ Violated Principles (No Implementations)", ""])
            for principle_id in violated:
                entry = self.entries[principle_id]
                lines.append(f"- **{principle_id}**: {entry.principle_name} ({entry.level})")
            lines.append("")

    def _add_unverified_principles(self, lines: list):
        """Add unverified principles section to report"""
        unverified = self.get_unverified_principles()
        if unverified:
            lines.extend(["## 🔍 Unverified Principles", ""])
            for principle_id in unverified:
                entry = self.entries[principle_id]
                lines.extend(
                    [
                        f"### {principle_id}: {entry.principle_name}",
                        f"- **Level**: {entry.level}",
                        f"- **Coverage**: {entry.coverage:.2%}",
                        f"- **Last Verified**: {entry.last_verified or 'Never'}",
                        "",
                    ]
                )
            lines.append("")

    def _add_entry_details(self, lines: list):
        """Add detailed entry information to report"""
        for principle_id, entry in sorted(self.entries.items()):
            lines.extend(
                [
                    f"### {principle_id}: {entry.principle_name}",
                    f"- **CWE**: {entry.cwe}",
                    f"- **Level**: {entry.level}",
                    f"- **Coverage**: {entry.coverage:.2%}",
                    f"- **Last Verified**: {entry.last_verified or 'Never'}",
                    "",
                ]
            )

            if entry.implementations:
                self._add_implementations(lines, entry.implementations)
            else:
                lines.extend(["❌ No implementations", ""])

    def _add_implementations(self, lines: list, implementations):
        """Add implementation details to report"""
        lines.extend(["**Implementations**:", ""])
        for imp in implementations:
            status_icon = "✅" if imp.is_verified() else "⏳"
            lines.append(
                f"- {status_icon} **{imp.file}:{','.join(map(str, imp.lines))}** "
                f"({imp.technique})"
            )
            if imp.verified_by:
                lines.append(f"  - Verified by: {imp.verified_by} at {imp.verified_at}")
            if imp.notes:
                lines.append(f"  - Notes: {imp.notes}")
        lines.append("")

    def generate_report(self) -> str:
        """
        Generate a comprehensive compliance report

        Returns:
            Markdown-formatted report
        """
        lines = [
            "# Compliance Matrix Report",
            "",
            f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        self._add_overall_status(lines)
        self._add_violated_principles(lines)
        self._add_unverified_principles(lines)

        lines.extend(["## Detailed Compliance Matrix", ""])

        self._add_entry_details(lines)

        return "\n".join(lines)

    def _write_csv_header(self, writer):
        """Write CSV header row"""
        writer.writerow(
            [
                "Principle ID",
                "CWE",
                "Principle Name",
                "Level",
                "File",
                "Lines",
                "Technique",
                "Status",
                "Verified At",
                "Verified By",
                "Notes",
            ]
        )

    def _write_no_implementation_row(self, writer, principle_id, entry):
        """Write CSV row for principle with no implementation"""
        writer.writerow(
            [
                principle_id,
                entry.cwe,
                entry.principle_name,
                entry.level,
                "",
                "",
                "",
                "No Implementation",
                "",
                "",
                "",
            ]
        )

    def _write_implementation_row(self, writer, principle_id, entry, imp):
        """Write CSV row for an implementation"""
        writer.writerow(
            [
                principle_id,
                entry.cwe,
                entry.principle_name,
                entry.level,
                imp.file,
                ",".join(map(str, imp.lines)),
                imp.technique,
                imp.status.value,
                imp.verified_at or "",
                imp.verified_by or "",
                imp.notes or "",
            ]
        )

    def export_to_csv(self, output_path: str):
        """
        Export compliance matrix to CSV format

        Args:
            output_path: Output CSV file path
        """
        import csv

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            self._write_csv_header(writer)

            for principle_id, entry in self.entries.items():
                if not entry.implementations:
                    self._write_no_implementation_row(writer, principle_id, entry)
                else:
                    for imp in entry.implementations:
                        self._write_implementation_row(writer, principle_id, entry, imp)

    def track_code_changes(self, old_content: str, new_content: str, file_path: str) -> List[str]:
        """
        Track code changes and identify which principles are affected

        Args:
            old_content: Old code content
            new_content: New code content
            file_path: File path

        Returns:
            List of principle IDs affected by changes
        """
        old_hash = hashlib.md5(old_content.encode()).hexdigest()
        new_hash = hashlib.md5(new_content.encode()).hexdigest()

        if old_hash == new_hash:
            return []  # No changes

        # Find principles with implementations in this file
        affected_principles = []

        for principle_id, entry in self.entries.items():
            for imp in entry.implementations:
                if imp.file == file_path:
                    # This file has implementations of this principle
                    # Mark for re-verification
                    imp.status = VerificationStatus.PENDING
                    affected_principles.append(principle_id)

        self.save()

        return affected_principles

    def get_principles_by_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get all principles implemented in a specific file

        Args:
            file_path: File path

        Returns:
            List of principle summaries
        """
        principles = []

        for principle_id, entry in self.entries.items():
            for imp in entry.implementations:
                if imp.file == file_path:
                    # Handle both enum and string status
                    status_value = imp.status.value if isinstance(imp.status, VerificationStatus) else imp.status
                    principles.append(
                        {
                            "principle_id": principle_id,
                            "principle_name": entry.principle_name,
                            "level": entry.level,
                            "lines": imp.lines,
                            "technique": imp.technique,
                            "status": status_value,
                        }
                    )

        return principles
