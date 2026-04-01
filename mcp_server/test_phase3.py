#!/usr/bin/env python3
"""测试 LingFlow MCP Server Phase 3 功能"""

import asyncio
import sys
import os

# 添加路径
sys.path.insert(0, '/home/ai/LingFlow')
sys.path.insert(0, '/home/ai/LingFlow/mcp_server')


async def test_health_check():
    """测试健康检查"""
    print("=" * 60)
    print("🧪 测试 1: 健康检查")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server

        server = create_server()
        result = await server._execute_tool(
            "get_health_status",
            {"checks": ["disk", "memory", "cpu"]}
        )

        if result.get("success"):
            print(f"✅ 健康检查成功")
            print(f"   总体状态: {result.get('overall_status')}")
            checks = result.get("checks", {})
            for check_name, check_data in checks.items():
                status = check_data.get("status", "unknown")
                print(f"   {check_name}: {status}")
            return True
        else:
            print(f"⚠️  健康检查失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 健康检查测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_metrics():
    """测试性能指标"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: 性能指标")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server

        server = create_server()
        result = await server._execute_tool(
            "get_metrics",
            {"metric_names": ["cpu", "memory"]}
        )

        if result.get("success"):
            print(f"✅ 性能指标获取成功")
            metrics = result.get("metrics", {})
            for name, data in metrics.items():
                print(f"   {name}:")
                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"     {key}: {value}")
            return True
        else:
            print(f"⚠️  性能指标获取失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 性能指标测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_anomaly_detection():
    """测试异常检测"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: 异常检测")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server

        server = create_server()

        # 检测 CPU 异常
        result = await server._execute_tool(
            "detect_anomaly",
            {
                "metric_name": "cpu",
                "threshold": 90.0
            }
        )

        if result.get("success"):
            print(f"✅ 异常检测成功")
            print(f"   指标: {result.get('metric_name')}")
            print(f"   是否异常: {result.get('is_anomaly')}")
            if "analysis" in result:
                analysis = result["analysis"]
                print(f"   平均值: {analysis.get('average')}")
                print(f"   建议: {result.get('recommendation')}")
            return True
        else:
            print(f"⚠️  异常检测失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 异常检测测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_run_tests():
    """测试运行测试"""
    print("\n" + "=" * 60)
    print("🧪 测试 4: 运行测试")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server

        server = create_server()

        # 运行快速测试
        result = await server._execute_tool(
            "run_tests",
            {
                "test_path": "mcp_server/tests/",
                "test_type": "unit",
                "verbose": False,
                "coverage": False
            }
        )

        if result.get("success"):
            print(f"✅ 测试运行成功")
            stats = result.get("stats", {})
            print(f"   总测试数: {stats.get('total', 0)}")
            print(f"   通过: {stats.get('passed', 0)}")
            print(f"   失败: {stats.get('failed', 0)}")
            print(f"   执行时间: {stats.get('duration', 0):.2f}s")
            return True
        else:
            print(f"⚠️  测试运行失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 测试运行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_count():
    """测试工具总数"""
    print("\n" + "=" * 60)
    print("🧪 测试 5: 工具总数验证")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server

        server = create_server()
        tools = server.tool_registry.get_mcp_tools()

        expected_count = 21  # Phase 1: 5, Phase 2: 10, Phase 3: 6
        actual_count = len(tools)

        print(f"   预期工具数: {expected_count}")
        print(f"   实际工具数: {actual_count}")

        if actual_count >= expected_count:
            print(f"✅ 工具数量验证通过")

            # 按类别统计
            categories = {}
            for tool in tools:
                if tool.name.startswith("list_"):
                    category = "查询"
                elif tool.name.startswith("run_"):
                    category = "执行"
                elif tool.name.startswith("get_"):
                    category = "获取"
                elif tool.name.startswith("create_"):
                    category = "创建"
                elif tool.name.startswith("update_"):
                    category = "更新"
                elif tool.name.startswith("link_"):
                    category = "关联"
                elif tool.name.startswith("generate_"):
                    category = "生成"
                else:
                    category = "其他"

                categories[category] = categories.get(category, 0) + 1

            print(f"\n   工具分类:")
            for category, count in categories.items():
                print(f"     {category}: {count}")

            return True
        else:
            print(f"⚠️  工具数量不足: {actual_count} < {expected_count}")
            return False

    except Exception as e:
        print(f"❌ 工具数量验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n🚀 LingFlow MCP Server Phase 3 测试套件")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(await test_health_check())
    results.append(await test_metrics())
    results.append(await test_anomaly_detection())
    results.append(await test_run_tests())
    results.append(await test_tool_count())

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"总测试数: {total}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
