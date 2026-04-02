"""LingFlow 多工程流协调器

支持双工程流和多工程流系统的核心实现
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, field

from lingflow.common.models import Task, TaskResult
from lingflow.workflow.orchestrator import WorkflowOrchestrator
from lingflow.coordination.coordinator import AgentCoordinator

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """工程流类型"""
    FAST = "fast"              # 快速工程流
    STABLE = "stable"          # 稳定工程流
    DEV = "dev"                # 开发工程流
    TEST = "test"              # 测试工程流
    DOCUMENTATION = "doc"      # 文档工程流
    OPTIMIZATION = "optimize"  # 优化工程流
    REVIEW = "review"          # 审查工程流
    DEPLOY = "deploy"          # 部署工程流


class WorkflowPriority(Enum):
    """工程流优先级"""
    CRITICAL = 0   # 关键路径
    HIGH = 1       # 高优先级
    NORMAL = 2     # 正常优先级
    LOW = 3        # 低优先级


class WorkflowStatus(Enum):
    """工程流状态"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    BLOCKED = "blocked"       # 被阻塞
    SKIPPED = "skipped"       # 已跳过


@dataclass
class WorkflowResult:
    """工程流执行结果"""
    workflow_id: str
    success: bool
    status: WorkflowStatus
    execution_time: float = 0.0
    output: Any = None
    error: Optional[str] = None
    tasks_results: Dict[str, TaskResult] = field(default_factory=dict)

    def __repr__(self) -> str:
        status_symbol = "✅" if self.success else "❌"
        return f"{status_symbol} {self.workflow_id}: {self.status.value}"


@dataclass
class WorkflowConfig:
    """工程流配置"""
    skip_steps: List[str] = field(default_factory=list)
    required_steps: List[str] = field(default_factory=list)
    quality_thresholds: Dict[str, Any] = field(default_factory=dict)
    auto_commit: bool = False
    bypass_hooks: bool = False
    parallel_execution: bool = True


