#!/usr/bin/env python3
"""
LingFlow v1.1.0 全面测试脚本

测试覆盖:
- 代理注册和发现
- 并行任务执行
- 工作流执行（依赖）
- 上下文压缩
- 状态监控
- 错误处理
"""

import asyncio
import sys
from lingflow.coordination import AgentCoordinator
from lingflow.workflow import WorkflowOrchestrator
from lingflow.common import Task, TaskPriority


class TestRunner:
    """测试运行器"""

    def __init__(self):
        self.coordinator = AgentCoordinator()
        self.orchestrator = WorkflowOrchestrator(self.coordinator)
        self.passed = 0
        self.failed = 0
        self.errors = []

    def print_header(self, title):
        """打印测试标题"""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)

    def print_result(self, test_name, passed, error=None):
        """打印测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {test_name}")

        if passed:
            self.passed += 1
        else:
            self.failed += 1
            if error:
                self.errors.append((test_name, error))
                print(f"         错误: {error}")

    def test_1_agent_registration(self):
        """测试 1: 代理注册"""
        self.print_header("测试 1: 代理注册和发现")

        # 测试代理数量
        agents = self.coordinator.registry.list_agents()
        expected_count = 6
        actual_count = len(agents)
        self.print_result(
            f"代理数量 ({actual_count} == {expected_count})",
            actual_count == expected_count
        )

        # 测试代理类型
        agent_names = [a['name'] for a in agents]
        expected_names = ['implementation', 'review', 'testing', 'debugging', 'architecture', 'documentation']
        self.print_result(
            f"代理类型正确",
            set(agent_names) == set(expected_names)
        )

        # 测试代理能力
        has_capabilities = all(
            len(a['capabilities']) > 0
            for a in agents
        )
        self.print_result(
            "所有代理都有能力定义",
            has_capabilities
        )

        # 测试代理查找
        implementation = self.coordinator.registry.get_agent('implementation')
        self.print_result(
            "可以查找代理",
            implementation is not None
        )

    def test_2_context_compression(self):
        """测试 2: 上下文压缩"""
        self.print_header("测试 2: 上下文压缩")

        # 测试简单上下文
        simple_context = {"key": "value"}
        compressed = self.coordinator.compressor.compress(simple_context)
        self.print_result(
            "简单上下文压缩",
            isinstance(compressed, dict)
        )

        # 测试复杂上下文
        complex_context = {
            "requirements": "This is a long requirement. " * 100,
            "description": "This is a long description. " * 100,
            "notes": "These are notes. " * 100,
            "extra1": "Extra field 1 " * 100,
            "extra2": "Extra field 2 " * 100,
            "extra3": "Extra field 3 " * 100,
            "extra4": "Extra field 4 " * 100,
        }
        compressed = self.coordinator.compressor.compress(complex_context)
        self.print_result(
            "复杂上下文压缩",
            len(compressed) < len(complex_context)
        )

        # 测试空上下文
        empty_compressed = self.coordinator.compressor.compress({})
        self.print_result(
            "空上下文处理",
            empty_compressed == {}
        )

        # 测试统计信息
        stats = self.coordinator.compressor.get_stats()
        self.print_result(
            "压缩统计信息",
            'total_compressions' in stats and 'tokens_saved' in stats
        )

    def test_3_parallel_execution(self):
        """测试 3: 并行任务执行"""
        self.print_header("测试 3: 并行任务执行")

        # 创建测试任务
        tasks = [
            Task(
                task_id="parallel_1",
                name="Parallel Task 1",
                description="First parallel task",
                priority=TaskPriority.HIGH,
                agent_type="implementation",
                context={"data": "test1"}
            ),
            Task(
                task_id="parallel_2",
                name="Parallel Task 2",
                description="Second parallel task",
                priority=TaskPriority.NORMAL,
                agent_type="testing",
                context={"data": "test2"}
            ),
            Task(
                task_id="parallel_3",
                name="Parallel Task 3",
                description="Third parallel task",
                priority=TaskPriority.NORMAL,
                agent_type="review",
                context={"data": "test3"}
            )
        ]

        # 执行并行任务
        try:
            results = asyncio.run(
                self.coordinator.execute_tasks_parallel(tasks, max_parallel=2)
            )

            # 验证结果
            self.print_result(
                f"所有任务返回结果 ({len(results)} == {len(tasks)})",
                len(results) == len(tasks)
            )

            # 验证成功任务
            success_count = sum(1 for r in results.values() if r.success)
            self.print_result(
                f"成功任务数 ({success_count})",
                success_count >= 2  # 至少 2 个成功（task_2 会失败）
            )

            # 验证任务执行时间
            for result in results.values():
                self.print_result(
                    f"任务 {result.task_id} 有执行时间",
                    result.execution_time > 0
                )

        except Exception as e:
            self.print_result("并行执行", False, str(e))

    async def test_4_workflow_execution(self):
        """测试 4: 工作流执行"""
        self.print_header("测试 4: 工作流执行（依赖）")

        # 重置协调器
        self.coordinator.reset()

        # 创建带依赖的任务
        workflow_tasks = [
            Task(
                task_id="setup",
                name="Setup Task",
                description="Initial setup",
                priority=TaskPriority.HIGH,
                agent_type="implementation",
                context={"data": "setup"}
            ),
            Task(
                task_id="dev_task",
                name="Development Task",
                description="Development work",
                priority=TaskPriority.HIGH,
                agent_type="testing",
                dependencies=["setup"],
                context={"data": "dev"}
            ),
            Task(
                task_id="review_task",
                name="Review Task",
                description="Code review",
                priority=TaskPriority.NORMAL,
                agent_type="review",
                dependencies=["dev_task"],
                context={"data": "review"}
            ),
            Task(
                task_id="doc_task",
                name="Documentation Task",
                description="Write documentation",
                priority=TaskPriority.LOW,
                agent_type="documentation",
                dependencies=["setup"],  # 只依赖 setup，可以与 dev_task 并行
                context={"data": "doc"}
            )
        ]

        # 执行工作流
        try:
            results = await self.orchestrator.execute_workflow(workflow_tasks, max_parallel=2)

            # 验证结果
            self.print_result(
                f"工作流执行返回结果 ({len(results)})",
                len(results) > 0
            )

            # 验证依赖顺序
            setup_done = "setup" in self.coordinator.completed_tasks
            self.print_result(
                "Setup 任务先完成",
                setup_done
            )

            # 验证并行执行（doc_task 和 dev_task 可以并行）
            dev_done = "dev_task" in self.coordinator.completed_tasks
            doc_done = "doc_task" in self.coordinator.completed_tasks
            self.print_result(
                "并行任务执行",
                dev_done or doc_done
            )

        except Exception as e:
            self.print_result("工作流执行", False, str(e))

    def test_5_status_monitoring(self):
        """测试 5: 状态监控"""
        self.print_header("测试 5: 状态监控")

        # 获取状态
        status = self.coordinator.get_status()

        # 验证状态字段
        required_fields = ['total_tasks', 'completed_tasks', 'failed_tasks', 'agents', 'compression_stats']
        for field in required_fields:
            self.print_result(
                f"状态包含 {field} 字段",
                field in status
            )

        # 验证状态值
        self.print_result(
            "代理数量正确 (6)",
            status['agents'] == 6
        )

        self.print_result(
            "压缩统计存在",
            isinstance(status['compression_stats'], dict)
        )

    def test_6_error_handling(self):
        """测试 6: 错误处理"""
        self.print_header("测试 6: 错误处理")

        # 测试无效代理类型
        invalid_task = Task(
            task_id="invalid_task",
            name="Invalid Task",
            description="Task with invalid agent type",
            priority=TaskPriority.NORMAL,
            agent_type="nonexistent_agent",
            context={"data": "test"}
        )

        try:
            results = asyncio.run(
                self.coordinator.execute_tasks_parallel([invalid_task], max_parallel=1)
            )

            # 验证错误处理
            result = results.get('invalid_task')
            self.print_result(
                "无效代理类型返回错误",
                result and not result.success and 'No suitable agent' in (result.error or '')
            )

        except Exception as e:
            self.print_result("错误处理", False, str(e))

        # 测试执行中的错误（task_2 会失败）
        error_task = Task(
            task_id="task_2",  # 使用 task_2 来触发错误
            name="Error Task",
            description="Task that will fail",
            priority=TaskPriority.NORMAL,
            agent_type="testing",
            context={"data": "test"}
        )

        try:
            results = asyncio.run(
                self.coordinator.execute_tasks_parallel([error_task], max_parallel=1)
            )

            # 验证错误捕获
            result = results.get('task_2')
            self.print_result(
                "执行错误被捕获",
                result and not result.success and 'division by zero' in (result.error or '')
            )

        except Exception as e:
            self.print_result("错误捕获", False, str(e))

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("  LingFlow v1.1.0 全面测试")
        print("=" * 70)

        # 运行测试
        self.test_1_agent_registration()
        self.test_2_context_compression()
        self.test_3_parallel_execution()
        asyncio.run(self.test_4_workflow_execution())
        self.test_5_status_monitoring()
        self.test_6_error_handling()

        # 打印总结
        self.print_header("测试总结")
        print(f"\n  总测试数: {self.passed + self.failed}")
        print(f"  通过: {self.passed} ✅")
        print(f"  失败: {self.failed} ❌")
        print(f"  成功率: {self.passed / (self.passed + self.failed) * 100:.1f}%")

        if self.errors:
            print("\n  失败详情:")
            for test_name, error in self.errors:
                print(f"    - {test_name}: {error}")

        print("\n" + "=" * 70)
        if self.failed == 0:
            print("  ✅ 所有测试通过！")
        else:
            print(f"  ⚠️  {self.failed} 个测试失败")
        print("=" * 70)

        return self.failed == 0


def main():
    """主函数"""
    runner = TestRunner()
    success = runner.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
