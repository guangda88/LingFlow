"""Unit tests for lingflow.coordination.agent module."""

import asyncio

import pytest

from lingflow.common.models import (
    AgentConfig,
    AgentStatus,
    Task,
    TaskPriority,
    TaskResult,
)
from lingflow.coordination.agent import Agent


class TestAgentInitialization:
    """Test Agent initialization."""

    def test_initialization_with_config(self):
        """Test agent initialization with AgentConfig."""
        config = AgentConfig(
            name="test_agent",
            description="Test agent for unit tests",
            capabilities=["test_capability"],
        )
        agent = Agent(config)

        assert agent.config.name == "test_agent"
        assert agent.config.description == "Test agent for unit tests"
        assert agent.config.capabilities == ["test_capability"]
        assert agent.status == AgentStatus.IDLE
        assert agent.tasks_completed == 0
        assert agent.tasks_failed == 0

    def test_initialization_default_status(self):
        """Test that agent starts with IDLE status."""
        config = AgentConfig(name="agent1", description="Agent 1", capabilities=["test"])
        agent = Agent(config)
        assert agent.status == AgentStatus.IDLE

    def test_initialization_counters_zero(self):
        """Test that task counters start at zero."""
        config = AgentConfig(name="agent1", description="Agent 1", capabilities=["test"])
        agent = Agent(config)
        assert agent.tasks_completed == 0
        assert agent.tasks_failed == 0


