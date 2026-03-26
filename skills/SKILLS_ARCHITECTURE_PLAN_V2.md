# LingFlow 技能架构优化计划 V2.0

**版本**: 2.0
**日期**: 2026-03-26
**基于**: 对齐分析报告
**目标**: 技能数量控制在 30 个以内，核心常驻 17 个

---

## 一、当前状态分析

### 1.1 技能清单 (当前 32 个)

```
L1: 核心调度层 (5 个) ────────────────────────────────
├── workflow-executor      ✅ 工作流执行
├── task-runner            ✅ 任务执行
├── conditional-branch     ✅ 条件分支
├── loop-iterator          ✅ 循环迭代
└── error-handler          ✅ 错误处理

L2: 专业能力层 (12 个) ───────────────────────────────
├── 代码质量组 (互斥):
│   ├── code-review        ✅ 8维审查
│   └── code-refactor      ✅ 代码重构
├── 开发流程组 (顺序):
│   ├── brainstorming      ✅ 需求探索
│   ├── systematic-debugging ✅ 系统调试
│   └── verification-before-completion ✅ 完成验证
├── 测试验证组 (互斥):
│   ├── test-runner        ✅ 测试执行
│   └── test-driven-development ✅ TDD
├── 版本控制组 (互斥):
│   ├── using-git-worktrees ✅ Git 工作树
│   └── finishing-a-development-branch ✅ 完成分支
└── 通用服务:
    ├── notification       ✅ 通知
    └── skill-creator      ✅ 创建技能

L3: 扩展能力层 (按需加载, 15 个) ────────────────────
├── 设计工具 (5 个):
│   ├── writing-plans              ✅ 方案设计
│   ├── api-doc-generator          ✅ API 文档 [P0]
│   ├── ui-mockup-generator        ✅ UI 原型 [P0]
│   └── database-schema-designer   ✅ 数据库设计 [P0]
├── DevOps (3 个):
│   ├── ci-cd-orchestrator         ✅ CI/CD 编排 [P1]
│   ├── deployment-automation      ✅ 自动化部署 [P1]
│   └── environment-manager        ✅ 环境管理 [P1]
├── 数据处理 (1 个):
│   └── database-export            ✅ 数据库导出
├── 工作流高级 (2 个):
│   ├── dispatching-parallel-agents ✅ 并行协调
│   └── subagent-driven-development ✅ 子代理开发
└── 技能管理 (4 个):
    ├── skill-integration          ✅ 技能集成
    ├── skill-categorization       ✅ 技能分类
    ├── skill-versioning           ✅ 版本管理
    ├── skill-analytics            ✅ 使用分析
    ├── skill-templates            ✅ 模板管理
    └── skill-testing              ✅ 技能测试

待删除/合并 (6 个) ─────────────────────────────────
├── requesting-code-review   ❌ 废弃 → code-review
├── receiving-code-review    ❌ 废弃 → code-review
├── executing-plans          ❌ 废弃 → subagent-driven
├── code-analysis            ❌ 合并 → code-review
├── code-optimizer           ❌ 分流 → review + refactor
└── skill-automation         ❌ 合并 → skill-creator

其他 (2 个) ────────────────────────────────────────
├── code-review-js           ✅ JS 专项审查
└── test-runner              ✅ (已在 L2 列出)
```

### 1.2 统计摘要

| 类别 | 数量 | 状态 |
|------|------|------|
| **核心常驻 (L1+L2)** | 17 | 保持不变 |
| **扩展按需 (L3)** | 15 | 按需加载 |
| **待删除** | 6 | 安全移除 |
| **当前总计** | 32 | → 26 (删除后) |
| **目标** | ≤30 | ✅ 达标 |

---

## 二、已完成的 P0/P1 技能

### 2.1 P0 核心缺失 (全部完成 ✅)

| 技能 | 优先级 | 工程影响 | 状态 |
|------|--------|----------|------|
| `api-doc-generator` | P0 | 设计阶段 60%→85% | ✅ 已实现 |
| `ui-mockup-generator` | P0 | 设计阶段 0%→60% | ✅ 已实现 |
| `database-schema-designer` | P0 | 设计阶段 30%→70% | ✅ 已实现 |

### 2.2 P1 流程增强 (全部完成 ✅)

