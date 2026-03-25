#!/usr/bin/env python3
"""LingFlow CLI Interface.

Provides command-line interface for executing LingFlow skills and workflows.
Uses Click for CLI argument parsing and command organization.
"""
import json

import click

from lingflow import LingFlow

lf = LingFlow()


@click.group()
def cli():
    pass


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
    skills = lf._coordinator.list_skills()
    for skill in skills:
        click.echo(f"  - {skill}")


if __name__ == "__main__":
    cli()
