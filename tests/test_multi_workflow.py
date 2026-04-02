"""Multi-workflow coordinator tests"""

import pytest

from lingflow.common.models import Task, TaskPriority
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
        assert WorkflowPriority.CRITICAL.value < WorkflowPriority.HIGH.value
        assert WorkflowPriority.HIGH.value < WorkflowPriority.NORMAL.value
        assert WorkflowPriority.NORMAL.value < WorkflowPriority.LOW.value

    def test_workflow_status(self):
        assert WorkflowStatus.PENDING.value == "pending"
        assert WorkflowStatus.RUNNING.value == "running"
        assert WorkflowStatus.COMPLETED.value == "completed"
        assert WorkflowStatus.FAILED.value == "failed"
        assert WorkflowStatus.BLOCKED.value == "blocked"
        assert WorkflowStatus.SKIPPED.value == "skipped"


class TestWorkflowResult:
    def test_defaults(self):
        r = WorkflowResult(workflow_id="w1", success=True, status=WorkflowStatus.COMPLETED)
        assert r.execution_time == 0.0
        assert r.output is None
        assert r.error is None
        assert r.tasks_results == {}

    def test_repr_success(self):
        r = WorkflowResult(workflow_id="w1", success=True, status=WorkflowStatus.COMPLETED)
        assert "w1" in repr(r)
        assert "completed" in repr(r)

    def test_repr_failure(self):
        r = WorkflowResult(workflow_id="w2", success=False, status=WorkflowStatus.FAILED)
        assert "w2" in repr(r)


class TestWorkflowConfig:
    def test_defaults(self):
        cfg = WorkflowConfig()
        assert cfg.skip_steps == []
        assert cfg.required_steps == []
        assert cfg.quality_thresholds == {}
        assert cfg.auto_commit is False
        assert cfg.bypass_hooks is False
        assert cfg.parallel_execution is True


