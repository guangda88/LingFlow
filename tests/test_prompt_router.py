"""Tests for lingflow.core.prompt_router"""

import json
import tempfile
from pathlib import Path

import pytest

from lingflow.core.prompt_router import (
    RouteStrategy,
    RouteRule,
    RouteTarget,
    RouteResult,
    PromptRouter,
    create_default_router,
    create_code_focused_router,
)


class TestRouteStrategy:
    def test_values(self):
        assert RouteStrategy.KEYWORD_MATCH.value == "keyword_match"
        assert RouteStrategy.PATTERN_MATCH.value == "pattern_match"
        assert RouteStrategy.SEMANTIC_SIMILARITY.value == "semantic_similarity"
        assert RouteStrategy.CUSTOM.value == "custom"


class TestRouteRule:
    def test_defaults(self):
        rule = RouteRule(name="test")
        assert rule.keywords == []
        assert rule.patterns == []
        assert rule.priority == 0
        assert rule.strategy == RouteStrategy.KEYWORD_MATCH
        assert rule.metadata == {}

    def test_keyword_match_hit(self):
        rule = RouteRule(name="py", keywords=["python", "code"])
        matches, score = rule.matches("I love python code")
        assert matches is True
        assert score == 1.0

    def test_keyword_match_partial(self):
        rule = RouteRule(name="py", keywords=["python", "code", "debug"])
        matches, score = rule.matches("python is great")
        assert matches is True
        assert score == pytest.approx(1 / 3)

    def test_keyword_match_miss(self):
        rule = RouteRule(name="py", keywords=["python"])
        matches, score = rule.matches("I love java")
        assert matches is False
        assert score == 0.0

    def test_keyword_match_empty_keywords(self):
        rule = RouteRule(name="empty", keywords=[])
        matches, score = rule.matches("anything")
        assert matches is False
        assert score == 0.0

    def test_keyword_match_case_insensitive(self):
        rule = RouteRule(name="py", keywords=["Python"])
        matches, score = rule.matches("I love python")
        assert matches is True

    def test_pattern_match_hit(self):
        rule = RouteRule(name="ip", patterns=[r"\d+\.\d+\.\d+\.\d+"], strategy=RouteStrategy.PATTERN_MATCH)
        matches, score = rule.matches("connect to 192.168.1.1")
        assert matches is True
        assert score == 1.0

    def test_pattern_match_miss(self):
        rule = RouteRule(name="ip", patterns=[r"\d+\.\d+\.\d+\.\d+"], strategy=RouteStrategy.PATTERN_MATCH)
        matches, score = rule.matches("hello world")
        assert matches is False
        assert score == 0.0

    def test_pattern_match_empty_patterns(self):
        rule = RouteRule(name="empty", patterns=[], strategy=RouteStrategy.PATTERN_MATCH)
        matches, score = rule.matches("anything")
        assert matches is False

    def test_pattern_match_invalid_regex(self):
        rule = RouteRule(name="bad", patterns=[r"[invalid", r"\d+"], strategy=RouteStrategy.PATTERN_MATCH)
        matches, score = rule.matches("test 123")
        assert matches is True
        assert score == 0.5

    def test_pattern_match_partial(self):
        rule = RouteRule(name="multi", patterns=[r"\d+", r"[a-z]+"], strategy=RouteStrategy.PATTERN_MATCH)
        matches, score = rule.matches("ABC DEF")
        assert matches is True
        assert score == 0.5

    def test_custom_strategy_no_match(self):
        rule = RouteRule(name="custom", strategy=RouteStrategy.CUSTOM)
        matches, score = rule.matches("anything")
        assert matches is False
        assert score == 0.0

    def test_semantic_strategy_no_match(self):
        rule = RouteRule(name="semantic", strategy=RouteStrategy.SEMANTIC_SIMILARITY)
        matches, score = rule.matches("anything")
        assert matches is False


class TestRouteTarget:
    def test_defaults(self):
        target = RouteTarget(name="t1", agent_type="CodeAgent", description="code")
        assert target.capabilities == []
        assert target.metadata == {}

    def test_with_capabilities(self):
        target = RouteTarget(
            name="t1", agent_type="CodeAgent", description="code",
            capabilities=["review", "refactor"]
        )
        assert len(target.capabilities) == 2


