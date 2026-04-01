#!/usr/bin/env python3
"""测试 LingFlow MCP 服务器功能"""

import asyncio
import sys
import os

# 添加路径
sys.path.insert(0, '/home/ai/LingFlow')
sys.path.insert(0, '/home/ai/LingFlow/mcp_server')


async def test_basic_functionality():
    """测试基础功能"""
    print("=" * 60)
    print("🧪 测试 1: 基础功能测试")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server
        from lingflow_mcp.config import ServerConfig

        config = ServerConfig.from_env()
        server = create_server(server_config=config)

        print(f"✅ 服务器创建成功")
        print(f"   工具数量: {len(server.tool_registry.get_mcp_tools())}")

        return True
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False


async def test_tool_registry():
    """测试工具注册"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: 工具注册测试")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server

        server = create_server()
        tools = server.tool_registry.get_mcp_tools()

        print(f"✅ 工具注册测试通过")
        print(f"\n已注册工具 ({len(tools)} 个):")

        for tool in tools:
            print(f"  • {tool.name}")
            print(f"    {tool.description[:60]}...")

        return True
    except Exception as e:
        print(f"❌ 工具注册测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_list_skills():
    """测试列出技能"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: 列出技能测试")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server

        server = create_server()
        result = await server._execute_tool("list_skills", {})

        if result.get("success"):
            print(f"✅ 列出技能成功")
            print(f"   技能总数: {result.get('total', 0)}")

            # 显示前 5 个技能
            skills = result.get("skills", [])[:5]
            if skills:
                print(f"\n前 5 个技能:")
                for skill in skills:
                    print(f"  • {skill.get('name', 'Unknown')}")

            return True
        else:
            print(f"⚠️  列出技能返回失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 列出技能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_code_review():
    """测试代码审查"""
    print("\n" + "=" * 60)
    print("🧪 测试 4: 代码审查测试")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server
        import tempfile

        server = create_server()

        # 创建测试文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    for i in range(10):
        print(fibonacci(i))
""")
            test_file = f.name

        # 执行代码审查
        result = await server._execute_tool(
            "review_code",
            {
                "target_path": test_file,
                "dimensions": ["complexity", "style"]
            }
        )

        # 清理
        os.unlink(test_file)

        if result.get("success"):
            print(f"✅ 代码审查成功")
            report = result.get("report", {})
            print(f"   目标: {result.get('target')}")
            if isinstance(report, dict):
                print(f"   审查完成")
            return True
        else:
            print(f"⚠️  代码审查返回失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 代码审查测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_async_tasks():
    """测试异步任务"""
    print("\n" + "=" * 60)
    print("🧪 测试 5: 异步任务测试")
    print("=" * 60)

    try:
        from lingflow_mcp import create_server

        server = create_server()

        # 测试异步任务创建（工作流）
        result = await server._execute_tool(
            "run_workflow",
            {
                "workflow_id": "test_workflow",
                "params": {}
            }
        )

        if "task_id" in result:
            task_id = result["task_id"]
            print(f"✅ 异步任务创建成功")
            print(f"   任务 ID: {task_id}")
            print(f"   状态: {result.get('status')}")

            # 测试状态查询
            status = await server._execute_tool(
                "get_task_status",
                {"task_id": task_id}
            )

            print(f"\n✅ 状态查询成功")
            print(f"   任务状态: {status.get('status')}")

            return True
        else:
            print(f"⚠️  异步任务创建失败: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 异步任务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n🚀 LingFlow MCP Server 测试套件")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(await test_basic_functionality())
    results.append(await test_tool_registry())
    results.append(await test_list_skills())
    results.append(await test_code_review())
    results.append(await test_async_tasks())

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
