# Metacognition Guide / 元认知指南

**Version**: v1.0.0
**Last Updated**: 2026-04-08
**Status**: Production Ready

---

## Table of Contents / 目录

1. [Overview / 概述](#overview--概述)
2. [Why Metacognition / 为什么需要元认知](#why-metacognition--为什么需要元认知)
3. [Core Concepts / 核心概念](#core-concepts--核心概念)
4. [Quick Start / 快速开始](#quick-start--快速开始)
5. [Usage Examples / 使用示例](#usage-examples--使用示例)
6. [Integration Patterns / 集成模式](#integration-patterns--集成模式)
7. [Best Practices / 最佳实践](#best-practices--最佳实践)
8. [API Reference / API 参考](#api-reference--api-参考)
9. [FAQ / 常见问题](#faq--常见问题)

---

## Overview / 概述

### What is Metacognition? / 什么是元认知？

Metacognition is the ability to think about your own thinking. In the context of AI, it means:

**元认知是对自己思维的思考能力。在 AI 上下文中，它意味着：**

- **Knowing what you know** (知道你知道什么)
- **Knowing what you don't know** (知道你不知道什么)
- **Knowing how to bridge the gap** (知道如何弥补差距)

### The Problem / 问题

> "这是声明的前验。"

Before metacognition, the workflow was:

**在元认知之前，工作流程是：**

```
AI claims "I'm done" → Verify → "Failed" → Fix
```

This is **post-validation**, not **prevention**.

这是**事后验证**，不是**预防**。

### The Solution / 解决方案

With metacognition, the workflow becomes:

**使用元认知后，工作流程变为：**

```
Check capabilities BEFORE starting → Identify gaps → Learn first → Execute → Verify
```

This is **prevention first**.

这是**预防优先**。

---

## Why Metacognition / 为什么需要元认知

### The "Dunning-Kruger" Problem / 达克效应问题

Low-capability AI agents tend to overestimate their abilities:

**低能力 AI 倾向于高估自己的能力：**

| Actual Level | Estimated Level | Risk |
|--------------|----------------|------|
| UNKNOWN | MASTERED | ❌ High risk of failure |
| FAMILIAR | PARTIAL | ⚠️  Moderate risk |
| PARTIAL | PARTIAL | ✅ Accurate |

Metacognition forces **honest self-assessment**.

**元认知强制诚实的自我评估。**

### The "Data Hallucination" Problem / 数据幻觉问题

Example from lingyi project:

**来自 lingyi 项目的例子：**

- `energy_pct` field was defined, stored, and displayed
- But never updated by any code
- UI failed to answer: **Where does data come from? Who updates it?**
- `energy_pct` 字段被定义、存储和显示
- 但从未被任何代码更新
- UI 未能回答：**数据从哪里来？谁更新它？**

With metacognition, AI must declare **data flow knowledge** BEFORE starting.

**使用元认知，AI 必须在开始前声明**数据流知识**。**

---

## Core Concepts / 核心概念

### Capability Levels / 能力等级

```python
from lingflow.trust.metacognition import CapabilityLevel

class CapabilityLevel(IntEnum):
    UNKNOWN = 0    # Complete unknown (完全未知)
    FAMILIAR = 1   # Familiar with concepts (熟悉概念)
    PARTIAL = 2    # Partial mastery (部分掌握)
    MASTERED = 3   # Complete mastery (完全掌握)
```

### Complexity Levels / 复杂度等级

| Complexity | Required Level | Description |
|-----------|----------------|-------------|
| **simple** | FAMILIAR+ | Basic tasks with clear patterns |
| **medium** | PARTIAL+ | Tasks requiring some expertise |
| **complex** | MASTERED | Tasks requiring deep expertise |

### Key Classes / 核心类

```python
from lingflow.trust.metacognition import (
    CapabilityLevel,
    Capability,
    TaskRequirements,
    EvolutionPath,
    MetacognitiveAgent,
    get_metacognitive_agent
)
```

---

## Quick Start / 快速开始

### Installation / 安装

```bash
# Metacognition is part of lingflow
pip install -e .
```

### Basic Usage / 基本使用

```python
from lingflow.trust import get_metacognitive_agent
from lingflow.trust.metacognition import CapabilityLevel

# Get the singleton agent
agent = get_metacognitive_agent()

# Register your capabilities
agent.register_capability(
    name="Python",
    level=CapabilityLevel.MASTERED,
    last_practiced="2026-04-01"
)

# Analyze task requirements
requirements = agent.analyze_task_requirements(
    task_id="task-001",
    task_description="Write a Python script",
    required_capabilities=["Python"],
    complexity="simple"
)

# Check if you can start
if requirements["can_start"]:
    print("✅ Can start task")
else:
    print(f"❌ Cannot start: {requirements['reason']}")
```

---

## Usage Examples / 使用示例

### Example 1: PostgreSQL Migration / PostgreSQL 迁移

**Scenario**: Migrate SQLite database to PostgreSQL

**场景**：将 SQLite 数据库迁移到 PostgreSQL

```python
from lingflow.trust import get_metacognitive_agent
from lingflow.trust.metacognition import CapabilityLevel

agent = get_metacognitive_agent()

# 1. Declare current capabilities
agent.register_capability("PostgreSQL", CapabilityLevel.UNKNOWN)
agent.register_capability("SQL", CapabilityLevel.FAMILIAR)
agent.register_capability("Python", CapabilityLevel.MASTERED)

# 2. Analyze task
requirements = agent.analyze_task_requirements(
    task_id="postgres-migration-001",
    task_description="Migrate SQLite database to PostgreSQL",
    required_capabilities=["PostgreSQL", "SQL", "Python"],
    complexity="complex"
)

# 3. Check result
print(f"Can start: {requirements['can_start']}")
# Output: Can start: False

print(f"Gaps: {requirements['gaps']}")
# Output: Gaps: ['PostgreSQL: UNKNOWN < required PARTIAL']

# 4. Get evolution path
evolution = agent.propose_evolution("PostgreSQL", CapabilityLevel.PARTIAL)
print(f"Steps: {evolution['steps']}")
# Output:
# Steps: [
#   'Read PostgreSQL official documentation (1-2 days)',
#   'Practice basic CRUD operations (3-5 days)',
#   'Build small PostgreSQL project (1-2 weeks)'
# ]

# 5. After learning, update capability
agent.update_capability_level("PostgreSQL", CapabilityLevel.PARTIAL)

# 6. Check again
requirements = agent.analyze_task_requirements(...)
print(f"Can start: {requirements['can_start']}")
# Output: Can start: True
```

### Example 2: Metacognition Guard Skill / 元认知守卫技能

**Scenario**: Check capabilities before starting a task

**场景**：在开始任务前检查能力

```python
from lingflow import lingflow

lf = lingflow()

# Run metacognition guard before task
result = lf.run_skill("metacognition-guard", {
    "task_id": "energy-pct-fix",
    "task_description": "Fix energy_pct data flow issue",
    "required_capabilities": ["Python", "lingyi architecture"],
    "complexity": "medium",
    "current_capabilities": {
        "Python": "MASTERED",
        "lingyi architecture": "UNKNOWN"
    }
})

# Check result
if not result["can_start"]:
    print(f"❌ Cannot start: {result['reason']}")

    # Review evolution suggestions
    for path in result["evolution_paths"]:
        print(f"\nFrom {path['source_level']} to {path['target_level']}:")
        for step in path["steps"]:
            print(f"  • {step}")
else:
    print("✅ All requirements met, starting task...")
```

### Example 3: Completion Declaration / 完成声明

**Scenario**: Verify that you can claim completion

**场景**：验证你可以声称完成

```python
from lingflow.trust import get_metacognitive_agent

agent = get_metacognitive_agent()

# After completing a task
can_declare, reason = agent.can_declare_completion(
    task_id="postgres-migration-001",
    declared_capabilities=["Python", "SQL", "PostgreSQL"],
    complexity="complex"
)

if can_declare:
    print("✅ Task verified, can declare completion")
    # Generate completion report
    report = agent.generate_completion_report(task_id)
    print(f"Confidence: {report['confidence']}")
else:
    print(f"❌ Cannot declare: {reason}")
    # Either learn missing skills or re-evaluate task complexity
```

### Example 4: Learning History Tracking / 学习历史跟踪

**Scenario**: Track your learning progress

**场景**：跟踪你的学习进度

```python
from lingflow.trust import get_metacognitive_agent
from lingflow.trust.metacognition import CapabilityLevel

agent = get_metacognitive_agent()

# Simulate learning journey
timeline = [
    ("2026-04-01", "PostgreSQL", CapabilityLevel.UNKNOWN),
    ("2026-04-05", "PostgreSQL", CapabilityLevel.FAMILIAR),
    ("2026-04-10", "PostgreSQL", CapabilityLevel.PARTIAL),
    ("2026-04-20", "PostgreSQL", CapabilityLevel.MASTERED),
]

for date, capability, level in timeline:
    agent.register_capability(capability, level, last_practiced=date)

# Get learning history
history = agent.get_learning_history("PostgreSQL")
print(f"Learning path for PostgreSQL:")
for entry in history:
    print(f"  {entry['date']}: {entry['level']}")
# Output:
# Learning path for PostgreSQL:
#   2026-04-01: UNKNOWN
#   2026-04-05: FAMILIAR
#   2026-04-10: PARTIAL
#   2026-04-20: MASTERED
```

---

## Integration Patterns / 集成模式

### Pattern 1: Pre-Task Check / 任务前检查

```python
def execute_with_metacognition(task):
    """Execute task with metacognition guard"""
    # 1. Check capabilities
    result = lf.run_skill("metacognition-guard", {
        "task_id": task.id,
        "task_description": task.description,
        "required_capabilities": extract_capabilities(task),
        "complexity": estimate_complexity(task),
        "current_capabilities": get_agent_capabilities()
    })

    # 2. Guard clause
    if not result["can_start"]:
        return {"status": "rejected", "reason": result['reason']}

    # 3. Execute task
    result = execute_task(task)

    # 4. Verify completion
    if get_config("trust.auto_verify"):
        verify_result = lf.run_skill("trust-guardrail", {
            "verification_contract": result["verification_contract"]
        })

    return result
```

### Pattern 2: Adaptive Task Assignment / 自适应任务分配

```python
def assign_agent(task):
    """Assign agent based on capability matching"""
    agent = get_metacognitive_agent()

    # Check all available agents
    for candidate_agent in available_agents:
        requirements = agent.analyze_task_requirements(
            task_id=task.id,
            task_description=task.description,
            required_capabilities=extract_capabilities(task),
            complexity=task.complexity,
            current_capabilities=candidate_agent.capabilities
        )

        if requirements["can_start"]:
            return candidate_agent

    # No agent has sufficient capabilities
    return None
```

### Pattern 3: Learning-First Workflow / 学习优先工作流

```python
def learning_first_workflow(task):
    """Prioritize learning over execution"""
    agent = get_metacognitive_agent()

    # 1. Check capabilities
    requirements = agent.analyze_task_requirements(...)

    if not requirements["can_start"]:
        # 2. Propose learning plan
        learning_plan = generate_learning_plan(requirements["gaps"])

        # 3. Execute learning plan first
        execute_learning_plan(learning_plan)

        # 4. Update capabilities
        for capability in requirements["gaps"]:
            agent.update_capability_level(capability.name, required_level)

    # 5. Now execute task
    return execute_task(task)
```

---

## Best Practices / 最佳实践

### DO's / 应该做

1. **Always declare capabilities before starting tasks**
   **在开始任务前总是声明能力**

2. **Be honest about knowledge gaps**
   **诚实地承认知识缺口**

3. **Follow evolution paths systematically**
   **系统地遵循进化路径**

4. **Track learning progress**
   **跟踪学习进度**

5. **Use metacognition in combination with trust verification**
   **结合信任验证使用元认知**

### DON'Ts / 不应该做

1. **Never start tasks with insufficient capabilities**
   **永远不要在能力不足时开始任务**

2. **Don't fake capability levels**
   **不要伪造能力等级**

3. **Don't skip the learning phase**
   **不要跳过学习阶段**

4. **Don't ignore evolution suggestions**
   **不要忽略进化建议**

5. **Don't declare completion without verification**
   **不要在没有验证的情况下声称完成**

---

## API Reference / API 参考

### MetacognitiveAgent

```python
class MetacognitiveAgent:
    def __init__(self):
        """Initialize metacognitive agent"""

    def register_capability(
        self,
        name: str,
        level: CapabilityLevel,
        last_practiced: Optional[str] = None,
        practice_notes: Optional[str] = None
    ) -> None:
        """Register a capability with its proficiency level"""

    def update_capability_level(
        self,
        capability_name: str,
        new_level: CapabilityLevel
    ) -> None:
        """Update capability level and track learning"""

    def analyze_task_requirements(
        self,
        task_id: str,
        task_description: str,
        required_capabilities: List[str],
        complexity: str
    ) -> TaskRequirements:
        """Analyze if current capabilities meet task requirements"""

    def can_declare_completion(
        self,
        task_id: str,
        declared_capabilities: List[str],
        complexity: str
    ) -> Tuple[bool, Optional[str]]:
        """Check if completion can be declared"""

    def propose_evolution(
        self,
        capability_name: str,
        target_level: CapabilityLevel
    ) -> EvolutionPath:
        """Propose learning path to reach target capability"""

    def get_learning_history(
        self,
        capability_name: str
    ) -> List[Dict]:
        """Get learning history for a capability"""

    def get_all_capabilities(self) -> Dict[str, Capability]:
        """Get all registered capabilities"""
```

### Helper Functions

```python
def get_metacognitive_agent() -> MetacognitiveAgent:
    """Get singleton metacognitive agent"""
```

---

## FAQ / 常见问题

### Q1: When should I use metacognition?

**A**: Always before starting a new task, especially when:
- Working with new technologies
- Tackling complex problems
- Claiming task completion

**问**: 什么时候应该使用元认知？

**答**: 总是在开始新任务之前，特别是：
- 使用新技术时
- 解决复杂问题时
- 声称任务完成时

### Q2: What if I don't know a required capability?

**A**: Declare it as `UNKNOWN`, then use the evolution path to learn it. Don't fake it.

**问**: 如果我不知道一个必需的能力怎么办？

**答**: 声明为 `UNKNOWN`，然后使用进化路径学习它。不要伪造。

### Q3: Can I start a task if I have PARTIAL level but need MASTERED?

**A**: For `simple` tasks, `PARTIAL` is sufficient. For `complex` tasks, you need `MASTERED`.

**问**: 如果我有 PARTIAL 级别但需要 MASTERED，我可以开始任务吗？

**答**: 对于 `simple` 任务，`PARTIAL` 就足够了。对于 `complex` 任务，你需要 `MASTERED`。

### Q4: How does metacognition relate to trust verification?

**A**: Metacognition is **prevention** (before starting), trust verification is **validation** (after completion). Use both for maximum reliability.

**问**: 元认知与信任验证有什么关系？

**答**: 元认知是**预防**（在开始之前），信任验证是**验证**（在完成之后）。两者结合使用以获得最大可靠性。

### Q5: What's the difference between FAMILIAR and PARTIAL?

**A**:
- `FAMILIAR`: You know the concepts but lack practice
- `PARTIAL`: You have some practice and can handle medium tasks

**问**: FAMILIAR 和 PARTIAL 有什么区别？

**答**:
- `FAMILIAR`: 你知道概念但缺乏实践
- `PARTIAL`: 你有一些实践并且可以处理中等任务

---

## Examples / 示例

See `/home/ai/lingflow/tests/test_metacognition.py` for complete test cases and examples.

---

## Related Documentation / 相关文档

- [Trust Framework Summary](TRUST_FRAMEWORK_SUMMARY.md)
- [lingflow Agent Guide](AGENTS.md)
- [Metacognition Guard Skill](skills/metacognition-guard/SKILL.md)

---

**Version**: v1.0.0
**Last Updated**: 2026-04-08
**Maintained by**: lingflow Development Team
