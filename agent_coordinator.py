"""
LingFlow Agent Coordinator - 简化版本

核心功能:
- 代理注册和发现
- 任务调度和并行执行
- 上下文压缩和优化
- 状态监控和管理
"""

import asyncio
import json
import logging
import hashlib
import re
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 简化日志配置
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


# ============================================================================
# 数据模型
# ============================================================================

class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class AgentConfig:
    name: str
    description: str
    capabilities: List[str]
    max_tasks: int = 1
    context_limit: int = 8000
    timeout: int = 300
    parallel_safe: bool = True


@dataclass
class Task:
    task_id: str
    name: str
    description: str
    priority: TaskPriority
    agent_type: str = ""  # 指定代理类型（简化）
    dependencies: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    task_id: str
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    agent_used: Optional[str] = None


# ============================================================================
# 上下文压缩器（简化）
# ============================================================================

class ContextCompressor:
    """简化的上下文压缩器"""

    def __init__(self, target_tokens: int = 4000):
        self.target_tokens = target_tokens
        self.compressions_count = 0
        self.tokens_saved = 0

    def compress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """压缩上下文"""
        if not context:
            return context

        self.compressions_count += 1
        original_tokens = self._estimate_tokens(context)

        # 简化策略：保留关键字段，截断长文本
        compressed = {}
        priority_keys = ['requirements', 'specification', 'description']

        # 优先保留高优先级字段
        for key in priority_keys:
            if key in context:
                value = str(context[key])
                if len(value) > 1000:
                    value = value[:1000] + "... [truncated]"
                compressed[key] = value

        # 处理其他字段（限制数量）
        other_count = 0
        max_other = 3
        for key, value in context.items():
            if key not in compressed and other_count < max_other:
                compressed[key] = str(value)[:500]
                other_count += 1

        saved_tokens = original_tokens - self._estimate_tokens(compressed)
        self.tokens_saved += saved_tokens

        return compressed

    def _estimate_tokens(self, data: Any) -> int:
        """估算 token 数量"""
        text = str(data)
        return len(text) // 4  # 简单估算：4 字符/token

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            'total_compressions': self.compressions_count,
            'tokens_saved': self.tokens_saved
        }


# ============================================================================
# 代理类（简化）
# ============================================================================

class Agent:
    """简化的代理类"""

    def __init__(self, config: AgentConfig):
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


# ============================================================================
# 代理注册表（简化）
# ============================================================================

