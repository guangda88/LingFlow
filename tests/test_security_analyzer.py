"""
lingflow 安全分析器测试套件

测试AST-based代码安全分析器的各种检测能力。

测试覆盖：
- 所有违规类型的检测
- 严重程度分级（CRITICAL, HIGH, MEDIUM, LOW）
- 白名单功能
- 误报和漏报场景
- 复杂代码模式
- 沙箱集成
"""

import os
import sys
import unittest

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lingflow.common.security_analyzer import SecurityAnalyzer, SecurityViolation, analyze_code_security, get_security_report


class TestSecurityAnalyzer(unittest.TestCase):
    """SecurityAnalyzer基础功能测试"""

    def setUp(self):
        """设置测试环境"""
        self.allowed_modules = {
            "typing",
            "dataclasses",
            "datetime",
            "math",
            "time",
            "json",
            "random",
        }
        self.analyzer = SecurityAnalyzer(self.allowed_modules)

    def test_safe_code(self):
        """测试安全代码的验证"""
        safe_code = """
x = 1 + 2
y = [1, 2, 3]
result = sum(y)
print(f"Result: {result}")
"""
        violations = self.analyzer.analyze(safe_code)
        self.assertEqual(len(violations), 0)

    def test_syntax_error_detection(self):
        """测试语法错误检测"""
        invalid_code = "def broken(:\n    return 1"
        violations = self.analyzer.analyze(invalid_code)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].severity, "CRITICAL")
        self.assertEqual(violations[0].violation_type, "SYNTAX_ERROR")


class TestForbiddenImportDetection(unittest.TestCase):
    """禁止导入检测测试"""

    def setUp(self):
        """设置测试环境"""
        self.allowed_modules = {"typing", "dataclasses", "datetime"}
        self.analyzer = SecurityAnalyzer(self.allowed_modules)

    def test_os_module_import(self):
        """测试os模块导入检测"""
        code = "import os"
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].violation_type, "FORBIDDEN_IMPORT")
        self.assertIn("os", violations[0].message)

    def test_sys_module_import(self):
        """测试sys模块导入检测"""
        code = "import sys"
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].violation_type, "FORBIDDEN_IMPORT")

    def test_subprocess_module_import(self):
        """测试subprocess模块导入检测"""
        code = "import subprocess"
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].violation_type, "FORBIDDEN_IMPORT")

    def test_from_import_forbidden_module(self):
        """测试from导入禁止模块"""
        code = "from os import path"
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].violation_type, "FORBIDDEN_IMPORT")

    def test_allowed_module_import(self):
        """测试允许的模块导入"""
        code = "import typing"
        violations = self.analyzer.analyze(code)
        self.assertEqual(len(violations), 0)

    def test_from_allowed_module_import(self):
        """测试from允许模块导入"""
        code = "from datetime import datetime"
        violations = self.analyzer.analyze(code)
        self.assertEqual(len(violations), 0)

    def test_future_import_allowed(self):
        """测试__future__导入（应允许）"""
        code = "from __future__ import annotations"
        violations = self.analyzer.analyze(code)
        self.assertEqual(len(violations), 0)


class TestDangerousFunctionDetection(unittest.TestCase):
    """危险函数检测测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_eval_detection(self):
        """测试eval函数检测"""
        code = "result = eval('1 + 1')"
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        eval_violation = next(v for v in violations if v.violation_type == "FORBIDDEN_FUNCTION")
        self.assertIn("eval", eval_violation.message)

    def test_exec_detection(self):
        """测试exec函数检测"""
        code = "exec('print(\"hello\")')"
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        exec_violation = next(v for v in violations if v.violation_type == "FORBIDDEN_FUNCTION")
        self.assertIn("exec", exec_violation.message)

    def test_compile_detection(self):
        """测试compile函数检测"""
        code = "code = compile('1+1', '<string>', 'eval')"
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        compile_violation = next(v for v in violations if v.violation_type == "FORBIDDEN_FUNCTION")
        self.assertIn("compile", compile_violation.message)

    def test_open_detection(self):
        """测试open函数检测"""
        code = "f = open('file.txt', 'r')"
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        open_violation = next(v for v in violations if v.violation_type == "FORBIDDEN_FUNCTION")
        self.assertIn("open", open_violation.message)

    def test___import__detection(self):
        """测试__import__检测"""
        code = "module = __import__('os')"
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        import_violation = next(v for v in violations if v.violation_type == "FORBIDDEN_FUNCTION")
        self.assertIn("__import__", import_violation.message)


class TestDangerousModuleAccess(unittest.TestCase):
    """危险模块访问检测测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_os_system_call(self):
        """测试os.system调用检测"""
        code = """
import os
os.system('ls -la')
"""
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        module_access = next(v for v in violations if v.violation_type == "FORBIDDEN_MODULE_ACCESS")
        self.assertIn("os", module_access.message)

    def test_subprocess_call(self):
        """测试subprocess调用检测"""
        code = """
import subprocess
subprocess.run(['ls', '-la'])
"""
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)

    def test_sys_exit_call(self):
        """测试sys.exit调用检测"""
        code = """
import sys
sys.exit(1)
"""
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)


