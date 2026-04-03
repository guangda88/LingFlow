"""Extended AI runner tests for additional coverage."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from lingflow.testing.ai_runner import (
    AIScenarioRunner,
    ScenarioStatus,
    ScenarioResult,
)


class TestScenarioStatus:
    def test_values(self):
        assert ScenarioStatus.PENDING == "pending"
        assert ScenarioStatus.RUNNING == "running"
        assert ScenarioStatus.PASSED == "passed"
        assert ScenarioStatus.FAILED == "failed"
        assert ScenarioStatus.SKIPPED == "skipped"
        assert ScenarioStatus.TIMEOUT == "timeout"


class TestScenarioResult:
    def test_defaults(self):
        r = ScenarioResult(scenario_name="test", status=ScenarioStatus.PASSED, execution_time=1.0)
        assert r.captured_calls == []
        assert r.error_message is None
        assert r.response_data is None
        assert r.tool_expectations_met is True
        assert r.timestamp == 0.0

    def test_to_dict(self):
        r = ScenarioResult(
            scenario_name="test",
            status=ScenarioStatus.PASSED,
            execution_time=1.5,
            timestamp=1234567890.0,
        )
        d = r.to_dict()
        assert d["status"] == "passed"
        assert d["scenario_name"] == "test"
        assert d["timestamp"] == 1234567890.0


class TestAIScenarioRunnerInit:
    def test_init_defaults(self):
        runner = AIScenarioRunner()
        assert runner.timeout == 60
        assert runner.scenarios_run == 0
        assert runner.scenarios_passed == 0
        assert runner.scenarios_failed == 0
        assert runner.scenarios_timeout == 0

    def test_init_custom_timeout(self):
        runner = AIScenarioRunner(timeout=30)
        assert runner.timeout == 30


class TestAIScenarioRunnerSummary:
    def test_get_summary_empty(self):
        runner = AIScenarioRunner()
        summary = runner.get_summary()
        assert summary["total_scenarios"] == 0
        assert summary["passed"] == 0
        assert summary["failed"] == 0
        assert summary["timeout"] == 0
        assert summary["success_rate"] == 0

    def test_get_summary_with_results(self):
        runner = AIScenarioRunner()
        runner.scenarios_run = 10
        runner.scenarios_passed = 7
        runner.scenarios_failed = 2
        runner.scenarios_timeout = 1
        summary = runner.get_summary()
        assert summary["success_rate"] == 0.7

    def test_reset_stats(self):
        runner = AIScenarioRunner()
        runner.scenarios_run = 10
        runner.scenarios_passed = 5
        runner.reset_stats()
        assert runner.scenarios_run == 0
        assert runner.scenarios_passed == 0


class TestAIScenarioRunnerRunScenario:
    @pytest.fixture
    def mock_server(self):
        server = MagicMock()
        server.temp_dir = "/tmp/test"
        server.add_python_route = MagicMock()
        server.restore = MagicMock()
        return server

    @pytest.fixture
    def runner(self, mock_server):
        return AIScenarioRunner(test_server=mock_server, timeout=5)

    def _make_scenario(self, name="test", tools=None, required=None, code="pass", max_turns=5, expectations=None):
        s = MagicMock()
        s.name = name
        s.code_content = code
        s.expected_tools = tools or ["tool_a"]
        s.required_tools = required or []
        s.max_turns = max_turns
        s.expectations = expectations
        s.validate = MagicMock()
        return s

    def _make_tool(self, name="tool_a"):
        tool = AsyncMock()
        tool.handle = AsyncMock()
        return tool

    @pytest.mark.asyncio
    async def test_validation_failure(self, runner):
        scenario = self._make_scenario()
        scenario.validate.side_effect = ValueError("bad scenario")
        result = await runner.run_scenario(scenario, {})
        assert result.status == ScenarioStatus.FAILED
        assert "验证失败" in result.error_message

    @pytest.mark.asyncio
    async def test_missing_tool_logs_warning(self, runner):
        scenario = self._make_scenario(tools=["nonexistent"])
        result = await runner.run_scenario(scenario, {})
        assert result.status == ScenarioStatus.PASSED
        assert len(result.captured_calls) == 1
        assert result.captured_calls[0].result is None

    @pytest.mark.asyncio
    async def test_successful_run(self, runner):
        scenario = self._make_scenario(tools=["tool_a"])
        tool = self._make_tool()
        tools = {"tool_a": tool}
        result = await runner.run_scenario(scenario, tools)
        assert result.status == ScenarioStatus.PASSED

    @pytest.mark.asyncio
    async def test_expectation_failure(self, runner):
        def bad_expectations(calls):
            raise AssertionError("expected tool not called")

        scenario = self._make_scenario(tools=["tool_a"], expectations=bad_expectations)
        tool = self._make_tool()
        tools = {"tool_a": tool}
        result = await runner.run_scenario(scenario, tools)
        assert result.status == ScenarioStatus.FAILED

    @pytest.mark.asyncio
    async def test_skip_validation(self, runner):
        scenario = self._make_scenario()
        result = await runner.run_scenario(scenario, {}, validate_scenario=False)
        scenario.validate.assert_not_called()

    @pytest.mark.asyncio
    async def test_required_tool_missing(self, runner):
        scenario = self._make_scenario(tools=["tool_a"], required=["tool_b"])
        tool = self._make_tool()
        result = await runner.run_scenario(scenario, {"tool_a": tool})
        assert result.tool_expectations_met is False

    @pytest.mark.asyncio
    async def test_max_turns_limits_iterations(self, runner):
        scenario = self._make_scenario(tools=["t1", "t2", "t3"], max_turns=2)
        tool = self._make_tool()
        tools = {"t1": tool, "t2": tool, "t3": tool}
        result = await runner.run_scenario(scenario, tools)
        assert result.status == ScenarioStatus.PASSED

    @pytest.mark.asyncio
    async def test_run_updates_stats(self, runner):
        scenario = self._make_scenario(tools=["tool_a"])
        tool = self._make_tool()
        await runner.run_scenario(scenario, {"tool_a": tool})
        assert runner.scenarios_run == 1
        assert runner.scenarios_passed == 1

    @pytest.mark.asyncio
    async def test_execution_time_set(self, runner):
        scenario = self._make_scenario(tools=["tool_a"])
        tool = self._make_tool()
        result = await runner.run_scenario(scenario, {"tool_a": tool})
        assert result.execution_time >= 0

    @pytest.mark.asyncio
    async def test_run_batch(self, runner):
        s1 = self._make_scenario(name="s1", tools=["tool_a"])
        s2 = self._make_scenario(name="s2", tools=["tool_a"])
        tool = self._make_tool()
        results = await runner.run_batch([s1, s2], {"tool_a": tool})
        assert len(results) == 2
        assert runner.scenarios_run == 2
