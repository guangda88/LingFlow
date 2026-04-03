"""测试命令"""

import subprocess
import sys

import click


@click.group()
def test():
    """测试系统"""


@test.command()
@click.option("--coverage", is_flag=True, help="生成覆盖率报告")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
@click.option("--parallel", is_flag=True, help="并行运行测试")
@click.option("--target", help="目标测试路径")
def run_test(coverage, verbose, parallel, target):
    """运行测试套件"""
    click.echo("\n🧪 运行测试套件...")

    # 构建pytest命令
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if coverage:
        cmd.extend(["--cov=lingflow", "--cov-report=term-missing"])

    if parallel:
        cmd.extend(["-n", "auto"])

    if target:
        cmd.append(target)

    click.echo(f"命令: {' '.join(cmd)}")

    # 运行测试
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


@test.command("e2e")
@click.option("--scenario", "-s", help="运行特定场景")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def run_e2e_test(scenario, verbose):
    """运行端到端测试"""
    import subprocess
    from pathlib import Path

    click.echo("\n🧪 运行 E2E 测试...")

    # 集成E2E测试框架
    e2e_test_dir = Path("tests/integration")
    if not e2e_test_dir.exists():
        click.echo(f"⚠️  E2E测试目录不存在: {e2e_test_dir}")
        return

    # 查找E2E测试文件
    test_files = list(e2e_test_dir.glob("*e2e*.py"))
    if not test_files:
        click.echo("⚠️  未找到E2E测试文件")
        return

    click.echo(f"找到 {len(test_files)} 个E2E测试文件")

    # 运行pytest
    cmd = ["python", "-m", "pytest"]
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if scenario:
        # 运行特定场景
        cmd.extend(["-k", scenario])

    cmd.extend([str(f) for f in test_files])

    click.echo(f"命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode
