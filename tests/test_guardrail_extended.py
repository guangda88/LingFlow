"""Extended guardrail validation tests for additional coverage."""

import pytest
from unittest.mock import patch

from lingflow.guardrail import (
    ValidationLevel,
    Severity,
    Violation,
    ValidationResult,
    SecurityReport,
    GuardrailValidator,
    DeploymentGate,
)


class TestGuardrailValidatorPolicyPatterns:
    @pytest.fixture
    def validator(self):
        return GuardrailValidator()

    def test_api_key_detection(self, validator):
        code = 'api_key = "abcdefghijklmnopqrstuvwxyz123456"\n'
        result = validator.validate_policy(code, "test.py")
        violations = [v for v in result.violations if "api_key" in v.code.lower()]
        assert len(violations) > 0

    def test_access_token_detection(self, validator):
        code = 'access_token = "abcdefghijklmnopqrstuvwxyz123456"\n'
        result = validator.validate_policy(code, "test.py")
        assert result.is_passed is False

    def test_sql_injection_execute(self, validator):
        code = 'cursor.execute("SELECT * FROM users WHERE id=" + user_id)\n'
        result = validator.validate_policy(code, "test.py")
        assert result.is_passed is False

    def test_sql_injection_query(self, validator):
        code = 'db.query("SELECT * FROM t WHERE id=" + val)\n'
        result = validator.validate_policy(code, "test.py")
        assert result.is_passed is False

    def test_xss_dangerouslySetInnerHTML(self, validator):
        code = 'div = <div dangerouslySetInnerHTML={html} />\n'
        result = validator.validate_policy(code, "test.jsx")
        violations = [v for v in result.violations if "xss" in v.code.lower()]
        assert len(violations) > 0

    def test_xss_innerHTML(self, validator):
        code = 'element.innerHTML = "<b>" + userInput\n'
        result = validator.validate_policy(code, "test.js")
        assert any("xss" in v.code.lower() for v in result.violations)

    def test_xss_document_write(self, validator):
        code = 'document.write(user_input)\n'
        result = validator.validate_policy(code, "test.js")
        assert any("xss" in v.code.lower() for v in result.violations)

    def test_weak_crypto_md5(self, validator):
        code = 'hash = MD5(data)\n'
        result = validator.validate_policy(code, "test.py")
        assert any("weak_crypto" in v.code.lower() for v in result.violations)

    def test_weak_crypto_sha1(self, validator):
        code = 'h = SHA1(data)\n'
        result = validator.validate_policy(code, "test.py")
        assert any("weak_crypto" in v.code.lower() for v in result.violations)

    def test_weak_crypto_des(self, validator):
        code = 'encrypted = DES(key)\n'
        result = validator.validate_policy(code, "test.py")
        assert any("weak_crypto" in v.code.lower() for v in result.violations)

    def test_weak_crypto_rc4(self, validator):
        code = 'cipher = RC4(key)\n'
        result = validator.validate_policy(code, "test.py")
        assert any("weak_crypto" in v.code.lower() for v in result.violations)

    def test_debug_info_console_log_password(self, validator):
        code = 'console.log("password: " + pwd)\n'
        result = validator.validate_policy(code, "test.js")
        assert any("debug_info" in v.code.lower() for v in result.violations)

    def test_debug_info_print_password(self, validator):
        code = 'print("password is " + password)\n'
        result = validator.validate_policy(code, "test.py")
        assert any("debug_info" in v.code.lower() for v in result.violations)

    def test_debug_info_pprint_token(self, validator):
        code = 'pprint(token_data)\n'
        result = validator.validate_policy(code, "test.py")
        assert any("debug_info" in v.code.lower() for v in result.violations)

    def test_exec_usage_detection(self, validator):
        code = 'exec("print(1)")\n'
        result = validator.validate_policy(code, "test.py")
        assert result.is_passed is False

    def test_double_slash_comment_skipped(self, validator):
        code = '// eval("something")\n'
        result = validator.validate_policy(code, "test.js")
        assert result.is_passed is True

    def test_pwd_hardcoded(self, validator):
        code = 'pwd = "my_super_secret_password"\n'
        result = validator.validate_policy(code, "test.py")
        assert result.is_passed is False

    def test_secret_hardcoded(self, validator):
        code = 'secret = "a1b2c3d4e5f6g7h8"\n'
        result = validator.validate_policy(code, "test.py")
        assert result.is_passed is False

    def test_sql_injection_format(self, validator):
        code = 'query = format("SELECT * FROM users WHERE id={0}", user_id)\n'
        result = validator.validate_policy(code, "test.py")
        assert any("sql_injection" in v.code.lower() for v in result.violations)

    def test_multiple_violations_penalties(self, validator):
        code = 'api_key = "a" * 40\nexec("code")\n'
        result = validator.validate_policy(code, "test.py")
        assert result.score < 100.0


class TestGuardrailValidateSemantics:
    @pytest.fixture
    def validator(self):
        return GuardrailValidator()

    def test_exec_semantic_detection(self, validator):
        code = 'exec("os.system(\'rm -rf /\')")\n'
        result = validator.validate_semantics(code, "test.py")
        assert any(v.code == "DANGEROUS_EXEC" for v in result.violations)

    def test_eval_semantic_detection(self, validator):
        code = 'eval("1 + 1")\n'
        result = validator.validate_semantics(code, "test.py")
        assert any(v.code == "DANGEROUS_EXEC" for v in result.violations)

    def test_no_docstring_detection(self, validator):
        code = "def public_func():\n    pass\n"
        result = validator.validate_semantics(code, "test.py")
        assert any(v.code == "NO_DOCSTRING" for v in result.violations)

    def test_private_func_no_docstring_ok(self, validator):
        code = "def _private_func():\n    pass\n"
        result = validator.validate_semantics(code, "test.py")
        assert not any(v.code == "NO_DOCSTRING" for v in result.violations)

    def test_documented_func_ok(self, validator):
        code = 'def foo():\n    """Docstring."""\n    pass\n'
        result = validator.validate_semantics(code, "test.py")
        assert not any(v.code == "NO_DOCSTRING" for v in result.violations)


