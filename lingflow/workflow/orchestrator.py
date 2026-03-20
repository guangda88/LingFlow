"""LingFlow 工作流编排器"""

import asyncio
from typing import Dict, List, Any
from lingflow.coordination.coordinator import AgentCoordinator
from lingflow.common.models import Task, TaskResult


class WorkflowOrchestrator:
    """工作流编排器"""

    def __init__(self, coordinator: AgentCoordinator):
        self.coordinator = coordinator

    async def execute_workflow(self, tasks: List[Task], max_parallel: int = 2) -> Dict[str, TaskResult]:
        """执行工作流（带依赖关系）"""
        results = {}

        # 初始化任务状态
        for task in tasks:
            self.coordinator.submit_task(task)

        # 持续调度直到所有任务完成或失败
        max_iterations = 100  # 防止无限循环
        iteration = 0

        while len(self.coordinator.completed_tasks) + len(self.coordinator.failed_tasks) < len(tasks) and iteration < max_iterations:
            iteration += 1

            # 查找准备执行的任务
            ready_tasks = self._get_ready_tasks(tasks)

            if not ready_tasks:
                break

            # 并行执行准备好的任务
            batch_results = await self.coordinator.execute_tasks_parallel(ready_tasks, max_parallel)
            results.update(batch_results)

            # 短暂延迟
            await asyncio.sleep(0.01)

        return results

    def _get_ready_tasks(self, all_tasks: List[Task]) -> List[Task]:
        """获取准备执行的任务（依赖已满足，未完成/失败）"""
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

        # 按优先级排序
        ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)

        return ready_tasks

    def execute(self, tasks: list):
        """执行工作流"""
        # 这里可以添加工作流执行逻辑
        # 目前返回一个模拟结果
        return {
            "tasks": [task['id'] for task in tasks],
            "status": "completed",
            "result": "Workflow executed successfully"
        }
