"""Trust Guardrail Skill Implementation

This skill provides automatic verification for AI outputs before completion.
"""

from typing import Dict, Any
from pathlib import Path


def execute_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute trust guardrail verification.

    Args:
        params: Dictionary containing:
            - action: str - What action was taken
            - target: str - Target file/command/directory
            - expected: str - Expected content/output
            - actual_result: Any (optional) - Actual result from execution

    Returns:
        Dict with verification results and confidence score
    """
    from lingflow.trust import (
        TaskClaim,
        VerificationPipeline,
        FileContentVerifier,
        CommandOutputVerifier,
        DirectoryStructureVerifier,
        GitDiffVerifier,
        Skeptic,
    )

    # Extract parameters
    action = params.get("action", "")
    target = params.get("target", "")
    expected = params.get("expected", "")
    actual_result = params.get("actual_result")
    verifier_type = params.get("verifier_type", "file")  # file, command, directory, git

    # Create task claim
    claim = TaskClaim(
        action=action,
        target=target,
        expected=expected
    )

    # Create verification pipeline
    pipeline = VerificationPipeline()

    # Add appropriate verifier based on type
    if verifier_type == "file":
        pipeline.add_verifier(FileContentVerifier())
    elif verifier_type == "command":
        pipeline.add_verifier(CommandOutputVerifier())
    elif verifier_type == "directory":
        pipeline.add_verifier(DirectoryStructureVerifier())
    elif verifier_type == "git":
        pipeline.add_verifier(GitDiffVerifier())
    else:
        # Default to file verifier
        pipeline.add_verifier(FileContentVerifier())

    # Execute verification
    result = pipeline.execute(claim, actual_result=actual_result)

    # Create skeptic and audit
    skeptic = Skeptic()
    skeptic.verification_results = [result]
    skeptic.claim = claim
    audit_report = skeptic.audit(claim)

    # Generate report
    report = pipeline.generate_report()

    return {
        "success": report.passed,
        "confidence": report.overall_confidence,
        "summary": report.summary,
        "verification_result": {
            "level": result.level.name,
            "passed": result.passed,
            "detail": result.detail,
            "evidence": result.evidence,
            "confidence": result.confidence
        },
        "audit_report": {
            "questions": audit_report.questions,
            "challenges": audit_report.challenges,
            "confidence": audit_report.confidence,
            "summary": audit_report.summary
        },
        "claim": {
            "action": claim.action,
            "target": claim.target,
            "expected": claim.expected
        }
    }


# Example usage function
def example_verify_file_edit():
    """Example: Verify a file edit was successful."""
    result = execute_skill({
        "action": "添加 calculate_energy() 函数",
        "target": "energy.py",
        "expected": "def calculate_energy()",
        "verifier_type": "file"
    })

    if result["success"]:
        print(f"✓ Verification passed: {result['summary']}")
        print(f"  Confidence: {result['confidence']:.0%}")
    else:
        print(f"✗ Verification failed: {result['summary']}")
        print(f"  Challenges: {result['audit_report']['challenges']}")

    return result


def example_verify_test_run():
    """Example: Verify tests passed."""
    result = execute_skill({
        "action": "运行单元测试",
        "target": "pytest",
        "expected": "PASSED",
        "verifier_type": "command",
        "actual_result": "tests/test_energy.py::test_calculate PASSED [100%]"
    })

    if result["success"]:
        print(f"✓ Verification passed: {result['summary']}")
    else:
        print(f"✗ Verification failed: {result['summary']}")

    return result


def example_verify_directory_structure():
    """Example: Verify directory structure exists."""
    result = execute_skill({
        "action": "创建项目目录结构",
        "target": "/home/ai/myproject",
        "expected": "src,tests,docs",
        "verifier_type": "directory"
    })

    if result["success"]:
        print(f"✓ Verification passed: {result['summary']}")
    else:
        print(f"✗ Verification failed: {result['summary']}")

    return result


if __name__ == "__main__":
    print("Trust Guardrail Skill Examples\n")
    print("=" * 60)
    print("\n1. File Edit Verification:")
    print("-" * 60)
    example_verify_file_edit()

    print("\n2. Test Run Verification:")
    print("-" * 60)
    example_verify_test_run()

    print("\n3. Directory Structure Verification:")
    print("-" * 60)
    example_verify_directory_structure()

    print("\n" + "=" * 60)