class BaseWorkflow:
    """工程流基类

    所有工程流的基础实现，提供通用功能
    """

    def __init__(
        self,
        workflow_id: str,
        workflow_type: WorkflowType,
        priority: WorkflowPriority = WorkflowPriority.NORMAL,
        coordinator: Optional[AgentCoordinator] = None,
        config: Optional[WorkflowConfig] = None
    ):
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.priority = priority
        self.config = config or WorkflowConfig()
        self.status = WorkflowStatus.PENDING
        self.dependencies: List[str] = []
        self.tasks: List[Task] = []

        # 如果没有提供协调器，创建新的
        self.coordinator = coordinator
        self.orchestrator = None
        if coordinator:
            self.orchestrator = WorkflowOrchestrator(coordinator)

    def add_dependency(self, workflow_id: str) -> None:
        """添加依赖的工程流"""
        if workflow_id not in self.dependencies:
            self.dependencies.append(workflow_id)
            logger.debug("Workflow %s now depends on %s", self.workflow_id, workflow_id)

    def add_task(self, task: Task) -> None:
        """添加任务到工程流"""
        task.context = task.context or {}
        task.context['workflow_id'] = self.workflow_id
        self.tasks.append(task)

    def validate(self) -> bool:
        """验证工程流配置

        检查：
        1. 必要的字段存在
        2. 任务列表有效
        3. 依赖的工程流已定义（在协调器级别检查）
        """
        if not self.workflow_id:
            logger.error("Workflow must have an ID")
            return False

        if not self.tasks:
            logger.warning("Workflow %s has no tasks", self.workflow_id)
            return False

        # 验证任务
        for task in self.tasks:
            if not task.task_id:
                logger.error("Task in %s missing task_id", self.workflow_id)
                return False

        logger.debug("Workflow %s validation passed", self.workflow_id)
        return True

    async def execute(self, context: Dict[str, Any]) -> WorkflowResult:
        """执行工程流

        Args:
            context: 执行上下文

        Returns:
            WorkflowResult: 执行结果
        """
        if not self.validate():
            return WorkflowResult(
                workflow_id=self.workflow_id,
                success=False,
                status=WorkflowStatus.FAILED,
                error="Validation failed"
            )

        # 检查依赖是否满足
        if not self._check_dependencies(context):
            logger.warning("Workflow %s dependencies not met", self.workflow_id)
            return WorkflowResult(
                workflow_id=self.workflow_id,
                success=False,
                status=WorkflowStatus.BLOCKED,
                error="Dependencies not satisfied"
            )

        self.status = WorkflowStatus.RUNNING
        start_time = asyncio.get_event_loop().time()

        try:
            # 执行任务
            if self.orchestrator:
                task_results = await self.orchestrator.execute_workflow(
                    self.tasks,
                    max_parallel=3 if self.config.parallel_execution else 1
                )
            else:
                # 如果没有orchestrator，直接执行（简化模式）
                task_results = {}

            execution_time = asyncio.get_event_loop().time() - start_time

            # 检查是否所有任务都成功
            all_success = all(
                result.success for result in task_results.values()
                if isinstance(result, TaskResult)
            )

            self.status = WorkflowStatus.COMPLETED if all_success else WorkflowStatus.FAILED

            return WorkflowResult(
                workflow_id=self.workflow_id,
                success=all_success,
                status=self.status,
                execution_time=execution_time,
                tasks_results=task_results
            )

        except (RuntimeError, ValueError, TypeError, KeyError, AttributeError, asyncio.TimeoutError) as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            self.status = WorkflowStatus.FAILED
            logger.error("Workflow %s failed: %s", self.workflow_id, e)

            return WorkflowResult(
                workflow_id=self.workflow_id,
                success=False,
                status=WorkflowStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )

    def _check_dependencies(self, context: Dict[str, Any]) -> bool:
        """检查依赖是否满足

        Args:
            context: 包含其他工程流执行结果的上下文

        Returns:
            bool: 所有依赖是否满足
        """
        if not self.dependencies:
            return True

        # 检查依赖的工程流是否都已完成
        for dep_id in self.dependencies:
            dep_result = context.get(f"workflow:{dep_id}")
            if not dep_result or not isinstance(dep_result, WorkflowResult):
                return False
            if dep_result.status != WorkflowStatus.COMPLETED:
                return False

        return True

    def can_promote_to(self, target_type: WorkflowType) -> bool:
        """检查是否可以提升到目标工程流类型

        Args:
            target_type: 目标工程流类型

        Returns:
            bool: 是否可以提升
        """
        # 快速流可以提升到稳定流
        if self.workflow_type == WorkflowType.FAST and target_type == WorkflowType.STABLE:
            return self.status == WorkflowStatus.COMPLETED and self.success

        # 开发流可以提升到测试流
        if self.workflow_type == WorkflowType.DEV and target_type == WorkflowType.TEST:
            return self.status == WorkflowStatus.COMPLETED and self.success

        return False

    @property
    def success(self) -> bool:
        """工程流是否成功完成"""
        return self.status == WorkflowStatus.COMPLETED


class FastTrackWorkflow(BaseWorkflow):
    """快速工程流

    特点：
    - 跳过耗时步骤
    - 较低的质量阈值
    - 自动提交
    """

    def __init__(
        self,
        workflow_id: str,
        coordinator: Optional[AgentCoordinator] = None,
        config: Optional[WorkflowConfig] = None
    ):
        if config is None:
            config = WorkflowConfig(
                skip_steps=["full_test_suite", "code_review", "documentation"],
                required_steps=["syntax_check", "unit_test"],
                quality_thresholds={
                    "test_coverage": 0.30,
                    "code_quality": 6.0
                },
                auto_commit=True,
                bypass_hooks=True,
                parallel_execution=True
            )

        super().__init__(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.FAST,
            priority=WorkflowPriority.HIGH,
            coordinator=coordinator,
            config=config
        )


