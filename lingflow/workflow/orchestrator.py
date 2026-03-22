"""LingFlow 工作流编排器"""

import asyncio
import logging
from typing import Dict, List, Optional
from lingflow.coordination.coordinator import AgentCoordinator
from lingflow.common.models import Task, TaskResult, TaskPriority
from lingflow.common.config import get_config

# 常量定义（消除魔法值）
MAX_SCHEDULING_ITERATIONS = 100  # 最大调度迭代次数
SCHEDULING_DELAY = 0.01  # 调度间隔（秒）
DEFAULT_MAX_PARALLEL = 2  # 默认最大并行数

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """工作流编排器"""

    def __init__(self, coordinator: AgentCoordinator):
        self.coordinator = coordinator

    async def execute_workflow(self, tasks: List[Task], max_parallel: int = DEFAULT_MAX_PARALLEL) -> Dict[str, TaskResult]:
        """
        执行工作流（带依赖关系）

        Args:
            tasks: 要执行的任务列表
            max_parallel: 最大并行执行数

        Returns:
            任务ID到结果的映射
        """
        if not tasks:
            logger.warning("No tasks provided to execute_workflow")
            return {}

        logger.info(f"Starting workflow execution with {len(tasks)} tasks, max_parallel={max_parallel}")
        results = {}
        task_event = asyncio.Event()
        
        # 从配置获取最大并行数
        if max_parallel is None:
            max_parallel = get_config('workflow.max_parallel', 2)
        
        # 初始化任务状态
        for task in tasks:
            try:
                self.coordinator.submit_task(task)
            except Exception as e:
                logger.error(f"Failed to submit task {task.task_id}: {e}")
                results[task.task_id] = TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error=str(e)
                )

        # 持续调度直到所有任务完成或失败
        iteration = 0
        while len(self.coordinator.completed_tasks) + len(self.coordinator.failed_tasks) < len(tasks) and iteration < MAX_SCHEDULING_ITERATIONS:
            iteration += 1
            # 查找准备执行的任务
            ready_tasks = self._get_ready_tasks(tasks)

            if not ready_tasks:
                logger.debug(f"Iteration {iteration}: No ready tasks, waiting for dependencies")
                break

            logger.debug(f"Iteration {iteration}: Executing {len(ready_tasks)} ready tasks")

            # 并行执行准备好的任务
            try:
                batch_results = await self.coordinator.execute_tasks_parallel(ready_tasks, max_parallel)
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
            if task.task_id in self.coordinator.completed_tasks or task.task_id in self.coordinator.failed_tasks:
                continue

            # 检查依赖是否满足
            dependencies_met = all(
                dep_id in self.coordinator.completed_tasks
                for dep_id in task.dependencies
            )

            if dependencies_met:
                ready_tasks.append(task)

        # 按优先级排序（高优先级先执行）
        ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)

        return ready_tasks

    def execute(self, tasks: List[Task], max_parallel: int = DEFAULT_MAX_PARALLEL, async_execution: bool = False) -> Dict[str, TaskResult]:
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
        else:
            # 同步执行，等待完成
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已经在事件循环中，使用create_task
                    # 注意：这种情况下需要由调用者处理异步逻辑
                    logger.warning("Called from within event loop, returning coroutine")
                    return self.execute_workflow(tasks, max_parallel)
                else:
                    # 创建新的事件循环执行
                    return loop.run_until_complete(self.execute_workflow(tasks, max_parallel))
            except RuntimeError:
                # 没有事件循环，创建新的
                return asyncio.run(self.execute_workflow(tasks, max_parallel))
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                raise RuntimeError(f"Failed to execute workflow: {e}") from e
