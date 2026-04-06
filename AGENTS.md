# LingFlow Agent Guide

**Version**: v3.9.1
**Status**: Production Ready
**Last Updated**: 2026-04-05

---

## Project Overview

LingFlow (灵通 工程流系统) is an intelligent software development workflow engine. It uses a skill-driven architecture with multi-agent coordination, smart context compression, and process-isolated sandbox execution to automate the full software engineering lifecycle.

### Core Philosophy

- **Skill-Driven Architecture**: Complex development workflows decomposed into composable, reusable skills organized in a three-layer architecture (L1/L2/L3)
- **Agent Coordination**: Multi-agent system with capability-based matching, intelligent task scheduling, and parallel execution
- **Smart Compression**: tiktoken-based token-aware context management with multi-strategy compression (30-50% token savings)
- **Process-Isolated Sandbox**: Skills execute in isolated processes with timeout, memory limits, module whitelists, and AST-level security analysis
- **Type-Safe**: `Result[T]` generic type for success/failure handling; strict mypy mode enabled

### Primary API Entry Point

The `LingFlow` class in `lingflow/__init__.py` provides a unified interface:

```python
from lingflow import LingFlow

lf = LingFlow()

# Execute a single skill
result = lf.run_skill("brainstorming", {"topic": "new feature"})

# Execute a workflow from YAML file
result = lf.run_workflow_file("test_workflow.yaml")

# Execute a workflow definition directly
result = lf.run_workflow({"tasks": [...]})
```

On import, LingFlow auto-initializes:
1. Smart compression (`SmartContextCompressor`, max_tokens=180000)
2. Context manager (session persistence via `~/.claude/projects/lingflow/context/`)
3. Session resume (displays last session summary on stderr)

---

## Essential Commands

### Testing

```bash
# Run full test suite via pytest
pytest

# Run with markers
pytest -m unit          # Unit tests only
pytest -m e2e           # End-to-end tests
pytest -m snapshot      # Snapshot tests
pytest -m scenario      # Scenario tests
pytest -m "not slow"    # Skip slow tests

# Run with coverage
pytest --cov=lingflow --cov-report=html

# Parallel execution (requires pytest-xdist)
pytest -n auto

# Quick system verification
python verify_system_simple.py
python test_comprehensive.py

# Demo
python agent_coordinator.py
```

### Linting & Formatting

```bash
# Format with black (line-length=127)
black --line-length=127 lingflow/

# Sort imports
isort --profile black --line-length=127 lingflow/

# Lint with flake8
flake8 --max-line-length=127 --max-complexity=15 lingflow/

# Type check with mypy (strict mode)
mypy lingflow/

# Security scan
bandit -r lingflow/ -f txt

# All pre-commit hooks
pre-commit run --all-files
```

### Git Operations

```bash
git push origin master --tags
git push github master --tags
./push_to_remote.sh
```

---

## Project Structure

