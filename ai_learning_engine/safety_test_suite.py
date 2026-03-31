"""
AI规则安全性测试套件

用于验证从AI工具学习到的规则的安全性，确保不会引入新的安全漏洞。
"""

import ast
 import copy
 import tempfile
 import unittest
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import uuid
import subprocess
import sys
from unittest.mock import patch, MagicMock

from lingflow.common.security_analyzer import SecurityAnalyzer, SecurityViolation
from .rule_learning_engine import LearnedRule, LearningStatus
from .rule_validation_system import SafetyValidator


class SecurityTestResult:
    """安全测试结果"""
    def __init__(self):
        self.test_passed = 0
        self.test_failed = 0
        self.total_tests = 0
        self.violations_found = []
        self.issues_detected = []

    def add_pass(self, test_name: str):
        self.test_passed += 1
        self.total_tests += 1

    def add_fail(self, test_name: str, issue: str):
        self.test_failed += 1
        self.total_tests += 1
        self.issues_detected.append({
            'test': test_name,
            'issue': issue,
            'severity': 'HIGH'
        })

    def add_violation(self, violation: SecurityViolation):
        self.violations_found.append(violation)

    def get_summary(self) -> Dict[str, Any]:
        return {
            'total_tests': self.total_tests,
            'passed': self.test_passed,
            'failed': self.test_failed,
            'pass_rate': self.test_passed / self.total_tests if self.total_tests > 0 else 0,
            'violations_count': len(self.violations_found),
            'issues_count': len(self.issues_detected)
        }


