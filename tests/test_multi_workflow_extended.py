"""Extended multi-workflow coordinator tests for additional coverage."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from lingflow.workflow.multi_workflow import (
    WorkflowType,
    WorkflowPriority,
    WorkflowStatus,
    WorkflowResult,
    WorkflowConfig,
    BaseWorkflow,
    FastTrackWorkflow,
    StableTrackWorkflow,
    DevWorkflow,
    TestWorkflow,
    DocWorkflow,
    OptimizeWorkflow,
    ReviewWorkflow,
    DeployWorkflow,
    ExecutionStrategy,
    MultiWorkflowCoordinator,
)
from lingflow.common.models import Task, TaskPriority


def _make_task(tid="t1"):
    return Task(
        task_id=tid,
        name=f"Task {tid}",
        description="test task",
        priority=TaskPriority.NORMAL,
        agent_type="implementation",
    )


class TestEnums:
    def test_workflow_type_values(self):
        assert WorkflowType.FAST.value == "fast"
        assert WorkflowType.STABLE.value == "stable"
        assert WorkflowType.DEV.value == "dev"
        assert WorkflowType.TEST.value == "test"
        assert WorkflowType.DOCUMENTATION.value == "doc"
        assert WorkflowType.OPTIMIZATION.value == "optimize"
        assert WorkflowType.REVIEW.value == "review"
        assert WorkflowType.DEPLOY.value == "deploy"

    def test_workflow_priority(self):
        assert WorkflowPriority.CRITICAL.value == 0
        assert WorkflowPriority.HIGH.value == 1
        assert WorkflowPriority.NORMAL.value == 2
        assert WorkflowPriority.LOW.value == 3

    def test_workflow_status(self):
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.BLOCKED.value == "blocked"
        assert WorkflowStatus.SKIPPED.value == "skipped"


class TestWorkflowResult:
    def test_repr_success(self):
        r = WorkflowResult(workflow_id="w1", success=True, status=WorkflowStatus.COMPLETED)
        assert "✅" in repr(r)

    def test_repr_failure(self):
        r = WorkflowResult(workflow_id="w1", success=False, status=WorkflowStatus.FAILED)
        assert "❌" in repr(r)

    def test_defaults(self):
        r = WorkflowResult(workflow_id="w1", success=True, status=WorkflowStatus.COMPLETED)
        assert r.execution_time == 0.0
        assert r.output is None
        assert r.error is None
        assert r.tasks_results == {}


class TestWorkflowConfig:
    def test_defaults(self):
        c = WorkflowConfig()
        assert c.skip_steps == []
        assert c.required_steps == []
        assert c.auto_commit is False
        assert c.bypass_hooks is False
        assert c.parallel_execution is True


class TestBaseWorkflow:
    def test_init_defaults(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        assert wf.workflow_id == "wf1"
        assert wf.status == WorkflowStatus.PENDING
        assert wf.dependencies == []
        assert wf.tasks == []
        assert wf.coordinator is None
        assert wf.orchestrator is None

    def test_add_dependency(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.add_dependency("wf0")
        assert "wf0" in wf.dependencies
        wf.add_dependency("wf0")
        assert wf.dependencies.count("wf0") == 1

    def test_add_task_sets_context(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        t = _make_task()
        wf.add_task(t)
        assert t.context["workflow_id"] == "wf1"

    def test_add_task_preserves_existing_context(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        t = _make_task()
        t.context = {"existing": True}
        wf.add_task(t)
        assert t.context["existing"] is True
        assert t.context["workflow_id"] == "wf1"

    def test_validate_empty_id_fails(self):
        wf = BaseWorkflow("", WorkflowType.FAST)
        assert wf.validate() is False

    def test_validate_no_tasks_fails(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        assert wf.validate() is False

    def test_validate_task_missing_id_fails(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        t = Task(task_id="", name="", description="", priority=TaskPriority.NORMAL, agent_type="impl")
        wf.tasks.append(t)
        assert wf.validate() is False

    def test_validate_passes(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.add_task(_make_task())
        assert wf.validate() is True

    def test_check_dependencies_empty(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        assert wf._check_dependencies({}) is True

    def test_check_dependencies_not_satisfied(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.add_dependency("wf0")
        assert wf._check_dependencies({}) is False

    def test_check_dependencies_satisfied(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.add_dependency("wf0")
        ctx = {"workflow:wf0": WorkflowResult(workflow_id="wf0", success=True, status=WorkflowStatus.COMPLETED)}
        assert wf._check_dependencies(ctx) is True

    def test_check_dependencies_dep_failed(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.add_dependency("wf0")
        ctx = {"workflow:wf0": WorkflowResult(workflow_id="wf0", success=False, status=WorkflowStatus.FAILED)}
        assert wf._check_dependencies(ctx) is False

    def test_success_property(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        assert wf.success is False
        wf.status = WorkflowStatus.COMPLETED
        assert wf.success is True

    def test_can_promote_fast_to_stable(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.status = WorkflowStatus.COMPLETED
        assert wf.can_promote_to(WorkflowType.STABLE) is True

    def test_can_promote_fast_not_completed(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        assert wf.can_promote_to(WorkflowType.STABLE) is False

    def test_can_promote_dev_to_test(self):
        wf = BaseWorkflow("wf1", WorkflowType.DEV)
        wf.status = WorkflowStatus.COMPLETED
        assert wf.can_promote_to(WorkflowType.TEST) is True

    def test_can_promote_incompatible(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.status = WorkflowStatus.COMPLETED
        assert wf.can_promote_to(WorkflowType.DEPLOY) is False

    @pytest.mark.asyncio
    async def test_execute_validation_fails(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        result = await wf.execute({})
        assert result.status == WorkflowStatus.FAILED
        assert result.error == "Validation failed"

    @pytest.mark.asyncio
    async def test_execute_dependencies_not_met(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.add_task(_make_task())
        wf.add_dependency("missing")
        result = await wf.execute({})
        assert result.status == WorkflowStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_execute_no_orchestrator(self):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.add_task(_make_task())
        result = await wf.execute({})
        assert result.status == WorkflowStatus.COMPLETED
        assert result.tasks_results == {}


class TestWorkflowSubclasses:
    def test_fast_track_defaults(self):
        wf = FastTrackWorkflow("fast1")
        assert wf.workflow_type == WorkflowType.FAST
        assert wf.priority == WorkflowPriority.HIGH
        assert "full_test_suite" in wf.config.skip_steps
        assert wf.config.auto_commit is True

    def test_stable_track_defaults(self):
        wf = StableTrackWorkflow("stable1")
        assert wf.workflow_type == WorkflowType.STABLE
        assert wf.priority == WorkflowPriority.CRITICAL
        assert wf.config.skip_steps == []
        assert wf.config.auto_commit is False

    def test_dev_workflow(self):
        wf = DevWorkflow("dev1")
        assert wf.workflow_type == WorkflowType.DEV
        assert wf.priority == WorkflowPriority.CRITICAL

    def test_test_workflow(self):
        wf = TestWorkflow("test1")
        assert wf.workflow_type == WorkflowType.TEST
        assert wf.priority == WorkflowPriority.HIGH

    def test_doc_workflow(self):
        wf = DocWorkflow("doc1")
        assert wf.workflow_type == WorkflowType.DOCUMENTATION

    def test_optimize_workflow(self):
        wf = OptimizeWorkflow("opt1")
        assert wf.workflow_type == WorkflowType.OPTIMIZATION

    def test_review_workflow(self):
        wf = ReviewWorkflow("rev1")
        assert wf.workflow_type == WorkflowType.REVIEW
        assert wf.priority == WorkflowPriority.HIGH

    def test_deploy_workflow(self):
        wf = DeployWorkflow("dep1")
        assert wf.workflow_type == WorkflowType.DEPLOY
        assert wf.priority == WorkflowPriority.CRITICAL


class TestMultiWorkflowCoordinator:
    @pytest.fixture
    def coord(self):
        with patch("lingflow.workflow.multi_workflow.AgentCoordinator"):
            return MultiWorkflowCoordinator()

    def test_register_workflow(self, coord):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        coord.register_workflow(wf)
        assert "wf1" in coord.workflows

    def test_register_workflow_assigns_coordinator(self, coord):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        coord.register_workflow(wf)
        assert wf.coordinator is coord.coordinator

    def test_get_workflow(self, coord):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        coord.register_workflow(wf)
        assert coord.get_workflow("wf1") is wf
        assert coord.get_workflow("missing") is None

    def test_list_workflows(self, coord):
        coord.register_workflow(BaseWorkflow("wf1", WorkflowType.FAST))
        coord.register_workflow(BaseWorkflow("wf2", WorkflowType.STABLE))
        assert len(coord.list_workflows()) == 2
        assert len(coord.list_workflows(WorkflowType.FAST)) == 1

    def test_get_status(self, coord):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        coord.register_workflow(wf)
        status = coord.get_status()
        assert status["total_workflows"] == 1
        assert status["pending"] == 1

    def test_reset(self, coord):
        coord.register_workflow(BaseWorkflow("wf1", WorkflowType.FAST))
        coord.results = {"x": MagicMock()}
        coord.reset()
        assert len(coord.workflows) == 0
        assert len(coord.results) == 0

    def test_promote_workflow_not_found(self, coord):
        result = coord.promote_workflow("missing", WorkflowType.STABLE)
        assert result is None

    def test_promote_workflow_cannot_promote(self, coord):
        wf = BaseWorkflow("wf1", WorkflowType.FAST)
        wf.status = WorkflowStatus.PENDING
        coord.register_workflow(wf)
        result = coord.promote_workflow("wf1", WorkflowType.STABLE)
        assert result is None

    def test_promote_workflow_success(self, coord):
        wf = FastTrackWorkflow("fast1")
        wf.status = WorkflowStatus.COMPLETED
        coord.register_workflow(wf)
        promoted = coord.promote_workflow("fast1", WorkflowType.STABLE)
        assert promoted is not None
        assert promoted.workflow_type == WorkflowType.STABLE

    def test_promote_with_custom_id(self, coord):
        wf = FastTrackWorkflow("fast1")
        wf.status = WorkflowStatus.COMPLETED
        coord.register_workflow(wf)
        promoted = coord.promote_workflow("fast1", WorkflowType.STABLE, new_workflow_id="custom_id")
        assert promoted is not None
        assert promoted.workflow_id == "custom_id"

    def test_create_workflow_all_types(self, coord):
        for wt in WorkflowType:
            wf = coord._create_workflow(wt, f"test_{wt.value}")
            assert wf is not None

    @pytest.mark.asyncio
    async def test_execute_all_sequential(self, coord):
        wf1 = BaseWorkflow("wf1", WorkflowType.FAST)
        wf1.add_task(_make_task())
        coord.register_workflow(wf1)
        results = await coord.execute_all(strategy=ExecutionStrategy.SEQUENTIAL)
        assert "wf1" in results

    @pytest.mark.asyncio
    async def test_execute_all_parallel(self, coord):
        wf1 = BaseWorkflow("wf1", WorkflowType.FAST)
        wf1.add_task(_make_task())
        coord.register_workflow(wf1)
        results = await coord.execute_all(strategy=ExecutionStrategy.PARALLEL)
        assert "wf1" in results

    @pytest.mark.asyncio
    async def test_execute_all_hybrid(self, coord):
        wf1 = BaseWorkflow("wf1", WorkflowType.FAST)
        wf1.add_task(_make_task())
        coord.register_workflow(wf1)
        results = await coord.execute_all(strategy=ExecutionStrategy.HYBRID)
        assert "wf1" in results