```
LingFlow/
├── lingflow/                        # Main Python package
│   ├── __init__.py                  # LingFlow class, version, auto-init
│   ├── cli.py                       # CLI interface
│   ├── bootstrap.py                 # Bootstrap utilities
│   ├── ai_friendly.py               # AI-friendly utilities
│   ├── core/                        # Core abstractions
│   │   ├── config.py                # LingFlowConfig dataclass
│   │   ├── types.py                 # Result[T] generic type
│   │   └── skill.py                 # BaseSkill, FunctionSkill, SkillRegistry (singleton)
│   ├── coordination/                # Agent coordination
│   │   ├── base.py                  # BaseCoordinator ABC
│   │   ├── coordinator.py           # AgentCoordinator (419 lines)
│   │   ├── registry.py              # AgentRegistry
│   │   ├── agent.py                 # Agent class
│   │   └── adapter.py               # Agent adapters
│   ├── common/                      # Shared modules
│   │   ├── models.py                # AgentConfig, Task, TaskResult, TaskPriority, AgentStatus
│   │   ├── exceptions.py            # Full exception hierarchy
│   │   ├── sandbox.py               # SkillSandbox (process-isolated execution)
│   │   ├── security_analyzer.py     # AST-based code security analysis
│   │   ├── audit_logger.py          # Audit logging
│   │   ├── config.py                # Global config access
│   │   ├── logger.py                # Logging setup
│   │   └── skill_manager.py         # Skill management
│   ├── compression/                 # Context compression
│   │   ├── compressor.py            # ContextCompressor, AdvancedContextCompressor
│   │   ├── smart_compressor.py      # SmartContextCompressor (tiktoken-based)
│   │   └── config.py                # Compression config
│   ├── workflow/                    # Workflow engine
│   │   ├── orchestrator.py          # WorkflowOrchestrator (252 lines)
│   │   └── cache.py                 # Workflow caching
│   ├── context/                     # Context management
│   │   ├── manager.py               # ContextManager (session persistence)
│   │   ├── session.py               # Session handling
│   │   └── auto_resume.py           # Auto session resume
│   ├── code_review/                 # Code review framework
│   │   └── core/
│   │       ├── base_reviewer.py     # BaseCodeReviewer
│   │       ├── rule_engine.py       # RuleEngine, Rule
│   │       ├── scorer.py            # QualityScorer
│   │       ├── severity.py          # Severity levels
│   │       └── reporter.py          # ReportGenerator
│   ├── self_optimizer/              # Self-optimization system
│   │   ├── __init__.py              # quick_optimize(), check_and_optimize()
│   │   ├── optimizer.py             # ProcessIsolatedOptimizer, SynchronousOptimizer
│   │   ├── trigger.py               # OptimizationTrigger, TriggerInfo
│   │   ├── evaluator.py             # StructureEvaluator
│   │   ├── performance_evaluator.py # PerformanceEvaluator
│   │   ├── simplicity_evaluator.py  # SimplicityEvaluator
│   │   ├── advisor.py               # OptimizationAdvisor
│   │   ├── config.py                # OptimizationConfig
│   │   ├── phase4/                  # Bayesian optimization
│   │   └── phase5/                  # Learning system
│   ├── testing/                     # Testing framework
│   │   ├── unit/                    # Unit test utilities
│   │   ├── e2e/                     # E2E test utilities
│   │   ├── snapshot/                # Snapshot testing
│   │   ├── scenarios/               # Scenario tests
│   │   ├── fixtures/                # Test fixtures
│   │   ├── ci/                      # CI test config
│   │   ├── ai_runner.py             # AI-powered test runner
│   │   ├── scenario.py              # Scenario runner
│   │   ├── snapshot.py              # Snapshot runner
│   │   └── test_server.py           # Test server
│   ├── monitoring/                  # Operations monitoring
│   │   ├── operations_monitor.py    # OperationsMonitor
│   │   └── default_checks.py        # Default health checks
│   ├── feedback/                    # Feedback collection
│   │   └── collector.py             # FeedbackCollector
│   ├── utils/                       # Utilities
│   │   ├── performance.py           # Performance utilities
│   │   ├── rate_limiter.py          # Rate limiting
│   │   └── sampling.py              # Sampling utilities
│   ├── requirements/                # Requirements traceability
│   │   └── traceability.py          # RequirementsTraceability
│   ├── guardrail/                   # Guardrails (placeholder)
│   └── hooks/                       # Hook system
│       └── auto_optimize_hook.py    # Auto-optimization hook
├── skills/                          # Skill definitions (32 skills)
│   ├── skills.json                  # Flat skill registry
│   ├── skills-layer-configuration.yaml  # L1/L2/L3 layer config
│   ├── brainstorming/
│   ├── writing-plans/
│   ├── test-driven-development/
│   ├── systematic-debugging/
│   ├── subagent-driven-development/
│   ├── verification-before-completion/
│   ├── using-git-worktrees/
│   ├── finishing-a-development-branch/
│   ├── dispatching-parallel-agents/
│   ├── skill-creator/
│   ├── workflow-executor/
│   ├── task-runner/
│   ├── conditional-branch/
│   ├── loop-iterator/
│   ├── error-handler/
│   ├── code-review/
│   ├── code-refactor/
│   ├── api-doc-generator/
│   ├── ui-mockup-generator/
│   ├── database-schema-designer/
│   ├── ci-cd-orchestrator/
│   ├── deployment-automation/
│   ├── environment-manager/
│   ├── notification/
│   ├── database-export/
│   ├── test-runner/
│   ├── skill-analytics/
│   ├── skill-categorization/
│   ├── skill-integration/
│   ├── skill-templates/
│   ├── skill-testing/
│   └── skill-versioning/
├── agents/                          # Agent configurations
│   ├── agents.json                  # V1 format (6 agents)
│   └── agents.v2.json               # V2 capability-based format (6 agents)
├── hooks/                           # Hook definitions
│   ├── hooks.json                   # 5 hooks (session-start, pre/post-implementation, pre/post-review)
│   ├── session-start/
│   ├── pre-implementation/
│   ├── post-implementation/
│   ├── pre-review/
│   └── post-review/
├── .scripts/                        # Tool scripts
│   ├── check_docstrings.py
│   ├── check_type_hints.py
│   ├── check_complexity.py
│   ├── verify_system.py
│   └── skill_trigger.py
├── lingflow-core/                   # Core subpackage
│   ├── api/
│   ├── core/
│   ├── integration/
│   ├── tests/
│   └── utils/
├── lingflow-claude-code/            # Claude Code integration
│   ├── hooks/
│   └── tests/
├── lingflow-mcp-server/             # MCP server integration
│   ├── tests/
│   └── tools/
├── tests/                           # Test suite (pytest)
├── docs/                            # Documentation
├── config.yaml                      # Main configuration
├── .pytest.ini                      # Pytest configuration
├── .pre-commit-config.yaml          # Pre-commit hooks
├── pyproject.toml                   # Black, flake8, mypy config
├── setup.py                         # Package setup (pip installable)
├── requirements.txt                 # Dependencies
├── VERSION                          # Version file (3.5.7)
└── agent_coordinator.py             # Demo script (thin wrapper, imports from lingflow.*)
```

