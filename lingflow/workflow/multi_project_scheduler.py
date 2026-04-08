"""多项目并行调度器

按 project 字段分组任务，组内按依赖串行调度，组间并行执行。
"""

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from lingflow.common.models import Task, TaskResult, TaskPriority
from lingflow.coordination.coordinator import AgentCoordinator
from lingflow.coordination.project_manager import ProjectManager
from lingflow.workflow.orchestrator import WorkflowOrchestrator

logger = logging.getLogger(__name__)

DEFAULT_MAX_PROJECTS_PARALLEL = 3
DEFAULT_TASK_TIMEOUT = 300


@dataclass
class ProjectScheduleStatus:
    """项目调度状态"""

    project: str
    total: int = 0
    completed: int = 0
    failed: int = 0
    running: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def is_done(self) -> bool:
        return self.completed + self.failed >= self.total

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project,
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "running": self.running,
            "elapsed": (self.end_time or time.time()) - (self.start_time or time.time()),
            "is_done": self.is_done,
        }


class MultiProjectScheduler:
    """跨项目并行调度器

    核心调度逻辑：
    1. 按 task.project 分组
    2. 每组内走 WorkflowOrchestrator（依赖感知，串行）
    3. 组间 asyncio.gather 并行
    4. 每个项目切换 working_dir 上下文
    """

    def __init__(
        self,
        project_manager: Optional[ProjectManager] = None,
        coordinator: Optional[AgentCoordinator] = None,
        max_projects_parallel: int = DEFAULT_MAX_PROJECTS_PARALLEL,
    ):
        self.project_manager = project_manager or ProjectManager()
        self.coordinator = coordinator or AgentCoordinator()
        self.max_projects_parallel = max_projects_parallel
        self._statuses: Dict[str, ProjectScheduleStatus] = {}
        self._results: Dict[str, TaskResult] = {}
        self._progress_callbacks: List[Any] = []

    def on_progress(self, callback) -> None:
        """注册进度回调（供灵依 Web 看板消费）"""
        self._progress_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        """获取调度状态（供 API/Web 消费）"""
        return {
            "projects": {name: s.to_dict() for name, s in self._statuses.items()},
            "total_tasks": len(self._results),
            "total_completed": sum(1 for r in self._results.values() if r.success),
            "total_failed": sum(1 for r in self._results.values() if not r.success),
        }

    def execute(self, tasks: List[Task], max_parallel_per_project: int = 2) -> Dict[str, TaskResult]:
        """同步执行多项目调度"""
        return asyncio.run(self.execute_async(tasks, max_parallel_per_project))

    async def execute_async(
        self,
        tasks: List[Task],
        max_parallel_per_project: int = 2,
    ) -> Dict[str, TaskResult]:
        """异步执行多项目调度

        Args:
            tasks: 任务列表（需带 project 字段）
            max_parallel_per_project: 单项目内最大并行数

        Returns:
            所有任务结果的映射
        """
        if not tasks:
            return {}

        groups = self._group_by_project(tasks)
        logger.info(
            "MultiProjectScheduler: %d tasks across %d projects: %s",
            len(tasks),
            len(groups),
            list(groups.keys()),
        )

        for project_name in groups:
            self._statuses[project_name] = ProjectScheduleStatus(
                project=project_name,
                total=len(groups[project_name]),
                start_time=time.time(),
            )

        semaphore = asyncio.Semaphore(self.max_projects_parallel)

        async def _run_project(project_name: str, project_tasks: List[Task]) -> Dict[str, TaskResult]:
            async with semaphore:
                return await self._execute_project(project_name, project_tasks, max_parallel_per_project)

        coros = [_run_project(name, pts) for name, pts in groups.items()]
        results_list = await asyncio.gather(*coros, return_exceptions=True)

        all_results: Dict[str, TaskResult] = {}
        for result in results_list:
            if isinstance(result, Exception):
                logger.error(f"Project execution failed: {result}")
                continue
            if isinstance(result, dict):
                all_results.update(result)

        self._results = all_results
        return all_results

    async def _execute_project(
        self,
        project_name: str,
        tasks: List[Task],
        max_parallel: int,
    ) -> Dict[str, TaskResult]:
        """执行单个项目内的任务（带依赖感知）"""
        status = self._statuses[project_name]
        status.running = 1
        self._notify_progress()

        project_ctx = self.project_manager.get(project_name)
        working_dir = ""
        if project_ctx:
            working_dir = project_ctx.path
            for task in tasks:
                if not task.working_dir:
                    task.working_dir = working_dir

        self._set_cwd(working_dir)

        orchestrator = WorkflowOrchestrator(self.coordinator)
        try:
            results = await orchestrator.execute_workflow(tasks, max_parallel)
        except (RuntimeError, ValueError, asyncio.TimeoutError) as e:
            logger.error(f"Project {project_name} workflow failed: {e}")
            results = {
                t.task_id: TaskResult(
                    task_id=t.task_id,
                    success=False,
                    error=f"Workflow failed: {e}",
                )
                for t in tasks
            }
        finally:
            status.running = 0
            status.end_time = time.time()
            for r in results.values():
                if r.success:
                    status.completed += 1
                else:
                    status.failed += 1
            self._notify_progress()

        return results

    def _group_by_project(self, tasks: List[Task]) -> Dict[str, List[Task]]:
        """按 project 字段分组"""
        groups: Dict[str, List[Task]] = defaultdict(list)
        for task in tasks:
            project = task.project or "default"
            groups[project].append(task)
        return dict(groups)

    def _set_cwd(self, working_dir: str) -> None:
        """设置工作目录上下文（为 coordinator 的 skill 执行准备）"""
        if working_dir:
            import os
            os.chdir(working_dir)
            logger.debug(f"Switched working directory to: {working_dir}")

    def _notify_progress(self) -> None:
        """通知进度回调"""
        status = self.get_status()
        for cb in self._progress_callbacks:
            try:
                cb(status)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    @staticmethod
    def load_tasks_from_yaml(filepath: str) -> List[Task]:
        """从 YAML 加载多项目任务

        YAML 格式：
        tasks:
          - task_id: t1
            project: LingFlow
            skill: code-review
            priority: high
            depends_on: []
            params:
              target: src/
        """
        import yaml

        with open(filepath) as f:
            data = yaml.safe_load(f)

        priority_map = {
            "critical": TaskPriority.CRITICAL,
            "high": TaskPriority.HIGH,
            "normal": TaskPriority.NORMAL,
            "low": TaskPriority.LOW,
        }

        tasks = []
        for task_def in data.get("tasks", []):
            priority_str = task_def.get("priority", "normal")
            priority = priority_map.get(priority_str.lower(), TaskPriority.NORMAL)

            task = Task(
                task_id=task_def["task_id"],
                name=task_def.get("skill", task_def["task_id"]),
                description=task_def.get("description", ""),
                agent_type=task_def.get("skill", task_def.get("agent_type", "implementation")),
                project=task_def.get("project", ""),
                working_dir=task_def.get("working_dir", ""),
                priority=priority,
                dependencies=task_def.get("depends_on", []),
                context=task_def.get("params", {}),
            )
            tasks.append(task)

        return tasks
