# Agent 与 Skill 重构计划

**日期**: 2026-03-25
**目标**: 解决 Agents 与 Skills 重复问题，明确职责边界

---

## 1. 问题分析

### 1.1 重复度矩阵

| Agent | 重叠 Skills | 重合度 | 具体重复内容 |
|-------|-------------|--------|-------------|
| `review` | `code-review`, `code-review-js`, `requesting-code-review` | 85% | 代码审查能力完全重复 |
| `testing` | `test-driven-development`, `test-runner` | 70% | 测试执行能力重复 |
| `debugging` | `systematic-debugging`, `error-handler` | 75% | 错误分析方法重复 |
| `implementation` | `subagent-driven-development` | 60% | 开发流程重叠 |
| `architecture` | `writing-plans` (部分) | 40% | 规划能力部分重叠 |
| `documentation` | (无) | 0% | 无冲突 |

### 1.2 架构问题

```
当前架构问题:
├── 职责混淆: Agent 和 Skill 都定义"做什么"
├── 重复实现: 相同功能在两处定义
├── 维护困难: 修改需要同步两处
└── 概念不清: 用户不知何时用 Agent 还是 Skill
```

---

## 2. 重构原则

### 2.1 核心定义

```
┌─────────────────────────────────────────────────────────────┐
│                   重构后的职责边界                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  AGENT (执行者)                                               │
│  ├── 定义: "谁能做" (Capability Provider)                    │
│  ├── 职责: 提供执行能力和资源约束                             │
│  ├── 属性: capabilities, context_limit, timeout              │
│  └── 示例: "我有 code_review 能力，上下文限制 12K tokens"    │
│                                                               │
│  SKILL (工作流/方法)                                          │
│  ├── 定义: "怎么做" (Workflow/Procedure)                     │
│  ├── 职责: 定义执行步骤和流程控制                             │
│  ├── 属性: triggers, depends_on, steps                       │
│  └── 示例: "先 brainstorming，再 writing-plans，最后实施"   │
│                                                               │
│  协作关系:                                                    │
│  Skill 指定需要的 capability → Orchestrator 分配匹配的 Agent │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 重构策略

1. **Agent 精简**: 只保留核心能力定义，移除具体实现细节
2. **Skill 规范化**: 明确依赖的 Agent capabilities
3. **Orchestrator 增强**: 负责 Skill → Agent 的映射

---

## 3. 重构方案

### 3.1 Agent 配置重构

**重构前** (当前):
```json
{
  "name": "review",
  "description": "Agent for code and design review...",
  "capabilities": ["code_review", "design_review", "security_check", "quality_analysis"],
  "max_tasks": 2,
  "context_limit": 12000,
  "timeout": 180,
  "parallel_safe": true,
  "requires_isolation": false
}
```

**重构后**:
```json
{
  "name": "reviewer",
  "description": "执行审查任务的执行者",
  "capabilities": {
    "code_review": {
      "context_limit": 12000,
      "timeout": 180,
      "languages": ["python", "javascript", "typescript", "java", "go"]
    },
    "design_review": {
      "context_limit": 8000,
      "timeout": 300
    },
    "security_check": {
      "context_limit": 10000,
      "timeout": 240,
      "severity_levels": ["critical", "high", "medium", "low"]
    }
  },
  "constraints": {
    "max_concurrent": 2,
    "parallel_safe": true
  }
}
```

### 3.2 Skill 配置重构

**重构前** (当前):
```json
{
  "name": "code-review",
  "description": "执行代码审查",
  "path": "skills/code-review/SKILL.md",
  "triggers": ["code review", "review code"],
  "depends_on": []
}
```

**重构后**:
```json
{
  "name": "code-review",
  "description": "执行代码审查工作流",
  "version": "2.0",
  "triggers": ["code review", "review code", "code quality"],
  "requires_capability": "code_review",
  "preferred_agent": "reviewer",
  "steps": [
    {"skill": "brainstorming", "optional": true},
    {"action": "analyze_code"},
    {"action": "check_vulnerabilities"},
    {"action": "generate_report"}
  ],
  "config": {
    "depth": "standard",
    "severity_threshold": "medium"
  }
}
```

### 3.3 新的 Agent 映射表

| Skill | 需要 Capability | 首选 Agent | 备选 Agent |
|-------|----------------|-----------|-----------|
| `code-review` | `code_review` | `reviewer` | - |
| `code-review-js` | `code_review` | `reviewer` | - |
| `test-driven-development` | `test_generation` + `test_execution` | `tester` | `implementation` |
| `systematic-debugging` | `error_analysis` + `log_analysis` | `debugger` | - |
| `writing-plans` | `system_design` | `architect` | - |
| `subagent-driven-development` | `code_generation` | `implementation` | - |

---

## 4. 实施计划

### Phase 1: 配置重构 (不破坏现有功能)

```
Step 1.1: 创建新配置文件格式
├── agents/agents.v2.json  (新格式)
└── skills/skills.v2.json  (增强格式)

