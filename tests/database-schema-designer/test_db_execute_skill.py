"""Database Schema Designer execute_skill 函数测试"""

import pytest


class TestExecuteSkill:
    """测试 execute_skill 函数"""

    def test_generate_simple_schema(self, db_schema_module, simple_requirements):
        """测试生成简单数据库模式"""
        execute_skill = db_schema_module.execute_skill
        result = execute_skill(simple_requirements)

        assert 'error' not in result
        # 响应包含 design 键
        assert 'design' in result
        assert 'ddl' in result
        assert 'er_diagram' in result

    def test_generate_complex_schema(self, db_schema_module, complex_requirements):
        """测试生成复杂数据库模式"""
        execute_skill = db_schema_module.execute_skill
        result = execute_skill(complex_requirements)

        assert 'error' not in result
        assert 'design' in result
        assert len(result['design']['entities']) >= 2
        assert 'ddl' in result
        # DDL 应该包含 MySQL 或 PostgreSQL（不区分大小写）
        assert 'mysql' in result['ddl'].lower() or 'postgresql' in result['ddl'].lower()

    def test_output_format(self, db_schema_module):
        """测试不同数据库格式"""
        execute_skill = db_schema_module.execute_skill
        result = execute_skill({
            'requirement': '用户表',
            'database_type': 'postgresql'
        })

        assert 'error' not in result
        assert 'ddl' in result

    def test_er_diagram_generation(self, db_schema_module):
        """测试 ER 图生成"""
        execute_skill = db_schema_module.execute_skill
        result = execute_skill({
            'requirement': '用户表和订单表，用户有一个或多个订单'
        })

        assert 'error' not in result
        assert 'er_diagram' in result
        # ER 图以 "erDiagram" 开头
        assert result['er_diagram'].startswith('erDiagram')

    def test_empty_requirement(self, db_schema_module):
        """测试空需求"""
        execute_skill = db_schema_module.execute_skill
        result = execute_skill({'requirement': ''})

        assert 'error' in result or 'design' in result  # 可能使用默认值
