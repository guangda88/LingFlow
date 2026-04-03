"""Tests for lingflow.core.query_engine"""

import json
import tempfile
from pathlib import Path

import pytest

from lingflow.core.query_engine import (
    StopReason,
    QueryEngineConfig,
    TurnResult,
    UsageSummary,
    MessageCompactor,
    QueryEngine,
    create_default_engine,
    create_budget_conscious_engine,
    create_long_conversation_engine,
)


class TestStopReason:
    def test_values(self):
        assert StopReason.COMPLETED.value == "completed"
        assert StopReason.MAX_TURNS_REACHED.value == "max_turns_reached"
        assert StopReason.MAX_BUDGET_REACHED.value == "max_budget_reached"
        assert StopReason.USER_CANCELLED.value == "user_cancelled"
        assert StopReason.ERROR.value == "error"


class TestQueryEngineConfig:
    def test_defaults(self):
        config = QueryEngineConfig()
        assert config.max_turns == 8
        assert config.max_budget_tokens == 200000
        assert config.compact_after_turns == 12
        assert config.compact_threshold_tokens == 100000
        assert config.structured_output is False
        assert config.structured_retry_limit == 2
        assert config.auto_compact is True

    def test_frozen(self):
        config = QueryEngineConfig()
        with pytest.raises(AttributeError):
            config.max_turns = 99

    def test_custom_values(self):
        config = QueryEngineConfig(max_turns=4, max_budget_tokens=50000)
        assert config.max_turns == 4
        assert config.max_budget_tokens == 50000


class TestTurnResult:
    def test_defaults(self):
        result = TurnResult(
            prompt="test", output="out", matched_tools=(),
            matched_agents=(), input_tokens=5, output_tokens=3,
            stop_reason=StopReason.COMPLETED
        )
        assert result.error is None
        assert result.timestamp is not None

    def test_with_error(self):
        result = TurnResult(
            prompt="test", output="", matched_tools=(),
            matched_agents=(), input_tokens=0, output_tokens=0,
            stop_reason=StopReason.ERROR, error="boom"
        )
        assert result.error == "boom"

    def test_frozen(self):
        result = TurnResult(
            prompt="test", output="out", matched_tools=(),
            matched_agents=(), input_tokens=5, output_tokens=3,
            stop_reason=StopReason.COMPLETED
        )
        with pytest.raises(AttributeError):
            result.prompt = "changed"


class TestUsageSummary:
    def test_defaults(self):
        usage = UsageSummary()
        assert usage.total_input_tokens == 0
        assert usage.total_output_tokens == 0
        assert usage.turn_count == 0
        assert usage.total_tokens == 0

    def test_total_tokens(self):
        usage = UsageSummary(total_input_tokens=100, total_output_tokens=50)
        assert usage.total_tokens == 150

    def test_to_dict(self):
        usage = UsageSummary(total_input_tokens=100, total_output_tokens=50, turn_count=3)
        d = usage.to_dict()
        assert d["total_input_tokens"] == 100
        assert d["total_output_tokens"] == 50
        assert d["total_tokens"] == 150
        assert d["turn_count"] == 3


class TestMessageCompactor:
    def test_compact_no_need(self):
        messages = ["msg1", "msg2", "msg3"]
        result, tokens = MessageCompactor.compact_messages(messages, 100, 50)
        assert result == messages
        assert tokens == 50

    def test_compact_needed(self):
        messages = [f"message {i}" for i in range(20)]
        result, tokens = MessageCompactor.compact_messages(messages, 100, 500)
        assert len(result) < len(messages)
        assert tokens < 500
        assert len(result) >= 1

    def test_compact_single_message(self):
        messages = ["only one"]
        result, tokens = MessageCompactor.compact_messages(messages, 10, 100)
        assert len(result) == 1

    def test_summarize_empty(self):
        assert MessageCompactor.summarize_messages([]) == ""

    def test_summarize_messages(self):
        msgs = ["hello world this is a test", "second message here"]
        summary = MessageCompactor.summarize_messages(msgs)
        assert "总消息数: 2" in summary
        assert "最早消息" in summary
        assert "最近消息" in summary

    def test_summarize_single_message(self):
        msgs = ["only message"]
        summary = MessageCompactor.summarize_messages(msgs)
        assert "总消息数: 1" in summary

    def test_summarize_long_message_truncated(self):
        msgs = ["x" * 200]
        summary = MessageCompactor.summarize_messages(msgs)
        assert "..." in summary


