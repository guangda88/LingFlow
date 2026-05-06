# Metacognition Reference

> Extracted from AGENTS.md on 2026-05-06. Source: `docs/AGENTS_ARCHIVE_20260506.md`

## Overview (概述)

元认知系统是 LingFlow 的核心创新之一，它要求 AI 在开始任务前必须明确自己的知识边界。这不是事后验证，而是事前预防。

**核心哲学**：
- **知知与知不知** (Know what you know and don't know): AI 必须明确知道自己知道什么、不知道什么
- **进化方向** (Evolution direction): 从"不知道"到"知道"的学习路径
- **诚实优于自信** (Honesty over confidence): "我不知道"比"我也许可以"更有价值

## Capability Levels (能力等级)

| Level | Value | Can Handle | Description |
|-------|-------|------------|-------------|
| **UNKNOWN** | 0 | simple | 完全未知，需要从头学习 |
| **FAMILIAR** | 1 | simple | 熟悉概念，但缺乏实践经验 |
| **PARTIAL** | 2 | simple, medium | 部分掌握，需要查阅文档 |
| **MASTERED** | 3 | simple, medium, complex | 完全掌握，可以独立完成 |

## Usage Examples (使用示例)

### Example 1: PostgreSQL Migration (PostgreSQL 迁移)

```python
from lingflow import LingFlow
from lingflow.trust import get_metacognitive_agent

lf = LingFlow()
agent = get_metacognitive_agent()

agent.register_capability(
    name="PostgreSQL",
    level=CapabilityLevel.UNKNOWN,
    last_practiced=None
)
agent.register_capability(
    name="SQL",
    level=CapabilityLevel.FAMILIAR,
    last_practiced="2026-03-01"
)

requirements = agent.analyze_task_requirements(
    task_id="postgres-migration-001",
    task_description="Migrate SQLite database to PostgreSQL",
    required_capabilities=["PostgreSQL", "SQL"],
    complexity="complex"
)

print(f"Can start: {requirements['can_start']}")
# Output: Can start: False

evolution = agent.propose_evolution(
    capability_name="PostgreSQL",
    target_level=CapabilityLevel.PARTIAL
)
```

### Example 2: Pre-Task Check (任务前检查)

```python
result = lf.run_skill("metacognition-guard", {
    "task_id": "energy-pct-fix",
    "task_description": "Fix energy_pct data flow issue",
    "required_capabilities": ["Python", "LingYi architecture"],
    "complexity": "medium",
    "current_capabilities": {
        "Python": "MASTERED",
        "LingYi architecture": "UNKNOWN"
    }
})

if not result["can_start"]:
    print(f"Cannot start: {result['reason']}")
```

### Example 3: Completion Declaration (完成声明)

```python
can_declare, reason = agent.can_declare_completion(
    task_id="postgres-migration-001",
    declared_capabilities=["Python", "SQL", "PostgreSQL"],
    complexity="complex"
)
```

## Integration with Trust Framework (与信任框架集成)

```
┌─────────────────────────────────────────────────┐
│  PREVENTION LAYER (事前预防)                      │
│  1. Metacognition Guard                          │
│     • Check capabilities BEFORE starting         │
│     • Identify knowledge gaps                    │
│     • Block insufficient capabilities            │
└─────────────────────────────────────────────────┘
                      ↓ can_start?
                 [YES]    [NO]
                   |         ↓
                   │    Learn first
                   ↓
┌─────────────────────────────────────────────────┐
│  EXECUTION LAYER (执行层)                         │
│  Execute task with declared capabilities        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│  VALIDATION LAYER (事后验证)                      │
│  2. Trust Guardrail                              │
│     • Verify file changes AFTER completion       │
│     • Check against verification contract       │
│     • Generate confidence score                 │
└─────────────────────────────────────────────────┘
```

## Key Features (关键特性)

1. **Dunning-Kruger Prevention** (达克效应预防) — 防止低能力 AI 高估自己的能力
2. **Evolution-Oriented** (进化导向) — 知识缺口不是失败，而是学习机会
3. **Truth in Declaration** (声明真实性) — "我不知道" 和 "我知道" 同样有效

## Files (相关文件)

- `lingflow/trust/metacognition.py` — 核心元认知系统
- `skills/metacognition-guard/` — 元认知守卫技能
- `tests/test_metacognition.py` — 元认知测试套件（22个测试）

## Configuration (配置)

```python
# lingflow/common/config.py
"metacognition": {
    "enabled": True,
    "strict_mode": True,
    "evolution_mode": "suggest",  # suggest/require/disabled
}
```
