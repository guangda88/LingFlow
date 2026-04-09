# Metacognition Guard Skill / 元认知守护技能

## 概述 / Overview

在开始任务之前进行元认知检查，确保：
1. 声明需要什么能力
2. 验证当前能力是否足够
3. 识别知识缺口
4. 提出进化路径

Performs metacognitive checks before starting a task to ensure:
1. Declare required capabilities
2. Verify current capabilities are sufficient
3. Identify knowledge gaps
4. Propose evolution paths

## 门控 / Gates

### 🔒 硬门控 / Hard Gate
- **任务开始前必须通过能力检查**
- **如果存在知识缺口，不能声明可以开始工作**

### ⚠️ 软门控 / Soft Gate
- **知识边界声明必须明确**
- **进化路径必须合理**

## 触发器 / Triggers

- `pre-task check` - 任务前检查
- `capability check` - 能力检查
- `knowledge boundary` - 知识边界
- `ready to start` - 准备开始
- `元认知` - 元认知
- `能力检查` - 能力检查

## 流程 / Process

### 阶段 1: 声明 / Declaration

```
输入参数：
- task_id: 任务标识符
- task_description: 任务描述
- required_capabilities: 需要的能力列表（如 ["Python", "PostgreSQL", "pytest"]）
- complexity: 任务复杂度（simple, medium, complex）

系统要求：
- 明确声明每个需要的能力
- 声明当前掌握水平
```

### 阶段 2: 检查 / Verification

```
系统检查：
1. 所有需要的能力是否已声明？
2. 当前能力水平是否满足任务复杂度？
3. 是否存在知识缺口？

输出：
- gaps: 知识缺口列表
- can_start: 是否可以开始任务
- reason: 原因说明
```

### 阶段 3: 建议 / Recommendations

```
如果存在缺口：
- 提供替代方案
- 建议学习路径
- 推荐简化任务的方案

如果可以开始：
- 确认任务契约
- 列出关键注意事项
```

## 数据结构 / Data Structures

### TaskRequirements

```python
{
  "task_id": "task-001",
  "task_description": "Add energy_pct field",
  "required_capabilities": ["Python", "Database Schema Design"],
  "complexity": "medium",
  "gaps": [],
  "alternative_approaches": [],
  "recommendations": []
}
```

### Capability Levels

- `UNKNOWN (0)` - 完全未知，需要从头学习
- `FAMILIAR (1)` - 熟悉概念，但缺乏实践经验
- `PARTIAL (2)` - 部分掌握，需要查阅文档
- `MASTERED (3)` - 完全掌握，可以独立完成

## 检查清单 / Checklist

### 任务开始前 / Before Starting

- [ ] 声明所有需要的能力
- [ ] 评估每个能力的当前水平
- [ ] 识别是否存在知识缺口
- [ ] 如果有缺口，提出解决方案
- [ ] 确认是否可以安全地开始任务

### 知识边界声明 / Knowledge Boundary Declaration

- [ ] 我知道什么（已掌握的能力）
- [ ] 我不知道什么（知识盲区）
- [ ] 我需要学习什么（进化方向）
- [ ] 如何验证我确实掌握了（验证标准）

## 使用示例 / Usage Examples

### 示例 1: 简单任务（无缺口）

```python
params = {
    "task_id": "simple-task-001",
    "task_description": "Write Python function to calculate sum",
    "required_capabilities": ["Python"],
    "complexity": "simple"
}

result = execute_skill(params)

# Expected output:
{
    "can_start": True,
    "gaps": [],
    "reason": "All required capabilities available at sufficient level",
    "warnings": []
}
```

### 示例 2: 复杂任务（有缺口）

```python
params = {
    "task_id": "complex-task-001",
    "task_description": "Migrate to PostgreSQL with partitioning",
    "required_capabilities": ["Python", "SQL", "PostgreSQL"],
    "complexity": "complex"
}

result = execute_skill(params)

# Expected output:
{
    "can_start": False,
    "gaps": [
        "UNKNOWN: PostgreSQL - Completely unknown capability",
        "INSUFFICIENT: SQL - Current level PARTIAL, need COMPLEX complexity"
    ],
    "reason": "Cannot start: 2 capability gaps found",
    "recommendations": [
        "Need to learn PostgreSQL from scratch",
        "Need to evolve SQL to higher level",
        "Consider using simpler database"
    ],
    "alternative_approaches": [
        "Break down task into smaller sub-tasks",
        "Use simpler database (SQLite)",
        "Allocate time for learning before starting"
    ]
}
```

### 示例 3: 主动学习（带进化路径）

```python
params = {
    "task_id": "learning-task-001",
    "task_description": "Learn and implement PostgreSQL",
    "required_capabilities": ["PostgreSQL"],
    "complexity": "medium",
    "propose_evolution": True  # 自动提出学习路径
}

result = execute_skill(params)

# Expected output:
{
    "can_start": False,
    "gaps": ["UNKNOWN: PostgreSQL"],
    "evolution_proposed": {
        "capability": "PostgreSQL",
        "from_level": "UNKNOWN",
        "to_level": "PARTIAL",
        "steps": [
            "Read PostgreSQL documentation",
            "Set up local instance",
            "Practice basic queries",
            "Build sample project"
        ],
        "estimated_time": "1 week"
    },
    "recommendations": [
        "Complete evolution path first, then start task"
    ]
}
```

## 与 Trust Framework 的关系 / Relationship with Trust Framework

Metacognition Guard 是事前检查（预防），Trust Guardrail 是事后验证（确认）。

```
工作流：
1. Metacognition Guard (事前) → 可以开始吗？
2. Execute Task (执行) → 做工作
3. Trust Guardrail (事后) → 真的完成了？
```

## 核心原则 / Core Principles

### 明确性 / Explicitness
- 知道就是知道，不知道就是不知道
- 不模糊地带，不"可能知道"

### 诚实性 / Honesty
- 承认知识边界
- 不承诺无法交付的结果

### 进化导向 / Evolution-Oriented
- 从不知道到知道
- 从部分掌握到完全掌握
- 记录学习路径

### 安全优先 / Safety First
- 宁可拒绝，也不要冒险
- 能力不足时明确拒绝

## 故障模式 / Failure Modes

### 错误 1: 声称知道但实际不知道
**症状**: 声称已掌握某能力，但执行失败
**原因**: 元认知不准确
**解决**: 降低能力级别，诚实声明

### 错误 2: 忽略知识缺口
**症状**: 检测到缺口但仍然开始
**原因**: 过度自信
**解决**: 强制要求解决缺口

### 错误 3: 过度保守
**症状**: 能力足够但拒绝开始
**原因**: 评估过于严格
**解决**: 合理设定复杂度级别

## 相关概念 / Related Concepts

- **Dunning-Kruger Effect**: 低能力者高估自己
- **Meta-Cognition**: 对自己认知的认知
- **Growth Mindset**: 能力可以通过学习提升
- **Capability Maturity**: 能力成熟度模型

## 参考资料 / References

- "Knowing What We Don't Know: The Metacognitive Awareness"
- "The Dunning-Kruger Effect: On Being Ignorant of One's Own Ignorance"
- "Capability Maturity Model (CMM)"
