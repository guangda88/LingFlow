#!/usr/bin/env python3
import click
import yaml
import json
from lingflow import LingFlow

lf = LingFlow()

@click.group()
def cli():
    pass

@cli.command()
@click.argument('skill')
@click.option('--params', '-p', help='参数（JSON格式）')
def run(skill, params):
    """执行单个技能"""
    params_dict = json.loads(params) if params else {}
    result = lf.run_skill(skill, params_dict)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))

@cli.command()
@click.argument('workflow_file')
def workflow(workflow_file):
    """执行工作流文件（YAML格式）"""
    result = lf.run_workflow_file(workflow_file)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))

@cli.command('list-skills')
def list_skills():
    """列出所有可用技能"""
    skills = lf._coordinator.list_skills()
    for skill in skills:
        click.echo(f"  - {skill}")

if __name__ == '__main__':
    cli()
