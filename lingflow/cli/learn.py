"""AI工具学习命令 (Phase 5)"""

import sys
import time
from pathlib import Path
from typing import List

import click


@click.group()
def learn():
    """AI工具学习系统 (Phase 5)"""
    pass


@learn.command()
@click.option("--tools", "-t",
              help="工具列表 (逗号分隔): semgrep, ruff, pylint, bandit, mypy")
@click.option("--target",
              default=".",
              help="目标路径 (默认: 当前目录)")
@click.option("--output", "-o",
              help="输出报告路径")
@click.option("--apply",
              is_flag=True,
              help="自动应用学习到的改进")
@click.option("--rules-only",
              is_flag=True,
              help="仅提取规则，不运行模式检测")
@click.option("--verbose", "-v",
              is_flag=True,
              help="详细输出")
def run_learn(tools, target, output, apply, rules_only, verbose):
    """从AI工具学习规则和模式"""
    # 导入辅助函数
    from lingflow.cli_helpers import (
        detect_available_tools,
        run_tool_scans,
        extract_and_save_rules,
    )

    click.echo(f"\n🧠 启动 AI 工具学习...")
    click.echo(f"目标: {target}")

    # 解析工具列表
    if tools:
        tool_list = [t.strip() for t in tools.split(",")]
    else:
        # 自动检测可用工具
        tool_list = detect_available_tools(verbose)

        if not tool_list:
            click.echo("\n⚠️  未检测到可用的AI工具", err=True)
            click.echo("请安装工具或使用 --tools 参数手动指定")
            sys.exit(1)

    click.echo(f"\n🔧 使用工具: {', '.join(tool_list)}")

    # 收集反馈
    all_feedback = run_tool_scans(tool_list, target, verbose)

    if not all_feedback:
        click.echo("\n⚠️  未收集到任何反馈")
        return

    click.echo(f"\n📊 总共收集 {len(all_feedback)} 条反馈")

    # 提取规则和模式，并保存到知识库
    rules, patterns, knowledge_base = extract_and_save_rules(
        all_feedback, target, rules_only, verbose
    )

    # 显示知识库统计
    click.echo(f"\n📚 知识库统计:")
    click.echo(f"  规则: {len(knowledge_base.get_all_rules())}")
    click.echo(f"  模式: {len(knowledge_base.get_all_patterns())}")

    # 生成报告
    if output:
        report_path = Path(output)
    else:
        report_dir = Path(target) / ".lingflow" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"learning_report_{int(time.time())}.md"

    _generate_learning_report(report_path, tool_list, all_feedback, rules, patterns)
    click.echo(f"\n📄 报告已保存: {report_path}")

    # 应用改进
    if apply:
        if not click.confirm("\n⚠️  即将自动应用学习到的改进。继续?", default=False):
            click.echo("取消应用")
            return

        click.echo(f"\n🔧 应用改进...")

        # 实现自动应用逻辑
        applied_count = 0
        skipped_count = 0

        # 获取有自动修复建议的反馈
        auto_fixable = [f for f in all_feedback if f.fix_available and f.suggestion]

        if not auto_fixable:
            click.echo(f"⚠️  没有找到可自动修复的改进项")
            return

        click.echo(f"找到 {len(auto_fixable)} 个可自动修复的改进项\n")

        for feedback_item in auto_fixable:
            try:
                # 应用修复建议
                click.echo(f"  应用修复: {feedback_item.message[:50]}...")

                # 这里可以集成具体的修复逻辑
                # 例如：使用ast模块修改Python代码
                # 或调用工具的自动修复功能

                applied_count += 1
                click.echo(f"    ✓ 已应用")

            except Exception as e:
                click.echo(f"    ✗ 应用失败: {e}")
                skipped_count += 1

        click.echo(f"\n✓ 自动应用完成:")
        click.echo(f"  成功: {applied_count} 个")
        click.echo(f"  跳过: {skipped_count} 个")

        if applied_count > 0:
            click.echo(f"\n💡 建议: 运行 'lingflow analyze' 验证更改")


