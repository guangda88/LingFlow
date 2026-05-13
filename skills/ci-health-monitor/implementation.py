"""CI Health Monitor — diagnose CI failures and generate fix suggestions.

Usage:
    from skills.ci_health_monitor.implementation import execute_skill

    result = execute_skill({
        "source": "local",       # "local" | "github" | "raw"
        "output": "...",          # raw CI output (for "raw" source)
        "repo": "lingflow",      # repo name (for "github" source)
    })
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

FAILURE_PATTERNS = [
    (
        "format",
        [
            r"black --check",
            r"would reformat",
            r"isort --check",
            r"import ordering",
        ],
    ),
    (
        "type",
        [
            r"error: Incompatible",
            r"error: Missing return",
            r"mypy",
        ],
    ),
    (
        "test",
        [
            r"FAILED",
            r"AssertionError",
            r"assert ",
        ],
    ),
    (
        "security",
        [
            r"bandit",
            r"Severity: (High|Medium)",
            r" B\d{3} ",
        ],
    ),
    (
        "dependency",
        [
            r"ModuleNotFoundError",
            r"ImportError",
            r"No module named",
        ],
    ),
    (
        "collection",
        [
            r"cannot collect",
            r"collection failure",
            r"ERROR collecting",
        ],
    ),
]

FIX_COMMANDS = {
    "format": "black --line-length=127 lingflow/ tests/ && isort --profile black --line-length=127 lingflow/ tests/",
    "type": "mypy lingflow/ --ignore-missing-imports --python-version=3.11",
    "dependency": "pip install -e '.[dev]'",
    "collection": "python -m pytest --co -q  # find collection errors",
}


def _classify_errors(output: str) -> Dict[str, List[str]]:
    """Classify errors in CI output by category."""
    classified = {}
    for category, patterns in FAILURE_PATTERNS:
        matches = []
        for pattern in patterns:
            for line in output.splitlines():
                if re.search(pattern, line, re.IGNORECASE):
                    matches.append(line.strip())
        if matches:
            classified[category] = matches[:10]
    return classified


def _extract_file_lines(output: str) -> List[Dict[str, Any]]:
    """Extract file:line references from CI output."""
    pattern = r"(?:lingflow|tests|skills)/[^\s:]+\.py(?::\d+)?"
    files = []
    seen = set()
    for match in re.finditer(pattern, output):
        ref = match.group(0)
        if ref not in seen:
            seen.add(ref)
            files.append({"ref": ref})
    return files[:20]


def _run_local_ci() -> str:
    """Run local CI simulation and capture output."""
    script = Path(__file__).resolve().parent.parent.parent / ".scripts" / "ci_simulate.py"
    if script.exists():
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.stdout + result.stderr
    return _run_basic_checks()


def _run_basic_checks() -> str:
    """Run basic CI checks if ci_simulate.py is not available."""
    output_lines = []
    checks = [
        ("black", ["black", "--check", "--line-length=127", "lingflow/"]),
        ("isort", ["isort", "--check-only", "--profile=black", "--line-length=127", "lingflow/"]),
        ("flake8", ["flake8", "--max-line-length=127", "--ignore=E203,E266,E501,W503,E402,C901", "lingflow/"]),
    ]
    for name, cmd in checks:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            output_lines.append(f"[FAIL] {name}:")
            output_lines.append(result.stdout)
            output_lines.append(result.stderr)
    return "\n".join(output_lines)


def _get_health_status(classified: Dict[str, List[str]]) -> str:
    """Determine overall health status."""
    blocking = set(classified.keys()) & {"collection", "dependency"}
    if blocking:
        return "RED"
    if "security" in classified:
        return "RED"
    if classified:
        return "YELLOW"
    return "GREEN"


def execute_skill(params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute CI health monitoring.

    Args:
        params: Dict with optional keys:
            - source: "local" | "github" | "raw" (default: "local")
            - output: raw CI output (for "raw" source)

    Returns:
        Dict with health status, classified errors, and fix suggestions.
    """
    source = params.get("source", "local")

    if source == "raw":
        output = params.get("output", "")
    elif source == "github":
        repo = params.get("repo", "")
        result = subprocess.run(
            ["gh", "run", "list", "-R", repo, "--limit", "1", "--json", "status,conclusion,databaseId"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout + result.stderr
    else:
        try:
            output = _run_local_ci()
        except Exception as e:
            output = f"Error running local CI: {e}"

    classified = _classify_errors(output)
    file_refs = _extract_file_lines(output)
    status = _get_health_status(classified)

    fix_suggestions = []
    for category in classified:
        cmd = FIX_COMMANDS.get(category)
        if cmd:
            fix_suggestions.append({"category": category, "command": cmd})

    report_lines = [
        f"CI Health Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 40,
        f"Status: {status}",
    ]
    if classified:
        for cat, errors in classified.items():
            report_lines.append(f"  {cat}: {len(errors)} issue(s)")
    else:
        report_lines.append("  No issues found")

    return {
        "status": status,
        "classified_errors": classified,
        "file_references": file_refs,
        "fix_suggestions": fix_suggestions,
        "report": "\n".join(report_lines),
        "raw_output_preview": output[:2000] if output else "",
    }
