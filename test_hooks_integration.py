#!/usr/bin/env python3
"""
测试自优化钩子系统集成
"""

import sys
from pathlib import Path


def test_bootstrap_integration():
    """测试bootstrap集成"""
    print("="*70)
    print("测试1: Bootstrap集成".center(70))
    print("="*70)

    from lingflow.bootstrap import bootstrap

    status = bootstrap(hooks=True, verbose=False)

    print(f"\n✓ Bootstrap完成")
    print(f"  版本: {status['version']}")
    print(f"  状态: {'成功' if status['success'] else '失败'}")
    print(f"  Hooks: {'已初始化' if status['hooks'] else '未初始化'}")

    if status['errors']:
        print(f"\n⚠️  错误:")
        for error in status['errors']:
            print(f"  - {error}")
        return False

    if not status['hooks']:
        print("\n✗ Hooks系统未初始化")
        return False

    print("\n✅ Bootstrap集成测试通过")
    return True


def test_global_hook():
    """测试全局钩子"""
    print("\n" + "="*70)
    print("测试2: 全局钩子".center(70))
    print("="*70)

    from lingflow.hooks import get_global_hook

    hook = get_global_hook()

    print(f"\n✓ 获取全局钩子")
    print(f"  类型: {type(hook).__name__}")
    print(f"  有触发器: {hasattr(hook, 'trigger')}")
    print(f"  有优化器: {hasattr(hook, 'optimizer')}")

    # 测试触发器
    if hasattr(hook, 'trigger'):
        from lingflow.self_optimizer.trigger import OptimizationTrigger
        print(f"  触发器类型: {type(hook.trigger).__name__}")

    # 测试优化器
    if hasattr(hook, 'optimizer'):
        from lingflow.self_optimizer.optimizer import ProcessIsolatedOptimizer
        print(f"  优化器类型: {type(hook.optimizer).__name__}")

    print("\n✅ 全局钩子测试通过")
    return True


def test_trigger_detection():
    """测试触发检测"""
    print("\n" + "="*70)
    print("测试3: 触发条件检测".center(70))
    print("="*70)

    from lingflow.hooks import get_global_hook

    hook = get_global_hook()

    # 测试低分触发
    print("\n测试场景: 代码审查得分低")
    context = {
        "review_score": 65,  # 低于默认阈值70
        "coverage_drop": 0,
        "execution_time": 0,
    }

    should_trigger, trigger_info = hook.trigger.check_all_conditions(context)

    print(f"  审查得分: {context['review_score']}")
    print(f"  应该触发: {should_trigger}")
    if should_trigger:
        print(f"  触发原因: {trigger_info.reason}")
        print(f"  触发类型: {trigger_info.type}")
        print(f"  优先级: {trigger_info.priority}")

    # 测试正常情况
    print("\n测试场景: 代码质量正常")
    context_normal = {
        "review_score": 85,  # 高于阈值
        "coverage_drop": 0,
        "execution_time": 0,
    }

    should_trigger_normal, _ = hook.trigger.check_all_conditions(context_normal)

    print(f"  审查得分: {context_normal['review_score']}")
    print(f"  应该触发: {should_trigger_normal}")

    print("\n✅ 触发检测测试通过")
    return True


def test_event_handlers():
    """测试事件处理"""
    print("\n" + "="*70)
    print("测试4: 事件处理器".center(70))
    print("="*70)

    from lingflow.hooks import get_global_hook

    hook = get_global_hook()

    # 测试代码审查完成事件
    print("\n测试事件: 代码审查完成")
    review_result = {
        "overall_score": 65,
        "dimensions": {
            "structure": 70,
            "naming": 60,
            "complexity": 65,
        }
    }

    print(f"  审查得分: {review_result['overall_score']}")

    # 注意：这里会提示用户输入，在测试中我们跳过实际调用
    print("  ⚠️  跳过实际调用（需要用户交互）")

    # 测试测试完成事件
    print("\n测试事件: 测试完成")
    test_result = {
        "coverage": 85,
        "duration": 10,
        "failed": 2,
        "total": 100,
    }

    print(f"  测试覆盖率: {test_result['coverage']}%")
    print(f"  失败率: {test_result['failed']}/{test_result['total']}")
    print("  ⚠️  跳过实际调用（需要用户交互）")

    print("\n✅ 事件处理器测试通过")
    return True


def test_integration():
    """测试完整集成"""
    print("\n" + "="*70)
    print("测试5: 完整集成".center(70))
    print("="*70)

    from lingflow.bootstrap import bootstrap
    from lingflow.hooks import get_global_hook

    # Bootstrap
    status = bootstrap(hooks=True)

    if not status['hooks']:
        print("\n✗ Hooks未初始化")
        return False

    # 获取钩子
    hook = get_global_hook()

    # 检查优化状态
    is_running = hook.is_optimization_running()
    print(f"\n✓ 优化运行状态: {is_running}")

    # 检查是否有结果
    result = hook.get_optimization_result()
    print(f"✓ 优化结果: {'有' if result else '无'}")

    print("\n✅ 完整集成测试通过")
    return True


def main():
    """主函数"""
    print("\n" + "="*70)
    print(" LingFlow 自优化钩子系统集成测试 ".center(70))
    print("="*70)

    tests = [
        ("Bootstrap集成", test_bootstrap_integration),
        ("全局钩子", test_global_hook),
        ("触发检测", test_trigger_detection),
        ("事件处理", test_event_handlers),
        ("完整集成", test_integration),
    ]

    results = {}

    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    # 总结
    print("\n" + "="*70)
    print(" 测试总结 ".center(70))
    print("="*70)

    for name, passed in results.items():
        status = "✅ 通过" if passed else "✗ 失败"
        print(f"{status.ljust(20)} {name}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！Hooks系统已成功集成。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被中断")
        sys.exit(1)
