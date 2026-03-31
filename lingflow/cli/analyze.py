"""代码分析命令"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import click


@click.group()
def analyze():
    """代码分析系统"""
    pass


@analyze.command()
@click.option("--target", "-t",
              default=".",
              help="目标路径")
@click.option("--metrics", "-m",
              help="指标列表 (逗号分隔): complexity, duplication, security, maintainability")
@click.option("--output", "-o",
              help="输出报告路径")
@click.option("--format", "-f",
              type=click.Choice(["json", "markdown", "html"]),
              default="markdown",
              help="输出格式")
@click.option("--verbose", "-v",
              is_flag=True,
              help="详细输出")
def run_analyze(target, metrics, output, format, verbose):
    """运行代码分析"""
    from lingflow.self_optimizer.evaluator import StructureEvaluator

    click.echo(f"\n🔍 分析代码: {target}")

    # 默认指标
    if metrics:
        metric_list = [m.strip() for m in metrics.split(",")]
    else:
        metric_list = ["complexity", "duplication"]

    click.echo(f"📊 分析指标: {', '.join(metric_list)}")

    # 创建评估器
    evaluator = StructureEvaluator(target)

    # 收集指标
    with click.progressbar(length=100, label="分析中") as bar:
        current_metrics = evaluator.get_current_metrics()
        bar.update(100)

    # 显示结果
    click.echo(f"\n📊 分析结果:")
    click.echo(f"  结构违规: {current_metrics.get('structure_violations', 0)}")
    click.echo(f"  平均类大小: {current_metrics.get('avg_class_size', 0):.0f} 行")
    click.echo(f"  平均复杂度: {current_metrics.get('avg_complexity', 0):.1f}")
    click.echo(f"  大型类数量: {current_metrics.get('large_classes_count', 0)}")
    click.echo(f"  长方法数量: {current_metrics.get('long_methods_count', 0)}")

    # 保存报告
    if output:
        report_path = Path(output)
    else:
        report_dir = Path(target) / ".lingflow" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"analysis_report_{int(time.time())}.{format}"

    _generate_analysis_report(report_path, metric_list, current_metrics, format)
    click.echo(f"\n📄 报告已保存: {report_path}")


@analyze.command("complexity")
@click.option("--target", "-t",
              default=".",
              help="目标路径")
@click.option("--threshold",
              type=int,
              default=10,
              help="复杂度阈值")
def analyze_complexity(target, threshold):
    """分析代码复杂度"""
    from lingflow.self_optimizer.evaluator import StructureEvaluator
    import ast
    from pathlib import Path

    click.echo(f"\n🔍 分析复杂度: {target}")
    click.echo(f"阈值: {threshold}")

    evaluator = StructureEvaluator(target)
    metrics = evaluator.get_current_metrics()

    # 实现详细的复杂度分析
    click.echo(f"\n📊 复杂度统计:")
    click.echo(f"  平均复杂度: {metrics.get('avg_complexity', 0):.1f}")
    click.echo(f"  最大复杂度: {metrics.get('max_complexity', 0)}")
    click.echo(f"  高复杂度函数: {metrics.get('high_complexity_count', 0)}")

    # 分析超过阈值的函数
    target_path = Path(target)
    if target_path.is_dir():
        python_files = list(target_path.rglob("*.py"))
    else:
        python_files = [target_path] if target_path.suffix == ".py" else []

    high_complexity_functions = []
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 简化的圈复杂度计算
                    complexity = 1  # 基础复杂度
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                            complexity += 1

                    if complexity > threshold:
                        high_complexity_functions.append({
                            "file": str(py_file),
                            "function": node.name,
                            "line": node.lineno,
                            "complexity": complexity
                        })
        except Exception as e:
            if verbose:
                click.echo(f"  跳过文件 {py_file}: {e}")

    if high_complexity_functions:
        click.echo(f"\n⚠️  超过阈值的函数 ({threshold}):")
        for func in sorted(high_complexity_functions, key=lambda x: -x['complexity'])[:10]:
            click.echo(f"  - {Path(func['file']).name}:{func['line']} {func['function']}() - 复杂度 {func['complexity']}")
    else:
        click.echo(f"\n✓ 没有函数超过复杂度阈值 {threshold}")


@analyze.command("duplication")
@click.option("--target", "-t",
              default=".",
              help="目标路径")
@click.option("--min-lines",
              type=int,
              default=10,
              help="最小重复行数")
def analyze_duplication(target, min_lines):
    """分析代码重复"""
    from pathlib import Path
    import ast

    click.echo(f"\n🔍 分析代码重复: {target}")
    click.echo(f"最小重复行数: {min_lines}")

    # 实现代码重复检测
    target_path = Path(target)
    if target_path.is_dir():
        python_files = list(target_path.rglob("*.py"))
    else:
        python_files = [target_path] if target_path.suffix == ".py" else []

    # 收集所有代码块
    code_blocks = {}
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 简化的代码块检测（连续的非空行）
            current_block = []
            block_start = 0

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    current_block.append((i + 1, stripped))
                elif current_block:
                    if len(current_block) >= min_lines:
                        block_key = '\n'.join(ln[1] for ln in current_block)
                        if block_key not in code_blocks:
                            code_blocks[block_key] = []
                        code_blocks[block_key].append({
                            "file": str(py_file),
                            "start": block_start + 1,
                            "lines": len(current_block)
                        })
                    current_block = []
                    block_start = i + 1
        except Exception:
            pass

    # 查找重复
    duplicates = []
    seen_blocks = {}

    for block_key, occurrences in code_blocks.items():
        if len(occurrences) > 1:
            duplicates.append({
                "block": block_key[:50] + "...",
                "count": len(occurrences),
                "occurrences": occurrences
            })

    if duplicates:
        click.echo(f"\n⚠️  发现 {len(duplicates)} 处重复代码:")
        for dup in sorted(duplicates, key=lambda x: -x['count'])[:5]:
            click.echo(f"\n  重复 {dup['count']} 次:")
            for occ in dup['occurrences']:
                click.echo(f"    - {Path(occ['file']).name}:{occ['start']} ({occ['lines']} 行)")
    else:
        click.echo(f"\n✓ 未发现超过 {min_lines} 行的重复代码")


def _generate_analysis_report(
    report_path: Path,
    metrics: List[str],
    results: Dict,
    format: str
):
    """生成分析报告"""
    if format == "json":
        content = json.dumps({
            "metrics": metrics,
            "results": results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }, indent=2, ensure_ascii=False)
    else:  # markdown
        content = f"""# 代码分析报告

生成时间: {time.strftime("%Y-%m-%d %H:%M:%S")}

## 📊 分析指标

{', '.join(metrics)}

## 📈 分析结果

- **结构违规**: {results.get('structure_violations', 0)}
- **平均类大小**: {results.get('avg_class_size', 0):.0f} 行
- **平均复杂度**: {results.get('avg_complexity', 0):.1f}
- **大型类数量**: {results.get('large_classes_count', 0)}
- **长方法数量**: {results.get('long_methods_count', 0)}
"""

    report_path.write_text(content, encoding="utf-8")
