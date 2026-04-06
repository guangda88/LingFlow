import pytest
from lingflow.common.sandbox import (
    SkillSandbox,
    SandboxTimeoutError,
    _create_safe_import,
    execute_in_sandbox,
    get_default_sandbox,
)


class TestCreateSafeImport:
    def test_allowed_module(self):
        safe_import = _create_safe_import({"math", "time"})
        import math
        result = safe_import("math")
        assert result is math

    def test_blocked_module(self):
        safe_import = _create_safe_import({"math"})
        with pytest.raises(ImportError, match="not allowed"):
            safe_import("os")

    def test_submodule_base_check(self):
        safe_import = _create_safe_import({"datetime"})
        import datetime
        result = safe_import("datetime")
        assert result is datetime


class TestSkillSandboxValidate:
    def test_validate_safe_code(self):
        sb = SkillSandbox(timeout=5, enable_ast_analysis=True)
        assert sb.validate_code("x = 1 + 2\ny = x * 3\n") is True

    def test_validate_unsafe_code(self):
        sb = SkillSandbox(timeout=5, enable_ast_analysis=True)
        assert sb.validate_code("import os\nos.system('rm -rf /')\n") is False

    def test_validate_syntax_error(self):
        sb = SkillSandbox(timeout=5)
        assert sb.validate_code("def foo(\n") is False

    def test_validate_simple_mode(self):
        sb = SkillSandbox(timeout=5, enable_ast_analysis=False)
        assert sb.validate_code("x = 1\n") is False

    def test_validate_code_with_dangerous_strings(self):
        sb = SkillSandbox(timeout=5, enable_ast_analysis=True)
        assert sb.validate_code("eval('1+1')\n") is False
        assert sb.validate_code("exec('x=1')\n") is False
        assert sb.validate_code("open('file.txt')\n") is False


class TestSkillSandboxExecute:
    def test_execute_simple_function(self):
        sb = SkillSandbox(timeout=10)
        result = sb.execute(lambda x: x * 2, 5)
        assert result == 10

    def test_execute_no_result(self):
        sb = SkillSandbox(timeout=5)

        def no_return():
            pass

        result = sb.execute(no_return)
        assert result is None

    def test_execute_timeout(self):
        sb = SkillSandbox(timeout=0.5)
        import time

        def slow_func():
            time.sleep(5)

        with pytest.raises(SandboxTimeoutError):
            sb.execute(slow_func)

    def test_execute_exception(self):
        sb = SkillSandbox(timeout=5)
        with pytest.raises(ValueError, match="test error"):
            sb.execute(lambda: (_ for _ in ()).throw(ValueError("test error")))


class TestSkillSandboxCode:
    def test_validate_code_simple_fallback(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        assert sb.validate_code("x = 1") is False

    def test_get_security_report(self):
        sb = SkillSandbox(enable_ast_analysis=True)
        report = sb.get_security_report("x = 1 + 2")
        assert "is_safe" in report
        assert report["is_safe"] is True

    def test_get_security_report_no_ast(self):
        sb = SkillSandbox(enable_ast_analysis=False)
        report = sb.get_security_report("x = 1")
        assert "is_safe" in report
        assert report["is_safe"] is False

    def test_get_security_report_unsafe(self):
        sb = SkillSandbox(enable_ast_analysis=True)
        report = sb.get_security_report("import os")
        assert report["is_safe"] is False


class TestConvenienceFunctions:
    def test_get_default_sandbox(self):
        sb1 = get_default_sandbox()
        sb2 = get_default_sandbox()
        assert sb1 is sb2

    def test_execute_in_sandbox(self):
        result = execute_in_sandbox(lambda x: x + 1, 5)
        assert result == 6

    def test_execute_in_sandbox_with_timeout(self):
        result = execute_in_sandbox(lambda x: x * 2, 3, timeout=10)
        assert result == 6


class TestExecuteCode:
    def test_execute_simple_code(self):
        sb = SkillSandbox(timeout=10)
        result = sb.execute_code("x = 1 + 2")
        assert isinstance(result, dict)

    def test_execute_code_syntax_error(self):
        sb = SkillSandbox(timeout=10)
        with pytest.raises(SyntaxError):
            sb.execute_code("if if if")

    def test_execute_code_with_globals(self):
        sb = SkillSandbox(timeout=10)
        result = sb.execute_code("y = x + 1", globals_dict={"x": 10})
        assert isinstance(result, dict)

    def test_execute_code_with_locals(self):
        sb = SkillSandbox(timeout=10)
        result = sb.execute_code("z = 42", locals_dict={})
        assert isinstance(result, dict)

    def test_execute_code_math_allowed(self):
        sb = SkillSandbox(timeout=10)
        result = sb.execute_code(
            "import math\nresult = math.sqrt(16)"
        )
        assert isinstance(result, dict)

    def test_execute_code_unsafe_import_blocked(self):
        sb = SkillSandbox(timeout=10, enable_ast_analysis=False)
        with pytest.raises(Exception):
            sb.execute_code("import os\nos.listdir('.')")

    def test_execute_code_return_values(self):
        sb = SkillSandbox(timeout=10)
        result = sb.execute_code("values = [1, 2, 3]\ntotal = sum(values)")
        assert isinstance(result, dict)


class TestCreateSafeGlobals:
    def test_safe_globals_has_builtins(self):
        sb = SkillSandbox()
        g = sb._create_safe_globals()
        assert "__builtins__" in g

    def test_safe_globals_has_import(self):
        sb = SkillSandbox()
        g = sb._create_safe_globals()
        assert "__import__" in g

    def test_safe_builtins_subset(self):
        sb = SkillSandbox()
        g = sb._create_safe_globals()
        builtins = g["__builtins__"]
        assert "abs" in builtins
        assert "len" in builtins
        assert "str" in builtins
        assert "list" in builtins
        assert "dict" in builtins
        assert "range" in builtins

    def test_dangerous_builtins_excluded(self):
        sb = SkillSandbox()
        g = sb._create_safe_globals()
        builtins = g["__builtins__"]
        assert "open" not in builtins
        assert "exec" not in builtins
        assert "eval" not in builtins
        assert "compile" not in builtins
