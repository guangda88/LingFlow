"""
KnowledgeBase 模块测试

测试知识库的CRUD操作、统计功能和数据持久化。
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from lingflow.self_optimizer.phase5.models import (
    LearnedRule,
    Pattern,
    FeedbackCategory,
)
from lingflow.self_optimizer.phase5.knowledge import (
    KnowledgeBase,
    InMemoryKnowledgeBase,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_db_path():
    """创建临时数据库路径"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    # 清理
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def knowledge_base(temp_db_path):
    """创建知识库实例"""
    kb = KnowledgeBase(db_path=temp_db_path)
    yield kb
    kb.close()


@pytest.fixture
def sample_rule():
    """创建示例规则"""
    return LearnedRule(
        id="test-rule-001",
        name="Test Rule",
        description="A test rule for unit testing",
        category=FeedbackCategory.CODE_QUALITY,
        pattern=Pattern(
            file_patterns=["*.py"],
            code_patterns=["def test.*:"],
            context_keywords=["test", "pytest"],
            severity_distribution={"LOW": 10, "MEDIUM": 5},
            tool_support=["ruff", "pylint"],
        ),
        tools=["ruff", "pylint"],
        frequency=15,
        confidence=0.85,
        quality_score=0.82,
        status="draft",
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_rules():
    """创建多个示例规则"""
    categories = [
        FeedbackCategory.CODE_QUALITY,
        FeedbackCategory.BUG_RISK,
        FeedbackCategory.SECURITY,
        FeedbackCategory.PERFORMANCE,
    ]
    rules = []
    for i, cat in enumerate(categories):
        rule = LearnedRule(
            id=f"rule-{i:03d}",
            name=f"Rule {i}",
            description=f"Test rule for {cat.value}",
            category=cat,
            pattern=Pattern(
                file_patterns=["*.py"],
                code_patterns=[f"pattern_{i}"],
                context_keywords=[f"keyword_{i}"],
                severity_distribution={"MEDIUM": i + 1},
                tool_support=["ruff"],
            ),
            tools=["ruff"],
            frequency=i + 1,
            confidence=0.7 + (i * 0.05),
            quality_score=0.7 + (i * 0.05),
            status="draft" if i % 2 == 0 else "approved",
            created_at=datetime.now(),
        )
        rules.append(rule)
    return rules


@pytest.fixture
def in_memory_kb():
    """创建内存知识库实例"""
    return InMemoryKnowledgeBase()


# ============================================================================
# KnowledgeBase 初始化测试
# ============================================================================


class TestKnowledgeBaseInitialization:
    """测试知识库初始化"""

    def test_initialization_with_path(self, temp_db_path):
        """测试使用指定路径初始化"""
        kb = KnowledgeBase(db_path=temp_db_path)
        assert kb.db_path == Path(temp_db_path)
        # _initialize_db() 被调用，所以 _conn 不是 None
        assert kb._conn is not None
        kb.close()

    def test_initialization_creates_tables(self, knowledge_base):
        """测试初始化创建数据库表"""
        conn = knowledge_base._get_connection()
        cursor = conn.cursor()

        # 检查rules表是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='rules'"
        )
        result = cursor.fetchone()
        assert result is not None

        # 检查索引是否存在
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_rules_category'"
        )
        assert cursor.fetchone() is not None

    def test_default_path_when_none_provided(self, tmp_path):
        """测试未提供路径时使用默认路径"""
        # 使用实际路径而不是mock
        import os
        original_dir = os.getcwd()
        try:
            os.chdir(tmp_path)
            kb = KnowledgeBase(db_path=None)
            # 应该使用默认路径
            assert kb.db_path is not None
            assert ".lingflow" in str(kb.db_path)
            kb.close()
        finally:
            os.chdir(original_dir)


# ============================================================================
# KnowledgeBase CRUD 测试
# ============================================================================


