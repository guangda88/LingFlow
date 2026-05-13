#!/usr/bin/env python3
"""
demo-01: 基础智能体示例

展示 lingflow 核心能力的完整示例
按照 VibeCoding 三轮开发法构建
"""

import asyncio
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BasicAgentExample:
    """基础智能体示例类"""

    def __init__(self):
        """初始化示例"""
        self.coordinator = None
        self.results = []

    def initialize(self):
        """
        第一步: 初始化 AgentCoordinator

        这是最基础的步骤，创建协调器实例
        """
        from lingflow import AgentCoordinator

        logger.info("初始化 AgentCoordinator...")
        self.coordinator = AgentCoordinator()

        # 显示可用信息
        agents = self.coordinator.list_agents()
        skills = self.coordinator.list_skills()

        logger.info(f"✅ 可用 Agent: {len(agents)} 个")
        logger.info(f"✅ 可用技能: {len(skills)} 个")

        return self

    def create_task(self, task_id: str, name: str, description: str, agent_type: str = "implementation"):
        """
        第二步: 创建任务

        任务是 lingflow 的基本执行单元
        """
        from lingflow import Task, TaskPriority

        logger.info(f"创建任务: {name}")

        task = Task(
            task_id=task_id,
            name=name,
            description=description,
            priority=TaskPriority.NORMAL,
            agent_type=agent_type
        )

        logger.info(f"✅ 任务创建成功: {task.task_id}")
        return task

    def execute_task(self, task):
        """
        第三步: 执行任务

        同步执行单个任务
        """
        logger.info(f"执行任务: {task.name}")

        # 准备上下文
        context = {
            "project_root": Path(__file__).parent.parent,
            "example": "demo-01"
        }

        # 执行任务
        result = self.coordinator.execute_task(task, context)

        # 记录结果
        self.results.append(result)

        # 处理结果
        if result.success:
            logger.info(f"✅ 任务成功: {result.output}")
        else:
            logger.error(f"❌ 任务失败: {result.error}")

        return result

    async def execute_task_async(self, task):
        """
        异步执行任务

        适合 IO 密集型任务
        """
        logger.info(f"异步执行任务: {task.name}")

        context = {
            "project_root": Path(__file__).parent.parent,
            "example": "demo-01"
        }

        result = await self.coordinator.execute_task_async(task, context)
        return result

    async def execute_tasks_parallel(self, tasks):
        """
        并行执行多个任务

        利用多智能体并行能力，提升性能
        """
        logger.info(f"并行执行 {len(tasks)} 个任务")

        context = {
            "project_root": Path(__file__).parent.parent,
            "example": "demo-01"
        }

        results = await self.coordinator.execute_tasks_parallel(
            tasks,
            max_parallel=3
        )

        # 统计结果
        success_count = sum(1 for r in results if r.success)
        logger.info(f"✅ 并行执行完成: {success_count}/{len(results)} 成功")

        return results

    def demonstrate_skill_chain(self):
        """
        展示技能链的使用

        lingflow 的强大之处在于技能的组合使用
        """
        logger.info("演示技能链: brainstorming → writing-plans → test-driven-development")

        # 第一步: 头脑风暴
        brainstorm_task = self.create_task(
            task_id="brainstorm-001",
            name="需求头脑风暴",
            description="探索如何改进这个示例项目",
            agent_type="architecture"
        )
        brainstorm_result = self.execute_task(brainstorm_task)

        if not brainstorm_result.success:
            logger.error("头脑风暴失败，停止技能链")
            return

        # 第二步: 编写计划
        plan_task = self.create_task(
            task_id="plan-001",
            name="实施计划",
            description="基于头脑风暴结果创建实施计划",
            agent_type="documentation"
        )
        plan_result = self.execute_task(plan_task)

        if not plan_result.success:
            logger.error("计划编写失败，停止技能链")
            return

        # 第三步: TDD 开发
        tdd_task = self.create_task(
            task_id="tdd-001",
            name="测试驱动开发",
            description="使用 TDD 方法实施改进",
            agent_type="testing"
        )
        tdd_result = self.execute_task(tdd_task)

        logger.info("✅ 技能链演示完成")

    def print_summary(self):
        """打印执行摘要"""
        logger.info("=" * 60)
        logger.info("执行摘要")
        logger.info("=" * 60)

        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        failed = total - success

        logger.info(f"总任务数: {total}")
        logger.info(f"成功: {success}")
        logger.info(f"失败: {failed}")

        if total > 0:
            success_rate = (success / total) * 100
            logger.info(f"成功率: {success_rate:.1f}%")

        # 详细结果
        for i, result in enumerate(self.results, 1):
            status = "✅" if result.success else "❌"
            logger.info(f"{i}. {status} {result.task_id} - {result.agent_used}")

        logger.info("=" * 60)


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("lingflow 基础智能体示例")
    print("=" * 60 + "\n")

    # 创建示例实例
    example = BasicAgentExample()

    try:
        # 第一步: 初始化
        example.initialize()
        print()

        # 第二步: 创建并执行单个任务
        logger.info("→ 演示 1: 单个任务执行")
        task1 = example.create_task(
            task_id="task-001",
            name="代码审查",
            description="审查示例代码质量",
            agent_type="review"
        )
        example.execute_task(task1)
        print()

        # 第三步: 并行执行多个任务
        logger.info("→ 演示 2: 并行任务执行")
        tasks = [
            example.create_task(f"parallel-{i}", f"并行任务 {i}", f"执行第 {i} 个任务")
            for i in range(1, 4)
        ]
        await example.execute_tasks_parallel(tasks)
        print()

        # 第四步: 技能链演示
        logger.info("→ 演示 3: 技能链使用")
        # example.demonstrate_skill_chain()
        print()

        # 打印摘要
        example.print_summary()

    except Exception as e:
        logger.error(f"执行出错: {e}", exc_info=True)
    finally:
        logger.info("✅ 示例执行完成")


def run_simple_example():
    """运行简化版示例"""
    print("\n" + "=" * 60)
    print("lingflow 简化示例")
    print("=" * 60 + "\n")

    # 最简单的使用方式
    from lingflow import AgentCoordinator, Task, TaskPriority

    # 1. 创建协调器
    coordinator = AgentCoordinator()

    # 2. 创建任务
    task = Task(
        task_id="simple-001",
        name="简单任务",
        description="这是一个简单的示例任务",
        priority=TaskPriority.NORMAL
    )

    # 3. 执行任务
    result = coordinator.execute_task(task, {})

    # 4. 查看结果
    if result.success:
        print(f"✅ 成功: {result.output}")
    else:
        print(f"❌ 失败: {result.error}")


if __name__ == "__main__":
    import sys

    # 根据命令行参数选择运行模式
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        run_simple_example()
    else:
        asyncio.run(main())