| 技能 | 优先级 | 工程影响 | 状态 |
|------|--------|----------|------|
| `ci-cd-orchestrator` | P1 | 部署阶段 50%→70% | ✅ 已实现 |
| `deployment-automation` | P1 | 部署阶段 65%→80% | ✅ 已实现 |
| `environment-manager` | P1 | 部署阶段 70%→80% | ✅ 已实现 |

### 2.3 实施验证

```bash
# 验证 P0/P1 技能实现
skills/api-doc-generator/implementation.py       ✅ 存在
skills/ui-mockup-generator/implementation.py     ✅ 存在
skills/database-schema-designer/implementation.py ✅ 存在
skills/ci-cd-orchestrator/implementation.py      ✅ 存在
skills/deployment-automation/implementation.py   ✅ 存在
skills/environment-manager/implementation.py     ✅ 存在

# 验证测试覆盖
tests/api-doc-generator/                          ✅ 存在
tests/ui-mockup-generator/                        ✅ 存在
tests/database-schema-designer/                   ✅ 存在
tests/ci-cd-orchestrator/                         ✅ 存在
tests/deployment-automation/                      ✅ 存在
tests/environment-manager/                        ✅ 存在
```

---

## 三、技能精简计划

### 3.1 删除清单 (6 个)

| 技能 | 删除理由 | 影响评估 | 操作 |
|------|----------|----------|------|
| `requesting-code-review` | 被 code-review 替代 | 无影响 | DELETE |
| `receiving-code-review` | 被 code-review 替代 | 无影响 | DELETE |
| `executing-plans` | 被 subagent-driven 替代 | 无影响 | DELETE |
| `code-analysis` | 功能合并到 code-review | 低影响 | DELETE |
| `code-optimizer` | 功能分流到 review + refactor | 低影响 | DELETE |
| `skill-automation` | 合并到 skill-creator | 低影响 | DELETE |

### 3.2 删除操作步骤

```bash
# 1. 删除技能目录
rm -rf skills/requesting-code-review/
rm -rf skills/receiving-code-review/
rm -rf skills/executing-plans/
rm -rf skills/code-analysis/
rm -rf skills/code-optimizer/
rm -rf skills/skill-automation/

# 2. 更新 skills.v2.json
# - 从 skills 数组移除
# - 更新 deprecated 列表

# 3. 删除测试目录（如果有）
rm -rf tests/code-analysis/
rm -rf tests/code-optimizer/
rm -rf tests/skill-automation/
```

---

## 四、分层架构配置

### 4.1 技能分层定义

```yaml
# skills-layer-configuration.yaml
layers:
  L1:  # 核心调度层 - 永不卸载
    loading: "eager"
    unloading: "never"
    skills:
      - workflow-executor
      - task-runner
      - conditional-branch
      - loop-iterator
      - error-handler

  L2:  # 专业能力层 - 常驻
    loading: "eager"
    unloading: "never"
    groups:
      code_quality:          # 互斥组
        mutex: true
        skills: [code-review, code-refactor]
      development_flow:      # 顺序组
        ordered: true
        chain: [brainstorming, systematic-debugging, verification-before-completion]
      testing:               # 互斥组
        mutex: true
        skills: [test-runner, test-driven-development]
      git:                   # 互斥组
        mutex: true
        skills: [using-git-worktrees, finishing-a-development-branch]
      common:                # 可组合
        skills: [notification, skill-creator]

  L3:  # 扩展能力层 - 按需加载
    loading: "lazy"
    unloading: "after_task"
    categories:
      design:
        trigger_keywords: [api, ui, database, design, schema]
        skills:
          - writing-plans
          - api-doc-generator
          - ui-mockup-generator
          - database-schema-designer
      devops:
        trigger_keywords: [ci, cd, deploy, pipeline, environment]
        skills:
          - ci-cd-orchestrator
          - deployment-automation
          - environment-manager
      data:
        trigger_keywords: [export, database, backup]
        skills:
          - database-export
      workflow_advanced:
        trigger_keywords: [parallel, concurrent, agent]
        skills:
          - dispatching-parallel-agents
          - subagent-driven-development
      skill_management:
        trigger_keywords: [skill, integration, version, template]
        skills:
          - skill-integration
          - skill-categorization
          - skill-versioning
          - skill-analytics
          - skill-templates
          - skill-testing
```

### 4.2 触发词路由表

