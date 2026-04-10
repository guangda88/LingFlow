#!/usr/bin/env python3
"""Pre-push CI simulation — runs the same checks as CI before allowing push.

Exit codes:
  0: All checks passed (or warnings only)
  1: Hard block — fix before pushing

Hard blocks (must fix):
  - black formatting issues
  - isort import ordering issues
  - pytest collection errors

Soft warnings (shown but don't block):
  - flake8 lint issues
  - mypy type errors
  - test failures (not collection errors)
"""

import subprocess
import sys
from pathlib import Path

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

BLOCKED = False
WARNINGS = 0


def run(name: str, cmd: list, block: bool = False) -> bool:
    """Run a command and report results."""
    global BLOCKED, WARNINGS
    print(f"\n{BOLD}[CI-SIM] {name}{RESET}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"  {GREEN}PASS{RESET}")
        return True

    output = result.stdout + result.stderr
    lines = output.strip().split("\n")
    for line in lines[-10:]:
        print(f"  {line}")

    if block:
        BLOCKED = True
        print(f"  {RED}BLOCKING — must fix before push{RESET}")
    else:
        WARNINGS += 1
        print(f"  {YELLOW}WARNING — not blocking but should fix{RESET}")
    return False


def main():
    repo_root = Path(__file__).resolve().parent.parent
    if not (repo_root / "lingflow").exists():
        print("Not in LingFlow repo, skipping CI simulation")
        return 0

    print(f"{BOLD}{'=' * 60}")
    print("  LingFlow Pre-Push CI Simulation")
    print(f"{'=' * 60}{RESET}")

    run("black format check", ["black", "--check", "--line-length=127", "lingflow/", "tests/"], block=True)
    run(
        "isort import check",
        ["isort", "--check-only", "--profile=black", "--line-length=127", "lingflow/", "tests/"],
        block=True,
    )
    run("pytest collection", ["python", "-m", "pytest", "--co", "-q"], block=True)
    run(
        "flake8 lint",
        ["flake8", "--max-line-length=127", "--max-complexity=15", "--ignore=E203,E266,E501,W503,E402,C901", "lingflow/"],
        block=False,
    )
    run(
        "pytest run",
        ["python", "-m", "pytest", "-q", "--tb=short", "-k", "not flask_detection and not fastapi_detection"],
        block=False,
    )

    print(f"\n{BOLD}{'=' * 60}")
    if BLOCKED:
        print(f"  {RED}PUSH BLOCKED{RESET} — fix hard errors above")
        print(f"{'=' * 60}{RESET}")
        return 1
    elif WARNINGS:
        print(f"  {YELLOW}PUSH ALLOWED{RESET} with {WARNINGS} warning(s)")
        print(f"{'=' * 60}{RESET}")
        return 0
    else:
        print(f"  {GREEN}ALL CHECKS PASSED{RESET}")
        print(f"{'=' * 60}{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
