"""Guardrail validation tests"""

import pytest

from lingflow.guardrail import (
    DeploymentGate,
    GuardrailValidator,
    SecurityReport,
    Severity,
    ValidationLevel,
    ValidationResult,
    Violation,
)


class TestEnums:
    def test_validation_levels(self):
        assert ValidationLevel.SYNTAX.value == "syntax"
        assert ValidationLevel.POLICY.value == "policy"
        assert ValidationLevel.SEMANTICS.value == "semantics"
        assert ValidationLevel.RISK.value == "risk"

    def test_severity(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"


class TestViolation:
    def test_defaults(self):
        v = Violation(
            level=ValidationLevel.SYNTAX,
            severity=Severity.HIGH,
            code="TEST",
            description="test violation",
        )
        assert v.location is None
        assert v.line_number is None
        assert v.suggestion is None
        assert v.cwe_id is None


class TestValidationResult:
    def test_defaults(self):
        r = ValidationResult(level=ValidationLevel.SYNTAX, is_passed=True)
        assert r.violations == []
        assert r.score == 0.0
        assert r.execution_time == 0.0


class TestSecurityReport:
    def test_defaults(self):
        r = SecurityReport(overall_score=100.0, risk_level="LOW", is_approved=True)
        assert r.total_violations == 0
        assert r.critical_violations == 0

    def test_get_summary(self):
        r = SecurityReport(overall_score=85.5, risk_level="LOW", is_approved=True)
        s = r.get_summary()
        assert s["risk_level"] == "LOW"
        assert s["is_approved"] is True


class TestGuardrailValidator:
    @pytest.fixture
    def validator(self):
        return GuardrailValidator()

    def test_init(self, validator):
        assert validator.config is not None
        assert validator.auto_approve_threshold == 20.0

    def test_validate_syntax_clean_code(self, validator):
        code = "x = 1\ny = 2\n"
        result = validator.validate_syntax(code, "test.py")
        assert result.is_passed is True
        assert result.score == 100.0

    def test_validate_syntax_error(self, validator):
        code = "def foo(\n"
        result = validator.validate_syntax(code, "test.py")
        assert result.is_passed is False
        assert len(result.violations) > 0

    def test_validate_syntax_non_python(self, validator):
        code = "const x = 1;"
        result = validator.validate_syntax(code, "test.js")
        assert result.is_passed is True

    def test_validate_syntax_mixed_indentation(self, validator):
        code = "if True:\n\tx = 1\n    y = 2\n"
        result = validator.validate_syntax(code, "test.py")
        assert result.is_passed is False
        assert len(result.violations) > 0

    def test_validate_syntax_long_line(self, validator):
        code = "x = " + "'" * 200 + "\n"
        result = validator.validate_syntax(code, "test.py")
        violations = [v for v in result.violations if v.code == "LONG_LINE"]
        assert len(violations) > 0

    def test_validate_policy_clean(self, validator):
        code = "x = 1\ny = 2\n"
        result = validator.validate_policy(code, "test.py")
        assert result.is_passed is True
        assert result.score == 100.0

    def test_validate_policy_hardcoded_password(self, validator):
        code = 'password = "super_secret_password_123"\n'
        result = validator.validate_policy(code, "test.py")
        violations = [v for v in result.violations if "password" in v.code.lower()]
        assert len(violations) > 0

    def test_validate_policy_eval_usage(self, validator):
        code = "eval('1+1')\n"
        result = validator.validate_policy(code, "test.py")
        violations = [v for v in result.violations if "eval" in v.code.lower()]
        assert len(violations) > 0
        assert result.is_passed is False

    def test_validate_policy_skips_comments(self, validator):
        code = "# eval('something')\n"
        result = validator.validate_policy(code, "test.py")
        assert result.is_passed is True

    def test_validate_semantics_clean(self, validator):
        code = "def foo():\n    pass\n"
        result = validator.validate_semantics(code, "test.py")
        assert result.is_passed is True

    def test_validate_semantics_bare_except(self, validator):
        code = "try:\n    pass\nexcept:\n    pass\n"
        result = validator.validate_semantics(code, "test.py")
        violations = [v for v in result.violations if v.code == "BARE_EXCEPT"]
        assert len(violations) > 0

    def test_validate_semantics_syntax_error(self, validator):
        code = "def foo(\n"
        result = validator.validate_semantics(code, "test.py")
        assert result.is_passed is True

    def test_assess_risk_high_score(self, validator):
        results = {
            ValidationLevel.SYNTAX: ValidationResult(level=ValidationLevel.SYNTAX, is_passed=True, score=100.0),
            ValidationLevel.POLICY: ValidationResult(level=ValidationLevel.POLICY, is_passed=True, score=100.0),
            ValidationLevel.SEMANTICS: ValidationResult(level=ValidationLevel.SEMANTICS, is_passed=True, score=100.0),
        }
        result = validator.assess_risk(results)
        assert result.score == 100.0
        assert result.is_passed is True

    def test_assess_risk_low_score(self, validator):
        results = {
            ValidationLevel.SYNTAX: ValidationResult(level=ValidationLevel.SYNTAX, is_passed=True, score=0.0),
            ValidationLevel.POLICY: ValidationResult(level=ValidationLevel.POLICY, is_passed=True, score=0.0),
            ValidationLevel.SEMANTICS: ValidationResult(level=ValidationLevel.SEMANTICS, is_passed=True, score=0.0),
        }
        result = validator.assess_risk(results)
        assert result.is_passed is False

    def test_calculate_risk_level(self, validator):
        assert validator._calculate_risk_level(90) == "LOW"
        assert validator._calculate_risk_level(70) == "MEDIUM"
        assert validator._calculate_risk_level(50) == "HIGH"
        assert validator._calculate_risk_level(30) == "CRITICAL"

    def test_validate_agcef_clean(self, validator):
        code = "def well_documented_func():\n    '''Does something good.'''\n    return 42\n"
        report = validator.validate_agcef(code, "clean.py")
        assert report.overall_score > 0

    def test_validate_agcef_syntax_fail(self, validator):
        code = "def bad(\n"
        report = validator.validate_agcef(code, "bad.py")
        assert report.overall_score < 100

    def test_generate_report(self, validator):
        code = "x = 1\n"
        report = validator.validate_agcef(code, "test.py")
        text = validator.generate_report(report)
        assert "Security Validation Report" in text
        assert "Risk Level" in text

    def test_get_policy_suggestion(self, validator):
        s = validator._get_policy_suggestion("hardcoded_passwords")
        assert "environment" in s.lower() or "secret" in s.lower()
        s = validator._get_policy_suggestion("unknown_category")
        assert s == "Review and fix security issue"


class TestDeploymentGate:
    def test_init(self):
        gate = DeploymentGate()
        assert "test_coverage" in gate.gates

    def test_check_ready(self):
        gate = DeploymentGate()
        report = SecurityReport(overall_score=95.0, risk_level="LOW", is_approved=True)
        ready, issues = gate.check_deployment_readiness(report, test_coverage=90.0)
        assert ready is True
        assert len(issues) == 0

    def test_check_low_coverage(self):
        gate = DeploymentGate()
        report = SecurityReport(overall_score=95.0, risk_level="LOW", is_approved=True)
        ready, issues = gate.check_deployment_readiness(report, test_coverage=50.0)
        assert ready is False
        assert any("coverage" in i.lower() for i in issues)

    def test_check_critical_violations(self):
        gate = DeploymentGate()
        report = SecurityReport(overall_score=95.0, risk_level="LOW", is_approved=True, critical_violations=2)
        ready, issues = gate.check_deployment_readiness(report, test_coverage=90.0)
        assert ready is False
        assert any("critical" in i.lower() for i in issues)

    def test_check_paper_tests(self):
        gate = DeploymentGate()
        report = SecurityReport(overall_score=95.0, risk_level="LOW", is_approved=True)
        ready, issues = gate.check_deployment_readiness(report, test_coverage=90.0, paper_tests=3)
        assert ready is False
        assert any("paper" in i.lower() for i in issues)

    def test_check_high_violations(self):
        gate = DeploymentGate()
        report = SecurityReport(overall_score=95.0, risk_level="LOW", is_approved=True, high_violations=3)
        ready, issues = gate.check_deployment_readiness(report, test_coverage=90.0)
        assert ready is False

    def test_not_approved(self):
        gate = DeploymentGate()
        report = SecurityReport(overall_score=95.0, risk_level="LOW", is_approved=False)
        ready, issues = gate.check_deployment_readiness(report, test_coverage=90.0)
        assert ready is False