class TestDangerousAttributeDetection(unittest.TestCase):
    """危险属性访问检测测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test___dict__access(self):
        """测试__dict__属性访问检测"""
        code = """
class MyClass:
    pass

obj = MyClass()
print(obj.__dict__)
"""
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        dict_violation = next(v for v in violations if v.violation_type == "DANGEROUS_ATTRIBUTE")
        self.assertIn("__dict__", dict_violation.message)

    def test___class__access(self):
        """测试__class__属性访问检测"""
        code = """
x = 5
cls = x.__class__
"""
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        class_violation = next(v for v in violations if v.violation_type == "DANGEROUS_ATTRIBUTE")
        self.assertIn("__class__", class_violation.message)


class TestRecursionDetection(unittest.TestCase):
    """递归检测测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_simple_recursion(self):
        """测试简单递归检测"""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 0)
        recursion_violation = next(v for v in violations if v.violation_type == "RECURSION_DETECTED")
        self.assertEqual(recursion_violation.severity, "MEDIUM")

    def test_no_recursion(self):
        """测试非递归函数"""
        code = """
def add(a, b):
    return a + b
"""
        violations = self.analyzer.analyze(code)
        recursion_violations = [v for v in violations if v.violation_type == "RECURSION_DETECTED"]
        self.assertEqual(len(recursion_violations), 0)


class TestLoopDetection(unittest.TestCase):
    """循环检测测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_deep_loop_nesting(self):
        """测试深层循环嵌套检测"""
        code = """
for i in range(10):
    for j in range(10):
        for k in range(10):
            for l in range(10):
                pass
"""
        violations = self.analyzer.analyze(code)
        nesting_violations = [v for v in violations if v.violation_type == "DEEP_NESTING"]
        self.assertGreater(len(nesting_violations), 0)

    def test_while_true_detection(self):
        """测试while True检测"""
        code = """
while True:
    pass
"""
        violations = self.analyzer.analyze(code)
        infinite_loop = next(v for v in violations if v.violation_type == "POTENTIAL_INFINITE_LOOP")
        self.assertEqual(infinite_loop.severity, "HIGH")

    def test_safe_while_loop(self):
        """测试安全的while循环"""
        code = """
x = 10
while x > 0:
    x -= 1
"""
        violations = self.analyzer.analyze(code)
        infinite_loop_violations = [v for v in violations if v.violation_type == "POTENTIAL_INFINITE_LOOP"]
        self.assertEqual(len(infinite_loop_violations), 0)


class TestCodeInjectionDetection(unittest.TestCase):
    """代码注入检测测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_f_string_code_injection(self):
        """测试f-string中的代码注入"""
        code = """
user_input = "__import__('os')"
result = f"{eval(user_input)}"
"""
        violations = self.analyzer.analyze(code)
        injection_violations = [v for v in violations if v.violation_type == "CODE_INJECTION"]
        self.assertGreater(len(injection_violations), 0)

    def test_safe_f_string(self):
        """测试安全的f-string"""
        code = """
name = "World"
result = f"Hello, {name}"
"""
        violations = self.analyzer.analyze(code)
        injection_violations = [v for v in violations if v.violation_type == "CODE_INJECTION"]
        self.assertEqual(len(injection_violations), 0)


class TestStringConcatBypassDetection(unittest.TestCase):
    """字符串拼接绕过检测测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_dangerous_string_concat(self):
        """测试危险字符串拼接"""
        code = """
mod = "__imp"
mod += "ort__('os')"
"""
        violations = self.analyzer.analyze(code)
        bypass_violations = [v for v in violations if v.violation_type == "STRING_CONCAT_BYPASS"]
        self.assertGreater(len(bypass_violations), 0)

    def test_safe_string_concat(self):
        """测试安全字符串拼接"""
        code = """
