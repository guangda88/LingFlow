"""Tests for Constitutional Constraint System"""

import tempfile
from pathlib import Path

import pytest
import yaml

from lingflow.core.constitution import (
    ComplianceReport,
    Constitution,
    ConstitutionalPrinciple,
    EnforcementLevel,
    Violation,
)


class TestEnforcementLevel:
    """Test EnforcementLevel enum"""

    def test_enforcement_level_values(self):
        """Test enforcement level values"""
        assert EnforcementLevel.MUST.value == "MUST"
        assert EnforcementLevel.SHOULD.value == "SHOULD"
        assert EnforcementLevel.MAY.value == "MAY"


class TestConstitutionalPrinciple:
    """Test ConstitutionalPrinciple dataclass"""

    def test_principle_initialization(self):
        """Test principle initialization"""
        principle = ConstitutionalPrinciple(
            id="SEC-001",
            cwe="CWE-79",
            name="XSS",
            level=EnforcementLevel.MUST,
            constraint="No unsafe HTML",
            implementation_pattern="Use DOMPurify",
            rationale="Prevents injection",
        )
        assert principle.id == "SEC-001"
        assert principle.cwe == "CWE-79"
        assert principle.level == EnforcementLevel.MUST

    def test_principle_str(self):
        """Test principle string representation"""
        principle = ConstitutionalPrinciple(
            id="SEC-001",
            cwe="CWE-79",
            name="XSS",
            level=EnforcementLevel.MUST,
            constraint="No unsafe HTML",
            implementation_pattern="Use DOMPurify",
            rationale="Prevents injection",
        )
        assert str(principle) == "SEC-001: XSS (MUST)"


class TestViolation:
    """Test Violation dataclass"""

    def test_violation_initialization(self):
        """Test violation initialization"""
        violation = Violation(
            principle_id="SEC-001",
            principle_name="XSS",
            severity=EnforcementLevel.MUST,
            description="Detected dangerous HTML",
            location="file.py",
            line_number=10,
            suggested_fix="Use escaping",
        )
        assert violation.principle_id == "SEC-001"
        assert violation.line_number == 10

    def test_violation_minimal(self):
        """Test violation with minimal parameters"""
        violation = Violation(
            principle_id="SEC-001",
            principle_name="XSS",
            severity=EnforcementLevel.MUST,
            description="Detected dangerous HTML",
        )
        assert violation.location is None
        assert violation.line_number is None
        assert violation.suggested_fix is None


class TestComplianceReport:
    """Test ComplianceReport dataclass"""

    def test_report_initialization(self):
        """Test report initialization"""
        report = ComplianceReport(
            is_compliant=True,
            total_principles=10,
            compliant_principles=10,
            coverage=1.0,
        )
        assert report.is_compliant is True
        assert report.total_principles == 10
        assert report.violations == []

    def test_add_violation(self):
        """Test adding a violation"""
        report = ComplianceReport(is_compliant=True, total_principles=10, compliant_principles=10)
        violation = Violation(
            principle_id="SEC-001",
            principle_name="XSS",
            severity=EnforcementLevel.MUST,
            description="Detected dangerous HTML",
        )
        report.add_violation(violation)
        assert len(report.violations) == 1
        assert report.is_compliant is False

    def test_get_summary(self):
        """Test getting summary statistics"""
        report = ComplianceReport(is_compliant=False, total_principles=10, compliant_principles=8)
        report.add_violation(
            Violation(
                principle_id="SEC-001",
                principle_name="XSS",
                severity=EnforcementLevel.MUST,
                description="Detected dangerous HTML",
            )
        )
        report.add_violation(
            Violation(
                principle_id="SEC-007",
                principle_name="Resource Consumption",
                severity=EnforcementLevel.SHOULD,
                description="No rate limiting",
            )
        )
        summary = report.get_summary()
        assert summary["is_compliant"] is False
        assert summary["total_principles"] == 10
        assert summary["compliant_principles"] == 8
        assert summary["violations_count"] == 2
        assert summary["must_violations"] == 1
        assert summary["should_violations"] == 1
        assert "coverage" in summary