```yaml
# skills-routing.yaml
routing:
  # L1 路由 - 工作流控制
  - triggers: [workflow, yaml, 流水线, 批量, 多任务]
    route: L1.workflow-executor
    priority: 10

  - triggers: [run, execute, call, 执行]
    route: L1.task-runner
    priority: 9

  # L2 路由 - 专业能力
  - triggers: [review, 审查, 检查, code quality, 代码质量]
    route: L2.code-review
    group: code_quality
    priority: 8

  - triggers: [refactor, 重构, 优化代码]
    route: L2.code-refactor
    group: code_quality
    require_after: L2.code-review
    priority: 7

  - triggers: [debug, fix, bug, 错误, 异常]
    route: L2.systematic-debugging
    phase: debugging
    priority: 8

  - triggers: [test, pytest, 测试]
    route: L2.test-runner
    group: testing
    priority: 7

  # L3 路由 - 扩展能力
  - triggers: [api doc, 接口文档, openapi, swagger]
    route: L3.api-doc-generator
    category: design
    priority: 6

  - triggers: [ui, mockup, 原型, 界面]
    route: L3.ui-mockup-generator
    category: design
    priority: 6

  - triggers: [database design, schema, 表结构, 数据库设计]
    route: L3.database-schema-designer
    category: design
    priority: 6

  - triggers: [ci cd, pipeline, github actions, jenkins]
    route: L3.ci-cd-orchestrator
    category: devops
    priority: 6

  - triggers: [deploy, 部署, 发布]
    route: L3.deployment-automation
    category: devops
    priority: 6
```

---

## 五、工程流程对齐验证

### 5.1 SDLC 阶段覆盖

| SDLC 阶段 | 覆盖率 | 主要技能 | 状态 |
|-----------|--------|----------|------|
| 1. 需求分析 | 65% | brainstorming | ✅ L2 常驻 |
| 2. 设计阶段 | 85% | api-doc, ui-mockup, db-schema | ✅ L3 按需 |
| 3. 编码实现 | 90% | code-review, code-refactor | ✅ L2 常驻 |
| 4. 测试阶段 | 80% | test-runner, TDD | ✅ L2 常驻 |
| 5. 部署发布 | 80% | ci-cd, deployment, env | ✅ L3 按需 |
| 6. 监控运维 | 60% | debugging, error-handler | ⚠️ 需改进 |
| 7. 维护迭代 | 75% | code-review, refactor | ✅ L2 常驻 |

**综合对齐度**: **82%** (目标 85%，差距 3%)

### 5.2 剩余缺口分析

```
当前缺口 3% (85% - 82%):
├── 监控运维阶段 (当前 60% → 目标 70%)
│   ├── 缺少: APM 集成
│   ├── 缺少: 业务指标监控
│   └── 缺少: 分布式追踪
│
└── 决策: 暂不新增，通过现有 debugging + notification 应对
```

---

## 六、实施计划

### 6.1 Phase 1: 清理 (立即执行)

- [ ] 删除 6 个冗余/废弃技能
- [ ] 更新 skills.v2.json
- [ ] 清理测试目录
- [ ] 更新文档引用

### 6.2 Phase 2: 配置 (短期)

- [ ] 创建 skills-layer-configuration.yaml
- [ ] 创建 skills-routing.yaml
- [ ] 实现路由逻辑
- [ ] 实现分层加载

### 6.3 Phase 3: 验证 (中期)

- [ ] 决策测试
- [ ] 互斥测试
- [ ] 回退测试
- [ ] 性能测试

---

## 七、指标与目标

### 7.1 成功指标

| 指标 | 当前 | 目标 | 状态 |
|------|------|------|------|
| 技能总数 | 32 | ≤30 | ⚠️ 删除后 26 |
| 核心常驻 | 17 | 17 | ✅ |
| 扩展按需 | 15 | ≤15 | ✅ |
| SDLC 对齐度 | 82% | 85% | ⚠️ 差 3% |

### 7.2 质量指标

| 指标 | 目标 | 验证方式 |
|------|------|----------|
| 技能调用成功率 | ≥90% | 回归测试 |
| 平均决策步骤 | ≤2 | 场景测试 |
| 上下文占用 | ≤60% | 内存分析 |
| L3 卸载延迟 | <1s | 性能测试 |

---

## 八、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 删除技能影响现有工作流 | 中 | 保留 30 天迁移期 |
| 路由逻辑复杂度 | 中 | 使用决策树简化 |
| L3 加载延迟 | 低 | 预加载常用技能 |

---

**文档版本**: 2.0
**下次审查**: 2026-04-01
**负责人**: LingFlow Team
