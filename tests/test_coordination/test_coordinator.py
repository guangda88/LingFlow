"""Tests for lingflow.coordination.coordinator module"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from lingflow.common.models import AgentConfig, Task, TaskPriority, TaskResult
from lingflow.coordination.coordinator import AgentCoordinator
from lingflow.coordination.registry import AgentRegistry


class TestAgentCoordinator:
    """Test AgentCoordinator class"""

    def test_init_default_registry(self):
        """Test initialization with default registry"""
        coordinator = AgentCoordinator()

        assert coordinator.registry is not None
        assert isinstance(coordinator.registry, AgentRegistry)
        assert coordinator.task_queue == []
        assert coordinator.completed_tasks == {}
        assert coordinator.failed_tasks == {}

    def test_init_with_custom_registry(self):
        """Test initialization with custom registry"""
        custom_registry = AgentRegistry()
        coordinator = AgentCoordinator(registry=custom_registry)

        assert coordinator.registry == custom_registry

    def test_default_agents_registered(self):
        """Test that default agents are registered"""
        coordinator = AgentCoordinator()

        agents_count = len(coordinator.registry.agents)
        assert agents_count > 0

        # Check for expected default agents
        expected_agents = [
            "implementation",
            "review",
            "testing",
            "debugging",
            "architecture",
            "documentation",
        ]
        for agent_name in expected_agents:
            assert agent_name in coordinator.registry.agents

    def test_submit_task(self):
        """Test submitting a task"""
        coordinator = AgentCoordinator()
        task = Task(task_id="test-task", name="Test", description="Test task", priority=TaskPriority.NORMAL)

        coordinator.submit_task(task)

        assert len(coordinator.task_queue) == 1
        assert coordinator.task_queue[0] == task

    def test_submit_multiple_tasks(self):
        """Test submitting multiple tasks"""
        coordinator = AgentCoordinator()

        for i in range(5):
            task = Task(task_id=f"task-{i}", name=f"Task{i}", description=f"Task {i}", priority=TaskPriority.NORMAL)
            coordinator.submit_task(task)

        assert len(coordinator.task_queue) == 5

    @pytest.mark.asyncio
    async def test_execute_tasks_parallel(self):
        """Test parallel task execution"""
        coordinator = AgentCoordinator()

        tasks = [
            Task(task_id=f"task-{i}", name=f"Task{i}", description=f"Task {i}", priority=TaskPriority.NORMAL) for i in range(3)
        ]

        results = await coordinator.execute_tasks_parallel(tasks, max_parallel=2)

        assert len(results) == 3
        for task_id, result in results.items():
            assert result.success is True
            assert result.task_id == task_id

    @pytest.mark.asyncio
    async def test_execute_tasks_with_max_parallel_one(self):
        """Test parallel execution with max_parallel=1"""
        coordinator = AgentCoordinator()

        tasks = [
            Task(task_id=f"task-{i}", name=f"Task{i}", description=f"Task {i}", priority=TaskPriority.NORMAL) for i in range(3)
        ]

        results = await coordinator.execute_tasks_parallel(tasks, max_parallel=1)

        assert len(results) == 3
        assert all(r.success for r in results.values())

    def test_get_status(self):
        """Test getting coordinator status"""
        coordinator = AgentCoordinator()
        status = coordinator.get_status()

        assert isinstance(status, dict)
        assert "total_tasks" in status
        assert "completed_tasks" in status
        assert "failed_tasks" in status
        assert "agents" in status
        assert "compression_stats" in status
        assert "budget" in status

    def test_get_status_with_tasks(self):
        """Test status with tasks in queue"""
        coordinator = AgentCoordinator()

        coordinator.submit_task(Task(task_id="task-1", name="T1", description="Test", priority=TaskPriority.NORMAL))
        coordinator.submit_task(Task(task_id="task-2", name="T2", description="Test", priority=TaskPriority.NORMAL))

        status = coordinator.get_status()
        assert status["total_tasks"] >= 2

    def test_reset(self):
        """Test resetting coordinator"""
        coordinator = AgentCoordinator()

        coordinator.submit_task(Task(task_id="task-1", name="T1", description="Test", priority=TaskPriority.NORMAL))
        coordinator.completed_tasks["task-1"] = TaskResult(task_id="task-1", success=True, output="Done")
        coordinator.failed_tasks["task-2"] = TaskResult(task_id="task-2", success=False, error="Failed")

        assert len(coordinator.task_queue) > 0
        assert len(coordinator.completed_tasks) > 0
        assert len(coordinator.failed_tasks) > 0

        coordinator.reset()

        assert coordinator.task_queue == []
        assert coordinator.completed_tasks == {}
        assert coordinator.failed_tasks == {}

    def test_list_skills(self):
        """Test listing available skills"""
        coordinator = AgentCoordinator()
        skills = coordinator.list_skills()

        assert isinstance(skills, list)
        # Skills directory may not exist in test environment
        # so we just verify it returns a list

    def test_execute_skill_nonexistent(self):
        """Test executing non-existent skill"""
        coordinator = AgentCoordinator()
        result = coordinator.execute_skill("nonexistent_skill_xyz", {})

        assert "error" in result
        assert "nonexistent_skill_xyz" in result.get("error", "")


class TestAgentCoordinatorContextCompression:
    """Test coordinator context compression functionality"""

    def test_compress_context_normal(self):
        """Test context compression with normal data"""
        coordinator = AgentCoordinator()

        context = {"key1": "value1", "key2": "value2", "data": list(range(100))}
        compressed = coordinator._compress_context(context)

        # Should return a dict (may be compressed or original)
        assert isinstance(compressed, dict)

    def test_compress_context_empty(self):
        """Test compressing empty context"""
        coordinator = AgentCoordinator()
        compressed = coordinator._compress_context({})
        assert isinstance(compressed, dict)

    def test_compress_context_invalid_input(self):
        """Test compressing invalid context input"""
        coordinator = AgentCoordinator()

        # Should handle various input types gracefully
        result1 = coordinator._compress_context(None)
        result2 = coordinator._compress_context("string")
        result3 = coordinator._compress_context(123)

        # Should not crash


class TestAgentCoordinatorAgentFinding:
    """Test coordinator agent finding logic"""

    def test_find_agent_for_task_no_agents(self):
        """Test finding agent when registry is empty"""
        coordinator = AgentCoordinator()
        coordinator.registry = AgentRegistry()

        task = Task(task_id="test", name="Test", description="Test", priority=TaskPriority.NORMAL)
        agent = coordinator._find_agent_for_task(task)

        assert agent is None

    def test_find_agent_for_task_with_agent_type(self):
        """Test finding agent with specific agent_type"""
        from lingflow.coordination.agent import Agent

        coordinator = AgentCoordinator()
        coordinator.registry = AgentRegistry()

        # Register a test agent
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)
        coordinator.registry.register_agent(agent)

        task = Task(task_id="test", name="Test", description="Test", priority=TaskPriority.NORMAL, agent_type="test_agent")
        found_agent = coordinator._find_agent_for_task(task)

        assert found_agent is not None
        assert found_agent.config.name == "test_agent"

    def test_find_agent_for_task_without_agent_type(self):
        """Test finding agent without specific agent_type"""
        coordinator = AgentCoordinator()

        task = Task(task_id="test", name="Test", description="Test", priority=TaskPriority.NORMAL, agent_type="")
        agent = coordinator._find_agent_for_task(task)

        # Should find some default agent
        assert agent is not None