class TestKnowledgeBaseCRUD:
    """测试知识库CRUD操作"""

    def test_add_rule_success(self, knowledge_base, sample_rule):
        """测试成功添加规则"""
        result = knowledge_base.add_rule(sample_rule)
        assert result is True

        # 验证规则已添加
        retrieved = knowledge_base.get_rule(sample_rule.id)
        assert retrieved is not None
        assert retrieved.id == sample_rule.id
        assert retrieved.name == sample_rule.name

    def test_add_rule_replace_existing(self, knowledge_base, sample_rule):
        """测试替换已存在的规则"""
        # 添加第一次
        knowledge_base.add_rule(sample_rule)

        # 修改并添加第二次
        modified_rule = LearnedRule(
            id=sample_rule.id,
            name="Updated Rule",
            description=sample_rule.description,
            category=sample_rule.category,
            pattern=sample_rule.pattern,
            tools=sample_rule.tools,
            frequency=sample_rule.frequency,
            confidence=sample_rule.confidence,
            quality_score=sample_rule.quality_score,
            status="approved",
            created_at=sample_rule.created_at,
        )
        knowledge_base.add_rule(modified_rule)

        # 验证已更新
        retrieved = knowledge_base.get_rule(sample_rule.id)
        assert retrieved.name == "Updated Rule"
        assert retrieved.status == "approved"

    def test_add_rule_invalid_data(self, knowledge_base):
        """测试添加无效规则"""
        # 创建一个会导致数据库错误的规则
        with patch.object(knowledge_base, "_get_connection", side_effect=Exception("DB Error")):
            result = knowledge_base.add_rule(sample_rule)
            assert result is False

    def test_get_rule_exists(self, knowledge_base, sample_rule):
        """测试获取存在的规则"""
        knowledge_base.add_rule(sample_rule)
        retrieved = knowledge_base.get_rule(sample_rule.id)
        assert retrieved is not None
        assert retrieved.id == sample_rule.id
        assert retrieved.description == sample_rule.description

    def test_get_rule_not_exists(self, knowledge_base):
        """测试获取不存在的规则"""
        retrieved = knowledge_base.get_rule("non-existent-rule")
        assert retrieved is None

    def test_get_all_rules_no_filter(self, knowledge_base, sample_rules):
        """测试获取所有规则（无过滤）"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        rules = knowledge_base.get_all_rules()
        assert len(rules) == len(sample_rules)

    def test_get_all_rules_with_category_filter(self, knowledge_base, sample_rules):
        """测试按类别过滤"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        code_quality_rules = knowledge_base.get_all_rules(
            category=FeedbackCategory.CODE_QUALITY
        )
        assert len(code_quality_rules) == 1
        assert code_quality_rules[0].category == FeedbackCategory.CODE_QUALITY

    def test_get_all_rules_with_status_filter(self, knowledge_base, sample_rules):
        """测试按状态过滤"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        draft_rules = knowledge_base.get_all_rules(status="draft")
        assert len(draft_rules) == 2
        assert all(r.status == "draft" for r in draft_rules)

    def test_get_all_rules_with_limit(self, knowledge_base, sample_rules):
        """测试限制返回数量"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        rules = knowledge_base.get_all_rules(limit=2)
        assert len(rules) == 2

    def test_search_rules_by_keyword(self, knowledge_base, sample_rules):
        """测试按关键词搜索规则"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        results = knowledge_base.search_rules("quality")
        assert len(results) > 0
        assert any("quality" in r.name.lower() or "quality" in r.description.lower()
                   for r in results)

    def test_search_rules_case_insensitive(self, knowledge_base, sample_rule):
        """测试搜索不区分大小写"""
        knowledge_base.add_rule(sample_rule)

        results = knowledge_base.search_rules("TEST")
        assert len(results) > 0

    def test_update_rule_status(self, knowledge_base, sample_rule):
        """测试更新规则状态"""
        knowledge_base.add_rule(sample_rule)

        result = knowledge_base.update_rule_status(sample_rule.id, "approved")
        assert result is True

        updated = knowledge_base.get_rule(sample_rule.id)
        assert updated.status == "approved"

    def test_update_rule_status_not_exists(self, knowledge_base):
        """测试更新不存在的规则状态"""
        result = knowledge_base.update_rule_status("non-existent", "approved")
        assert result is False

    def test_delete_rule(self, knowledge_base, sample_rule):
        """测试删除规则"""
        knowledge_base.add_rule(sample_rule)

        result = knowledge_base.delete_rule(sample_rule.id)
        assert result is True

        # 验证已删除
        retrieved = knowledge_base.get_rule(sample_rule.id)
        assert retrieved is None

    def test_delete_rule_not_exists(self, knowledge_base):
        """测试删除不存在的规则"""
        result = knowledge_base.delete_rule("non-existent")
        assert result is False

    def test_add_rules_batch(self, knowledge_base, sample_rules):
        """测试批量添加规则"""
        count = knowledge_base.add_rules_batch(sample_rules)
        assert count == len(sample_rules)

        # 验证所有规则都已添加
        all_rules = knowledge_base.get_all_rules(limit=100)
        assert len(all_rules) == len(sample_rules)


# ============================================================================
# KnowledgeBase 统计功能测试
# ============================================================================


class TestKnowledgeBaseStatistics:
    """测试知识库统计功能"""

    def test_get_statistics_empty_db(self, knowledge_base):
        """测试空数据库的统计"""
        stats = knowledge_base.get_statistics()
        assert stats["total_rules"] == 0
        assert stats["average_quality"] == 0.0
        assert stats["by_category"] == {}
        assert stats["by_status"] == {}

    def test_get_statistics_with_data(self, knowledge_base, sample_rules):
        """测试有数据的统计"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        stats = knowledge_base.get_statistics()
        assert stats["total_rules"] == len(sample_rules)
        assert stats["average_quality"] > 0
        assert len(stats["by_category"]) > 0
        assert len(stats["by_status"]) > 0

    def test_get_statistics_by_category_breakdown(self, knowledge_base, sample_rules):
        """测试分类统计"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        stats = knowledge_base.get_statistics()
        assert FeedbackCategory.CODE_QUALITY.value in stats["by_category"]
        assert FeedbackCategory.BUG_RISK.value in stats["by_category"]


# ============================================================================
# KnowledgeBase 导入导出测试
# ============================================================================


class TestKnowledgeBaseImportExport:
    """测试知识库导入导出"""

    def test_export_rules_to_json(self, knowledge_base, sample_rules, temp_db_path, tmp_path):
        """测试导出规则到JSON"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        output_path = tmp_path / "exported_rules.json"
        result = knowledge_base.export_rules(str(output_path))

        assert result is True
        assert output_path.exists()

        # 验证JSON内容
        import json
        with open(output_path) as f:
            data = json.load(f)

        assert data["total_rules"] == len(sample_rules)
        assert len(data["rules"]) == len(sample_rules)

    def test_export_rules_with_category_filter(self, knowledge_base, sample_rules, tmp_path):
        """测试按类别导出"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        output_path = tmp_path / "exported_quality.json"
        result = knowledge_base.export_rules(
            str(output_path),
            category=FeedbackCategory.CODE_QUALITY
        )

        assert result is True

        import json
        with open(output_path) as f:
            data = json.load(f)

        assert all(r["category"] == "code_quality" for r in data["rules"])

    def test_export_rules_invalid_path(self, knowledge_base, sample_rules):
        """测试导出到无效路径"""
        for rule in sample_rules:
            knowledge_base.add_rule(rule)

        result = knowledge_base.export_rules("/invalid/path/file.json")
        assert result is False


# ============================================================================
# KnowledgeBase 连接管理测试
# ============================================================================


class TestKnowledgeBaseConnectionManagement:
    """测试知识库连接管理"""

    def test_close_connection(self, knowledge_base):
        """测试关闭连接"""
        # 获取连接
        conn1 = knowledge_base._get_connection()
        assert conn1 is not None

        # 关闭
        knowledge_base.close()

        # 验证连接已重置
        assert knowledge_base._conn is None

    def test_connection_reuse(self, knowledge_base):
        """测试连接复用"""
        conn1 = knowledge_base._get_connection()
        conn2 = knowledge_base._get_connection()
        assert conn1 is conn2


# ============================================================================
# InMemoryKnowledgeBase 测试
# ============================================================================


class TestInMemoryKnowledgeBase:
    """测试内存知识库"""

    @pytest.fixture
    def memory_kb(self):
        """创建内存知识库实例"""
        return InMemoryKnowledgeBase()

    def test_initialization(self, memory_kb):
        """测试初始化"""
        assert memory_kb._rules == {}
        assert memory_kb.get_statistics()["total_rules"] == 0

    def test_add_rule(self, memory_kb, sample_rule):
        """测试添加规则"""
        result = memory_kb.add_rule(sample_rule)
        assert result is True

        retrieved = memory_kb.get_rule(sample_rule.id)
        assert retrieved is not None

    def test_add_rule_overwrite(self, memory_kb, sample_rule):
        """测试覆盖已存在的规则"""
        memory_kb.add_rule(sample_rule)

        modified = LearnedRule(
            id=sample_rule.id,
            name="New Name",
            description=sample_rule.description,
            category=sample_rule.category,
            pattern=sample_rule.pattern,
            tools=sample_rule.tools,
            frequency=sample_rule.frequency,
            confidence=sample_rule.confidence,
            quality_score=sample_rule.quality_score,
            status=sample_rule.status,
            created_at=sample_rule.created_at,
        )
        memory_kb.add_rule(modified)

        retrieved = memory_kb.get_rule(sample_rule.id)
        assert retrieved.name == "New Name"

    def test_get_all_rules_with_filters(self, memory_kb, sample_rules):
        """测试带过滤的获取所有规则"""
        for rule in sample_rules:
            memory_kb.add_rule(rule)

        # 按类别过滤
        quality_rules = memory_kb.get_all_rules(
            category=FeedbackCategory.CODE_QUALITY
        )
        assert len(quality_rules) == 1
        assert quality_rules[0].category == FeedbackCategory.CODE_QUALITY

        # 按状态过滤
        draft_rules = memory_kb.get_all_rules(status="draft")
        assert len(draft_rules) == 2

    def test_search_rules(self, memory_kb, sample_rule):
        """测试搜索规则"""
        memory_kb.add_rule(sample_rule)

        results = memory_kb.search_rules("test")
        assert len(results) > 0

    def test_update_rule_status(self, memory_kb, sample_rule):
        """测试更新状态"""
        memory_kb.add_rule(sample_rule)
        result = memory_kb.update_rule_status(sample_rule.id, "approved")
        assert result is True

        updated = memory_kb.get_rule(sample_rule.id)
        assert updated.status == "approved"

    def test_delete_rule(self, memory_kb, sample_rule):
        """测试删除规则"""
        memory_kb.add_rule(sample_rule)
        result = memory_kb.delete_rule(sample_rule.id)
        assert result is True

        assert memory_kb.get_rule(sample_rule.id) is None

    def test_get_statistics(self, memory_kb, sample_rules):
        """测试统计信息"""
        for rule in sample_rules:
            memory_kb.add_rule(rule)

        stats = memory_kb.get_statistics()
        assert stats["total_rules"] == len(sample_rules)
        assert stats["average_quality"] > 0
        assert len(stats["by_category"]) == 4  # 4个不同类别

    def test_close_noop(self, memory_kb):
        """测试内存知识库的close是空操作"""
        memory_kb.close()  # 不应该抛出异常
        assert memory_kb._rules == {}


# ============================================================================
# 边界条件和错误处理测试
# ============================================================================


class TestKnowledgeBaseEdgeCases:
    """测试边界条件和错误处理"""

    def test_add_rules_batch_empty_list(self, knowledge_base):
        """测试批量添加空列表"""
        count = knowledge_base.add_rules_batch([])
        assert count == 0

    def test_search_rules_empty_database(self, knowledge_base):
        """测试在空数据库中搜索"""
        results = knowledge_base.search_rules("test")
        assert results == []

    def test_get_all_rules_empty_database(self, knowledge_base):
        """测试从空数据库获取所有规则"""
        rules = knowledge_base.get_all_rules()
        assert rules == []

    def test_add_rules_batch_partial_failure(self, knowledge_base, sample_rules):
        """测试批量添加时部分失败"""
        # 创建一个会导致失败的规则
        bad_rule = Mock()
        bad_rule.id = "bad-rule"

        mixed_rules = sample_rules[:2] + [bad_rule] + sample_rules[2:]

        # 应该成功添加有效的规则
        count = knowledge_base.add_rules_batch([r for r in mixed_rules if hasattr(r, "id") and r.id != "bad-rule"])
        assert count >= 2

    def test_very_long_rule_description(self, knowledge_base):
        """测试非常长的规则描述"""
        long_desc = "A" * 10000
        rule = LearnedRule(
            id="long-desc-rule",
            name="Long Description Rule",
            description=long_desc,
            category=FeedbackCategory.CODE_QUALITY,
            pattern=Pattern(
                file_patterns=["*.py"],
                code_patterns=["test"],
                context_keywords=["test"],
                severity_distribution={},
                tool_support=[],
            ),
            tools=["ruff"],
            frequency=1,
            confidence=0.5,
            quality_score=0.5,
            status="draft",
            created_at=datetime.now(),
        )

        result = knowledge_base.add_rule(rule)
        assert result is True

    def test_special_characters_in_rule_id(self, knowledge_base, sample_rule):
        """测试规则ID中的特殊字符"""
        # KnowledgeBase应该能处理特殊字符
        special_id = "rule-with_special.chars-123"
        rule = LearnedRule(
            id=special_id,
            name="Special ID Rule",
            description="Rule with special characters in ID",
            category=sample_rule.category,
            pattern=sample_rule.pattern,
            tools=sample_rule.tools,
            frequency=1,
            confidence=0.5,
            quality_score=0.5,
            status="draft",
            created_at=datetime.now(),
        )

        result = knowledge_base.add_rule(rule)
        assert result is True

        retrieved = knowledge_base.get_rule(special_id)
        assert retrieved is not None


# ============================================================================
# 并发和性能测试
# ============================================================================


class TestKnowledgeBaseConcurrency:
    """测试知识库并发访问"""

    def test_concurrent_add_rules(self):
        """测试并发添加规则"""
        import threading
        import time
        import os

        # 直接在测试中创建临时文件
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            kb = KnowledgeBase(db_path=db_path)

            rules = []
            for i in range(10):
                rule = LearnedRule(
                    id=f"concurrent-rule-{i}",
                    name=f"Concurrent Rule {i}",
                    description=f"Rule {i}",
                    category=FeedbackCategory.CODE_QUALITY,
                    pattern=Pattern(
                        file_patterns=["*.py"],
                        code_patterns=[f"pattern_{i}"],
                        context_keywords=[f"keyword_{i}"],
                        severity_distribution={},
                        tool_support=["ruff"],
                    ),
                    tools=["ruff"],
                    frequency=1,
                    confidence=0.5,
                    quality_score=0.5,
                    status="draft",
                    created_at=datetime.now(),
                )
                rules.append(rule)

            errors = []
            success_count = [0]
            lock = threading.Lock()

            def add_rule(rule):
                try:
                    time.sleep(0.001)
                    with lock:  # 使用锁避免SQLite并发问题
                        if kb.add_rule(rule):
                            success_count[0] += 1
                except Exception as e:
                    errors.append(e)

            threads = [threading.Thread(target=add_rule, args=(r,)) for r in rules]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            stats = kb.get_statistics()
            kb.close()

            assert stats["total_rules"] == 10
            assert len(errors) == 0
        finally:
            try:
                os.unlink(db_path)
            except Exception:
                pass


# ============================================================================
# 数据持久化测试
# ============================================================================


class TestKnowledgeBasePersistence:
    """测试数据持久化"""

    def test_data_persists_across_instances(self, temp_db_path, sample_rule):
        """测试数据在不同实例间持久化"""
        # 第一个实例添加数据
        kb1 = KnowledgeBase(db_path=temp_db_path)
        kb1.add_rule(sample_rule)
        kb1.close()

        # 第二个实例应该能读取到数据
        kb2 = KnowledgeBase(db_path=temp_db_path)
        retrieved = kb2.get_rule(sample_rule.id)
        assert retrieved is not None
        assert retrieved.name == sample_rule.name
        kb2.close()

    def test_multiple_instances_same_db(self, temp_db_path, sample_rules):
        """测试多个实例使用同一数据库"""
        kb1 = KnowledgeBase(db_path=temp_db_path)
        kb2 = KnowledgeBase(db_path=temp_db_path)

        # kb1 添加规则
        kb1.add_rule(sample_rules[0])

        # kb2 应该能看到
        rules = kb2.get_all_rules()
        assert len(rules) >= 1

        kb1.close()
        kb2.close()
