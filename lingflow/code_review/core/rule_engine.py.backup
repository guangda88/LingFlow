"""
规则引擎 - 可配置的代码检查规则

该模块提供了可扩展的规则引擎，用于静态代码分析。
支持自定义规则注册、规则启用/禁用等功能。
"""

import ast
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from .severity import Severity

logger = logging.getLogger(__name__)


@dataclass
class Rule:
    """
    审查规则定义

    Attributes:
        id: 规则唯一标识符 (如 "SEC001")
        name: 规则名称
        category: 规则类别 (security, performance, code_quality等)
        check_func: 检查函数，签名为 (content, tree, file_path) -> Optional[str]
        severity: 问题严重程度
        suggestion_template: 修复建议模板
        enabled: 是否启用该规则

    Examples:
        >>> def check_eval(content, tree, path):
        ...     return "发现eval使用" if "eval(" in content else None
        >>> rule = Rule(
        ...     id="CUSTOM001",
        ...     name="custom_eval_check",
        ...     category="security",
        ...     check_func=check_eval,
        ...     severity=Severity.CRITICAL,
        ...     suggestion_template="避免使用eval"
        ... )
    """

    id: str
    name: str
    category: str
    check_func: Callable
    severity: Severity
    suggestion_template: str
    enabled: bool = True

    def __post_init__(self):
        """初始化后处理，确保类别不为None"""
        if not self.category:
            self.category = "general"
        if not self.id:
            raise ValueError("规则ID不能为空")

    def validate(self) -> bool:
        """
        验证规则配置是否有效

        Returns:
            bool: 规则是否有效
        """
        return bool(self.id and self.name and self.check_func)


class RuleEngineError(Exception):
    """规则引擎异常基类"""
    pass


class RuleNotFoundError(RuleEngineError):
    """规则未找到异常"""
    pass


class RuleValidationError(RuleEngineError):
    """规则验证异常"""
    pass


