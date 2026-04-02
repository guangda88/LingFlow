"""
LingFlow Agent Coordinator - 主入口文件

核心功能:
- 代理注册和发现
- 任务调度和并行执行
- 上下文压缩和优化
- 状态监控和管理
- 工作流编排
"""

import asyncio
from lingflow.coordination import AgentCoordinator
from lingflow.workflow import WorkflowOrchestrator
from lingflow.common import Task, TaskPriority


async def main():
    """测试主函数"""
    print("=" * 60)
    print("LingFlow Agent Coordinator - 重构版本")
    print("=" * 60)

    # 初始化协调器
    coordinator = AgentCoordinator()
    orchestrator = WorkflowOrchestrator(coordinator)

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

    results = await orchestrator.execute_workflow(workflow_tasks, max_parallel=2)

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
