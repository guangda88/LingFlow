"""Tests for lingflow.core.prompt_router module"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from lingflow.core.prompt_router import (
    PromptRouter,
    RouteRule,
    RouteTarget,
    RouteResult,
    RouteStrategy,
    create_default_router,
    create_code_focused_router,
)


class TestRouteStrategy:
    """Test RouteStrategy enum"""

    def test_strategy_values(self):
        """Test strategy enum values"""
        assert RouteStrategy.KEYWORD_MATCH.value == "keyword_match"
        assert RouteStrategy.PATTERN_MATCH.value == "pattern_match"
        assert RouteStrategy.SEMANTIC_SIMILARITY.value == "semantic_similarity"
        assert RouteStrategy.CUSTOM.value == "custom"


class TestRouteTarget:
    """Test RouteTarget dataclass"""

    def test_create_target(self):
        """Test creating a route target"""
        target = RouteTarget(
            name="test_agent",
            agent_type="TestAgent",
            description="A test agent",
            capabilities=["test", "demo"],
            metadata={"key": "value"},
        )
        assert target.name == "test_agent"
        assert target.agent_type == "TestAgent"
        assert target.description == "A test agent"
        assert target.capabilities == ["test", "demo"]
        assert target.metadata == {"key": "value"}

    def test_create_target_minimal(self):
        """Test creating target with minimal parameters"""
        target = RouteTarget(name="minimal", agent_type="MinimalAgent", description="Minimal")
        assert target.capabilities == []
        assert target.metadata == {}


class TestRouteRule:
    """Test RouteRule class"""

    def test_create_rule(self):
        """Test creating a route rule"""
        rule = RouteRule(
            name="test_rule",
            keywords=["test", "demo"],
            patterns=[r"test_\w+"],
            priority=5,
            strategy=RouteStrategy.KEYWORD_MATCH,
            metadata={"target": "test_agent"},
        )
        assert rule.name == "test_rule"
        assert rule.keywords == ["test", "demo"]
        assert rule.patterns == [r"test_\w+"]
        assert rule.priority == 5
        assert rule.strategy == RouteStrategy.KEYWORD_MATCH

    def test_keyword_match_score_positive(self):
        """Test keyword matching with positive score"""
        rule = RouteRule(name="test", keywords=["python", "code"], strategy=RouteStrategy.KEYWORD_MATCH)
        matches, score = rule.matches("I need help with python code")

        assert matches is True
        assert score == 1.0  # 2/2 keywords matched

    def test_keyword_match_score_partial(self):
        """Test keyword matching with partial score"""
        rule = RouteRule(name="test", keywords=["python", "django", "flask"], strategy=RouteStrategy.KEYWORD_MATCH)
        matches, score = rule.matches("I need help with python")

        assert matches is True
        assert score == pytest.approx(1/3, rel=0.01)

    def test_keyword_match_score_zero(self):
        """Test keyword matching with no matches"""
        rule = RouteRule(name="test", keywords=["python", "code"], strategy=RouteStrategy.KEYWORD_MATCH)
        matches, score = rule.matches("I need help with javascript")

        assert matches is False
        assert score == 0.0

    def test_keyword_match_case_insensitive(self):
        """Test keyword matching is case insensitive"""
        rule = RouteRule(name="test", keywords=["PYTHON"], strategy=RouteStrategy.KEYWORD_MATCH)
        matches, score = rule.matches("i need python help")

        assert matches is True
        assert score > 0

    def test_keyword_match_empty_keywords(self):
        """Test keyword matching with empty keywords"""
        rule = RouteRule(name="test", keywords=[], strategy=RouteStrategy.KEYWORD_MATCH)
        matches, score = rule.matches("Any text")

        assert matches is False
        assert score == 0.0

    def test_pattern_match_score_positive(self):
        """Test pattern matching with positive score"""
        rule = RouteRule(
            name="test", patterns=[r"error:\s*\d+", r"warning:\s*\d+"], strategy=RouteStrategy.PATTERN_MATCH
        )
        matches, score = rule.matches("error: 404 occurred")

        assert matches is True
        assert score > 0

    def test_pattern_match_no_match(self):
        """Test pattern matching with no matches"""
        rule = RouteRule(name="test", patterns=[r"error:\s*\d+"], strategy=RouteStrategy.PATTERN_MATCH)
        matches, score = rule.matches("no error here")

        assert matches is False
        assert score == 0.0

    def test_pattern_match_invalid_pattern(self):
        """Test pattern matching with invalid regex"""
        rule = RouteRule(name="test", patterns=["[invalid("], strategy=RouteStrategy.PATTERN_MATCH)
        # Should not crash, just return 0
        matches, score = rule.matches("test")
        assert matches is False
        assert score == 0.0

    def test_pattern_match_empty_patterns(self):
        """Test pattern matching with empty patterns"""
        rule = RouteRule(name="test", patterns=[], strategy=RouteStrategy.PATTERN_MATCH)
        matches, score = rule.matches("Any text")

        assert matches is False
        assert score == 0.0

    def test_unknown_strategy(self):
        """Test unknown strategy returns zero score"""
        rule = RouteRule(name="test", keywords=["test"], strategy=RouteStrategy.CUSTOM)
        matches, score = rule.matches("test keyword")

        assert matches is False
        assert score == 0.0


class TestRouteResult:
    """Test RouteResult dataclass"""

    def test_create_result(self):
        """Test creating a route result"""
        result = RouteResult(
            prompt="Test prompt",
            matched_rules=[("rule1", 0.8), ("rule2", 0.5)],
            selected_target=None,
            confidence=0.8,
        )
        assert result.prompt == "Test prompt"
        assert result.matched_rules == [("rule1", 0.8), ("rule2", 0.5)]
        assert result.selected_target is None
        assert result.confidence == 0.8

    def test_best_match_property(self):
        """Test best_match property"""
        result = RouteResult(
            prompt="Test",
            matched_rules=[("rule1", 0.5), ("rule2", 0.9), ("rule3", 0.7)],
            selected_target=None,
            confidence=0.9,
        )
        assert result.best_match == ("rule2", 0.9)

    def test_best_match_empty_rules(self):
        """Test best_match with empty rules"""
        result = RouteResult(prompt="Test", matched_rules=[], selected_target=None, confidence=0.0)
        assert result.best_match is None

    def test_timestamp_auto_generated(self):
        """Test timestamp is auto-generated"""
        before = datetime.now()
        result = RouteResult(prompt="Test", matched_rules=[], selected_target=None, confidence=0.0)
        after = datetime.now()

        assert before < datetime.fromisoformat(result.timestamp) < after


class TestPromptRouter:
    """Test PromptRouter class"""

    def test_init(self):
        """Test initialization"""
        router = PromptRouter()
        assert router._rules == {}
        assert router._targets == {}
        assert router._history == []
        assert router._default_target is None

    def test_add_rule(self):
        """Test adding a rule"""
        router = PromptRouter()
        rule = RouteRule(name="test", keywords=["test"])

        result = router.add_rule(rule)
        assert result is router  # Chainable
        assert "test" in router._rules
        assert router._rules["test"] == rule

    def test_add_target(self):
        """Test adding a target"""
        router = PromptRouter()
        target = RouteTarget(name="test", agent_type="TestAgent", description="Test")

        result = router.add_target(target)
        assert result is router  # Chainable
        assert "test" in router._targets
        assert router._targets["test"] == target

    def test_set_default_target(self):
        """Test setting default target"""
        router = PromptRouter()
        target = RouteTarget(name="default", agent_type="DefaultAgent", description="Default")

        result = router.set_default_target(target)
        assert result is router  # Chainable
        assert router._default_target == target

    def test_route_with_keyword_match(self):
        """Test routing with keyword match"""
        router = PromptRouter()
        router.add_target(RouteTarget(name="code", agent_type="CodeAgent", description="Code"))
        router.add_rule(
            RouteRule(name="code_rule", keywords=["code", "programming"], metadata={"target_name": "code"})
        )

        result = router.route("I need help with code")

        assert len(result.matched_rules) > 0
        assert result.matched_rules[0][0] == "code_rule"
        assert result.selected_target is not None
        assert result.selected_target.name == "code"
        assert result.confidence > 0

    def test_route_with_priority(self):
        """Test routing with priority weights"""
        router = PromptRouter()
        router.add_target(RouteTarget(name="target", agent_type="Agent", description="T"))
        router.add_rule(RouteRule(name="low", keywords=["test"], priority=0, metadata={"target_name": "target"}))
        router.add_rule(RouteRule(name="high", keywords=["test"], priority=5, metadata={"target_name": "target"}))

        result = router.route("test")

        # High priority rule should come first
        assert result.matched_rules[0][0] == "high"

    def test_route_no_matches(self):
        """Test routing with no matches"""
        router = PromptRouter()
        default_target = RouteTarget(name="default", agent_type="DefaultAgent", description="Default")
        router.set_default_target(default_target)

        result = router.route("unmatched content")

        assert len(result.matched_rules) == 0
        assert result.selected_target == default_target
        assert result.confidence == 0.0

    def test_route_top_k(self):
        """Test routing with top_k parameter"""
        router = PromptRouter()
        router.add_target(RouteTarget(name="target", agent_type="Agent", description="T"))
        router.add_rule(RouteRule(name="r1", keywords=["a"], metadata={"target_name": "target"}))
        router.add_rule(RouteRule(name="r2", keywords=["b"], metadata={"target_name": "target"}))
        router.add_rule(RouteRule(name="r3", keywords=["c"], metadata={"target_name": "target"}))

        result = router.route("a b c", top_k=2)

        assert len(result.matched_rules) == 2

    def test_route_history_tracking(self):
        """Test that route calls are tracked in history"""
        router = PromptRouter()
        router.add_target(RouteTarget(name="target", agent_type="Agent", description="T"))
        router.add_rule(RouteRule(name="test", keywords=["test"], metadata={"target_name": "target"}))

        router.route("test")
        router.route("another test")

        assert len(router._history) == 2
        assert router._history[0].prompt == "test"

    def test_get_statistics_empty(self):
        """Test statistics with no history"""
        router = PromptRouter()
        stats = router.get_statistics()

        assert stats["total_routes"] == 0
        assert stats["avg_confidence"] == 0.0
        assert stats["most_used_targets"] == []
        assert stats["most_matched_rules"] == []

    def test_get_statistics_with_history(self):
        """Test statistics with route history"""
        router = PromptRouter()
        target = RouteTarget(name="target", agent_type="Agent", description="T")
        router.add_target(target)
        router.add_rule(RouteRule(name="rule1", keywords=["a"], metadata={"target_name": "target"}))
        router.add_rule(RouteRule(name="rule2", keywords=["b"], metadata={"target_name": "target"}))

        router.route("a")
        router.route("b")
        router.route("a")

        stats = router.get_statistics()

        assert stats["total_routes"] == 3
        assert stats["avg_confidence"] > 0
        assert stats["most_used_targets"][0][0] == "target"
        assert len(stats["most_matched_rules"]) == 2

    def test_clear_history(self):
        """Test clearing route history"""
        router = PromptRouter()
        router.add_target(RouteTarget(name="target", agent_type="Agent", description="T"))
        router.add_rule(RouteRule(name="test", keywords=["test"], metadata={"target_name": "target"}))

        router.route("test")
        assert len(router._history) == 1

        router.clear_history()
        assert len(router._history) == 0

    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading router configuration"""
        router = PromptRouter()
        target = RouteTarget(name="test", agent_type="TestAgent", description="Test", capabilities=["test"])
        router.add_target(target)
        rule = RouteRule(
            name="test_rule",
            keywords=["test"],
            patterns=[r"test"],
            priority=1,
            strategy=RouteStrategy.KEYWORD_MATCH,
            metadata={"target_name": "test"},
        )
        router.add_rule(rule)

        config_path = tmp_path / "router_config.json"
        saved_path = router.save_config(path=config_path)

        assert saved_path.exists()

        loaded_router = PromptRouter.load_config(saved_path)
        assert "test" in loaded_router._targets
        assert loaded_router._targets["test"].agent_type == "TestAgent"
        assert "test_rule" in loaded_router._rules
        assert loaded_router._rules["test_rule"].keywords == ["test"]


