"""自优化相关命令"""

import sys
from pathlib import Path

import click


@click.group()
def optimize():
    """自优化系统（基于LingMinOpt）"""


@optimize.command()
@click.argument("goal", type=click.Choice(["structure", "performance", "simplicity"]))
@click.option("--target", "-t", default=".", help="目标路径（默认当前目录）")
@click.option("--async", "async_mode", is_flag=True, help="异步执行（后台运行）")
@click.option("--experiments", "-e", type=int, default=20, help="最大实验次数")
@click.option("--report", "-r", help="保存报告到文件")
def run(goal, target, async_mode, experiments, report):
    """运行自优化"""
    from lingflow.self_optimizer import OptimizationAdvisor, StructureEvaluator, quick_optimize
    from lingflow.self_optimizer.config import get_global_config

    click.echo(f"\n🔍 启动 {goal} 优化...")
    click.echo(f"目标: {target}")

    # 获取当前指标
    if goal == "structure":
        evaluator = StructureEvaluator(target)
        current_metrics = evaluator.get_current_metrics()

        click.echo("\n📊 当前状态:")
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
                    goal=goal, target=target, current_metrics=current_metrics, optimization_result=result
                )
                report_path = advisor.save_report(report_content, report)
                click.echo(f"📄 报告已保存: {report_path}")
            else:
                # 询问是否保存报告
                if click.confirm("\n是否保存优化报告?", default=True):
                    report_content = advisor.generate_report(
                        goal=goal, target=target, current_metrics=current_metrics, optimization_result=result
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
            goal="structure", target=".", current_metrics=current_metrics, optimization_result=result
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

    report_path = Path(report)
    if not report_path.exists():
        click.echo(f"✗ 报告文件不存在: {report}", err=True)
        sys.exit(1)

    # 解析报告，提取最佳参数
    content = report_path.read_text(encoding="utf-8")

    # 简单解析（从YAML代码块中提取）
    in_yaml = False
    yaml_lines = []
    for line in content.split("\n"):
        if "```yaml" in line or "```YAML" in line:
            in_yaml = True
            continue
        if in_yaml and line.strip() == "```":
            break
        if in_yaml and line.strip() and not line.strip().startswith("#"):
            yaml_lines.append(line)

    yaml_content = "\n".join(yaml_lines)
    params = yaml.safe_load(yaml_content)

    click.echo("\n📋 将应用以下参数:")
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
        with open(config_file, "r", encoding="utf-8") as f:
            existing_config = yaml.safe_load(f) or {}

    # 更新配置
    if "structure_optimization" not in existing_config:
        existing_config["structure_optimization"] = {}
    existing_config["structure_optimization"].update(params)

    # 保存
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(existing_config, f, default_flow_style=False, allow_unicode=True)

    click.echo(f"\n✓ 配置已保存到: {config_file}")


@optimize.command("generate-config")
@click.option("--report", "-r", required=True, help="报告文件路径")
@click.option("--output", "-o", help="输出文件路径（默认：config_optimized.yaml）")
def generate_config(report, output):
    """从报告生成配置文件"""
    import yaml

    report_path = Path(report)
    if not report_path.exists():
        click.echo(f"✗ 报告文件不存在: {report}", err=True)
        sys.exit(1)

    # 解析报告
    content = report_path.read_text(encoding="utf-8")

    # 提取YAML参数
    in_yaml = False
    yaml_lines = []
    for line in content.split("\n"):
        if "```yaml" in line or "```YAML" in line:
            in_yaml = True
            continue
        if in_yaml and line.strip() == "```":
            break
        if in_yaml and line.strip() and not line.strip().startswith("#"):
            yaml_lines.append(line)

    yaml_content = "\n".join(yaml_lines)
    params = yaml.safe_load(yaml_content)

    # 生成配置文件
    output_path = Path(output) if output else Path("config_optimized.yaml")

    config = {"structure_optimization": params}

    with open(output_path, "w", encoding="utf-8") as f:
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
        click.echo("\n✓ 需要优化")
        click.echo(f"  原因: {trigger_info.reason}")
        click.echo(f"  优先级: {trigger_info.priority}")
    else:
        click.echo("\n✓ 暂时不需要优化")
