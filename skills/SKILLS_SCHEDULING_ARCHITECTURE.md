# lingflow 技能调度架构方案

**版本**: 1.0
**日期**: 2026-03-26
**状态**: 草案 - 待审查

---

## 一、设计原则

基于"技能越多 AI 越笨"的洞察，本方案遵循：

1. **少而精**: 核心常驻 ≤ 15 个，扩展技能按需加载
2. **清晰路由**: 明确什么场景用什么技能，禁止混用
3. **任务隔离**: 一次只做一件事，做完再切换
4. **轻量化**: 技能描述简洁，不撑爆上下文
5. **失败回退**: 调用失败即降级，不重试死循环

---

## 二、三层架构

```
┌────────────────────────────────────────────────────────────┐
│                     L1: 核心调度层 (5个)                      │
│  职责：工作流编排、任务执行、流程控制                          │
│  常驻：是                                                   │
├────────────────────────────────────────────────────────────┤
│  技能           |  触发词                    |  输出         │
│ ───────────────┼──────────────────────────┼──────────────│
│  workflow-exec │ workflow, yaml, 批量      | 任务编排结果   │
│  task-runner   │ run, execute, call       | 单任务执行     │
│  conditional   │ if, switch, branch        | 分支决策       │
│  loop-iterator │ for, while, each, iterate  | 循环执行      │
│  error-handler │ retry, fallback, error    | 错误恢复       │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│                     L2: 专业能力层 (12个)                     │
│  职责：特定领域的专业能力                                    │
│  常驻：是                                                   │
│  分组：同一时间只能用同组内的一个技能                         │
├────────────────────────────────────────────────────────────┤
│  【代码质量组】(互斥)           【开发流程组】(顺序)          │
│  • code-review                  • brainstorming             │
│  • code-refactor               • systematic-debugging      │
│                                 • verification-before-comp│
├────────────────────────────────────────────────────────────┤
│  【测试验证组】(互斥)           【版本控制组】(互斥)          │
│  • test-runner                  • using-git-worktrees      │
│  • test-driven-development      • finishing-dev-branch     │
├────────────────────────────────────────────────────────────┤
│  【通用服务】(可组合)                                       │
│  • notification   • skill-creator                            │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│                     L3: 扩展能力层 (按需加载)                 │
│  职责：特定场景的专业能力                                    │
│  常驻：否 (检测到需要时才加载)                               │
│  卸载：任务完成后自动卸载                                    │
├────────────────────────────────────────────────────────────┤
│  类别           | 技能                              │
│  ████████████████████████████████████████████████████████  │
│  【数据库】      │ database-export, database-schema-...  │
│  【DevOps】      │ ci-cd-orchestrator, deployment-automation│
│  【设计生成】    │ ui-mockup-generator, api-doc-generator │
│  【环境管理】    │ environment-manager                      │
│  【分析工具】    │ skill-analytics, skill-testing         │
└────────────────────────────────────────────────────────────┘
```

---

## 三、技能清单与分类

### 3.1 L1 核心调度层 (5个)

| 技能 | 简写描述 | 触发词 | 互斥 | 依赖 |
|------|----------|--------|------|------|
| `workflow-executor` | 执行YAML工作流 | workflow, yaml, 流水线 | 无 | task-runner |
| `task-runner` | 执行单个任务 | run, execute, call | 无 | 无 |
| `conditional-branch` | 条件分支判断 | if, branch, switch, 条件 | 无 | task-runner |
| `loop-iterator` | 循环迭代执行 | for, while, each, loop, 迭代 | 无 | task-runner |
| `error-handler` | 错误处理与重试 | retry, fallback, error, 重试 | 无 | task-runner |

### 3.2 L2 专业能力层 (12个)

#### 代码质量组 (互斥：同一时间只能用1个)

| 技能 | 简写描述 | 触发词 | 优先级 |
|------|----------|--------|--------|
| `code-review` | 8维代码审查 | review, 审查, 检查质量 | 最高 |
| `code-refactor` | 执行代码重构 | refactor, 重构 | 中 |

> **路由规则**: 当触发词匹配时，优先使用 `code-review`。只有在审查结果明确需要重构时，才调用 `code-refactor`。

#### 开发流程组 (顺序：按阶段流动)

