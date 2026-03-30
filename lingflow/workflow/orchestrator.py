"""LingFlow 工作流编排器"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, List

from lingflow.common.config import get_config
from lingflow.common.models import Task, TaskResult, TaskPriority
from lingflow.coordination.coordinator import AgentCoordinator

# 常量定义（消除魔法值）
MAX_SCHEDULING_ITERATIONS = 100  # 最大调度迭代次数
SCHEDULING_DELAY = 0.01  # 调度间隔（秒）
DEFAULT_MAX_PARALLEL = 2  # 默认最大并行数

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

        with open(filepath, 'r', encoding='utf-8') as f:
            workflow_data = yaml.safe_load(f)

        if not workflow_data:
            raise ValueError(f"Empty workflow file: {filepath}")

        # 兼容不同字段名
        tasks_data = workflow_data.get('tasks') or workflow_data.get('stages', [])

        if not tasks_data:
            logger.warning(f"No tasks found in workflow: {filepath}")
            return []

        tasks = []
        for task_def in tasks_data:
            task_id = task_def.get('id', task_def.get('name'))
            if not task_id:
                logger.warning(f"Task missing id/name: {task_def}")
                continue

            # 解析优先级
            priority_str = task_def.get('priority', task_def.get('metadata', {}).get('priority', 'normal'))
            priority_map = {
                'high': TaskPriority.HIGH,
                'normal': TaskPriority.NORMAL,
                'low': TaskPriority.LOW
            }
            priority = priority_map.get(priority_str.lower(), TaskPriority.NORMAL)

            # 解析依赖
            dependencies = task_def.get('depends_on', task_def.get('dependencies', []))

            # 创建任务
            task = Task(
                task_id=task_id,
                name=task_def.get('skill', task_id),
                description=task_def.get('description', ''),
                agent_type=task_def.get('skill', 'general'),
                context=task_def.get('params', {}),
                priority=priority,
                dependencies=dependencies
            )
            tasks.append(task)

        logger.info(f"Loaded {len(tasks)} tasks from {filepath}")
        return tasks

    async def execute_workflow(
        self, tasks: List[Task], max_parallel: int = DEFAULT_MAX_PARALLEL
    ) -> Dict[str, TaskResult]:
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

        logger.info(
            f"Starting workflow execution with {len(tasks)} tasks, max_parallel={max_parallel}"
        )
        results = {}

        # 从配置获取最大并行数
        if max_parallel is None:
            max_parallel = get_config("workflow.max_parallel", 2)

        # 初始化任务状态
        for task in tasks:
            try:
                self.coordinator.submit_task(task)
            except Exception as e:
                logger.error(f"Failed to submit task {task.task_id}: {e}")
                results[task.task_id] = TaskResult(
                    task_id=task.task_id, success=False, error=str(e)
                )

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
                logger.debug(f"Iteration {iteration}: No ready tasks, waiting for dependencies")
                break

            logger.debug(f"Iteration {iteration}: Executing {len(ready_tasks)} ready tasks")

            # 并行执行准备好的任务
            try:
                batch_results = await self.coordinator.execute_tasks_parallel(
                    ready_tasks, max_parallel
                )
                results.update(batch_results)
            except Exception as e:
                logger.error(f"Failed to execute batch of tasks: {e}")
                break

            # 短暂延迟
            await asyncio.sleep(SCHEDULING_DELAY)

        # 检查是否有未完成的任务
        total_completed = len(self.coordinator.completed_tasks) + len(self.coordinator.failed_tasks)
        if total_completed < len(tasks):
            logger.warning(
                f"Workflow incomplete: {total_completed}/{len(tasks)} tasks completed. "
                f"Possible dependency cycle or timeout."
            )

        logger.info(
            f"Workflow execution completed: {len(self.coordinator.completed_tasks)} succeeded, "
            f"{len(self.coordinator.failed_tasks)} failed"
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
            if (
                task.task_id in self.coordinator.completed_tasks
                or task.task_id in self.coordinator.failed_tasks
            ):
                continue

            # 检查依赖是否满足
            dependencies_met = all(
                dep_id in self.coordinator.completed_tasks for dep_id in task.dependencies
            )

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
        logger.info(f"Executing workflow with {len(tasks)} tasks")

        if async_execution:
            # 直接返回coroutine，由调用者处理
            return self.execute_workflow(tasks, max_parallel)

        # 同步执行：创建新的事件循环执行
        # 这样可以避免在已有事件循环中的冲突
        try:
            return asyncio.run(self.execute_workflow(tasks, max_parallel))
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise RuntimeError(f"Failed to execute workflow: {e}") from e
