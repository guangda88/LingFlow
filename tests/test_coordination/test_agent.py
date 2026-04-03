"""Tests for lingflow.coordination.agent module"""

import pytest
import asyncio

from lingflow.coordination.agent import Agent
from lingflow.common.models import AgentConfig, AgentStatus, Task, TaskResult, TaskPriority


class TestAgent:
    """Test Agent class"""

    def test_init(self):
        """Test agent initialization"""
        config = AgentConfig(
            name="test_agent",
            description="A test agent",
            capabilities=["test", "demo"],
        )
        agent = Agent(config)

        assert agent.config == config
        assert agent.status == AgentStatus.IDLE
        assert agent.tasks_completed == 0
        assert agent.tasks_failed == 0

    def test_can_execute_matching_agent_type(self):
        """Test can_execute with matching agent type"""
        config = AgentConfig(
            name="python_expert",
            description="Python expert",
            capabilities=["python"]
        )
        agent = Agent(config)

        task = Task(
            task_id="test",
            name="Test",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type="python_expert"
        )
        assert agent.can_execute(task) is True

    def test_can_execute_different_agent_type(self):
        """Test can_execute with different agent type"""
        config = AgentConfig(
            name="python_expert",
            description="Python expert",
            capabilities=["python"]
        )
        agent = Agent(config)

        task = Task(
            task_id="test",
            name="Test",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type="javascript_expert"
        )
        assert agent.can_execute(task) is False

    def test_can_execute_no_agent_type_specified(self):
        """Test can_execute when no agent type is specified"""
        config = AgentConfig(
            name="general_agent",
            description="General agent",
            capabilities=["general"]
        )
        agent = Agent(config)

        task = Task(
            task_id="test",
            name="Test",
            description="Test",
            priority=TaskPriority.NORMAL,
            agent_type=""
        )
        assert agent.can_execute(task) is True

    async def test_execute_task_success(self):
        """Test successful task execution"""
        config = AgentConfig(
            name="test_agent",
            description="Test",
            capabilities=["testing"]
        )
        agent = Agent(config)

        task = Task(
            task_id="test-task",
            name="TestTask",
            description="Test task",
            priority=TaskPriority.NORMAL
        )
        context = {"key": "value"}

        result = await agent.execute_task(task, context)

        assert isinstance(result, TaskResult)
        assert result.task_id == "test-task"
        assert result.success is True
        assert result.agent_used == "test_agent"
        assert result.output != ""
        assert result.execution_time > 0
        assert result.error is None

        # Agent status should return to IDLE
        assert agent.status == AgentStatus.IDLE
        assert agent.tasks_completed == 1
        assert agent.tasks_failed == 0

    async def test_execute_task_multiple(self):
        """Test executing multiple tasks"""
        config = AgentConfig(
            name="multi_agent",
            description="Multi",
            capabilities=["multi"]
        )
        agent = Agent(config)

        task1 = Task(
            task_id="task-1",
            name="First",
            description="First",
            priority=TaskPriority.NORMAL
        )
        task2 = Task(
            task_id="task-2",
            name="Second",
            description="Second",
            priority=TaskPriority.NORMAL
        )

        result1 = await agent.execute_task(task1, {})
        result2 = await agent.execute_task(task2, {})

        assert result1.success is True
        assert result2.success is True
        assert agent.tasks_completed == 2

    def test_get_info(self):
        """Test getting agent info"""
        config = AgentConfig(
            name="info_agent",
            description="Info test agent",
            capabilities=["testing", "debugging"],
        )
        agent = Agent(config)

        info = agent.get_info()

        assert isinstance(info, dict)
        assert info["name"] == "info_agent"
        assert info["description"] == "Info test agent"
        assert info["capabilities"] == ["testing", "debugging"]
        assert info["status"] == AgentStatus.IDLE.value
        assert info["tasks_completed"] == 0
        assert info["tasks_failed"] == 0

    def test_get_info_after_tasks(self):
        """Test getting agent info after tasks"""
        config = AgentConfig(
            name="active_agent",
            description="Active",
            capabilities=["active"]
        )
        agent = Agent(config)

        # Simulate task completion
        agent.tasks_completed = 5
        agent.tasks_failed = 2

        info = agent.get_info()
        assert info["tasks_completed"] == 5
        assert info["tasks_failed"] == 2


class TestAgentAsyncIntegration:
    """Test Agent async execution integration"""

    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        """Test executing tasks concurrently"""
        config = AgentConfig(
            name="concurrent_agent",
            description="Concurrent",
            capabilities=["concurrent"]
        )
        agent = Agent(config)

        tasks = [
            Task(
                task_id=f"task-{i}",
                name=f"Task{i}",
                description=f"Task {i}",
                priority=TaskPriority.NORMAL
            )
            for i in range(5)
        ]

        results = await asyncio.gather(*[
            agent.execute_task(task, {}) for task in tasks
        ])

        assert len(results) == 5
        assert all(r.success for r in results)
        assert agent.tasks_completed == 5

    @pytest.mark.asyncio
    async def test_agent_status_during_execution(self):
        """Test agent status changes during execution"""
        config = AgentConfig(
            name="status_agent",
            description="Status",
            capabilities=["status"]
        )
        agent = Agent(config)

        task = Task(
            task_id="status-task",
            name="Status",
            description="Status test",
            priority=TaskPriority.NORMAL
        )

        # Status should be IDLE before execution
        assert agent.status == AgentStatus.IDLE

        # Execute task
        await agent.execute_task(task, {})

        # Status should return to IDLE after execution
        assert agent.status == AgentStatus.IDLE
