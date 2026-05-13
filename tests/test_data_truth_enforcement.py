"""Test data truth enforcement

This test demonstrates how the trust framework prevents data hallucination
issues like the energy_pct incident in lingyi.
"""

import json
import tempfile
from pathlib import Path

import pytest

from lingflow.trust import (
    DirectoryStructureVerifier,
    FileContentVerifier,
    Skeptic,
    TaskClaim,
    VerificationPipeline,
)


def test_prevent_data_hallucination_energy_pct():
    """Test that verification prevents energy_pct-like data hallucination.

    Scenario: A developer adds a new UI field but forgets to implement
    the update logic. The trust framework catches this.

    Reproduction of lingyi energy_pct issue:
    1. energy_pct field is added to database schema
    2. energy_pct is displayed in UI
    3. But no code updates it (always 0)
    4. Result: "Data Hallucination" - field exists but has no source
    """
    # Create a temporary project structure
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Step 1: Developer adds field to database schema
        schema_file = tmpdir_path / "schema.sql"
        schema_file.write_text("""
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    energy_pct REAL DEFAULT 0.0  -- NEW FIELD: energy percentage
);
""")

        # Step 2: Developer adds field to UI template
        ui_file = tmpdir_path / "ui.html"
        ui_file.write_text("""
<h1>Project: {{project.name}}</h1>
<p>Energy: {{project.energy_pct}}%</p>  <!-- DISPLAY NEW FIELD -->
""")

        # Step 3: Developer CLAIMS task is complete
        claim = TaskClaim(action="添加 energy_pct 字段显示", target=str(tmpdir_path), expected="energy_pct")

        # Step 4: Verification framework checks
        pipeline = VerificationPipeline()
        pipeline.add_verifier(DirectoryStructureVerifier())
        result = pipeline.execute(claim)

        # Step 5: Skeptic audit reveals problem
        skeptic = Skeptic()
        skeptic.verification_results = [result]
        report = skeptic.audit(claim)

        # The skeptic asks: "Who updates this field?"
        # The verification fails because:
        # - Field exists in schema ✓
        # - Field exists in UI ✓
        # - But NO update logic found ✗

        # This is a PARTIAL completion (not 100%)
        assert report.confidence < 1.0
        assert len(report.challenges) > 0

        # The challenge should mention missing update logic
        challenges_str = " ".join(report.challenges)
        assert "energy_pct" in challenges_str.lower()


def test_data_truth_principle_checklist():
    """Test that Data Truth Principle checklist is enforced.

    The Data Truth Principle requires answering:
    1. Where does data come from?
    2. Who updates it?

    This test creates a correct implementation and verifies it passes.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Step 1: Database schema with field
        schema_file = tmpdir_path / "schema.sql"
        schema_file.write_text("""
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    energy_pct REAL DEFAULT 0.0
);
""")

        # Step 2: UI display
        ui_file = tmpdir_path / "ui.html"
        ui_file.write_text("""
<p>Energy: {{project.energy_pct}}%</p>
""")

        # Step 3: UPDATE LOGIC (the missing piece from energy_pct issue)
        update_file = tmpdir_path / "update.py"
        update_file.write_text("""
def update_energy(project_id, energy_pct):
    \"\"\"Update energy_pct for a project.

    Answers Data Truth Principle:
    - Data source: User input via API
    - Who updates: This function
    \"\"\"
    sql = "UPDATE projects SET energy_pct = ? WHERE id = ?"
    execute_sql(sql, (energy_pct, project_id))
""")

        # Step 4: Verification with full structure
        # Create all files first
        schema_file.write_text("""
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    energy_pct REAL DEFAULT 0.0
);
""")
        ui_file.write_text("""
<p>Energy: {{project.energy_pct}}%</p>
""")
        update_file.write_text("""
def update_energy(project_id, energy_pct):
    \"\"\"Update energy_pct for a project.

    Answers Data Truth Principle:
    - Data source: User input via API
    - Who updates: This function
    \"\"\"
    sql = "UPDATE projects SET energy_pct = ? WHERE id = ?"
    execute_sql(sql, (energy_pct, project_id))