| 技能 | 简写描述 | 触发词 | 可接 | 可转 |
|------|----------|--------|------|------|
| `brainstorming` | 头脑风暴 | plan, design, 思路, 方案 | 无 | debugging, review |
| `systematic-debugging` | 系统化调试 | debug, fix, bug, 错误 | brainstorming | verification |
| `verification-before-completion` | 完成前验证 | verify, check, 验证 | debugging | 无 |

> **路由规则**: brainstorming → debugging → verification，单向流动。

#### 测试验证组 (互斥)

| 技能 | 简写描述 | 触发词 |
|------|----------|--------|
| `test-runner` | 运行测试 | test, pytest, 测试 |
| `test-driven-development` | TDD 流程 | tdd, 红绿灯重构 |

#### 版本控制组 (互斥)

| 技能 | 简写描述 | 触发词 |
|------|----------|--------|
| `using-git-worktrees` | Git 工作树 | new branch, worktree, 新分支 |
| `finishing-a-development-branch` | 完成分支 | done, finish, merge, 完成 |

#### 通用服务 (可组合)

| 技能 | 简写描述 | 触发词 |
|------|----------|--------|
| `notification` | 发送通知 | notify, alert, 通知 |
| `skill-creator` | 创建技能 | create skill, 新技能 |

### 3.3 L3 扩展能力层 (按需加载)

| 类别 | 技能 | 加载条件 | 卸载条件 |
|------|------|----------|----------|
| 数据库 | `database-export` | 包含 "export database" | 任务完成 |
| 数据库 | `database-schema-designer` | 包含 "database design" | 任务完成 |
| DevOps | `ci-cd-orchestrator` | 包含 "ci/cd", "pipeline" | 任务完成 |
| DevOps | `deployment-automation` | 包含 "deploy", "发布" | 任务完成 |
| 设计 | `ui-mockup-generator` | 包含 "ui", "mockup" | 任务完成 |
| 设计 | `api-doc-generator` | 包含 "api doc", "接口文档" | 任务完成 |
| 环境 | `environment-manager` | 包含 "env", "环境" | 任务完成 |
| 分析 | `skill-analytics` | 包含 "analytics", "统计" | 任务完成 |
| 分析 | `skill-testing` | 包含 "test skill" | 任务完成 |

---

## 四、路由规则配置

### 4.1 触发词映射表

```yaml
trigger_mapping:
  # 工作流触发 → L1
  - triggers: [workflow, yaml, 流水线, 批量, 多任务]
    route: L1.workflow-executor

  - triggers: [run, execute, call, 执行]
    route: L1.task-runner

  # 代码触发 → L2.代码质量组
  - triggers: [review, 审查, 检查, analyze code, 代码质量]
    route: L2.code-review
    mutex_group: code_quality

  - triggers: [refactor, 重构, 优化代码]
    route: L2.code-refactor
    mutex_group: code_quality
    require_after: L2.code-review  # 需要先审查

  # 开发流程触发 → L2.开发流程组
  - triggers: [plan, design, 方案, 思路, 新功能]
    route: L2.brainstorming
    phase: requirements

  - triggers: [debug, fix, bug, 错误, 异常]
    route: L2.systematic-debugging
    phase: debugging

  - triggers: [verify, check, 验证, 确认]
    route: L2.verification-before-completion
    phase: completion
```

### 4.2 互斥与依赖

```yaml
constraints:
  # 互斥组：同一时间只能激活一个
  mutex_groups:
    code_quality: [code-review, code-refactor]
    testing: [test-runner, test-driven-development]
    git: [using-git-worktrees, finishing-a-development-branch]

  # 依赖链：A 完成后才能调用 B
  chains:
    - [brainstorming, systematic-debugging, verification-before-completion]
    - [code-review, code-refactor]
    - [workflow-executor, task-runner]
```

---

## 五、加载与卸载策略

### 5.1 常驻技能 (17个)

**L1 全部 + L2 全部** = 17 个技能始终加载

### 5.2 按需加载 (20个)

| 加载时机 | 卸载时机 | 技能示例 |
|----------|----------|----------|
| 检测到触发词 | 任务完成后 | L3 所有技能 |
| 用户显式请求 | 用户切换任务 | 扩展技能 |

### 5.3 卸载规则

