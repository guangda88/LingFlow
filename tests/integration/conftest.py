"""
集成测试配置文件

提供共享的pytest fixtures和测试配置。
"""

import sys
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, Mock

import pytest

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入测试fixtures
from tests.integration.fixtures import (
    SAMPLE_PYTHON_CODE,
    SAMPLE_SECURITY_ISSUES,
    TempDirectory,
    create_sample_project,
    get_combined_feedback,
)


@pytest.fixture(scope="session")
def project_root():
    """项目根目录路径"""
    return PROJECT_ROOT


@pytest.fixture
def temp_project() -> Generator[str, None, None]:
    """创建临时测试项目

    Yields:
        临时项目路径
    """
    with TempDirectory() as temp_dir:
        create_sample_project(temp_dir)
        yield temp_dir


@pytest.fixture
def sample_code():
    """示例代码"""
    return SAMPLE_PYTHON_CODE


@pytest.fixture
def security_issues_code():
    """安全问题示例代码"""
    return SAMPLE_SECURITY_ISSUES


@pytest.fixture
def mock_feedback_data():
    """模拟工具反馈数据"""
    return get_combined_feedback()


@pytest.fixture
def mock_semgrep():
    """Mock Semgrep工具"""
    mock = Mock()
    mock.name = "Semgrep"
    mock.tool_type = "security_scanner"

    def mock_run(path, rules=None):
        return [
            {
                "tool_name": "Semgrep",
                "tool_type": "security_scanner",
                "rule_id": "python.lang.security.hardcoded_password",
                "rule_name": "Hardcoded password detected",
                "category": "security",
                "severity": "high",
                "message": "Hardcoded password detected",
                "file_path": "src/auth.py",
                "line": 1,
                "snippet": "password = 'admin123'",
                "suggestion": "Use environment variables",
                "confidence": 0.95,
            }
        ]

    mock.run = mock_run
    return mock


@pytest.fixture
def mock_ruff():
    """Mock Ruff工具"""
    mock = Mock()
    mock.name = "Ruff"
    mock.tool_type = "linter"

    def mock_run(path, rules=None):
        return [
            {
                "tool_name": "Ruff",
                "tool_type": "linter",
                "rule_id": "F401",
                "rule_name": "Unused import",
                "category": "code_quality",
                "severity": "low",
                "message": "Unused import 'os'",
                "file_path": "src/utils.py",
                "line": 3,
                "snippet": "import os",
                "suggestion": "Remove unused import",
                "confidence": 0.85,
            }
        ]

    mock.run = mock_run
    return mock


@pytest.fixture
def mock_bandit():
    """Mock Bandit工具"""
    mock = Mock()
    mock.name = "Bandit"
    mock.tool_type = "security_scanner"

    def mock_run(path, rules=None):
        return [
            {
                "tool_name": "Bandit",
                "tool_type": "security_scanner",
                "rule_id": "B105:hardcoded_password",
                "rule_name": "Possible hardcoded password",
                "category": "security",
                "severity": "high",
                "message": "Possible hardcoded password",
                "file_path": "src/auth.py",
                "line": 1,
                "snippet": "password = 'admin123'",
                "suggestion": "Use secure credential manager",
                "confidence": 0.90,
            }
        ]

    mock.run = mock_run
    return mock


@pytest.fixture
def mock_tools(mock_semgrep, mock_ruff, mock_bandit):
    """所有Mock工具"""
    return {"semgrep": mock_semgrep, "ruff": mock_ruff, "bandit": mock_bandit}


@pytest.fixture
def optimization_config():
    """优化配置"""
    return {
        "n_trials": 10,
        "timeout": 30,
        "early_stopping_patience": 5,
        "min_improvement": 0.01,
        "seed": 42,
        "generate_reports": False,  # 加速测试
    }


@pytest.fixture
def sample_search_space():
    """示例搜索空间"""
    return {
        "max_class_size": {"type": "int", "min": 100, "max": 500},
        "max_method_count": {"type": "categorical", "choices": [10, 15, 20]},
        "max_complexity": {"type": "int", "min": 5, "max": 20},
    }


@pytest.fixture
def sample_objective():
    """示例目标函数（简单的二次函数）"""

    def objective(params):
        x = params.get("max_class_size", 100)
        y = params.get("max_method_count", 10)
        # 简单的目标函数：最小化 (x-300)^2 + (y-15)^2
        return ((x - 300) ** 2 + (y - 15) ** 2) / 10000

    return objective


# pytest标记
pytestmark = [pytest.mark.integration, pytest.mark.slow]


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line("markers", "integration: 集成测试标记")
    config.addinivalue_line("markers", "slow: 慢速测试标记")
    config.addinivalue_line("markers", "phase4: Phase 4测试标记")
    config.addinivalue_line("markers", "phase5: Phase 5测试标记")
