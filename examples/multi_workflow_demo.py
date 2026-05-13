#!/usr/bin/env python3
"""
lingflow 多工程流系统演示

展示如何使用双工程流和多工程流系统
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lingflow.workflow.multi_workflow import (
    MultiWorkflowCoordinator,
    FastTrackWorkflow,
    StableTrackWorkflow,
    DevWorkflow,
    TestWorkflow,
    DocWorkflow,
    ExecutionStrategy,
    WorkflowType,
    WorkflowConfig
)
from lingflow.common.models import Task, TaskPriority


async def demo_dual_workflow():
    """演示双工程流系统"""
    print("\n" + "="*60)
    print("🚀 双工程流系统演示")
    print("="*60)

    # 创建协调器
    coordinator = MultiWorkflowCoordinator(max_parallel_workflows=2)

    # 快速工程流（YOLO模式）
    print("\n📦 创建快速工程流（YOLO模式）...")
    fast_track = FastTrackWorkflow("fast_demo")

    # 添加任务
    fast_track.add_task(Task(
        task_id="syntax_check",
        name="语法检查",
        description="Python语法检查",
        priority=TaskPriority.HIGH,
        agent_type="implementation"
    ))

    fast_track.add_task(Task(
        task_id="quick_test",
        name="快速测试",
        description="基础单元测试（30%覆盖率）",
        priority=TaskPriority.NORMAL,
        agent_type="testing"
    ))

    # 稳定工程流（生产就绪）
    print("\n📦 创建稳定工程流（生产就绪）...")
    stable_track = StableTrackWorkflow("stable_demo")

    stable_track.add_task(Task(
        task_id="full_test",
        name="完整测试",
        description="全面测试套件（70%覆盖率）",
        priority=TaskPriority.HIGH,
        agent_type="testing"
    ))

    stable_track.add_task(Task(
        task_id="code_review",
        name="代码审查",
        description="高级开发者审查",
        priority=TaskPriority.HIGH,
        agent_type="review"
    ))

    # 注册工程流
    coordinator.register_workflow(fast_track)
    coordinator.register_workflow(stable_track)

    print("\n✅ 工程流注册完成")
    print(f"   - 快速工程流: {fast_track.workflow_id}")
    print(f"   - 稳定工程流: {stable_track.workflow_id}")

    # 显示配置
    print("\n⚙️  配置对比:")
    print(f"\n快速工程流 ({fast_track.workflow_id}):")
    print(f"   - 跳过步骤: {fast_track.config.skip_steps}")
    print(f"   - 质量阈值: {fast_track.config.quality_thresholds}")
    print(f"   - 自动提交: {fast_track.config.auto_commit}")

    print(f"\n稳定工程流 ({stable_track.workflow_id}):")
    print(f"   - 必需步骤: {stable_track.config.required_steps[:3]}...")
    print(f"   - 质量阈值: {stable_track.config.quality_thresholds}")
    print(f"   - 自动提交: {stable_track.config.auto_commit}")

    # 执行
    print("\n🔄 执行工程流（并行策略）...")
    results = await coordinator.execute_all(
        strategy=ExecutionStrategy.PARALLEL
    )

    # 结果
    print("\n📊 执行结果:")
    for wf_id, result in results.items():
        status = "✅" if result.success else "❌"
        print(f"   {status} {wf_id}: {result.status.value}")
        if result.execution_time > 0:
            print(f"      执行时间: {result.execution_time:.2f}s")

    print("\n✅ 双工程流演示完成！")


async def demo_multi_workflow():
    """演示多工程流系统"""
    print("\n" + "="*60)
    print("🚀 多工程流系统演示")
    print("="*60)

    # 创建协调器
    coordinator = MultiWorkflowCoordinator(max_parallel_workflows=5)

    # 开发工程流
    print("\n📦 创建开发工程流...")
    dev_workflow = DevWorkflow("feature_dev")
    dev_workflow.add_task(Task(
        task_id="code_generation",
        name="代码生成",
        description="生成功能代码",
        priority=TaskPriority.CRITICAL,
        agent_type="implementation"
    ))

    # 测试工程流（依赖开发）
    print("📦 创建测试工程流...")
    test_workflow = TestWorkflow("feature_test")
    test_workflow.add_dependency("feature_dev")
    test_workflow.add_task(Task(
        task_id="unit_tests",
        name="单元测试",
        description="编写和运行单元测试",
        priority=TaskPriority.HIGH,
        agent_type="testing"
    ))

    # 文档工程流（依赖开发）
    print("📦 创建文档工程流...")
    doc_workflow = DocWorkflow("feature_doc")
    doc_workflow.add_dependency("feature_dev")
    doc_workflow.add_task(Task(
        task_id="api_docs",
        name="API文档",
        description="生成API文档",
        priority=TaskPriority.NORMAL,
        agent_type="documentation"
    ))

    # 优化工程流（独立运行）
    print("📦 创建优化工程流...")
    opt_workflow = OptimizeWorkflow("code_optimize")
    opt_workflow.add_task(Task(
        task_id="analyze_complexity",
        name="复杂度分析",
        description="分析代码复杂度",
        priority=TaskPriority.NORMAL,
        agent_type="architecture"
    ))

    # 注册所有工程流
    for wf in [dev_workflow, test_workflow, doc_workflow, opt_workflow]:
        coordinator.register_workflow(wf)

    print("\n✅ 工程流注册完成")

    # 显示依赖关系
    print("\n🔗 依赖关系:")
    for wf in coordinator.list_workflows():
        if wf.dependencies:
            print(f"   {wf.workflow_id} ← {wf.dependencies}")

    # 显示状态
    print("\n📊 工程流状态:")
    status = coordinator.get_status()
    for wf_id, info in status['workflows'].items():
        print(f"   {wf_id}: {info['type']} ({info['status']})")

    # 执行（混合策略：关键路径优先）
    print("\n🔄 执行工程流（混合策略）...")
    results = await coordinator.execute_all(
        strategy=ExecutionStrategy.HYBRID
    )

    # 结果
    print("\n📊 执行结果:")
    for wf_id, result in results.items():
        status = "✅" if result.success else "❌"
        print(f"   {status} {wf_id}: {result.status.value}")
        if result.execution_time > 0:
            print(f"      执行时间: {result.execution_time:.2f}s")

    print("\n✅ 多工程流演示完成！")


async def demo_workflow_promotion():
    """演示工程流提升"""
    print("\n" + "="*60)
    print("🚀 工程流提升演示")
    print("="*60)

    coordinator = MultiWorkflowCoordinator()

    # 创建快速工程流
    print("\n📦 创建快速工程流（原型）...")
    fast = FastTrackWorkflow("prototype")

    fast.add_task(Task(
        task_id="proto_code",
        name="原型代码",
        description="快速原型开发",
        priority=TaskPriority.HIGH,
        agent_type="implementation"
    ))

    coordinator.register_workflow(fast)

    # 执行快速工程流
    print("\n🔄 执行快速工程流...")
    result = await fast.execute({})

    if result.success:
        print(f"✅ 原型成功: {fast.workflow_id}")

        # 检查是否可以提升
        if fast.can_promote_to(WorkflowType.STABLE):
            print("\n⬆️  提升到稳定工程流...")

            # 提升到稳定流
            stable = coordinator.promote_workflow(
                from_workflow_id="prototype",
                to_type=WorkflowType.STABLE,
                new_workflow_id="production"
            )

            if stable:
                print(f"✅ 提升成功: {stable.workflow_id}")
                print(f"   类型: {stable.workflow_type.value}")
                print(f"   优先级: {stable.priority.value}")

                # 添加生产级别的任务
                stable.add_task(Task(
                    task_id="full_validation",
                    name="完整验证",
                    description="生产级别的完整验证",
                    priority=TaskPriority.CRITICAL,
                    agent_type="testing"
                ))

                print("\n🔄 执行稳定工程流...")
                result = await stable.execute({})

                if result.success:
                    print("✅ 生产就绪！")
                else:
                    print(f"❌ 验证失败: {result.error}")

    print("\n✅ 工程流提升演示完成！")


async def demo_custom_config():
    """演示自定义配置"""
    print("\n" + "="*60)
    print("🚀 自定义配置演示")
    print("="*60)

    # 创建自定义配置
    print("\n⚙️  创建自定义配置...")

    config = WorkflowConfig(
        skip_steps=["e2e_test", "performance_test"],
        required_steps=["unit_test", "integration_test"],
        quality_thresholds={
            "test_coverage": 0.60,
            "code_quality": 8.0,
            "complexity_limit": 10
        },
        auto_commit=False,
        bypass_hooks=False,
        parallel_execution=True
    )

    print(f"   配置:")
    print(f"   - 跳过: {config.skip_steps}")
    print(f"   - 必需: {config.required_steps}")
    print(f"   - 覆盖率目标: {config.quality_thresholds['test_coverage']*100}%")
    print(f"   - 代码质量: {config.quality_thresholds['code_quality']}/10")

    # 创建使用自定义配置的工程流
    print("\n📦 创建工程流（自定义配置）...")
    from lingflow.workflow.multi_workflow import BaseWorkflow

    custom_wf = BaseWorkflow(
        workflow_id="custom_workflow",
        workflow_type=WorkflowType.DEV,
        priority=WorkflowPriority.HIGH,
        config=config
    )

    custom_wf.add_task(Task(
        task_id="custom_task",
        name="自定义任务",
        description="使用自定义配置的任务",
        priority=TaskPriority.HIGH,
        agent_type="implementation"
    ))

    print(f"\n✅ 自定义工程流创建完成")
    print(f"   ID: {custom_wf.workflow_id}")
    print(f"   类型: {custom_wf.workflow_type.value}")
    print(f"   优先级: {custom_wf.priority.value}")

    # 验证配置
    if custom_wf.validate():
        print("\n✅ 配置验证通过")

    print("\n✅ 自定义配置演示完成！")


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("🎯 lingflow 多工程流系统 - 完整演示")
    print("="*60)

    demos = [
        ("双工程流系统", demo_dual_workflow),
        ("多工程流系统", demo_multi_workflow),
        ("工程流提升", demo_workflow_promotion),
        ("自定义配置", demo_custom_config),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        print(f"\n{'='*60}")
        print(f"演示 {i}/{len(demos)}: {name}")
        print('='*60)

        try:
            await demo_func()
        except Exception as e:
            print(f"\n❌ 演示失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("🎉 所有演示完成！")
    print("="*60)

    print("\n💡 提示:")
    print("   - 双工程流: 适合快速开发 + 稳定发布")
    print("   - 多工程流: 适合专业分工、并行协作")
    print("   - 工程流提升: 快速验证后升级到生产")
    print("   - 自定义配置: 根据需求调整质量阈值")

    print("\n📚 更多信息:")
    print("   - 设计文档: docs/architecture/MULTI_WORKFLOW_DESIGN.md")
    print("   - 快速指南: docs/architecture/MULTI_WORKFLOW_GUIDE.md")
    print("   - 核心实现: lingflow/workflow/multi_workflow.py")

    print("\n" + "="*60)


if __name__ == "__main__":
    asyncio.run(main())