class TestFactoryFunctions:
    """Test factory functions"""

    def test_create_default_router(self):
        """Test creating default router"""
        router = create_default_router()

        assert len(router._targets) == 4
        assert "code_analyzer" in router._targets
        assert "writer" in router._targets
        assert "tester" in router._targets
        assert "explainer" in router._targets

        assert len(router._rules) == 4
        assert "code_analysis" in router._rules
        assert "testing" in router._rules
        assert "writing" in router._rules
        assert "explanation" in router._rules

    def test_default_router_routes_correctly(self):
        """Test that default router routes correctly"""
        router = create_default_router()

        result = router.route("帮我分析这段代码")
        assert result.selected_target is not None
        assert result.selected_target.name == "code_analyzer"

        result = router.route("写一个文档")
        assert result.selected_target is not None
        assert result.selected_target.name == "writer"

    def test_create_code_focused_router(self):
        """Test creating code-focused router"""
        router = create_code_focused_router()

        assert len(router._targets) == 3
        assert "python_expert" in router._targets
        assert "web_dev" in router._targets
        assert "data_science" in router._targets

        assert len(router._rules) == 3
        assert "python" in router._rules
        assert "web" in router._rules
        assert "data" in router._rules

    def test_code_focused_router_routes_correctly(self):
        """Test that code-focused router routes correctly"""
        router = create_code_focused_router()

        result = router.route("I need help with Django")
        assert result.selected_target is not None
        assert result.selected_target.name == "python_expert"

        result = router.route("React component issue")
        assert result.selected_target is not None
        assert result.selected_target.name == "web_dev"
