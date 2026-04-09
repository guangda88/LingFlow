"""Tests for lingflow.coordination.base module"""

import pytest

from lingflow.common.models import Task, TaskPriority, TaskResult
from lingflow.coordination.base import BaseAgent, BaseCoordinator


class TestBaseCoordinator:
    """Test BaseCoordinator class"""

    def test_init(self):
        """Test initialization"""
        coordinator = BaseCoordinator()
        assert coordinator is not None

    def test_format_result_success(self):
        """Test formatting successful result"""
        coordinator = BaseCoordinator()
        result = coordinator._format_result("task-1", True, "output data")

        assert isinstance(result, TaskResult)
        assert result.task_id == "task-1"
        assert result.success is True
        assert result.output == "output data"
        assert result.error == ""  # Empty string, not None
        assert result.agent_used == "base"

    def test_format_result_failure(self):
        """Test formatting failed result"""
        coordinator = BaseCoordinator()
        result = coordinator._format_result("task-2", False, error="Test error")

        assert isinstance(result, TaskResult)
        assert result.task_id == "task-2"
        assert result.success is False
        assert result.output == ""  # Empty string, not None
        assert result.error == "Test error"

    def test_format_result_with_both_result_and_error(self):
        """Test formatting with both result and error (error takes precedence)"""
        coordinator = BaseCoordinator()
        result = coordinator._format_result("task-3", False, result="Some output", error="Error occurred")

        assert result.error == "Error occurred"

    def test_validate_task_valid(self):
        """Test validating a valid task"""
        coordinator = BaseCoordinator()
        task = Task(task_id="test-task", name="Test Task", description="Test task", priority=TaskPriority.NORMAL)

        assert coordinator._validate_task(task) is True

    def test_validate_task_minimal(self):
        """Test validating minimal task"""
        coordinator = BaseCoordinator()
        task = Task(task_id="minimal", name="Minimal", description="Minimal task", priority=TaskPriority.LOW)

        assert coordinator._validate_task(task) is True


class TestBaseAgent:
    """Test BaseAgent class"""

    def test_init(self):
        """Test initialization"""
        agent = BaseAgent()
        assert agent is not None

    def test_can_execute_default_true(self):
        """Test default can_execute returns True"""
        agent = BaseAgent()
        task = Task(task_id="test", name="Test", description="Test task", priority=TaskPriority.NORMAL)

        assert agent.can_execute(task) is True

    def test_can_execute_with_task_context(self):
        """Test can_execute with different task contexts"""
        agent = BaseAgent()

        task1 = Task(task_id="1", name="Simple", description="Simple task", priority=TaskPriority.NORMAL)
        task2 = Task(
            task_id="2", name="Complex", description="Complex task", priority=TaskPriority.HIGH, context={"key": "value"}
        )

        assert agent.can_execute(task1) is True
        assert agent.can_execute(task2) is True

    def test_get_info_returns_dict(self):
        """Test get_info returns dictionary"""
        agent = BaseAgent()
        info = agent.get_info()

        assert isinstance(info, dict)
        # Base implementation returns empty dict
        assert info == {}


class TestBaseCoordinatorIntegration:
    """Test BaseCoordinator and BaseAgent integration"""

    def test_coordinator_and_agent_interaction(self):
        """Test basic interaction between coordinator and agent"""
        coordinator = BaseCoordinator()
        agent = BaseAgent()

        task = Task(task_id="integration-test", name="Integration", description="Test", priority=TaskPriority.NORMAL)
        assert coordinator._validate_task(task)
        assert agent.can_execute(task)

        result = coordinator._format_result("integration-test", True, "Success")
        assert result.success is True
