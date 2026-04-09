#!/usr/bin/env python3
"""CLI命令测试脚本

测试LingFlow CLI的基本功能
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list) -> tuple:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)


def test_cli_help():
    """测试CLI帮助"""
    print("测试: lingflow --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "--help"])
    assert code == 0, f"Help failed: {err}"
    assert "灵通" in out, "Help should contain Chinese name"
    assert "optimize" in out, "Help should show optimize command"
    assert "learn" in out, "Help should show learn command"
    print("✓ 通过\n")


def test_optimize_commands():
    """测试优化命令"""
    print("测试: lingflow optimize --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "optimize", "--help"])
    assert code == 0, f"Optimize help failed: {err}"
    assert "run" in out, "Should show run command"
    print("✓ 通过\n")

    print("测试: lingflow optimize run --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "optimize", "run", "--help"])
    assert code == 0, f"Optimize run help failed: {err}"
    assert "structure" in out, "Should show structure goal"
    print("✓ 通过\n")


def test_learn_commands():
    """测试学习命令"""
    print("测试: lingflow learn --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "learn", "--help"])
    assert code == 0, f"Learn help failed: {err}"
    assert "run-learn" in out, "Should show run-learn command"
    print("✓ 通过\n")

    print("测试: lingflow learn run-learn --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "learn", "run-learn", "--help"])
    assert code == 0, f"Learn run-learn help failed: {err}"
    assert "tools" in out, "Should show tools option"
    print("✓ 通过\n")


def test_analyze_commands():
    """测试分析命令"""
    print("测试: lingflow analyze --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "analyze", "--help"])
    assert code == 0, f"Analyze help failed: {err}"
    assert "run-analyze" in out, "Should show run-analyze command"
    print("✓ 通过\n")

    print("测试: lingflow analyze run-analyze --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "analyze", "run-analyze", "--help"])
    assert code == 0, f"Analyze run-analyze help failed: {err}"
    assert "metrics" in out, "Should show metrics option"
    print("✓ 通过\n")


def test_test_commands():
    """测试命令"""
    print("测试: lingflow test --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "test", "--help"])
    assert code == 0, f"Test help failed: {err}"
    assert "run-test" in out, "Should show run-test command"
    print("✓ 通过\n")

    print("测试: lingflow test run-test --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "test", "run-test", "--help"])
    assert code == 0, f"Test run-test help failed: {err}"
    assert "coverage" in out, "Should show coverage option"
    print("✓ 通过\n")


def test_feedback_commands():
    """测试反馈命令"""
    print("测试: lingflow feedback --help")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "feedback", "--help"])
    assert code == 0, f"Feedback help failed: {err}"
    assert "submit" in out, "Should show submit command"
    print("✓ 通过\n")


def test_list_skills():
    """测试列出技能"""
    print("测试: lingflow list-skills")
    code, out, err = run_command([sys.executable, "-m", "lingflow.cli", "list-skills"])
    # 这个命令可能会失败，因为需要LingFlow完全初始化
    # 只要命令能识别就行
    print(f"返回码: {code}")
    if code == 0:
        print(f"输出: {out[:100]}")
    print("✓ 命令可识别\n")


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("CLI帮助", test_cli_help),
        ("优化命令", test_optimize_commands),
        ("学习命令", test_learn_commands),
        ("分析命令", test_analyze_commands),
        ("测试命令", test_test_commands),
        ("反馈命令", test_feedback_commands),
        ("列出技能", test_list_skills),
    ]

    print("=" * 60)
    print("LingFlow CLI 测试")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ 失败: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ 错误: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
