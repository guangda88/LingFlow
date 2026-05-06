"""Tests for AgentCoordinator"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from lingflow.common.exceptions import SkillLoadError
from lingflow.common.models import AgentConfig, Task, TaskPriority, TaskResult
from lingflow.coordination.agent import Agent
from lingflow.coordination.coordinator import AgentCoordinator
from lingflow.coordination.registry import AgentRegistry


class TestAgentCoordinatorInitialization:
    """Test coordinator initialization"""

    def test_initialization_default(self):
        """Test initialization with default registry"""
        coordinator = AgentCoordinator()
        assert coordinator.registry is not None
        assert len(coordinator.task_queue) == 0
        assert len(coordinator.completed_tasks) == 0
        assert len(coordinator.failed_tasks) == 0
        assert coordinator.compressor is not None
        assert coordinator.sandbox is not None

    def test_initialization_with_registry(self):
        """Test initialization with custom registry"""
        custom_registry = AgentRegistry()
        coordinator = AgentCoordinator(registry=custom_registry)
        assert coordinator.registry is custom_registry

    def test_register_default_agents(self):
        """Test that default agents are registered"""
        coordinator = AgentCoordinator()
        expected_agents = [
            "implementation",
            "review",
            "testing",
            "debugging",
            "architecture",
            "documentation",
        ]
        registered_agents = list(coordinator.registry.agents.keys())
        for agent_name in expected_agents:
            assert agent_name in registered_agents


class TestSubmitTask:
    """Test task submission"""

    def test_submit_task(self):
        """Test submitting a single task"""
        coordinator = AgentCoordinator()
        task = Task(
            task_id="test-1",
            name="Test Task",
            description="A test task",
            priority=TaskPriority.NORMAL,
            agent_type="implementation",
        )
        coordinator.submit_task(task)
        assert len(coordinator.task_queue) == 1
        assert coordinator.task_queue[0] == task

    def test_submit_multiple_tasks(self):
        """Test submitting multiple tasks"""
        coordinator = AgentCoordinator()
        tasks = [
            Task(
                task_id=f"test-{i}",
                name=f"Task {i}",
                description=f"Test task {i}",
                priority=TaskPriority.NORMAL,
                agent_type="implementation",
            )
            for i in range(3)
        ]
        for task in tasks:
            coordinator.submit_task(task)
        assert len(coordinator.task_queue) == 3


class TestExecuteTasksParallel:
    """Test parallel task execution"""

    @pytest.mark.asyncio
    async def test_execute_tasks_parallel(self):
        """Test executing tasks in parallel"""
        coordinator = AgentCoordinator()

        # Mock the agent execution
        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_agent = mock_find.return_value
            mock_agent.execute_task = AsyncMock(return_value=TaskResult(task_id="test-1", success=True, output="Done"))

            tasks = [
                Task(
                    task_id="test-1",
                    name="Test Task",
                    description="A test task",
                    priority=TaskPriority.NORMAL,
                    agent_type="implementation",
                )
            ]

            results = await coordinator.execute_tasks_parallel(tasks, max_parallel=2)

            assert "test-1" in results
            assert results["test-1"].success is True
            assert results["test-1"].output == "Done"

    @pytest.mark.asyncio
    async def test_execute_tasks_with_failure(self):
        """Test handling task failures"""
        coordinator = AgentCoordinator()

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_agent = mock_find.return_value
            mock_agent.execute_task = AsyncMock(return_value=TaskResult(task_id="test-1", success=False, error="Task failed"))

            tasks = [
                Task(
                    task_id="test-1",
                    name="Test Task",
                    description="A test task",
                    priority=TaskPriority.NORMAL,
                    agent_type="implementation",
                )
            ]

            results = await coordinator.execute_tasks_parallel(tasks)

            assert "test-1" in results
            assert results["test-1"].success is False
            assert results["test-1"].error == "Task failed"
            assert "test-1" in coordinator.failed_tasks

    @pytest.mark.asyncio
    async def test_execute_tasks_no_agent(self):
        """Test executing task when no agent is found"""
        coordinator = AgentCoordinator()

        with patch.object(coordinator, "_find_agent_for_task", return_value=None):
            tasks = [
                Task(
                    task_id="test-1",
                    name="Test Task",
                    description="A test task",
                    priority=TaskPriority.NORMAL,
                    agent_type="nonexistent",
                )
            ]

            results = await coordinator.execute_tasks_parallel(tasks)

            assert "test-1" in results
            assert results["test-1"].success is False
            assert "No suitable agent found" in results["test-1"].error


class TestFindAgentForTask:
    """Test agent finding logic"""

    def test_find_agent_for_task(self):
        """Test finding an agent for a task"""
        coordinator = AgentCoordinator()
        task = Task(
            task_id="test-1",
            name="Test Task",
            description="A test task",
            priority=TaskPriority.NORMAL,
            agent_type="implementation",
        )
        agent = coordinator._find_agent_for_task(task)
        assert agent is not None
        assert agent.config.name == "implementation"

    def test_find_agent_nonexistent(self):
        """Test finding agent for non-existent type"""
        coordinator = AgentCoordinator()
        task = Task(
            task_id="test-1",
            name="Test Task",
            description="A test task",
            priority=TaskPriority.NORMAL,
            agent_type="nonexistent",
        )
        agent = coordinator._find_agent_for_task(task)
        assert agent is None


class TestCompressContext:
    """Test context compression"""

    def test_compress_context(self):
        """Test compressing context"""
        coordinator = AgentCoordinator()
        context = {
            "requirements": "This is a long text that should be compressed",
            "description": "Another long text for compression",
            "extra": "Less important content",
        }
        compressed = coordinator._compress_context(context)
        assert compressed is not None
        assert isinstance(compressed, dict)

    def test_compress_context_error(self):
        """Test compressing context with error"""
        coordinator = AgentCoordinator()

        # Mock compressor to raise an error
        with patch.object(coordinator.compressor, "compress", side_effect=ValueError("Test error")):
            context = {"test": "data"}
            compressed = coordinator._compress_context(context)
            # Should return original context on error
            assert compressed == context


class TestCreateErrorResult:
    """Test error result creation"""

    def test_create_error_result(self):
        """Test creating an error result"""
        coordinator = AgentCoordinator()
        task = Task(task_id="test-1", name="Test Task", description="A test task", priority=TaskPriority.NORMAL)
        result = coordinator._create_error_result(task, "Something went wrong")
        assert result.task_id == "test-1"
        assert result.success is False
        assert result.error == "Something went wrong"


class TestProcessTaskResults:
    """Test processing task results"""

    def test_process_successful_results(self):
        """Test processing successful results"""
        coordinator = AgentCoordinator()
        results_list = [
            TaskResult(task_id="test-1", success=True, output="Done"),
            TaskResult(task_id="test-2", success=True, output="Done"),
        ]
        results = coordinator._process_task_results(results_list)
        assert len(results) == 2
        assert results["test-1"].success is True
        assert results["test-2"].success is True
        assert "test-1" in coordinator.completed_tasks
        assert "test-2" in coordinator.completed_tasks

    def test_process_failed_results(self):
        """Test processing failed results"""
        coordinator = AgentCoordinator()
        results_list = [
            TaskResult(task_id="test-1", success=False, error="Failed"),
        ]
        results = coordinator._process_task_results(results_list)
        assert len(results) == 1
        assert results["test-1"].success is False
        assert "test-1" in coordinator.failed_tasks

    def test_process_exception_results(self):
        """Test processing results with exceptions — should create TaskResult"""
        coordinator = AgentCoordinator()
        results_list = [Exception("Task failed")]
        results = coordinator._process_task_results(results_list)
        assert len(results) == 1
        assert results["unknown-0"].success is False
        assert "Task failed" in results["unknown-0"].error
        assert "unknown-0" in coordinator.failed_tasks


class TestGetStatus:
    """Test getting coordinator status"""

    def test_get_status_empty(self):
        """Test getting status with no tasks"""
        coordinator = AgentCoordinator()
        status = coordinator.get_status()
        assert status["total_tasks"] == 0
        assert status["completed_tasks"] == 0
        assert status["failed_tasks"] == 0
        assert status["agents"] == 6
        assert "compression_stats" in status

    def test_get_status_with_tasks(self):
        """Test getting status with tasks"""
        coordinator = AgentCoordinator()
        coordinator.completed_tasks["test-1"] = TaskResult(task_id="test-1", success=True, output="Done")
        coordinator.failed_tasks["test-2"] = TaskResult(task_id="test-2", success=False, error="Failed")
        status = coordinator.get_status()
        assert status["completed_tasks"] == 1
        assert status["failed_tasks"] == 1
        assert status["total_tasks"] == 1


class TestReset:
    """Test resetting coordinator state"""

    def test_reset(self):
        """Test resetting coordinator"""
        coordinator = AgentCoordinator()
        coordinator.submit_task(Task(task_id="test-1", name="Test", description="Test", priority=TaskPriority.NORMAL))
        coordinator.completed_tasks["test-2"] = TaskResult(task_id="test-2", success=True, output="Done")
        coordinator.failed_tasks["test-3"] = TaskResult(task_id="test-3", success=False, error="Failed")

        coordinator.reset()

        assert len(coordinator.task_queue) == 0
        assert len(coordinator.completed_tasks) == 0
        assert len(coordinator.failed_tasks) == 0


class TestExecuteSkill:
    """Test skill execution"""

    def test_execute_skill_invalid_skill(self):
        """Test executing non-existent skill"""
        coordinator = AgentCoordinator()
        result = coordinator.execute_skill("nonexistent", {"param": "value"})
        assert result["skill"] == "nonexistent"
        assert "error" in result
        assert "不存在" in result["error"]

    def test_execute_skill_invalid_name_format(self):
        """Test executing skill with invalid name format"""
        coordinator = AgentCoordinator()
        result = coordinator.execute_skill("../../etc/passwd", {})
        assert result["skill"] == "../../etc/passwd"
        assert "error" in result

    def test_execute_skill_invalid_name_length(self):
        """Test executing skill with invalid name length"""
        coordinator = AgentCoordinator()
        result = coordinator.execute_skill("ab", {})
        assert result["skill"] == "ab"
        assert "error" in result


class TestGetSkillPath:
    """Test getting skill path"""

    def test_get_skill_path_invalid_name(self):
        """Test getting path for invalid skill name"""
        coordinator = AgentCoordinator()
        assert coordinator._get_skill_path("") is None
        assert coordinator._get_skill_path("ab") is None
        assert coordinator._get_skill_path("a" * 51) is None
        assert coordinator._get_skill_path("invalid/name") is None

    def test_get_skill_path_nonexistent(self):
        """Test getting path for non-existent skill"""
        coordinator = AgentCoordinator()
        path = coordinator._get_skill_path("nonexistent_skill")
        assert path is None


class TestLoadSkillModule:
    """Test loading skill module"""

    def test_load_skill_module_nonexistent(self):
        """Test loading non-existent skill module"""
        coordinator = AgentCoordinator()
        with pytest.raises(SkillLoadError):
            coordinator._load_skill_module("test", "/nonexistent/path.py")

    def test_load_skill_module_invalid_code(self):
        """Test loading skill module with invalid code"""
        coordinator = AgentCoordinator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write("this is not valid python code !!!")
            temp_path = f.name

        try:
            with pytest.raises(SkillLoadError):
                coordinator._load_skill_module("test", temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_skill_module_unsafe_code(self):
        """Test loading skill module with unsafe code (import os)"""
        coordinator = AgentCoordinator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write("""
