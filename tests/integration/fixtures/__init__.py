"""
集成测试共享fixtures

提供测试数据、Mock对象和工具函数。
"""

from pathlib import Path
from typing import Dict, List, Any
import tempfile
import shutil

from lingflow.self_optimizer.phase5.models import ToolType, FeedbackCategory, SeverityLevel

# 测试数据目录
FIXTURES_DIR = Path(__file__).parent
CODE_SAMPLES_DIR = FIXTURES_DIR / "code_samples"
SNAPSHOTS_DIR = Path(__file__).parent.parent.parent / "lingflow" / "testing" / "fixtures" / "snapshots"


class TempDirectory:
    """临时目录上下文管理器"""

    def __init__(self):
        self.temp_dir = None

    def __enter__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="lingflow_e2e_")
        return self.temp_dir

    def __exit__(self, *args):
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)


# 示例代码片段
SAMPLE_PYTHON_CODE = """
def calculate_factorial(n):
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

class DataProcessor:
    def __init__(self, data):
        self.data = data
        self.cache = {}

    def process(self):
        results = []
        for item in self.data:
            if item in self.cache:
                results.append(self.cache[item])
            else:
                processed = self._process_item(item)
                self.cache[item] = processed
                results.append(processed)
        return results

    def _process_item(self, item):
        return item * 2
"""

SAMPLE_SECURITY_ISSUES = """
import os

# 硬编码密码
password = "admin123"
api_key = "sk-1234567890abcdef"

# SQL注入风险
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return execute_query(query)

# 不安全的随机数
import random
secret_token = random.random()
"""

SAMPLE_PERFORMANCE_ISSUES = """
def inefficient_duplicate_check(items):
    \"\"\"Inefficient duplicate check\"\"\"
    duplicates = []
    for i, item1 in enumerate(items):
        for j, item2 in enumerate(items):
            if i != j and item1 == item2:
                duplicates.append(item1)
    return duplicates

def memory_intensive_operation(data):
    \"\"\"Memory intensive operation\"\"\"
    results = []
    for item in data:
        # 不必要的列表复制
        temp_list = list(data)
        processed = process_item(item)
        results.append(processed)
    return results
"""


# 模拟工具反馈数据
MOCK_SEMGREP_FEEDBACK = [
    {
        "tool_name": "Semgrep",
        "tool_type": ToolType.SECURITY_SCANNER,
        "rule_id": "python.lang.security.hardcoded_password",
        "rule_name": "Hardcoded password detected",
        "category": FeedbackCategory.SECURITY,
        "severity": SeverityLevel.HIGH,
        "message": "Hardcoded password detected in source code",
        "file_path": "src/auth.py",
        "line": 45,
        "snippet": "password = 'admin123'",
        "suggestion": "Use environment variables for credentials",
        "confidence": 0.95
    },
    {
        "tool_name": "Semgrep",
        "tool_type": ToolType.SECURITY_SCANNER,
        "rule_id": "python.lang.security.sql_injection",
        "rule_name": "SQL injection risk",
        "category": FeedbackCategory.SECURITY,
        "severity": SeverityLevel.CRITICAL,
        "message": "Possible SQL injection vulnerability",
        "file_path": "src/database.py",
        "line": 23,
        "snippet": 'query = f"SELECT * FROM users WHERE id = {user_id}"',
        "suggestion": "Use parameterized queries",
        "confidence": 0.90
    }
]

MOCK_RUFF_FEEDBACK = [
    {
        "tool_name": "Ruff",
        "tool_type": ToolType.LINTING,
        "rule_id": "F401",
        "rule_name": "Unused import",
        "category": FeedbackCategory.CODE_QUALITY,
        "severity": SeverityLevel.LOW,
        "message": "Unused import 'os'",
        "file_path": "src/utils.py",
        "line": 3,
        "snippet": "import os",
        "suggestion": "Remove unused import",
        "confidence": 0.85
    },
    {
        "tool_name": "Ruff",
        "tool_type": ToolType.LINTING,
        "rule_id": "E501",
        "rule_name": "Line too long",
        "category": FeedbackCategory.CODE_QUALITY,
        "severity": SeverityLevel.LOW,
        "message": "Line too long (120 > 100)",
        "file_path": "src/utils.py",
        "line": 45,
        "snippet": "long_line_with_many_characters_here = '...'",
        "suggestion": "Break line into multiple lines",
        "confidence": 0.90
    }
]

MOCK_BANDIT_FEEDBACK = [
    {
        "tool_name": "Bandit",
        "tool_type": ToolType.SECURITY_SCANNER,
        "rule_id": "B105:hardcoded_password",
        "rule_name": "Possible hardcoded password",
        "category": FeedbackCategory.SECURITY,
        "severity": SeverityLevel.HIGH,
        "message": "Possible hardcoded password: 'admin123'",
        "file_path": "src/auth.py",
        "line": 45,
        "snippet": "password = 'admin123'",
        "suggestion": "Use a secure credential manager",
        "confidence": 0.90
    }
]


def create_sample_project(target_dir: str) -> None:
    """创建示例项目结构

    Args:
        target_dir: 目标目录路径
    """
    target_path = Path(target_dir)

    # 创建目录结构
    (target_path / "src").mkdir(parents=True, exist_ok=True)
    (target_path / "tests").mkdir(exist_ok=True)

    # 创建示例文件
    (target_path / "src" / "auth.py").write_text(SAMPLE_SECURITY_ISSUES)
    (target_path / "src" / "utils.py").write_text(SAMPLE_PYTHON_CODE)
    (target_path / "src" / "processor.py").write_text(SAMPLE_PERFORMANCE_ISSUES)
    (target_path / "src" / "__init__.py").write_text("")
    (target_path / "tests" / "__init__.py").write_text("")


def get_combined_feedback() -> List[Dict[str, Any]]:
    """获取所有工具的反馈数据"""
    return MOCK_SEMGREP_FEEDBACK + MOCK_RUFF_FEEDBACK + MOCK_BANDIT_FEEDBACK


__all__ = [
    "TempDirectory",
    "SAMPLE_PYTHON_CODE",
    "SAMPLE_SECURITY_ISSUES",
    "SAMPLE_PERFORMANCE_ISSUES",
    "MOCK_SEMGREP_FEEDBACK",
    "MOCK_RUFF_FEEDBACK",
    "MOCK_BANDIT_FEEDBACK",
    "create_sample_project",
    "get_combined_feedback",
    "FIXTURES_DIR",
    "CODE_SAMPLES_DIR",
    "SNAPSHOTS_DIR",
]
