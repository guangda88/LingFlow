"""Additional sandbox coverage tests for uncovered lines."""

import pytest

from lingflow.common.sandbox import (
    SkillSandbox,
    _create_safe_import,
)


class TestCreateSafeImport:
    def test_allowed_base_module(self):
        fn = _create_safe_import({"math", "time"})
        mod = fn("math")
        assert hasattr(mod, "sqrt")

    def test_allowed_submodule_dot(self):
        fn = _create_safe_import({"typing"})
        mod = fn("typing")
        assert mod is not None

    def test_disallowed_raises(self):
        fn = _create_safe_import({"math"})
        with pytest.raises(ImportError):
            fn("os")


class TestSimpleValidationFallback:
    def test_simple_validate_safe(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("x = 1 + 2") is True

    def test_simple_validate_os(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("import os") is False

    def test_simple_validate_eval(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("eval('x')") is False

    def test_simple_validate_exec(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("exec('x')") is False

    def test_simple_validate_open(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("open('f')") is False

    def test_simple_validate_sys(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("import sys") is False

    def test_simple_validate_subprocess(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("import subprocess") is False

    def test_simple_validate_compile(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("compile('x','','exec')") is False

    def test_simple_validate_os_dot(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("os.getcwd()") is False

    def test_simple_validate_sys_dot(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("sys.exit()") is False

    def test_simple_validate_subprocess_dot(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("subprocess.run([])") is False

    def test_simple_validate_import(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("__import__('os')") is False

    def test_simple_report_safe(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        report = sb.get_security_report("x = 1")
        assert report["is_safe"] is True
        assert report["total_violations"] == 0

    def test_simple_report_unsafe(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        report = sb.get_security_report("import os")
        assert report["is_safe"] is False
        assert report["total_violations"] == 1
