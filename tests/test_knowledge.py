import json
from datetime import datetime

import pytest

from lingflow.self_optimizer.phase5.knowledge import InMemoryKnowledgeBase, KnowledgeBase
from lingflow.self_optimizer.phase5.models import (
    FeedbackCategory,
    LearnedRule,
    Pattern,
)


def _make_rule(
    rule_id="r1",
    name="Test Rule",
    description=None,
    category=FeedbackCategory.SECURITY,
    quality_score=0.9,
    status="active",
    frequency=5,
    confidence=0.85,
):
    return LearnedRule(
        id=rule_id,
        name=name,
        description=description or f"Description for {name}",
        category=category,
        pattern=Pattern(
            file_patterns=["*.py"],
            code_patterns=["eval("],
            context_keywords=["security"],
            severity_distribution={"high": 3, "medium": 2},
            tool_support=["semgrep"],
        ),
        tools=["semgrep"],
        frequency=frequency,
        confidence=confidence,
        quality_score=quality_score,
        status=status,
        created_at=datetime.now(),
    )


class TestKnowledgeBase:
    @pytest.fixture
    def kb(self, tmp_path):
        db = KnowledgeBase(db_path=str(tmp_path / "test.db"))
        yield db
        db.close()

    def test_add_and_get_rule(self, kb):
        rule = _make_rule()
        assert kb.add_rule(rule) is True
        retrieved = kb.get_rule("r1")
        assert retrieved is not None
        assert retrieved.name == "Test Rule"
        assert retrieved.category == FeedbackCategory.SECURITY

    def test_get_rule_not_found(self, kb):
        assert kb.get_rule("nonexistent") is None

    def test_add_rules_batch(self, kb):
        rules = [_make_rule(f"r{i}", name=f"Rule {i}") for i in range(5)]
        count = kb.add_rules_batch(rules)
        assert count == 5

    def test_get_all_rules(self, kb):
        kb.add_rule(_make_rule("r1", category=FeedbackCategory.SECURITY, quality_score=0.9))
        kb.add_rule(_make_rule("r2", category=FeedbackCategory.PERFORMANCE, quality_score=0.7))
        all_rules = kb.get_all_rules()
        assert len(all_rules) == 2

    def test_get_all_rules_filter_category(self, kb):
        kb.add_rule(_make_rule("r1", category=FeedbackCategory.SECURITY))
        kb.add_rule(_make_rule("r2", category=FeedbackCategory.PERFORMANCE))
        rules = kb.get_all_rules(category=FeedbackCategory.SECURITY)
        assert len(rules) == 1
        assert rules[0].category == FeedbackCategory.SECURITY

    def test_get_all_rules_filter_status(self, kb):
        kb.add_rule(_make_rule("r1", status="active"))
        kb.add_rule(_make_rule("r2", status="draft"))
        rules = kb.get_all_rules(status="active")
        assert len(rules) == 1

    def test_get_all_rules_limit(self, kb):
        for i in range(10):
            kb.add_rule(_make_rule(f"r{i}", quality_score=i / 10.0))
        rules = kb.get_all_rules(limit=3)
        assert len(rules) == 3

    def test_search_rules_by_name(self, kb):
        kb.add_rule(_make_rule("r1", name="SQL Injection Detection"))
        kb.add_rule(_make_rule("r2", name="XSS Prevention"))
        results = kb.search_rules("SQL")
        assert len(results) == 1
        assert "SQL" in results[0].name

    def test_search_rules_by_description(self, kb):
        kb.add_rule(_make_rule("r1", name="Rule A", description="prevents buffer overflow"))
        results = kb.search_rules("buffer")
        assert len(results) == 1

    def test_search_rules_no_match(self, kb):
        kb.add_rule(_make_rule("r1", name="Rule A"))
        results = kb.search_rules("nonexistent_keyword")
        assert len(results) == 0

    def test_update_rule_status(self, kb):
        kb.add_rule(_make_rule("r1", status="draft"))
        assert kb.update_rule_status("r1", "active") is True
        rule = kb.get_rule("r1")
        assert rule.status == "active"

    def test_update_rule_status_not_found(self, kb):
        assert kb.update_rule_status("nonexistent", "active") is False

    def test_delete_rule(self, kb):
        kb.add_rule(_make_rule("r1"))
        assert kb.delete_rule("r1") is True
        assert kb.get_rule("r1") is None

    def test_delete_rule_not_found(self, kb):
        assert kb.delete_rule("nonexistent") is False

    def test_get_statistics(self, kb):
        kb.add_rule(_make_rule("r1", category=FeedbackCategory.SECURITY, quality_score=0.9, status="active"))
        kb.add_rule(_make_rule("r2", category=FeedbackCategory.PERFORMANCE, quality_score=0.7, status="draft"))
        stats = kb.get_statistics()
        assert stats["total_rules"] == 2
        assert "security" in stats["by_category"]
        assert "performance" in stats["by_category"]
        assert stats["average_quality"] == pytest.approx(0.8, abs=0.01)

    def test_get_statistics_empty(self, kb):
        stats = kb.get_statistics()
        assert stats["total_rules"] == 0
        assert stats["average_quality"] == 0.0

    def test_export_rules(self, kb, tmp_path):
        kb.add_rule(_make_rule("r1"))
        out_path = str(tmp_path / "export.json")
        assert kb.export_rules(out_path) is True
        with open(out_path) as f:
            data = json.load(f)
        assert data["total_rules"] == 1
        assert data["rules"][0]["id"] == "r1"

    def test_export_rules_with_category_filter(self, kb, tmp_path):
        kb.add_rule(_make_rule("r1", category=FeedbackCategory.SECURITY))
        kb.add_rule(_make_rule("r2", category=FeedbackCategory.PERFORMANCE))
        out_path = str(tmp_path / "export.json")
        assert kb.export_rules(out_path, category=FeedbackCategory.SECURITY) is True
        with open(out_path) as f:
            data = json.load(f)
        assert data["total_rules"] == 1

    def test_import_rules(self, kb, tmp_path):
        import_file = tmp_path / "import.json"
        import_file.write_text(json.dumps({"rules": [{"id": "x1"}, {"id": "x2"}]}))
        count = kb.import_rules(str(import_file))
        assert count == 2

    def test_import_rules_bad_file(self, kb):
        count = kb.import_rules("/nonexistent/path.json")
        assert count == 0


