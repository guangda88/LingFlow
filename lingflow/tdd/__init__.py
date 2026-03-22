"""
TDD Validation System

This module implements test-driven development enforcement and validation,
based on the Ten Simple Rules for AI-Assisted Coding in Science research.

Key Features:
- Test specification generation
- "Paper test" detection and prevention
- Test coverage analysis
- Test-first workflow enforcement
"""

import ast
import re
import subprocess
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class TestType(Enum):
    """Type of test"""
    UNIT = "unit"
    INTEGRATION = "integration"
    END_TO_END = "end_to_end"


class TestCaseStatus(Enum):
    """Status of a test case"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestCase:
    """A test case specification"""
    name: str
    description: str
    test_type: TestType
    scenario: str  # What is being tested
    expected_behavior: str  # What should happen
    edge_cases: List[str] = field(default_factory=list)
    assertions: List[str] = field(default_factory=list)
    status: TestCaseStatus = TestCaseStatus.PENDING
    is_paper_test: bool = False  # True if no assertions


@dataclass
class TestSpec:
    """Complete test specification for a feature"""
    feature_name: str
    description: str
    requirements: List[str]
    test_cases: List[TestCase] = field(default_factory=list)
    coverage_target: float = 80.0  # Target percentage

    def add_test_case(self, test_case: TestCase):
        """Add a test case to the specification"""
        self.test_cases.append(test_case)


@dataclass
class TestViolation:
    """A test-related violation"""
    type: str  # "paper_test", "no_edge_cases", "missing_assertion", etc.
    severity: str  # "critical", "high", "medium", "low"
    description: str
    location: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class TestReport:
    """Complete test validation report"""
    total_tests: int
    paper_tests: int
    test_coverage: float
    is_valid: bool
    violations: List[TestViolation] = field(default_factory=list)
    test_cases: List[TestCase] = field(default_factory=list)
    missing_edge_cases: List[str] = field(default_factory=list)
    execution_time: float = 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "total_tests": self.total_tests,
            "paper_tests": self.paper_tests,
            "test_coverage": f"{self.test_coverage:.2%}",
            "is_valid": self.is_valid,
            "violations": len(self.violations),
            "missing_edge_cases": len(self.missing_edge_cases)
        }


class TDDValidator:
    """
    Test-driven development validation system

    Enforces TDD best practices and detects anti-patterns like "paper tests".
    """

    def __init__(self, coverage_target: float = 80.0):
        """
        Initialize TDD validator

        Args:
            coverage_target: Target test coverage percentage
        """
        self.coverage_target = coverage_target

    def generate_test_specification(
        self,
        feature_description: str,
        requirements: List[str],
        security_principles: Optional[List[str]] = None
    ) -> TestSpec:
        """
        Generate a comprehensive test specification

        Args:
            feature_description: Description of the feature
            requirements: Functional requirements
            security_principles: Security principles that must be tested

        Returns:
            Complete test specification
        """
        spec = TestSpec(
            feature_name=self._extract_feature_name(feature_description),
            description=feature_description,
            requirements=requirements,
            coverage_target=self.coverage_target
        )

        # Generate test cases for each requirement
        for requirement in requirements:
            # Main happy path test
            spec.add_test_case(TestCase(
                name=f"test_{self._to_snake_case(requirement[:50])}",
                description=f"Test: {requirement}",
                test_type=TestType.UNIT,
                scenario=requirement,
                expected_behavior="Feature works as expected",
                edge_cases=self._generate_edge_cases(requirement),
                assertions=self._generate_assertions(requirement)
            ))

        # Add security tests if specified
        if security_principles:
            for principle in security_principles:
                spec.add_test_case(TestCase(
                    name=f"test_security_{self._to_snake_case(principle[:30])}",
                    description=f"Security test: {principle}",
                    test_type=TestType.UNIT,
                    scenario=f"Verify security principle: {principle}",
                    expected_behavior="Security principle is enforced",
                    assertions=[
                        "assert security_violation_detected() is False",
                        "assert error_message is not None or success is True"
                    ]
                ))

        # Add edge case tests
        spec.add_test_case(TestCase(
            name="test_edge_cases",
            description="Test edge cases and boundary conditions",
            test_type=TestType.UNIT,
            scenario="Test with edge cases",
            expected_behavior="Graceful handling of edge cases",
            edge_cases=["Empty input", "Null values", "Maximum values", "Minimum values"],
            assertions=["assert no_exceptions_raised()"]
        ))

        # Add error handling tests
        spec.add_test_case(TestCase(
            name="test_error_handling",
            description="Test error handling",
            test_type=TestType.UNIT,
            scenario="Test error scenarios",
            expected_behavior="Proper error handling and messages",
            edge_cases=["Invalid input", "Malformed data", "Network errors"],
            assertions=[
                "assert exception is caught",
                "assert error_message is not None",
                "assert system_remains_stable()"
            ]
        ))

        return spec

    def validate_tests(self, test_file: str) -> TestReport:
        """
        Validate test file for TDD best practices

        Args:
            test_file: Path to test file

        Returns:
            Test validation report
        """
        import time
        start_time = time.time()

        report = TestReport(
            total_tests=0,
            paper_tests=0,
            test_coverage=0.0,
            is_valid=True
        )

        if not Path(test_file).exists():
            report.violations.append(TestViolation(
                type="file_not_found",
                severity="critical",
                description=f"Test file not found: {test_file}"
            ))
            report.is_valid = False
            return report

        # Read test file
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            report.violations.append(TestViolation(
                type="read_error",
                severity="critical",
                description=f"Error reading test file: {e}",
                location=test_file
            ))
            report.is_valid = False
            return report

        # Parse test file
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            report.violations.append(TestViolation(
                type="syntax_error",
                severity="critical",
                description=f"Syntax error in test file: {e.msg}",
                location=test_file,
                line_number=e.lineno
            ))
            report.is_valid = False
            return report

        # Extract test functions
        test_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_functions.append(node)

        report.total_tests = len(test_functions)

        # Validate each test
        for func in test_functions:
            test_case = self._validate_test_function(func, content, test_file)
            report.test_cases.append(test_case)

            if test_case.is_paper_test:
                report.paper_tests += 1
                report.violations.append(TestViolation(
                    type="paper_test",
                    severity="critical",
                    description=f"Paper test detected: {test_case.name} has no assertions",
                    location=test_file,
                    line_number=func.lineno,
                    suggestion="Add meaningful assertions to verify expected behavior"
                ))
                report.is_valid = False

        # Check for edge case coverage
        report.missing_edge_cases = self._check_missing_edge_cases(test_functions)

        if report.missing_edge_cases:
            report.violations.append(TestViolation(
                type="missing_edge_cases",
                severity="medium",
                description=f"Missing edge case tests: {', '.join(report.missing_edge_cases[:5])}",
                suggestion="Add tests for edge cases and boundary conditions"
            ))

        # Calculate coverage (mock - would use coverage.py in production)
        report.test_coverage = self._estimate_coverage(content)

        # Check if coverage meets target
        if report.test_coverage < self.coverage_target:
            report.violations.append(TestViolation(
                type="low_coverage",
                severity="high",
                description=f"Test coverage ({report.test_coverage:.2%}) below target ({self.coverage_target:.2%})",
                suggestion=f"Increase test coverage to at least {self.coverage_target:.2%}"
            ))
            report.is_valid = False

        # Final validity check
        if report.paper_tests > 0 or report.test_coverage < self.coverage_target:
            report.is_valid = False

        report.execution_time = time.time() - start_time

        return report

    def _validate_test_function(self, func: ast.FunctionDef, content: str, file_path: str) -> TestCase:
        """Validate a single test function"""
        # Get function source
        lines = content.split('\n')
        func_lines = lines[func.lineno - 1:func.end_lineno]

        test_case = TestCase(
            name=func.name,
            description=ast.get_docstring(func) or f"Test: {func.name}",
            test_type=TestType.UNIT,
            scenario="",
            expected_behavior=""
        )

        # Check for assertions
        has_assertion = False
        assertion_count = 0

        for node in ast.walk(func):
            if isinstance(node, ast.Assert):
                has_assertion = True
                assertion_count += 1

                # Extract assertion
                assertion_code = ast.unparse(node.test) if hasattr(ast, 'unparse') else str(node.test)
                test_case.assertions.append(f"assert {assertion_code}")

        # Check if it's a paper test
        if not has_assertion:
            test_case.is_paper_test = True

        # Check for edge case indicators
        edge_case_keywords = ['edge', 'boundary', 'limit', 'empty', 'null', 'none', 'zero', 'max', 'min']
        func_text = ' '.join(func_lines).lower()
        test_case.edge_cases = [kw for kw in edge_case_keywords if kw in func_text]

        return test_case

    def _check_missing_edge_cases(self, test_functions: List[ast.FunctionDef]) -> List[str]:
        """Check for common edge cases that aren't tested"""
        edge_case_patterns = {
            'empty': r'\b(empty|null|none)\b',
            'boundary': r'\b(limit|boundary|max|min|edge)\b',
            'negative': r'\b(negative|<\s*0)\b',
            'large': r'\b(large|big|maximum|overflow)\b'
        }

        missing_cases = []

        # Check if patterns are present in any test
        for case_name, pattern in edge_case_patterns.items():
            found = False
            for func in test_functions:
                # Check docstring
                docstring = ast.get_docstring(func) or ""
                if re.search(pattern, docstring, re.IGNORECASE):
                    found = True
                    break

                # Check function body (simple check)
                func_source = ast.unparse(func) if hasattr(ast, 'unparse') else ""
                if re.search(pattern, func_source, re.IGNORECASE):
                    found = True
                    break

            if not found:
                missing_cases.append(case_name)

        return missing_cases

    def _estimate_coverage(self, content: str) -> float:
        """
        Estimate test coverage (simplified version)

        In production, this would use coverage.py or similar tools.
        """
        # Count lines and estimate based on test complexity
        lines = content.split('\n')
        non_empty_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))

        # Estimate: each test function covers about 10-20 lines of implementation
        test_functions = len(re.findall(r'def test_\w+', content))

        if test_functions == 0:
            return 0.0

        estimated_covered = test_functions * 15  # Rough estimate

        # Cap at 100%
        coverage = min(1.0, estimated_covered / max(non_empty_lines, 1))

        return coverage

    def _extract_feature_name(self, description: str) -> str:
        """Extract a simple feature name from description"""
        # Take first few words, convert to snake_case
        words = description.lower().split()[:5]
        return '_'.join(re.sub(r'[^a-z0-9]', '', w) for w in words)

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        text = re.sub(r'\s+', '_', text.strip())
        return text.lower()

    def _generate_edge_cases(self, requirement: str) -> List[str]:
        """Generate edge cases for a requirement"""
        # Common edge cases
        common_cases = [
            "Empty input",
            "Null/None values",
            "Maximum values",
            "Minimum values",
            "Invalid input format"
        ]

        # Context-specific edge cases
        if re.search(r'(password|auth|login)', requirement, re.IGNORECASE):
            common_cases.extend([
                "Wrong password",
                "Empty password",
                "Password too short",
                "Special characters in password"
            ])

        if re.search(r'(file|upload|download)', requirement, re.IGNORECASE):
            common_cases.extend([
                "Large file",
                "Zero-byte file",
                "Invalid file type",
                "File with spaces in name"
            ])

        if re.search(r'(api|request|response)', requirement, re.IGNORECASE):
            common_cases.extend([
                "Network timeout",
                "Server error (500)",
                "Bad request (400)",
                "Unauthorized (401)"
            ])

        return common_cases

    def _generate_assertions(self, requirement: str) -> List[str]:
        """Generate assertions for a requirement"""
        # Common assertions
        assertions = [
            "assert result is not None",
            "assert no_exceptions_raised()"
        ]

        # Context-specific assertions
        if re.search(r'(return|output)', requirement, re.IGNORECASE):
            assertions.extend([
                "assert expected_output == actual_output",
                "assert result.success is True"
            ])

        if re.search(r'(error|exception|fail)', requirement, re.IGNORECASE):
            assertions.extend([
                "assert error is caught",
                "assert error_message is not None"
            ])

        if re.search(r'(create|add|insert)', requirement, re.IGNORECASE):
            assertions.extend([
                "assert created_item.id is not None",
                "assert item_count_increased()"
            ])

        if re.search(r'(delete|remove)', requirement, re.IGNORECASE):
            assertions.extend([
                "assert item_removed() is True",
                "assert item_not_found_after_deletion()"
            ])

        return assertions

    def run_test_suite(self, test_file: str, verbose: bool = False) -> Dict[str, Any]:
        """
        Run the test suite and report results

        Args:
            test_file: Path to test file
            verbose: Show detailed output

        Returns:
            Test execution results
        """
        import time
        start_time = time.time()

        try:
            # Run pytest
            result = subprocess.run(
                ['python', '-m', 'pytest', test_file, '-v' if verbose else '-q', '--tb=short'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            execution_time = time.time() - start_time

            # Parse output
            output = result.stdout + result.stderr

            # Extract test counts
            match = re.search(r'(\d+) (passed|failed)', output)
            passed = int(match.group(1)) if match else 0

            match = re.search(r'(\d+) failed', output)
            failed = int(match.group(1)) if match else 0

            return {
                'success': result.returncode == 0,
                'passed': passed,
                'failed': failed,
                'total': passed + failed,
                'execution_time': execution_time,
                'output': output if verbose else None
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test execution timed out',
                'execution_time': 300.0
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': 'pytest not found. Install with: pip install pytest',
                'execution_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }

    def generate_test_report(self, test_spec: TestSpec, test_report: TestReport) -> str:
        """
        Generate comprehensive test report

        Args:
            test_spec: Test specification
            test_report: Test validation report

        Returns:
            Markdown-formatted report
        """
        lines = [
            f"# Test Validation Report: {test_spec.feature_name}",
            "",
            f"**Generated**: {test_spec.description}",
            "",
            "## Summary",
            "",
            f"- **Total Tests**: {test_report.total_tests}",
            f"- **Paper Tests**: {test_report.paper_tests} ⚠️",
            f"- **Test Coverage**: {test_report.test_coverage:.2%} (Target: {self.coverage_target:.2%})",
            f"- **Status**: {'✅ Valid' if test_report.is_valid else '❌ Invalid'}",
            f"- **Execution Time**: {test_report.execution_time:.3f}s",
            "",
        ]

        if test_report.violations:
            lines.extend([
                "## Violations",
                ""
            ])
            for violation in test_report.violations:
                severity_icon = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(violation.severity, '⚪')

                lines.extend([
                    f"- {severity_icon} **{violation.type}** ({violation.severity})",
                    f"  - Description: {violation.description}",
                ])

                if violation.suggestion:
                    lines.append(f"  - Suggestion: {violation.suggestion}")

                lines.append("")

        if test_report.missing_edge_cases:
            lines.extend([
                "## Missing Edge Cases",
                "",
                "Consider adding tests for:",
                ""
            ])
            for case in test_report.missing_edge_cases:
                lines.append(f"- {case}")
            lines.append("")

        if test_report.test_cases:
            lines.extend([
                "## Test Cases",
                ""
            ])
            for test_case in test_report.test_cases:
                status_icon = "✅" if not test_case.is_paper_test else "⚠️"
                lines.extend([
                    f"- {status_icon} **{test_case.name}**",
                    f"  - Description: {test_case.description}",
                    f"  - Assertions: {len(test_case.assertions)}",
                    f"  - Paper Test: {'Yes' if test_case.is_paper_test else 'No'}",
                ])

                if test_case.edge_cases:
                    lines.append(f"  - Edge Cases: {', '.join(test_case.edge_cases)}")

                lines.append("")

        return "\n".join(lines)
