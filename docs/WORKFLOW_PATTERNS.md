# Workflow Patterns Reference

> Extracted from AGENTS.md on 2026-05-06. Source: `docs/AGENTS_ARCHIVE_20260506.md`

## Standard Development Workflow

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

## Parallel Development Workflow

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

## Debugging Workflow

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

## Parallel Execution Notes

- Tasks must be independent (no shared file modifications)
- Not all agents are `parallel_safe` (debugging agent is NOT)
- Default max parallel: 2 (configurable)
- Max scheduling iterations: 100 (prevents infinite loops)
