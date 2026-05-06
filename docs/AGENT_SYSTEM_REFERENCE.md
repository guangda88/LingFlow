# Agent System Reference

> Extracted from AGENTS.md on 2026-05-06. Source: `docs/AGENTS_ARCHIVE_20260506.md`

## Agent Types (6 agents, V1 and V2 formats coexist)

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

## V2 Format Features

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

## Agent Selection

Agents are matched based on `agent_type` in `Task`:
```python
task = Task(task_id="t1", name="Code Review", agent_type="review", ...)
```
The coordinator finds agents whose capabilities match the task requirements.
