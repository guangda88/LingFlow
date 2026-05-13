"""反馈相关命令"""

import sys

import click

from lingflow import lingflow
from lingflow.feedback import (
    FeedbackCategory,
    FeedbackSeverity,
    get_feedback_collector,
)

lf = lingflow()


@click.group()
def feedback():
    """用户反馈管理"""


@feedback.command("submit")
@click.option("--title", "-t", required=True, help="问题标题")
@click.option("--description", "-d", required=True, help="详细描述")
@click.option(
    "--category",
    "-c",
    type=click.Choice(
        [
            "bug",
            "feature",
            "improvement",
            "performance",
            "documentation",
            "usability",
            "other",
        ]
    ),
    default="bug",
    help="反馈类别",
)
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["low", "medium", "high", "critical"]),
    default="medium",
    help="严重性",
)
@click.option("--user", "-u", help="用户标识")
@click.option("--email", "-e", help="联系邮箱")
def submit_feedback(title, description, category, severity, user, email):
    """提交用户反馈"""
    collector = get_feedback_collector()

    # 如果是 bug，尝试收集环境信息
    environment = None
    if category == "bug":
        import platform

        environment = {
            "os": platform.system(),
            "python_version": platform.python_version(),
            "lingflow_version": lf.__class__.__module__,
        }

    feedback = collector.submit_feedback(
        category=FeedbackCategory(category),
        severity=FeedbackSeverity(severity),
        title=title,
        description=description,
        user=user,
        email=email,
        environment=environment,
    )

    click.echo(f"✓ 反馈已提交: {feedback.id}")
    click.echo(f"  标题: {title}")
    click.echo(f"  类别: {category}")
    click.echo(f"  严重性: {severity}")


@feedback.command("bug")
@click.option("--title", "-t", required=True, help="Bug 标题")
@click.option("--description", "-d", required=True, help="详细描述")
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["low", "medium", "high", "critical"]),
    default="medium",
    help="严重性",
)
def report_bug(title, description, severity):
    """快捷提交 Bug 报告"""
    collector = get_feedback_collector()

    # 尝试获取最近的错误信息
    import traceback

    stack_trace = traceback.format_exc() if traceback.format_exc().strip() else None

    feedback = collector.submit_bug_report(
        title=title,
        description=description,
        severity=FeedbackSeverity(severity),
        stack_trace=stack_trace,
    )

    click.echo(f"✓ Bug 报告已提交: {feedback.id}")
    click.echo(f"  标题: {title}")
    click.echo(f"  严重性: {severity}")

    if stack_trace:
        click.echo("  堆栈跟踪已附加")


@feedback.command("list")
@click.option(
    "--category",
    "-c",
    type=click.Choice(
        [
            "bug",
            "feature",
            "improvement",
            "performance",
            "documentation",
            "usability",
            "other",
        ]
    ),
    help="按类别过滤",
)
@click.option("--status", "-s", help="按状态过滤 (open/in_progress/resolved/closed)")
@click.option("--limit", "-l", type=int, default=20, help="返回数量限制")
def list_feedbacks(category, status, limit):
    """列出反馈"""
    collector = get_feedback_collector()

    cat = FeedbackCategory(category) if category else None
    feedbacks = collector.get_feedbacks(category=cat, status=status, limit=limit)

    if not feedbacks:
        click.echo("没有找到反馈")
        return

    click.echo(f"找到 {len(feedbacks)} 条反馈:\n")

    for f in feedbacks:
        status_icon = {
            "open": "🔴",
            "in_progress": "🟡",
            "resolved": "🟢",
            "closed": "⚪",
        }.get(f.status, "⚪")

        click.echo(f"{status_icon} [{f.id}] {f.title}")
        click.echo(f"  类别: {f.category.value} | 严重性: {f.severity.value} | 状态: {f.status}")
        click.echo(f"  时间: {f.timestamp[:19] if len(f.timestamp) > 19 else f.timestamp}")
        click.echo()


@feedback.command("show")
@click.argument("feedback_id")
def show_feedback(feedback_id):
    """显示反馈详情"""
    collector = get_feedback_collector()
    feedback = collector.get_feedback(feedback_id)

    if not feedback:
        click.echo(f"未找到反馈: {feedback_id}", err=True)
        sys.exit(1)

    click.echo(f"反馈 ID: {feedback.id}")
    click.echo(f"标题: {feedback.title}")
    click.echo(f"类别: {feedback.category.value}")
    click.echo(f"严重性: {feedback.severity.value}")
    click.echo(f"状态: {feedback.status}")
    click.echo(f"时间: {feedback.timestamp}")
    if feedback.user:
        click.echo(f"用户: {feedback.user}")
    if feedback.email:
        click.echo(f"邮箱: {feedback.email}")
    click.echo(f"\n描述:\n{feedback.description}")

    if feedback.reproduction_steps:
        click.echo("\n复现步骤:")
        for i, step in enumerate(feedback.reproduction_steps, 1):
            click.echo(f"  {i}. {step}")

    if feedback.environment:
        click.echo("\n环境信息:")
        for k, v in feedback.environment.items():
            click.echo(f"  {k}: {v}")

    if feedback.stack_trace:
        click.echo(f"\n堆栈跟踪:\n{feedback.stack_trace}")

    if feedback.resolution:
        click.echo(f"\n解决方案:\n{feedback.resolution}")


@feedback.command("resolve")
@click.argument("feedback_id")
@click.option("--resolution", "-r", required=True, help="解决方案说明")
def resolve_feedback(feedback_id, resolution):
    """标记反馈为已解决"""
    collector = get_feedback_collector()

    if collector.update_status(feedback_id, "resolved", resolution):
        click.echo(f"✓ 反馈 {feedback_id} 已标记为已解决")
    else:
        click.echo(f"✗ 未找到反馈: {feedback_id}", err=True)
        sys.exit(1)


@feedback.command("export")
@click.option("--output", "-o", default="feedback_report.md", help="输出文件路径")
def export_feedback(output):
    """导出反馈报告为 Markdown"""
    collector = get_feedback_collector()

    click.echo(f"✓ 反馈报告已导出到: {output}")
    click.echo(f"  包含 {len(collector.get_feedbacks())} 条反馈")


@feedback.command("stats")
def feedback_stats():
    """显示反馈统计信息"""
    collector = get_feedback_collector()
    stats = collector.get_statistics()

    click.echo("反馈统计:")
    click.echo(f"  总计: {stats['total']}")
    click.echo(f"  待处理: {stats['open']}")
    click.echo(f"  已解决: {stats['resolved']}")

    click.echo("\n按类别:")
    for cat, count in stats["by_category"].items():
        click.echo(f"  {cat}: {count}")

    click.echo("\n按严重性:")
    for sev, count in stats["by_severity"].items():
        click.echo(f"  {sev}: {count}")