---

## Core Components

### LingFlow Class (`lingflow/__init__.py`)

Unified entry point. Methods:
- `run_skill(skill_name, params)` — Execute a single skill
- `run_workflow_file(filepath)` — Load and execute a YAML/JSON workflow (with path traversal protection)
- `run_workflow(workflow_def)` — Execute an in-memory workflow definition

Uses lazy imports for `AgentCoordinator` and `WorkflowOrchestrator` to avoid circular dependencies.

### AgentCoordinator (`lingflow/coordination/coordinator.py`)

Main coordination engine (419 lines). Key responsibilities:
- Register 6 default agents from `AgentConfig` dataclasses
- Submit and execute tasks with context compression
- Parallel task execution via `asyncio.Semaphore`
- Skill execution with sandbox security validation
- Path traversal protection on skill loading

Key methods:
- `submit_task(task)` — Queue a task
- `execute_tasks_parallel(tasks, max_parallel)` — Async parallel execution
- `execute_skill(skill_name, params)` — Execute a skill with sandbox validation
- `list_skills()` — Discover available skills from `skills/` directory
- `get_status()` — Coordinator status with compression stats

### WorkflowOrchestrator (`lingflow/workflow/orchestrator.py`)

Workflow engine (252 lines). Handles:
- YAML workflow loading with dependency parsing
- Dependency-aware task scheduling
- Parallel execution of independent tasks
- Priority-based task ordering (CRITICAL > HIGH > NORMAL > LOW)
- Sync wrapper via `asyncio.run()` for the async engine

Key methods:
- `load_workflow_from_yaml(filepath)` — Parse YAML into `Task` list
- `execute(tasks, max_parallel)` — Synchronous workflow execution
- `execute_workflow(tasks, max_parallel)` — Async workflow execution

### SkillRegistry (`lingflow/core/skill.py`)