first_name = "John"
last_name = "Doe"
full_name = first_name + " " + last_name
"""
        violations = self.analyzer.analyze(code)
        bypass_violations = [v for v in violations if v.violation_type == "STRING_CONCAT_BYPASS"]
        self.assertEqual(len(bypass_violations), 0)


class TestBroadExceptionDetection(unittest.TestCase):
    """宽泛异常检测测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_bare_except(self):
        """测试裸except检测"""
        code = """
try:
    risky_operation()
except:
    pass
"""
        violations = self.analyzer.analyze(code)
        bare_except = next(v for v in violations if v.violation_type == "BROAD_EXCEPTION")
        self.assertEqual(bare_except.severity, "MEDIUM")

    def test_specific_exception(self):
        """测试特定异常处理"""
        code = """
try:
    risky_operation()
except ValueError as e:
    print(f"Error: {e}")
"""
        violations = self.analyzer.analyze(code)
        bare_except_violations = [v for v in violations if v.violation_type == "BROAD_EXCEPTION"]
        self.assertEqual(len(bare_except_violations), 0)


class TestSeverityLevels(unittest.TestCase):
    """严重程度分级测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_critical_severity(self):
        """测试CRITICAL严重程度"""
        code = "import os"
        violations = self.analyzer.analyze(code)
        critical_violations = [v for v in violations if v.severity == "CRITICAL"]
        self.assertGreater(len(critical_violations), 0)

    def test_high_severity(self):
        """测试HIGH严重程度"""
        code = "while True: pass"
        violations = self.analyzer.analyze(code)
        high_violations = [v for v in violations if v.severity == "HIGH"]
        self.assertGreater(len(high_violations), 0)

    def test_medium_severity(self):
        """测试MEDIUM严重程度"""
        code = """
def recurse(n):
    return recurse(n)
"""
        violations = self.analyzer.analyze(code)
        medium_violations = [v for v in violations if v.severity == "MEDIUM"]
        self.assertGreater(len(medium_violations), 0)

    def test_low_severity(self):
        """测试LOW严重程度"""
        code = """
for i in range(10):
    for j in range(10):
        for k in range(10):
            for l in range(10):
                pass
"""
        violations = self.analyzer.analyze(code)
        low_violations = [v for v in violations if v.severity == "LOW"]
        self.assertGreater(len(low_violations), 0)


class TestAnalyzeCodeSecurity(unittest.TestCase):
    """analyze_code_security函数测试"""

    def test_safe_code_returns_true(self):
        """测试安全代码返回True"""
        code = """
x = 1 + 2
y = [1, 2, 3]
result = sum(y)
"""
        is_safe, violations = analyze_code_security(code)
        self.assertTrue(is_safe)
        self.assertEqual(len(violations), 0)

    def test_unsafe_code_returns_false(self):
        """测试不安全代码返回False"""
        code = "import os"
        is_safe, violations = analyze_code_security(code)
        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)

    def test_custom_allowed_modules(self):
        """测试自定义允许模块"""
        code = "import typing"
        is_safe, violations = analyze_code_security(code, allowed_modules={"typing"})
        self.assertTrue(is_safe)

    def test_critical_violation_makes_code_unsafe(self):
        """测试CRITICAL违规使代码不安全"""
        code = "eval('1+1')"
        is_safe, violations = analyze_code_security(code)
        self.assertFalse(is_safe)
        critical_violations = [v for v in violations if v.severity == "CRITICAL"]
        self.assertGreater(len(critical_violations), 0)

    def test_high_violation_makes_code_unsafe(self):
        """测试HIGH违规使代码不安全"""
        code = "while True: pass"
        is_safe, violations = analyze_code_security(code)
        self.assertFalse(is_safe)
        high_violations = [v for v in violations if v.severity == "HIGH"]
        self.assertGreater(len(high_violations), 0)


class TestGetSecurityReport(unittest.TestCase):
    """get_security_report函数测试"""

    def test_report_structure(self):
        """测试报告结构"""
        code = "import os"
        report = get_security_report(code)

        self.assertIn("is_safe", report)
        self.assertIn("total_violations", report)
        self.assertIn("by_severity", report)
        self.assertIn("by_type", report)
        self.assertIn("has_recursion", report)

    def test_report_by_severity(self):
        """测试按严重程度分组"""
        code = "import os"
        report = get_security_report(code)

        self.assertIn("CRITICAL", report["by_severity"])
        self.assertIn("HIGH", report["by_severity"])
        self.assertIn("MEDIUM", report["by_severity"])
        self.assertIn("LOW", report["by_severity"])

    def test_report_by_type(self):
        """测试按类型分组"""
        code = "import os"
        report = get_security_report(code)

        self.assertIn("FORBIDDEN_IMPORT", report["by_type"])

    def test_report_has_recursion(self):
        """测试递归检测标志"""
        code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
        report = get_security_report(code)
        self.assertTrue(report["has_recursion"])


class TestComplexCodePatterns(unittest.TestCase):
    """复杂代码模式测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_nested_function_with_recursion(self):
        """测试嵌套函数中的递归"""
        code = """
def outer():
    def inner():
        return inner()
    return inner
"""
        violations = self.analyzer.analyze(code)
        recursion_violations = [v for v in violations if v.violation_type == "RECURSION_DETECTED"]
        self.assertGreater(len(recursion_violations), 0)

    def test_multiple_violations_same_code(self):
        """测试同一代码中的多个违规"""
        code = """
import os
import sys
eval('1+1')
"""
        violations = self.analyzer.analyze(code)
        self.assertGreater(len(violations), 2)

    def test_lambda_expression(self):
        """测试lambda表达式"""
        code = """
f = lambda x: x + 1
"""
        violations = self.analyzer.analyze(code)
        # lambda应该是安全的
        forbidden = [v for v in violations if v.severity in ("CRITICAL", "HIGH")]
        self.assertEqual(len(forbidden), 0)

    def test_list_comprehension(self):
        """测试列表推导式"""
        code = """
squares = [x**2 for x in range(10)]
"""
        violations = self.analyzer.analyze(code)
        # 列表推导式应该是安全的
        forbidden = [v for v in violations if v.severity in ("CRITICAL", "HIGH")]
        self.assertEqual(len(forbidden), 0)

    def test_with_statement(self):
        """测试with语句"""
        code = """
with open('file.txt', 'r') as f:
    content = f.read()
"""
        violations = self.analyzer.analyze(code)
        # open应该被检测为危险
        self.assertGreater(len(violations), 0)