class TestBaseWorkflow:
    def test_init(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        assert wf.workflow_id == "w1"
        assert wf.workflow_type == WorkflowType.FAST
        assert wf.priority == WorkflowPriority.NORMAL
        assert wf.status == WorkflowStatus.PENDING
        assert wf.tasks == []
        assert wf.dependencies == []
        assert wf.coordinator is None
        assert wf.orchestrator is None

    def test_add_dependency(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        wf.add_dependency("w0")
        assert "w0" in wf.dependencies
        wf.add_dependency("w0")
        assert len(wf.dependencies) == 1

    def test_add_task(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        task = Task(task_id="t1", name="n", description="d", priority=TaskPriority.NORMAL)
        wf.add_task(task)
        assert len(wf.tasks) == 1
        assert wf.tasks[0].context.get("workflow_id") == "w1"

    def test_validate_empty_id(self):
        wf = BaseWorkflow("", WorkflowType.FAST)
        assert wf.validate() is False

    def test_validate_no_tasks(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        assert wf.validate() is False

    def test_validate_task_no_id(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        wf.tasks.append(Task(task_id="", name="n", description="d", priority=TaskPriority.NORMAL))
        assert wf.validate() is False

    def test_validate_ok(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        wf.tasks.append(Task(task_id="t1", name="n", description="d", priority=TaskPriority.NORMAL))
        assert wf.validate() is True

    def test_check_deps_none(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        assert wf._check_dependencies({}) is True

    def test_check_deps_unmet(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        wf.add_dependency("w0")
        assert wf._check_dependencies({}) is False

    def test_check_deps_met(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        wf.add_dependency("w0")
        ctx = {"workflow:w0": WorkflowResult("w0", True, WorkflowStatus.COMPLETED)}
        assert wf._check_dependencies(ctx) is True

    def test_success_property(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        assert wf.success is False
        wf.status = WorkflowStatus.COMPLETED
        assert wf.success is True

    def test_can_promote_fast_to_stable(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        assert wf.can_promote_to(WorkflowType.STABLE) is False
        wf.status = WorkflowStatus.COMPLETED
        assert wf.can_promote_to(WorkflowType.STABLE) is True

    def test_can_promote_dev_to_test(self):
        wf = BaseWorkflow("w1", WorkflowType.DEV)
        assert wf.can_promote_to(WorkflowType.TEST) is False
        wf.status = WorkflowStatus.COMPLETED
        assert wf.can_promote_to(WorkflowType.TEST) is True

    def test_can_promote_invalid(self):
        wf = BaseWorkflow("w1", WorkflowType.DEPLOY)
        assert wf.can_promote_to(WorkflowType.DOCUMENTATION) is False

    @pytest.mark.asyncio
    async def test_execute_validation_fails(self):
        wf = BaseWorkflow("", WorkflowType.FAST)
        result = await wf.execute({})
        assert result.success is False
        assert result.status == WorkflowStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_deps_not_met(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        wf.add_dependency("w0")
        wf.tasks.append(Task(task_id="t1", name="n", description="d", priority=TaskPriority.NORMAL))
        result = await wf.execute({})
        assert result.success is False
        assert result.status == WorkflowStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_execute_no_orchestrator(self):
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        wf.tasks.append(Task(task_id="t1", name="n", description="d", priority=TaskPriority.NORMAL))
        result = await wf.execute({})
        assert result.success is True
        assert result.status == WorkflowStatus.COMPLETED


class TestWorkflowSubclasses:
    def test_fast_track(self):
        wf = FastTrackWorkflow("f1")
        assert wf.workflow_type == WorkflowType.FAST
        assert wf.priority == WorkflowPriority.HIGH
        assert "full_test_suite" in wf.config.skip_steps

    def test_stable_track(self):
        wf = StableTrackWorkflow("s1")
        assert wf.workflow_type == WorkflowType.STABLE
        assert wf.priority == WorkflowPriority.CRITICAL
        assert "code_review" in wf.config.required_steps

    def test_dev_workflow(self):
        wf = DevWorkflow("d1")
        assert wf.workflow_type == WorkflowType.DEV
        assert wf.priority == WorkflowPriority.CRITICAL

    def test_test_workflow(self):
        wf = TestWorkflow("t1")
        assert wf.workflow_type == WorkflowType.TEST
        assert wf.priority == WorkflowPriority.HIGH

    def test_doc_workflow(self):
        wf = DocWorkflow("doc1")
        assert wf.workflow_type == WorkflowType.DOCUMENTATION
        assert wf.priority == WorkflowPriority.NORMAL

    def test_optimize_workflow(self):
        wf = OptimizeWorkflow("opt1")
        assert wf.workflow_type == WorkflowType.OPTIMIZATION

    def test_review_workflow(self):
        wf = ReviewWorkflow("rev1")
        assert wf.workflow_type == WorkflowType.REVIEW

    def test_deploy_workflow(self):
        wf = DeployWorkflow("dep1")
        assert wf.workflow_type == WorkflowType.DEPLOY
        assert wf.priority == WorkflowPriority.CRITICAL


class TestMultiWorkflowCoordinator:
    def test_register_and_get(self):
        coord = MultiWorkflowCoordinator()
        wf = BaseWorkflow("w1", WorkflowType.FAST)
        coord.register_workflow(wf)
        assert coord.get_workflow("w1") is wf
        assert coord.get_workflow("missing") is None

    def test_list_workflows(self):
        coord = MultiWorkflowCoordinator()
        coord.register_workflow(FastTrackWorkflow("f1"))
        coord.register_workflow(StableTrackWorkflow("s1"))
        assert len(coord.list_workflows()) == 2
        assert len(coord.list_workflows(WorkflowType.FAST)) == 1

    def test_get_status(self):
        coord = MultiWorkflowCoordinator()
        coord.register_workflow(FastTrackWorkflow("f1"))
        status = coord.get_status()
        assert status["total_workflows"] == 1
        assert status["pending"] == 1

    def test_reset(self):
        coord = MultiWorkflowCoordinator()
        coord.register_workflow(FastTrackWorkflow("f1"))
        coord.reset()
        assert len(coord.workflows) == 0

    def test_promote_not_found(self):
        coord = MultiWorkflowCoordinator()
        assert coord.promote_workflow("missing", WorkflowType.STABLE) is None

    def test_promote_cannot(self):
        coord = MultiWorkflowCoordinator()
        wf = FastTrackWorkflow("f1")
        coord.register_workflow(wf)
        assert coord.promote_workflow("f1", WorkflowType.DEPLOY) is None

    @pytest.mark.asyncio
    async def test_execute_parallel(self):
        coord = MultiWorkflowCoordinator()
        wf1 = FastTrackWorkflow("f1")
        wf1.tasks.append(Task(task_id="t1", name="n", description="d", priority=TaskPriority.NORMAL))
        coord.register_workflow(wf1)
        results = await coord.execute_all(strategy=ExecutionStrategy.PARALLEL)
        assert "f1" in results

    @pytest.mark.asyncio
    async def test_execute_sequential(self):
        coord = MultiWorkflowCoordinator()
        wf1 = FastTrackWorkflow("f1")
        wf1.tasks.append(Task(task_id="t1", name="n", description="d", priority=TaskPriority.NORMAL))
        coord.register_workflow(wf1)
        results = await coord.execute_all(strategy=ExecutionStrategy.SEQUENTIAL)
        assert "f1" in results

    @pytest.mark.asyncio
    async def test_execute_hybrid(self):
        coord = MultiWorkflowCoordinator()
        wf1 = FastTrackWorkflow("f1")
        wf1.tasks.append(Task(task_id="t1", name="n", description="d", priority=TaskPriority.NORMAL))
        coord.register_workflow(wf1)
        results = await coord.execute_all(strategy=ExecutionStrategy.HYBRID)
        assert "f1" in results

    def test_create_workflow_factory(self):
        coord = MultiWorkflowCoordinator()
        for wt in WorkflowType:
            wf = coord._create_workflow(wt, "test")
            assert wf is not None

    def test_promote_success(self):
        coord = MultiWorkflowCoordinator()
        wf = FastTrackWorkflow("f1")
        wf.status = WorkflowStatus.COMPLETED
        wf.tasks.append(Task(task_id="t1", name="n", description="d", priority=TaskPriority.NORMAL))
        coord.register_workflow(wf)
        promoted = coord.promote_workflow("f1", WorkflowType.STABLE)
        assert promoted is not None
        assert promoted.workflow_type == WorkflowType.STABLE
