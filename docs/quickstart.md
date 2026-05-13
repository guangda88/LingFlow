# Quick Start Guide

5 minutes to get lingflow running.

## Install

```bash
pip install lingflow
```

Or from source:

```bash
git clone https://github.com/guangda88/lingflow.git
cd lingflow
pip install -e .
```

Verify:

```bash
lingflow --version
# lingflow, version 3.8.0
```

## Initialize a Project

```bash
lingflow init
```

This creates a `.lingflow/` directory with default configuration.

## Core API

### Run a Skill

```python
from lingflow import lingflow

lf = lingflow()

result = lf.run_skill("brainstorming", {"topic": "new feature"})
print(result)
```

### Run a Workflow

Create `workflow.yaml`:

```yaml
name: "Code Review Pipeline"
tasks:
  - name: "Review code"
    agent_type: "reviewer"
    skill: "code_review"
    params:
      file_path: "src/main.py"
      dimensions:
        - code_quality
        - security
        - performance

  - name: "Run tests"
    agent_type: "tester"
    skill: "test_runner"
    depends_on: ["Review code"]
    params:
      target: "tests/"

  - name: "Verify fixes"
    agent_type: "implementation"
    skill: "verification"
    depends_on: ["Run tests"]
```

Execute:

```python
result = lf.run_workflow_file("workflow.yaml")
```

### Smart Compression

lingflow automatically manages context window usage:

```python
from lingflow.compression import compress_messages

messages = [
    {"role": "system", "content": "You are a coding assistant."},
    {"role": "user", "content": "Fix the bug in auth.py"},
    # ... long conversation history
]

compressed = compress_messages(messages, target_tokens=4000)
# Returns compressed messages preserving critical content
```

### Monitoring

```python
from lingflow.monitoring import OperationsMonitor

monitor = OperationsMonitor()

monitor.register_health_check("database", lambda: HealthCheckResult(
    component="database",
    healthy=True,
    message="Connection OK",
))

results = monitor.run_health_checks()
status = monitor.get_overall_health()
```

## Built-in Skills (32)

| Layer | Skills | Loading |
|-------|--------|---------|
| **L1 Core** | workflow-executor, task-runner, conditional-branch, loop-iterator, error-handler | Always loaded |
| **L2 Professional** | brainstorming, code-review, code-refactor, test-driven-development, systematic-debugging, verification | Always loaded |
| **L3 Extension** | writing-plans, api-doc-generator, ui-mockup-generator, ci-cd-orchestrator, deployment-automation, ... | Loaded on demand |

List available skills:

```python
from lingflow import lingflow
lf = lingflow()
skills = lf.list_skills()
for s in skills:
    print(f"  {s['name']}: {s['description']}")
```

## Configuration

Default config in `config.yaml`. Override via environment variables with `LINGFLOW_` prefix:

```bash
export LINGFLOW_LOG_LEVEL=DEBUG
export LINGFLOW_MAX_PARALLEL=4
```

## Next Steps

- [API Reference](api/lingflow.md)
- [Examples](examples/basic_usage.md)
- [Architecture Guide](guides/architecture.md)
- [CLI Guide](CLI_GUIDE.md)
