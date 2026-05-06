# Security Reference

> Extracted from AGENTS.md on 2026-05-06. Source: `docs/AGENTS_ARCHIVE_20260506.md`

## SkillSandbox (`lingflow/common/sandbox.py`)

Process-isolated execution environment for skill code:
- **Process isolation**: Runs in separate `multiprocessing.Process`
- **Timeout**: Default 30s, configurable
- **Memory limit**: Default 100MB
- **Recursion depth limit**: Default 100
- **Loop iteration limit**: Default 1,000,000
- **Module whitelist**: Only `typing`, `dataclasses`, `datetime`, `math`, `time`
- **Safe builtins**: Limited set (abs, all, any, bool, dict, enumerate, filter, float, int, isinstance, len, list, map, max, min, range, reversed, round, set, sorted, str, sum, tuple, zip)
- **AST analysis**: `SecurityAnalyzer` performs static code analysis before execution

Default sandbox instance via `get_default_sandbox()` or convenience function `execute_in_sandbox(func, *args, timeout=None, **kwargs)`.

## Path Traversal Protection

- Skill name validation: regex `^[a-z0-9_-]+$`, length 3-50
- Workflow file path validation: `resolve()` + `relative_to()` check
- Symlink rejection for workflow files

## Pre-commit Security Checks

- `bandit` scan on `lingflow/`
- Custom `check-eval-usage` hook (blocks `eval()`/`exec()`)
- Custom `check-os-system` hook (blocks `os.system()`, suggests `subprocess.run()`)

## Sandbox Constraints Summary

Skill code with `implementation.py` runs in a sandbox:
- Cannot import `os`, `sys`, `subprocess`, or any module not in the whitelist
- Cannot use `eval()`, `exec()`, `open()`, `__import__`
- 30-second timeout, 100MB memory limit
- Max 1,000,000 loop iterations, max 100 recursion depth
