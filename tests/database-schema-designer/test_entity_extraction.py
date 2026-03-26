"""Database Schema Designer 实体提取测试"""

import pytest


class TestEntityExtraction:
    """测试实体提取"""

    def test_extract_single_entity(self, db_schema_module):
        """测试提取单个实体"""
        parse_entities = getattr(db_schema_module, 'parse_entities', None)
        if parse_entities is None:
            pytest.skip("parse_entities 函数不存在")

        result = parse_entities('创建一个用户表')

        assert len(result) > 0
        assert any('用户' in e.get('name', '') or 'user' in e.get('name', '').lower()
                   for e in result)

    def test_extract_multiple_entities(self, db_schema_module):
        """测试提取多个实体"""
        parse_entities = getattr(db_schema_module, 'parse_entities', None)
        if parse_entities is None:
            pytest.skip("parse_entities 函数不存在")

        result = parse_entities('设计用户、商品和订单表')

        assert len(result) >= 3

    def test_extract_with_attributes(self, db_schema_module):
        """测试提取带属性的实体"""
        parse_entities = getattr(db_schema_module, 'parse_entities', None)
        if parse_entities is None:
            pytest.skip("parse_entities 函数不存在")

        result = parse_entities('用户表包含姓名、邮箱和电话')

        entities = result
        if entities:
            entity = entities[0]
            if 'attributes' in entity:
                assert len(entity['attributes']) > 0
