"""LingFlow 工作流编排器"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from lingflow.common.config import get_config
from lingflow.common.models import Task, TaskPriority, TaskResult
from lingflow.coordination.coordinator import AgentCoordinator

# 常量定义（消除魔法值）
MAX_SCHEDULING_ITERATIONS = 100  # 最大调度迭代次数
SCHEDULING_DELAY = 0.01  # 调度间隔（秒）
DEFAULT_MAX_PARALLEL = 2  # 默认最大并行数
DEGRADATION_CHECK_INTERVAL = 3  # 每完成 N 个任务检查一次退化

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Workflow orchestrator for managing task dependencies and parallel execution.

    This orchestrator handles task scheduling based on dependencies,
    enabling parallel execution of independent tasks while respecting
    dependency constraints.
    """

    def __init__(self, coordinator: AgentCoordinator) -> None:
        """Initialize the workflow orchestrator.

        Args:
            coordinator: The agent coordinator to use for task execution
        """
        self.coordinator = coordinator
        self._degradation_detector = None
        self._workflow_messages: List[Dict[str, str]] = []
        self._degradation_report: Optional[Dict[str, Any]] = None

    def load_workflow_from_yaml(self, filepath: str) -> List[Task]:
        """从 YAML 文件加载工作流任务

        Args:
            filepath: YAML 文件路径

        Returns:
            任务列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: YAML 格式错误
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Workflow file not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            workflow_data = yaml.safe_load(f)

        if not workflow_data:
            raise ValueError(f"Empty workflow file: {filepath}")

        # 兼容不同字段名
        tasks_data = workflow_data.get("tasks") or workflow_data.get("stages", [])

        if not tasks_data:
            logger.warning("No tasks found in workflow: %s", filepath)
            return []

        tasks = []
        for task_def in tasks_data:
            task_id = task_def.get("id", task_def.get("name"))
            if not task_id:
                logger.warning("Task missing id/name: %s", task_def)
                continue

            # 解析优先级
            priority_str = task_def.get("priority", task_def.get("metadata", {}).get("priority", "normal"))
            priority_map = {"high": TaskPriority.HIGH, "normal": TaskPriority.NORMAL, "low": TaskPriority.LOW}
            priority = priority_map.get(priority_str.lower(), TaskPriority.NORMAL)

            # 解析依赖
            dependencies = task_def.get("depends_on", task_def.get("dependencies", []))

            # 创建任务
            # 创建任务
            task_params = dict(task_def.get("params", {}))
            mcp_route = task_def.get("_mcp_route")
            if mcp_route:
                task_params["_mcp_route"] = mcp_route

            task = Task(
                task_id=task_id,
                name=task_def.get("skill", task_id),
                description=task_def.get("description", ""),
                agent_type=task_def.get("skill", task_def.get("agent_type", "implementation")),
                context=task_params,
                priority=priority,
                dependencies=dependencies,
            )
            tasks.append(task)

        logger.info("Loaded %d tasks from %s", len(tasks), filepath)
        return tasks

    async def execute_workflow(self, tasks: List[Task], max_parallel: int = DEFAULT_MAX_PARALLEL) -> Dict[str, TaskResult]:
        """Execute a workflow with task dependencies.

        Tasks are scheduled based on their dependencies. Independent tasks
        can be executed in parallel, while dependent tasks wait for their
        prerequisites to complete.

        Args:
            tasks: List of tasks to execute
            max_parallel: Maximum number of parallel executions

        Returns:
            Dictionary mapping task IDs to their results

        Raises:
            RuntimeError: If workflow execution fails
        """
        if not tasks:
            logger.warning("No tasks provided to execute_workflow")
            return {}

        logger.info("Starting workflow execution with %d tasks, max_parallel=%d", len(tasks), max_parallel)
        results = {}

        # 从配置获取最大并行数
        if max_parallel is None:
            max_parallel = get_config("workflow.max_parallel", 2)

        # 初始化任务状态
        for task in tasks:
            try:
                self.coordinator.submit_task(task)
            except (ValueError, TypeError, RuntimeError, AttributeError) as e:
                logger.error("Failed to submit task %s: %s", task.task_id, e)
                results[task.task_id] = TaskResult(task_id=task.task_id, success=False, error=str(e))

        # 持续调度直到所有任务完成或失败
        iteration = 0
        while (
            len(self.coordinator.completed_tasks) + len(self.coordinator.failed_tasks) < len(tasks)
            and iteration < MAX_SCHEDULING_ITERATIONS
        ):
            iteration += 1
            # 查找准备执行的任务
            ready_tasks = self._get_ready_tasks(tasks)

            if not ready_tasks:
                logger.debug("Iteration %d: No ready tasks, waiting for dependencies", iteration)
                break

            logger.debug("Iteration %d: Executing %d ready tasks", iteration, len(ready_tasks))

            # 并行执行准备好的任务
            try:
                batch_results = await self.coordinator.execute_tasks_parallel(ready_tasks, max_parallel)
                results.update(batch_results)
            except (RuntimeError, ValueError, asyncio.TimeoutError) as e:
                logger.error("Failed to execute batch of tasks: %s", e)
                break

            # 短暂延迟
            await asyncio.sleep(SCHEDULING_DELAY)

            # 定期退化检测
            if batch_results and iteration % DEGRADATION_CHECK_INTERVAL == 0:
                self._check_degradation(batch_results)

        # 检查是否有未完成的任务
        total_completed = len(self.coordinator.completed_tasks) + len(self.coordinator.failed_tasks)
        if total_completed < len(tasks):
            logger.warning(
                "Workflow incomplete: %d/%d tasks completed. " "Possible dependency cycle or timeout.",
                total_completed,
                len(tasks),
            )

        logger.info(
            "Workflow execution completed: %d succeeded, %d failed",
            len(self.coordinator.completed_tasks),
            len(self.coordinator.failed_tasks),
        )

        return results

    def _get_ready_tasks(self, all_tasks: List[Task]) -> List[Task]:
        """
        获取准备执行的任务（依赖已满足，未完成/失败）

        Args:
            all_tasks: 所有任务的列表

        Returns:
            准备执行的任务列表（按优先级排序）
        """
        ready_tasks = []

        for task in all_tasks:
            # 跳过已完成或已失败的任务
            if task.task_id in self.coordinator.completed_tasks or task.task_id in self.coordinator.failed_tasks:
                continue

            # 检查依赖是否满足
            dependencies_met = all(dep_id in self.coordinator.completed_tasks for dep_id in task.dependencies)

            if dependencies_met:
                ready_tasks.append(task)

        # 按优先级排序（高优先级先执行）
        ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)

        return ready_tasks

    def execute(
        self,
        tasks: List[Task],
        max_parallel: int = DEFAULT_MAX_PARALLEL,
        async_execution: bool = False,
    ) -> Dict[str, TaskResult]:
        """
        执行工作流（同步接口，内部使用异步执行）

        Args:
            tasks: 要执行的任务列表
            max_parallel: 最大并行执行数
            async_execution: 是否使用异步执行（默认为False，同步等待）

        Returns:
            任务ID到结果的映射

        Raises:
            RuntimeError: 当异步执行失败时
        """
        self._workflow_messages = []
        self._degradation_report = None

        logger.info("Executing workflow with %d tasks", len(tasks))

        if async_execution:
            # 直接返回coroutine，由调用者处理
            return self.execute_workflow(tasks, max_parallel)

        # 同步执行：创建新的事件循环执行
        # 这样可以避免在已有事件循环中的冲突
        try:
            return asyncio.run(self.execute_workflow(tasks, max_parallel))
        except (RuntimeError, ValueError, asyncio.TimeoutError) as e:
            logger.error("Workflow execution failed: %s", e)
            raise RuntimeError(f"Failed to execute workflow: {e}") from e

    def _check_degradation(self, batch_results: Dict[str, TaskResult]) -> None:
        """检查工作流执行中的 LLM 退化信号

        在每个批次完成后，收集执行结果到消息列表中，
        使用 DegradationDetector 分析是否出现退化。

        Args:
            batch_results: 最新一批任务的执行结果
        """
        for task_id, result in batch_results.items():
            role = "assistant" if result.success else "user"
            content = result.output if result.success else (result.error or "unknown error")
            self._workflow_messages.append({"role": role, "content": content})

        if self._degradation_detector is None:
            from lingflow.context.degradation import DegradationDetector

            self._degradation_detector = DegradationDetector()

        report = self._degradation_detector.get_health_score(self._workflow_messages)
        self._degradation_report = report.to_dict()

        if report.health.value == "critical":
            logger.warning(
                "工作流退化检测: 状态=%s, 得分=%.2f, 退化类型=%s",
                report.health.value,
                report.score,
                [t.value for t in report.detected_types],
            )
            for rec in report.recommendations:
                logger.warning("  退化建议: %s", rec)
        elif report.health.value == "degraded":
            logger.info("工作流退化检测: 状态=%s, 得分=%.2f", report.health.value, report.score)

    def get_degradation_report(self) -> Optional[Dict]:
        """获取最近的退化检测报告

        Returns:
            退化检测报告字典，如果从未检测过则返回 None
        """
        return self._degradation_report
