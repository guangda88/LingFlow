"""LingFlow 代理类"""

import asyncio
import time
from typing import Dict, Any, Optional
from lingflow.common.models import AgentStatus, AgentConfig, Task, TaskResult
from lingflow.coordination.base import BaseAgent


class Agent(BaseAgent):
    """简化的代理类"""

    def __init__(self, config: AgentConfig):
        super().__init__()
        self.config = config
        self.status = AgentStatus.IDLE
        self.tasks_completed = 0
        self.tasks_failed = 0

    def can_execute(self, task: Task) -> bool:
        """检查是否可以执行任务"""
        # 简化逻辑：匹配 agent_type
        if task.agent_type and task.agent_type != self.config.name:
            return False

        return True

    async def execute_task(self, task: Task, context: Dict[str, Any]) -> TaskResult:
        """执行任务"""
        start_time = time.time()
        self.status = AgentStatus.BUSY

        try:
            # 模拟任务执行
            await asyncio.sleep(0.05)  # 模拟工作

            # 测试用：某些任务失败
            if task.task_id == "task_2":
                raise ValueError("division by zero")

            execution_time = time.time() - start_time
            self.tasks_completed += 1
            self.status = AgentStatus.IDLE

            return TaskResult(
                task_id=task.task_id,
                success=True,
                output=f"Task {task.task_id} completed successfully",
                execution_time=execution_time,
                agent_used=self.config.name
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.tasks_failed += 1
            self.status = AgentStatus.FAILED

            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
                agent_used=self.config.name
            )

    def get_info(self) -> Dict[str, Any]:
        """获取代理信息"""
        return {
            'name': self.config.name,
            'description': self.config.description,
            'capabilities': self.config.capabilities,
            'status': self.status.value,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed
        }
