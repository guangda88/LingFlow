#!/usr/bin/env python3
"""
lingflow Test Runner - 运行所有测试
"""

import sys
import subprocess
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_unit_tests():
    """运行单元测试"""
    print("\n" + "=" * 70)
    print("🧪 Running Unit Tests")
    print("=" * 70 + "\n")

    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "lingflow-core/tests/test_units.py",
        "-v",
        "--tb=short",
        "--color=yes"
    ], cwd=project_root)

    return result.returncode == 0


def run_e2e_tests():
    """运行端到端测试"""
    print("\n" + "=" * 70)
    print("🧪 Running E2E Tests")
    print("=" * 70 + "\n")

    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "lingflow-core/tests/test_e2e.py",
        "-v",
        "--tb=short",
        "--color=yes"
    ], cwd=project_root)

    return result.returncode == 0


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 Running All Tests")
    print("=" * 70 + "\n")

    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "lingflow-core/tests/",
        "-v",
        "--tb=short",
        "--color=yes"
    ], cwd=project_root)

    return result.returncode == 0


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="lingflow Test Runner")
    parser.add_argument(
        "--type",
        choices=["unit", "e2e", "all"],
        default="all",
        help="Test type to run"
    )

    args = parser.parse_args()

    # 运行测试
    if args.type == "unit":
        success = run_unit_tests()
    elif args.type == "e2e":
        success = run_e2e_tests()
    else:
        success = run_all_tests()

    # 输出结果
    print("\n" + "=" * 70)
    if success:
        print("✅ All Tests Passed!")
    else:
        print("❌ Some Tests Failed!")
    print("=" * 70 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
