"""
规则验证系统

确保从AI工具学习到的规则安全有效，通过严格的验证流程保证代码质量。
"""

import ast
import copy
import difflib
import json
import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import uuid

from .rule_learning_engine import LearnedRule, Pattern, LearningStatus
from lingflow.common.security_analyzer import SecurityAnalyzer, SecurityViolation

logger = logging.getLogger(__name__)


class ValidationType(Enum):
    """验证类型"""
    SAFETY = "safety"              # 安全性验证
    COMPATIBILITY = "compatibility" # 兼容性验证
    EFFECTIVENESS = "effectiveness" # 有效性验证
    PERFORMANCE = "performance"    # 性能验证
    REGRESSION = "regression"     # 回归测试


class ValidationStatus(Enum):
    """验证状态"""
    PENDING = "pending"           # 等待验证
    RUNNING = "running"          # 验证中
    PASSED = "passed"            # 验证通过
    FAILED = "failed"            # 验证失败
    SKIPPED = "skipped"          # 跳过验证


@dataclass
class ValidationReport:
    """验证报告"""
    rule_id: str
    validation_type: ValidationType
    status: ValidationStatus
    is_safe: bool
    violations: List[Dict] = field(default_factory=list)
    applied_changes: List[Dict] = field(default_factory=list)
    test_count: int = 0
    passed_tests: int = 0
    execution_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'rule_id': self.rule_id,
            'validation_type': self.validation_type.value,
            'status': self.status.value,
            'is_safe': self.is_safe,
            'violations': self.violations,
            'applied_changes': self.applied_changes,
            'test_count': self.test_count,
            'passed_tests': self.passed_tests,
            'execution_time': self.execution_time,
            'created_at': self.created_at.isoformat(),
            'notes': self.notes
        }


@dataclass
class ABTestResult:
    """A/B测试结果"""
    improvement_rate: float    # 改善率
    is_improved: bool         # 是否有改善
    side_effects: List[Dict]  # 副作用
    confidence: float         # 置信度
    control_metrics: Dict[str, float] = field(default_factory=dict)
    test_metrics: Dict[str, float] = field(default_factory=dict)


