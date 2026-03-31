"""
回归测试系统

用于检测优化过程中是否引入新的问题，确保代码质量的稳定性。
"""

import ast
import difflib
 import hashlib
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
import subprocess

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """测试用例"""
    id: str
    name: str
    description: str
    category: str
    file_path: str
    expected_result: Any
    test_code: str
    priority: int = 1  # 1-5, 5为最高
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    test_name: str
    passed: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    baseline_value: Optional[Any] = None
    current_value: Optional[Any] = None
    difference: Optional[float] = None
    severity: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'passed': self.passed,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'baseline_value': self.baseline_value,
            'current_value': self.current_value,
            'difference': self.difference,
            'severity': self.severity
        }


@dataclass
class RegressionReport:
    """回归测试报告"""
    timestamp: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    regression_count: int
    new_issues: int
    fixed_issues: int
    test_results: List[TestResult]
    summary: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)


class TestCaseManager:
    """测试用例管理器"""

    def __init__(self, test_dir: str = "./test_cases"):
        self.test_dir = Path(test_dir)
        self.test_dir.mkdir(exist_ok=True)
        self.test_cases: Dict[str, TestCase] = {}

    def create_test_case(self, name: str, description: str, category: str,
                        file_path: str, expected_result: Any,
                        test_code: str, priority: int = 1,
                        tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """创建测试用例"""
        test_id = hashlib.md5(f"{name}_{category}_{file_path}".encode()).hexdigest()[:16]

        test_case = TestCase(
            id=test_id,
            name=name,
            description=description,
            category=category,
            file_path=file_path,
            expected_result=expected_result,
            test_code=test_code,
            priority=priority,
            tags=tags or [],
            metadata=metadata or {}
        )

        self.test_cases[test_id] = test_case

        # 保存到文件
        self._save_test_case(test_case)

        logger.info(f"Created test case: {name} (ID: {test_id})")
        return test_id

    def _save_test_case(self, test_case: TestCase):
        """保存测试用例到文件"""
        test_file = self.test_dir / f"test_{test_case.id}.json"
        with open(test_file, 'w') as f:
            json.dump({
                'id': test_case.id,
                'name': test_case.name,
                'description': test_case.description,
                'category': test_case.category,
                'file_path': test_case.file_path,
                'expected_result': test_case.expected_result,
                'test_code': test_case.test_code,
                'priority': test_case.priority,
                'tags': test_case.tags,
                'metadata': test_case.metadata,
                'created_at': datetime.now().isoformat()
            }, f, indent=2)

    def load_test_cases(self):
        """加载所有测试用例"""
        for test_file in self.test_dir.glob("test_*.json"):
            try:
                with open(test_file, 'r') as f:
                    data = json.load(f)
                    test_case = TestCase(
                        id=data['id'],
                        name=data['name'],
                        description=data['description'],
                        category=data['category'],
                        file_path=data['file_path'],
                        expected_result=data['expected_result'],
                        test_code=data['test_code'],
                        priority=data['priority'],
                        tags=data['tags'],
                        metadata=data['metadata']
                    )
                    self.test_cases[test_case.id] = test_case
            except Exception as e:
                logger.error(f"Failed to load test case {test_file}: {e}")

    def get_test_cases_by_category(self, category: str) -> List[TestCase]:
        """获取指定类别的测试用例"""
        return [tc for tc in self.test_cases.values() if tc.category == category]

    def get_high_priority_tests(self) -> List[TestCase]:
        """获取高优先级测试用例"""
        return [tc for tc in self.test_cases.values() if tc.priority >= 4]

    def create_default_test_cases(self):
        """创建默认测试用例"""
        # 代码质量测试
        self.create_test_case(
            name="Function Complexity Check",
            description="Check if function complexity is within acceptable limits",
            category="code_quality",
            file_path="*.py",
            expected_result=10,
            test_code="""
def calculate_complexity(code):
    tree = ast.parse(code)
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
            complexity += 1
    return complexity
""",
            priority=5,
            tags=["complexity", "quality"]
        )

        # 安全测试
        self.create_test_case(
            name="Security Risk Detection",
            description="Check for security vulnerabilities in code",
            category="security",
            file_path="*.py",
            expected_result=0,
            test_code="""
def detect_security_issues(code):
    issues = []
    if 'eval(' in code:
        issues.append("eval() usage detected")
    if 'exec(' in code:
        issues.append("exec() usage detected")
    return len(issues)
""",
            priority=5,
            tags=["security", "vulnerability"]
        )

        # 性能测试
        self.create_test_case(
            name="Performance Baseline",
            description="Check if performance metrics meet baseline",
            category="performance",
            file_path="*.py",
            expected_result=1000,  # ms
            test_code="""
def measure_performance(file_path):
    import time
    start = time.time()
    # Simulate processing
    _ = [x**2 for x in range(1000)]
    end = time.time()
    return (end - start) * 1000  # ms
""",
            priority=4,
            tags=["performance", "benchmark"]
        )

        # 兼容性测试
        self.create_test_case(
            name="API Compatibility",
            description="Check if API usage is compatible",
            category="compatibility",
            file_path="*.py",
            expected_result=True,
            test_code="""
def check_api_compatibility(code):
    # Check for deprecated patterns
    deprecated_patterns = ['dict.iteritems()', 'dict.iterkeys()']
    for pattern in deprecated_patterns:
        if pattern in code:
            return False
    return True
""",
            priority=3,
            tags=["compatibility", "api"]
        )


class BaselineManager:
    """基线管理器"""

    def __init__(self, baseline_dir: str = "./baselines"):
        self.baseline_dir = Path(baseline_dir)
        self.baseline_dir.mkdir(exist_ok=True)

    def create_baseline(self, test_case_id: str, value: Any, metadata: Dict[str, Any] = None):
        """创建基线值"""
        baseline_data = {
            'test_case_id': test_case_id,
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {},
            'hash': self._calculate_hash(value)
        }

        baseline_file = self.baseline_dir / f"baseline_{test_case_id}.json"
        with open(baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)

        logger.info(f"Created baseline for test case {test_case_id}")

    def get_baseline(self, test_case_id: str) -> Optional[Any]:
        """获取基线值"""
        baseline_file = self.baseline_dir / f"baseline_{test_case_id}.json"
        if not baseline_file.exists():
            return None

        with open(baseline_file, 'r') as f:
            data = json.load(f)
            return data['value']

    def _calculate_hash(self, value: Any) -> str:
        """计算值的哈希"""
        value_str = str(value).encode('utf-8')
        return hashlib.md5(value_str).hexdigest()

    def compare_with_baseline(self, test_case_id: str, current_value: Any) -> Tuple[bool, Optional[float]]:
        """与基线值比较"""
        baseline_file = self.baseline_dir / f"baseline_{test_case_id}.json"
        if not baseline_file.exists():
            return True, None

        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
            baseline_value = baseline_data['value']

        # 计算差异
        try:
            if isinstance(baseline_value, (int, float)) and isinstance(current_value, (int, float)):
                difference = current_value - baseline_value
                is_regression = abs(difference) > 0.1  # 10%阈值
                return is_regression, difference
            else:
                # 对于非数值类型，直接比较
                is_regression = baseline_value != current_value
                return is_regression, None
        except Exception:
            return True, None


class RegressionTester:
    """回归测试执行器"""

    def __init__(self, test_case_manager: TestCaseManager, baseline_manager: BaselineManager):
        self.test_case_manager = test_case_manager
        self.baseline_manager = baseline_manager
        self.results: List[TestResult] = []

    def run_regression_tests(self, target_files: List[str] = None) -> RegressionReport:
        """运行回归测试"""
        logger.info("Starting regression tests...")
        start_time = datetime.now()

        self.results = []
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        regressions = 0
        new_issues = 0
        fixed_issues = 0

        # 如果没有指定目标文件，使用所有测试用例的文件路径
        if target_files is None:
            target_files = list(set(tc.file_path for tc in self.test_case_manager.test_cases.values()))

        for file_path in target_files:
            logger.info(f"Testing file: {file_path}")

            # 获取相关的测试用例
            relevant_tests = [
                tc for tc in self.test_case_manager.test_cases.values()
                if self._matches_file_pattern(tc.file_path, file_path)
            ]

            for test_case in relevant_tests:
                total_tests += 1
                result = self._run_single_test(test_case, file_path)

                if result.passed:
                    passed_tests += 1
                else:
                    failed_tests += 1

                # 检查是否为回归
                if not result.passed and result.severity == "HIGH":
                    regressions += 1

                self.results.append(result)

        # 计算执行时间
        execution_time = (datetime.now() - start_time).total_seconds()

        # 生成报告
        report = RegressionReport(
            timestamp=start_time,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            regression_count=regressions,
            new_issues=new_issues,
            fixed_issues=fixed_issues,
            test_results=self.results,
            summary={
                'execution_time': execution_time,
                'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'regression_rate': regressions / total_tests if total_tests > 0 else 0
            },
            recommendations=self._generate_recommendations()
        )

        # 保存报告
        self._save_regression_report(report)

        logger.info(f"Regression tests completed: {passed_tests}/{total_tests} passed")
        return report

    def _matches_file_pattern(self, pattern: str, file_path: str) -> bool:
        """检查文件是否匹配模式"""
        if pattern == "*":
            return True

        if pattern.endswith("*.py"):
            return file_path.endswith(".py")

        # 支持简单的通配符
        if "*" in pattern:
            pattern = pattern.replace("*", ".*")
            import re
            return re.match(pattern, file_path) is not None

        return pattern == file_path

    def _run_single_test(self, test_case: TestCase, file_path: str) -> TestResult:
        """运行单个测试"""
        start_time = time.time()

        try:
            # 读取目标文件
            with open(file_path, 'r') as f:
                file_content = f.read()

            # 执行测试代码
            test_globals = {
                'ast': ast,
                'file_content': file_content,
                'file_path': file_path
            }
            test_locals = {}

            exec(test_case.test_code, test_globals, test_locals)

            # 获取测试结果
            current_value = test_locals.get('result', None)

            # 与基线比较
            is_regression, difference = self.baseline_manager.compare_with_baseline(
                test_case.id, current_value
            )

            # 确定严重程度
            severity = self._determine_severity(test_case, difference)

            # 判断是否通过
            if is_regression:
                error_message = f"Regression detected. Baseline: {self.baseline_manager.get_baseline(test_case.id)}, Current: {current_value}"
                passed = False
            elif current_value == test_case.expected_result:
                error_message = None
                passed = True
            else:
                error_message = f"Expected: {test_case.expected_result}, Got: {current_value}"
                passed = False

            execution_time = time.time() - start_time

            return TestResult(
                test_id=test_case.id,
                test_name=test_case.name,
                passed=passed,
                error_message=error_message,
                execution_time=execution_time,
                baseline_value=self.baseline_manager.get_baseline(test_case.id),
                current_value=current_value,
                difference=difference,
                severity=severity
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_id=test_case.id,
                test_name=test_case.name,
                passed=False,
                error_message=str(e),
                execution_time=execution_time,
                severity="CRITICAL"
            )

    def _determine_severity(self, test_case: TestCase, difference: Optional[float]) -> str:
        """确定问题严重程度"""
        if difference is None:
            return "LOW"

        if test_case.category == "security":
            if difference > 0:
                return "CRITICAL"
        elif test_case.category == "performance":
            if difference > 0.5:  # 50%性能下降
                return "HIGH"
            elif difference > 0.2:
                return "MEDIUM"
        elif test_case.category == "code_quality":
            if difference > 0.3:  # 30%质量下降
                return "HIGH"
            elif difference > 0.1:
                return "MEDIUM"

        return "LOW"

    def _generate_recommendations(self) -> List[str]:
        """生成建议"""
        recommendations = []

        # 统计失败测试
        failed_results = [r for r in self.results if not r.passed]
        high_severity = [r for r in failed_results if r.severity in ["HIGH", "CRITICAL"]]

        if len(high_severity) > 0:
            recommendations.append(f"发现 {len(high_severity)} 个高严重性问题，需要立即处理")

        # 统计回归
        regressions = [r for r in self.results if r.severity == "HIGH"]
        if len(regressions) > 0:
            recommendations.append(f"发现 {len(regressions)} 个回归问题，建议回滚相关更改")

        # 性能问题
        performance_issues = [r for r in self.results if r.category == "performance" and not r.passed]
        if len(performance_issues) > 0:
            recommendations.append("性能测试未通过，建议优化性能瓶颈")

        # 通过率
        pass_rate = len([r for r in self.results if r.passed]) / len(self.results) if self.results else 0
        if pass_rate < 0.9:
            recommendations.append(f"测试通过率较低 ({pass_rate:.1%})，建议改进测试覆盖率")

        return recommendations

    def _save_regression_report(self, report: RegressionReport):
        """保存回归测试报告"""
        report_dir = Path("./regression_reports")
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / f"regression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': report.timestamp.isoformat(),
                'total_tests': report.total_tests,
                'passed_tests': report.passed_tests,
                'failed_tests': report.failed_tests,
                'regression_count': report.regression_count,
                'new_issues': report.new_issues,
                'fixed_issues': report.fixed_issues,
                'summary': report.summary,
                'recommendations': report.recommendations,
                'test_results': [r.to_dict() for r in report.test_results]
            }, f, indent=2)

        logger.info(f"Regression report saved to: {report_file}")


