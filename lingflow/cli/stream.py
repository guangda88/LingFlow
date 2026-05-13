"""Stream command for lingflow - multi-project streaming responses."""

import asyncio
import json
from pathlib import Path

import click

from lingflow import lingflow

lf = lingflow()


@click.command()
@click.option("--project", "-p", default="default", help="项目ID（工程流）")
@click.option("--message", "-m", required=True, help="要发送的消息")
@click.option("--thread", "-t", help="线程ID")
@click.option("--timeout", default=120, help="超时时间（秒）")
def stream(project, message, thread, timeout):
    """流式响应 - 支持多工程流

    用于实时流式返回lingflow的响应内容。
    """
    async def _stream():
        # 发送特殊标记以标识流开始
        click.echo("STREAM_START")

        try:
            # 这里模拟流式响应
            # 在实际实现中，应该从lingflow获取流式输出
            result = lf.run_skill("default", {"message": message})

            # 将结果分割成块来模拟流式输出
            result_str = json.dumps(result, ensure_ascii=False)

            # 模拟打字机效果
            chunk_size = 20  # 每次输出20个字符
            for i in range(0, len(result_str), chunk_size):
                chunk = result_str[i:i + chunk_size]
                click.echo(chunk)
                await asyncio.sleep(0.05)  # 模拟网络延迟

        except Exception as e:
            click.echo(f"ERROR: {e}", err=True)

        # 发送结束标记
        click.echo("STREAM_END")

    asyncio.run(_stream())


@click.command()
def list_projects():
    """列出所有可用项目（工程流）"""
    # 获取项目列表
    projects_dir = Path.home() / ".lingflow" / "projects"

    if not projects_dir.exists():
        projects_dir.mkdir(parents=True, exist_ok=True)

    projects = [d.name for d in projects_dir.iterdir() if d.is_dir()]

    if not projects:
        click.echo("未找到项目，使用默认项目: default")
        return

    click.echo("可用项目:")
    for proj in projects:
        click.echo(f"  - {proj}")


@click.command()
@click.argument("project_id")
@click.option("--name", help="项目名称")
def create_project(project_id, name):
    """创建新项目（工程流）"""
    projects_dir = Path.home() / ".lingflow" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

    project_path = projects_dir / project_id
    if project_path.exists():
        click.echo(f"项目已存在: {project_id}", err=True)
        raise click.Abort()

    project_path.mkdir()
    config = {
        "project_id": project_id,
        "name": name or project_id,
        "created_at": Path(project_path).stat().st_mtime,
    }

    config_file = project_path / "config.json"
    config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    click.echo(f"项目已创建: {project_id}")


# 导出命令
__all__ = ["stream", "list_projects", "create_project"]