Singleton registry for skill registration. Supports:
- `BaseSkill` — Abstract base class with `execute()`, `_execute_impl()`, `validate_params()`
- `FunctionSkill` — Wraps any `Callable` as a skill
- `register()`, `register_function()`, `get()`, `list()`, `has()`

### Result[T] (`lingflow/core/types.py`)

Generic result type for success/failure handling:
```python
result = Result.ok(data)
result = Result.fail("error message", code="LF_ERROR")

result.success   # bool
result.is_ok     # bool (alias)
result.is_error  # bool
result.data      # Optional[T]
result.error     # Optional[str]
result.to_dict() # Dict
```

### Data Models (`lingflow/common/models.py`)

All data models use `@dataclass`:
- `AgentConfig` — name, description, capabilities, max_tasks, context_limit (8000), timeout (300s), parallel_safe
- `Task` — task_id, name, description, priority (TaskPriority), agent_type, dependencies, context
- `TaskResult` — task_id, success, output, error, execution_time, agent_used
- `TaskPriority` — CRITICAL=0, HIGH=1, NORMAL=2, LOW=3
- `AgentStatus` — IDLE, BUSY, FAILED

### Exception Hierarchy (`lingflow/common/exceptions.py`)

```
LingFlowError (base, with code + details)
├── SkillError
│   ├── SkillNotFoundError
│   ├── SkillLoadError
│   └── SkillExecutionError
├── WorkflowError
│   ├── WorkflowValidationError
│   └── WorkflowExecutionError
├── AgentError
│   ├── AgentNotFoundError
│   └── AgentExecutionError
├── CompressionError
├── ConfigurationError
└── ValidationError
```

### LingFlowConfig (`lingflow/core/config.py`)

Type-safe configuration dataclass with validation:
- `max_parallel` (2), `max_iterations` (100), `workflow_timeout` (600s)
- `skills_path` ("skills"), `skill_timeout` (30s), `skill_cache_enabled` (False)
- `agent_timeout` (300s), `agent_context_limit` (8000)
- `compression_enabled` (True), `compression_target_tokens` (4000)
- `log_level` ("INFO")
- `from_dict()` / `to_dict()` for backward compatibility

---

## Skill System

### Three-Layer Architecture (`skills/skills-layer-configuration.yaml`)

Skills are organized in three layers with different loading/unloading strategies:

| Layer | Description | Loading | Unloading | Skills |
|-------|-------------|---------|-----------|--------|
| **L1** | Core scheduling | eager | never | workflow-executor, task-runner, conditional-branch, loop-iterator, error-handler |
| **L2** | Professional capabilities | eager | never | brainstorming, systematic-debugging, verification-before-completion, code-review, code-refactor, test-runner, test-driven-development, using-git-worktrees, finishing-a-development-branch, notification, skill-creator |
| **L3** | Extended capabilities | lazy | after_task (5min idle) | writing-plans, api-doc-generator, ui-mockup-generator, database-schema-designer, ci-cd-orchestrator, deployment-automation, environment-manager, database-export, dispatching-parallel-agents, subagent-driven-development, skill-integration, skill-categorization, skill-versioning, skill-analytics, skill-templates, skill-testing |

### L2 Skill Groups

L2 skills are organized into groups with execution constraints:

- **code_quality** (mutex): code-review, code-refactor
- **development_flow** (ordered): brainstorming → systematic-debugging → verification-before-completion
- **testing** (mutex): test-runner, test-driven-development
- **version_control** (mutex): using-git-worktrees, finishing-a-development-branch
- **common_services** (composable): notification, skill-creator

### Routing Rules

Priority-based routing from `skills-layer-configuration.yaml`:
- `workflow|yaml` → L1.workflow-executor (priority 10)
- `review|审查|检查` → L2.code_review (priority 9)
- `debug|bug|错误` → L2.systematic_debugging (priority 9)
- `api.*doc|接口文档` → L3.api_doc_generator (priority 7)
- `ui|mockup|原型` → L3.ui_mockup_generator (priority 7)
- `database.*design|schema` → L3.database_schema_designer (priority 7)
- `ci.*cd|pipeline` → L3.ci_cd_orchestrator (priority 7)
- `deploy|部署` → L3.deployment_automation (priority 7)

