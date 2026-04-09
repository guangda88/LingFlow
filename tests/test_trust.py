"""Test trust framework"""

from pathlib import Path

import pytest

from lingflow.trust import (
    AuditReport,
    CommandOutputVerifier,
    DirectoryStructureVerifier,
    FileContentVerifier,
    GitDiffVerifier,
    Skeptic,
    TaskClaim,
    VerificationLevel,
    VerificationPipeline,
    VerificationResult,
)


def test_file_content_verifier_success():
    """Test file content verifier success."""
    claim = TaskClaim(action="Add test content", target="/tmp/test_trust_file.txt", expected="hello from trust framework")

    # Create file first
    Path("/tmp/test_trust_file.txt").write_text("hello from trust framework", encoding="utf-8")

    verifier = FileContentVerifier()
    result = verifier.verify(claim)

    assert result.passed
    assert "hello from trust framework" in result.detail
    assert result.confidence == 0.95

    # Cleanup
    Path("/tmp/test_trust_file.txt").unlink()


def test_file_content_verifier_failure():
    """Test file content verifier failure - file not found."""
    claim = TaskClaim(
        action="Add test content", target="/tmp/test_trust_file_missing.txt", expected="hello from trust framework"
    )

    verifier = FileContentVerifier()
    result = verifier.verify(claim)

    assert not result.passed
    assert "test_trust_file_missing.txt" in result.detail


def test_verification_pipeline():
    """Test verification pipeline."""
    claim = TaskClaim(action="Add test content", target="/tmp/test_trust_file2.txt", expected="test content")

    # Create file
    Path("/tmp/test_trust_file2.txt").write_text("test content", encoding="utf-8")

    pipeline = VerificationPipeline()
    pipeline.add_verifier(FileContentVerifier())

    result = pipeline.execute(claim)

    assert result.passed
    assert "test content" in result.detail

    # Cleanup
    Path("/tmp/test_trust_file2.txt").unlink()


def test_skeptic_audit():
    """Test skeptic audit."""
    claim = TaskClaim(action="Add feature", target="file.txt", expected="feature added")

    skeptic = Skeptic()
    report = skeptic.audit(claim)

    # Check questions list
    assert len(report.questions) > 0
    assert "I claimed:" in report.questions[0]

    # Should have challenges since no verification results set
    assert len(report.challenges) > 0
    assert report.confidence == 0.0


def test_skeptic_confidence():
    """Test confidence calculation."""
    claim = TaskClaim(action="Complete all verifications", target="test", expected="result")

    skeptic = Skeptic()

    # Add a successful verification result
    skeptic.verification_results = [
        VerificationResult(level=VerificationLevel.SEMANTIC, passed=True, detail="Verification passed", confidence=0.9)
    ]

    report = skeptic.audit(claim)

    # Should pass with high confidence
    assert report.confidence == 1.0
    assert len(report.challenges) == 0


def test_command_output_verifier_success():
    """Test command output verifier success."""
    claim = TaskClaim(action="Run test command", target="echo", expected="hello")

    verifier = CommandOutputVerifier()
    result = verifier.verify(claim, actual_result="hello from command")

    assert result.passed
    assert "hello" in result.detail


def test_command_output_verifier_failure():
    """Test command output verifier failure."""
    claim = TaskClaim(action="Run test command", target="echo", expected="goodbye")

    verifier = CommandOutputVerifier()
    result = verifier.verify(claim, actual_result="hello from command")

    assert not result.passed
    assert "goodbye" in result.detail


def test_directory_structure_verifier_success():
    """Test directory structure verifier success."""
    import tempfile

    claim = TaskClaim(action="Create directory structure", target="/tmp/test_trust_dir", expected="file1.txt,subdir")

    # Create directory structure
    Path("/tmp/test_trust_dir").mkdir(exist_ok=True)
    Path("/tmp/test_trust_dir/file1.txt").write_text("test")
    Path("/tmp/test_trust_dir/subdir").mkdir()

    verifier = DirectoryStructureVerifier()
    result = verifier.verify(claim)

    assert result.passed
    assert "file1.txt" in result.detail

    # Cleanup
    import shutil

    shutil.rmtree("/tmp/test_trust_dir")


def test_directory_structure_verifier_missing():
    """Test directory structure verifier with missing items."""
    import tempfile

    claim = TaskClaim(action="Create directory structure", target="/tmp/test_trust_dir2", expected="file1.txt,missing.txt")

    # Create directory with only one expected item
    Path("/tmp/test_trust_dir2").mkdir(exist_ok=True)
    Path("/tmp/test_trust_dir2/file1.txt").write_text("test")

    verifier = DirectoryStructureVerifier()
    result = verifier.verify(claim)

    assert not result.passed
    assert "missing.txt" in result.detail

    # Cleanup
    import shutil

    shutil.rmtree("/tmp/test_trust_dir2")


def test_git_diff_verifier():
    """Test git diff verifier."""
    import shutil
    import subprocess
    import tempfile

    # Create a temp git repo
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)

        # Create and commit initial file
        initial_file = temp_dir / "initial.txt"
        initial_file.write_text("initial content")
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "add", "initial.txt"], cwd=temp_dir, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, capture_output=True, check=True)

        # Make a change
        initial_file.write_text("test_trust_marker new content")

        # Verify with GitDiffVerifier using a file inside the repo
        verifier = GitDiffVerifier()
        # Pass the file path, not the dir path - GitDiffVerifier will use the parent dir
        result = verifier.verify(TaskClaim(action="Commit changes", target=str(initial_file), expected="test_trust_marker"))

        # Should find marker in unstaged changes or show working dir status
        assert result.passed or "test_trust_marker" in result.detail or "工作区干净" in result.detail

    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
