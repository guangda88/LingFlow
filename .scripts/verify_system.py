#!/usr/bin/env python3
"""
LingFlow v1.1.0 系统验证脚本

快速验证所有核心功能是否正常工作
"""

import asyncio
import sys
from agent_coordinator import AgentCoordinator, Task, TaskPriority

def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_agent_registry():
    """测试代理注册系统"""
    print_section("1. 代理注册系统测试")

    coordinator = AgentCoordinator()

    # 检查代理数量
    agents = coordinator.registry.list_agents()
    assert len(agents) == 6, f"Expected 6 agents, got {len(agents)}"
    print(f"✅ 代理注册成功: {len(agents)} 个代理")

    # 检查代理类型
    agent_names = [a['name'] for a in agents]
    expected_names = ['implementation', 'review', 'testing', 'debugging', 'architecture', 'documentation']
    assert set(agent_names) == set(expected_names), f"Expected {expected_names}, got {agent_names}"
    print(f"✅ 代理类型正确: {', '.join(expected_names)}")

    # 检查代理能力
    for agent_info in agents:
        assert 'capabilities' in agent_info, f"Agent {agent_info['name']} missing capabilities"
        assert len(agent_info['capabilities']) > 0, f"Agent {agent_info['name']} has no capabilities"
    print(f"✅ 所有代理都有能力定义")

    return coordinator

def test_context_compression(coordinator):
    """测试上下文压缩"""
    print_section("2. 上下文压缩测试")

    # 测试长文本压缩
    long_text = """
    This is a long text for testing context compression.
    The compression algorithm should identify the most important parts
    and reduce the overall size while maintaining key information.
    """ * 10

    compressed = coordinator.compressor.compress(long_text)
    assert len(compressed) <= len(long_text), "Compressed text should not be longer"
    print(f"✅ 压缩功能正常: {len(long_text)} → {len(compressed)} 字符")

    # 测试空文本
    assert coordinator.compressor.compress("") == "", "Empty text should compress to empty"
    print(f"✅ 空文本处理正常")

    # 获取统计信息
    stats = coordinator.compressor.get_stats()
    assert 'total_compressions' in stats, "Missing total_compressions stat"
    assert 'tokens_saved' in stats, "Missing tokens_saved stat"
    print(f"✅ 压缩统计正常")

async def test_parallel_execution(coordinator):
    """测试并行任务执行"""
    print_section("3. 并行任务执行测试")

    # 创建测试任务
    tasks = [
        Task(
            id="test-1",
            description="Test task 1",
            agent_type="testing",
            context={"data": "test1"}
        ),
        Task(
            id="test-2",
            description="Test task 2",
            agent_type="testing",
            context={"data": "test2"}
        ),
        Task(
            id="test-3",
            description="Test task 3",
            agent_type="review",
            context={"data": "test3"}
        )
    ]

    # 执行并行任务
    results = await coordinator.execute_tasks_parallel(tasks, max_parallel=2)

    # 验证结果
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"
    print(f"✅ 并行执行完成: {len(results)} 个任务")

    # 检查成功/失败数量
    success_count = sum(1 for r in results.values() if r.success)
    failed_count = sum(1 for r in results.values() if not r.success)
    print(f"✅ 成功: {success_count}, 失败: {failed_count}")

    # 重置协调器
    coordinator.reset()

async def test_workflow_execution(coordinator):
    """测试工作流执行"""
    print_section("4. 工作流执行测试")

    # 创建带依赖的任务
    tasks = [
        Task(
            id="setup",
            description="Setup task",
            agent_type="implementation",
            context={"data": "setup"}
        ),
        Task(
            id="task-1",
            description="Task 1",
            agent_type="testing",
            dependencies=["setup"],
            context={"data": "task1"}
        ),
        Task(
            id="task-2",
            description="Task 2",
            agent_type="review",
            dependencies=["task-1"],
            context={"data": "task2"}
        )
    ]

    # 执行工作流
    results = await coordinator.execute_workflow(tasks)

    # 验证结果
    assert len(results) > 0, "Expected at least some results"
    print(f"✅ 工作流执行完成: {len(results)} 个任务")

    # 检查任务状态
    for task_id, result in results.items():
        status = "✅" if result.success else "❌"
        print(f"  {status} {task_id}: {result.error if not result.success else 'OK'}")

    # 重置协调器
    coordinator.reset()

def test_status_monitoring(coordinator):
    """测试状态监控"""
    print_section("5. 状态监控测试")

    # 获取状态
    status = coordinator.get_status()

    # 验证状态字段
    required_fields = ['total_tasks', 'pending_tasks', 'completed_tasks', 'failed_tasks']
    for field in required_fields:
        assert field in status, f"Missing field: {field}"

    print(f"✅ 状态监控正常:")
    print(f"  总任务: {status['total_tasks']}")
    print(f"  待处理: {status['pending_tasks']}")
    print(f"  已完成: {status['completed_tasks']}")
    print(f"  已失败: {status['failed_tasks']}")
    print(f"  代理数: {len(status['agents'])}")

async def main():
    """主测试函数"""
    print("=" * 70)
    print("  LingFlow v1.1.0 系统验证")
    print("=" * 70)

    try:
        # 测试 1: 代理注册
        coordinator = test_agent_registry()

        # 测试 2: 上下文压缩
        test_context_compression(coordinator)

        # 测试 3: 并行执行
        await test_parallel_execution(coordinator)

        # 测试 4: 工作流执行
        await test_workflow_execution(coordinator)

        # 测试 5: 状态监控
        test_status_monitoring(coordinator)

        # 总结
        print_section("验证总结")
        print("✅ 所有测试通过！")
        print("\nLingFlow v1.1.0 系统已就绪，可以正常使用。")
        print("\n下一步:")
        print("  1. 查看 docs/V1.1.0_IMPLEMENTATION_SUMMARY.md 了解详细实现")
        print("  2. 查看 docs/AGENT_COORDINATION_GUIDE.md 学习如何使用")
        print("  3. 运行 python agent_coordinator.py 查看更多示例")

        return 0

    except Exception as e:
        print_section("❌ 验证失败")
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