class TestQueryEngine:
    def test_init_default_session(self):
        engine = QueryEngine(QueryEngineConfig())
        assert engine.session_id is not None
        assert len(engine.session_id) > 0

    def test_init_custom_session(self):
        engine = QueryEngine(QueryEngineConfig(), session_id="my-session")
        assert engine.session_id == "my-session"

    def test_submit_basic(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("hello world")
        assert result.stop_reason == StopReason.COMPLETED
        assert result.output != ""
        assert result.input_tokens > 0
        assert result.output_tokens > 0

    def test_submit_with_process_func(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("test", process_func=lambda p: "custom response")
        assert result.output == "custom response"

    def test_submit_with_tools(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("use pytest to run tests", tools=["pytest", "flake8"])
        assert len(result.matched_tools) > 0
        assert "pytest" in result.matched_tools

    def test_submit_with_agents(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("ask the tester to run tests", agents=["tester", "reviewer"])
        assert len(result.matched_agents) > 0
        assert "tester" in result.matched_agents

    def test_submit_tools_no_match(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("hello world", tools=["pytest"])
        assert len(result.matched_tools) == 0

    def test_submit_agents_no_match(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("hello world", agents=["reviewer"])
        assert len(result.matched_agents) == 0

    def test_submit_empty_tools(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("hello world", tools=[])
        assert result.matched_tools == ()

    def test_submit_empty_agents(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("hello world", agents=[])
        assert result.matched_agents == ()

    def test_max_turns_reached(self):
        config = QueryEngineConfig(max_turns=2)
        engine = QueryEngine(config)
        engine.submit("first")
        engine.submit("second")
        result = engine.submit("third")
        assert result.stop_reason == StopReason.MAX_TURNS_REACHED
        assert result.error is not None
        assert "2" in result.error

    def test_max_budget_reached(self):
        config = QueryEngineConfig(max_budget_tokens=5)
        engine = QueryEngine(config)
        engine.submit("short")
        result = engine.submit("another prompt to exceed budget")
        assert result.stop_reason == StopReason.MAX_BUDGET_REACHED

    def test_usage_summary(self):
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("hello world")
        usage = engine.usage_summary
        assert usage.turn_count == 1
        assert usage.total_input_tokens > 0
        assert usage.total_output_tokens > 0

    def test_default_process_with_tools(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("test prompt", tools=["tool1", "tool2", "tool3"])
        assert "tool1" in result.output

    def test_default_process_with_agents(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("test prompt", agents=["agent1", "agent2"])
        assert "agent1" in result.output

    def test_default_process_no_tools_no_agents(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("test prompt")
        assert "正在处理" in result.output

    def test_auto_compact(self):
        config = QueryEngineConfig(
            max_turns=20,
            compact_after_turns=3,
            compact_threshold_tokens=10,
            auto_compact=True,
        )
        engine = QueryEngine(config)
        for i in range(5):
            engine.submit(f"prompt {i} " + "word " * 20)
        assert len(engine._messages) > 0

    def test_auto_compact_disabled(self):
        config = QueryEngineConfig(
            max_turns=20,
            compact_after_turns=2,
            auto_compact=False,
        )
        engine = QueryEngine(config)
        for i in range(5):
            engine.submit(f"prompt {i}")
        assert engine._turn_count == 5

    def test_get_compact_summary(self):
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("hello")
        summary = engine.get_compact_summary()
        assert isinstance(summary, str)

    def test_save_and_load_state(self):
        engine = QueryEngine(QueryEngineConfig(), session_id="test-session")
        engine.submit("hello world")
        engine.submit("second prompt")

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "state.json"
            saved_path = engine.save_state(path)
            assert saved_path == path
            assert path.exists()

            loaded = QueryEngine.load_state(path)
            assert loaded.session_id == "test-session"
            assert loaded._turn_count == 2
            assert len(loaded._messages) > 0
            assert loaded.usage_summary.total_input_tokens > 0

    def test_save_state_default_path(self):
        engine = QueryEngine(QueryEngineConfig(), session_id="test-session")
        path = engine.save_state()
        assert path.exists()
        assert "test-session" in str(path)
        path.unlink()

    def test_load_state_preserves_config(self):
        config = QueryEngineConfig(max_turns=5, max_budget_tokens=10000)
        engine = QueryEngine(config, session_id="cfg-test")
        engine.submit("test")

        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "state.json"
            engine.save_state(path)
            loaded = QueryEngine.load_state(path)
            assert loaded.config.max_turns == 5
            assert loaded.config.max_budget_tokens == 10000

    def test_reset(self):
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("hello")
        engine.submit("world")
        engine.reset()
        assert engine._turn_count == 0
        assert engine._input_tokens == 0
        assert engine._output_tokens == 0
        assert len(engine._messages) == 0
        assert len(engine._history) == 0

    def test_get_history(self):
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("first")
        engine.submit("second")
        history = engine.get_history()
        assert len(history) == 2
        assert history[0].prompt == "first"
        assert history[1].prompt == "second"

    def test_get_history_is_copy(self):
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("test")
        history = engine.get_history()
        history.clear()
        assert len(engine.get_history()) == 1

    def test_get_stats(self):
        engine = QueryEngine(QueryEngineConfig(), session_id="stats-test")
        engine.submit("hello")
        stats = engine.get_stats()
        assert stats["session_id"] == "stats-test"
        assert stats["turn_count"] == 1
        assert stats["message_count"] > 0
        assert "usage" in stats
        assert "config" in stats

    def test_determine_stop_reason_completed(self):
        engine = QueryEngine(QueryEngineConfig(max_turns=10, max_budget_tokens=100000))
        engine.submit("hello")
        assert engine._determine_stop_reason() == StopReason.COMPLETED

    def test_match_tools_case_insensitive(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("use PyTest", tools=["pytest"])
        assert "pytest" in result.matched_tools

    def test_match_agents_case_insensitive(self):
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("ask the TESTER", agents=["tester"])
        assert "tester" in result.matched_agents


class TestConvenienceFunctions:
    def test_create_default_engine(self):
        engine = create_default_engine()
        assert isinstance(engine, QueryEngine)
        assert engine.config.max_turns == 8

    def test_create_budget_conscious_engine(self):
        engine = create_budget_conscious_engine(50000)
        assert isinstance(engine, QueryEngine)
        assert engine.config.max_budget_tokens == 50000
        assert engine.config.compact_after_turns == 6

    def test_create_long_conversation_engine(self):
        engine = create_long_conversation_engine()
        assert isinstance(engine, QueryEngine)
        assert engine.config.max_turns == 20
        assert engine.config.max_budget_tokens == 500000
        assert engine.config.compact_after_turns == 15
