"""
lingflow 增强的沙箱安全验证模块

使用AST（抽象语法树）进行深度代码静态分析，
检测潜在的安全漏洞和危险操作。

安全检查：
- AST分析检测危险操作
- 导入白名单验证
- 危险函数调用检测
- 代码复杂度分析
- 递归深度检测
- 循环检测
- 代码注入检测
- 字节码操作检测
"""

import ast
from typing import Any, Dict, List, Optional, Set, Tuple


class SecurityViolation:
    """安全违规"""

    def __init__(self, severity: str, violation_type: str, message: str, line: int, col_offset: int):
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.violation_type = violation_type
        self.message = message
        self.line = line
        self.col_offset = col_offset

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "severity": self.severity,
            "violation_type": self.violation_type,
            "message": self.message,
            "line": self.line,
            "col_offset": self.col_offset,
        }


class SecurityAnalyzer(ast.NodeVisitor):
    """AST安全分析器"""

    def __init__(self, allowed_modules: Optional[Set[str]] = None):
        self.violations: List[SecurityViolation] = []
        self.allowed_modules = allowed_modules or {
            "typing",
            "dataclasses",
            "datetime",
            "math",
            "time",
            "json",
            "random",
            "decimal",
            "fractions",
            "collections",
        }
        # 预处理：为带点的模块（如 os.path）提取 base module
        # 将 os.path → os 也视为允许
        self._allowed_base_modules = set()
        for mod in self.allowed_modules:
            if "." in mod:
                base = mod.split(".")[0]
                self._allowed_base_modules.add(base)
        self.function_depth = 0
        self.loop_depth = 0
        self.has_recursion = False

    def analyze(self, code: str) -> List[SecurityViolation]:
        """分析代码并返回违规列表"""
        try:
            tree = ast.parse(code)
            self.visit(tree)
        except SyntaxError as e:
            self.violations.append(
                SecurityViolation(
                    severity="CRITICAL",
                    violation_type="SYNTAX_ERROR",
                    message=f"Syntax error: {e.msg}",
                    line=e.lineno or 0,
                    col_offset=e.offset or 0,
                )
            )
        return self.violations

    def _is_module_allowed(self, module_name: str) -> bool:
        """检查模块是否在白名单中（支持精确匹配和子模块匹配）"""
        if module_name in self.allowed_modules:
            return True
        if "." in module_name:
            base = module_name.split(".")[0]
            if base in self.allowed_modules:
                return True
        return False

    def visit_Import(self, node: ast.Import) -> None:
        """检查导入语句"""
        for alias in node.names:
            module_name = alias.name
            if not self._is_module_allowed(module_name):
                self.violations.append(
                    SecurityViolation(
                        severity="CRITICAL",
                        violation_type="FORBIDDEN_IMPORT",
                        message=f'Import of module "{module_name}" is not allowed',
                        line=node.lineno,
                        col_offset=node.col_offset,
                    )
                )

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """检查from导入语句"""
        if node.module:
            module_name = node.module

            # 特殊检查：from __future__ imports（优先检查）
            if module_name == "__future__":
                self.generic_visit(node)
                return

            if not self._is_module_allowed(module_name):
                self.violations.append(
                    SecurityViolation(
                        severity="CRITICAL",
                        violation_type="FORBIDDEN_IMPORT",
                        message=f'Import from module "{module_name}" is not allowed',
                        line=node.lineno,
                        col_offset=node.col_offset,
                    )
                )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """检查函数调用"""
        # 检查是否是危险的内置函数调用
        if isinstance(node.func, ast.Name):
            func_name = node.func.id

            # 危险的内置函数
            dangerous_builtins = {
                "eval",
                "exec",
                "compile",
                "open",
                "__import__",
                "globals",
                "locals",
                "vars",
                "dir",
                "input",
                "raw_input",
                "getattr",
                "setattr",
                "delattr",
            }

            if func_name in dangerous_builtins:
                self.violations.append(
                    SecurityViolation(
                        severity="CRITICAL",
                        violation_type="FORBIDDEN_FUNCTION",
                        message=f'Use of dangerous built-in function "{func_name}" is prohibited',
                        line=node.lineno,
                        col_offset=node.col_offset,
                    )
                )

        # 检查属性访问调用 (e.g., os.system)
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                module_name = node.func.value.id
                func_name = node.func.attr

                # 检查是否在调用危险模块的方法
                dangerous_modules = {
                    "sys",
                    "subprocess",
                    "shutil",
                    "socket",
                    "http",
                    "urllib",
                    "ftplib",
                    "pickle",
                    "shelve",
                    "marshal",
                    "types",
                }
                # importlib 危险子模块（但允许 util）
                _importlib_dangerous = {"__import__", "reload", "invalidate_caches", "import_module"}
                # os 的危险子模块调用（但允许 os.path）
                _os_dangerous = {
                    "system",
                    "popen",
                    "execv",
                    "execve",
                    "spawnl",
                    "spawnv",
                    "fork",
                    "kill",
                    "remove",
                    "unlink",
                    "rename",
                    "mkdir",
                    "makedirs",
                    "rmdir",
                    "listdir",
                    "walk",
                    "chmod",
                    "chown",
                    "environ",
                    "putenv",
                    "getenv",
                    "fdopen",
                    "pipe",
                    "dup2",
                }

                if module_name == "os" and func_name in _os_dangerous:
                    self.violations.append(
                        SecurityViolation(
                            severity="CRITICAL",
                            violation_type="FORBIDDEN_MODULE_ACCESS",
                            message=f'Access to dangerous function "os.{func_name}" is prohibited',
                            line=node.lineno,
                            col_offset=node.col_offset,
                        )
                    )
                elif module_name == "importlib" and func_name in _importlib_dangerous:
                    self.violations.append(
                        SecurityViolation(
                            severity="CRITICAL",
                            violation_type="FORBIDDEN_MODULE_ACCESS",
                            message=f'Access to dangerous function "importlib.{func_name}" is prohibited',
                            line=node.lineno,
                            col_offset=node.col_offset,
                        )
                    )
                elif module_name in dangerous_modules:
                    self.violations.append(
                        SecurityViolation(
                            severity="CRITICAL",
                            violation_type="FORBIDDEN_MODULE_ACCESS",
                            message=f'Access to module "{module_name}.{func_name}" is prohibited',
                            line=node.lineno,
                            col_offset=node.col_offset,
                        )
                    )

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """检查属性访问"""
        # 检查危险属性访问
        if isinstance(node.value, ast.Name):
            # __dict__, __class__ 等特殊属性
            dangerous_attrs = {
                "__dict__",
                "__class__",
                "__bases__",
                "__subclasses__",
                "__mro__",
                "__code__",
                "__globals__",
                "__closure__",
            }

            if node.attr in dangerous_attrs:
                self.violations.append(
                    SecurityViolation(
                        severity="HIGH",
                        violation_type="DANGEROUS_ATTRIBUTE",
                        message=f'Access to dangerous attribute "{node.attr}" is prohibited',
                        line=node.lineno,
                        col_offset=node.col_offset,
                    )
                )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """检查函数定义"""
        # 增加函数嵌套深度
        self.function_depth += 1

        # 检查是否是递归函数
        self._check_recursion(node)

        self.generic_visit(node)

        self.function_depth -= 1

    def _check_recursion(self, node: ast.FunctionDef) -> None:
        """检查函数是否递归调用自身"""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name) and child.func.id == node.name:
                    self.has_recursion = True
                    self.violations.append(
                        SecurityViolation(
                            severity="MEDIUM",
                            violation_type="RECURSION_DETECTED",
                            message=f'Function "{node.name}" contains recursive calls',
                            line=node.lineno,
                            col_offset=node.col_offset,
                        )
                    )
                    break

    def visit_For(self, node: ast.For) -> None:
        """检查for循环"""
        self.loop_depth += 1

        # 检查循环嵌套深度
        if self.loop_depth > 3:
            self.violations.append(
                SecurityViolation(
                    severity="LOW",
                    violation_type="DEEP_NESTING",
                    message=f"Loop nesting depth of {self.loop_depth} exceeds recommended limit (3)",
                    line=node.lineno,
                    col_offset=node.col_offset,
                )
            )

        self.generic_visit(node)

        self.loop_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        """检查while循环"""
        self.loop_depth += 1

        # 检查是否有while True（潜在无限循环）
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            self.violations.append(
                SecurityViolation(
                    severity="HIGH",
                    violation_type="POTENTIAL_INFINITE_LOOP",
                    message="while True loop detected - potential infinite loop",
                    line=node.lineno,
                    col_offset=node.col_offset,
                )
            )

        self.generic_visit(node)

        self.loop_depth -= 1

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """检查f-string中的代码注入"""
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                # 检查f-string中的表达式是否包含危险操作
                self._check_string_injection(value)

        self.generic_visit(node)

    def _check_string_injection(self, node) -> None:
        """检查字符串注入"""
        # 检查是否在f-string中调用eval/exec
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                if node.value.func.id in ("eval", "exec"):
                    self.violations.append(
                        SecurityViolation(
                            severity="CRITICAL",
                            violation_type="CODE_INJECTION",
                            message="Code injection attempt detected in f-string",
                            line=node.lineno,
                            col_offset=node.col_offset,
                        )
                    )

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """检查增强赋值（用于检测字符串拼接绕过）"""
        # 检查 += 操作
        if isinstance(node.op, ast.Add):
            # 尝试提取右边的字符串
            right_str = self._extract_string_literal(node.value)

            if right_str:
                # 检查字符串是否包含危险内容
                if any(dangerous in right_str.lower() for dangerous in ["import", "eval", "exec", "open", "__"]):
                    self.violations.append(
                        SecurityViolation(
                            severity="HIGH",
                            violation_type="STRING_CONCAT_BYPASS",
                            message=f'String concatenation that may form dangerous code: "{right_str}"',
                            line=node.lineno,
                            col_offset=node.col_offset,
                        )
                    )

        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        """检查二进制操作（用于检测字符串拼接绕过）"""
        # 检查字符串拼接是否在构建危险的模块名
        if isinstance(node.op, ast.Add):
            left_str = self._extract_string_literal(node.left)
            right_str = self._extract_string_literal(node.right)

            if left_str and right_str:
                combined = left_str + right_str
                if any(dangerous in combined.lower() for dangerous in ["import", "eval", "exec", "open", "__"]):
                    self.violations.append(
                        SecurityViolation(
                            severity="HIGH",
                            violation_type="STRING_CONCAT_BYPASS",
                            message=f'String concatenation that may form dangerous code: "{combined}"',
                            line=node.lineno,
                            col_offset=node.col_offset,
                        )
                    )

        self.generic_visit(node)

    def _extract_string_literal(self, node) -> Optional[str]:
        """提取字符串字面量"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def visit_Try(self, node: ast.Try) -> None:
        """检查try块"""
        # 检查是否使用了try/except来绕过错误
        if not node.handlers:
            # 有try但没有except，可能是滥用
            pass
        else:
            # 检查except块是否过于宽泛
            for handler in node.handlers:
                if handler.type is None:
                    self.violations.append(
                        SecurityViolation(
                            severity="MEDIUM",
                            violation_type="BROAD_EXCEPTION",
                            message="Bare except clause detected - may hide security issues",
                            line=handler.lineno,
                            col_offset=handler.col_offset,
                        )
                    )

        self.generic_visit(node)


def analyze_code_security(code: str, allowed_modules: Optional[Set[str]] = None) -> Tuple[bool, List[SecurityViolation]]:
    """
    分析代码安全性

    Args:
        code: 要分析的Python代码
        allowed_modules: 允许的模块白名单

    Returns:
        (is_safe, violations) 元组
        - is_safe: True表示代码安全，False表示发现违规
        - violations: 违规列表
    """
    analyzer = SecurityAnalyzer(allowed_modules)
    violations = analyzer.analyze(code)

    # 分类违规
    critical = [v for v in violations if v.severity == "CRITICAL"]
    high = [v for v in violations if v.severity == "HIGH"]

    # 如果有CRITICAL或HIGH违规，代码不安全
    is_safe = len(critical) == 0 and len(high) == 0

    return is_safe, violations


def get_security_report(code: str, allowed_modules: Optional[Set[str]] = None) -> Dict[str, Any]:
    """
    获取详细的安全报告

    Args:
        code: 要分析的Python代码
        allowed_modules: 允许的模块白名单

    Returns:
        安全报告字典
    """
    is_safe, violations = analyze_code_security(code, allowed_modules)

    # 按严重程度分组
    by_severity = {
        "CRITICAL": [v.to_dict() for v in violations if v.severity == "CRITICAL"],
        "HIGH": [v.to_dict() for v in violations if v.severity == "HIGH"],
        "MEDIUM": [v.to_dict() for v in violations if v.severity == "MEDIUM"],
        "LOW": [v.to_dict() for v in violations if v.severity == "LOW"],
    }

    # 按类型分组
    by_type: dict[str, list[dict[str, Any]]] = {}
    for v in violations:
        if v.violation_type not in by_type:
            by_type[v.violation_type] = []
        by_type[v.violation_type].append(v.to_dict())

    return {
        "is_safe": is_safe,
        "total_violations": len(violations),
        "by_severity": by_severity,
        "by_type": by_type,
        "has_recursion": any(v.violation_type == "RECURSION_DETECTED" for v in violations),
        "max_loop_depth": 0,  # 将在分析器中跟踪
    }
