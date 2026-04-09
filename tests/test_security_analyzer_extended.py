"""Extended tests for lingflow.common.security_analyzer - additional edge cases"""

import pytest

from lingflow.common.security_analyzer import (
    SecurityAnalyzer,
    SecurityViolation,
    analyze_code_security,
    get_security_report,
)


class TestSecurityViolationInit:
    def test_all_fields(self):
        v = SecurityViolation(severity="CRITICAL", violation_type="TEST", message="test msg", line=10, col_offset=5)
        assert v.severity == "CRITICAL"
        assert v.violation_type == "TEST"
        assert v.message == "test msg"
        assert v.line == 10
        assert v.col_offset == 5


class TestAnalyzerInit:
    def test_default_allowed_modules(self):
        a = SecurityAnalyzer()
        assert "typing" in a.allowed_modules
        assert "json" in a.allowed_modules
        assert "collections" in a.allowed_modules

    def test_custom_allowed_modules(self):
        a = SecurityAnalyzer(allowed_modules={"mymod"})
        assert a.allowed_modules == {"mymod"}

    def test_initial_state(self):
        a = SecurityAnalyzer()
        assert a.function_depth == 0
        assert a.loop_depth == 0
        assert a.has_recursion is False
        assert a.violations == []


class TestAdditionalImportChecks:
    def test_submodule_import_allowed(self):
        a = SecurityAnalyzer(allowed_modules={"os"})
        violations = a.analyze("import os.path")
        assert len(violations) == 0

    def test_submodule_import_forbidden(self):
        a = SecurityAnalyzer(allowed_modules={"typing"})
        violations = a.analyze("import os.path")
        assert len(violations) > 0

    def test_from_import_none_module(self):
        a = SecurityAnalyzer()
        code = "from . import something"
        violations = a.analyze(code)
        import_violations = [v for v in violations if v.violation_type == "FORBIDDEN_IMPORT"]
        assert len(import_violations) == 0

    def test_from_import_allowed_decimal(self):
        a = SecurityAnalyzer()
        violations = a.analyze("from decimal import Decimal")
        assert len(violations) == 0

    def test_from_import_allowed_fractions(self):
        a = SecurityAnalyzer()
        violations = a.analyze("from fractions import Fraction")
        assert len(violations) == 0


class TestAdditionalDangerousBuiltins:
    def test_globals_detection(self):
        a = SecurityAnalyzer()
        violations = a.analyze("g = globals()")
        assert any(v.violation_type == "FORBIDDEN_FUNCTION" and "globals" in v.message for v in violations)

    def test_locals_detection(self):
        a = SecurityAnalyzer()
        violations = a.analyze("l = locals()")
        assert any(v.violation_type == "FORBIDDEN_FUNCTION" and "locals" in v.message for v in violations)

    def test_vars_detection(self):
        a = SecurityAnalyzer()
        violations = a.analyze("v = vars()")
        assert any(v.violation_type == "FORBIDDEN_FUNCTION" for v in violations)

    def test_dir_detection(self):
        a = SecurityAnalyzer()
        violations = a.analyze("d = dir()")
        assert any(v.violation_type == "FORBIDDEN_FUNCTION" for v in violations)

    def test_getattr_detection(self):
        a = SecurityAnalyzer()
        violations = a.analyze("getattr(obj, 'x')")
        assert any(v.violation_type == "FORBIDDEN_FUNCTION" and "getattr" in v.message for v in violations)

    def test_setattr_detection(self):
        a = SecurityAnalyzer()
        violations = a.analyze("setattr(obj, 'x', 1)")
        assert any(v.violation_type == "FORBIDDEN_FUNCTION" for v in violations)

    def test_delattr_detection(self):
        a = SecurityAnalyzer()
        violations = a.analyze("delattr(obj, 'x')")
        assert any(v.violation_type == "FORBIDDEN_FUNCTION" for v in violations)

    def test_hasattr_detection(self):
        a = SecurityAnalyzer()
        violations = a.analyze("hasattr(obj, 'x')")
        assert not any(v.violation_type == "FORBIDDEN_FUNCTION" for v in violations)

    def test_input_detection(self):
        a = SecurityAnalyzer()
        violations = a.analyze("x = input('prompt')")
        assert any(v.violation_type == "FORBIDDEN_FUNCTION" and "input" in v.message for v in violations)


class TestAdditionalModuleAccess:
    def test_socket_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("socket.connect()")
        assert any(v.violation_type == "FORBIDDEN_MODULE_ACCESS" for v in violations)

    def test_pickle_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("pickle.loads(data)")
        assert any(v.violation_type == "FORBIDDEN_MODULE_ACCESS" for v in violations)

    def test_shutil_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("shutil.rmtree('/tmp')")
        assert any(v.violation_type == "FORBIDDEN_MODULE_ACCESS" for v in violations)

    def test_importlib_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("importlib.import_module('os')")
        assert any(v.violation_type == "FORBIDDEN_MODULE_ACCESS" for v in violations)

    def test_types_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("types.ModuleType('x')")
        assert any(v.violation_type == "FORBIDDEN_MODULE_ACCESS" for v in violations)


