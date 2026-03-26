"""CI/CD Orchestrator 测试配置和 fixture"""

import pytest
from pathlib import Path


@pytest.fixture
def temp_output_dir(tmp_path):
    """临时输出目录 fixture"""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


@pytest.fixture
def github_params():
    """GitHub Actions 参数"""
    return {
        'action': 'generate',
        'platform': 'github',
        'language': 'python',
        'stages': ['test', 'build'],
        'output_file': None
    }


@pytest.fixture
def jenkins_params():
    """Jenkins 参数"""
    return {
        'action': 'generate',
        'platform': 'jenkins',
        'language': 'javascript',
        'stages': ['test', 'build']
    }


@pytest.fixture
def gitlab_params():
    """GitLab CI 参数"""
    return {
        'action': 'generate',
        'platform': 'gitlab',
        'language': 'go',
        'stages': ['test', 'build', 'deploy'],
        'deploy_target': 'docker'
    }


@pytest.fixture(scope="session")
def ci_cd_module():
    """加载 ci-cd-orchestrator 模块"""
    import sys
    import importlib.util
    from pathlib import Path

    skills_dir = Path(__file__).parent.parent.parent / "skills"
    module_path = skills_dir / 'ci-cd-orchestrator' / "implementation.py"
    spec = importlib.util.spec_from_file_location(
        "ci_cd_orchestrator_implementation",
        module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["ci_cd_orchestrator_implementation"] = module
    spec.loader.exec_module(module)
    return module