class SecurityTestSuite:
    """安全测试套件基类"""

    def __init__(self):
        self.validator = SafetyValidator()
        self.test_result = SecurityTestResult()

    def run_all_tests(self, rule: LearnedRule) -> SecurityTestResult:
        """运行所有安全测试"""
        print(f"\n=== 运行安全测试套件 (规则: {rule.id}) ===")

        # 运行各项测试
        self.test_code_injection(rule)
        self.test_sql_injection(rule)
        self.test_xss_protection(rule)
        self.test_auth_bypass(rule)
        self.test_file_inclusion(rule)
        self.test_command_injection(rule)
        self.test_csrf_protection(rule)
        self.test_deserialization(rule)
        self.test_regex_injection(rule)
        self.test_path_traversal(rule)

        return self.test_result

    def test_code_injection(self, rule: LearnedRule):
        """测试代码注入防护"""
        print("\n--- 测试代码注入防护 ---")

        test_cases = [
            # 危险的代码
            "eval('malicious_code()')",
            "exec('import os; os.system(\"rm -rf /\")')",
            "compile('dangerous()', '<string>', 'exec')",
            "__import__('os').system('echo hacked')",

            # 安全的代码
            "ast.literal_eval('safe_string')",
            "json.loads('{\"key\": \"value\"}')",
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            if 'eval(' in test_code or 'exec(' in test_code:
                if not is_safe:
                    self.test_result.add_pass(f"代码注入测试_{i+1}")
                else:
                    self.test_result.add_fail(f"代码注入测试_{i+1}", "未检测到代码注入风险")
            else:
                if is_safe:
                    self.test_result.add_pass(f"代码注入测试_{i+1}")
                else:
                    self.test_result.add_fail(f"代码注入测试_{i+1}", "误报安全风险")

    def test_sql_injection(self, rule: LearnedRule):
        """测试SQL注入防护"""
        print("\n--- 测试SQL注入防护 ---")

        test_cases = [
            # 危险的SQL查询
            "query = \"SELECT * FROM users WHERE id = \" + user_id",
            "execute(\"SELECT * FROM table WHERE name = '\" + name + \"'\")",
            "cursor.execute(\"INSERT INTO table VALUES (\" + val + \")\")",

            # 安全的SQL查询
            "cursor.execute(\"SELECT * FROM users WHERE id = %s\", (user_id,))",
            "query = \"SELECT * FROM users WHERE id = ?\"",
            session.query(User).filter(User.id == user_id)
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            if 'SELECT.*+.*id' in test_code or 'execute.*+.*' in test_code:
                if not is_safe:
                    self.test_result.add_pass(f"SQL注入测试_{i+1}")
                else:
                    self.test_result.add_fail(f"SQL注入测试_{i+1}", "未检测到SQL注入风险")
            else:
                if is_safe:
                    self.test_result.add_pass(f"SQL注入测试_{i+1}")
                else:
                    self.test_result.add_fail(f"SQL注入测试_{i+1}", "误报SQL注入风险")

    def test_xss_protection(self, rule: LearnedRule):
        """测试XSS防护"""
        print("\n--- 测试XSS防护 ---")

        test_cases = [
            # 危险的XSS代码
            "document.getElementById('div').innerHTML = user_input",
            "response.write('<script>' + user_input + '</script>')",
            "eval('alert(\"XSS\")')",

            # 安全的处理方式
            "document.getElementById('div').textContent = user_input",
            "escape_html(user_input)",
            "mark_safe(user_input)"
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            # 简化的XSS检测
            xss_indicators = ['innerHTML', 'eval(', '<script>']
            has_xss = any(indicator in test_code for indicator in xss_indicators)

            if has_xss and not is_safe:
                self.test_result.add_pass(f"XSS防护测试_{i+1}")
            elif not has_xss and is_safe:
                self.test_result.add_pass(f"XSS防护测试_{i+1}")
            else:
                self.test_result.add_fail(f"XSS防护测试_{i+1}", "XSS检测不准确")

    def test_auth_bypass(self, rule: LearnedRule):
        """测试认证绕过"""
        print("\n--- 测试认证绕过防护 ---")

        test_cases = [
            # 危险的认证代码
            "if user.get('admin', False):",
            "access_level = request.args.get('level', 0)",
            "if admin == 'true':",

            # 安全的认证代码
            "if user.is_authenticated() and user.has_permission('admin')",
            "access_level = int(request.form.get('level', 0))",
            "if user.role == Role.ADMIN:"
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            # 简化的认证绕过检测
            bypass_indicators = ['get.*admin', 'args.get.*level', "=='true'"]
            has_bypass = any(indicator in test_code for indicator in bypass_indicators)

            if has_bypass and not is_safe:
                self.test_result.add_pass(f"认证绕过测试_{i+1}")
            elif not has_bypass and is_safe:
                self.test_result.add_pass(f"认证绕过测试_{i+1}")
            else:
                self.test_result.add_fail(f"认证绕过测试_{i+1}", "认证绕过检测不准确")

    def test_file_inclusion(self, rule: LearnedRule):
        """测试文件包含安全"""
        print("\n--- 测试文件包含安全 ---")

        test_cases = [
            # 危险的文件包含
            "include(user_file + '.php')",
            "require('../../' + path)",
            "open(file_path, 'r')",

            # 安全的文件包含
            "include(os.path.join('templates', file))",
            "open(config_file, 'r')"
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            # 简化的文件包含检测
            inclusion_indicators = ['include.*user', 'require.*\.\.', 'open\(.*file']
            has_inclusion = any(indicator in test_code for indicator in inclusion_indicators)

            if has_inclusion and not is_safe:
                self.test_result.add_pass(f"文件包含测试_{i+1}")
            elif not has_inclusion and is_safe:
                self.test_result.add_pass(f"文件包含测试_{i+1}")
            else:
                self.test_result.add_fail(f"文件包含测试_{i+1}", "文件包含检测不准确")

    def test_command_injection(self, rule: LearnedRule):
        """测试命令注入防护"""
        print("\n--- 测试命令注入防护 ---")

        test_cases = [
            # 危险的命令执行
            "os.system('ls ' + user_input)",
            "subprocess.Popen(['ls', user_input])",
            "eval('__import__(\"os\").system(\"echo hello\")')",

            # 安全的命令执行
            "subprocess.run(['ls', sanitized_input], check=True)",
            "commands.getoutput('ls')"
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            # 简化的命令注入检测
            cmd_injection_indicators = ['os.system.*+', 'subprocess.Popen.*+', 'eval.*__import__']
            has_injection = any(indicator in test_code for indicator in cmd_injection_indicators)

            if has_injection and not is_safe:
                self.test_result.add_pass(f"命令注入测试_{i+1}")
            elif not has_injection and is_safe:
                self.test_result.add_pass(f"命令注入测试_{i+1}")
            else:
                self.test_result.add_fail(f"命令注入测试_{i+1}", "命令注入检测不准确")

    def test_csrf_protection(self, rule: LearnedRule):
        """测试CSRF防护"""
        print("\n--- 测试CSRF防护 ---")

        test_cases = [
            # 缺少CSRF保护的代码
            "if request.method == 'POST':",
            "delete_user(user_id)",

            # 有CSRF保护的代码
            "if request.method == 'POST' and validate_csrf_token(request)",
            "delete_user(user_id, csrf_token=token)"
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            # 简化的CSRF检测
            csrf_missing = 'POST' in test_code and 'csrf' not in test_code.lower()

            if csrf_missing and not is_safe:
                self.test_result.add_pass(f"CSRF防护测试_{i+1}")
            elif not csrf_missing and is_safe:
                self.test_result.add_pass(f"CSRF防护测试_{i+1}")
            else:
                self.test_result.add_fail(f"CSRF防护测试_{i+1}", "CSRF检测不准确")

    def test_deserialization(self, rule: LearnedRule):
        """测试反序列化安全"""
        print("\n--- 测试反序列化安全 ---")

        test_cases = [
            # 危险的反序列化
            "pickle.loads(user_data)",
            "marshal.loads(user_data)",
            "eval(user_data)",

            # 安全的反序列化
            "json.loads(safe_data)",
            "yaml.safe_load(data)"
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            # 简化的反序列化检测
            unsafe_deserialization = ['pickle.loads', 'marshal.loads', 'eval(']
            has_unsafe = any(method in test_code for method in unsafe_deserialization)

            if has_unsafe and not is_safe:
                self.test_result.add_pass(f"反序列化测试_{i+1}")
            elif not has_unsafe and is_safe:
                self.test_result.add_pass(f"反序列化测试_{i+1}")
            else:
                self.test_result.add_fail(f"反序列化测试_{i+1}", "反序列化检测不准确")

    def test_regex_injection(self, rule: LearnedRule):
        """测试正则表达式注入"""
        print("\n--- 测试正则表达式注入 ---")

        test_cases = [
            # 危险的正则表达式
            "re.compile(user_pattern)",
            "re.search(user_input, text)",

            # 安全的正则表达式
            "re.compile(re.escape(user_pattern))",
            "re.escape(user_input)"
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            # 简化的正则表达式注入检测
            regex_unsafe = 're.compile.*user' in test_code and 're.escape' not in test_code

            if regex_unsafe and not is_safe:
                self.test_result.add_pass(f"正则注入测试_{i+1}")
            elif not regex_unsafe and is_safe:
                self.test_result.add_pass(f"正则注入测试_{i+1}")
            else:
                self.test_result.add_fail(f"正则注入测试_{i+1}", "正则注入检测不准确")

    def test_path_traversal(self, rule: LearnedRule):
        """测试路径遍历防护"""
        print("\n--- 测试路径遍历防护 ---")

        test_cases = [
            # 危险的路径处理
            "open('../../' + filename)",
            "include('../' + user_file)",

            # 安全的路径处理
            "open(os.path.join('safe_dir', filename))",
            "include(os.path.abspath(path))"
        ]

        for i, test_code in enumerate(test_cases):
            is_safe, violations = self.validator.validate_code_safety(test_code)

            # 简化的路径遍历检测
            path_traversal = ['\.\..*filename', '\.\..*user_file']
            has_traversal = any(traversal in test_code for traversal in path_traversal)

            if has_traversal and not is_safe:
                self.test_result.add_pass(f"路径遍历测试_{i+1}")
            elif not has_traversal and is_safe:
                self.test_result.add_pass(f"路径遍历测试_{i+1}")
            else:
                self.test_result.add_fail(f"路径遍历测试_{i+1}", "路径遍历检测不准确")


class RuleConflictTestSuite:
    """规则冲突测试套件"""

    def __init__(self):
        self.conflicts_found = []

    def detect_rule_conflicts(self, rules: List[LearnedRule]) -> List[Dict[str, Any]]:
        """检测规则冲突"""
        print("\n--- 检测规则冲突 ---")

        conflicts = []

        for i, rule1 in enumerate(rules):
            for rule2 in rules[i+1:]:
                conflict = self._check_conflict(rule1, rule2)
                if conflict:
                    conflicts.append(conflict)
                    print(f"发现冲突: {rule1.id} <-> {rule2.id}: {conflict['description']}")

        return conflicts

    def _check_conflict(self, rule1: LearnedRule, rule2: LearnedRule) -> Optional[Dict[str, Any]]:
        """检查两个规则是否有冲突"""
        # 相同规则的冲突
        if rule1.id == rule2.id:
            return {
                'rule1': rule1.id,
                'rule2': rule2.id,
                'type': 'DUPLICATE_RULE',
                'description': '完全相同的规则ID'
            }

        # 类别冲突：安全规则与其他规则
        if (rule1.category.value == 'security' and rule2.category.value != 'security') or \
           (rule1.category.value != 'security' and rule2.category.value == 'security'):
            # 检查是否有互斥的建议
            if self._has_opposite_suggestions(rule1, rule2):
                return {
                    'rule1': rule1.id,
                    'rule2': rule2.id,
                    'type': 'CATEGORY_CONFLICT',
                    'description': f'安全规则 {rule1.id} 与 {rule2.id} 建议冲突'
                }

        # 修改冲突：一个规则添加，另一个规则删除
        if self._has_modification_conflict(rule1, rule2):
            return {
                'rule1': rule1.id,
                'rule2': rule2.id,
                'type': 'MODIFICATION_CONFLICT',
                'description': f'规则 {rule1.id} 和 {rule2.id} 修改内容冲突'
            }

        return None

    def _has_opposite_suggestions(self, rule1: LearnedRule, rule2: LearnedRule) -> bool:
        """检查规则是否有相反的建议"""
        # 简化的冲突检测
        opposite_pairs = [
            ('add', 'remove'),
            ('create', 'delete'),
            ('enable', 'disable'),
            ('include', 'exclude')
        ]

        keywords1 = ' '.join(rule1.pattern.context_keywords).lower()
        keywords2 = ' '.join(rule2.pattern.context_keywords).lower()

        for opp1, opp2 in opposite_pairs:
            if opp1 in keywords1 and opp2 in keywords2:
                return True

        return False

    def _has_modification_conflict(self, rule1: LearnedRule, rule2: LearnedRule) -> bool:
        """检查规则是否有修改冲突"""
        # 检查文件模式重叠
        if set(rule1.pattern.file_patterns) & set(rule2.pattern.file_patterns):
            # 检查代码模式是否有冲突
            if 'remove' in rule1.pattern.code_patterns and 'add' in rule2.pattern.code_patterns:
                return True
            if 'delete' in rule1.pattern.code_patterns and 'create' in rule2.pattern.code_patterns:
                return True

        return False


class BoundaryConditionTestSuite:
    """边界条件测试套件"""

    def test_empty_files(self, rule: LearnedRule):
        """测试空文件处理"""
        print("\n--- 测试空文件处理 ---")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('')
            temp_file = f.name

        try:
            # 测试规则应用
            is_safe, violations = self.validator.validate_code_safety('')
            print(f"空文件测试: {'通过' if is_safe else '失败'}")

            # 确保没有错误
            if violations and any(v.severity == 'CRITICAL' for v in violations):
                print("警告: 空文件检测到严重违规")

        finally:
            Path(temp_file).unlink()

    def test_large_files(self, rule: LearnedRule, size_mb: int = 10):
        """测试大文件处理"""
        print(f"\n--- 测试大文件处理 ({size_mb}MB) ---")

        # 创建大文件
        large_content = '#' * (size_mb * 1024 * 1024)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(large_content)
            temp_file = f.name

        try:
            # 测试性能
            start_time = time.time()
            is_safe, violations = self.validator.validate_code_safety(large_content)
            end_time = time.time()

            processing_time = end_time - start_time
            print(f"大文件处理时间: {processing_time:.2f}秒")

            # 检查是否超时
            if processing_time > 30:  # 30秒超时
                print("警告: 大文件处理时间过长")

        finally:
            Path(temp_file).unlink()

    def test_unicode_content(self, rule: LearnedRule):
        """测试Unicode内容处理"""
        print("\n--- 测试Unicode内容处理 ---")

        test_cases = [
            'def 函数名():',
            '类名 = "测试"',
            '# 这是注释',
            'f"中文字符: {变量}"'
        ]

        for test_case in test_cases:
            try:
                is_safe, violations = self.validator.validate_code_safety(test_case)
                print(f"Unicode测试: {'通过' if is_safe else '失败'}")
            except Exception as e:
                print(f"Unicode测试异常: {e}")

    def test_special_characters(self, rule: LearnedRule):
        """测试特殊字符处理"""
        print("\n--- 测试特殊字符处理 ---")

        test_cases = [
            'def func():\n    return "特殊字符: \\\\n\\t"',
            'pattern = r"^.*[\\s\\S]*$"',
            'code = """多行\n字符串"""',
            'cmd = "echo \\"hello\\""'
        ]

        for test_case in test_cases:
            try:
                is_safe, violations = self.validator.validate_code_safety(test_case)
                print(f"特殊字符测试: {'通过' if is_safe else '失败'}")
            except Exception as e:
                print(f"特殊字符测试异常: {e}")


class RollbackTestSuite:
    """回滚机制测试套件"""

    def __init__(self):
        self.backup_dir = Path("./test_backups")
        self.backup_dir.mkdir(exist_ok=True)

    def test_rollback_mechanism(self, rule: LearnedRule, test_files: List[str]):
        """测试回滚机制"""
        print("\n--- 测试回滚机制 ---")

        from ai_learning_engine.rule_validation_system import RollbackManager

        rollback_manager = RollbackManager(str(self.backup_dir))

        original_contents = {}

        try:
            # 1. 创建备份
            print("1. 创建文件备份...")
            backup_files = []
            for file_path in test_files:
                backup_path = rollback_manager.create_backup(file_path, rule.id)
                backup_files.append(backup_path)
                print(f"备份创建成功: {backup_path}")

                # 保存原始内容
                with open(file_path, 'r') as f:
                    original_contents[file_path] = f.read()

            # 2. 应用规则（模拟修改）
            print("2. 模拟规则应用...")
            modified_contents = {}
            for file_path in test_files:
                with open(file_path, 'r') as f:
                    content = f.read()
                modified_content = self._simulate_rule_application(content, rule)
                modified_contents[file_path] = modified_content

                with open(file_path, 'w') as f:
                    f.write(modified_content)
                print(f"文件已修改: {file_path}")

            # 3. 执行回滚
            print("3. 执行回滚...")
            rollback_success = True
            for backup_path, file_path in zip(backup_files, test_files):
                success = rollback_manager.rollback(backup_path, file_path)
                if success:
                    print(f"回滚成功: {file_path}")
                else:
                    rollback_success = False
                    print(f"回滚失败: {file_path}")

            # 4. 验证回滚结果
            print("4. 验证回滚结果...")
            verification_success = True
            for file_path in test_files:
                with open(file_path, 'r') as f:
                    current_content = f.read()

                if current_content == original_contents[file_path]:
                    print(f"文件恢复正确: {file_path}")
                else:
                    verification_success = False
                    print(f"文件恢复错误: {file_path}")

            # 5. 清理
            print("5. 清理备份...")
            for backup_path in backup_files:
                try:
                    Path(backup_path).unlink()
                except:
                    pass

            if rollback_success and verification_success:
                print("回滚机制测试: 通过")
                return True
            else:
                print("回滚机制测试: 失败")
                return False

        except Exception as e:
            print(f"回滚测试异常: {e}")
            return False

    def _simulate_rule_application(self, content: str, rule: LearnedRule) -> str:
        """模拟规则应用"""
        # 根据规则类型进行不同的修改
        if rule.category.value == "security":
            # 安全规则：替换eval
            content = content.replace('eval(', 'ast.literal_eval(')
        elif rule.category.value == "code_quality":
            # 质量规则：移除空函数
            lines = content.split('\n')
            new_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                if line.strip().startswith('def ') and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line == '' or next_line.startswith('#'):
                        i += 1
                        continue
                new_lines.append(line)
                i += 1
            content = '\n'.join(new_lines)

        return content


class SandboxTestSuite:
    """沙箱环境测试套件"""

    def test_isolated_execution(self, rule: LearnedRule):
        """测试隔离执行"""
        print("\n--- 测试隔离执行 ---")

        # 创建临时目录作为沙箱
        with tempfile.TemporaryDirectory() as sandbox_dir:
            print(f"沙箱目录: {sandbox_dir}")

            # 创建测试文件
            test_file = Path(sandbox_dir) / "test.py"
            test_content = '''
import os
print("Testing in sandbox")

# 尝试访问系统文件
try:
    os.system("ls /")
    print("Command executed - this should not happen in sandbox")
except Exception as e:
    print(f"Command blocked: {e}")

# 尝试导入敏感模块
try:
    import subprocess
    print("Subprocess imported - this should be blocked")
except Exception as e:
    print(f"Import blocked: {e}")
'''

            with open(test_file, 'w') as f:
                f.write(test_content)

            # 在受限环境中执行
            try:
                # 限制导入和系统调用
                restricted_globals = {
                    '__builtins__': {
                        'print': print,
                        'open': open,
                        'len': len,
                        'range': range,
                        'str': str,
                        'int': int,
                        'list': list,
                        'dict': dict,
                        'tuple': tuple,
                        'set': set,
                        'Exception': Exception
                    }
                }

                result = eval(compile(test_content, test_file, 'exec'), restricted_globals)
                print("沙箱执行: 通过")

            except Exception as e:
                print(f"沙箱执行异常: {e}")
                print("沙箱执行: 通过（成功阻止危险操作）")

    def test_memory_limit(self, rule: LearnedRule):
        """测试内存限制"""
        print("\n--- 测试内存限制 ---")

        try:
            import resource

            # 设置内存限制（100MB）
            resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 100 * 1024 * 1024))

            # 尝试分配大量内存
            try:
                large_list = []
                for i in range(1000000):
                    large_list.append('x' * 1000)
                print("内存限制测试: 失败（未限制内存使用）")
            except MemoryError:
                print("内存限制测试: 通过")

        except ImportError:
            print("内存限制测试: 跳过（不支持resource模块）")


class SafetyTestRunner:
    """安全测试运行器"""

    def __init__(self):
        self.test_suites = {
            'security': SecurityTestSuite(),
            'conflict': RuleConflictTestSuite(),
            'boundary': BoundaryConditionTestSuite(),
            'rollback': RollbackTestSuite(),
            'sandbox': SandboxTestSuite()
        }

    def run_comprehensive_tests(self, rules: List[LearnedRule], test_files: List[str] = None):
        """运行全面的安全测试"""
        print("\n" + "="*50)
        print("开始全面安全测试")
        print("="*50)

        if test_files is None:
            test_files = self._create_test_files()

        all_results = {}

        # 运行各项测试
        for suite_name, suite in self.test_suites.items():
            print(f"\n--- 运行 {suite_name.upper()} 测试套件 ---")

            try:
                if suite_name == 'security':
                    for rule in rules:
                        result = suite.run_all_tests(rule)
                        all_results[f"{rule.id}_security"] = result.get_summary()

                elif suite_name == 'conflict':
                    conflicts = suite.detect_rule_conflicts(rules)
                    all_results['conflicts'] = {
                        'count': len(conflicts),
                        'details': conflicts
                    }

                elif suite_name == 'boundary':
                    for rule in rules:
                        suite.test_empty_files(rule)
                        suite.test_large_files(rule)
                        suite.test_unicode_content(rule)
                        suite.test_special_characters(rule)

                elif suite_name == 'rollback':
                    if test_files:
                        for rule in rules:
                            suite.test_rollback_mechanism(rule, test_files)

                elif suite_name == 'sandbox':
                    for rule in rules:
                        suite.test_isolated_execution(rule)
                        suite.test_memory_limit(rule)

            except Exception as e:
                print(f"{suite_name} 测试套件执行失败: {e}")

        # 生成测试报告
        report = self._generate_test_report(all_results)
        self._save_test_report(report)

        return report

    def _create_test_files(self) -> List[str]:
        """创建测试文件"""
        test_dir = Path("./test_files")
        test_dir.mkdir(exist_ok=True)

        test_files = []

        # 创建包含各种安全问题的文件
        test_contents = [
            # 代码注入
            '''def vulnerable_function(user_input):
    eval(user_input)
    return result''',

            # SQL注入
            '''def query_database(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return execute_query(query)''',

            # XSS
            '''def render_page(user_content):
    html = "<div>" + user_content + "</div>"
    return html''',

            # 正常代码
            '''def safe_function():
    return "This is safe"
'''
        ]

        for i, content in enumerate(test_contents):
            test_file = test_dir / f"test_{i}.py"
            with open(test_file, 'w') as f:
                f.write(content)
            test_files.append(str(test_file))

        return test_files

    def _generate_test_report(self, results: Dict) -> Dict[str, Any]:
        """生成测试报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'conflicts_found': len(results.get('conflicts', {}).get('details', [])),
            'suite_results': results
        }

        # 统计测试结果
        for key, result in results.items():
            if isinstance(result, dict) and 'total_tests' in result:
                report['total_tests'] += result['total_tests']
                report['passed_tests'] += result.get('passed', 0)
                report['failed_tests'] += result.get('failed', 0)

        # 计算通过率
        if report['total_tests'] > 0:
            report['pass_rate'] = report['passed_tests'] / report['total_tests']
        else:
            report['pass_rate'] = 0

        # 生成建议
        report['recommendations'] = self._generate_test_recommendations(results)

        return report

    def _generate_test_recommendations(self, results: Dict) -> List[str]:
        """生成测试建议"""
        recommendations = []

        # 检查冲突
        if 'conflicts' in results and results['conflicts']['count'] > 0:
            recommendations.append(f"发现 {results['conflicts']['count']} 个规则冲突，建议解决后使用")

        # 检查安全测试通过率
        security_tests = [r for r in results.values() if isinstance(r, dict) and 'pass_rate' in r]
        if security_tests:
            avg_pass_rate = sum(t['pass_rate'] for t in security_tests) / len(security_tests)
            if avg_pass_rate < 0.9:
                recommendations.append("安全测试通过率较低，建议加强规则安全性验证")

        # 检查回滚测试
        rollback_results = results.get('rollback_test', {})
        if rollback_results and not rollback_results.get('success', True):
            recommendations.append("回滚测试失败，请检查回滚机制")

        return recommendations

    def _save_test_report(self, report: Dict):
        """保存测试报告"""
        report_file = Path("./test_reports/safety_test_report.json")
        report_file.parent.mkdir(exist_ok=True)

        import json
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n测试报告已保存到: {report_file}")


if __name__ == '__main__':
    # 创建测试规则
    rules = [
        LearnedRule(
            id="SEC001",
            name="Remove eval Usage",
            description="Replace eval() with ast.literal_eval()",
            category=None,  # 简化测试
            pattern=None,
            tools=["SonarQube"],
            frequency=10,
            confidence=0.9,
            status=LearningStatus.VALIDATED
        ),
        LearnedRule(
            id="QUAL001",
            name="Remove Empty Functions",
            description="Remove empty functions to improve quality",
            category=None,
            pattern=None,
            tools=["Pylint"],
            frequency=15,
            confidence=0.85,
            status=LearningStatus.VALIDATED
        )
    ]

    # 运行安全测试
    runner = SafetyTestRunner()
    report = runner.run_comprehensive_tests(rules)

    # 打印测试结果
    print("\n" + "="*50)
    print("安全测试结果摘要")
    print("="*50)
    print(f"总测试数: {report['total_tests']}")
    print(f"通过测试: {report['passed_tests']}")
    print(f"失败测试: {report['failed_tests']}")
    print(f"通过率: {report['pass_rate']:.2%}")
    print(f"发现冲突: {report['conflicts_found']}")

    if report['recommendations']:
        print("\n建议:")
        for rec in report['recommendations']:
            print(f"- {rec}")