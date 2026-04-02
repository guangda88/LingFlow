import time
import pytest
from unittest.mock import AsyncMock, MagicMock
from lingflow.testing.ai_runner import AIScenarioRunner, ScenarioResult, ScenarioStatus
from lingflow.testing.scenario import CodeTestScenario, CapturedToolCall


def _make_scenario(name="test_scenario", prompt="test prompt", code="def foo(): pass",
                   expected_tools=None, required_tools=None, expectations=None,
                   max_turns=3):
    return CodeTestScenario(
        name=name,
        prompt=prompt,
        description=f"Description for {name}",
        code_content=code,
        expected_tools=expected_tools or [],
        required_tools=required_tools or [],
        expectations=expectations,
        max_turns=max_turns,
    )


class TestScenarioResult:
    def test_to_dict(self):
        result = ScenarioResult(
            scenario_name="test",
            status=ScenarioStatus.PASSED,
            execution_time=1.5,
            error_message=None,
            timestamp=1234567890.0,
        )
        d = result.to_dict()
        assert d["scenario_name"] == "test"
        assert d["status"] == "passed"
        assert d["execution_time"] == 1.5
        assert d["timestamp"] == 1234567890.0

    def test_to_dict_with_captured_calls(self):
        call = CapturedToolCall(name="tool1", args={"x": 1}, timestamp=time.time())
        result = ScenarioResult(
            scenario_name="t",
            status=ScenarioStatus.FAILED,
            execution_time=0.1,
            captured_calls=[call],
            error_message="something failed",
        )
        d = result.to_dict()
        assert len(d["captured_calls"]) == 1


class TestAIScenarioRunner:
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

    def test_init(self, runner):
        assert runner.timeout == 5
        assert runner.scenarios_run == 0
        assert runner.scenarios_passed == 0

    def test_get_summary_empty(self, runner):
        summary = runner.get_summary()
        assert summary["total_scenarios"] == 0
        assert summary["success_rate"] == 0

    def test_reset_stats(self, runner):
        runner.scenarios_run = 5
        runner.scenarios_passed = 3
        runner.reset_stats()
        assert runner.scenarios_run == 0
        assert runner.scenarios_passed == 0

    @pytest.mark.asyncio
    async def test_run_scenario_validation_fails(self, runner):
        scenario = _make_scenario(name="")
        result = await runner.run_scenario(scenario, {})
        assert result.status == ScenarioStatus.FAILED
        assert "场景验证失败" in result.error_message

    @pytest.mark.asyncio
    async def test_run_scenario_validation_prompt_missing(self, runner):
        scenario = _make_scenario(prompt="")
        result = await runner.run_scenario(scenario, {})
        assert result.status == ScenarioStatus.FAILED

    @pytest.mark.asyncio
    async def test_run_scenario_validation_code_missing(self, runner):
        scenario = _make_scenario(code="")
        result = await runner.run_scenario(scenario, {})
        assert result.status == ScenarioStatus.FAILED

    @pytest.mark.asyncio
    async def test_run_scenario_validation_max_turns(self, runner):
        scenario = _make_scenario(max_turns=0)
        result = await runner.run_scenario(scenario, {})
        assert result.status == ScenarioStatus.FAILED

    @pytest.mark.asyncio
    async def test_run_scenario_skip_validation(self, runner):
        scenario = _make_scenario(name="")
        result = await runner.run_scenario(scenario, {}, validate_scenario=False)
        assert result.status != ScenarioStatus.FAILED or result.error_message != "场景验证失败"

    @pytest.mark.asyncio
    async def test_run_scenario_tool_not_found(self, runner):
        scenario = _make_scenario(expected_tools=["nonexistent_tool"])
        result = await runner.run_scenario(scenario, {})
        assert len(result.captured_calls) == 1
        assert result.captured_calls[0].result is None

    @pytest.mark.asyncio
    async def test_run_scenario_with_mock_tool(self, runner):
        mock_tool = AsyncMock()
        scenario = _make_scenario(
            expected_tools=["read_file"],
            required_tools=["read_file"],
        )
        tools = {"read_file": mock_tool}
        result = await runner.run_scenario(scenario, tools)
        assert result.status == ScenarioStatus.PASSED
        assert runner.scenarios_passed == 1

    @pytest.mark.asyncio
    async def test_run_scenario_missing_required_tool(self, runner):
        mock_tool = AsyncMock()
        scenario = _make_scenario(
            expected_tools=["read_file"],
            required_tools=["write_file"],
        )
        tools = {"read_file": mock_tool}
        result = await runner.run_scenario(scenario, tools)
        assert result.tool_expectations_met is False
        assert result.status == ScenarioStatus.FAILED

    @pytest.mark.asyncio
    async def test_run_scenario_expectations_fail(self, runner):
        def bad_expectations(calls):
            raise AssertionError("Expected 5 calls")

        mock_tool = AsyncMock()
        scenario = _make_scenario(
            expected_tools=["tool1"],
            expectations=bad_expectations,
        )
        tools = {"tool1": mock_tool}
        result = await runner.run_scenario(scenario, tools)
        assert result.status == ScenarioStatus.FAILED
        assert "期望验证失败" in result.error_message

    @pytest.mark.asyncio
    async def test_run_batch(self, runner):
        mock_tool = AsyncMock()
        scenarios = [
            _make_scenario(name=f"scene_{i}", expected_tools=["tool1"])
            for i in range(3)
        ]
        tools = {"tool1": mock_tool}
        results = await runner.run_batch(scenarios, tools)
        assert len(results) == 3
        assert runner.scenarios_run == 3

    def test_verify_tool_expectations_empty(self, runner):
        scenario = _make_scenario(required_tools=[], expected_tools=[])
        assert runner._verify_tool_expectations(scenario, []) is True

    def test_verify_tool_expectations_missing_required(self, runner):
        scenario = _make_scenario(required_tools=["required_tool"])
        calls = [CapturedToolCall(name="other_tool", args={}, timestamp=0)]
        assert runner._verify_tool_expectations(scenario, calls) is False

    def test_verify_tool_expectations_all_present(self, runner):
        scenario = _make_scenario(required_tools=["tool_a"], expected_tools=["tool_b"])
        calls = [
            CapturedToolCall(name="tool_a", args={}, timestamp=0),
            CapturedToolCall(name="tool_b", args={}, timestamp=0),
        ]
        assert runner._verify_tool_expectations(scenario, calls) is True

    def test_verify_tool_expectations_missing_expected_ok(self, runner):
        scenario = _make_scenario(required_tools=["tool_a"], expected_tools=["tool_b"])
        calls = [CapturedToolCall(name="tool_a", args={}, timestamp=0)]
        assert runner._verify_tool_expectations(scenario, calls) is True
