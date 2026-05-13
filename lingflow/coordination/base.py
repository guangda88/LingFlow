"""lingflow 协调相关的基类"""

from typing import Any, Dict

from lingflow.common.models import Task, TaskResult


class BaseCoordinator:
    """协调器基类"""

    def __init__(self) -> None:
        pass

    def _format_result(self, task_id: str, success: bool, result: Any = None, error: str = None) -> TaskResult:
        """格式化任务结果"""
        # 这里可以添加通用的结果格式化逻辑
        return TaskResult(
            task_id=task_id,
            success=success,
            output=str(result) if result else "",
            error=error or "",
            execution_time=0.0,
            agent_used="base",
        )

    def _validate_task(self, task: Task) -> bool:
        """验证任务是否有效"""
        # 这里可以添加通用的任务验证逻辑
        return True


class BaseAgent:
    """代理基类"""

    def __init__(self) -> None:
        pass

    def can_execute(self, task: Task) -> bool:
        """检查是否可以执行任务"""
        # 基础实现
        return True

    def get_info(self) -> Dict[str, Any]:
        """获取代理信息"""
        # 基础实现
        return {}
