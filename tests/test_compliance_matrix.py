"""
Test suite for compliance_matrix module
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from lingflow.core.compliance_matrix import (
    ComplianceEntry,
    ComplianceMatrix,
    Implementation,
    VerificationStatus,
)


class TestImplementation:
    """Test Implementation dataclass"""

    def test_initialization(self):
        """Test basic initialization"""
        impl = Implementation(
            file="test.py",
            lines=[10, 11, 12],
            technique="SQLAlchemy ORM"
        )
        assert impl.file == "test.py"
        assert impl.lines == [10, 11, 12]
        assert impl.technique == "SQLAlchemy ORM"
        assert impl.status == VerificationStatus.UNVERIFIED
        assert impl.verified_at is None
        assert impl.verified_by is None

    def test_calculate_hash(self):
        """Test hash calculation"""
        impl = Implementation(
            file="test.py",
            lines=[10],
            technique="test"
        )
        content = "some code"
        impl.calculate_hash(content)
        assert impl.hash is not None
        assert len(impl.hash) == 32  # MD5 hash length

    def test_is_verified(self):
        """Test is_verified method"""
        impl = Implementation(
            file="test.py",
            lines=[10],
            technique="test",
            status=VerificationStatus.VERIFIED
        )
        assert impl.is_verified() is True

        impl.status = VerificationStatus.PENDING
        assert impl.is_verified() is False


class TestComplianceEntry:
    """Test ComplianceEntry dataclass"""

    def test_initialization(self):
        """Test basic initialization"""
        entry = ComplianceEntry(
            principle_id="PRINC-001",
            cwe="CWE-89",
            principle_name="SQL Injection Prevention",
            level="MUST"
        )
        assert entry.principle_id == "PRINC-001"
        assert entry.cwe == "CWE-89"
        assert entry.principle_name == "SQL Injection Prevention"
        assert entry.level == "MUST"
        assert entry.implementations == []
        assert entry.coverage == 0.0

    def test_add_implementation(self):
        """Test adding implementation"""
        entry = ComplianceEntry(
            principle_id="PRINC-001",
            cwe="CWE-89",
            principle_name="SQL Injection Prevention",
            level="MUST"
        )
        impl = Implementation(
            file="test.py",
            lines=[10],
            technique="test"
        )
        entry.add_implementation(impl)
        assert len(entry.implementations) == 1
        assert entry.implementations[0] == impl

    def test_update_coverage_empty(self):
        """Test coverage update with no implementations"""
        entry = ComplianceEntry(
            principle_id="PRINC-001",
            cwe="CWE-89",
            principle_name="SQL Injection Prevention",
            level="MUST"
        )
        entry.update_coverage()
        assert entry.coverage == 0.0

    def test_update_coverage_all_verified(self):
        """Test coverage update with all verified"""
        entry = ComplianceEntry(
            principle_id="PRINC-001",
            cwe="CWE-89",
            principle_name="SQL Injection Prevention",
            level="MUST"
        )
        for i in range(3):
            impl = Implementation(
                file=f"test{i}.py",
                lines=[10],
                technique="test",
                status=VerificationStatus.VERIFIED
            )
            entry.add_implementation(impl)
        entry.update_coverage()
        assert entry.coverage == 1.0

    def test_update_coverage_partial(self):
        """Test coverage update with partial verification"""
        entry = ComplianceEntry(
            principle_id="PRINC-001",
            cwe="CWE-89",
            principle_name="SQL Injection Prevention",
            level="MUST"
        )
        impl1 = Implementation(
            file="test1.py",
            lines=[10],
            technique="test",
            status=VerificationStatus.VERIFIED
        )
        impl2 = Implementation(
            file="test2.py",
            lines=[10],
            technique="test",
            status=VerificationStatus.PENDING
        )
        entry.add_implementation(impl1)
        entry.add_implementation(impl2)
        entry.update_coverage()
        assert entry.coverage == 0.5

    def test_get_summary(self):
        """Test get summary method"""
        entry = ComplianceEntry(
            principle_id="PRINC-001",
            cwe="CWE-89",
            principle_name="SQL Injection Prevention",
            level="MUST",
            last_verified="2024-01-01"
        )
        impl = Implementation(
            file="test.py",
            lines=[10],
            technique="test",
            status=VerificationStatus.VERIFIED
        )
        entry.add_implementation(impl)

        summary = entry.get_summary()
        assert summary["principle_id"] == "PRINC-001"
        assert summary["principle_name"] == "SQL Injection Prevention"
        assert summary["level"] == "MUST"
        assert summary["total_implementations"] == 1
        assert summary["verified_implementations"] == 1
        assert summary["coverage"] == "100.00%"
        assert summary["last_verified"] == "2024-01-01"


class TestComplianceMatrix:
    """Test ComplianceMatrix class"""

    def test_initialization_default_path(self):
        """Test initialization with default path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            default_path = Path(tmpdir) / ".lingflow" / "compliance_matrix.json"
            # Change current directory to tmpdir
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                matrix = ComplianceMatrix()
                assert matrix.path == ".lingflow/compliance_matrix.json"
                assert matrix.entries == {}
            finally:
                os.chdir(old_cwd)

    def test_initialization_custom_path(self):
        """Test initialization with custom path"""
        matrix = ComplianceMatrix(matrix_path="/custom/path.json")
        assert matrix.path == "/custom/path.json"

    def test_get_or_create_entry_new(self):
        """Test get_or_create_entry for new entry"""
        matrix = ComplianceMatrix()
        entry = matrix.get_or_create_entry(
            principle_id="PRINC-001",
            cwe="CWE-89",
            principle_name="SQL Injection Prevention",
            level="MUST"
        )
        assert entry.principle_id == "PRINC-001"
        assert "PRINC-001" in matrix.entries

    def test_get_or_create_entry_existing(self):
        """Test get_or_create_entry for existing entry"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))
            matrix.get_or_create_entry(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST"
            )
            entry2 = matrix.get_or_create_entry(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="Different Name",
                level="SHOULD"
            )
            assert entry2.principle_name == "SQL Injection Prevention"
            assert entry2.level == "MUST"
            assert len(matrix.entries) == 1

    def test_add_implementation(self):
        """Test adding implementation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            impl = matrix.add_implementation(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST",
                file_path="test.py",
                lines=[10, 11],
                technique="SQLAlchemy ORM",
                content="some code"
            )

            assert impl.file == "test.py"
            assert impl.lines == [10, 11]
            assert impl.technique == "SQLAlchemy ORM"
            assert impl.status == VerificationStatus.PENDING
            assert impl.hash is not None
            assert "PRINC-001" in matrix.entries

    def test_add_implementation_without_content(self):
        """Test adding implementation without content"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            impl = matrix.add_implementation(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST",
                file_path="test.py",
                lines=[10],
                technique="test"
            )

            assert impl.hash is None

    def test_verify_implementation_success(self):
        """Test verifying implementation successfully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            matrix.add_implementation(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST",
                file_path="test.py",
                lines=[10, 11],
                technique="test"
            )

            result = matrix.verify_implementation(
                principle_id="PRINC-001",
                file_path="test.py",
                lines=[10, 11],
                verified_by="user@example.com",
                notes="Verified manually"
            )

            assert result is True
            entry = matrix.entries["PRINC-001"]
            assert entry.implementations[0].status == VerificationStatus.VERIFIED
            assert entry.implementations[0].verified_by == "user@example.com"
            assert entry.implementations[0].notes == "Verified manually"
            assert entry.last_verified is not None

    def test_verify_implementation_not_found(self):
        """Test verifying non-existent principle"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))
            result = matrix.verify_implementation(
                principle_id="PRINC-001",
                file_path="test.py",
                lines=[10],
                verified_by="user@example.com"
            )
            assert result is False

    def test_verify_implementation_wrong_file(self):
        """Test verifying with wrong file path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            matrix.add_implementation(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST",
                file_path="test.py",
                lines=[10],
                technique="test"
            )

            result = matrix.verify_implementation(
                principle_id="PRINC-001",
                file_path="other.py",
                lines=[10],
                verified_by="user@example.com"
            )

            assert result is False

    def test_get_compliance_status(self):
        """Test getting compliance status for a principle"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))
            matrix.get_or_create_entry(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST"
            )

            status = matrix.get_compliance_status("PRINC-001")
            assert status["principle_id"] == "PRINC-001"
            assert status["principle_name"] == "SQL Injection Prevention"
            assert status["total_implementations"] == 0

    def test_get_compliance_status_not_found(self):
        """Test getting compliance status for non-existent principle"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))
            status = matrix.get_compliance_status("PRINC-001")
            assert status is None

    def test_get_overall_compliance_empty(self):
        """Test getting overall compliance with no entries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))
            overall = matrix.get_overall_compliance()
            assert overall["total_principles"] == 0
            assert overall["principles_with_implementations"] == 0
            assert overall["average_coverage"] == "0.00%"
            assert overall["verified_principles"] == 0

    def test_get_overall_compliance_with_entries(self):
        """Test getting overall compliance with entries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            # Add first principle with verified implementations
            entry1 = matrix.get_or_create_entry(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST"
            )
            impl1 = Implementation(
                file="test1.py",
                lines=[10],
                technique="test",
                status=VerificationStatus.VERIFIED
            )
            entry1.add_implementation(impl1)
            entry1.update_coverage()

            # Add second principle with unverified implementations
            entry2 = matrix.get_or_create_entry(
                principle_id="PRINC-002",
                cwe="CWE-90",
                principle_name="XSS Prevention",
                level="MUST"
            )
            impl2 = Implementation(
                file="test2.py",
                lines=[10],
                technique="test",
                status=VerificationStatus.PENDING
            )
            entry2.add_implementation(impl2)
            entry2.update_coverage()

            overall = matrix.get_overall_compliance()
            assert overall["total_principles"] == 2
            assert overall["principles_with_implementations"] == 2
            assert overall["verified_principles"] == 1
            assert overall["average_coverage"] == "50.00%"
            assert overall["verification_rate"] == "50.00%"

    def test_get_unverified_principles(self):
        """Test getting unverified principles"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            # Add verified principle
            entry1 = matrix.get_or_create_entry(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST"
            )
            impl1 = Implementation(
                file="test1.py",
                lines=[10],
                technique="test",
                status=VerificationStatus.VERIFIED
            )
            entry1.add_implementation(impl1)
            entry1.update_coverage()

            # Add unverified principle
            entry2 = matrix.get_or_create_entry(
                principle_id="PRINC-002",
                cwe="CWE-90",
                principle_name="XSS Prevention",
                level="MUST"
            )
            impl2 = Implementation(
                file="test2.py",
                lines=[10],
                technique="test",
                status=VerificationStatus.PENDING
            )
            entry2.add_implementation(impl2)
            entry2.update_coverage()

            unverified = matrix.get_unverified_principles()
            assert len(unverified) == 1
            assert "PRINC-002" in unverified

    def test_get_violated_principles(self):
        """Test getting violated principles (no implementations)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            # Add principle with implementations
            entry1 = matrix.get_or_create_entry(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST"
            )
            impl1 = Implementation(
                file="test1.py",
                lines=[10],
                technique="test"
            )
            entry1.add_implementation(impl1)

            # Add principle without implementations
            matrix.get_or_create_entry(
                principle_id="PRINC-002",
                cwe="CWE-90",
                principle_name="XSS Prevention",
                level="MUST"
            )

            violated = matrix.get_violated_principles()
            assert len(violated) == 1
            assert "PRINC-002" in violated

    def test_generate_report(self):
        """Test generating compliance report"""
        matrix = ComplianceMatrix()
        matrix.get_or_create_entry(
            principle_id="PRINC-001",
            cwe="CWE-89",
            principle_name="SQL Injection Prevention",
            level="MUST"
        )

        report = matrix.generate_report()
        assert "# Compliance Matrix Report" in report
        assert "PRINC-001" in report
        assert "SQL Injection Prevention" in report

    def test_export_to_csv(self):
        """Test exporting to CSV"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            csv_path = Path(tmpdir) / "export.csv"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            matrix.add_implementation(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST",
                file_path="test.py",
                lines=[10],
                technique="test"
            )

            matrix.export_to_csv(str(csv_path))
            assert csv_path.exists()

            content = csv_path.read_text()
            assert "Principle ID" in content
            assert "PRINC-001" in content
            assert "test.py" in content

    def test_track_code_changes_no_changes(self):
        """Test tracking code changes with no changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            matrix.add_implementation(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST",
                file_path="test.py",
                lines=[10],
                technique="test",
                content="old content"
            )

            affected = matrix.track_code_changes(
                old_content="old content",
                new_content="old content",
                file_path="test.py"
            )

            assert len(affected) == 0

    def test_track_code_changes_with_changes(self):
        """Test tracking code changes with actual changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            matrix.add_implementation(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST",
                file_path="test.py",
                lines=[10],
                technique="test",
                content="old content"
            )

            # Verify it first
            matrix.verify_implementation(
                principle_id="PRINC-001",
                file_path="test.py",
                lines=[10],
                verified_by="user@example.com"
            )

            affected = matrix.track_code_changes(
                old_content="old content",
                new_content="new content",
                file_path="test.py"
            )

            assert len(affected) == 1
            assert "PRINC-001" in affected
            assert matrix.entries["PRINC-001"].implementations[0].status == VerificationStatus.PENDING

    def test_get_principles_by_file(self):
        """Test getting principles by file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))

            matrix.add_implementation(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST",
                file_path="test.py",
                lines=[10],
                technique="test"
            )

            matrix.add_implementation(
                principle_id="PRINC-002",
                cwe="CWE-90",
                principle_name="XSS Prevention",
                level="MUST",
                file_path="test.py",
                lines=[20],
                technique="test"
            )

            principles = matrix.get_principles_by_file("test.py")
            assert len(principles) == 2
            assert any(p["principle_id"] == "PRINC-001" for p in principles)
            assert any(p["principle_id"] == "PRINC-002" for p in principles)

    def test_save_and_load(self):
        """Test saving and loading compliance matrix"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix1 = ComplianceMatrix(matrix_path=str(matrix_path))

            matrix1.add_implementation(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST",
                file_path="test.py",
                lines=[10],
                technique="test",
                content="content"
            )

            matrix1.save()

            # Load in a new instance
            matrix2 = ComplianceMatrix(matrix_path=str(matrix_path))
            assert "PRINC-001" in matrix2.entries
            assert len(matrix2.entries["PRINC-001"].implementations) == 1

    def test_load_nonexistent_file(self):
        """Test loading non-existent file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "nonexistent.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))
            assert matrix.entries == {}

    def test_load_corrupted_file(self):
        """Test loading corrupted JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "corrupted.json"
            matrix_path.write_text("invalid json")

            matrix = ComplianceMatrix(matrix_path=str(matrix_path))
            # Should not crash, entries should be empty
            assert matrix.entries == {}

    def test_entry_to_dict(self):
        """Test _entry_to_dict method"""
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_path = Path(tmpdir) / "matrix.json"
            matrix = ComplianceMatrix(matrix_path=str(matrix_path))
            entry = matrix.get_or_create_entry(
                principle_id="PRINC-001",
                cwe="CWE-89",
                principle_name="SQL Injection Prevention",
                level="MUST"
            )

            impl = Implementation(
                file="test.py",
                lines=[10],
                technique="test"
            )
            entry.add_implementation(impl)

            entry_dict = matrix._entry_to_dict(entry)
            assert entry_dict["principle_id"] == "PRINC-001"
            assert entry_dict["cwe"] == "CWE-89"
            assert len(entry_dict["implementations"]) == 1