class TestRouteResult:
    def test_best_match_empty(self):
        result = RouteResult(prompt="test", matched_rules=[], selected_target=None, confidence=0.0)
        assert result.best_match is None

    def test_best_match_single(self):
        result = RouteResult(
            prompt="test",
            matched_rules=[("rule1", 0.8)],
            selected_target=None,
            confidence=0.8
        )
        assert result.best_match == ("rule1", 0.8)

    def test_best_match_multiple(self):
        result = RouteResult(
            prompt="test",
            matched_rules=[("rule1", 0.5), ("rule2", 0.9), ("rule3", 0.7)],
            selected_target=None,
            confidence=0.9
        )
        assert result.best_match == ("rule2", 0.9)

    def test_timestamp_auto_set(self):
        result = RouteResult(prompt="test", matched_rules=[], selected_target=None, confidence=0.0)
        assert result.timestamp is not None


class TestPromptRouter:
    def test_init(self):
        router = PromptRouter()
        assert len(router._rules) == 0
        assert len(router._targets) == 0
        assert len(router._history) == 0
        assert router._default_target is None

    def test_add_rule_returns_self(self):
        router = PromptRouter()
        result = router.add_rule(RouteRule(name="r1", keywords=["test"]))
        assert result is router

    def test_add_target_returns_self(self):
        router = PromptRouter()
        result = router.add_target(RouteTarget(name="t1", agent_type="A", description="d"))
        assert result is router

    def test_set_default_target_returns_self(self):
        router = PromptRouter()
        result = router.set_default_target(RouteTarget(name="t1", agent_type="A", description="d"))
        assert result is router

    def test_route_no_match_returns_default(self):
        router = PromptRouter()
        default = RouteTarget(name="default", agent_type="Fallback", description="fallback")
        router.set_default_target(default)
        result = router.route("hello world")
        assert result.selected_target is default
        assert result.confidence == 0.0

    def test_route_no_match_no_default(self):
        router = PromptRouter()
        result = router.route("hello world")
        assert result.selected_target is None
        assert result.confidence == 0.0
        assert result.matched_rules == []

    def test_route_keyword_match(self):
        router = PromptRouter()
        target = RouteTarget(name="code", agent_type="CodeAgent", description="code")
        router.add_target(target)
        router.add_rule(RouteRule(
            name="code_rule",
            keywords=["code", "python"],
            priority=1,
            metadata={"target_name": "code"}
        ))
        result = router.route("write python code")
        assert result.selected_target is target
        assert result.confidence > 0
        assert len(result.matched_rules) == 1

    def test_route_priority_weighting(self):
        router = PromptRouter()
        t1 = RouteTarget(name="t1", agent_type="A", description="a")
        t2 = RouteTarget(name="t2", agent_type="B", description="b")
        router.add_target(t1)
        router.add_target(t2)
        router.add_rule(RouteRule(
            name="low", keywords=["test"],
            priority=1,
            metadata={"target_name": "t1"}
        ))
        router.add_rule(RouteRule(
            name="high", keywords=["test"],
            priority=5,
            metadata={"target_name": "t2"}
        ))
        result = router.route("test")
        assert result.selected_target is t2

    def test_route_top_k(self):
        router = PromptRouter()
        for i in range(5):
            router.add_rule(RouteRule(
                name=f"rule_{i}",
                keywords=["common"],
                priority=i,
                metadata={"target_name": "t"}
            ))
        router.add_target(RouteTarget(name="t", agent_type="A", description="d"))
        result = router.route("common", top_k=2)
        assert len(result.matched_rules) == 2

    def test_route_saves_history(self):
        router = PromptRouter()
        router.route("first")
        router.route("second")
        assert len(router._history) == 2

    def test_clear_history(self):
        router = PromptRouter()
        router.route("first")
        router.route("second")
        router.clear_history()
        assert len(router._history) == 0

    def test_get_statistics_empty(self):
        router = PromptRouter()
        stats = router.get_statistics()
        assert stats["total_routes"] == 0
        assert stats["avg_confidence"] == 0.0
        assert stats["most_used_targets"] == []
        assert stats["most_matched_rules"] == []

    def test_get_statistics_with_history(self):
        router = PromptRouter()
        target = RouteTarget(name="code", agent_type="A", description="d")
        router.add_target(target)
        router.set_default_target(target)
        router.add_rule(RouteRule(
            name="code_rule",
            keywords=["code"],
            metadata={"target_name": "code"}
        ))
        router.route("code analysis")
        router.route("code review")
        stats = router.get_statistics()
        assert stats["total_routes"] == 2
        assert stats["avg_confidence"] > 0
        assert len(stats["most_used_targets"]) > 0
        assert len(stats["most_matched_rules"]) > 0

    def test_save_and_load_config(self):
        router = PromptRouter()
        target = RouteTarget(name="t1", agent_type="A", description="desc", capabilities=["cap1"])
        router.add_target(target)
        router.set_default_target(target)
        router.add_rule(RouteRule(
            name="r1",
            keywords=["python"],
            patterns=[r"\d+"],
            priority=2,
            strategy=RouteStrategy.KEYWORD_MATCH,
            metadata={"target_name": "t1"}
        ))

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "config.json"
            saved_path = router.save_config(path)
            assert saved_path == path
            assert path.exists()

            loaded = PromptRouter.load_config(path)
            assert "r1" in loaded._rules
            assert loaded._rules["r1"].keywords == ["python"]
            assert loaded._rules["r1"].priority == 2
            assert "t1" in loaded._targets
            assert loaded._default_target is not None
            assert loaded._default_target.name == "t1"

    def test_save_config_default_path(self):
        router = PromptRouter()
        path = router.save_config()
        assert path.exists()
        path.unlink()

    def test_load_config_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            PromptRouter.load_config(Path("/nonexistent/config.json"))

    def test_load_config_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json{{{")
            f.flush()
            with pytest.raises(json.JSONDecodeError):
                PromptRouter.load_config(Path(f.name))
            Path(f.name).unlink()

    def test_select_target_no_match_with_default(self):
        router = PromptRouter()
        default = RouteTarget(name="def", agent_type="D", description="d")
        router.set_default_target(default)
        result = router._select_target([])
        assert result is default

    def test_select_target_no_match_no_default(self):
        router = PromptRouter()
        result = router._select_target([])
        assert result is None

    def test_select_target_rule_without_target_metadata(self):
        router = PromptRouter()
        router.add_rule(RouteRule(name="r1", keywords=["test"]))
        result = router._select_target([("r1", 0.5)])
        assert result is None

    def test_calculate_confidence_empty(self):
        router = PromptRouter()
        assert router._calculate_confidence([]) == 0.0

    def test_calculate_confidence_capped(self):
        router = PromptRouter()
        confidence = router._calculate_confidence([("r1", 5.0)])
        assert confidence == 1.0


class TestCreateDefaultRouter:
    def test_has_targets(self):
        router = create_default_router()
        assert "code_analyzer" in router._targets
        assert "writer" in router._targets
        assert "tester" in router._targets
        assert "explainer" in router._targets

    def test_has_rules(self):
        router = create_default_router()
        assert "code_analysis" in router._rules
        assert "testing" in router._rules
        assert "writing" in router._rules
        assert "explanation" in router._rules

    def test_has_default_target(self):
        router = create_default_router()
        assert router._default_target is not None
        assert router._default_target.name == "code_analyzer"

    def test_route_code_prompt(self):
        router = create_default_router()
        result = router.route("优化代码性能")
        assert result.selected_target is not None
        assert result.selected_target.name == "code_analyzer"

    def test_route_test_prompt(self):
        router = create_default_router()
        result = router.route("写测试用例")
        assert result.selected_target is not None

    def test_route_writing_prompt(self):
        router = create_default_router()
        result = router.route("生成文档")
        assert result.selected_target is not None

    def test_route_explanation_prompt(self):
        router = create_default_router()
        result = router.route("解释什么是API")
        assert result.selected_target is not None


class TestCreateCodeFocusedRouter:
    def test_has_targets(self):
        router = create_code_focused_router()
        assert "python_expert" in router._targets
        assert "web_dev" in router._targets
        assert "data_science" in router._targets

    def test_has_rules(self):
        router = create_code_focused_router()
        assert "python" in router._rules
        assert "web" in router._rules
        assert "data" in router._rules

    def test_route_python(self):
        router = create_code_focused_router()
        result = router.route("I need help with django")
        assert result.selected_target is not None
        assert result.selected_target.name == "python_expert"

    def test_route_web(self):
        router = create_code_focused_router()
        result = router.route("help with react components")
        assert result.selected_target is not None
        assert result.selected_target.name == "web_dev"

    def test_route_data(self):
        router = create_code_focused_router()
        result = router.route("机器学习模型训练")
        assert result.selected_target is not None
        assert result.selected_target.name == "data_science"

    def test_no_default_target(self):
        router = create_code_focused_router()
        result = router.route("unrelated prompt")
        assert result.selected_target is None
