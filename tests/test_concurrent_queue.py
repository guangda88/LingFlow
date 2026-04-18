"""Tests for concurrent read/write task queue in AgentCoordinator.

Validates the two-phase execution model:
- Read-only tasks (is_read_only=True) run concurrently
- Write tasks (is_read_only=False) run sequentially, ordered by priority
- Write tasks wait for all read tasks to complete
"""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest

from lingflow.common.models import Task, TaskPriority, TaskResult
from lingflow.coordination.coordinator import AgentCoordinator


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


def _make_task(task_id: str, is_read_only: bool = True, priority: TaskPriority = TaskPriority.NORMAL) -> Task:
    return Task(
        task_id=task_id,
        name=f"Task {task_id}",
        description=f"Test task {task_id}",
        priority=priority,
        agent_type="implementation",
        is_read_only=is_read_only,
    )


class TestReadWriteSplit:
    """Test that read and write tasks are correctly separated."""

    @pytest.mark.asyncio
    async def test_read_only_tasks_run_concurrently(self):
        """Read tasks should execute in parallel (up to max_parallel)."""
        coordinator = AgentCoordinator()
        timestamps = []

        async def track_execute(task, context):
            timestamps.append((task.task_id, time.monotonic()))
            await asyncio.sleep(0.05)
            return TaskResult(task_id=task.task_id, success=True, output="ok")

        tasks = [_make_task(f"read-{i}", is_read_only=True) for i in range(3)]

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_find.return_value.execute_task = track_execute
            results = await coordinator.execute_tasks_parallel(tasks, max_parallel=3)

        assert len(results) == 3
        for t in tasks:
            assert results[t.task_id].success is True

    @pytest.mark.asyncio
    async def test_write_tasks_run_sequentially(self):
        """Write tasks should execute one at a time, never overlapping."""
        coordinator = AgentCoordinator()
        active_count = 0
        max_active = 0
        lock = asyncio.Lock()

        async def track_concurrency(task, context):
            nonlocal active_count, max_active
            async with lock:
                active_count += 1
                max_active = max(max_active, active_count)
            await asyncio.sleep(0.05)
            async with lock:
                active_count -= 1
            return TaskResult(task_id=task.task_id, success=True, output="ok")

        tasks = [_make_task(f"write-{i}", is_read_only=False) for i in range(3)]

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_find.return_value.execute_task = track_concurrency
            results = await coordinator.execute_tasks_parallel(tasks, max_parallel=4)

        assert max_active <= 1, f"Write tasks overlapped: max_active={max_active}"
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_default_is_read_only(self):
        """Tasks without explicit is_read_only default to True (read-only)."""
        task = Task(
            task_id="default-readonly",
            name="Default",
            description="desc",
            priority=TaskPriority.NORMAL,
        )
        assert task.is_read_only is True

    @pytest.mark.asyncio
    async def test_empty_task_list(self):
        """Empty task list should return empty dict."""
        coordinator = AgentCoordinator()
        results = await coordinator.execute_tasks_parallel([], max_parallel=2)
        assert results == {}


class TestWritePriorityOrdering:
    """Test that write tasks execute in priority order."""

    @pytest.mark.asyncio
    async def test_write_tasks_ordered_by_priority(self):
        """Write tasks should execute in priority order (CRITICAL first)."""
        coordinator = AgentCoordinator()
        execution_order = []

        async def track_order(task, context):
            execution_order.append(task.task_id)
            return TaskResult(task_id=task.task_id, success=True, output="ok")

        tasks = [
            _make_task("low", is_read_only=False, priority=TaskPriority.LOW),
            _make_task("critical", is_read_only=False, priority=TaskPriority.CRITICAL),
            _make_task("normal", is_read_only=False, priority=TaskPriority.NORMAL),
        ]

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_find.return_value.execute_task = track_order
            results = await coordinator.execute_tasks_parallel(tasks, max_parallel=1)

        assert execution_order == ["critical", "normal", "low"]


class TestMixedReadWrite:
    """Test mixed read and write task scenarios."""

    @pytest.mark.asyncio
    async def test_reads_before_writes(self):
        """All read tasks should complete before write tasks start."""
        coordinator = AgentCoordinator()
        phases = []

        async def track_phase(task, context):
            phase = "read" if task.is_read_only else "write"
            phases.append((task.task_id, phase))
            return TaskResult(task_id=task.task_id, success=True, output="ok")

        tasks = [
            _make_task("write-1", is_read_only=False),
            _make_task("read-1", is_read_only=True),
            _make_task("read-2", is_read_only=True),
            _make_task("write-2", is_read_only=False),
        ]

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_find.return_value.execute_task = track_phase
            results = await coordinator.execute_tasks_parallel(tasks, max_parallel=2)

        assert len(results) == 4
        read_indices = [i for i, (_, p) in enumerate(phases) if p == "read"]
        write_indices = [i for i, (_, p) in enumerate(phases) if p == "write"]
        assert all(idx < min(write_indices) for idx in read_indices)

    @pytest.mark.asyncio
    async def test_write_failure_does_not_block_others(self):
        """A failed write task should not prevent subsequent writes."""
        coordinator = AgentCoordinator()

        async def selective_fail(task, context):
            if task.task_id == "write-fail":
                return TaskResult(task_id=task.task_id, success=False, error="boom")
            return TaskResult(task_id=task.task_id, success=True, output="ok")

        tasks = [
            _make_task("write-fail", is_read_only=False),
            _make_task("write-ok", is_read_only=False),
        ]

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_find.return_value.execute_task = selective_fail
            results = await coordinator.execute_tasks_parallel(tasks)

        assert results["write-fail"].success is False
        assert results["write-ok"].success is True


class TestStopInterruptsWrites:
    """Test that stop command interrupts remaining write tasks."""

    @pytest.mark.asyncio
    async def test_stop_skips_remaining_writes(self):
        """If stop is requested during a write, remaining writes are skipped."""
        coordinator = AgentCoordinator()

        async def trigger_stop_on_first(task, context):
            if task.task_id == "w1":
                coordinator._stop_requested = True
                coordinator._stop_reason = "test stop"
            return TaskResult(task_id=task.task_id, success=True, output="ok")

        tasks = [_make_task(f"w{i}", is_read_only=False) for i in range(1, 4)]

        with patch.object(coordinator, "_find_agent_for_task", return_value=MagicMock()) as mock_find:
            mock_find.return_value.execute_task = trigger_stop_on_first
            results = await coordinator.execute_tasks_parallel(tasks)

        assert results["w1"].success is True
        assert results["w2"].success is False
        assert "Stopped by user" in results["w2"].error

        coordinator.clear_stop()
