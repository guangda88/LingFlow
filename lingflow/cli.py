#!/usr/bin/env python3
"""灵通 (LingFlow) CLI Interface

众智混元，万法灵通

Provides command-line interface for executing LingFlow skills and workflows.
Uses Click for CLI argument parsing and command organization.
"""
import json
import sys

import click

from lingflow import LingFlow
from lingflow.feedback import (
    FeedbackCategory,
    FeedbackSeverity,
    get_feedback_collector,
)

lf = LingFlow()


@click.group()
def cli() -> None:
    """灵通 (LingFlow) CLI 主入口 - 众智混元，万法灵通"""


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


# ============================================================================
# 自优化相关命令
# ============================================================================

@cli.group()
def optimize():
    """自优化系统（基于LingMinOpt）"""
    pass


@optimize.command()
@click.argument("goal",
                type=click.Choice(["structure", "performance", "simplicity"]))
@click.option("--target", "-t", default=".", help="目标路径（默认当前目录）")
@click.option("--async", "async_mode", is_flag=True, help="异步执行（后台运行）")
@click.option("--experiments", "-e", type=int, default=20, help="最大实验次数")
@click.option("--report", "-r", help="保存报告到文件")
def run(goal, target, async_mode, experiments, report):
    """运行自优化"""
    from lingflow.self_optimizer import (
        quick_optimize,
        StructureEvaluator,
        OptimizationAdvisor
    )
    from lingflow.self_optimizer.config import get_global_config

    click.echo(f"\n🔍 启动 {goal} 优化...")
    click.echo(f"目标: {target}")

    # 获取当前指标
    if goal == "structure":
        evaluator = StructureEvaluator(target)
        current_metrics = evaluator.get_current_metrics()

        click.echo(f"\n📊 当前状态:")
        click.echo(f"  结构违规: {current_metrics.get('structure_violations', 0)}")
        click.echo(f"  平均类大小: {current_metrics.get('avg_class_size', 0):.0f}行")
        click.echo(f"  平均复杂度: {current_metrics.get('avg_complexity', 0):.1f}")
    else:
        current_metrics = {}

    # 更新配置
    config = get_global_config()
    config.set("optimization.max_experiments", experiments)

    # 运行优化
    result = quick_optimize(target, goal, async_mode)

    if async_mode:
        click.echo("\n✓ 优化已启动（后台运行）")
        click.echo("  使用 'lingflow optimize status' 查看进度")
        click.echo("  使用 'lingflow optimize wait' 等待完成")
    elif result:
        if result.success:
            # 生成报告
            advisor = OptimizationAdvisor()
            advisor.print_summary(result, current_metrics)

            if report or config.get("report.auto_save"):
                report_content = advisor.generate_report(
                    goal=goal,
                    target=target,
                    current_metrics=current_metrics,
                    optimization_result=result
                )
                report_path = advisor.save_report(report_content, report)
                click.echo(f"📄 报告已保存: {report_path}")
            else:
                # 询问是否保存报告
                if click.confirm("\n是否保存优化报告?", default=True):
                    report_content = advisor.generate_report(
                        goal=goal,
                        target=target,
                        current_metrics=current_metrics,
                        optimization_result=result
                    )
                    report_path = advisor.save_report(report_content)
                    click.echo(f"📄 报告已保存: {report_path}")
        else:
            click.echo(f"\n✗ 优化失败: {result.error}", err=True)
            sys.exit(1)


@optimize.command("status")
def status():
    """查看优化状态"""
    from lingflow.hooks import get_global_hook

    hook = get_global_hook()

    if not hook.is_optimization_running():
        click.echo("⚪ 没有运行中的优化")
        return

    progress = hook.optimizer.get_progress()

    click.echo("🔄 优化运行中")
    if progress and progress.get("pid"):
        click.echo(f"  进程ID: {progress['pid']}")


@optimize.command("wait")
@click.option("--timeout", "-t", type=int, default=300, help="超时时间（秒）")
def wait_completion(timeout):
    """等待优化完成"""
    from lingflow.hooks import get_global_hook
    from lingflow.self_optimizer import OptimizationAdvisor, StructureEvaluator

    hook = get_global_hook()

    if not hook.is_optimization_running():
        click.echo("⚪ 没有运行中的优化")
        return

    click.echo(f"⏳ 等待优化完成（最多 {timeout} 秒）...")

    result = hook.optimizer.wait_for_completion(timeout)

    if result and result.success:
        # 获取当前指标
        evaluator = StructureEvaluator(".")
        current_metrics = evaluator.get_current_metrics()

        # 打印摘要
        advisor = OptimizationAdvisor()
        advisor.print_summary(result, current_metrics)

        # 生成报告
        report_content = advisor.generate_report(
            goal="structure",
            target=".",
            current_metrics=current_metrics,
            optimization_result=result
        )
        report_path = advisor.save_report(report_content)
        click.echo(f"📄 报告已保存: {report_path}")
    else:
        click.echo("⚠️  优化未完成或失败")
        if result and result.error:
            click.echo(f"错误: {result.error}")


@optimize.command("cancel")
def cancel():
    """取消当前优化"""
    from lingflow.hooks import get_global_hook

    hook = get_global_hook()

    if not hook.is_optimization_running():
        click.echo("⚪ 没有运行中的优化")
        return

    click.echo("⏹️  正在取消优化...")
    hook.cancel_optimization()
    click.echo("✓ 优化已取消")


