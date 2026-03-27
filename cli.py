#!/usr/bin/env python3
"""灵通 (LingFlow) 命令行接口

众智混元，万法灵通

提供 CLI 命令来执行技能和工作流。

Usage:
    lingflow run <skill> [--params JSON]
    lingflow workflow <workflow_file>
    lingflow list-skills
    lingflow context status
    lingflow context compress

Example:
    lingflow run code-review --params '{"file": "main.py"}'
    lingflow workflow my_workflow.yaml
"""

import click
import json
from lingflow import LingFlow

lf = LingFlow()

# 启用智能上下文压缩 (模块导入时自动启用)
from lingflow.compression import enable_smart_compression
enable_smart_compression()


@click.group()
def cli():
    """灵通 (LingFlow) - 众智混元，万法灵通

    这是一个命令行工具，用于执行和管理灵通的技能和工作流。
    """

@cli.command()
@click.argument('skill')
@click.option('--params', '-p', help='技能参数（JSON格式字符串）')
def run(skill, params):
    """执行单个技能

    \b
    SKILL: 要执行的技能名称（如 code-review, test-runner）

    \b
    PARAMS: 可选的 JSON 格式参数字符串
           示例: --params '{"file": "main.py", "strict": true}'

    \b
    示例:
        lingflow run code-review
        lingflow run code-review --params '{"file": "main.py"}'
        lingflow run database-export -p '{"query": "SELECT * FROM users"}'

    \b
    返回值:
        以 JSON 格式输出执行结果
    """
    try:
        params_dict = json.loads(params) if params else {}
    except json.JSONDecodeError as e:
        click.echo(f"错误: 参数格式无效 - {e}", err=True)
        raise click.Abort()

    result = lf.run_skill(skill, params_dict)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))

@cli.command()
@click.argument('workflow_file')
def workflow(workflow_file):
    """执行工作流文件

    \b
    WORKFLOW_FILE: YAML 格式的工作流文件路径

    \b
    工作流文件格式示例:
        \b
        name: my_workflow
        skills:
          - name: code-review
            params:
              file: main.py
          - name: test-runner
            params:
              coverage: true

    \b
    示例:
        lingflow workflow my_workflow.yaml
        lingflow workflow workflows/deploy.yaml

    \b
    返回值:
        以 JSON 格式输出工作流执行结果
    """
    result = lf.run_workflow_file(workflow_file)
    click.echo(json.dumps(result, indent=2, ensure_ascii=False))

@cli.command('list-skills')
def list_skills():
    """列出所有可用技能

    \b
    显示当前已注册的所有技能名称。

    \b
    示例:
        lingflow list-skills

    \b
    输出:
        - code-review
        - test-runner
        - database-export
        ...
    """
    skills = lf._coordinator.list_skills()
    if not skills:
        click.echo("未找到可用技能")
    else:
        click.echo(f"可用技能 ({len(skills)} 个):")
        for skill in skills:
            click.echo(f"  - {skill}")


@cli.command('resume')
def resume_session():
    """恢复上次会话（新会话开始时使用）"""
    from lingflow.context.session import print_recovery
    print_recovery()


@cli.group()
def context():
    """管理对话上下文和压缩"""
    pass


@context.command('status')
def context_status():
    """查看上下文状态"""
    from lingflow.context import get_context_manager
    from lingflow.compression import get_smart_compressor, estimate_current_tokens

    cm = get_context_manager()
    compressor = get_smart_compressor()
    status = cm.get_status()

    click.echo("对话上下文状态:")
    click.echo(f"  会话 ID: {status['session_id']}")
    click.echo(f"  消息数: {status['message_count']}")
    click.echo(f"  估计 Token: {status['estimated_tokens']}")
    click.echo(f"  Token 使用率: {status['token_usage_ratio']:.1%}")
    click.echo(f"  已完成任务: {status['tasks_completed']}")
    click.echo(f"  待完成任务: {status['tasks_pending']}")

    # 智能压缩器状态
    comp_status = compressor.get_status()
    click.echo("\n智能压缩器:")
    click.echo(f"  最大 Token: {comp_status['max_tokens']}")
    click.echo(f"  压缩次数: {comp_status['compression_count']}")
    click.echo(f"  节省 Token: {comp_status['total_tokens_saved']}")


@context.command('compress')
@click.option('--mode', '-m', default='normal',
              type=click.Choice(['normal', 'aggressive', 'emergency']),
              help='压缩模式')
def context_compress(mode):
    """立即压缩当前上下文

    \b
    模式:
        normal: 标准压缩 (保留 50%)
        aggressive: 激进压缩 (保留 30%)
        emergency: 紧急压缩 (保留 20%)

    \b
    示例:
        lingflow context compress
        lingflow context compress --mode aggressive
    """
    from lingflow.context import compress_context
    summary = compress_context()
    click.echo("上下文已压缩:")
    click.echo(summary)


@context.command('estimate')
@click.argument('text', required=False)
@click.option('--file', '-f', type=click.Path(exists=True), help='估算文件内容')
def context_estimate(text, file):
    """估算文本或文件的 Token 数量

    \b
    示例:
        lingflow context estimate "Hello, world!"
        lingflow context estimate --file README.md
    """
    from lingflow.compression import get_smart_compressor

    compressor = get_smart_compressor()
    estimator = compressor.token_estimator

    if file:
        content = click.open_file(file).read()
        tokens = estimator.count_tokens(content)
        click.echo(f"文件 {file}:")
        click.echo(f"  字符数: {len(content)}")
        click.echo(f"  Token 数: {tokens}")
    elif text:
        tokens = estimator.count_tokens(text)
        click.echo(f"文本:")
        click.echo(f"  字符数: {len(text)}")
        click.echo(f"  Token 数: {tokens}")
    else:
        click.echo("请提供文本或 --file 选项", err=True)


@context.command('recovery')
def context_recovery():
    """获取上下文恢复摘要（用于新会话）"""
    from lingflow.context import get_recovery_context
    summary = get_recovery_context()
    click.echo(summary)


@context.command('add-task')
@click.argument('task')
@click.option('--completed', '-c', is_flag=True, help='标记为已完成')
def context_add_task(task, completed):
    """添加任务到上下文

    \b
    示例:
        lingflow context add-task "实现新功能"
        lingflow context add-task "修复bug" --completed
    """
    from lingflow.context import add_task
    add_task(task, completed)
    status = "已完成" if completed else "待完成"
    click.echo(f"已添加任务 ({status}): {task}")


@context.command('complete-task')
@click.argument('task')
def context_complete_task(task):
    """标记任务为已完成

    \b
    示例:
        lingflow context complete-task "实现新功能"
    """
    from lingflow.context import complete_task
    complete_task(task)
    click.echo(f"已完成任务: {task}")

if __name__ == '__main__':
    cli()
