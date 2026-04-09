import os
import tempfile
from unittest.mock import MagicMock

import pytest

from lingflow.common.models import Task, TaskPriority, TaskResult
from lingflow.workflow.orchestrator import WorkflowOrchestrator


class TestLoadWorkflowFromYaml:
    def test_load_valid_yaml(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
tasks:
  - id: task1
    skill: test_skill
    description: Test task
    priority: high
    depends_on: []
""")
            f.flush()
            tasks = orch.load_workflow_from_yaml(f.name)
        os.unlink(f.name)
        assert len(tasks) == 1
        assert tasks[0].task_id == "task1"
        assert tasks[0].priority == TaskPriority.HIGH

    def test_load_yaml_with_stages(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
stages:
  - name: stage1
    skill: skill1
""")
            f.flush()
            tasks = orch.load_workflow_from_yaml(f.name)
        os.unlink(f.name)
        assert len(tasks) == 1

    def test_load_missing_file(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        with pytest.raises(FileNotFoundError):
            orch.load_workflow_from_yaml("/nonexistent/file.yaml")

    def test_load_empty_yaml(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            with pytest.raises(ValueError):
                orch.load_workflow_from_yaml(f.name)
        os.unlink(f.name)

    def test_load_yaml_no_tasks(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("tasks: []\n")
            f.flush()
            tasks = orch.load_workflow_from_yaml(f.name)
        os.unlink(f.name)
        assert tasks == []

    def test_load_yaml_with_dependencies(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
tasks:
  - id: t1
    skill: s1
  - id: t2
    skill: s2
    dependencies: [t1]
""")
            f.flush()
            tasks = orch.load_workflow_from_yaml(f.name)
        os.unlink(f.name)
        assert tasks[1].dependencies == ["t1"]


class TestGetReadyTasks:
    def test_ready_tasks_sorted_by_priority(self):
        coordinator = MagicMock()
        coordinator.completed_tasks = set()
        coordinator.failed_tasks = set()
        orch = WorkflowOrchestrator(coordinator)

        tasks = [
            Task(task_id="t1", name="low", description="", agent_type="general", priority=TaskPriority.LOW, dependencies=[]),
            Task(task_id="t2", name="high", description="", agent_type="general", priority=TaskPriority.HIGH, dependencies=[]),
        ]
        ready = orch._get_ready_tasks(tasks)
        assert len(ready) == 2
        assert ready[0].priority == TaskPriority.LOW  # reverse=True sorts by value desc, LOW=3 > HIGH=1

    def test_skip_completed_tasks(self):
        coordinator = MagicMock()
        coordinator.completed_tasks = {"t1"}
        coordinator.failed_tasks = set()
        orch = WorkflowOrchestrator(coordinator)

        tasks = [
            Task(
                task_id="t1", name="done", description="", agent_type="general", priority=TaskPriority.NORMAL, dependencies=[]
            ),
            Task(
                task_id="t2",
                name="pending",
                description="",
                agent_type="general",
                priority=TaskPriority.NORMAL,
                dependencies=[],
            ),
        ]
        ready = orch._get_ready_tasks(tasks)
        assert len(ready) == 1
        assert ready[0].task_id == "t2"

    def test_dependency_not_met(self):
        coordinator = MagicMock()
        coordinator.completed_tasks = set()
        coordinator.failed_tasks = set()
        orch = WorkflowOrchestrator(coordinator)

        tasks = [
            Task(
                task_id="t1", name="first", description="", agent_type="general", priority=TaskPriority.NORMAL, dependencies=[]
            ),
            Task(
                task_id="t2",
                name="second",
                description="",
                agent_type="general",
                priority=TaskPriority.NORMAL,
                dependencies=["t1"],
            ),
        ]
        ready = orch._get_ready_tasks(tasks)
        assert len(ready) == 1
        assert ready[0].task_id == "t1"


class TestOrchestratorExecute:
    def test_execute_empty_tasks(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        result = orch.execute([])
        assert result == {}

    def test_get_degradation_report_none(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        assert orch.get_degradation_report() is None


class TestCheckDegradation:
    def test_check_degradation_basic(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        batch = {
            "t1": TaskResult(task_id="t1", success=True, output="ok"),
            "t2": TaskResult(task_id="t2", success=False, error="fail"),
        }
        orch._check_degradation(batch)
        assert orch.get_degradation_report() is not None

    def test_check_degradation_accumulates_messages(self):
        coordinator = MagicMock()
        orch = WorkflowOrchestrator(coordinator)
        batch1 = {"t1": TaskResult(task_id="t1", success=True, output="first")}
        batch2 = {"t2": TaskResult(task_id="t2", success=True, output="second")}
        orch._check_degradation(batch1)
        orch._check_degradation(batch2)
        assert len(orch._workflow_messages) == 2