class StableTrackWorkflow(BaseWorkflow):
    """稳定工程流

    特点：
    - 完整的质量检查
    - 严格的质量阈值
    - 需要审批
    """

    def __init__(
        self,
        workflow_id: str,
        coordinator: Optional[AgentCoordinator] = None,
        config: Optional[WorkflowConfig] = None
    ):
        if config is None:
            config = WorkflowConfig(
                skip_steps=[],
                required_steps=[
                    "syntax_check", "linting", "unit_test",
                    "integration_test", "e2e_test", "code_review",
                    "security_scan", "documentation"
                ],
                quality_thresholds={
                    "test_coverage": 0.70,
                    "code_quality": 9.0,
                    "security_scan": True
                },
                auto_commit=False,
                bypass_hooks=False,
                parallel_execution=True
            )

        super().__init__(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.STABLE,
            priority=WorkflowPriority.CRITICAL,
            coordinator=coordinator,
            config=config
        )


class DevWorkflow(BaseWorkflow):
    """开发工程流"""

    def __init__(
        self,
        workflow_id: str,
        coordinator: Optional[AgentCoordinator] = None,
        config: Optional[WorkflowConfig] = None
    ):
        if config is None:
            config = WorkflowConfig(
                quality_thresholds={"test_coverage": 0.50},
                parallel_execution=True
            )

        super().__init__(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.DEV,
            priority=WorkflowPriority.CRITICAL,
            coordinator=coordinator,
            config=config
        )


class TestWorkflow(BaseWorkflow):
    """测试工程流"""

    def __init__(
        self,
        workflow_id: str,
        coordinator: Optional[AgentCoordinator] = None,
        config: Optional[WorkflowConfig] = None
    ):
        if config is None:
            config = WorkflowConfig(
                quality_thresholds={"test_coverage": 0.70},
                parallel_execution=True
            )

        super().__init__(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.TEST,
            priority=WorkflowPriority.HIGH,
            coordinator=coordinator,
            config=config
        )


class DocWorkflow(BaseWorkflow):
    """文档工程流"""

    def __init__(
        self,
        workflow_id: str,
        coordinator: Optional[AgentCoordinator] = None,
        config: Optional[WorkflowConfig] = None
    ):
        super().__init__(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.DOCUMENTATION,
            priority=WorkflowPriority.NORMAL,
            coordinator=coordinator,
            config=config
        )


class OptimizeWorkflow(BaseWorkflow):
    """优化工程流"""

    def __init__(
        self,
        workflow_id: str,
        coordinator: Optional[AgentCoordinator] = None,
        config: Optional[WorkflowConfig] = None
    ):
        super().__init__(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.OPTIMIZATION,
            priority=WorkflowPriority.NORMAL,
            coordinator=coordinator,
            config=config
        )


class ReviewWorkflow(BaseWorkflow):
    """审查工程流"""

    def __init__(
        self,
        workflow_id: str,
        coordinator: Optional[AgentCoordinator] = None,
        config: Optional[WorkflowConfig] = None
    ):
        super().__init__(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.REVIEW,
            priority=WorkflowPriority.HIGH,
            coordinator=coordinator,
            config=config
        )


class DeployWorkflow(BaseWorkflow):
    """部署工程流"""

    def __init__(
        self,
        workflow_id: str,
        coordinator: Optional[AgentCoordinator] = None,
        config: Optional[WorkflowConfig] = None
    ):
        super().__init__(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.DEPLOY,
            priority=WorkflowPriority.CRITICAL,
            coordinator=coordinator,
            config=config
        )


class ExecutionStrategy(Enum):
    """执行策略"""
    PARALLEL = "parallel"      # 完全并行
    SEQUENTIAL = "sequential"  # 顺序执行
    HYBRID = "hybrid"          # 混合模式