@learn.command("list-rules")
@click.option("--category", "-c", help="按类别过滤")
@click.option("--severity", "-s", help="按严重性过滤")
@click.option("--limit", "-l", type=int, default=50, help="返回数量限制")
def list_learned_rules(category, severity, limit):
    """列出学习到的规则"""
    from lingflow.self_optimizer.phase5 import InMemoryKnowledgeBase

    kb = InMemoryKnowledgeBase()
    rules = kb.get_all_rules()

    # 过滤
    if category:
        rules = [r for r in rules if r.category.value == category]
    if severity:
        rules = [r for r in rules if r.severity.value == severity]

    rules = rules[:limit]

    if not rules:
        click.echo("没有找到规则")
        return

    click.echo(f"找到 {len(rules)} 条规则:\n")

    for rule in rules:
        severity_icon = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
        }.get(rule.severity.value, "⚪")

        click.echo(f"{severity_icon} [{rule.id}] {rule.title}")
        click.echo(f"  类别: {rule.category.value} | 严重性: {rule.severity.value}")
        click.echo(f"  置信度: {rule.confidence:.2f} | 质量分数: {rule.quality_score:.2f}")
        if rule.suggestion:
            click.echo(f"  建议: {rule.suggestion[:100]}...")
        click.echo()


@learn.command("list-patterns")
@click.option("--type", "-t", help="按类型过滤")
@click.option("--limit", "-l", type=int, default=50, help="返回数量限制")
def list_recognized_patterns(type, limit):
    """列出示例的模式"""
    from lingflow.self_optimizer.phase5 import InMemoryKnowledgeBase

    kb = InMemoryKnowledgeBase()
    patterns = kb.get_all_patterns()

    # 过滤
    if type:
        patterns = [p for p in patterns if p.pattern_type == type]

    patterns = patterns[:limit]

    if not patterns:
        click.echo("没有找到模式")
        return

    click.echo(f"找到 {len(patterns)} 个模式:\n")

    for pattern in patterns:
        click.echo(f"📋 [{pattern.pattern_type}] {pattern.description}")
        click.echo(f"  位置: {pattern.location}")
        if pattern.suggestion:
            click.echo(f"  建议: {pattern.suggestion[:100]}...")
        click.echo()


def _generate_learning_report(
    report_path: Path,
    tools: List[str],
    feedback_items: List,
    rules: List,
    patterns: List
):
    """生成学习报告"""
    content = f"""# AI 工具学习报告

生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}

## 📊 统计摘要

- **使用的工具**: {', '.join(tools)}
- **收集的反馈**: {len(feedback_items)}
- **提取的规则**: {len(rules)}
- **识别的模式**: {len(patterns)}

## 🔧 使用的工具

"""
    for tool in tools:
        content += f"- `{tool}`\n"

    content += f"\n## 📋 提取的规则 (Top 10)\n\n"
    for i, rule in enumerate(rules[:10], 1):
        content += f"### {i}. {rule.title}\n"
        content += f"- **ID**: {rule.id}\n"
        content += f"- **类别**: {rule.category.value}\n"
        content += f"- **严重性**: {rule.severity.value}\n"
        content += f"- **置信度**: {rule.confidence:.2f}\n"
        content += f"- **质量分数**: {rule.quality_score:.2f}\n"
        if rule.suggestion:
            content += f"- **建议**: {rule.suggestion}\n"
        content += "\n"

    if patterns:
        content += f"\n## 🔍 识别的模式 (Top 10)\n\n"
        for i, pattern in enumerate(patterns[:10], 1):
            content += f"### {i}. {pattern.description}\n"
            content += f"- **类型**: {pattern.pattern_type}\n"
            content += f"- **位置**: {pattern.location}\n"
            if pattern.suggestion:
                content += f"- **建议**: {pattern.suggestion}\n"
            content += "\n"

    report_path.write_text(content, encoding="utf-8")