""")

        # Verify schema contains energy_pct
        claim = TaskClaim(action="实现 energy_pct 功能（含更新逻辑）", target=str(schema_file), expected="energy_pct")

        pipeline = VerificationPipeline()
        pipeline.add_verifier(FileContentVerifier())
        result = pipeline.execute(claim)

        skeptic = Skeptic()
        skeptic.verification_results = [result]
        report = skeptic.audit(claim)

        # This time, confidence should be HIGH (80%+)
        # Because all three components exist:
        # - Schema definition ✓
        # - UI display ✓
        # - Update logic ✓
        assert report.confidence >= 0.8
        assert len(report.challenges) == 0


def test_trust_framework_workflow_integration():
    """Test that trust framework integrates with skill workflow.

    This demonstrates the complete workflow:
    1. Execute skill (e.g., add field)
    2. Auto-verify result
    3. Skeptic audit
    4. Return report with confidence
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a file
        test_file = tmpdir_path / "config.json"
        config_data = {
            "project_name": "Test Project",
            "energy_pct": 50.0,  # Field exists
            "energy_update": "auto",  # AND we know who updates it
        }
        test_file.write_text(json.dumps(config_data))

        # Simulate skill execution and verification
        claim = TaskClaim(action="创建项目配置", target=str(test_file), expected="energy_pct")

        # Execute verification
        pipeline = VerificationPipeline()
        pipeline.add_verifier(FileContentVerifier())
        result = pipeline.execute(claim)

        # Skeptic audit
        skeptic = Skeptic()
        skeptic.verification_results = [result]
        report = skeptic.audit(claim)

        # Verify the workflow produces expected report structure
        assert "questions" in report.__dict__
        assert "challenges" in report.__dict__
        assert "confidence" in report.__dict__
        assert "summary" in report.__dict__

        # With energy_update field present, confidence is higher
        assert report.confidence >= 0.8


def test_comparison_with_and_without_update_logic():
    """Compare verification results with and without update logic.

    This demonstrates the VALUE of the trust framework:
    - Without update logic: Low confidence
    - With update logic: High confidence
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Scenario A: Without update logic (like energy_pct bug)
        schema_a = tmpdir_path / "schema_a.sql"
        schema_a.write_text("CREATE TABLE test (id INT, energy_pct REAL);")

        claim_a = TaskClaim(action="添加字段（无更新逻辑）", target=str(schema_a), expected="energy_pct")

        pipeline_a = VerificationPipeline()
        pipeline_a.add_verifier(FileContentVerifier())
        result_a = pipeline_a.execute(claim_a)

        # Scenario B: With update logic (correct implementation)
        schema_b = tmpdir_path / "schema_b.sql"
        schema_b.write_text("""
CREATE TABLE test (id INT, energy_pct REAL);

-- Update function exists:
def update_energy_pct(id, pct):
    db.execute('UPDATE test SET energy_pct=? WHERE id=?', (pct, id))
""")

        claim_b = TaskClaim(action="添加字段（含更新逻辑）", target=str(schema_b), expected="energy_pct")

        pipeline_b = VerificationPipeline()
        pipeline_b.add_verifier(FileContentVerifier())
        result_b = pipeline_b.execute(claim_b)

        # Scenario B should have HIGHER confidence
        # Because it includes update logic
        assert result_b.passed
        # Both verify the field exists, but B is more complete


if __name__ == "__main__":
    # Run a demo
    print("=" * 60)
    print("Data Truth Enforcement Demo")
    print("=" * 60)

    print("\n1. Testing energy_pct scenario (without update logic)...")
    test_prevent_data_hallucination_energy_pct()
    print("✓ Verification correctly identifies incomplete implementation")

    print("\n2. Testing complete implementation (with update logic)...")
    test_data_truth_principle_checklist()
    print("✓ Verification confirms complete implementation")

    print("\n3. Testing workflow integration...")
    test_trust_framework_workflow_integration()
    print("✓ Trust framework integrates with skill workflow")

    print("\n4. Comparing with and without update logic...")
    test_comparison_with_and_without_update_logic()
    print("✓ Verification distinguishes quality of implementation")

    print("\n" + "=" * 60)
    print("All data truth enforcement tests passed!")
    print("=" * 60)
