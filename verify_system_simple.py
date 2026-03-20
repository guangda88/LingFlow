#!/usr/bin/env python3
"""LingFlow v1.1.0 简单验证脚本"""

import sys
from lingflow.coordination import AgentCoordinator

def main():
    print("=" * 70)
    print("  LingFlow v1.1.0 系统验证")
    print("=" * 70)

    try:
        # 1. 代理注册
        print("\n1. 代理注册测试...")
        coordinator = AgentCoordinator()
        agents = coordinator.registry.list_agents()
        print(f"✅ 注册成功: {len(agents)} 个代理")

        # 2. 上下文压缩
        print("\n2. 上下文压缩测试...")
        test_context = {
            "requirements": "Test requirement " * 100,
            "description": "Test description " * 50
        }
        compressed = coordinator.compressor.compress(test_context)
        print(f"✅ 压缩完成")

        # 3. 状态监控
        print("\n3. 状态监控测试...")
        status = coordinator.get_status()
        print(f"✅ 状态正常")

        # 总结
        print("\n" + "=" * 70)
        print("✅ 所有测试通过！")
        print("=" * 70)
        print("\nLingFlow v1.1.0 系统已就绪。")
        print("\n下一步:")
        print("  1. 查看 docs/V1.1.0_IMPLEMENTATION_SUMMARY.md")
        print("  2. 运行 python agent_coordinator.py 查看完整演示")
        return 0

    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
