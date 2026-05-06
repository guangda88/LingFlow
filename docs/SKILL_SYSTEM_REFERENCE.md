# Skill System Reference

> Extracted from AGENTS.md on 2026-05-06. Source: `docs/AGENTS_ARCHIVE_20260506.md`

## Three-Layer Architecture (`skills/skills-layer-configuration.yaml`)

Skills are organized in three layers with different loading/unloading strategies:

| Layer | Description | Loading | Unloading | Skills |
|-------|-------------|---------|-----------|--------|
| **L1** | Core scheduling | eager | never | workflow-executor, task-runner, conditional-branch, loop-iterator, error-handler |
| **L2** | Professional capabilities | eager | never | brainstorming, systematic-debugging, verification-before-completion, code-review, code-refactor, test-runner, test-driven-development, using-git-worktrees, finishing-a-development-branch, notification, skill-creator |
| **L3** | Extended capabilities | lazy | after_task (5min idle) | writing-plans, api-doc-generator, ui-mockup-generator, database-schema-designer, ci-cd-orchestrator, deployment-automation, environment-manager, database-export, dispatching-parallel-agents, subagent-driven-development, skill-integration, skill-categorization, skill-versioning, skill-analytics, skill-templates, skill-testing |

## L2 Skill Groups

L2 skills are organized into groups with execution constraints:

- **code_quality** (mutex): code-review, code-refactor
- **development_flow** (ordered): brainstorming → systematic-debugging → verification-before-completion
- **testing** (mutex): test-runner, test-driven-development
- **version_control** (mutex): using-git-worktrees, finishing-a-development-branch
- **common_services** (composable): notification, skill-creator

## Routing Rules

Priority-based routing from `skills-layer-configuration.yaml`:
- `workflow|yaml` → L1.workflow-executor (priority 10)
- `review|审查|检查` → L2.code_review (priority 9)
- `debug|bug|错误` → L2.systematic_debugging (priority 9)
- `api.*doc|接口文档` → L3.api_doc_generator (priority 7)
- `ui|mockup|原型` → L3.ui_mockup_generator (priority 7)
- `database.*design|schema` → L3.database_schema_designer (priority 7)
- `ci.*cd|pipeline` → L3.ci_cd_orchestrator (priority 7)
- `deploy|部署` → L3.deployment_automation (priority 7)

## Core Skills (L2)

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
   - Triggers: verify, check, confirm fix, audit, 交叉审计
   - Three-layer audit: single-file → cross-file verification → peer review by another AI

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

## Workflow Skills (L1)

- **workflow-executor** — Execute YAML/JSON workflows
- **task-runner** — Execute single tasks (skill calls)
- **conditional-branch** — If/else branching in workflows
- **loop-iterator** — Loop execution in workflows (max 100 iterations)
- **error-handler** — Retry and fallback on task failure (max 3 retries)

## Skill Metadata

Each skill in `skills/skills.json` has:
- `name` — Unique identifier (kebab-case, `[a-z0-9_-]+`)
- `description` — Purpose (bilingual Chinese/English)
- `path` — Path to `SKILL.md`
- `triggers` — Keywords for auto-triggering
- `depends_on` — Required prerequisite skills

Skills with implementation code have an `implementation.py` file with a required `execute_skill(params: Dict) -> Dict` function.

## Skill Dependencies

Skills have strict dependency chains from `skills/skills-layer-configuration.yaml`:
- `brainstorming` → `systematic-debugging` → `verification-before-completion`
- `code-review` → `code-refactor` (refactor requires review first)
- `workflow-executor` → `task-runner`
- `brainstorming` → `writing-plans` → `test-driven-development`

## Mutex Groups

These skill pairs cannot run simultaneously:
- code-review / code-refactor
- test-runner / test-driven-development
- using-git-worktrees / finishing-a-development-branch
