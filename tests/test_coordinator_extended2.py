"""Extended tests for coordinator covering skill execution, budget compression, etc."""
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lingflow.common.models import AgentConfig, Task, TaskPriority, TaskResult
from lingflow.coordination.agent import Agent
from lingflow.coordination.coordinator import AgentCoordinator
from lingflow.coordination.registry import AgentRegistry


class TestRegisterDefaultAgentsDetails:
    def test_agent_capabilities(self):
        coord = AgentCoordinator()
        agents = coord.registry.agents
        assert len(agents) == 6
        impl = agents.get("implementation")
        assert impl is not None
        assert "code_generation" in impl.config.capabilities
        assert "testing" in impl.config.capabilities
        assert "documentation" in impl.config.capabilities

    def test_agent_descriptions(self):
        coord = AgentCoordinator()
        agents = coord.registry.agents
        for name, agent in agents.items():
            assert agent.config.description
            assert len(agent.config.description) > 5


class TestCompressContextBudget:
    def test_compress_normal_context(self):
        coord = AgentCoordinator()
        ctx = {"key": "value", "data": [1, 2, 3]}
        result = coord._compress_context(ctx)
        assert isinstance(result, dict)

    def test_compress_with_empty_context(self):
        coord = AgentCoordinator()
        result = coord._compress_context({})
        assert isinstance(result, dict)

    def test_compress_preserves_on_error(self):
        coord = AgentCoordinator()
        ctx = {"key": "value"}
        with patch.object(coord.compressor, "compress", side_effect=ValueError("bad")):
            result = coord._compress_context(ctx)
        assert result == ctx

    def test_compress_preserves_on_unexpected_error(self):
        coord = AgentCoordinator()
        ctx = {"key": "value"}
        with patch.object(coord.compressor, "compress", side_effect=RuntimeError("oops")):
            result = coord._compress_context(ctx)
        assert result == ctx


class TestGetStatusBudget:
    def test_status_includes_budget(self):
        coord = AgentCoordinator()
        status = coord.get_status()
        assert "budget" in status
        assert status["budget"] is not None

    def test_status_total_tasks_includes_queue(self):
        coord = AgentCoordinator()
        task = Task(task_id="t1", name="test", description="test task", priority=TaskPriority.NORMAL)
        coord.submit_task(task)
        status = coord.get_status()
        assert status["total_tasks"] == 1


class TestExecuteSkillHappyPath:
    def test_execute_skill_returns_error_for_missing_path(self):
        coord = AgentCoordinator()
        with patch.object(coord, "_get_skill_path", return_value=None):
            result = coord.execute_skill("nonexistent-skill", {})
        assert result["skill"] == "nonexistent-skill"
        assert "error" in result

    def test_execute_skill_returns_error_for_failed_load(self):
        coord = AgentCoordinator()
        with patch.object(coord, "_get_skill_path", return_value="/fake/path.py"), \
             patch.object(coord, "_load_skill_module", return_value=None):
            result = coord.execute_skill("broken-skill", {})
        assert result["skill"] == "broken-skill"
        assert "error" in result

    def test_execute_skill_success_with_mocked_load(self):
        coord = AgentCoordinator()
        mock_module = MagicMock()
        mock_module.execute_skill.return_value = {"output": 42}

        with patch.object(coord, "_get_skill_path", return_value="/fake/path.py"), \
             patch.object(coord, "_load_skill_module", return_value=mock_module):
            result = coord.execute_skill("good-skill", {"x": 1})
        assert result["skill"] == "good-skill"
        assert result["result"] == {"output": 42}

    def test_execute_skill_import_error(self):
        coord = AgentCoordinator()
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = os.path.join(tmp, "skills", "bad-skill")
            os.makedirs(skill_dir)
            impl_path = os.path.join(skill_dir, "implementation.py")
            with open(impl_path, "w") as f:
                f.write("import nonexistent_module_xyz\ndef execute_skill(params): return {}\n")

            with patch("os.getcwd", return_value=tmp):
                result = coord.execute_skill("bad-skill", {})
            assert result["skill"] == "bad-skill"
            assert "error" in result


class TestGetSkillPathEdgeCases:
    def test_empty_name(self):
        coord = AgentCoordinator()
        assert coord._get_skill_path("") is None

    def test_too_short_name(self):
        coord = AgentCoordinator()
        assert coord._get_skill_path("ab") is None

    def test_too_long_name(self):
        coord = AgentCoordinator()
        assert coord._get_skill_path("a" * 51) is None

    def test_valid_name_nonexistent(self):
        coord = AgentCoordinator()
        assert coord._get_skill_path("nonexistent-skill") is None


class TestExecuteSkillModuleDirectly:
    def test_module_with_execute_skill(self):
        coord = AgentCoordinator()
        mock_module = MagicMock()
        mock_module.execute_skill.return_value = {"status": "ok"}
        result = coord._execute_skill_module(mock_module, {"p": 1})
        assert result == {"status": "ok"}

    def test_module_without_execute_skill(self):
        coord = AgentCoordinator()
        mock_module = MagicMock(spec=[])
        with pytest.raises(Exception, match="execute_skill"):
            coord._execute_skill_module(mock_module, {})


class TestProcessTaskResultsEdgeCases:
    def test_mixed_results(self):
        coord = AgentCoordinator()
        results = [
            TaskResult(task_id="t1", success=True, output="ok"),
            TaskResult(task_id="t2", success=False, error="fail"),
            RuntimeError("unexpected"),
        ]
        processed = coord._process_task_results(results)
        assert "t1" in processed
        assert "t2" in processed
        assert "t1" in coord.completed_tasks
        assert "t2" in coord.failed_tasks
        assert len(processed) == 2


class TestListSkillsEdgeCases:
    def test_no_skills_dir(self):
        coord = AgentCoordinator()
        with tempfile.TemporaryDirectory() as tmp:
            with patch("os.getcwd", return_value=tmp):
                result = coord.list_skills()
            assert result == []

    def test_ignores_underscore_dirs(self):
        coord = AgentCoordinator()
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = os.path.join(tmp, "skills")
            os.makedirs(os.path.join(skills_dir, "_private"))
            os.makedirs(os.path.join(skills_dir, "real-skill"))
            with open(os.path.join(skills_dir, "real-skill", "SKILL.md"), "w") as f:
                f.write("# Skill")
            with open(os.path.join(skills_dir, "_private", "SKILL.md"), "w") as f:
                f.write("# Private")
            with patch("os.getcwd", return_value=tmp):
                result = coord.list_skills()
            assert "real-skill" in result
            assert "_private" not in result


class TestFindAgentForTaskDetails:
    def test_finds_implementation_agent(self):
        coord = AgentCoordinator()
        task = Task(task_id="t1", name="code gen", description="generate code", priority=TaskPriority.NORMAL, agent_type="implementation")
        agent = coord._find_agent_for_task(task)
        assert agent is not None
        assert agent.config.name == "implementation"

    def test_no_agent_for_unknown_type(self):
        registry = AgentRegistry()
        coord = AgentCoordinator(registry=registry)
        task = Task(task_id="t1", name="unknown", description="unknown task", priority=TaskPriority.NORMAL, agent_type="nonexistent")
        agent = coord._find_agent_for_task(task)
        assert agent is None