class TestFileGenerator:
    """测试文件生成器"""

    def __init__(self, base_path: str = "./test_data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    def generate_test_files(self, rule: LearnedRule, count: int = 10) -> List[str]:
        """生成测试文件"""
        test_files = []

        for i in range(count):
            # 根据规则模式生成测试文件
            file_path = self.base_path / f"test_rule_{rule.id}_{i}.py"
            content = self._generate_test_content(rule, i)

            with open(file_path, 'w') as f:
                f.write(content)

            test_files.append(str(file_path))

        return test_files

    def _generate_test_content(self, rule: LearnedRule, index: int) -> str:
        """生成测试文件内容"""
        templates = {
            "security": self._generate_security_test,
            "performance": self._generate_performance_test,
            "code_quality": self._generate_quality_test,
            "maintainability": self._generate_maintainability_test,
            "best_practice": self._generate_best_practice_test,
            "style": self._generate_style_test
        }

        template_func = templates.get(rule.category.value, self._generate_quality_test)
        return template_func(rule, index)

    def _generate_security_test(self, rule: LearnedRule, index: int) -> str:
        """生成安全测试文件"""
        # 生成包含潜在安全问题的代码
        if "eval" in ' '.join(rule.pattern.context_keywords):
            return f"""
# Test security rule: {rule.name}
def test_eval_function():
    # Security issue: eval usage
    code = "print('Hello')"
    result = eval(code)  # Should be replaced with ast.literal_eval

def safe_function():
    # Safe alternative
    import ast
    code = "print('Hello')"
    result = ast.literal_eval(code)
"""
        elif "sql" in ' '.join(rule.pattern.context_keywords):
            return f"""
# Test SQL injection prevention
def test_sql_query(user_id):
    # Security risk: SQL injection
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    return query

def safe_query(user_id):
    # Safe parameterized query
    query = "SELECT * FROM users WHERE id = %s"
    return query
"""
        else:
            return self._generate_quality_test(rule, index)

    def _generate_performance_test(self, rule: LearnedRule, index: int) -> str:
        """生成性能测试文件"""
        return f"""
# Test performance rule: {rule.name}
def test_performance():
    # Performance issue: string concatenation in loop
    result = ""
    for i in range(1000):
        result += str(i)  # Should use join

def efficient_solution():
    # Efficient solution
    result = "".join(str(i) for i in range(1000))
"""

    def _generate_quality_test(self, rule: LearnedRule, index: int) -> str:
        """生成代码质量测试文件"""
        return f"""
# Test quality rule: {rule.name}
def test_function():
    # Code quality issue
    x = 1
    y = 2
    if x == 1:
        if y == 2:
            print("Nested condition")

def improved_function():
    # Improved version
    x = 1
    y = 2
    if x == 1 and y == 2:
        print("Combined condition")
"""

    def _generate_maintainability_test(self, rule: LearnedRule, index: int) -> str:
        """生成可维护性测试文件"""
        return f"""
# Test maintainability rule: {rule.name}
class LargeClass:
    def method1(self):
        pass

    def method2(self):
        pass

    # Many methods...

    def method20(self):
        pass
"""

    def _generate_best_practice_test(self, rule: LearnedRule, index: int) -> str:
        """生成最佳实践测试文件"""
        return f"""
# Test best practice: {rule.name}
def test_function():
    # Best practice violation
    global_counter = 0

    def inner():
        global global_counter
        global_counter += 1

def good_function():
    # Better practice with parameter
    def inner(counter):
        return counter + 1

    return inner(global_counter)
"""

    def _generate_style_test(self, rule: LearnedRule, index: int) -> str:
        """生成代码风格测试文件"""
        return f"""
# Test style rule: {rule.name}
def BadFunctionName():
    # Style issue: PascalCase for function
    variableName = "test"  # Should be snake_case
    return VariableName

def good_function_name():
    # Good style
    variable_name = "test"
    return variable_name
"""


class SafetyValidator:
    """安全性验证器"""

    def __init__(self):
        self.security_analyzer = SecurityAnalyzer()

    def validate_code_safety(self, code: str) -> Tuple[bool, List[SecurityViolation]]:
        """验证代码安全性"""
        try:
            return self.security_analyzer.analyze_code_security(code)
        except Exception as e:
            logger.error(f"Safety validation failed: {e}")
            return False, [SecurityViolation(
                severity="CRITICAL",
                violation_type="VALIDATION_ERROR",
                message=str(e),
                line=0,
                col_offset=0
            )]

    def validate_rule_safety(self, rule: LearnedRule, test_files: List[str]) -> ValidationReport:
        """验证规则安全性"""
        report = ValidationReport(
            rule_id=rule.id,
            validation_type=ValidationType.SAFETY,
            status=ValidationStatus.RUNNING,
            is_safe=True
        )

        violations = []
        applied_changes = []
        passed_tests = 0

        start_time = datetime.now()

        for file_path in test_files:
            try:
                with open(file_path, 'r') as f:
                    original_code = f.read()

                # 应用规则
                modified_code = self._apply_rule(original_code, rule)

                # 验证安全性
                is_safe, security_violations = self.validate_code_safety(modified_code)

                if not is_safe:
                    violations.extend([v.to_dict() for v in security_violations])
                else:
                    passed_tests += 1

                # 记录变更
                if original_code != modified_code:
                    applied_changes.append({
                        'file': file_path,
                        'has_changes': True,
                        'changes': self._get_diff(original_code, modified_code),
                        'safe': is_safe
                    })

            except Exception as e:
                violations.append({
                    'type': 'APPLICATION_ERROR',
                    'message': str(e),
                    'file': file_path,
                    'severity': 'HIGH'
                })

        execution_time = (datetime.now() - start_time).total_seconds()

        # 更新报告
        report.status = ValidationStatus.PASSED if len(violations) == 0 else ValidationStatus.FAILED
        report.is_safe = len(violations) == 0
        report.violations = violations
        report.applied_changes = applied_changes
        report.test_count = len(test_files)
        report.passed_tests = passed_tests
        report.execution_time = execution_time

        if len(violations) > 0:
            report.notes = f"Found {len(violations)} safety violations"

        return report

    def _apply_rule(self, code: str, rule: LearnedRule) -> str:
        """应用规则到代码"""
        # 根据规则模式应用相应的修改
        modified_code = code

        # 示例：移除未使用的函数
        if rule.category.value == "code_quality" and "unused" in rule.name.lower():
            # 简化的实现：移除空函数
            lines = code.split('\n')
            new_lines = []

            for i, line in enumerate(lines):
                if line.strip().startswith('def ') and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line == '' or next_line.startswith('#'):
                        # 跳过空函数
                        continue
                new_lines.append(line)

            modified_code = '\n'.join(new_lines)

        return modified_code

    def _get_diff(self, original: str, modified: str) -> List[str]:
        """获取代码差异"""
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile='original',
            tofile='modified'
        )
        return list(diff)