class TestAgentCanExecute:
    """Test Agent.can_execute method."""

    def test_can_execute_with_matching_agent_type(self):
        """Test can_execute returns True when agent_type matches."""
        config = AgentConfig(name="implementation", description="Implementation agent", capabilities=["code"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type="implementation",
        )

        assert agent.can_execute(task) is True

    def test_can_execute_with_different_agent_type(self):
        """Test can_execute returns False when agent_type doesn't match."""
        config = AgentConfig(name="implementation", description="Implementation agent", capabilities=["code"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type="review",  # Different from agent name
        )

        assert agent.can_execute(task) is False

    def test_can_execute_without_agent_type(self):
        """Test can_execute returns True when task has no agent_type."""
        config = AgentConfig(name="implementation", description="Implementation agent", capabilities=["code"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type="",  # Empty agent_type
        )

        assert agent.can_execute(task) is True

    def test_can_execute_with_none_agent_type(self):
        """Test can_execute returns True when task.agent_type is None."""
        config = AgentConfig(name="implementation", description="Implementation agent", capabilities=["code"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )
        # task.agent_type is None by default

        assert agent.can_execute(task) is True


class TestAgentExecuteTask:
    """Test Agent.execute_task method."""

    @pytest.mark.asyncio
    async def test_execute_task_success(self):
        """Test successful task execution."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type="test_agent",
        )

        context = {"key": "value"}
        result = await agent.execute_task(task, context)

        # Verify result
        assert result is not None
        assert result.task_id == "task-1"
        assert result.success is True
        assert "completed successfully" in result.output
        assert result.execution_time > 0
        assert result.agent_used == "test_agent"
        assert result.error is None

        # Verify agent state
        assert agent.status == AgentStatus.IDLE
        assert agent.tasks_completed == 1
        assert agent.tasks_failed == 0

    @pytest.mark.asyncio
    async def test_execute_task_sets_busy_status(self):
        """Test that agent status is BUSY during execution."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )

        async def check_status_during_execution():
            # Give agent time to start
            await asyncio.sleep(0.01)
            assert agent.status == AgentStatus.BUSY

        # Create a task that checks status during execution
        await asyncio.gather(agent.execute_task(task, {}), check_status_during_execution())

    @pytest.mark.asyncio
    async def test_execute_task_increments_completion_counter(self):
        """Test that tasks_completed counter is incremented."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )

        assert agent.tasks_completed == 0

        await agent.execute_task(task, {})

        assert agent.tasks_completed == 1

    @pytest.mark.asyncio
    async def test_execute_task_resets_to_idle(self):
        """Test that agent status resets to IDLE after successful execution."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )

        await agent.execute_task(task, {})

        assert agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_execute_task_measures_execution_time(self):
        """Test that execution time is measured accurately."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )

        result = await agent.execute_task(task, {})

        assert result.execution_time > 0
        # Execution time should be around 0.05 seconds (the sleep time)
        assert 0.04 < result.execution_time < 0.1


class TestAgentExecuteTaskFailure:
    """Test Agent.execute_task method error handling."""

    @pytest.mark.asyncio
    async def test_execute_task_with_exception(self):
        """Test that exceptions are handled gracefully."""
        from unittest.mock import AsyncMock, patch

        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )

        # Mock asyncio.sleep to raise an exception
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = ValueError("Test exception")
            result = await agent.execute_task(task, {})

        # Verify error handling
        assert result is not None
        assert result.task_id == "task-1"
        assert result.success is False
        assert "Test exception" in result.error
        assert result.execution_time > 0
        assert result.agent_used == "test_agent"

    @pytest.mark.asyncio
    async def test_execute_task_failure_sets_failed_status(self):
        """Test that agent status is set to FAILED on exception."""
        from unittest.mock import AsyncMock, patch

        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )

        # Mock asyncio.sleep to raise an exception
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = RuntimeError("Test error")
            await agent.execute_task(task, {})

        assert agent.status == AgentStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_task_failure_increments_failure_counter(self):
        """Test that tasks_failed counter is incremented on exception."""
        from unittest.mock import AsyncMock, patch

        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )

        assert agent.tasks_failed == 0

        # Mock asyncio.sleep to raise an exception
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = Exception("Test exception")
            await agent.execute_task(task, {})

        assert agent.tasks_failed == 1


class TestAgentGetInfo:
    """Test Agent.get_info method."""

    def test_get_info_returns_complete_info(self):
        """Test that get_info returns all agent information."""
        config = AgentConfig(
            name="test_agent",
            description="Test agent description",
            capabilities=["capability1", "capability2"],
        )
        agent = Agent(config)

        info = agent.get_info()

        assert info is not None
        assert info["name"] == "test_agent"
        assert info["description"] == "Test agent description"
        assert info["capabilities"] == ["capability1", "capability2"]
        assert info["status"] == AgentStatus.IDLE.value
        assert info["tasks_completed"] == 0
        assert info["tasks_failed"] == 0

    def test_get_info_updates_status(self):
        """Test that get_info reflects current agent status."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        agent.status = AgentStatus.BUSY
        info = agent.get_info()
        assert info["status"] == AgentStatus.BUSY.value

        agent.status = AgentStatus.FAILED
        info = agent.get_info()
        assert info["status"] == AgentStatus.FAILED.value

    def test_get_info_updates_counters(self):
        """Test that get_info reflects current task counters."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        agent.tasks_completed = 5
        agent.tasks_failed = 2
        info = agent.get_info()

        assert info["tasks_completed"] == 5
        assert info["tasks_failed"] == 2


class TestAgentIntegration:
    """Integration tests for Agent."""

    @pytest.mark.asyncio
    async def test_full_task_lifecycle(self):
        """Test complete lifecycle: check, execute, get info."""
        config = AgentConfig(
            name="implementation",
            description="Implementation agent",
            capabilities=["code_generation"],
        )
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Generate code",
            description="Write a function",
            priority=TaskPriority.HIGH,
            agent_type="implementation",
        )

        # Check if can execute
        assert agent.can_execute(task) is True

        # Execute task
        result = await agent.execute_task(task, {})
        assert result.success is True

        # Get agent info
        info = agent.get_info()
        assert info["tasks_completed"] == 1
        assert info["tasks_failed"] == 0
        assert info["status"] == AgentStatus.IDLE.value

    @pytest.mark.asyncio
    async def test_multiple_tasks_sequential(self):
        """Test executing multiple tasks sequentially."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        for i in range(3):
            task = Task(
                task_id=f"task-{i}",
                name=f"Task {i}",
                description="Test",
                priority=TaskPriority.NORMAL,
            )
            result = await agent.execute_task(task, {})
            assert result.success is True

        assert agent.tasks_completed == 3
        assert agent.tasks_failed == 0
        assert agent.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_task_with_context(self):
        """Test that context parameter is accepted even if not used."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-1",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )

        context = {
            "requirements": "Must be efficient",
            "constraints": ["low memory", "fast"],
            "timeout": 30,
        }

        result = await agent.execute_task(task, context)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_task_output_format(self):
        """Test that task output follows expected format."""
        config = AgentConfig(name="test_agent", description="Test agent", capabilities=["test"])
        agent = Agent(config)

        task = Task(
            task_id="task-123",
            name="Test task",
            description="Test",
            priority=TaskPriority.NORMAL,
        )

        result = await agent.execute_task(task, {})

        # Verify output format
        assert isinstance(result.output, str)
        assert "task-123" in result.output
        assert "completed" in result.output.lower()


class TestAgentConcurrentExecution:
    """Test concurrent execution of multiple agents."""

    @pytest.mark.asyncio
    async def test_multiple_agents_execute_concurrently(self):
        """Test that multiple agents can execute tasks concurrently."""
        # Create multiple agents
        configs = [AgentConfig(name=f"agent-{i}", description=f"Agent {i}", capabilities=["test"]) for i in range(5)]
        agents = [Agent(config) for config in configs]

        # Create tasks for each agent
        tasks = [
            Task(
                task_id=f"task-{i}",
                name=f"Task {i}",
                description=f"Test task {i}",
                priority=TaskPriority.NORMAL,
            )
            for i in range(5)
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*[agents[i].execute_task(tasks[i], {}) for i in range(5)])

        # Verify all tasks completed successfully
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.success is True, f"Task {i} failed"
            assert result.task_id == f"task-{i}"
            assert agents[i].tasks_completed == 1
            assert agents[i].tasks_failed == 0

    @pytest.mark.asyncio
    async def test_concurrent_execution_independent(self):
        """Test that concurrent executions are independent."""
        config1 = AgentConfig(name="agent1", description="Agent 1", capabilities=["test"])
        config2 = AgentConfig(name="agent2", description="Agent 2", capabilities=["test"])
        agent1 = Agent(config1)
        agent2 = Agent(config2)

        task1 = Task(
            task_id="task-1",
            name="Task 1",
            description="First task",
            priority=TaskPriority.NORMAL,
        )
        task2 = Task(
            task_id="task-2",
            name="Task 2",
            description="Second task",
            priority=TaskPriority.NORMAL,
        )

        # Execute tasks concurrently
        results = await asyncio.gather(
            agent1.execute_task(task1, {}),
            agent2.execute_task(task2, {}),
        )

        # Both should succeed independently
        assert len(results) == 2
        assert all(r.success for r in results)
        assert agent1.tasks_completed == 1
        assert agent2.tasks_completed == 1

    @pytest.mark.asyncio
    async def test_concurrent_with_varying_durations(self):
        """Test concurrent execution with tasks of different durations."""
        # Create agents
        configs = [AgentConfig(name=f"agent-{i}", description=f"Agent {i}", capabilities=["test"]) for i in range(3)]
        agents = [Agent(config) for config in configs]

        # Create tasks with different simulated durations
        tasks = [
            Task(
                task_id=f"task-{i}",
                name=f"Task {i}",
                description=f"Task with duration {i * 0.02}s",
                priority=TaskPriority.NORMAL,
            )
            for i in range(3)
        ]

        # Execute all tasks concurrently
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*[agents[i].execute_task(tasks[i], {}) for i in range(3)])
        end_time = asyncio.get_event_loop().time()

        # Verify all tasks completed
        assert len(results) == 3
        assert all(r.success for r in results)

        # Concurrent execution should be faster than sequential
        # Each task takes ~0.05s, so sequential would be ~0.15s
        # Concurrent should be ~0.05s (the longest task)
        execution_time = end_time - start_time
        assert execution_time < 0.1, f"Concurrent execution took {execution_time}s, expected < 0.1s"

    @pytest.mark.asyncio
    async def test_concurrent_error_handling(self):
        """Test error handling during concurrent execution."""
        config1 = AgentConfig(name="agent1", description="Agent 1", capabilities=["test"])
        config2 = AgentConfig(name="agent2", description="Agent 2", capabilities=["test"])
        agent1 = Agent(config1)
        agent2 = Agent(config2)

        task1 = Task(
            task_id="task-1",
            name="Task 1",
            description="Normal task",
            priority=TaskPriority.NORMAL,
        )
        task2 = Task(
            task_id="task-2",
            name="Task 2",
            description="Task that will fail",
            priority=TaskPriority.NORMAL,
        )

        # Modify agent2 to fail
        async def failing_execute(task, context):
            raise ValueError("Simulated failure")

        original_execute = agent2.execute_task
        agent2.execute_task = failing_execute

        # Execute tasks concurrently (one will fail)
        results = await asyncio.gather(
            agent1.execute_task(task1, {}),
            agent2.execute_task(task2, {}),
            return_exceptions=True,
        )

        # One result should be a TaskResult, one should be an exception
        assert len(results) == 2
        assert isinstance(results[0], TaskResult) and results[0].success
        assert isinstance(results[1], Exception)

        # Agent1 should have completed, agent2 should have failed
        assert agent1.tasks_completed == 1
        assert agent1.tasks_failed == 0

        # Restore original execute method
        agent2.execute_task = original_execute
