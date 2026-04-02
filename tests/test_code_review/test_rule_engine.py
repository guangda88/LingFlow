"""
规则引擎单元测试

测试 Rule 类和 RuleEngine 类的功能
"""

import ast
import pytest
from pathlib import Path
from lingflow.code_review.core.rule_engine import RuleEngine
from lingflow.code_review.core.rules.models import (
    Rule,
    RuleEngineError,
    RuleNotFoundError,
    RuleValidationError,
    RuleResult,
)
from lingflow.code_review.core.severity import Severity


def _make_rule(rule_id="TEST001", name="test_rule", category="test", severity=Severity.LOW):
    def dummy_check(content, tree, path):
        return None
    return Rule(
        id=rule_id,
        name=name,
        category=category,
        check_func=dummy_check,
        severity=severity,
        suggestion_template="Test suggestion",
    )


class TestRule:
    """Rule 类测试"""

    def test_rule_creation(self):
        rule = _make_rule("TEST001", "test_rule", "test")
        assert rule.id == "TEST001"
        assert rule.name == "test_rule"
        assert rule.category == "test"
        assert rule.severity == Severity.LOW
        assert rule.enabled is True

    def test_rule_default_category(self):
        rule = _make_rule("TEST002")
        rule_defaulted = Rule(
            id="TEST002b",
            name="test_rule",
            category="",
            check_func=lambda c, t, p: None,
            severity=Severity.LOW,
            suggestion_template="Test",
        )
        assert rule_defaulted.category == "general"

    def test_rule_validation_success(self):
        rule = _make_rule("TEST003")
        assert rule.validate() is True

    def test_rule_validation_empty_id(self):
        with pytest.raises(ValueError):
            Rule(
                id="",
                name="test_rule",
                category="test",
                check_func=lambda c, t, p: None,
                severity=Severity.LOW,
                suggestion_template="Test",
            )


class TestRuleEngine:
    """RuleEngine 类测试"""

    def test_engine_initialization(self):
        engine = RuleEngine()
        assert engine.loader is not None

    def test_register_rule(self):
        engine = RuleEngine()
        rule = _make_rule("CUSTOM001", "custom_rule", "test", Severity.MEDIUM)
        engine.register_rule(rule)
        retrieved = engine.get_rule("CUSTOM001")
        assert retrieved is not None
        assert retrieved.name == "custom_rule"

    def test_register_invalid_rule(self):
        with pytest.raises(ValueError):
            Rule(
                id="",
                name="invalid",
                category="test",
                check_func=lambda c, t, p: None,
                severity=Severity.LOW,
                suggestion_template="Test",
            )

    def test_unregister_rule(self):
        engine = RuleEngine()
        rule = _make_rule("TEMP001")
        engine.register_rule(rule)
        assert engine.get_rule("TEMP001") is not None

        result = engine.unregister_rule("TEMP001")
        assert result is True
        assert engine.get_rule("TEMP001") is None or not engine.get_rule("TEMP001").enabled

    def test_unregister_nonexistent_rule(self):
        engine = RuleEngine()
        result = engine.unregister_rule("NONEXISTENT")
        assert result is False

    def test_get_nonexistent_rule(self):
        engine = RuleEngine()
        rule = engine.get_rule("NONEXISTENT")
        assert rule is None

    def test_list_rules_all(self):
        engine = RuleEngine()
        rules = engine.list_rules()
        assert isinstance(rules, list)

    def test_list_rules_by_category(self):
        engine = RuleEngine()
        rule = _make_rule("SEC_TEST", "sec_rule", "security", Severity.HIGH)
        engine.register_rule(rule)
        security_rules = engine.list_rules(category="security")
        assert all(r.category == "security" for r in security_rules)

    def test_enable_disable_rule(self):
        engine = RuleEngine()
        rule = _make_rule("ENABLE_TEST")
        engine.register_rule(rule)
        engine.disable_rule("ENABLE_TEST")
        retrieved = engine.get_rule("ENABLE_TEST")
        assert retrieved is not None
        assert retrieved.enabled is False

        engine.enable_rule("ENABLE_TEST")
        retrieved = engine.get_rule("ENABLE_TEST")
        assert retrieved is not None
        assert retrieved.enabled is True

    def test_enable_nonexistent_rule(self):
        engine = RuleEngine()
        result = engine.enable_rule("NONEXISTENT")
        assert result is False

    def test_disable_nonexistent_rule(self):
        engine = RuleEngine()
        result = engine.disable_rule("NONEXISTENT")
        assert result is False


