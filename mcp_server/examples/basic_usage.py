"""LingFlow MCP Server 基础使用示例

演示如何直接调用 MCP 服务器工具（不通过 AI 客户端）
"""

import asyncio
import json
from pathlib import Path


async def example_list_skills():
    """示例 1: 列出所有技能"""
    from lingflow_mcp import create_server

    server = create_server()

    # 调用工具
    result = await server._execute_tool(
        "list_skills",
        {"layer": "L1"}  # 只列出基础技能
    )

    print("🔧 基础技能列表:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def example_review_code():
    """示例 2: 代码审查"""
    from lingflow_mcp import create_server

    server = create_server()

    # 创建示例文件
    test_file = Path("/tmp/example.py")
    test_file.write_text("""
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    for i in range(10):
        print(fibonacci(i))
""")

    # 执行代码审查
    result = await server._execute_tool(
        "review_code",
        {
            "target_path": str(test_file),
            "dimensions": ["complexity", "style", "documentation"],
        }
    )

    print("📊 代码审查结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def example_github_trends():
    """示例 3: 获取 GitHub 趋势"""
    from lingflow_mcp import create_server

    server = create_server()

    # 获取 AI 相关的 GitHub 趋势
    result = await server._execute_tool(
        "get_github_trends",
        {
            "keywords": ["python", "ai", "llm"],
            "limit": 5,
            "min_stars": 1000,
        }
    )

    print("📈 GitHub 趋势项目:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def example_run_skill():
    """示例 4: 执行技能"""
    from lingflow_mcp import create_server

    server = create_server()

    # 执行代码分析技能
    result = await server._execute_tool(
        "run_skill",
        {
            "skill_name": "code_analysis",
            "params": {
                "target": "mcp_server/",
                "depth": "quick",
            }
        }
    )

    print("⚡ 技能执行结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


async def example_async_workflow():
    """示例 5: 异步工作流执行"""
    from lingflow_mcp import create_server

    server = create_server()

    # 提交工作流（异步）
    result = await server._execute_tool(
        "run_workflow",
        {
            "workflow_id": "feature-development",
            "params": {
                "feature": "add-user-auth",
            }
        }
    )

    print("🚀 工作流已提交:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("task_id"):
        task_id = result["task_id"]

        # 轮询状态
        import asyncio

        for i in range(5):
            await asyncio.sleep(2)

            status = await server._execute_tool(
                "get_task_status",
                {"task_id": task_id}
            )

            print(f"📊 状态更新: {status['status']}")

            if status["status"] in ["completed", "failed"]:
                print("✅ 工作流完成!")
                print(json.dumps(status, ensure_ascii=False, indent=2))
                break


async def main():
    """运行所有示例"""
    print("=" * 60)
    print("LingFlow MCP Server 使用示例")
    print("=" * 60)
    print()

    # 示例 1: 列出技能
    print("\n### 示例 1: 列出基础技能 ###\n")
    await example_list_skills()

    print("\n" + "=" * 60 + "\n")

    # 示例 2: 代码审查
    print("\n### 示例 2: 代码审查 ###\n")
    await example_review_code()

    print("\n" + "=" * 60 + "\n")

    # 示例 3: GitHub 趋势
    print("\n### 示例 3: GitHub 趋势 ###\n")
    await example_github_trends()

    print("\n" + "=" * 60 + "\n")

    # 示例 4: 执行技能
    print("\n### 示例 4: 执行技能 ###\n")
    await example_run_skill()

    print("\n" + "=" * 60 + "\n")

    # 示例 5: 异步工作流
    print("\n### 示例 5: 异步工作流 ###\n")
    await example_async_workflow()

    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