class TestSecurityViolation(unittest.TestCase):
    """SecurityViolation类测试"""

    def test_violation_to_dict(self):
        """测试转换为字典"""
        violation = SecurityViolation(
            severity="CRITICAL",
            violation_type="FORBIDDEN_IMPORT",
            message='Import of module "os" is not allowed',
            line=10,
            col_offset=5,
        )
        result = violation.to_dict()

        self.assertEqual(result["severity"], "CRITICAL")
        self.assertEqual(result["violation_type"], "FORBIDDEN_IMPORT")
        self.assertEqual(result["message"], 'Import of module "os" is not allowed')
        self.assertEqual(result["line"], 10)
        self.assertEqual(result["col_offset"], 5)


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_empty_code(self):
        """测试空代码"""
        violations = self.analyzer.analyze("")
        self.assertEqual(len(violations), 0)

    def test_only_whitespace(self):
        """测试只有空白字符"""
        violations = self.analyzer.analyze("   \n\t\n   ")
        self.assertEqual(len(violations), 0)

    def test_only_comments(self):
        """测试只有注释"""
        code = """
# This is a comment
# Another comment
"""
        violations = self.analyzer.analyze(code)
        self.assertEqual(len(violations), 0)

    def test_very_long_code(self):
        """测试非常长的代码"""
        code = "\n".join([f"x{i} = {i}" for i in range(1000)])
        violations = self.analyzer.analyze(code)
        self.assertEqual(len(violations), 0)


class TestFalseNegativeScenarios(unittest.TestCase):
    """漏报场景测试（应该检测但可能漏报的场景）"""

    def setUp(self):
        """设置测试环境"""
        self.analyzer = SecurityAnalyzer()

    def test_dynamic_import_via_getattr(self):
        """测试通过getattr动态导入（可能漏报）"""
        code = """
mod = __import__('builtins')
imp = getattr(mod, '__import__')
os_module = imp('os')
"""
        violations = self.analyzer.analyze(code)
        # __import__应该被检测
        self.assertGreater(len(violations), 0)

    def test_obfuscated_eval(self):
        """测试混淆的eval调用（可能漏报）"""
        code = """
ev = 'eval'
getattr(builtins, ev)('1+1')
"""
        violations = self.analyzer.analyze(code)
        # getattr访问builtins应该被检测
        self.assertGreater(len(violations), 0)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestForbiddenImportDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestDangerousFunctionDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestDangerousModuleAccess))
    suite.addTests(loader.loadTestsFromTestCase(TestDangerousAttributeDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestRecursionDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestLoopDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeInjectionDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestStringConcatBypassDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestBroadExceptionDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestSeverityLevels))
    suite.addTests(loader.loadTestsFromTestCase(TestAnalyzeCodeSecurity))
    suite.addTests(loader.loadTestsFromTestCase(TestGetSecurityReport))
    suite.addTests(loader.loadTestsFromTestCase(TestComplexCodePatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityViolation))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestFalseNegativeScenarios))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 返回测试结果
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