class TestInMemoryKnowledgeBase:
    def test_add_and_get_rule(self):
        kb = InMemoryKnowledgeBase()
        rule = _make_rule()
        assert kb.add_rule(rule) is True
        retrieved = kb.get_rule("r1")
        assert retrieved is not None
        assert retrieved.name == "Test Rule"

    def test_get_rule_not_found(self):
        kb = InMemoryKnowledgeBase()
        assert kb.get_rule("nonexistent") is None

    def test_add_rules_batch(self):
        kb = InMemoryKnowledgeBase()
        rules = [_make_rule(f"r{i}") for i in range(3)]
        count = kb.add_rules_batch(rules)
        assert count == 3

    def test_get_all_rules_sorted_by_quality(self):
        kb = InMemoryKnowledgeBase()
        kb.add_rule(_make_rule("r1", quality_score=0.5))
        kb.add_rule(_make_rule("r2", quality_score=0.9))
        kb.add_rule(_make_rule("r3", quality_score=0.7))
        rules = kb.get_all_rules()
        assert rules[0].quality_score == 0.9
        assert rules[1].quality_score == 0.7
        assert rules[2].quality_score == 0.5

    def test_get_all_rules_filter_category(self):
        kb = InMemoryKnowledgeBase()
        kb.add_rule(_make_rule("r1", category=FeedbackCategory.SECURITY))
        kb.add_rule(_make_rule("r2", category=FeedbackCategory.PERFORMANCE))
        rules = kb.get_all_rules(category=FeedbackCategory.SECURITY)
        assert len(rules) == 1

    def test_get_all_rules_filter_status(self):
        kb = InMemoryKnowledgeBase()
        kb.add_rule(_make_rule("r1", status="active"))
        kb.add_rule(_make_rule("r2", status="draft"))
        rules = kb.get_all_rules(status="draft")
        assert len(rules) == 1
        assert rules[0].status == "draft"

    def test_get_all_rules_limit(self):
        kb = InMemoryKnowledgeBase()
        for i in range(5):
            kb.add_rule(_make_rule(f"r{i}", quality_score=i / 5.0))
        rules = kb.get_all_rules(limit=2)
        assert len(rules) == 2

    def test_search_rules(self):
        kb = InMemoryKnowledgeBase()
        kb.add_rule(_make_rule("r1", name="SQL Injection"))
        kb.add_rule(_make_rule("r2", name="XSS Filter"))
        results = kb.search_rules("sql")
        assert len(results) == 1

    def test_search_rules_by_description(self):
        kb = InMemoryKnowledgeBase()
        kb.add_rule(_make_rule("r1", description="prevents memory leaks"))
        results = kb.search_rules("memory")
        assert len(results) == 1

    def test_update_rule_status(self):
        kb = InMemoryKnowledgeBase()
        kb.add_rule(_make_rule("r1", status="draft"))
        assert kb.update_rule_status("r1", "active") is True
        assert kb.get_rule("r1").status == "active"

    def test_update_rule_status_not_found(self):
        kb = InMemoryKnowledgeBase()
        assert kb.update_rule_status("nonexistent", "active") is False

    def test_delete_rule(self):
        kb = InMemoryKnowledgeBase()
        kb.add_rule(_make_rule("r1"))
        assert kb.delete_rule("r1") is True
        assert kb.get_rule("r1") is None

    def test_delete_rule_not_found(self):
        kb = InMemoryKnowledgeBase()
        assert kb.delete_rule("nonexistent") is False

    def test_get_statistics(self):
        kb = InMemoryKnowledgeBase()
        kb.add_rule(_make_rule("r1", category=FeedbackCategory.SECURITY, quality_score=0.9, status="active"))
        kb.add_rule(_make_rule("r2", category=FeedbackCategory.SECURITY, quality_score=0.7, status="draft"))
        stats = kb.get_statistics()
        assert stats["total_rules"] == 2
        assert stats["by_category"]["security"] == 2
        assert stats["by_status"]["active"] == 1
        assert stats["by_status"]["draft"] == 1
        assert stats["average_quality"] == pytest.approx(0.8, abs=0.01)

    def test_get_statistics_empty(self):
        kb = InMemoryKnowledgeBase()
        stats = kb.get_statistics()
        assert stats["total_rules"] == 0
        assert stats["average_quality"] == 0.0

    def test_close_does_nothing(self):
        kb = InMemoryKnowledgeBase()
        kb.close()
