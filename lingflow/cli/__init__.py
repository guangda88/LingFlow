"""灵通 (lingflow) CLI Interface

众智混元，万法灵通

Provides command-line interface for executing lingflow skills and workflows.
Uses Click for CLI argument parsing and command organization.
"""

import json
from pathlib import Path

import click

from lingflow import lingflow
from lingflow.cli.analyze import analyze
from lingflow.cli.feedback import feedback
from lingflow.cli.learn import learn
from lingflow.cli.optimize import optimize
from lingflow.cli.stream import create_project, list_projects, stream
from lingflow.cli.test import test

__all__ = ["cli", "run", "workflow", "list_skills", "init", "config_cmd"]

lf = lingflow()


def _get_version() -> str:
    try:
        from importlib.metadata import version

        return version("lingflow-core")
    except Exception:
        vfile = Path(__file__).parent.parent.parent / "VERSION"
        if vfile.exists():
            return vfile.read_text().strip()
        return "unknown"


@click.group()
@click.version_option(version=_get_version(), prog_name="lingflow")
def cli() -> None:
    """灵通 (lingflow) CLI 主入口 - 众智混元，万法灵通"""


@cli.command()
@click.argument("skill")
@click.option("--params", "-p", help="参数（JSON格式）")
def run(skill, params):
    """执行单个技能"""
    if params:
        try:
            # Add size limit to prevent DoS
            if len(params) > 10_000_000:  # 10MB limit
                raise ValueError("Parameters too large (max 10MB)")
            params_dict = json.loads(params)
        except json.JSONDecodeError as e:
            click.echo(f"Invalid JSON: {e}", err=True)
            raise click.Abort()
        except ValueError as e:
            click.echo(f"Validation error: {e}", err=True)
            raise click.Abort()
    else:
        params_dict = {}
    result = lf.run_skill(skill, params_dict)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@cli.command()
@click.argument("workflow_file")
def workflow(workflow_file):
    """执行工作流文件（YAML格式）"""
    result = lf.run_workflow_file(workflow_file)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))


@cli.command("list-skills")
def list_skills():
    """列出所有可用技能"""
    skills = lf.list_skills()
    for skill in skills:
        click.echo(f"  - {skill}")


@cli.command()
def init():
    """初始化 lingflow 工作目录"""
    lingflow_dir = Path(".lingflow")
    lingflow_dir.mkdir(exist_ok=True)
    (lingflow_dir / "config").mkdir(exist_ok=True)
    (lingflow_dir / "sessions").mkdir(exist_ok=True)
    (lingflow_dir / "logs").mkdir(exist_ok=True)

    config_file = lingflow_dir / "config" / "config.yaml"
    if not config_file.exists():
        config_file.write_text(
            "# lingflow configuration\n"
            "# Override with LINGFLOW_ env vars\n"
            "workflow:\n  max_parallel: 2\n  max_iterations: 100\n"
            "skills:\n  path: skills\n  default_timeout: 30\n"
            "compression:\n  enabled: true\n"
            "logging:\n  level: INFO\n",
            encoding="utf-8",
        )
        click.echo(f"Created default config: {config_file}")
    click.echo("lingflow 工作目录已初始化: .lingflow/")


@cli.command("config")
@click.argument("key", required=False)
@click.argument("value", required=False)
@click.option("--list", "list_all", is_flag=True, help="列出所有配置")
def config_cmd(key, value, list_all):
    """查看或设置配置"""
    from lingflow.common.config import config_manager

    if list_all:
        click.echo(json.dumps(config_manager.config, indent=2, ensure_ascii=False))
    elif key and value:
        config_manager.set(key, value)
        config_manager.save()
        click.echo(f"Set {key} = {value}")
    elif key:
        v = config_manager.get(key)
        if v is not None:
            click.echo(json.dumps(v, indent=2, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v))
        else:
            click.echo(f"Key not found: {key}", err=True)
    else:
        click.echo("Usage: lingflow config KEY [VALUE] or --list")


# 添加命令组
cli.add_command(analyze)
cli.add_command(feedback)
cli.add_command(learn)
cli.add_command(optimize)
cli.add_command(stream)
cli.add_command(list_projects)
cli.add_command(create_project)
cli.add_command(test)


if __name__ == "__main__":  # pragma: no cover
    cli()