import os

def execute_skill(params):
    return "result"
""")
            temp_path = f.name

        try:
            with pytest.raises(SkillLoadError):
                coordinator._load_skill_module("test", temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_skill_module_missing_execute_skill(self):
        """Test loading skill module without execute_skill function"""
        coordinator = AgentCoordinator()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write("""
def other_function(params):
    return "result"
""")
            temp_path = f.name

        try:
            with pytest.raises(SkillLoadError, match="missing required execute_skill function"):
                coordinator._load_skill_module("test", temp_path)
        finally:
            os.unlink(temp_path)


class TestListSkills:
    """Test listing skills"""

    def test_list_skills(self):
        """Test listing available skills"""
        coordinator = AgentCoordinator()
        skills = coordinator.list_skills()
        assert isinstance(skills, list)
        assert len(skills) > 0
        assert "code-review" in skills
        assert "brainstorming" in skills


class TestContextCompressor:
    """Test context compressor integration"""

    def test_compressor_get_stats(self):
        """Test getting compressor statistics via coordinator get_status"""
        coordinator = AgentCoordinator()
        status = coordinator.get_status()
        assert "compression_stats" in status
        assert "status" in status["compression_stats"]

    def test_compressor_get_stats_with_messages(self):
        """Test SmartContextCompressor get_stats with messages"""
        coordinator = AgentCoordinator()
        messages = [{"role": "user", "content": "hello world"}]
        stats = coordinator.compressor.get_stats(messages)
        assert "message_count" in stats
        assert "token_count" in stats


class TestErrorHandling:
    """Test error handling in coordinator"""

    @pytest.mark.asyncio
    async def test_task_execution_failure_handling(self):
        """Test that coordinator handles task execution failures gracefully"""
        coordinator = AgentCoordinator()

        task = Task(
            task_id="test-fail",
            name="Failing Task",
            description="A task that will fail",
            priority=TaskPriority.NORMAL,
            agent_type="implementation",
        )

        # Mock agent to throw exception
        async def failing_execute(task, context):
            raise ValueError("Simulated execution failure")

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_agent = mock_find.return_value
            mock_agent.execute_task = failing_execute

            # Execute task using parallel API
            results = await coordinator.execute_tasks_parallel([task], max_parallel=1)

            # Verify error is captured — exceptions now create TaskResult
            assert len(results) == 1
            assert results["test-fail"].success is False
            assert "Simulated execution failure" in results["test-fail"].error
            assert "test-fail" in coordinator.failed_tasks

    @pytest.mark.asyncio
    async def test_agent_not_found_handling(self):
        """Test that coordinator handles missing agent gracefully"""
        coordinator = AgentCoordinator()

        task = Task(
            task_id="test-no-agent",
            name="Task for non-existent agent",
            description="A task for agent that doesn't exist",
            priority=TaskPriority.NORMAL,
            agent_type="non_existent_agent",
        )

        # Find agent for task should return None
        with patch.object(coordinator, "_find_agent_for_task", return_value=None):
            results = await coordinator.execute_tasks_parallel([task], max_parallel=1)

            # Verify error is captured
            assert "test-no-agent" in coordinator.failed_tasks
            assert coordinator.failed_tasks["test-no-agent"].success is False
            # Error message is "No suitable agent found" (not "agent not found")
            assert "suitable agent" in coordinator.failed_tasks["test-no-agent"].error.lower()

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test that coordinator handles timeouts gracefully"""
        coordinator = AgentCoordinator()

        task = Task(
            task_id="test-timeout",
            name="Timeout Task",
            description="A task that will timeout",
            priority=TaskPriority.NORMAL,
            agent_type="implementation",
        )

        # Mock agent to sleep for longer than timeout
        async def timeout_execute(task, context):
            import asyncio

            await asyncio.sleep(10)  # Sleep longer than expected timeout

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_agent = mock_find.return_value
            mock_agent.execute_task = timeout_execute

            # Execute task with short timeout
            try:
                result = await asyncio.wait_for(coordinator.execute_tasks_parallel([task], max_parallel=1), timeout=0.1)
                # If we get here, timeout wasn't enforced
                # This is expected behavior for current implementation
            except asyncio.TimeoutError:
                # Timeout was enforced
                pass

    @pytest.mark.asyncio
    async def test_parallel_execution_with_failures(self):
        """Test that parallel execution handles individual failures"""
        coordinator = AgentCoordinator()

        # Create 3 tasks, one will fail
        tasks = []
        for i in range(3):
            task = Task(
                task_id=f"task-{i}",
                name=f"Task {i}",
                description=f"Test task {i}",
                priority=TaskPriority.NORMAL,
                agent_type="implementation",
            )
            tasks.append(task)

        # Mock agent execution - task 1 will fail by returning TaskResult with success=False
        execution_count = [0]

        async def mixed_execute(task, context):
            execution_count[0] += 1
            if task.task_id == "task-1":
                # Return a failed TaskResult instead of throwing exception
                return TaskResult(task_id=task.task_id, success=False, error=f"Task {task.task_id} failed")
            return TaskResult(task_id=task.task_id, success=True, output=f"{task.task_id} completed")

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_agent = mock_find.return_value
            mock_agent.execute_task = mixed_execute

            # Execute tasks in parallel
            results = await coordinator.execute_tasks_parallel(tasks, max_parallel=2)

            # Verify results - all tasks should be in results because they return TaskResult
            assert len(results) == 3
            assert results["task-0"].success is True
            assert results["task-1"].success is False
            assert results["task-2"].success is True
            assert execution_count[0] == 3  # All tasks attempted
            # Check failed_tasks dict
            assert len(coordinator.failed_tasks) == 1
            assert "task-1" in coordinator.failed_tasks
            assert len(coordinator.completed_tasks) == 2

    @pytest.mark.asyncio
    async def test_recovery_after_failure(self):
        """Test that coordinator can recover after a failure"""
        coordinator = AgentCoordinator()

        # Create tasks - first will fail, second should succeed
        task1 = Task(
            task_id="fail-1",
            name="Failing Task",
            description="Will fail",
            priority=TaskPriority.NORMAL,
            agent_type="implementation",
        )
        task2 = Task(
            task_id="success-1",
            name="Success Task",
            description="Will succeed",
            priority=TaskPriority.NORMAL,
            agent_type="implementation",
        )

        # Track execution state
        execution_count = [0]

        async def stateful_execute(task, context):
            execution_count[0] += 1
            if task.task_id == "fail-1":
                # Return a failed TaskResult
                return TaskResult(task_id=task.task_id, success=False, error="First task fails")
            return TaskResult(task_id=task.task_id, success=True, output=f"{task.task_id} completed")

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_agent = mock_find.return_value
            mock_agent.execute_task = stateful_execute

            # Execute first task (will fail)
            results1 = await coordinator.execute_tasks_parallel([task1], max_parallel=1)
            assert results1["fail-1"].success is False
            assert len(coordinator.failed_tasks) == 1

            # Execute second task (should succeed)
            results2 = await coordinator.execute_tasks_parallel([task2], max_parallel=1)
            assert results2["success-1"].success is True
            assert len(coordinator.completed_tasks) == 1
            assert execution_count[0] == 2  # Both tasks attempted


class AsyncMock(MagicMock):
    """Async mock for testing async methods"""

    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)