### Core Skills (L2)

1. **brainstorming** — Design and ideation (MUST use before creative work)
   - Triggers: feature, build, create, implement, plan, design
   - HARD-GATE: Cannot proceed without design approval

2. **writing-plans** — Multi-step task planning (L3, loaded on demand)
   - Triggers: plan, implementation plan, break down, spec
   - Depends on: brainstorming

3. **test-driven-development** — TDD enforcement
   - Triggers: test, write test, implement, tdd
   - Depends on: writing-plans
   - Enforces RED-GREEN-REFACTOR cycle

4. **systematic-debugging** — 4-phase root cause analysis
   - Triggers: debug, fix, error, issue, broken
   - Phases: observe → isolate → hypothesize → verify

5. **subagent-driven-development** — Rapid iteration with two-phase review
   - Triggers: execute plan, implement plan
   - Depends on: writing-plans

6. **verification-before-completion** — Ensures problems are actually fixed
   - Triggers: verify, check, confirm fix

7. **using-git-worktrees** — Isolated workspace creation
   - Triggers: new branch, start work, begin development
   - Depends on: brainstorming

8. **finishing-a-development-branch** — Branch cleanup and merge options
   - Triggers: done, complete, finish, ready to merge
   - Options: merge, PR, keep, discard

9. **code-review** — 8-dimension code review
   - Triggers: review, code review, check code
   - Dimensions: code_quality, architecture, performance, security, maintainability, best_practices, consistency, bug_analysis

10. **dispatching-parallel-agents** — Parallel multi-agent coordination (L3)
    - Triggers: parallel, concurrent, simultaneous
    - max_parallel: 3, dependency-aware

### Workflow Skills (L1)

- **workflow-executor** — Execute YAML/JSON workflows
- **task-runner** — Execute single tasks (skill calls)
- **conditional-branch** — If/else branching in workflows
- **loop-iterator** — Loop execution in workflows (max 100 iterations)
- **error-handler** — Retry and fallback on task failure (max 3 retries)

### Skill Metadata

Each skill in `skills/skills.json` has:
- `name` — Unique identifier (kebab-case, `[a-z0-9_-]+`)
- `description` — Purpose (bilingual Chinese/English)
- `path` — Path to `SKILL.md`
- `triggers` — Keywords for auto-triggering
- `depends_on` — Required prerequisite skills

Skills with implementation code have an `implementation.py` file with a required `execute_skill(params: Dict) -> Dict` function.

---

## Agent System

### Agent Types (6 agents, V1 and V2 formats coexist)

Both `agents/agents.json` (V1, flat capability list) and `agents/agents.v2.json` (V2, capability-based with per-capability config) define the same 6 agents:

1. **implementation** — Code generation, refactoring, testing, documentation
   - Context limit: 8000 tokens, Timeout: 300s, max_concurrent: 3

2. **reviewer** — Code review (8 dimensions), design review, security check, quality analysis
   - Context limit: 12000 tokens, Timeout: 180s, max_concurrent: 2

3. **tester** — Test generation (pytest/jest), test execution, coverage analysis, performance testing
   - Context limit: 6000 tokens, Timeout: 600s, max_concurrent: 2

4. **debugger** — Error analysis, root cause, fix generation, log analysis
   - Context limit: 10000 tokens, Timeout: 300s, max_concurrent: 1, **not parallel_safe**

5. **architect** — System design, architecture review, API design, schema design
   - Context limit: 15000 tokens, Timeout: 600s, max_concurrent: 1

6. **documentation** — Doc generation, API docs, tutorials, README
   - Context limit: 5000 tokens, Timeout: 300s, max_concurrent: 2

### V2 Format Features

`agents.v2.json` adds per-capability configuration:
```json
{
  "code_review": {
    "description": "Execute code review",
    "context_limit": 12000,
    "timeout": 180,
    "languages": ["python", "javascript", "..."],
    "review_dimensions": ["code_quality", "architecture", "..."]
  }
}
```

