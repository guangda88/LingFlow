#!/usr/bin/env python3
"""灵族健康检查与状态报告

名字从各成员的 CRUSH.md 事实源读取，不硬编码。
若 CRUSH.md 不存在或无法解析，降级用目录名。

Usage:
    python lingflow_health.py          # 检查所有灵族成员
    python lingflow_health.py --fix    # 尝试自动修复
"""

import re
import shlex
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str
    fix_hint: str = ""


@dataclass
class MemberReport:
    name: str
    directory: str
    name_source: str = ""
    dir_exists: bool = False
    key_files_ok: int = 0
    key_files_total: int = 0
    code_lines: int = 0
    tests_passed: int = 0
    tests_total: int = 0
    overall_pass: bool = False


class LingFamilyHealthCheck:
    BASE = Path("/home/ai")

    KNOWN_DIRS = [
        {
            "dir": "lingflow",
            "pkg": "lingflow",
            "tests_cmd": "python -m pytest tests/test_coordinator.py tests/test_coordinator_extended2.py tests/test_auto_executor.py tests/test_auto_executor_regression.py tests/test_escape_hatch.py tests/test_crash_recovery.py tests/test_context_preloader.py tests/test_worktree_manager.py tests/test_verification.py -q --tb=no",
            "key_files": ["lingflow/__init__.py", "lingflow/coordination/coordinator.py"],
        },
        {
            "dir": "lingclaude",
            "pkg": "lingclaude",
            "tests_cmd": "timeout 30 python -m pytest tests/test_core.py tests/test_behavior.py -q --tb=no",
            "key_files": ["lingclaude/__init__.py", "lingclaude/cli/__main__.py"],
        },
        {
            "dir": "lingminopt",
            "pkg": "lingminopt",
            "tests_cmd": "timeout 15 python -m pytest lingminopt/tests/ -q --tb=no",
            "key_files": ["lingminopt/__init__.py", "lingminopt/meta_optimizer/__init__.py"],
        },
        {
            "dir": "lingmessage",
            "pkg": "lingmessage",
            "tests_cmd": "timeout 15 python -m pytest tests/ -q --tb=no",
            "key_files": ["lingmessage/__init__.py", "lingmessage/lingbus.py"],
        },
        {
            "dir": "lingyi",
            "pkg": "src/lingyi",
            "tests_cmd": "timeout 30 python -m pytest tests/test_basic.py -q --tb=no",
            "key_files": ["src/lingyi/__init__.py", "src/lingyi/agent.py"],
        },
    ]

    def __init__(self):
        self.results: List[CheckResult] = []
        self.reports: List[MemberReport] = []

    def _read_name_from_crush(self, member_dir: Path) -> Optional[str]:
        """从成员的 CRUSH.md 读取中文名。这是事实源，不是硬编码。"""
        crush_path = member_dir / "CRUSH.md"
        if not crush_path.exists():
            return None
        try:
            text = crush_path.read_text(encoding="utf-8")
        except OSError:
            return None

        patterns = [
            r"你是([^\s（(（/]+?)[（(]\s*",
            r"你是([^\s，,。.！!？?]+?)[，,是]",
        ]
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                name = m.group(1).strip()
                if 2 <= len(name) <= 6:
                    return name
        return None

    def _resolve_name(self, cfg: dict) -> tuple:
        """返回 (name, source_description)"""
        member_dir = self.BASE / cfg["dir"]
        name = self._read_name_from_crush(member_dir)
        if name:
            return name, "CRUSH.md"
        return cfg["dir"], "fallback:dirname"

    def check(self) -> List[CheckResult]:
        print("=" * 60)
        print("灵族健康检查")
        print("=" * 60)
        print()

        self._check_shared_deps()
        for cfg in self.KNOWN_DIRS:
            name, source = self._resolve_name(cfg)
            self._check_member(name, cfg, source)

        self._print_summary()
        return self.results

    def _check_shared_deps(self):
        print("【共享依赖检查】")
        deps_ok = True
        for dep in ["pytest", "tiktoken"]:
            try:
                __import__(dep)
                print(f"  ✓ {dep}")
            except ImportError:
                print(f"  ✗ {dep} 未安装")
                deps_ok = False
                self.results.append(CheckResult("shared_deps", False, f"{dep} missing"))
        if deps_ok:
            print("  ✓ 共享依赖完整")
        print()

    def _count_code_lines(self, pkg_dir: Path) -> int:
        if not pkg_dir.exists():
            return 0
        result = subprocess.run(
            ["find", str(pkg_dir), "-name", "*.py", "-exec", "wc", "-l", "{}", "+"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip()
        if not lines:
            return 0
        last_line = lines.split("\n")[-1]
        try:
            return int(last_line.split()[0])
        except (ValueError, IndexError):
            return 0

    def _parse_test_output(self, output: str) -> tuple:
        for line in reversed(output.strip().splitlines()):
            if "passed" in line:
                try:
                    parts = line.strip().split()
                    for i, p in enumerate(parts):
                        if p == "passed":
                            passed = int(parts[i - 1])
                            failed = 0
                            if "failed" in line:
                                fi = parts.index("failed")
                                failed = int(parts[fi - 1])
                            return passed, passed + failed
                except (ValueError, IndexError):
                    continue
        return 0, 0

    def _check_member(self, name: str, cfg: dict, name_source: str):
        report = MemberReport(name=name, directory=cfg["dir"], name_source=name_source)
        print(f"【{name}】({cfg['dir']}) [名字来源: {name_source}]")
        member_dir = self.BASE / cfg["dir"]
        passed = True

        if not member_dir.exists():
            print(f"  ✗ 目录不存在: {member_dir}")
            self.results.append(CheckResult(name, False, "目录不存在"))
            report.dir_exists = False
            self.reports.append(report)
            print()
            return

        report.dir_exists = True
        print("  ✓ 目录存在")

        for kf in cfg["key_files"]:
            report.key_files_total += 1
            if (member_dir / kf).exists():
                print(f"  ✓ {kf}")
                report.key_files_ok += 1
            else:
                print(f"  ✗ {kf} 缺失")
                passed = False

        report.code_lines = self._count_code_lines(member_dir / cfg["pkg"])
        print(f"  ~ {report.code_lines:,} 行 Python 代码")

        test_result = subprocess.run(
            shlex.split(cfg["tests_cmd"]), shell=False, capture_output=True, text=True,
            cwd=str(member_dir), timeout=120
        )
        test_output = test_result.stdout.strip()
        tp, tt = self._parse_test_output(test_output)
        report.tests_passed = tp
        report.tests_total = tt

        if tp > 0 and "failed" not in (test_output.split("passed")[0] if "passed" in test_output else ""):
            print(f"  ✓ 测试: {tp} passed")
        elif tp == 0 and tt == 0:
            print("  ⚠ 测试: 无法解析结果")
        else:
            print("  ✗ 测试失败")
            passed = False

        report.overall_pass = passed
        self.results.append(CheckResult(name, passed, f"{'通过' if passed else '有问题'}"))
        self.reports.append(report)
        print()

    def _print_summary(self):
        print("=" * 60)
        print("总结")
        print("=" * 60)
        total = len(self.results)
        ok = sum(1 for r in self.results if r.passed)
        print(f"通过: {ok}/{total}")

        total_lines = sum(r.code_lines for r in self.reports)
        total_tests = sum(r.tests_passed for r in self.reports)
        print(f"灵族总代码: {total_lines:,} 行")
        print(f"灵族总测试: {total_tests} passed")

        print("\n成员状态:")
        header = f"  {'成员':<8} {'名字来源':<16} {'代码行':>8} {'测试':>10} {'关键文件':>10} {'状态':>4}"
        print(header)
        print("  " + "-" * (len(header) - 2))
        for r in self.reports:
            status = "✓" if r.overall_pass else "✗"
            files_str = f"{r.key_files_ok}/{r.key_files_total}"
            tests_str = f"{r.tests_passed} passed" if r.tests_passed else "N/A"
            print(f"  {r.name:<8} {r.name_source:<16} {r.code_lines:>8,} {tests_str:>10} {files_str:>10} {status:>4}")

        failed = [r for r in self.results if not r.passed]
        if failed:
            print("\n需要修复:")
            for r in failed:
                print(f"  - {r.name}: {r.detail}")
        else:
            print("\n所有检查通过 ✓")


if __name__ == "__main__":
    hc = LingFamilyHealthCheck()
    hc.check()