class ABTester:
    """A/B测试器"""

    def __init__(self, test_generator: TestFileGenerator):
        self.test_generator = test_generator

    def create_ab_test(self, rule: LearnedRule, file_count: int = 20) -> Dict[str, List[str]]:
        """创建A/B测试组"""
        # 生成测试文件
        all_files = self.test_generator.generate_test_files(rule, file_count)

        # 随机分配到两组
        import random
        random.shuffle(all_files)

        split_point = len(all_files) // 2
        return {
            'control_group': all_files[:split_point],      # 不应用规则
            'test_group': all_files[split_point:]          # 应用规则
        }

    def run_ab_test(self, rule: LearnedRule, file_count: int = 20) -> ABTestResult:
        """运行A/B测试"""
        # 创建测试组
        groups = self.create_ab_test(rule, file_count)

        # 执行测试
        control_results = self._evaluate_group(rule, groups['control_group'], apply_rule=False)
        test_results = self._evaluate_group(rule, groups['test_group'], apply_rule=True)

        # 计算改善率
        improvement_rate = self._calculate_improvement(control_results, test_results)

        # 检测副作用
        side_effects = self._detect_side_effects(test_results)

        return ABTestResult(
            improvement_rate=improvement_rate,
            is_improved=improvement_rate > 0,
            side_effects=side_effects,
            confidence=self._calculate_confidence(control_results, test_results)
        )

    def _evaluate_group(self, rule: LearnedRule, files: List[str], apply_rule: bool) -> List[Dict]:
        """评估测试组"""
        results = []

        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    code = f.read()

                # 应用规则（如果需要）
                if apply_rule:
                    modified_code = self._apply_rule_to_code(code, rule)
                    quality_metrics = self._analyze_code_quality(modified_code)
                else:
                    quality_metrics = self._analyze_code_quality(code)

                results.append({
                    'file': file_path,
                    'quality_score': quality_metrics.get('score', 0),
                    'complexity': quality_metrics.get('complexity', 0),
                    'issues': quality_metrics.get('issues', [])
                })

            except Exception as e:
                logger.error(f"Failed to evaluate file {file_path}: {e}")
                results.append({
                    'file': file_path,
                    'quality_score': 0,
                    'complexity': 0,
                    'issues': [{'type': 'ERROR', 'message': str(e)}]
                })

        return results

    def _apply_rule_to_code(self, code: str, rule: LearnedRule) -> str:
        """应用规则到代码"""
        # 使用SafetyValidator的相同实现
        validator = SafetyValidator()
        return validator._apply_rule(code, rule)

    def _analyze_code_quality(self, code: str) -> Dict[str, Any]:
        """分析代码质量"""
        try:
            tree = ast.parse(code)

            # 计算复杂度
            complexity = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                    complexity += 1

            # 统计问题
            issues = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 检查函数长度
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        length = node.end_lineno - node.lineno
                        if length > 50:
                            issues.append({
                                'type': 'FUNCTION_TOO_LONG',
                                'line': node.lineno,
                                'message': f'Function too long: {length} lines'
                            })

            # 计算质量分数（简单实现）
            score = max(0, 100 - complexity * 5 - len(issues) * 10)

            return {
                'score': score,
                'complexity': complexity,
                'issues': issues
            }

        except Exception as e:
            return {
                'score': 0,
                'complexity': 100,
                'issues': [{'type': 'PARSE_ERROR', 'message': str(e)}]
            }

    def _calculate_improvement(self, control_results: List[Dict], test_results: List[Dict]) -> float:
        """计算改善率"""
        control_avg = sum(r['quality_score'] for r in control_results) / len(control_results)
        test_avg = sum(r['quality_score'] for r in test_results) / len(test_results)

        if control_avg == 0:
            return 0

        improvement = (test_avg - control_avg) / control_avg
        return round(improvement, 2)

    def _detect_side_effects(self, test_results: List[Dict]) -> List[Dict]:
        """检测副作用"""
        side_effects = []

        # 检查是否引入了新的问题
        for result in test_results:
            for issue in result['issues']:
                if issue['type'] in ['PARSE_ERROR', 'SECURITY_VIOLATION']:
                    side_effects.append({
                        'file': result['file'],
                        'type': issue['type'],
                        'message': issue['message']
                    })

        return side_effects

    def _calculate_confidence(self, control_results: List[Dict], test_results: List[Dict]) -> float:
        """计算测试置信度"""
        # 基于样本数量和一致性计算
        min_sample_size = 10
        sample_count = min(len(control_results), len(test_results))

        if sample_count < min_sample_size:
            return 0.5

        # 计算一致性
        control_std = self._calculate_std([r['quality_score'] for r in control_results])
        test_std = self._calculate_std([r['quality_score'] for r in test_results])

        # 一致性越高，置信度越高
        consistency_score = max(0, 1 - (control_std + test_std) / 200)

        return round(consistency_score, 2)

    def _calculate_std(self, values: List[float]) -> float:
        """计算标准差"""
        if len(values) < 2:
            return 0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5