class TestConstitutionInitialization:
    """Test Constitution initialization"""

    def test_initialization_defaults(self):
        """Test initialization with default principles"""
        constitution = Constitution()
        assert len(constitution.principles) > 0
        assert "SEC-001" in constitution._principle_by_id
        assert "CWE-79" in constitution._principles_by_cwe

    def test_initialization_with_file(self):
        """Test initialization from valid YAML file"""
        data = {
            "principles": [
                {
                    "id": "TEST-001",
                    "cwe": "CWE-XXX",
                    "name": "Test Principle",
                    "level": "MUST",
                    "constraint": "Test constraint",
                    "implementation_pattern": "Test pattern",
                    "rationale": "Test rationale",
                }
            ]
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            temp_path = f.name

        try:
            constitution = Constitution(temp_path)
            assert len(constitution.principles) == 1
            assert constitution.principles[0].id == "TEST-001"
        finally:
            Path(temp_path).unlink()

    def test_initialization_missing_file(self):
        """Test initialization with non-existent file"""
        constitution = Constitution("/nonexistent/path.yaml")
        assert len(constitution.principles) > 0

    def test_initialization_corrupted_file(self):
        """Test initialization with corrupted YAML file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            constitution = Constitution(temp_path)
            assert len(constitution.principles) > 0
        finally:
            Path(temp_path).unlink()


class TestConstitutionGetPrinciples:
    """Test getting principles"""

    def test_get_all_principles(self):
        """Test getting all principles"""
        constitution = Constitution()
        principles = constitution.get_principles()
        assert len(principles) > 0
        assert len(principles) == len(constitution.principles)

    def test_get_must_principles(self):
        """Test getting MUST principles"""
        constitution = Constitution()
        must_principles = constitution.get_principles(EnforcementLevel.MUST)
        for p in must_principles:
            assert p.level == EnforcementLevel.MUST

    def test_get_should_principles(self):
        """Test getting SHOULD principles"""
        constitution = Constitution()
        should_principles = constitution.get_principles(EnforcementLevel.SHOULD)
        for p in should_principles:
            assert p.level == EnforcementLevel.SHOULD


class TestConstitutionLookups:
    """Test principle lookups"""

    def test_get_principle_by_id(self):
        """Test getting principle by ID"""
        constitution = Constitution()
        principle = constitution.get_principle_by_id("SEC-001")
        assert principle is not None
        assert principle.id == "SEC-001"

    def test_get_principle_by_id_not_found(self):
        """Test getting non-existent principle by ID"""
        constitution = Constitution()
        principle = constitution.get_principle_by_id("NONEXISTENT")
        assert principle is None

    def test_get_principles_by_cwe(self):
        """Test getting principles by CWE"""
        constitution = Constitution()
        principles = constitution.get_principles_by_cwe("CWE-79")
        assert len(principles) > 0
        assert all(p.cwe == "CWE-79" for p in principles)


class TestConstitutionCheckCompliance:
    """Test compliance checking"""

    def test_check_compliance_clean_code(self):
        """Test checking clean code"""
        constitution = Constitution()
        code = "# This is clean code\nprint('Hello, World!')"
        report = constitution.check_compliance(code, "test.py")
        assert report.is_compliant is True
        assert report.total_principles == len(constitution.principles)

    def test_check_compliance_with_violations(self):
        """Test checking code with violations"""
        constitution = Constitution()
        code = 'password = "secret123"'
        report = constitution.check_compliance(code, "test.py")
        assert report.is_compliant is False
        assert len(report.violations) > 0

    def test_check_coverage_calculation(self):
        """Test coverage calculation"""
        constitution = Constitution()
        code = 'password = "secret123"'
        report = constitution.check_compliance(code, "test.py")
        assert report.coverage >= 0.0
        assert report.coverage <= 1.0


class TestConstitutionCheckXSS:
    """Test XSS checking"""

    def test_check_xss_dangerous_innerhtml(self):
        """Test detecting dangerous innerHTML"""
        constitution = Constitution()
        code = 'element.innerHTML = userInput + "text"'
        report = constitution.check_compliance(code, "test.js")
        xss_violations = [v for v in report.violations if v.principle_id == "SEC-001"]
        assert len(xss_violations) > 0

    def test_check_xss_dangerous_script_tag(self):
        """Test detecting script tags"""
        constitution = Constitution()
        code = 'html += "<script>" + userInput + "</script>"'
        report = constitution.check_compliance(code, "test.js")
        xss_violations = [v for v in report.violations if v.principle_id == "SEC-001"]
        assert len(xss_violations) > 0


class TestConstitutionCheckSQLInjection:
    """Test SQL injection checking"""

    def test_check_sql_injection_string_concat(self):
        """Test detecting string concatenation in SQL"""
        constitution = Constitution()
        code = 'cursor.execute("SELECT * FROM users WHERE name = \'" + userInput + "\'")'
        report = constitution.check_compliance(code, "test.py")
        sql_violations = [v for v in report.violations if v.principle_id == "SEC-002"]
        assert len(sql_violations) > 0

    def test_check_sql_injection_f_string(self):
        """Test detecting f-strings in SQL"""
        constitution = Constitution()
        code = 'query = f"SELECT * FROM users WHERE name = {userInput}"'
        report = constitution.check_compliance(code, "test.py")
        sql_violations = [v for v in report.violations if v.principle_id == "SEC-002"]
        assert len(sql_violations) > 0

    def test_check_sql_injection_safe_placeholder(self):
        """Test that parameterized queries are not flagged"""
        constitution = Constitution()
        code = 'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))'
        report = constitution.check_compliance(code, "test.py")
        sql_violations = [v for v in report.violations if v.principle_id == "SEC-002"]
        assert len(sql_violations) == 0


class TestConstitutionCheckHardcodedCredentials:
    """Test hardcoded credential checking"""

    def test_check_hardcoded_password(self):
        """Test detecting hardcoded password"""
        constitution = Constitution()
        code = 'password = "hardcoded_password"'
        report = constitution.check_compliance(code, "test.py")
        cred_violations = [v for v in report.violations if v.principle_id == "SEC-005"]
        assert len(cred_violations) > 0

    def test_check_hardcoded_api_key(self):
        """Test detecting hardcoded API key"""
        constitution = Constitution()
        code = 'api_key = "sk-1234567890abcdef"'
        report = constitution.check_compliance(code, "test.py")
        cred_violations = [v for v in report.violations if v.principle_id == "SEC-005"]
        assert len(cred_violations) > 0

    def test_skip_environment_variable_reference(self):
        """Test that environment variable references are not flagged"""
        constitution = Constitution()
        code = 'password = os.environ.get("PASSWORD")'
        report = constitution.check_compliance(code, "test.py")
        cred_violations = [v for v in report.violations if v.principle_id == "SEC-005"]
        assert len(cred_violations) == 0

    def test_skip_commented_password(self):
        """Test that commented passwords are not flagged"""
        constitution = Constitution()
        code = '# password = "hardcoded_password"'
        report = constitution.check_compliance(code, "test.py")
        cred_violations = [v for v in report.violations if v.principle_id == "SEC-005"]
        assert len(cred_violations) == 0


class TestConstitutionCheckWeakCrypto:
    """Test weak cryptographic algorithm checking"""

    def test_check_md5(self):
        """Test detecting MD5"""
        constitution = Constitution()
        code = "hash = hashlib.md5(data).hexdigest()"
        report = constitution.check_compliance(code, "test.py")
        crypto_violations = [v for v in report.violations if v.principle_id == "SEC-004"]
        assert len(crypto_violations) > 0

    def test_check_sha1(self):
        """Test detecting SHA1"""
        constitution = Constitution()
        code = "hash = hashlib.sha1(data).hexdigest()"
        report = constitution.check_compliance(code, "test.py")
        crypto_violations = [v for v in report.violations if v.principle_id == "SEC-004"]
        assert len(crypto_violations) > 0


class TestConstitutionCheckPathTraversal:
    """Test path traversal checking"""

    def test_check_path_traversal(self):
        """Test detecting path traversal"""
        constitution = Constitution()
        code = 'open("/var/data/" + user_input)'
        report = constitution.check_compliance(code, "test.py")
        path_violations = [v for v in report.violations if v.principle_id == "SEC-006"]
        assert len(path_violations) > 0


class TestConstitutionGetApplicablePrinciples:
    """Test getting applicable principles"""

    def test_get_applicable_principles(self):
        """Test getting applicable principles"""
        constitution = Constitution()
        context = {"type": "web"}
        principles = constitution.get_applicable_principles(context)
        assert len(principles) > 0


class TestConstitutionGenerateComplianceDocumentation:
    """Test compliance documentation generation"""

    def test_generate_documentation_clean(self):
        """Test generating documentation for clean code"""
        constitution = Constitution()
        code = "print('Hello, World!')"
        doc = constitution.generate_compliance_documentation(code, "test.py")
        assert "test.py" in doc
        assert "No violations detected" in doc

    def test_generate_documentation_with_violations(self):
        """Test generating documentation with violations"""
        constitution = Constitution()
        code = 'password = "secret123"'
        doc = constitution.generate_compliance_documentation(code, "test.py")
        assert "test.py" in doc
        assert "SEC-005" in doc
        assert "Hardcoded Credentials" in doc


class TestParameterizedSecurityChecks:
    """Parameterized security check tests"""

    @pytest.mark.parametrize(
        "code_snippet,expected_violation,principle_id",
        [
            # XSS attacks - using patterns that are actually detected
            (
                'element.innerHTML = userInput + "text"',
                True,
                "SEC-001",
            ),
            (
                "document.write(userInput)",
                True,
                "SEC-001",
            ),
            (
                'html += "<script>" + userInput + "</script>"',
                True,
                "SEC-001",
            ),
            (
                "element.textContent = userInput",
                False,
                "SEC-001",
            ),
            # SQL injection - using patterns that match actual detection rules
            (
                'cursor.execute("SELECT * FROM users WHERE name = \'" + userInput + "\'")',
                True,
                "SEC-002",
            ),
            (
                'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")',
                True,
                "SEC-002",
            ),
            (
                'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))',
                False,
                "SEC-002",
            ),
            # Hardcoded credentials
            (
                'password = "secret123"',
                True,
                "SEC-005",
            ),
            (
                'api_key = "sk-1234567890abcdef"',
                True,
                "SEC-005",
            ),
            (
                'password = os.environ.get("PASSWORD")',
                False,
                "SEC-005",
            ),
            (
                '# password = "secret123"',
                False,
                "SEC-005",
            ),
            # Weak cryptography
            (
                "hash = hashlib.md5(data).hexdigest()",
                True,
                "SEC-004",
            ),
            (
                "hash = hashlib.sha1(data).hexdigest()",
                True,
                "SEC-004",
            ),
            (
                "hash = hashlib.sha256(data).hexdigest()",
                False,
                "SEC-004",
            ),
            # Path traversal
            (
                'open("/var/data/" + user_input)',
                True,
                "SEC-006",
            ),
            (
                'open("/var/data/fixed_path")',
                False,
                "SEC-006",
            ),
        ],
    )
    def test_security_check_detection(self, code_snippet, expected_violation, principle_id):
        """Test detection of various security issues"""
        constitution = Constitution()
        report = constitution.check_compliance(code_snippet, "test.py")

        violations = [v for v in report.violations if v.principle_id == principle_id]

        if expected_violation:
            assert len(violations) > 0, f"Expected violation for {principle_id} in code: {code_snippet}"
        else:
            assert len(violations) == 0, f"Unexpected violation for {principle_id} in code: {code_snippet}"

    @pytest.mark.parametrize(
        "code_snippet,expected_violation_count",
        [
            # Multiple violations in single code - using patterns that are detected
            (
                'password = "secret"\nelement.innerHTML = userInput + "text"',
                2,
            ),
            (
                'cursor.execute("SELECT * FROM users WHERE name = \'" + userInput + "\'")\nhash = hashlib.md5(data)',
                2,
            ),
            # Single violation
            (
                'password = "secret"',
                1,
            ),
            # Clean code
            (
                'print("Hello, World!")',
                0,
            ),
        ],
    )
    def test_multiple_violation_detection(self, code_snippet, expected_violation_count):
        """Test detection of multiple violations in single code"""
        constitution = Constitution()
        report = constitution.check_compliance(code_snippet, "test.py")
        assert len(report.violations) == expected_violation_count

    @pytest.mark.parametrize(
        "file_extension,expected_applicable_count",
        [
            ("test.py", 10),
            ("test.js", 10),
            ("test.ts", 10),
            ("test.java", 10),
            ("test.rb", 10),
        ],
    )
    def test_applicability_by_file_type(self, file_extension, expected_applicable_count):
        """Test that principles are applicable to different file types"""
        constitution = Constitution()
        code = "print('Hello, World!')"
        report = constitution.check_compliance(code, file_extension)
        # All principles should be checked regardless of file extension
        assert report.total_principles >= expected_applicable_count