Capability matching strategy: `exact_or_broader` with fallback enabled.

### Agent Selection

Agents are matched based on `agent_type` in `Task`:
```python
task = Task(task_id="t1", name="Code Review", agent_type="review", ...)
```
The coordinator finds agents whose capabilities match the task requirements.

---

## Security

### SkillSandbox (`lingflow/common/sandbox.py`)

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

### Path Traversal Protection

- Skill name validation: regex `^[a-z0-9_-]+$`, length 3-50
- Workflow file path validation: `resolve()` + `relative_to()` check
- Symlink rejection for workflow files

### Pre-commit Security Checks

- `bandit` scan on `lingflow/`
- Custom `check-eval-usage` hook (blocks `eval()`/`exec()`)
- Custom `check-os-system` hook (blocks `os.system()`, suggests `subprocess.run()`)

---

## Smart Compression

### SmartContextCompressor (`lingflow/compression/smart_compressor.py`)

tiktoken-based intelligent context compression with:

1. **TokenEstimator** — Precise token counting via tiktoken (cl100k_base encoding), falls back to character estimation (ratio 0.25-0.28)
2. **MessageScorer** — Multi-dimensional scoring: role priority (system > user > assistant > tool), content importance (critical keywords), recency (exponential decay), length adjustment
3. **TieredCompressionStrategy** — Five tiers: KEEP_ALL, KEEP_IMPORTANT, COMPRESS, SUMMARIZE, DROP
4. **ConversationSummarizer** — Generates summaries preserving tasks, decisions, and errors

### Compression Modes

| Mode | Target Ratio | Message Compress Ratio |
|------|-------------|----------------------|
| normal | 50% | 70% |
| aggressive | 30% | 50% |
| emergency | 20% | 30% |

### Thresholds (default)

- **Warning**: 75% of max_tokens
- **Compress**: 85% of max_tokens
- **Critical**: 95% of max_tokens (emergency compression)

---

## Self-Optimizer System

### Components

- **OptimizationTrigger** — Checks conditions and triggers optimization with priority
- **ProcessIsolatedOptimizer** / **SynchronousOptimizer** — Execute optimizations
- **StructureEvaluator** / **PerformanceEvaluator** / **SimplicityEvaluator** — Multi-goal evaluation
- **OptimizationAdvisor** — Provides optimization recommendations
- **Phase 4** — Bayesian optimization
- **Phase 5** — Learning system

### Convenience Functions

```python
from lingflow.self_optimizer import quick_optimize, check_and_optimize

# Quick optimize
result = quick_optimize(target=".", goal="structure")

# Check conditions and optimize if needed
should_optimize, result = check_and_optimize(context={}, target=".", goal="performance")
```

Optimization goals: `structure`, `performance`, `simplicity`

---

## Code Review Framework

Modular code review system in `lingflow/code_review/`:
- **BaseCodeReviewer** — Abstract base for reviewers
- **RuleEngine** + **Rule** — Pluggable rule system
- **QualityScorer** — Quantitative quality scoring
- **Severity** — Issue severity levels
- **ReportGenerator** — Review report generation

---

## Hooks

5 hooks defined in `hooks/hooks.json`:

| Hook | Trigger Point |
|------|--------------|
| `session-start` | When a new session begins |
| `pre-implementation` | Before code implementation |
| `post-implementation` | After code implementation |
| `pre-review` | Before code review |
| `post-review` | After code review |

---

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

---

## Code Style

### Formatter & Linter Configuration

| Tool | Settings |
|------|----------|
| **black** | line-length=127, target=py311 |
| **isort** | profile=black, line-length=127 |
| **flake8** | max-line-length=127, max-complexity=15, ignore=E203,E266,E501,W503,E402 |
| **mypy** | python_version=3.11, strict mode (disallow_untyped_defs, disallow_incomplete_defs, strict_optional, strict_equality) |
| **bandit** | scans `lingflow/`, excludes `tests/` |