class TestAdditionalAttributeChecks:
    def test_bases_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("x.__bases__")
        assert any(v.violation_type == "DANGEROUS_ATTRIBUTE" for v in violations)

    def test_subclasses_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("x.__subclasses__()")
        assert any(v.violation_type == "DANGEROUS_ATTRIBUTE" for v in violations)

    def test_mro_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("x.__mro__")
        assert any(v.violation_type == "DANGEROUS_ATTRIBUTE" for v in violations)

    def test_code_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("func.__code__")
        assert any(v.violation_type == "DANGEROUS_ATTRIBUTE" for v in violations)

    def test_globals_attr_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("func.__globals__")
        assert any(v.violation_type == "DANGEROUS_ATTRIBUTE" for v in violations)

    def test_closure_access(self):
        a = SecurityAnalyzer()
        violations = a.analyze("func.__closure__")
        assert any(v.violation_type == "DANGEROUS_ATTRIBUTE" for v in violations)


class TestStringConcatBinOp:
    def test_binop_concat_dangerous(self):
        a = SecurityAnalyzer()
        code = 'x = "__imp" + "ort__(\'os\')"'
        violations = a.analyze(code)
        assert any(v.violation_type == "STRING_CONCAT_BYPASS" for v in violations)

    def test_binop_concat_safe(self):
        a = SecurityAnalyzer()
        code = 'x = "hello" + " world"'
        violations = a.analyze(code)
        assert not any(v.violation_type == "STRING_CONCAT_BYPASS" for v in violations)

    def test_augassign_concat_dangerous(self):
        a = SecurityAnalyzer()
        code = 'x = " "\nx += "eval(1+1)"'
        violations = a.analyze(code)
        assert any(v.violation_type == "STRING_CONCAT_BYPASS" for v in violations)

    def test_augassign_concat_safe(self):
        a = SecurityAnalyzer()
        code = 'x = "hello"\nx += " world"'
        violations = a.analyze(code)
        assert not any(v.violation_type == "STRING_CONCAT_BYPASS" for v in violations)

    def test_augassign_non_add(self):
        a = SecurityAnalyzer()
        code = "x = 5\nx -= 3"
        violations = a.analyze(code)
        assert not any(v.violation_type == "STRING_CONCAT_BYPASS" for v in violations)


class TestFStringInjection:
    def test_safe_fstring_with_variable(self):
        a = SecurityAnalyzer()
        code = 'x = "world"\nresult = f"hello {x}"'
        violations = a.analyze(code)
        assert not any(v.violation_type == "CODE_INJECTION" for v in violations)

    def test_fstring_with_eval_injection(self):
        a = SecurityAnalyzer()
        code = "result = f\"{eval('1+1')}\""
        violations = a.analyze(code)
        assert any(v.violation_type == "CODE_INJECTION" for v in violations)


class TestTryExcept:
    def test_try_with_handlers(self):
        a = SecurityAnalyzer()
        code = "try:\n    x = 1\nexcept ValueError:\n    pass"
        violations = a.analyze(code)
        assert not any(v.violation_type == "BROAD_EXCEPTION" for v in violations)

    def test_try_no_handlers(self):
        a = SecurityAnalyzer()
        code = "try:\n    x = 1\nfinally:\n    pass"
        violations = a.analyze(code)
        broad = [v for v in violations if v.violation_type == "BROAD_EXCEPTION"]
        assert len(broad) == 0


class TestAnalyzeCodeSecurityEdge:
    def test_only_medium_violations_still_safe(self):
        code = """
def recurse(n):
    return recurse(n)
"""
        is_safe, violations = analyze_code_security(code)
        assert is_safe is True
        assert any(v.severity == "MEDIUM" for v in violations)

    def test_safe_code_no_violations(self):
        code = "x = abs(-1) + max(1, 2)"
        is_safe, violations = analyze_code_security(code)
        assert is_safe is True
        assert len(violations) == 0


class TestGetSecurityReportEdge:
    def test_no_violations(self):
        report = get_security_report("x = 1")
        assert report["is_safe"] is True
        assert report["total_violations"] == 0
        assert report["has_recursion"] is False

    def test_multiple_types(self):
        code = "import os\nimport sys\neval('1')"
        report = get_security_report(code)
        assert report["is_safe"] is False
        assert report["total_violations"] > 0
        assert "FORBIDDEN_IMPORT" in report["by_type"]
        assert "FORBIDDEN_FUNCTION" in report["by_type"]

    def test_by_severity_counts(self):
        code = "import os\neval('1')"
        report = get_security_report(code)
        assert len(report["by_severity"]["CRITICAL"]) >= 2
