"""Environment Manager 测试配置和 fixture"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_env_dict():
    """示例环境变量字典"""
    return {
        'DATABASE_URL': 'postgresql://localhost/mydb',
        'REDIS_URL': 'redis://localhost/0',
        'DEBUG': 'true',
        'PORT': '8000'
    }


@pytest.fixture
def sample_env_file():
    """示例 .env 文件内容"""
    return """
DATABASE_URL=postgresql://localhost/mydb
REDIS_URL=redis://localhost/0
DEBUG=true
PORT=8000
SECRET_KEY=my-secret-key-12345
"""


@pytest.fixture
def sample_config_yaml():
    """示例 YAML 配置"""
    return """
database:
  host: localhost
  port: 5432
  name: mydb

redis:
  host: localhost
  port: 6379

app:
  debug: true
  port: 8000
"""


@pytest.fixture(scope="session")
def env_manager_module():
    """加载 environment-manager 模块"""
    import sys
    import importlib.util
    from pathlib import Path

    skills_dir = Path(__file__).parent.parent.parent / "skills"
    module_path = skills_dir / 'environment-manager' / "implementation.py"
    spec = importlib.util.spec_from_file_location(
        "environment_manager_implementation",
        module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["environment_manager_implementation"] = module
    spec.loader.exec_module(module)
    return module