```python
# 伪代码
def should_unload(skill, current_task):
    # L3 技能：任务完成立即卸载
    if skill.layer == "L3":
        return current_task.completed

    # L2 技能：保持加载（常驻）
    if skill.layer == "L2":
        return False

    # L1 技能：永不卸载
    return False
```

---

## 六、失败回退机制

### 6.1 回退链

```yaml
fallback_chains:
  code-review:
    - primary: code-review
    - fallback1: code-analysis  # 简化版分析
    - fallback2: notification    # 通知用户无法完成

  task-runner:
    - primary: task-runner
    - fallback1: error-handler   # 重试
    - fallback2: notification    # 通知失败

  database-export:
    - primary: database-export
    - fallback: notification     # 技能不可用
```

### 6.2 重试策略

```yaml
retry_policy:
  max_retries: 1
  timeout: 30s
  backoff: linear

  # 不可重试的错误（立即回退）
  no_retry:
    - ValidationError
    - PermissionError
    - SkillNotFoundError
```

---

## 七、精简后的技能列表

### 7.1 核心保留 (17个常驻)

```
L1 (5):
  workflow-executor, task-runner, conditional-branch,
  loop-iterator, error-handler

L2 (12):
  代码质量: code-review, code-refactor
  开发流程: brainstorming, systematic-debugging, verification-before-completion
  测试验证: test-runner, test-driven-development
  版本控制: using-git-worktrees, finishing-a-development-branch
  通用服务: notification, skill-creator
```

### 7.2 扩展技能 (按需)

```
数据库: database-export, database-schema-designer
DevOps: ci-cd-orchestrator, deployment-automation
设计: ui-mockup-generator, api-doc-generator
环境: environment-manager
分析: skill-analytics, skill-testing
其他: dispatching-parallel-agents, skill-automation,
     skill-categorization, skill-integration, skill-templates,
     skill-versioning, subagent-driven-development,
     test-driven-development, writing-plans
```

### 7.3 建议删除 (6个)

```
已弃用:
  requesting-code-review     → 被 code-review 替代
  receiving-code-review      → 被 code-review 替代
  executing-plans            → 被 subagent-driven-development 替代

重叠:
  code-analysis              → 合并到 code-review
  code-optimizer             → 功能由 code-review + code-refactor 分担
  skill-automation            → 合并到 skill-creator
```

---

## 八、实施计划

### Phase 1: 清理 (立即执行)
- [ ] 删除已弃用的 3 个技能
- [ ] 合并重叠的 3 个技能
- [ ] 更新 skills.v2.json

### Phase 2: 分层 (短期)
- [ ] 为每个技能添加 `layer` 字段
- [ ] 创建 `skills-routing.yaml`
- [ ] 实现路由逻辑

### Phase 3: 按需加载 (中期)
- [ ] 实现 L3 技能的动态加载
- [ ] 实现自动卸载机制

---

## 九、指标与验证

### 9.1 成功指标

| 指标 | 当前 | 目标 |
|------|------|------|
| 常驻技能数 | 37+ | 17 |
| 平均决策步骤 | 5+ | ≤2 |
| 上下文占用 | 100% | ≤60% |
| 技能调用成功率 | ~70% | ≥90% |

### 9.2 验证方法

1. **决策测试**: 给定场景，验证选择的技能是否正确
2. **互斥测试**: 验证互斥组不会同时激活
3. **回退测试**: 验证失败场景的降级行为
4. **性能测试**: 测量常驻内存和响应时间

---

**附录：技能分组决策树**

```
用户输入
    │
    ├─ 包含 "workflow"/"yaml"/"流水线"？
    │   └─ YES → workflow-executor
    │
    ├─ 包含 "review"/"审查"？
    │   └─ YES → code-review
    │            │
    │            └─ 需要重构？
    │                └─ YES → code-refactor
    │
    ├─ 包含 "debug"/"bug"？
    │   └─ YES → systematic-debugging
    │            │
    │            └─ 已有方案？
    │                └─ YES → verification-before-completion
    │
    ├─ 包含 "database"？
    │   └─ YES → 加载 database-export / database-schema-designer
    │
    ├─ 包含 "ui"/"mockup"？
    │   └─ YES → 加载 ui-mockup-generator
    │
    └─ 其他 → task-runner (默认)
```
