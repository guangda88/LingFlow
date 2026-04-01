"""LingFlow MCP Server CLI

命令行入口，用于启动 MCP 服务器。
"""

import asyncio
import sys
from pathlib import Path

import click


@click.group()
def cli():
    """LingFlow MCP Server - 将 LingFlow 工程流能力暴露为 MCP 工具"""
    pass


@cli.command()
@click.option("--host", default="localhost", help="监听地址")
@click.option("--port", default=8000, type=int, help="监听端口")
@click.option("--work-dir", type=click.Path(exists=True), help="工作目录")
@click.option("--log-level", default="INFO", help="日志级别")
def run(host, port, work_dir, log_level):
    """启动 MCP 服务器"""
    import logging

    # 配置日志
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    from lingflow_mcp.server import create_server
    from lingflow_mcp.config import ServerConfig

    # 加载配置
    config = ServerConfig.from_env()

    if work_dir:
        config.work_dir = Path(work_dir)

    config.log_level = log_level

    # 创建并启动服务器
    server = create_server(server_config=config)

    click.echo(
        click.style(
            f"🚀 LingFlow MCP Server 启动中...",
            fg="green",
            bold=True,
        )
    )
    click.echo(f"监听: {host}:{port}")
    click.echo(f"工作目录: {config.work_dir}")
    click.echo(f"日志级别: {log_level}")
    click.echo("")

    # 运行服务器
    asyncio.run(server.run(host, port))


@cli.command()
def tools():
    """列出所有可用工具"""
    from lingflow_mcp.server import create_server
    from lingflow_mcp.config import ServerConfig

    config = ServerConfig.from_env()
    server = create_server(server_config=config)

    tools = server.tool_registry.get_mcp_tools()

    click.echo(
        click.style(
            f"📋 LingFlow MCP 工具列表 (共 {len(tools)} 个)",
            fg="blue",
            bold=True,
        )
    )
    click.echo("")

    for tool in tools:
        click.echo(click.style(f"• {tool.name}", fg="cyan", bold=True))
        click.echo(f"  {tool.description}")
        click.echo("")


@cli.command()
def test():
    """测试 MCP 服务器连接"""
    import asyncio

    from lingflow_mcp.server import create_server
    from lingflow_mcp.config import ServerConfig

    async def run_test():
        config = ServerConfig.from_env()
        server = create_server(server_config=config)

        # 测试工具列表
        tools = server.tool_registry.get_mcp_tools()

        click.echo(
            click.style(
                f"✅ MCP 服务器测试通过",
                fg="green",
                bold=True,
            )
        )
        click.echo(f"工具数量: {len(tools)}")
        click.echo("")

        # 列出工具类别
        categories = {}
        for tool in tools:
            # 从工具名称推断类别
            if tool.name.startswith("list_"):
                category = "查询"
            elif tool.name.startswith("run_"):
                category = "执行"
            elif tool.name.startswith("get_"):
                category = "获取"
            elif tool.name.startswith("create_"):
                category = "创建"
            else:
                category = "其他"

            categories[category] = categories.get(category, 0) + 1

        click.echo("工具分类:")
        for category, count in categories.items():
            click.echo(f"  {category}: {count}")

    asyncio.run(run_test())


def main():
    """主入口"""
    cli()


if __name__ == "__main__":
    main()