class TestDeploymentDecision:
    @pytest.fixture
    def validator(self):
        return GuardrailValidator()

    def test_auto_approve_high_score(self, validator):
        report = SecurityReport(overall_score=85.0, risk_level="LOW", is_approved=False)
        assert validator._make_deployment_decision(report) is True

    def test_reject_very_low_score(self, validator):
        report = SecurityReport(overall_score=-5.0, risk_level="CRITICAL", is_approved=False)
        assert validator._make_deployment_decision(report) is False

    def test_manual_review_no_critical(self, validator):
        report = SecurityReport(overall_score=55.0, risk_level="MEDIUM", is_approved=False, critical_violations=0)
        assert validator._make_deployment_decision(report) is True

    def test_manual_review_with_critical(self, validator):
        report = SecurityReport(overall_score=55.0, risk_level="MEDIUM", is_approved=False, critical_violations=1)
        assert validator._make_deployment_decision(report) is False

    def test_reject_medium_risk(self, validator):
        report = SecurityReport(overall_score=45.0, risk_level="HIGH", is_approved=False)
        assert validator._make_deployment_decision(report) is False


class TestGenerateReportDetails:
    @pytest.fixture
    def validator(self):
        return GuardrailValidator()

    def test_report_with_violations(self, validator):
        code = 'eval("1+1")\n'
        report = validator.validate_agcef(code, "test.py")
        text = validator.generate_report(report)
        assert "Violations" in text
        assert "eval_usage" in text.lower() or "DANGEROUS_EXEC" in text

    def test_report_with_line_number_and_cwe(self, validator):
        v = Violation(
            level=ValidationLevel.POLICY,
            severity=Severity.HIGH,
            code="TEST_CODE",
            description="test",
            location="test.py",
            line_number=10,
            suggestion="Fix it",
            cwe_id="CWE-123",
        )
        report = SecurityReport(overall_score=90.0, risk_level="LOW", is_approved=True)
        report.validation_results[ValidationLevel.POLICY] = ValidationResult(
            level=ValidationLevel.POLICY, is_passed=False, violations=[v]
        )
        text = validator.generate_report(report)
        assert "test.py:10" in text
        assert "CWE-123" in text
        assert "Fix it" in text

    def test_report_without_line_number(self, validator):
        v = Violation(
            level=ValidationLevel.POLICY,
            severity=Severity.MEDIUM,
            code="TEST",
            description="test",
            location="test.py",
        )
        report = SecurityReport(overall_score=90.0, risk_level="LOW", is_approved=True)
        report.validation_results[ValidationLevel.POLICY] = ValidationResult(
            level=ValidationLevel.POLICY, is_passed=False, violations=[v]
        )
        text = validator.generate_report(report)
        assert "Location: test.py" in text

    def test_report_clean_no_violations(self, validator):
        report = SecurityReport(overall_score=100.0, risk_level="LOW", is_approved=True)
        report.validation_results[ValidationLevel.SYNTAX] = ValidationResult(
            level=ValidationLevel.SYNTAX, is_passed=True
        )
        text = validator.generate_report(report)
        assert "No violations" in text


class TestDeploymentGateExtended:
    def test_all_pass(self):
        gate = DeploymentGate()
        report = SecurityReport(overall_score=95.0, risk_level="LOW", is_approved=True)
        ready, issues = gate.check_deployment_readiness(report, test_coverage=90.0)
        assert ready is True
        assert issues == []

    def test_high_violations_block(self):
        gate = DeploymentGate()
        report = SecurityReport(overall_score=95.0, risk_level="LOW", is_approved=True, high_violations=5)
        ready, issues = gate.check_deployment_readiness(report, test_coverage=90.0)
        assert ready is False
        assert any("high" in i.lower() for i in issues)


class TestPolicySuggestion:
    def test_all_known_categories(self):
        validator = GuardrailValidator()
        categories = [
            "hardcoded_passwords",
            "hardcoded_api_keys",
            "sql_injection_patterns",
            "xss_patterns",
            "weak_crypto",
            "debug_info",
            "eval_usage",
        ]
        for cat in categories:
            suggestion = validator._get_policy_suggestion(cat)
            assert len(suggestion) > 0

    def test_unknown_category(self):
        validator = GuardrailValidator()
        assert validator._get_policy_suggestion("nonexistent") == "Review and fix security issue"


class TestValidateAGCEFIntegration:
    @pytest.fixture
    def validator(self):
        return GuardrailValidator()

    def test_agcef_with_syntax_fail_skips_policy(self, validator):
        code = "def bad(\n"
        report = validator.validate_agcef(code, "bad.py")
        policy = report.validation_results[ValidationLevel.POLICY]
        assert policy.is_passed is False

    def test_agcef_with_policy_fail_skips_semantics(self, validator):
        code = 'eval("1+1")\n'
        report = validator.validate_agcef(code, "evil.py")
        semantics = report.validation_results[ValidationLevel.SEMANTICS]
        assert semantics.is_passed is False

    def test_agcef_counts_violations(self, validator):
        code = 'eval("1")\nexec("2")\n'
        report = validator.validate_agcef(code, "test.py")
        assert report.total_violations > 0

    def test_agcef_execution_time(self, validator):
        code = "x = 1\n"
        report = validator.validate_agcef(code, "test.py")
        assert report.execution_time >= 0