class MultiWorkflowCoordinator:
    """多工程流协调器

    管理多条工程流的并行执行、依赖关系和资源调度
    """

    def __init__(
        self,
        max_parallel_workflows: int = 3,
        coordinator: Optional[AgentCoordinator] = None
    ):
        self.workflows: Dict[str, BaseWorkflow] = {}
        self.max_parallel = max_parallel_workflows
        self.coordinator = coordinator or AgentCoordinator()
        self.results: Dict[str, WorkflowResult] = {}

    def register_workflow(self, workflow: BaseWorkflow) -> None:
        """注册工程流

        Args:
            workflow: 要注册的工程流
        """
        # 如果工程流没有协调器，使用共享的
        if workflow.coordinator is None:
            workflow.coordinator = self.coordinator
            workflow.orchestrator = WorkflowOrchestrator(self.coordinator)

        self.workflows[workflow.workflow_id] = workflow
        logger.info("Registered workflow: %s (%s)", workflow.workflow_id, workflow.workflow_type.value)

    def get_workflow(self, workflow_id: str) -> Optional[BaseWorkflow]:
        """获取工程流"""
        return self.workflows.get(workflow_id)

    def list_workflows(self, type_filter: Optional[WorkflowType] = None) -> List[BaseWorkflow]:
        """列出工程流

        Args:
            type_filter: 可选的类型过滤器

        Returns:
            工程流列表
        """
        workflows = list(self.workflows.values())
        if type_filter:
            workflows = [wf for wf in workflows if wf.workflow_type == type_filter]
        return workflows

    async def execute_all(
        self,
        strategy: ExecutionStrategy = ExecutionStrategy.PARALLEL,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, WorkflowResult]:
        """执行所有工程流

        Args:
            strategy: 执行策略
            context: 执行上下文

        Returns:
            工作流ID到结果的映射
        """
        context = context or {}
        logger.info("Executing %d workflows with strategy: %s", len(self.workflows), strategy.value)

        if strategy == ExecutionStrategy.PARALLEL:
            return await self._execute_parallel(context)
        elif strategy == ExecutionStrategy.SEQUENTIAL:
            return await self._execute_sequential(context)
        else:  # HYBRID
            return await self._execute_hybrid(context)

    async def _execute_parallel(self, context: Dict[str, Any]) -> Dict[str, WorkflowResult]:
        """并行执行策略"""
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def execute_with_limit(workflow: BaseWorkflow, ctx: Dict[str, Any]):
            async with semaphore:
                result = await workflow.execute(ctx)
                # 更新上下文，供依赖使用
                ctx[f"workflow:{workflow.workflow_id}"] = result
                return result

        tasks = [
            execute_with_limit(wf, context.copy())
            for wf in self.workflows.values()
        ]

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for result in results_list:
            if isinstance(result, Exception):
                logger.error("Workflow execution exception: %s", result)
                continue
            if isinstance(result, WorkflowResult):
                self.results[result.workflow_id] = result

        return self.results

    async def _execute_sequential(self, context: Dict[str, Any]) -> Dict[str, WorkflowResult]:
        """顺序执行策略（按依赖顺序）"""
        executed = set()
        results = {}

        # 拓扑排序执行
        while len(executed) < len(self.workflows):
            # 找出所有依赖已满足的工程流
            ready = [
                wf for wf in self.workflows.values()
                if wf.workflow_id not in executed and
                all(dep in executed for dep in wf.dependencies)
            ]

            if not ready:
                logger.warning("No ready workflows found - possible circular dependency")
                break

            # 执行准备好的工程流
            for wf in ready:
                result = await wf.execute(context)
                results[wf.workflow_id] = result
                context[f"workflow:{wf.workflow_id}"] = result
                executed.add(wf.workflow_id)

        self.results.update(results)
        return results

    async def _execute_hybrid(self, context: Dict[str, Any]) -> Dict[str, WorkflowResult]:
        """混合执行策略：关键路径优先"""
        # 1. 识别关键路径（CRITICAL优先级 + 无依赖）
        critical_workflows = [
            wf for wf in self.workflows.values()
            if wf.priority == WorkflowPriority.CRITICAL
            and not wf.dependencies
        ]

        # 2. 并行执行关键路径
        logger.info("Executing %d critical workflows", len(critical_workflows))
        critical_results = await self._execute_workflows(critical_workflows, context)

        # 3. 执行依赖已满足的其他工程流
        remaining = self._get_ready_workflows(context)
        logger.info("Executing %d remaining workflows", len(remaining))
        remaining_results = await self._execute_workflows(remaining, context)

        return {**critical_results, **remaining_results}

    async def _execute_workflows(
        self,
        workflows: List[BaseWorkflow],
        context: Dict[str, Any]
    ) -> Dict[str, WorkflowResult]:
        """执行一组工程流"""
        results = {}
        for wf in workflows:
            result = await wf.execute(context)
            results[wf.workflow_id] = result
            context[f"workflow:{wf.workflow_id}"] = result

        return results

    def _get_ready_workflows(self, context: Dict[str, Any]) -> List[BaseWorkflow]:
        """获取依赖已满足的工程流"""
        ready = []
        for wf in self.workflows.values():
            if wf.status != WorkflowStatus.PENDING:
                continue

            # 检查依赖
            deps_met = all(
                context.get(f"workflow:{dep}", WorkflowStatus(
                    dep, "", WorkflowStatus.PENDING
                )).status == WorkflowStatus.COMPLETED
                for dep in wf.dependencies
            )

            if deps_met:
                ready.append(wf)

        # 按优先级排序
        ready.sort(key=lambda w: w.priority.value)
        return ready

    def promote_workflow(
        self,
        from_workflow_id: str,
        to_type: WorkflowType,
        new_workflow_id: Optional[str] = None
    ) -> Optional[BaseWorkflow]:
        """将一个工程流提升到另一种类型

        Args:
            from_workflow_id: 源工程流ID
            to_type: 目标类型
            new_workflow_id: 新工程流ID（可选）

        Returns:
            新创建的工程流，如果不可以提升则返回None
        """
        from_wf = self.get_workflow(from_workflow_id)
        if not from_wf:
            logger.error("Source workflow not found: %s", from_workflow_id)
            return None

        if not from_wf.can_promote_to(to_type):
            logger.warning("Cannot promote %s to %s", from_workflow_id, to_type.value)
            return None

        # 创建新工程流
        workflow_id = new_workflow_id or f"{from_workflow_id}_promoted"
        promoted_wf = self._create_workflow(to_type, workflow_id)

        # 复制任务
        promoted_wf.tasks = from_wf.tasks.copy()

        self.register_workflow(promoted_wf)
        logger.info("Promoted %s to %s (%s)", from_workflow_id, workflow_id, to_type.value)

        return promoted_wf

    def _create_workflow(self, workflow_type: WorkflowType, workflow_id: str) -> BaseWorkflow:
        """工厂方法：创建指定类型的工程流"""
        workflow_classes = {
            WorkflowType.FAST: FastTrackWorkflow,
            WorkflowType.STABLE: StableTrackWorkflow,
            WorkflowType.DEV: DevWorkflow,
            WorkflowType.TEST: TestWorkflow,
            WorkflowType.DOCUMENTATION: DocWorkflow,
            WorkflowType.OPTIMIZATION: OptimizeWorkflow,
            WorkflowType.REVIEW: ReviewWorkflow,
            WorkflowType.DEPLOY: DeployWorkflow,
        }

        workflow_class = workflow_classes.get(workflow_type, BaseWorkflow)
        return workflow_class(workflow_id=workflow_id)

    def get_status(self) -> Dict[str, Any]:
        """获取所有工程流的状态"""
        return {
            "total_workflows": len(self.workflows),
            "completed": sum(
                1 for wf in self.workflows.values()
                if wf.status == WorkflowStatus.COMPLETED
            ),
            "failed": sum(
                1 for wf in self.workflows.values()
                if wf.status == WorkflowStatus.FAILED
            ),
            "running": sum(
                1 for wf in self.workflows.values()
                if wf.status == WorkflowStatus.RUNNING
            ),
            "pending": sum(
                1 for wf in self.workflows.values()
                if wf.status == WorkflowStatus.PENDING
            ),
            "workflows": {
                wf_id: {
                    "type": wf.workflow_type.value,
                    "status": wf.status.value,
                    "priority": wf.priority.value
                }
                for wf_id, wf in self.workflows.items()
            }
        }

    def reset(self) -> None:
        """重置所有状态"""
        self.workflows.clear()
        self.results.clear()
        logger.info("Reset multi-workflow coordinator")