Step 1.2: 创建兼容层
├── lingflow/coordination/adapter.py
└── 支持新旧格式转换

Step 1.3: 更新 Orchestrator
├── 添加 Skill → Agent 映射逻辑
└── 实现 capability-based 分配
```

### Phase 2: 重复整合

```
Step 2.1: 整合 review 相关
├── 保留: code-review (通用审查)
├── 保留: code-review-js (JS专项)
├── 废弃: requesting-code-review (合并到 code-review)
└── 保留: reviewer Agent (统一提供 code_review capability)

Step 2.2: 整合 testing 相关
├── 保留: test-driven-development (TDD 流程)
├── 保留: test-runner (测试执行)
├── 明确: tester Agent 提供执行能力
└── 明确: test-driven-development 是流程 Skill

Step 2.3: 整合 debugging 相关
├── 保留: systematic-debugging (调试方法论)
├── 保留: error-handler (错误处理流程)
├── 明确: debugger Agent 提供分析能力
└── 明确: systematic-debugging 是指导 Skill
```

### Phase 3: 文档更新

```
Step 3.1: 更新架构文档
├── AGENT_SKILL_ARCHITECTURE.md
└── 说明新的职责边界

Step 3.2: 更新使用指南
├── 何时使用 Agent
├── 何时使用 Skill
└── 如何正确组合

Step 3.3: 迁移指南
└── 从旧格式迁移到新格式
```

---

## 5. 新架构示例

### 5.1 完整工作流示例

```yaml
# 用户请求: "审查这段代码"
workflow: code_review_workflow

steps:
  # Step 1: 分析请求 (Skill)
  - skill: brainstorming
    optional: true

  # Step 2: 执行审查 (Skill 指定需要的 capability)
  - skill: code-review
    config:
      target: "./src/"
      depth: "deep"
    requires_capability: code_review    # Skill 声明需求
    assigned_to: reviewer               # Orchestrator 分配

  # Step 3: 生成报告 (Skill)
  - skill: notification
    config:
      message: "代码审查完成"
```

### 5.2 Orchestrator 分配逻辑

```python
class Orchestrator:
    def assign_agent(self, skill: Skill) -> Agent:
        """根据 Skill 需求分配 Agent"""
        required_capability = skill.requires_capability

        # 查找有此 capability 的 Agent
        candidates = [
            agent for agent in self.agents
            if required_capability in agent.capabilities
        ]

        # 选择最合适的 (考虑负载、上下文限制等)
        return self.select_best_agent(candidates, skill)

# 示例
skill = Skill(name="code-review", requires_capability="code_review")
agent = orchestrator.assign_agent(skill)  # 返回 reviewer Agent
```

---

## 6. 迁移路径

### 6.1 兼容性策略

```python
# 支持新旧格式共存
class AgentRegistry:
    def register_agent(self, agent_config):
        if isinstance(agent_config, dict):
            if "capabilities" in agent_config:
                # 新格式: {"capabilities": {"code_review": {...}}}
                return self._register_v2(agent_config)
            else:
                # 旧格式: {"capabilities": ["code_review", ...]}
                return self._register_v1(agent_config)

    def _register_v1(self, config):
        """旧格式转换器"""
        # 将旧格式转换为新格式
        return self._migrate_to_v2(config)
```

### 6.2 废弃计划

| 项目 | 状态 | 替代方案 | 废弃版本 |
|------|------|---------|---------|
| `requesting-code-review` | 废弃 | `code-review` | v4.0 |
| `receiving-code-review` | 废弃 | `code-review` | v4.0 |
| 旧 Agent 格式 | 废弃 | 新格式 | v4.0 |

---

## 7. 验证标准

重构完成后应满足:

1. **职责清晰**: Agent 定义能力，Skill 定义流程
2. **无重复**: 相同功能只在一处定义
3. **可扩展**: 新增 Agent/Skill 不需修改现有代码
4. **向后兼容**: 旧格式仍可使用
5. **文档完整**: 使用示例清晰

---

## 8. 时间线

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| Phase 1 | 配置重构 + 兼容层 | 2 天 |
| Phase 2 | 重复整合 | 3 天 |
| Phase 3 | 文档更新 | 1 天 |
| 验收 | 测试 + 修复 | 1 天 |

**总计**: 7 天

---

**文档版本**: 1.0
**创建日期**: 2026-03-25
