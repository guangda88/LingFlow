"""LingFlow 测试根配置和共享 fixture"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Skills 目录路径
SKILLS_DIR = Path(__file__).parent.parent / "skills"


@pytest.fixture(scope="session")
def skills_dir():
    """Skills 目录路径"""
    return SKILLS_DIR


def load_skill_module(skill_name, module_name="implementation"):
    """加载带连字符的 skill 模块

    Args:
        skill_name: skill 目录名 (可能包含连字符)
        module_name: 模块名 (默认 implementation)

    Returns:
        加载的模块对象
    """
    module_path = SKILLS_DIR / skill_name / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"{skill_name.replace('-', '_')}.{module_name}", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{skill_name.replace('-', '_')}.{module_name}"] = module
    spec.loader.exec_module(module)
    return module


# 将加载器添加到 pytest namespace
pytest.load_skill_module = load_skill_module
