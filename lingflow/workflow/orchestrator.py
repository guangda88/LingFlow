"""LingFlow 工作流编排器"""

import asyncio
from typing import Dict, List, Any
from lingflow.coordination.coordinator import AgentCoordinator
from lingflow.common.models import Task, TaskResult, TaskPriority
from lingflow.common.config import get_config


class WorkflowOrchestrator:
    """工作流编排器"""

    def __init__(self, coordinator: AgentCoordinator):
        self.coordinator = coordinator

    async def execute_workflow(self, tasks: List[Task], max_parallel: int = None) -> Dict[str, TaskResult]:
        """执行工作流（带依赖关系）"""
        results = {}
        task_event = asyncio.Event()
        
        # 从配置获取最大并行数
        if max_parallel is None:
            max_parallel = get_config('workflow.max_parallel', 2)
        
        # 初始化任务状态
        for task in tasks:
            self.coordinator.submit_task(task)

        # 持续调度直到所有任务完成或失败
        while len(self.coordinator.completed_tasks) + len(self.coordinator.failed_tasks) < len(tasks):
            # 查找准备执行的任务
            ready_tasks = self._get_ready_tasks(tasks)

            if not ready_tasks:
                # 等待任务完成事件
                await asyncio.wait_for(task_event.wait(), timeout=5.0)
                task_event.clear()
                continue

            # 并行执行准备好的任务
            batch_results = await self.coordinator.execute_tasks_parallel(ready_tasks, max_parallel)
            results.update(batch_results)

            # 触发任务完成事件
            task_event.set()

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
        # 直接执行技能，不通过代理
        results = {}
        for task_dict in tasks:
            task_id = task_dict['id']
            skill = task_dict.get('skill')
            params = task_dict.get('params', {})
            
            if skill:
                result = self.coordinator.execute_skill(skill, params)
                results[task_id] = result
        
        return {
            "tasks": [task['id'] for task in tasks],
            "status": "completed",
            "result": "Workflow executed successfully",
            "details": results
        }