class CodeComparator:
    """代码比较器"""

    def __init__(self):
        self.baseline_dir = Path("./code_baselines")
        self.baseline_dir.mkdir(exist_ok=True)

    def create_code_baseline(self, file_path: str, baseline_name: str):
        """创建代码基线"""
        with open(file_path, 'r') as f:
            content = f.read()

        baseline_file = self.baseline_dir / f"{baseline_name}_{Path(file_path).stem}.json"
        with open(baseline_file, 'w') as f:
            json.dump({
                'file_path': str(file_path),
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'hash': hashlib.md5(content.encode()).hexdigest()
            }, f, indent=2)

    def compare_with_baseline(self, file_path: str, baseline_name: str) -> Dict[str, Any]:
        """与基线代码比较"""
        baseline_file = self.baseline_dir / f"{baseline_name}_{Path(file_path).stem}.json"
        if not baseline_file.exists():
            return {'error': 'Baseline not found'}

        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)

        with open(file_path, 'r') as f:
            current_content = f.read()

        # 计算差异
        diff = list(difflib.unified_diff(
            baseline_data['content'].splitlines(keepends=True),
            current_content.splitlines(keepends=True),
            fromfile='baseline',
            tofile='current'
        ))

        # 分析代码变化
        changes = self._analyze_code_changes(
            baseline_data['content'],
            current_content
        )

        return {
            'has_changes': len(diff) > 0,
            'diff': ''.join(diff),
            'changes_summary': changes,
            'baseline_hash': baseline_data['hash'],
            'current_hash': hashlib.md5(current_content.encode()).hexdigest()
        }

    def _analyze_code_changes(self, baseline: str, current: str) -> Dict[str, Any]:
        """分析代码变化"""
        baseline_lines = baseline.split('\n')
        current_lines = current.split('\n')

        changes = {
            'added_lines': 0,
            'removed_lines': 0,
            'modified_lines': 0,
            'functions_added': [],
            'functions_removed': [],
            'complexity_change': 0
        }

        # 计算行数变化
        changes['added_lines'] = len(current_lines) - len(baseline_lines)

        # 检测函数变化（简化版）
        baseline_functions = self._extract_functions(baseline)
        current_functions = self._extract_functions(current)

        changes['functions_added'] = list(set(current_functions) - set(baseline_functions))
        changes['functions_removed'] = list(set(baseline_functions) - set(current_functions))

        # 计算复杂度变化
        baseline_complexity = self._calculate_complexity(baseline)
        current_complexity = self._calculate_complexity(current)
        changes['complexity_change'] = current_complexity - baseline_complexity

        return changes

    def _extract_functions(self, code: str) -> List[str]:
        """提取函数名"""
        functions = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
        except:
            pass
        return functions

    def _calculate_complexity(self, code: str) -> int:
        """计算代码复杂度"""
        try:
            tree = ast.parse(code)
            complexity = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                    complexity += 1
            return complexity
        except:
            return 1


if __name__ == '__main__':
    # 初始化组件
    test_manager = TestCaseManager()
    baseline_manager = BaselineManager()
    tester = RegressionTester(test_manager, baseline_manager)

    # 创建默认测试用例
    test_manager.create_default_test_cases()

    # 创建基线值（需要先运行一次）
    print("Creating baselines...")
    for test_case in test_manager.test_cases.values():
        # 这里可以运行测试获取基线值
        baseline_value = test_case.expected_result
        baseline_manager.create_baseline(test_case.id, baseline_value)

    # 运行回归测试
    print("Running regression tests...")
    report = tester.run_regression_tests()

    # 打印结果
    print(f"\nRegression Test Results:")
    print(f"Total Tests: {report.total_tests}")
    print(f"Passed: {report.passed_tests}")
    print(f"Failed: {report.failed_tests}")
    print(f"Regressions: {report.regression_count}")
    print(f"Pass Rate: {report.summary['pass_rate']:.1%}")

    if report.recommendations:
        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"- {rec}")