class RuleEngine:
    """
    可配置的代码审查规则引擎

    该类管理所有代码审查规则，提供规则注册、启用/禁用、执行等功能。

    Attributes:
        rules: 已注册的规则字典，键为规则ID

    Examples:
        >>> engine = RuleEngine()
        >>> result = engine.run_rules(code, tree, Path("test.py"))
        >>> engine.disable_rule("SEC001")
    """

    # 默认嵌套循环深度阈值
    DEFAULT_NESTED_LOOP_THRESHOLD = 3

    # 默认复杂度阈值
    DEFAULT_COMPLEXITY_THRESHOLD = 15

    # 默认类方法数量阈值
    DEFAULT_CLASS_METHODS_THRESHOLD = 15

    # 默认导入数量阈值
    DEFAULT_IMPORT_COUNT_THRESHOLD = 20

    def __init__(self):
        """初始化规则引擎并注册默认规则"""
        self.rules: Dict[str, Rule] = {}
        try:
            self._register_default_rules()
        except Exception as e:
            logger.error(f"注册默认规则失败: {e}")
            raise RuleEngineError(f"规则引擎初始化失败: {e}") from e

    def _register_default_rules(self) -> None:
        """
        注册默认规则集

        注册以下类别的默认规则:
        - 安全规则 (SEC): eval/exec使用、硬编码密钥、SQL注入
        - 性能规则 (PERF): 嵌套循环、字符串拼接、全局变量
        - 代码质量 (QUAL): 复杂度、命名规范
        - 架构规则 (ARCH): 类方法数、导入数量

        Raises:
            RuleValidationError: 规则配置无效时
        """
        default_rules = [
            # ==================== 安全规则 ====================
            Rule(
                id="SEC001",
                name="eval_usage",
                category="security",
                check_func=self._check_eval_usage,
                severity=Severity.CRITICAL,
                suggestion_template="避免使用 eval()，存在代码注入风险，请考虑使用 ast.literal_eval() 或其他安全替代方案",
            ),
            Rule(
                id="SEC002",
                name="exec_usage",
                category="security",
                check_func=self._check_exec_usage,
                severity=Severity.CRITICAL,
                suggestion_template="避免使用 exec()，存在代码注入风险",
            ),
            Rule(
                id="SEC003",
                name="hardcoded_secrets",
                category="security",
                check_func=self._check_hardcoded_secrets,
                severity=Severity.HIGH,
                suggestion_template="使用环境变量或配置文件存储敏感信息",
            ),
            Rule(
                id="SEC004",
                name="sql_injection_risk",
                category="security",
                check_func=self._check_sql_injection,
                severity=Severity.HIGH,
                suggestion_template="使用参数化查询防止 SQL 注入",
            ),
            # ==================== 性能规则 ====================
            Rule(
                id="PERF001",
                name="nested_loops",
                category="performance",
                check_func=self._check_nested_loops,
                severity=Severity.MEDIUM,
                suggestion_template="考虑优化循环结构或使用向量化操作",
            ),
            Rule(
                id="PERF002",
                name="string_concatenation",
                category="performance",
                check_func=self._check_string_concatenation,
                severity=Severity.LOW,
                suggestion_template="使用 str.join() 代替循环中的字符串拼接",
            ),
            Rule(
                id="PERF003",
                name="global_variable_lookup",
                category="performance",
                check_func=self._check_global_lookup,
                severity=Severity.LOW,
                suggestion_template="缓存全局变量或使用局部变量以提高性能",
            ),
            # ==================== 代码质量规则 ====================
            Rule(
                id="QUAL001",
                name="high_complexity",
                category="code_quality",
                check_func=self._check_high_complexity,
                severity=Severity.MEDIUM,
                suggestion_template="考虑重构函数以降低圈复杂度",
            ),
            Rule(
                id="QUAL002",
                name="naming_convention",
                category="code_quality",
                check_func=self._check_naming_convention,
                severity=Severity.LOW,
                suggestion_template="遵循 PEP 8 命名规范",
            ),
            # ==================== 架构规则 ====================
            Rule(
                id="ARCH001",
                name="too_many_methods",
                category="architecture",
                check_func=self._check_class_methods,
                severity=Severity.MEDIUM,
                suggestion_template="考虑将类拆分为多个小类以遵循单一职责原则",
            ),
            Rule(
                id="ARCH002",
                name="too_many_imports",
                category="architecture",
                check_func=self._check_import_count,
                severity=Severity.LOW,
                suggestion_template="减少不必要的导入或重新组织模块结构",
            ),
        ]

        for rule in default_rules:
            try:
                self.register_rule(rule)
            except Exception as e:
                logger.warning(f"注册规则 {rule.id} 失败: {e}")

    def register_rule(self, rule: Rule) -> None:
        """
        注册新规则

        Args:
            rule: 要注册的规则对象

        Raises:
            RuleValidationError: 规则验证失败时
        """
        if not rule.validate():
            raise RuleValidationError(f"规则验证失败: {rule.id}")

        self.rules[rule.id] = rule
        logger.debug(f"已注册规则: {rule.id} - {rule.name}")

    def unregister_rule(self, rule_id: str) -> bool:
        """
        注销规则

        Args:
            rule_id: 要注销的规则ID

        Returns:
            bool: 是否成功注销
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.debug(f"已注销规则: {rule_id}")
            return True
        return False

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """
        获取规则

        Args:
            rule_id: 规则ID

        Returns:
            Optional[Rule]: 规则对象，不存在时返回None
        """
        return self.rules.get(rule_id)

    def list_rules(self, category: Optional[str] = None) -> List[Rule]:
        """
        列出规则

        Args:
            category: 可选，按类别过滤

        Returns:
            List[Rule]: 规则列表
        """
        rules = list(self.rules.values())
        if category:
            rules = [r for r in rules if r.category == category]
        return rules

    def enable_rule(self, rule_id: str) -> bool:
        """
        启用规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否成功启用

        Raises:
            RuleNotFoundError: 规则不存在时
        """
        if rule_id not in self.rules:
            raise RuleNotFoundError(f"规则不存在: {rule_id}")
        self.rules[rule_id].enabled = True
        logger.debug(f"已启用规则: {rule_id}")
        return True

    def disable_rule(self, rule_id: str) -> bool:
        """
        禁用规则

        Args:
            rule_id: 规则ID

        Returns:
            bool: 是否成功禁用

        Raises:
            RuleNotFoundError: 规则不存在时
        """
        if rule_id not in self.rules:
            raise RuleNotFoundError(f"规则不存在: {rule_id}")
        self.rules[rule_id].enabled = False
        logger.debug(f"已禁用规则: {rule_id}")
        return True

    def run_rules(
        self,
        content: str,
        tree: ast.AST,
        file_path: Path,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        运行所有启用的规则

        Args:
            content: 文件内容字符串
            tree: 解析后的AST树
            file_path: 文件路径
            category: 可选，只运行指定类别的规则

        Returns:
            List[Dict[str, Any]]: 检查结果列表，每个结果包含:
                - rule_id: 规则ID
                - rule_name: 规则名称
                - category: 规则类别
                - severity: 严重程度
                - issue: 问题描述
                - suggestion: 修复建议
                - file: 文件路径
        """
        results = []

        for rule in self.rules.values():
            # 跳过禁用的规则
            if not rule.enabled:
                continue

            # 按类别过滤
            if category and rule.category != category:
                continue

            try:
                issue = rule.check_func(content, tree, file_path)
                if issue:
                    results.append({
                        'rule_id': rule.id,
                        'rule_name': rule.name,
                        'category': rule.category,
                        'severity': rule.severity.value,
                        'issue': issue,
                        'suggestion': rule.suggestion_template,
                        'file': str(file_path)
                    })
            except SyntaxError as e:
                logger.warning(f"规则 {rule.id} 遇到语法错误: {e}")
            except AttributeError as e:
                logger.warning(f"规则 {rule.id} 访问属性失败: {e}")
            except Exception as e:
                logger.warning(f"规则 {rule.id} 执行失败: {e}", exc_info=True)

        return results

    # ==================== 规则检查函数 ====================

    @staticmethod
    def _check_eval_usage(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查 eval 使用

        eval() 存在代码注入风险，应避免使用。
        该检查会排除注释和字符串中的使用。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # 移除注释
            code_part = line.split('#')[0]
            if 'eval(' in code_part:
                # 进一步检查是否在字符串中
                if '"""' not in line and "'''" not in line:
                    return f"第 {i} 行: 使用 eval() 函数，存在代码注入风险"
        return None

    @staticmethod
    def _check_exec_usage(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查 exec 使用

        exec() 存在代码注入风险，应避免使用。
        该检查会排除注释和字符串中的使用。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # 移除注释
            code_part = line.split('#')[0]
            if 'exec(' in code_part:
                # 进一步检查是否在字符串中
                if '"""' not in line and "'''" not in line:
                    return f"第 {i} 行: 使用 exec() 函数，存在代码注入风险"
        return None

    @staticmethod
    def _check_hardcoded_secrets(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查硬编码敏感信息

        检测可能的硬编码密码、API密钥等。
        会排除环境变量引用、注释和示例代码。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        secret_patterns = {
            r'password\s*=\s*["\'][^"\']{4,}["\']',
            r'api_key\s*=\s*["\'][^"\']{10,}["\']',
            r'apikey\s*=\s*["\'][^"\']{10,}["\']',
            r'secret\s*=\s*["\'][^"\']{10,}["\']',
            r'access_token\s*=\s*["\'][^"\']{10,}["\']',
            r'private_key\s*=\s*["\'][^"\']{10,}["\']',
        }

        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # 跳过注释行
            if line.strip().startswith('#'):
                continue

            # 跳过包含环境变量引用的行
            if 'os.environ' in line or 'os.getenv' in line or 'ENV' in line:
                continue

            # 跳过包含示例/演示的行
            if any(keyword in line.lower() for keyword in ['example', 'demo', 'test', 'placeholder']):
                continue

            for pattern in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # 额外检查：排除常见的占位符
                    placeholders = ['xxx', 'yyy', 'test_', 'example_', 'your_', 'replace_', 'placeholder']
                    if any(placeholder in line.lower() for placeholder in placeholders):
                        continue
                    return f"第 {i} 行: 检测到可能的硬编码敏感信息"
        return None

    @staticmethod
    def _check_sql_injection(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查 SQL 注入风险

        检测字符串拼接构造SQL语句的模式。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        dangerous_patterns = [
            r'execute\s*\(\s*["\'].*\+\s*',  # execute("..." + var)
            r'query\s*\(\s*["\'].*\+\s*',  # query("..." + var)
            r'f["\'].*SELECT.*\{',        # f-string with SQL
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, content):
                return "检测到可能的 SQL 注入风险，请使用参数化查询"
        return None

    @staticmethod
    def _check_nested_loops(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查嵌套循环 - 优化版本 O(n) 复杂度

        深度嵌套循环可能影响性能和代码可读性。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        max_depth = 0
        
        # 使用迭代而非递归，避免重复遍历
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                # 计算此循环的嵌套深度
                depth = 1
                current = node
                
                # 使用栈来跟踪嵌套
                stack = [current]
                
                while stack:
                    current = stack.pop()
                    for child in ast.iter_child_nodes(current):
                        if isinstance(child, ast.For):
                            depth += 1
                            stack.append(child)
                            break
                
                max_depth = max(max_depth, depth)

        threshold = RuleEngine.DEFAULT_NESTED_LOOP_THRESHOLD
        if max_depth > threshold:
            return f"检测到 {max_depth} 层嵌套循环 (阈值: {threshold})"
        return None

    @staticmethod
    def _count_loop_depth(node: ast.For) -> int:
        """
        计算循环嵌套深度

        Args:
            node: for循环节点

        Returns:
            int: 嵌套深度
        """
        max_depth = 1
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.For):
                depth = RuleEngine._count_loop_depth(child) + 1
                max_depth = max(max_depth, depth)
        return max_depth

    @staticmethod
    def _check_string_concatenation(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查字符串拼接

        检测循环中的字符串拼接，建议使用 str.join()。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        issues = []

        for node in ast.walk(tree):
            # 检查在循环中使用 += 拼接字符串
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign):
                        if isinstance(child.op, ast.Add):
                            # 检查目标是否是字符串类型的变量
                            if isinstance(child.target, ast.Name):
                                var_name = child.target.id
                                # 检查赋值是否是字符串常量
                                if isinstance(child.value, ast.Constant) and isinstance(child.value.value, str):
                                    issues.append((var_name, child.lineno))

        if issues:
            line_numbers = ', '.join(str(l) for _, l in issues[:3])
            return f"在循环中拼接字符串 (行号: {line_numbers})，考虑使用 str.join()"
        return None

    @staticmethod
    def _check_global_lookup(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查全局变量使用

        全局变量的频繁查找可能影响性能。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        global_vars = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Global):
                for name in node.names:
                    global_vars.add(name)

        if global_vars:
            return f"使用全局变量: {', '.join(sorted(list(global_vars)))}"
        return None

    @staticmethod
    def _check_high_complexity(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查高复杂度函数

        使用圈复杂度度量函数复杂度。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        threshold = RuleEngine.DEFAULT_COMPLEXITY_THRESHOLD
        high_complexity_funcs = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = RuleEngine._calculate_complexity(node)
                if complexity > threshold:
                    high_complexity_funcs.append((node.name, complexity))

        if high_complexity_funcs:
            func_list = ', '.join([f"{name}({c})" for name, c in high_complexity_funcs[:3]])
            return f"高复杂度函数: {func_list} (阈值: {threshold})"
        return None

    @staticmethod
    def _calculate_complexity(node: ast.FunctionDef) -> int:
        """
        计算圈复杂度

        Args:
            node: 函数定义节点

        Returns:
            int: 圈复杂度值
        """
        complexity = 1

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1

        return complexity

    @staticmethod
    def _check_naming_convention(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查命名规范 (PEP 8)

        - 类名: CapWords (如 MyClass)
        - 函数/变量: snake_case (如 my_function)
        - 常量: UPPER_CASE (如 MAX_SIZE)

        跳过特殊方法 (__init__, __len__, forward等)和私有方法。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        issues = []

        # 特殊方法名和允许的方法名
        special_methods = {
            '__init__', '__del__', '__repr__', '__str__', '__call__',
            '__len__', '__getitem__', '__setitem__', '__contains__',
            '__iter__', '__next__', '__enter__', '__exit__',
            '__bool__', '__bytes__', '__format__', '__hash__',
            '__eq__', '__ne__', '__lt__', '__le__', '__gt__',
            '__ge__', '__add__', '__sub__', '__mul__', '__truediv__',
            '__floordiv__', '__mod__', '__pow__', '__and__', '__or__',
            '__xor__', '__lshift__', '__rshift__', '__pos__', '__neg__',
            '__invert__', '__setattr__', '__getattr__', '__delattr__',
            '__getattribute__', '__instancecheck__', '__subclasscheck__',
            # PyTorch/深度学习常用方法
            'forward', 'backward', 'train', 'eval', 'parameters', 'to',
            'load_state_dict', 'state_dict', 'zero_grad', 'extra_repr',
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                issues.extend(RuleEngine._check_class_naming(node))
            elif isinstance(node, ast.FunctionDef):
                issues.extend(RuleEngine._check_function_naming(node, special_methods))

        if issues:
            return f"命名不符合 PEP 8 规范: {', '.join(issues[:5])}"
        return None

    @staticmethod
    def _check_class_naming(node: ast.ClassDef) -> List[str]:
        """检查类名是否符合 CapWords 规范

        Args:
            node: 类定义节点

        Returns:
            List[str]: 发现的问题列表
        """
        issues = []
        if not node.name:
            return issues
        # 允许异常: 全大写缩写 (如 HTTP, URL)
        if node.name.isupper() or node.name.replace('_', '').isupper():
            return issues
        # 检查首字母是否大写
        if node.name[0].islower():
            issues.append(f"类名 '{node.name}' 应使用 CapWords 风格")
        return issues

    @staticmethod
    def _check_function_naming(node: ast.FunctionDef, special_methods: set) -> List[str]:
        """检查函数名是否符合 snake_case 规范

        Args:
            node: 函数定义节点
            special_methods: 特殊方法名集合

        Returns:
            List[str]: 发现的问题列表
        """
        issues = []
        # 跳过特殊方法和特殊名称
        if node.name in special_methods:
            return issues
        # 跳过魔术方法
        if node.name.startswith('__') and node.name.endswith('__'):
            return issues
        # 跳过私有方法
        if node.name.startswith('_'):
            return issues

        # 检查函数名是否使用 snake_case
        if node.name and node.name[0].isupper():
            issues.append(f"函数名 '{node.name}' 应使用 snake_case 风格")
        # 检查是否包含大写字母
        if any(c.isupper() for c in node.name):
            if not all(c == '_' or c.islower() for c in node.name):
                issues.append(f"函数名 '{node.name}' 应使用 snake_case 风格")
        return issues

    @staticmethod
    def _check_class_methods(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查类方法数量

        过多的方法可能表示类承担了过多职责。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        threshold = RuleEngine.DEFAULT_CLASS_METHODS_THRESHOLD

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > threshold:
                    return f"类 {node.name} 方法过多 ({len(methods)} 个，阈值: {threshold})"
        return None

    @staticmethod
    def _check_import_count(content: str, tree: ast.AST, file_path: Path) -> Optional[str]:
        """
        检查导入数量

        过多的导入可能表示模块职责不清晰。

        Args:
            content: 文件内容
            tree: AST树
            file_path: 文件路径

        Returns:
            Optional[str]: 发现问题时返回描述，否则返回None
        """
        threshold = RuleEngine.DEFAULT_IMPORT_COUNT_THRESHOLD

        imports = [node for node in ast.walk(tree)
                   if isinstance(node, (ast.Import, ast.ImportFrom))]

        if len(imports) > threshold:
            return f"导入过多 ({len(imports)} 个，阈值: {threshold})"
        return None