### Pre-commit Hooks (`.pre-commit-config.yaml`)

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

### Docstrings

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

### Dataclasses

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

### Async/Await

Use `asyncio` for parallel operations:
```python
async def execute_tasks_parallel(self, tasks: List[Task], max_parallel: int = 2) -> Dict[str, TaskResult]:
    semaphore = asyncio.Semaphore(max_parallel)
    tasks_to_execute = [asyncio.create_task(self._execute_one_task(task, semaphore)) for task in tasks]
    results_list = await asyncio.gather(*tasks_to_execute, return_exceptions=True)
    return self._process_task_results(results_list)
```

---

## Testing

### Framework

Pytest-based with `.pytest.ini` configuration:

```ini
[pytest]
python_files = test_*.py
asyncio_mode = auto
markers = unit, snapshot, scenario, e2e, ci, slow
```

### Test Markers

| Marker | Purpose |
|--------|---------|
| `unit` | Unit tests |
| `snapshot` | Snapshot/regression tests |
| `scenario` | Scenario-based tests |
| `e2e` | End-to-end tests |
| `ci` | CI/CD integration tests |
| `slow` | Slow running tests |

### Test Structure

```
lingflow/testing/
├── unit/          # Unit test utilities
├── e2e/           # E2E test utilities
├── snapshot/      # Snapshot testing
├── scenarios/     # Scenario definitions
├── fixtures/      # Shared fixtures
├── ci/            # CI configuration
tests/             # Root test directory
```

### CI Pipelines (`.github/workflows/`)

1. **ci.yml** — Main CI pipeline
2. **code-quality.yml** — Code quality + security scanning
3. **testing-framework.yml** — Comprehensive test execution

---

## Workflow Patterns

### Standard Development Workflow

```
1. brainstorming (design)
   ↓
2. writing-plans (implementation plan)
   ↓
3. using-git-worktrees (create workspace)
   ↓
4. test-driven-development (implement + test)
   ↓
5. code-review (get feedback)
   ↓
6. verification-before-completion (verify fixes)
   ↓
7. finishing-a-development-branch (cleanup)
```

### Parallel Development Workflow

```
1. brainstorming (design)
   ↓
2. writing-plans (detailed plan with dependencies)
   ↓
3. using-git-worktrees (isolated workspaces)
   ↓
4. dispatching-parallel-agents (execute in parallel)
   ├─ task-1 (implementation agent)
   ├─ task-2 (testing agent)
   └─ task-3 (documentation agent)
   ↓
5. code-review (aggregate review)
   ↓
6. finishing-a-development-branch (merge)
```

### Debugging Workflow

```
1. systematic-debugging
   ├─ Observe the issue
   ├─ Isolate the problem
   ├─ Form hypothesis
   └─ Verify hypothesis
   ↓
2. test-driven-development (fix + test)
   ↓
3. verification-before-completion
```

---

## Common Tasks

### Adding a New Skill

1. Create skill directory: `skills/my-new-skill/`
2. Create `SKILL.md` with frontmatter, gates, triggers, process, checklists
3. (Optional) Create `implementation.py` with `execute_skill(params: Dict) -> Dict`
4. Add to `skills/skills.json`
5. Add to appropriate layer in `skills/skills-layer-configuration.yaml`
6. Run: `python .scripts/skill_trigger.py`

### Adding a New Agent Type

1. Add to `agents/agents.json` (V1) and/or `agents/agents.v2.json` (V2)
2. Agent is auto-registered by `AgentCoordinator._register_default_agents()`
3. Run tests: `pytest`

### Creating a New Test

