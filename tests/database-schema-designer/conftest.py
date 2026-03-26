"""Database Schema Designer 测试配置和 fixture"""

import pytest


@pytest.fixture
def simple_requirements():
    """简单需求描述"""
    return {
        'requirement': '设计一个用户管理系统，包含用户表和订单表'
    }


@pytest.fixture
def complex_requirements():
    """复杂需求描述"""
    return {
        'requirement': '''
        设计一个电商系统数据库：
        - 用户表：id, 用户名, 邮箱, 注册时间
        - 商品表：id, 名称, 价格, 库存
        - 订单表：id, 用户ID, 商品ID, 数量, 金额, 时间
        - 用户和订单是一对多关系
        - 商品和订单是一对多关系
        '''
    }


@pytest.fixture(scope="session")
def db_schema_module():
    """加载 database-schema-designer 模块"""
    import sys
    import importlib.util
    from pathlib import Path

    skills_dir = Path(__file__).parent.parent.parent / "skills"
    module_path = skills_dir / 'database-schema-designer' / "implementation.py"
    spec = importlib.util.spec_from_file_location(
        "database_schema_designer_implementation",
        module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["database_schema_designer_implementation"] = module
    spec.loader.exec_module(module)
    return module
