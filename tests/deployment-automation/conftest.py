"""Deployment Automation 测试配置和 fixture"""

from pathlib import Path

import pytest


@pytest.fixture
def temp_output_dir(tmp_path):
    """临时输出目录 fixture"""
    output_dir = tmp_path / "deployment"
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


@pytest.fixture
def docker_params():
    """Docker 部署参数"""
    return {"action": "generate", "deployment_type": "docker", "language": "python"}


@pytest.fixture
def kubernetes_params():
    """Kubernetes 部署参数"""
    return {"action": "generate", "deployment_type": "kubernetes", "language": "node"}


@pytest.fixture
def blue_green_params():
    """蓝绿部署参数"""
    return {"action": "generate", "deployment_type": "blue-green", "language": "python"}


@pytest.fixture(scope="session")
def deployment_module():
    """加载 deployment-automation 模块"""
    import importlib.util
    import sys
    from pathlib import Path

    skills_dir = Path(__file__).parent.parent.parent / "skills"
    module_path = skills_dir / "deployment-automation" / "implementation.py"
    spec = importlib.util.spec_from_file_location("deployment_automation_implementation", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["deployment_automation_implementation"] = module
    spec.loader.exec_module(module)
    return module