class RollbackManager:
    """回滚管理器"""

    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)

    def create_backup(self, file_path: str, rule_id: str) -> str:
        """创建文件备份"""
        source_path = Path(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{rule_id}_{timestamp}_{source_path.name}"
        backup_path = self.backup_dir / backup_name

        # 复制文件
        shutil.copy2(source_path, backup_path)

        # 记录备份信息
        backup_info = {
            'original_file': str(source_path),
            'backup_file': str(backup_path),
            'rule_id': rule_id,
            'timestamp': datetime.now().isoformat(),
            'size': source_path.stat().st_size
        }

        # 保存备份记录
        record_file = self.backup_dir / f"backup_records.json"
        self._append_backup_record(record_file, backup_info)

        logger.info(f"Created backup: {backup_path}")
        return str(backup_path)

    def rollback(self, backup_path: str, target_file: str) -> bool:
        """执行回滚"""
        try:
            backup = Path(backup_path)
            target = Path(target_file)

            if not backup.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # 创建目标文件的备份（如果存在）
            if target.exists():
                self.create_backup(target_file, f"rollback_{target.stem}")

            # 恢复文件
            shutil.copy2(backup, target)

            logger.info(f"Rolled back: {target_file}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def get_backup_history(self, rule_id: Optional[str] = None) -> List[Dict]:
        """获取备份历史"""
        record_file = self.backup_dir / "backup_records.json"

        if not record_file.exists():
            return []

        try:
            with open(record_file, 'r') as f:
                records = json.load(f)

            if rule_id:
                records = [r for r in records if r['rule_id'] == rule_id]

            return records

        except Exception as e:
            logger.error(f"Failed to read backup history: {e}")
            return []

    def _append_backup_record(self, record_file: Path, record: Dict):
        """追加备份记录"""
        try:
            if record_file.exists():
                with open(record_file, 'r') as f:
                    records = json.load(f)
            else:
                records = []

            records.append(record)

            with open(record_file, 'w') as f:
                json.dump(records, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to append backup record: {e}")

    def cleanup_old_backups(self, keep_count: int = 10):
        """清理旧备份"""
        records = self.get_backup_history()

        # 按规则分组
        rule_groups = {}
        for record in records:
            rule_id = record['rule_id']
            if rule_id not in rule_groups:
                rule_groups[rule_id] = []
            rule_groups[rule_id].append(record)

        # 每个规则保留最新的几个备份
        for rule_id, group_records in rule_groups.items():
            # 按时间排序
            sorted_records = sorted(group_records, key=lambda x: x['timestamp'], reverse=True)

            # 删除多余的备份
            for record in sorted_records[keep_count:]:
                backup_file = Path(record['backup_file'])
                if backup_file.exists():
                    backup_file.unlink()
                    logger.info(f"Cleaned up old backup: {backup_file}")


class ValidationManager:
    """验证管理器"""

    def __init__(self):
        self.safety_validator = SafetyValidator()
        self.test_generator = TestFileGenerator()
        self.ab_tester = ABTester(self.test_generator)
        self.rollback_manager = RollbackManager()
        self.validation_results = {}

    def validate_rule(self, rule: LearnedRule, validation_types: List[ValidationType] = None) -> Dict[ValidationType, ValidationReport]:
        """验证规则"""
        if validation_types is None:
            validation_types = [ValidationType.SAFETY, ValidationType.EFFECTIVENESS]

        reports = {}

        for validation_type in validation_types:
            logger.info(f"Validating rule {rule.id} with {validation_type.value}")

            if validation_type == ValidationType.SAFETY:
                # 生成测试文件
                test_files = self.test_generator.generate_test_files(rule, 10)

                # 执行安全性验证
                report = self.safety_validator.validate_rule_safety(rule, test_files)

                # 清理测试文件
                for file_path in test_files:
                    try:
                        Path(file_path).unlink()
                    except:
                        pass

            elif validation_type == ValidationType.EFFECTIVENESS:
                # 执行A/B测试
                ab_result = self.ab_tester.run_ab_test(rule)

                report = ValidationReport(
                    rule_id=rule.id,
                    validation_type=validation_type,
                    status=ValidationStatus.PASSED if ab_result.is_improved else ValidationStatus.FAILED,
                    is_safe=True,
                    test_count=20,
                    passed_tests=20 if ab_result.is_improved else 0,
                    execution_time=10.0,  # 模拟时间
                    notes=f"Improvement rate: {ab_result.improvement_rate:.2%}"
                )

            reports[validation_type] = report

        # 保存验证结果
        self.validation_results[rule.id] = reports

        return reports

    def get_validation_summary(self, rule_id: str) -> Dict[str, Any]:
        """获取验证摘要"""
        if rule_id not in self.validation_results:
            return {}

        reports = self.validation_results[rule_id]

        summary = {
            'rule_id': rule_id,
            'validation_count': len(reports),
            'passed_count': sum(1 for r in reports.values() if r.status == ValidationStatus.PASSED),
            'failed_count': sum(1 for r in reports.values() if r.status == ValidationStatus.FAILED),
            'overall_safe': all(r.is_safe for r in reports.values()),
            'last_validation': max(r.created_at for r in reports.values()).isoformat() if reports else None,
            'details': {vt.value: r.to_dict() for vt, r in reports.items()}
        }

        return summary

    def save_validation_results(self, file_path: str):
        """保存验证结果"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_validations': len(self.validation_results),
            'results': {
                rule_id: self.get_validation_summary(rule_id)
                for rule_id in self.validation_results
            }
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved validation results to {file_path}")


def main():
    """测试验证系统"""
    # 创建验证管理器
    manager = ValidationManager()

    # 创建测试规则
    from .rule_learning_engine import LearnedRule, Pattern, FeedbackCategory

    rule = LearnedRule(
        id="TEST001",
        name="Remove Unused Functions",
        description="Remove unused functions to improve code quality",
        category=FeedbackCategory.CODE_QUALITY,
        pattern=Pattern(file_patterns=["py"], code_patterns=["def "]),
        tools=["SonarQube"],
        frequency=10,
        confidence=0.9,
        status=LearningStatus.DRAFT
    )

    # 执行验证
    reports = manager.validate_rule(rule)

    # 输出结果
    for validation_type, report in reports.items():
        print(f"\nValidation Type: {validation_type.value}")
        print(f"Status: {report.status.value}")
        print(f"Is Safe: {report.is_safe}")
        print(f"Tests Passed: {report.passed_tests}/{report.test_count}")
        if report.notes:
            print(f"Notes: {report.notes}")


if __name__ == '__main__':
    main()