class AgentRegistry:
    """简化的代理注册表"""

    def __init__(self):
        self.agents: Dict[str, Agent] = {}

    def register_agent(self, agent: Agent):
        """注册代理"""
        self.agents[agent.config.name] = agent

    def get_agent(self, name: str) -> Optional[Agent]:
        """获取代理"""
        return self.agents.get(name)

    def find_agents_for_task(self, task: Task) -> List[Agent]:
        """查找适合执行任务的代理"""
        capable_agents = []

        # 1. 如果指定了 agent_type，首先尝试精确匹配
        if task.agent_type:
            agent = self.get_agent(task.agent_type)
            if agent and agent.can_execute(task):
                return [agent]

        # 2. 否则，查找能力匹配的代理
        for agent in self.agents.values():
            if agent.can_execute(task):
                capable_agents.append(agent)

        return capable_agents

    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有代理"""
        return [agent.get_info() for agent in self.agents.values()]


# ============================================================================
# 代理协调器（简化）
# ============================================================================

class AgentCoordinator:
    """简化的代理协调器"""

    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or AgentRegistry()
        self.task_queue: List[Task] = []
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.failed_tasks: Dict[str, TaskResult] = {}
        self.compressor = ContextCompressor()
        self._register_default_agents()

    def _register_default_agents(self):
        """注册默认代理"""
        configs = [
            AgentConfig(
                name="implementation",
                description="Code implementation agent",
                capabilities=["code_generation", "testing", "documentation"]
            ),
            AgentConfig(
                name="review",
                description="Code review agent",
                capabilities=["code_review", "design_review", "security_check"]
            ),
            AgentConfig(
                name="testing",
                description="Testing agent",
                capabilities=["test_generation", "test_execution", "coverage_analysis"]
            ),
            AgentConfig(
                name="debugging",
                description="Debugging agent",
                capabilities=["error_analysis", "root_cause", "fix_generation"]
            ),
            AgentConfig(
                name="architecture",
                description="Architecture agent",
                capabilities=["system_design", "architecture_review", "api_design"]
            ),
            AgentConfig(
                name="documentation",
                description="Documentation agent",
                capabilities=["doc_generation", "api_doc_writing", "readme_generation"]
            )
        ]

        for config in configs:
            self.registry.register_agent(Agent(config))

    def submit_task(self, task: Task):
        """提交任务"""
        self.task_queue.append(task)

    async def execute_tasks_parallel(self, tasks: List[Task], max_parallel: int = 2) -> Dict[str, TaskResult]:
        """并行执行任务"""
        results = {}
        semaphore = asyncio.Semaphore(max_parallel)

        async def execute_one(task: Task):
            async with semaphore:
                # 查找代理
                agents = self.registry.find_agents_for_task(task)
                if not agents:
                    print(f"  ❌ No agent found for {task.task_id}")
                    return TaskResult(
                        task_id=task.task_id,
                        success=False,
                        error="No suitable agent found"
                    )

                # 使用第一个可用代理
                agent = agents[0]

                # 压缩上下文
                compressed_context = self.compressor.compress(task.context)

                # 执行任务
                result = await agent.execute_task(task, compressed_context)
                return result

        # 并行执行所有任务
        results_list = await asyncio.gather(*[execute_one(task) for task in tasks], return_exceptions=True)

        # 处理结果
        for result in results_list:
            if isinstance(result, Exception):
                print(f"  ❌ Exception: {result}")
                continue

            if result:
                results[result.task_id] = result

                if result.success:
                    self.completed_tasks[result.task_id] = result
                    print(f"  ✅ {result.task_id} completed")
                else:
                    self.failed_tasks[result.task_id] = result
                    print(f"  ❌ {result.task_id} failed: {result.error}")

        return results

    async def execute_workflow(self, tasks: List[Task], max_parallel: int = 2) -> Dict[str, TaskResult]:
        """执行工作流（带依赖关系）"""
        results = {}

        # 初始化任务状态
        for task in tasks:
            self.submit_task(task)

        # 持续调度直到所有任务完成或失败
        max_iterations = 100  # 防止无限循环
        iteration = 0

        while len(self.completed_tasks) + len(self.failed_tasks) < len(tasks) and iteration < max_iterations:
            iteration += 1

            # 查找准备执行的任务
            ready_tasks = self._get_ready_tasks(tasks)

            if not ready_tasks:
                break

            # 并行执行准备好的任务
            batch_results = await self.execute_tasks_parallel(ready_tasks, max_parallel)
            results.update(batch_results)

            # 短暂延迟
            await asyncio.sleep(0.01)

        return results

    def _get_ready_tasks(self, all_tasks: List[Task]) -> List[Task]:
        """获取准备执行的任务（依赖已满足，未完成/失败）"""
        ready_tasks = []

        for task in all_tasks:
            # 跳过已完成或已失败的任务
            if task.task_id in self.completed_tasks or task.task_id in self.failed_tasks:
                continue

            # 检查依赖是否满足
            dependencies_met = all(
                dep_id in self.completed_tasks
                for dep_id in task.dependencies
            )

            if dependencies_met:
                ready_tasks.append(task)

        # 按优先级排序
        ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)

        return ready_tasks

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'total_tasks': len(self.task_queue) + len(self.completed_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'agents': len(self.registry.agents),
            'compression_stats': self.compressor.get_stats()
        }

    def reset(self):
        """重置状态"""
        self.task_queue.clear()
        self.completed_tasks.clear()
        self.failed_tasks.clear()


# ============================================================================
# 主函数（测试）
# ============================================================================

async def main():
    """测试主函数"""
    print("=" * 60)
    print("LingFlow Agent Coordinator - 简化版本")
    print("=" * 60)

    # 初始化协调器
    coordinator = AgentCoordinator()

    # 显示注册的代理
    print("\n注册的代理:")
    for agent_info in coordinator.registry.list_agents():
        print(f"  - {agent_info['name']}: {agent_info['capabilities']}")

    # 测试并行执行
    print("\n测试并行执行:")
    tasks = [
        Task(
            task_id="task_1",
            name="Test Task 1",
            description="First test task",
            priority=TaskPriority.HIGH,
            agent_type="implementation",
            context={"data": "test1"}
        ),
        Task(
            task_id="task_2",
            name="Test Task 2",
            description="Second test task",
            priority=TaskPriority.NORMAL,
            agent_type="testing",
            context={"data": "test2"}
        ),
        Task(
            task_id="task_3",
            name="Test Task 3",
            description="Third test task",
            priority=TaskPriority.NORMAL,
            agent_type="review",
            context={"data": "test3"}
        )
    ]

    results = await coordinator.execute_tasks_parallel(tasks, max_parallel=2)

    print("\n结果:")
    for task_id, result in results.items():
        status = "✅" if result.success else "❌"
        print(f"  {status} {task_id}: {result.error if not result.success else 'OK'}")

    # 测试工作流
    print("\n测试工作流执行:")
    coordinator.reset()

    workflow_tasks = [
        Task(
            task_id="setup",
            name="Setup",
            description="Setup task",
            priority=TaskPriority.HIGH,
            agent_type="implementation"
        ),
        Task(
            task_id="task_1",
            name="Task 1",
            description="First task",
            priority=TaskPriority.HIGH,
            agent_type="testing",
            dependencies=["setup"]
        ),
        Task(
            task_id="task_2",
            name="Task 2",
            description="Second task",
            priority=TaskPriority.NORMAL,
            agent_type="review",
            dependencies=["task_1"]
        )
    ]

    results = await coordinator.execute_workflow(workflow_tasks, max_parallel=2)

    print("\n结果:")
    for task_id, result in results.items():
        status = "✅" if result.success else "❌"
        print(f"  {status} {task_id}: {result.error if not result.success else 'OK'}")

    # 显示状态
    print("\n系统状态:")
    status = coordinator.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

    print("\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