1. Create `test_*.py` in `tests/` or appropriate subdirectory
2. Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.e2e`, etc.
3. Run: `pytest`

---

## Important Gotchas

### Skill Dependencies

Skills have strict dependency chains from `skills/skills-layer-configuration.yaml`:
- `brainstorming` → `systematic-debugging` → `verification-before-completion`
- `code-review` → `code-refactor` (refactor requires review first)
- `workflow-executor` → `task-runner`
- `brainstorming` → `writing-plans` → `test-driven-development`

### Mutex Groups

These skill pairs cannot run simultaneously:
- code-review / code-refactor
- test-runner / test-driven-development
- using-git-worktrees / finishing-a-development-branch

### Sandbox Constraints

Skill code with `implementation.py` runs in a sandbox:
- Cannot import `os`, `sys`, `subprocess`, or any module not in the whitelist
- Cannot use `eval()`, `exec()`, `open()`, `__import__`
- 30-second timeout, 100MB memory limit
- Max 1,000,000 loop iterations, max 100 recursion depth

### Parallel Execution

- Tasks must be independent (no shared file modifications)
- Not all agents are `parallel_safe` (debugging agent is NOT)
- Default max parallel: 2 (configurable)
- Max scheduling iterations: 100 (prevents infinite loops)

### Context Compression

- Default max_tokens: 180,000
- Warning at 75%, auto-compress at 85%, emergency at 95%
- System messages always preserved
- `requirements`, `constraints`, `critical_requirements` sections preserved

### Host Infrastructure Paths

这些是主机上的关键路径，不要随意更改：

| 路径 | 用途 | 说明 |
|------|------|------|
| `/home/ai/lingtongask/.openlist/` | OpenList 服务 | 二进制 + 数据目录，端口 4255 |
| `/home/ai/lingtongask/.openlist/data/` | OpenList 数据 | config.json, data.db, 日志 |
| `/data/openlist_data_backup/` | OpenList 备份 | backup.json 含所有网盘存储配置 |
| `/home/ai/.config/rclone/rclone.conf` | rclone 配置 | 连接 OpenList WebDAV (openlist remote) |
| `/mnt/openlist/` | rclone 挂载点 | 通过 rclone mount 挂载 OpenList 的所有网盘 |
| `/opt/openlist/` | 旧版 OpenList | 端口 2455，已停用，数据库 63GB 不再使用 |

**OpenList 网盘列表**（7个）：115 Open、百度云x2、阿里云盘、夸克、豆包、一刻相册

**systemd 自启服务**：`openlist.service`、`rclone-openlist.service`（依赖前者）

---

## Dependencies

### Required

```
tiktoken>=0.5.0       # Token counting for smart compression
```

### Dev Dependencies

```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio
pytest-xdist          # Parallel test execution
pydantic
black                 # Formatting
flake8                # Linting
isort                 # Import sorting
mypy                  # Type checking
bandit                # Security scanning
```

### Python Version

- Minimum: Python 3.8+ (per `setup.py`)
- Target: Python 3.11 (per `pyproject.toml`)

### Installation

```bash
pip install -e .              # Install in development mode
pip install -e ".[dev]"       # Install with dev dependencies
```

---

## Resources

### Key Files

- `lingflow/__init__.py` — LingFlow class, primary API
- `lingflow/coordination/coordinator.py` — AgentCoordinator
- `lingflow/workflow/orchestrator.py` — WorkflowOrchestrator
- `lingflow/compression/smart_compressor.py` — SmartContextCompressor
- `lingflow/common/sandbox.py` — SkillSandbox
- `lingflow/common/exceptions.py` — Exception hierarchy
- `lingflow/core/types.py` — Result[T] type
- `lingflow/core/skill.py` — Skill system (BaseSkill, SkillRegistry)
- `skills/skills-layer-configuration.yaml` — Three-layer skill architecture
- `agents/agents.v2.json` — Capability-based agent definitions

### Configuration Files

- `config.yaml` — Main configuration (agents, compression, logging, skills, workflow)
- `.pytest.ini` — Test configuration
- `pyproject.toml` — Formatter/linter/type checker settings
- `.pre-commit-config.yaml` — Pre-commit hooks
- `setup.py` — Package installation

---

## Project Status

**Version**: v3.5.7
**Last Update**: 2026-03-31
**Status**: Production Ready

**Maintained by**: LingFlow Development Team
**Repository**: http://zhinenggitea.iepose.cn/guangda/LingFlow
