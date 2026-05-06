# Code Conventions Reference

> Extracted from AGENTS.md on 2026-05-06. Source: `docs/AGENTS_ARCHIVE_20260506.md`

## Naming Conventions

### Python Code

- **Classes**: PascalCase (`AgentCoordinator`, `TaskResult`)
- **Functions/Methods**: snake_case (`execute_task`, `compress_context`)
- **Constants**: UPPER_CASE (`MAX_SCHEDULING_ITERATIONS`, `DEFAULT_MAX_PARALLEL`)
- **Variables**: snake_case (`task_id`, `execution_time`)
- **Private members**: Leading underscore (`_execute_impl`, `_load_skill_module`)
- **Type hints**: Required on all function parameters and returns (mypy strict mode)

### File Names

- Python modules: `snake_case.py`
- Configuration: `snake_case.json` / `snake_case.yaml`
- Documentation: `UPPERCASE_SNAKE_CASE.md`
- Shell scripts: `snake_case.sh`

### Git Conventions

- **Branches**: kebab-case (`feature/add-auth-system`)
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`)
- **Tags**: Semantic versioning (`v3.5.7`)

## Formatter & Linter Configuration

| Tool | Settings |
|------|----------|
| **black** | line-length=127, target=py311 |
| **isort** | profile=black, line-length=127 |
| **flake8** | max-line-length=127, max-complexity=15, ignore=E203,E266,E501,W503,E402 |
| **mypy** | python_version=3.11, strict mode (disallow_untyped_defs, disallow_incomplete_defs, strict_optional, strict_equality) |
| **bandit** | scans `lingflow/`, excludes `tests/` |

## Pre-commit Hooks (`.pre-commit-config.yaml`)

1. **black** — Code formatting
2. **isort** — Import sorting
3. **flake8** — Linting (with flake8-docstrings)
4. **mypy** — Type checking (with `--ignore-missing-imports`)
5. **bandit** — Security scanning
6. **pre-commit-hooks** — Large files (500KB max), JSON/YAML/TOML validation, merge conflicts, debug statements, trailing whitespace, line endings
7. **Custom checks**:
   - Version consistency (outdated version references in docs)
   - eval/exec usage detection
   - os.system usage detection
   - Missing docstrings in public functions
   - Missing type hints in public functions

## Docstrings

Google-style, bilingual (Chinese + English):
```python
def execute(self, func: Callable, *args, **kwargs) -> Any:
    """在沙箱中执行函数

    Args:
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        函数执行结果

    Raises:
        SandboxError: 沙箱执行错误
        SandboxTimeoutError: 执行超时
    """
```

## Dataclasses

All data models use `@dataclass`:
```python
@dataclass
class AgentConfig:
    name: str
    description: str
    capabilities: List[str]
    max_tasks: int = 1
    context_limit: int = 8000
    timeout: int = 300
    parallel_safe: bool = True
```

## Async/Await

Use `asyncio` for parallel operations:
```python
async def execute_tasks_parallel(self, tasks: List[Task], max_parallel: int = 2) -> Dict[str, TaskResult]:
    semaphore = asyncio.Semaphore(max_parallel)
    tasks_to_execute = [asyncio.create_task(self._execute_one_task(task, semaphore)) for task in tasks]
    results_list = await asyncio.gather(*tasks_to_execute, return_exceptions=True)
    return self._process_task_results(results_list)
```