@optimize.command("apply")
@click.option("--report", "-r", required=True, help="报告文件路径")
def apply_optimization(report):
    """应用优化建议（自动修改配置）"""
    import yaml
    from pathlib import Path

    report_path = Path(report)
    if not report_path.exists():
        click.echo(f"✗ 报告文件不存在: {report}", err=True)
        sys.exit(1)

    # 解析报告，提取最佳参数
    content = report_path.read_text(encoding="utf-8")

    # 简单解析（从YAML代码块中提取）
    in_yaml = False
    yaml_lines = []
    for line in content.split('\n'):
        if '```yaml' in line or '```YAML' in line:
            in_yaml = True
            continue
        if in_yaml and line.strip() == '```':
            break
        if in_yaml and line.strip() and not line.strip().startswith('#'):
            yaml_lines.append(line)

    yaml_content = '\n'.join(yaml_lines)
    params = yaml.safe_load(yaml_content)

    click.echo(f"\n📋 将应用以下参数:")
    for key, value in params.items():
        click.echo(f"  {key}: {value}")

    if not click.confirm("\n确认应用?", default=False):
        click.echo("取消")
        return

    # 保存到配置文件
    config_dir = Path.home() / ".lingflow"
    config_dir.mkdir(exist_ok=True)
    config_file = config_dir / "config.yaml"

    existing_config = {}
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            existing_config = yaml.safe_load(f) or {}

    # 更新配置
    if "structure_optimization" not in existing_config:
        existing_config["structure_optimization"] = {}
    existing_config["structure_optimization"].update(params)

    # 保存
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(existing_config, f, default_flow_style=False, allow_unicode=True)

    click.echo(f"\n✓ 配置已保存到: {config_file}")


@optimize.command("generate-config")
@click.option("--report", "-r", required=True, help="报告文件路径")
@click.option("--output", "-o", help="输出文件路径（默认：config_optimized.yaml）")
def generate_config(report, output):
    """从报告生成配置文件"""
    import yaml
    from pathlib import Path

    report_path = Path(report)
    if not report_path.exists():
        click.echo(f"✗ 报告文件不存在: {report}", err=True)
        sys.exit(1)

    # 解析报告
    content = report_path.read_text(encoding="utf-8")

    # 提取YAML参数
    in_yaml = False
    yaml_lines = []
    for line in content.split('\n'):
        if '```yaml' in line or '```YAML' in line:
            in_yaml = True
            continue
        if in_yaml and line.strip() == '```':
            break
        if in_yaml and line.strip() and not line.strip().startswith('#'):
            yaml_lines.append(line)

    yaml_content = '\n'.join(yaml_lines)
    params = yaml.safe_load(yaml_content)

    # 生成配置文件
    output_path = Path(output) if output else Path("config_optimized.yaml")

    config = {
        "structure_optimization": params
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# LingFlow 自优化配置\n")
        f.write(f"# 从报告生成: {report}\n")
        f.write(f"# 时间: {Path(report).stat().st_mtime}\n\n")
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

    click.echo(f"✓ 配置文件已生成: {output_path}")


@optimize.command("check")
@click.option("--target", "-t", default=".", help="目标路径")
def check_trigger(target):
    """检查是否需要优化"""
    from lingflow.self_optimizer import OptimizationTrigger, StructureEvaluator

    trigger = OptimizationTrigger()

    # 收集上下文
    evaluator = StructureEvaluator(target)
    metrics = evaluator.get_current_metrics()

    context = {
        "avg_complexity": metrics.get("avg_complexity", 0),
        "large_classes_count": metrics.get("large_classes_count", 0),
        "structure_violations": metrics.get("structure_violations", 0),
    }

    # 检查条件
    should_trigger, trigger_info = trigger.check_all_conditions(context)

    if should_trigger:
        click.echo(f"\n✓ 需要优化")
        click.echo(f"  原因: {trigger_info.reason}")
        click.echo(f"  优先级: {trigger_info.priority}")
    else:
        click.echo("\n✓ 暂时不需要优化")


# ============================================================================
# 反馈相关命令
# ============================================================================

@cli.group()
def feedback():
    """用户反馈管理"""
    pass


@feedback.command("submit")
@click.option("--title", "-t", required=True, help="问题标题")
@click.option("--description", "-d", required=True, help="详细描述")
@click.option("--category", "-c",
              type=click.Choice(["bug", "feature", "improvement", "performance", "documentation", "usability", "other"]),
              default="bug", help="反馈类别")
@click.option("--severity", "-s",
              type=click.Choice(["low", "medium", "high", "critical"]),
              default="medium", help="严重性")
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
@click.option("--severity", "-s",
              type=click.Choice(["low", "medium", "high", "critical"]),
              default="medium", help="严重性")
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
        click.echo(f"  堆栈跟踪已附加")


@feedback.command("list")
@click.option("--category", "-c",
              type=click.Choice(["bug", "feature", "improvement", "performance", "documentation", "usability", "other"]),
              help="按类别过滤")
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
        click.echo(f"\n复现步骤:")
        for i, step in enumerate(feedback.reproduction_steps, 1):
            click.echo(f"  {i}. {step}")

    if feedback.environment:
        click.echo(f"\n环境信息:")
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

    content = collector.export_markdown(output)
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
    for cat, count in stats['by_category'].items():
        click.echo(f"  {cat}: {count}")

    click.echo("\n按严重性:")
    for sev, count in stats['by_severity'].items():
        click.echo(f"  {sev}: {count}")


if __name__ == "__main__":
    cli()
