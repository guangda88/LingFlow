# Self-Optimizer Reference

> Extracted from AGENTS.md on 2026-05-06. Source: `docs/AGENTS_ARCHIVE_20260506.md`

## Components

- **OptimizationTrigger** — Checks conditions and triggers optimization with priority
- **ProcessIsolatedOptimizer** / **SynchronousOptimizer** — Execute optimizations
- **StructureEvaluator** / **PerformanceEvaluator** / **SimplicityEvaluator** — Multi-goal evaluation
- **OptimizationAdvisor** — Provides optimization recommendations
- **Phase 4** — Bayesian optimization
- **Phase 5** — Learning system

## Convenience Functions

```python
from lingflow.self_optimizer import quick_optimize, check_and_optimize

# Quick optimize
result = quick_optimize(target=".", goal="structure")

# Check conditions and optimize if needed
should_optimize, result = check_and_optimize(context={}, target=".", goal="performance")
```

Optimization goals: `structure`, `performance`, `simplicity`

## Code Review Framework

Modular code review system in `lingflow/code_review/`:
- **BaseCodeReviewer** — Abstract base for reviewers
- **RuleEngine** + **Rule** — Pluggable rule system
- **QualityScorer** — Quantitative quality scoring
- **Severity** — Issue severity levels
- **ReportGenerator** — Review report generation

## Hooks

5 hooks defined in `hooks/hooks.json`:

| Hook | Trigger Point |
|------|--------------|
| `session-start` | When a new session begins |
| `pre-implementation` | Before code implementation |
| `post-implementation` | After code implementation |
| `pre-review` | Before code review |
| `post-review` | After code review |