class TestRuleCheckFunctions:
    """规则检查函数测试 — 测试 Rule 的 check_func 机制"""

    def test_eval_detection_check_func(self):
        def check_eval(content, tree, path):
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id == "eval":
                        return "使用 eval() 存在安全风险"
            return None

        content = "x = eval(user_input)\ny = 1"
        tree = ast.parse(content)
        assert check_eval(content, tree, Path("test.py")) is not None
        assert "eval" in check_eval(content, tree, Path("test.py")).lower()

        content_comment = "# x = eval(input)\ny = 1"
        tree_comment = ast.parse(content_comment)
        assert check_eval(content_comment, tree_comment, Path("test.py")) is None

    def test_exec_detection_check_func(self):
        def check_exec(content, tree, path):
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id == "exec":
                        return "使用 exec() 存在安全风险"
            return None

        content = "exec(code)"
        tree = ast.parse(content)
        result = check_exec(content, tree, Path("test.py"))
        assert result is not None
        assert "exec" in result.lower()

    def test_hardcoded_secrets_check_func(self):
        secret_names = {"password", "secret", "api_key", "token", "passwd"}

        def check_secrets(content, tree, path):
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            if target.id.lower() in secret_names:
                                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                                    return f"检测到硬编码敏感信息: {target.id}"
            return None

        content = "password = 'secret123'\n"
        tree = ast.parse(content)
        result = check_secrets(content, tree, Path("test.py"))
        assert result is not None
        assert "敏感信息" in result

        content_env = "password = os.environ.get('PASSWORD')\n"
        tree_env = ast.parse(content_env)
        assert check_secrets(content_env, tree_env, Path("test.py")) is None

    def test_sql_injection_check_func(self):
        import re
        def check_sql(content, tree, path):
            pattern = r'execute\s*\(\s*["\'].*?\+\s*\w+'
            if re.search(pattern, content):
                return "检测到SQL注入风险: 字符串拼接SQL"
            return None

        content = 'cursor.execute("SELECT * FROM users WHERE id = " + user_id)\n'
        result = check_sql(content, None, Path("test.py"))
        assert result is not None
        assert "SQL" in result or "注入" in result

    def test_nested_loops_check_func(self):
        def count_nested_loops(node, depth=0):
            max_depth = depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.For, ast.While)):
                    max_depth = max(max_depth, count_nested_loops(child, depth + 1))
                else:
                    max_depth = max(max_depth, count_nested_loops(child, depth))
            return max_depth

        def check_nested(content, tree, path):
            max_depth = count_nested_loops(tree)
            if max_depth >= 4:
                return f"嵌套循环层数过深: {max_depth} 层"
            return None

        content = """
for i in range(10):
    for j in range(10):
        for k in range(10):
            for l in range(10):
                pass
"""
        tree = ast.parse(content)
        result = check_nested(content, tree, Path("test.py"))
        assert result is not None
        assert "4" in result

    def test_import_count_check_func(self):
        def check_imports(content, tree, path):
            imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
            if len(imports) > 20:
                return f"导入过多: {len(imports)} 个导入语句"
            return None

        imports = "\n".join([f"import module{i}" for i in range(25)])
        content = f"{imports}\n\ndef foo(): pass"
        tree = ast.parse(content)
        result = check_imports(content, tree, Path("test.py"))
        assert result is not None
        assert "导入过多" in result


class TestRunRules:
    """run_rules 方法测试"""

    def setup_method(self):
        self.engine = RuleEngine()
        self.test_file = Path("test.py")

    def test_run_rules_with_registered_rule(self):
        def check_eval(content, tree, path):
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == "eval":
                        return "使用 eval() 存在安全风险"
            return None

        rule = Rule(
            id="SEC001",
            name="eval_usage",
            category="security",
            check_func=check_eval,
            severity=Severity.HIGH,
            suggestion_template="避免使用 eval()",
        )
        self.engine.register_rule(rule)

        content = 'x = eval("1 + 1")\n'
        tree = ast.parse(content)
        results = self.engine.run_rules(content, tree, self.test_file)
        assert len(results) > 0
        assert isinstance(results[0], RuleResult)

    def test_run_rules_no_issues(self):
        def noop_check(content, tree, path):
            return None

        rule = Rule(
            id="NOOP001",
            name="noop",
            category="test",
            check_func=noop_check,
            severity=Severity.LOW,
            suggestion_template="No suggestion",
        )
        self.engine.register_rule(rule)

        content = "x = 1\n"
        tree = ast.parse(content)
        results = self.engine.run_rules(content, tree, self.test_file)
        assert isinstance(results, list)

    def test_run_rules_with_syntax_error_content(self):
        content = "def foo(\n"
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        results = self.engine.run_rules(content, tree, self.test_file)
        assert isinstance(results, list)
