"""Tests for lingflow.core.query_engine module"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from lingflow.core.query_engine import (
    MessageCompactor,
    QueryEngine,
    QueryEngineConfig,
    StopReason,
    TurnResult,
    UsageSummary,
    create_budget_conscious_engine,
    create_default_engine,
    create_long_conversation_engine,
)


class TestQueryEngineConfig:
    """Test QueryEngineConfig dataclass"""

    def test_default_values(self):
        """Test default configuration values"""
        config = QueryEngineConfig()
        assert config.max_turns == 8
        assert config.max_budget_tokens == 200000
        assert config.compact_after_turns == 12
        assert config.compact_threshold_tokens == 100000
        assert config.structured_output is False
        assert config.structured_retry_limit == 2
        assert config.auto_compact is True

    def test_custom_values(self):
        """Test custom configuration values"""
        config = QueryEngineConfig(
            max_turns=20,
            max_budget_tokens=500000,
            compact_after_turns=15,
            compact_threshold_tokens=150000,
            structured_output=True,
            structured_retry_limit=5,
            auto_compact=False,
        )
        assert config.max_turns == 20
        assert config.max_budget_tokens == 500000
        assert config.compact_after_turns == 15
        assert config.compact_threshold_tokens == 150000
        assert config.structured_output is True
        assert config.structured_retry_limit == 5
        assert config.auto_compact is False

    def test_config_is_immutable(self):
        """Test that config is immutable (frozen)"""
        config = QueryEngineConfig()
        with pytest.raises(AttributeError):
            config.max_turns = 10


class TestTurnResult:
    """Test TurnResult dataclass"""

    def test_create_turn_result(self):
        """Test creating a turn result"""
        result = TurnResult(
            prompt="Test prompt",
            output="Test output",
            matched_tools=("tool1", "tool2"),
            matched_agents=("agent1",),
            input_tokens=100,
            output_tokens=50,
            stop_reason=StopReason.COMPLETED,
        )
        assert result.prompt == "Test prompt"
        assert result.output == "Test output"
        assert result.matched_tools == ("tool1", "tool2")
        assert result.matched_agents == ("agent1",)
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.stop_reason == StopReason.COMPLETED
        assert result.error is None

    def test_turn_result_with_error(self):
        """Test turn result with error"""
        result = TurnResult(
            prompt="Test",
            output="",
            matched_tools=(),
            matched_agents=(),
            input_tokens=0,
            output_tokens=0,
            stop_reason=StopReason.ERROR,
            error="Test error message",
        )
        assert result.error == "Test error message"
        assert result.stop_reason == StopReason.ERROR

    def test_turn_result_timestamp(self):
        """Test turn result has timestamp"""
        before = datetime.now()
        result = TurnResult(
            prompt="Test",
            output="Output",
            matched_tools=(),
            matched_agents=(),
            input_tokens=1,
            output_tokens=1,
            stop_reason=StopReason.COMPLETED,
        )
        after = datetime.now()
        assert before < datetime.fromisoformat(result.timestamp) < after

    def test_turn_result_is_immutable(self):
        """Test that turn result is immutable (frozen)"""
        result = TurnResult(
            prompt="Test",
            output="Output",
            matched_tools=(),
            matched_agents=(),
            input_tokens=1,
            output_tokens=1,
            stop_reason=StopReason.COMPLETED,
        )
        with pytest.raises(AttributeError):
            result.prompt = "New prompt"


class TestUsageSummary:
    """Test UsageSummary dataclass"""

    def test_default_values(self):
        """Test default usage summary values"""
        summary = UsageSummary()
        assert summary.total_input_tokens == 0
        assert summary.total_output_tokens == 0
        assert summary.turn_count == 0

    def test_custom_values(self):
        """Test custom usage summary values"""
        summary = UsageSummary(total_input_tokens=1000, total_output_tokens=500, turn_count=10)
        assert summary.total_input_tokens == 1000
        assert summary.total_output_tokens == 500
        assert summary.turn_count == 10

    def test_total_tokens_property(self):
        """Test total_tokens property calculation"""
        summary = UsageSummary(total_input_tokens=1000, total_output_tokens=500)
        assert summary.total_tokens == 1500

    def test_to_dict(self):
        """Test converting usage summary to dictionary"""
        summary = UsageSummary(total_input_tokens=100, total_output_tokens=50, turn_count=3)
        result = summary.to_dict()
        assert result == {"total_input_tokens": 100, "total_output_tokens": 50, "total_tokens": 150, "turn_count": 3}


class TestMessageCompactor:
    """Test MessageCompactor class"""

    def test_compact_messages_no_compaction_needed(self):
        """Test compaction when current_tokens <= target_tokens"""
        messages = ["msg1", "msg2", "msg3"]
        compacted, new_tokens = MessageCompactor.compact_messages(messages, target_tokens=100, current_tokens=50)
        assert compacted == messages
        assert new_tokens == 50

    def test_compact_messages_reduces_messages(self):
        """Test that compaction reduces message count"""
        messages = [f"msg{i}" for i in range(100)]
        compacted, new_tokens = MessageCompactor.compact_messages(messages, target_tokens=50, current_tokens=100)

        assert len(compacted) < len(messages)
        assert len(compacted) == 70  # 70% of 100
        assert new_tokens == 70

    def test_compact_messages_keeps_recent(self):
        """Test that compaction keeps recent messages"""
        messages = [f"msg{i}" for i in range(100)]
        compacted, _ = MessageCompactor.compact_messages(messages, target_tokens=50, current_tokens=100)

        # Should keep last 70 messages
        assert compacted[0] == "msg30"
        assert compacted[-1] == "msg99"

    def test_compact_messages_minimum_one(self):
        """Test that compaction keeps at least one message"""
        messages = ["msg1", "msg2"]
        compacted, _ = MessageCompactor.compact_messages(messages, target_tokens=1, current_tokens=100)
        assert len(compacted) >= 1

    def test_summarize_messages_empty(self):
        """Test summarizing empty message list"""
        summary = MessageCompactor.summarize_messages([])
        assert summary == ""

    def test_summarize_messages(self):
        """Test message summarization"""
        messages = ["First message here", "Middle content", "Last message here"]
        summary = MessageCompactor.summarize_messages(messages)
        assert "总消息数: 3" in summary
        assert "First message here" in summary
        assert "Last message here" in summary


class TestQueryEngine:
    """Test QueryEngine class"""

    def test_init_with_default_config(self):
        """Test initialization with default config"""
        engine = QueryEngine(QueryEngineConfig())
        assert engine.config.max_turns == 8
        assert engine.session_id is not None
        assert engine._messages == []
        assert engine._input_tokens == 0
        assert engine._output_tokens == 0
        assert engine._turn_count == 0

    def test_init_with_custom_session_id(self):
        """Test initialization with custom session ID"""
        engine = QueryEngine(QueryEngineConfig(), session_id="custom-session-123")
        assert engine.session_id == "custom-session-123"

    def test_usage_summary_property(self):
        """Test usage_summary property"""
        engine = QueryEngine(QueryEngineConfig())
        summary = engine.usage_summary
        assert isinstance(summary, UsageSummary)
        assert summary.total_input_tokens == 0
        assert summary.total_output_tokens == 0

    def test_submit_successful_query(self):
        """Test submitting a successful query"""
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("Hello, world!")

        assert result.prompt == "Hello, world!"
        assert result.output != ""
        assert result.input_tokens > 0
        assert result.output_tokens > 0
        assert result.stop_reason == StopReason.COMPLETED
        assert result.error is None

    def test_submit_increments_turn_count(self):
        """Test that submit increments turn count"""
        engine = QueryEngine(QueryEngineConfig())
        assert engine._turn_count == 0

        engine.submit("First")
        assert engine._turn_count == 1

        engine.submit("Second")
        assert engine._turn_count == 2

    def test_submit_max_turns_reached(self):
        """Test behavior when max turns is reached"""
        config = QueryEngineConfig(max_turns=2)
        engine = QueryEngine(config)

        result1 = engine.submit("First")
        assert result1.stop_reason == StopReason.COMPLETED
        assert engine._turn_count == 1

        # After first turn, only 1 more allowed
        result2 = engine.submit("Second")
        # After second submit, turn_count is now 2, which equals max_turns
        # But the submit itself succeeded, only the next one would fail
        assert result2.stop_reason in (StopReason.COMPLETED, StopReason.MAX_TURNS_REACHED)

        # Third should definitely fail
        result3 = engine.submit("Third")
        assert result3.stop_reason == StopReason.MAX_TURNS_REACHED
        assert result3.error is not None
        assert "最大轮数" in result3.error

    def test_submit_with_custom_process_func(self):
        """Test submit with custom processing function"""
        engine = QueryEngine(QueryEngineConfig())

        def custom_process(prompt):
            return f"Custom: {prompt}"

        result = engine.submit("Test", process_func=custom_process)
        assert result.output == "Custom: Test"

    def test_submit_with_tools_matching(self):
        """Test tool matching in submit"""
        engine = QueryEngine(QueryEngineConfig())
        tools = ["file_reader", "file_writer", "code_analyzer"]

        result = engine.submit("Please use file_reader to read the file", tools=tools)
        assert "file_reader" in result.matched_tools

    def test_submit_with_agents_matching(self):
        """Test agent matching in submit"""
        engine = QueryEngine(QueryEngineConfig())
        # Use exact case matching - the prompt must contain the agent name
        agents = ["python_expert", "javascript_expert", "data_scientist"]

        result = engine.submit("I need help with python_expert", agents=agents)
        assert "python_expert" in result.matched_agents

    def test_token_estimation(self):
        """Test token estimation for input/output"""
        engine = QueryEngine(QueryEngineConfig())
        result = engine.submit("This is a test message with five words")

        # Token estimation is based on word count (simplified)
        # The actual count includes all words in the prompt
        assert result.input_tokens > 0
        assert result.output_tokens > 0

    def test_get_history(self):
        """Test getting query history"""
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("First")
        engine.submit("Second")

        history = engine.get_history()
        assert len(history) == 2
        assert history[0].prompt == "First"
        assert history[1].prompt == "Second"

    def test_get_stats(self):
        """Test getting engine statistics"""
        engine = QueryEngine(QueryEngineConfig(max_turns=10))
        engine.submit("Test")

        stats = engine.get_stats()
        assert stats["session_id"] == engine.session_id
        assert stats["turn_count"] == 1
        assert stats["message_count"] == 2  # prompt + output
        assert "usage" in stats
        assert "config" in stats

    def test_reset(self):
        """Test resetting engine state"""
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("Test")

        assert engine._turn_count > 0
        assert len(engine._messages) > 0

        engine.reset()

        assert engine._turn_count == 0
        assert engine._messages == []
        assert engine._input_tokens == 0
        assert engine._output_tokens == 0

    def test_get_compact_summary(self):
        """Test getting compact summary"""
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("Test message")

        summary = engine.get_compact_summary()
        assert isinstance(summary, str)
        assert "总消息数" in summary

    def test_save_state(self, tmp_path):
        """Test saving engine state to file"""
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("Test")

        save_path = tmp_path / "test_state.json"
        result_path = engine.save_state(path=save_path)

        assert result_path.exists()
        with open(result_path) as f:
            data = json.load(f)
        assert data["session_id"] == engine.session_id
        assert "messages" in data
        assert "usage" in data

    def test_load_state(self, tmp_path):
        """Test loading engine state from file"""
        engine = QueryEngine(QueryEngineConfig())
        engine.submit("Test message")

        save_path = engine.save_state(path=tmp_path / "state.json")

        loaded_engine = QueryEngine.load_state(save_path)
        assert loaded_engine.session_id == engine.session_id
        assert loaded_engine._turn_count == engine._turn_count
        assert loaded_engine._messages == engine._messages


class TestFactoryFunctions:
    """Test factory functions"""

    def test_create_default_engine(self):
        """Test creating default engine"""
        engine = create_default_engine()
        assert isinstance(engine, QueryEngine)
        assert engine.config.max_turns == 8

    def test_create_budget_conscious_engine(self):
        """Test creating budget conscious engine"""
        engine = create_budget_conscious_engine(budget=50000)
        assert isinstance(engine, QueryEngine)
        assert engine.config.max_budget_tokens == 50000
        assert engine.config.compact_after_turns == 6
        assert engine.config.auto_compact is True

    def test_create_long_conversation_engine(self):
        """Test creating long conversation engine"""
        engine = create_long_conversation_engine()
        assert isinstance(engine, QueryEngine)
        assert engine.config.max_turns == 20
        assert engine.config.max_budget_tokens == 500000
        assert engine.config.compact_after_turns == 15
