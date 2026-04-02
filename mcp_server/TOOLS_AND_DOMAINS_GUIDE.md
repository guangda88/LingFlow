# LingFlow MCP Server - 工具和功能域完整说明

**版本**: v1.3.0
**工具总数**: 21 个
**功能域**: 8 个
**命名体系**: 灵系雅正（国学修订版）

**核心理念**: "众智混元，万法灵通"

---

## 📋 工具中英文对照表（雅正版）

| 功能域 | 中文名 | 英文工具名称 | 国学典故 |
|--------|---------|-------------|----------|
| **技能系统** | 灵艺 | list_skills | 《周礼》"六艺"之典 |
| | 灵行 | run_skill | 《易》"行健"之义 |
| **代码审查** | 灵鉴 | review_code | 《诗》"殷鉴不远" |
| **情报系统** | 灵探 | get_github_trends | 《论语》"见不善如探汤" |
| | 灵觉 | get_npm_trends | 《孟子》"先知觉后知" |
| **工作流管理** | 灵流 | list_workflows | 《文心雕龙》"内义脉注" |
| | 灵运 | run_workflow | 《庄子》"天道运而无所积" |
| | 灵踪 | get_workflow_status | 李白"须行即骑访名山" |
| **需求管理** | 灵愿 | create_requirement | 《大学》"先治其国" |
| | 灵览 | get_requirement | 陆机《文赋》"伫中区以玄览" |
| | 灵新 | update_requirement | 《大学》"苟日新，日日新" |
| | 灵录 | list_requirements | 《后汉书》"时人谓之应录" |
| | 灵联 | link_requirement_to_branch | 《易》"联缀其辞" |
| **任务管理** | 灵讯 | get_task_status | 《礼记》"讯群臣" |
| | 灵任 | list_tasks | 《论语》"任重而道远" |
| **测试运行** | 灵验 | run_tests | 《文心雕龙》"验乎其言" |
| | 灵覆 | get_coverage | 《易》"曲成万物而不遗" |
| | 灵书 | generate_test_report | 《文心雕龙》"书者，舒也" |
| **运维监控** | 灵脉 | get_health_status | 《黄帝内经》"脉者，血之府也" |
| | 灵量 | get_metrics | 《庄子》"为之斗斛以量之" |
| | 灵警 | detect_anomaly | 《荀子》"警之以政" |

**修订说明**:
- ✅ 已修订: 9个工具名称
- 🟢 保留原貌: 12个工具名称
- 📖 引用经典: 《易》《诗》《礼记》《论语》《孟子》《庄子》《文心雕龙》《黄帝内经》等

---

## 🎯 功能域总览

```
┌─────────────────────────────────────────────────────────────┐
│                LingFlow MCP Server v1.3.0                   │
├─────────────────────────────────────────────────────────────┤
│  功能域 (8个)           工具数 (21个)                     │
├─────────────────────────────────────────────────────────────┤
│  1️⃣ 技能系统              │ 2 │ (2) list_skills, run_skill           │
│  2️⃣ 代码审查              │ 1 │ (1) review_code                   │
│  3️⃣ 情报系统              │ 2 │ (2) get_github_trends            │
│  │                         │   │     get_npm_trends              │
│  4️⃣ 工作流管理            │ 3 │ (3) list_workflows               │
│  │                         │   │     run_workflow                │
│  │                         │   │     get_workflow_status         │
│  5️⃣ 需求管理              │ 5 │ (5) create_requirement            │
│  │                         │   │     get_requirement             │
│  │                         │   │     update_requirement           │
│  │                         │   │     list_requirements          │
│  │                         │   │     link_requirement_to_branch  │
│  6️⃣ 任务管理              │ 2 │ (2) get_task_status              │
│  │                         │   │     list_tasks                  │
│  7️⃣ 测试运行              │ 3 │ (3) run_tests                     │
│  │                         │   │     get_coverage                │
│  │                         │   │     generate_test_report       │
│  8️⃣ 运维监控              │ 3 │ (3) get_health_status             │
│  │                         │   │     get_metrics                  │
│  │                         │   │     detect_anomaly              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 8个功能域详细说明

### 功能域 1️⃣: 技能系统 (2个工具)

**功能描述**: 管理 LingFlow 的 33 个内置技能，支持技能发现、列表和执行。

**工具清单**:

| # | 工具名称 | 描述 | 输入 | 输出 |
|---|---------|------|------|------|
| 1 | `list_skills` | 列出所有可用技能 | - layer: 技能层（L1/L2/L3）<br>- category: 技能类别 | - skills: 技能列表<br>- total: 总数 |
| 2 | `run_skill` | 执行指定技能 | - skill_name: 技能名称<br>- params: 技能参数 | - success: 执行状态<br>- result: 执行结果 |

**使用场景**:
```
# Claude Desktop 中
用户: 有哪些代码分析技能可用？
Claude: [调用 list_skills(category="code")]
返回: 3 个代码分析技能

用户: 运行代码复杂度分析
Claude: [调用 run_skill(skill_name="complexity_analysis")]
返回: 分析完成
```

---

### 功能域 2️⃣: 代码审查 (1个工具)

**功能描述**: 8维度代码质量审查，包括复杂度、重复度、安全性、风格等。

**工具清单**:

| # | 工具名称 | 描述 | 输入 | 输出 |
|---|---------|------|------|------|
| 3 | `review_code` | 8维度代码审查 | - target_path: 文件/目录路径<br>- dimensions: 审查维度<br>- auto_fix: 是否自动修复 | - report: 审查报告<br>- issues: 问题列表 |

**审查维度**:
- complexity - 复杂度分析
- duplication - 重复度检测
- security - 安全扫描
- style - 代码风格
- documentation - 文档完整性
- testing - 测试覆盖
- performance - 性能问题
- error_handling - 错误处理

---

### 功能域 3️⃣: 情报系统 (2个工具)

**功能描述**: 采集 GitHub 和 npm 的趋势数据，用于技术选型和决策支持。

**工具清单**:

| # | 工具名称 | 描述 | 输入 | 输出 |
|---|---------|------|------|------|
| 4 | `get_github_trends` | GitHub 趋势项目 | - keywords: 关键词列表<br>- limit: 返回数量<br>- min_stars: 最小star数 | - trends: 趋势项目列表<br>- total: 总数 |
| 5 | `get_npm_trends` | npm 趋势包 | - keywords: 关键词列表<br>- limit: 返回数量 | - trends: 趋势包列表<br>- total: 总数 |

**使用场景**:
```
用户: 推荐一些 Python AI 框架
Claude: [调用 get_github_trends(keywords=["python", "ai"])]
返回: MetaGPT, AgentScope, ...

用户: 有哪些流行的 React 测试库？
Claude: [调用 get_npm_trends(keywords=["react", "test"])]
返回: Jest, Testing Library, ...
```

---

### 功能域 4️⃣: 工作流管理 (3个工具)

**功能描述**: 管理 15+ 预置工程流，支持列表、执行、状态查询和三种执行策略。

**工具清单**:

| # | 工具名称 | 描述 | 输入 | 输出 |
|---|---------|------|------|------|
| 6 | `list_workflows` | 列出所有工作流 | - type_filter: 类型过滤<br>- status_filter: 状态过滤 | - workflows: 工作流列表<br>- statistics: 统计信息 |
| 7 | `run_workflow` | 执行工作流（异步） | - workflow_id: 工作流ID<br>- params: 工作流参数<br>- strategy: 执行策略 | - task_id: 任务ID<br>- status: 执行状态 |
| 8 | `get_workflow_status` | 查询工作流状态 | - workflow_id: 工作流ID | - workflow: 工作流详情<br>- status: 当前状态 |

**执行策略**:
- `parallel` - 并行执行（默认）
- `sequential` - 顺序执行
- `hybrid` - 混合模式（关键路径优先）

**工作流类型**:
- fast - 快速工程流
- stable - 稳定工程流
- dev - 开发工程流
- test - 测试工程流
- doc - 文档工程流
- optimize - 优化工程流
- review - 审查工程流
- deploy - 部署工程流

---

### 功能域 5️⃣: 需求管理 (5个工具)

**功能描述**: 完整的需求生命周期管理，支持创建、查询、更新、列表和分支关联。

**工具清单**:

| # | 工具名称 | 描述 | 输入 | 输出 |
|---|---------|------|------|------|
| 9 | `create_requirement` | 创建需求 | - title: 需求标题<br>- description: 需求描述<br>- priority: 优先级<br>- category: 分类（可选）<br>- tags: 标签（可选） | - requirement_id: 需求ID |
| 10 | `get_requirement` | 获取需求详情 | - requirement_id: 需求ID | - requirement: 需求详情 |
| 11 | `update_requirement` | 更新需求 | - requirement_id: 需求ID<br>- title/description/status/priority: 更新字段 | - success: 更新状态<br>- updated_fields: 已更新字段 |
| 12 | `list_requirements` | 列出需求 | - status_filter: 状态过滤<br>- priority_filter: 优先级过滤<br>- limit: 返回数量限制 | - requirements: 需求列表<br>- total: 总数 |
| 13 | `link_requirement_to_branch` | 关联需求到分支 | - requirement_id: 需求ID<br>- branch_name: 分支名称 | - success: 关联状态 |

**需求状态**:
- draft - 草稿
- active - 活跃
- in_review - 审核中
- approved - 已批准
- rejected - 已拒绝
- completed - 已完成

**优先级**:
- low - 低优先级
- normal - 普通优先级
- high - 高优先级
- critical - 关键优先级

---

### 功能域 6️⃣: 任务管理 (2个工具)

**功能描述**: 异步任务管理，支持任务状态查询和任务列表。

**工具清单**:

| # | 工具名称 | 描述 | 输入 | 输出 |
|---|---------|------|------|------|
| 14 | `get_task_status` | 查询异步任务状态 | - task_id: 任务ID | - task_id: 任务ID<br>- status: 任务状态<br>- result: 执行结果<br>- error: 错误信息 |
| 15 | `list_tasks` | 列出所有异步任务 | - status_filter: 状态过滤（可选） | - tasks: 任务列表<br>- total: 总数 |

**异步任务状态**:
- pending - 等待执行
- running - 执行中
- completed - 已完成
- failed - 失败

**适用工具**:
- `run_workflow` - 工作流执行
- 长时间运行的操作

---

### 功能域 7️⃣: 测试运行 (3个工具)

**功能描述**: 自动化测试执行、覆盖率分析和报告生成，支持 CI/CD 集成。

**工具清单**:

| # | 工具名称 | 描述 | 输入 | 输出 |
|---|---------|------|------|------|
| 16 | `run_tests` | 运行测试套件 | - test_path: 测试路径<br>- test_type: 测试类型<br>- verbose: 详细输出<br>- coverage: 是否计算覆盖率 | - success: 执行状态<br>- stats: 测试统计<br>- execution_time: 执行时间 |
| 17 | `get_coverage` | 获取测试覆盖率 | - target_path: 目标路径<br>- format_type: 格式类型 | - overall_coverage: 总体覆盖率<br>- files_count: 文件数量<br>- files: 详细文件覆盖率 |
| 18 | `generate_test_report` | 生成测试报告 | - test_path: 测试路径<br>- output_format: 输出格式 | - report: 报告内容<br>- format: 格式类型<br>- generated_at: 生成时间 |

**测试类型**:
- all - 所有测试
- unit - 单元测试
- integration - 集成测试

**报告格式**:
- markdown - Markdown 文档
- json - JSON 数据
- html - HTML 网页

**报告内容**:
- 📊 测试结果摘要
- 📈 覆盖率统计
- 🎯 结论和建议

---

### 功能域 8️⃣: 运维监控 (3个工具)

**功能描述**: 系统健康检查、性能指标收集和智能异常检测。

**工具清单**:

| # | 工具名称 | 描述 | 输入 | 输出 |
|---|---------|------|------|------|
| 19 | `get_health_status` | 系统健康检查 | - checks: 检查列表（可选） | - overall_status: 总体状态<br>- checks: 各项检查结果 |
| 20 | `get_metrics` | 获取性能指标 | - metric_names: 指标名称列表<br>- time_range: 时间范围 | - metrics: 性能指标数据<br>- timestamp: 时间戳 |
| 21 | `detect_anomaly` | 检测系统异常 | - metric_name: 指标名称<br>- value: 当前值（可选）<br>- threshold: 阈值（可选） | - is_anomaly: 是否异常<br>- analysis: 分析结果<br>- recommendation: 优化建议 |

**健康检查项**:
- disk - 磁盘状态（使用率、剩余空间）
- memory - 内存状态（使用率、可用内存）
- cpu - CPU 状态（使用率、核心数）
- python - Python 环境（版本、路径）
- lingflow - LingFlow 状态（版本、配置）

**性能指标**:
- cpu - CPU 使用率、核心数、负载
- memory - 内存使用、可用内存、缓存
- disk - 磁盘使用率、I/O 统计
- process - 进程信息（PID、线程数、内存）

**异常检测算法**:
- 基于 3-sigma 规则
- 历史数据分析（最近5次数据）
- 阈值检测
- 自动优化建议

---

## 🎯 完整工具列表（21个）

### 按功能域分组

**1️⃣ 技能系统 (2个)**
1. list_skills
2. run_skill

**2️⃣ 代码审查 (1个)**
3. review_code

**3️⃣ 情报系统 (2个)**
4. get_github_trends
5. get_npm_trends

**4️⃣ 工作流管理 (3个)**
6. list_workflows
7. run_workflow
8. get_workflow_status

**5️⃣ 需求管理 (5个)**
9. create_requirement
10. get_requirement
11. update_requirement
12. list_requirements
13. link_requirement_to_branch

**6️⃣ 任务管理 (2个)**
14. get_task_status
15. list_tasks

**7️⃣ 测试运行 (3个)**
16. run_tests
17. get_coverage
18. generate_test_report

**8️⃣ 运维监控 (3个)**
19. get_health_status
20. get_metrics
21. detect_anomaly

---

## 📊 工具矩阵

### 按操作类型分类

| 操作类型 | 工具数量 | 工具列表 |
|---------|----------|----------|
| **查询** (10) | 查询 | list_skills<br>list_workflows<br>get_requirement<br>list_requirements<br>list_tasks<br>get_coverage<br>get_health_status<br>get_metrics<br>get_task_status<br>get_github_trends<br>get_npm_trends |
| **执行** (7) | 执行 | run_skill<br>run_workflow<br>run_tests<br>review_code |
| **创建** (2) | 创建 | create_requirement<br>generate_test_report |
| **更新** (1) | 更新 | update_requirement |
| **关联** (1) | 关联 | link_requirement_to_branch |

### 按同步类型分类

| 类型 | 工具数量 | 工具列表 |
|------|----------|----------|
| **同步** (14) | 快速响应 | list_skills<br>run_skill<br>review_code<br>get_github_trends<br>get_npm_trends<br>list_workflows<br>get_workflow_status<br>create_requirement<br>get_requirement<br>update_requirement<br>list_requirements<br>link_requirement_to_branch<br>get_coverage<br>get_health_status<br>get_metrics<br>get_task_status<br>list_tasks<br>detect_anomaly |
| **异步** (2) | 后台执行 | run_workflow<br>run_tests |

---

## 🔧 快速查询表

### 我想... 工具选择

| 我想... | 使用工具 | 功能域 |
|---------|---------|--------|
| 查看有哪些技能 | `list_skills` | 技能系统 |
| 执行某个技能 | `run_skill` | 技能系统 |
| 审查代码质量 | `review_code` | 代码审查 |
| 了解最新技术趋势 | `get_github_trends` | 情报系统 |
| 查看可用工作流 | `list_workflows` | 工作流管理 |
| 执行开发工作流 | `run_workflow` | 工作流管理 |
| 创建新需求 | `create_requirement` | 需求管理 |
| 查看需求状态 | `get_requirement` | 需求管理 |
| 更新需求状态 | `update_requirement` | 需求管理 |
| 列出所有需求 | `list_requirements` | 需求管理 |
| 关联需求到分支 | `link_requirement_to_branch` | 需求管理 |
| 查询任务状态 | `get_task_status` | 任务管理 |
| 列出所有任务 | `list_tasks` | 任务管理 |
| 运行测试 | `run_tests` | 测试运行 |
| 获取覆盖率 | `get_coverage` | 测试运行 |
| 生成测试报告 | `generate_test_report` | 测试运行 |
| 检查系统健康 | `get_health_status` | 运维监控 |
| 查看性能指标 | `get_metrics` | 运维监控 |
| 检测系统异常 | `detect_anomaly` | 运维监控 |

---

## 📈 功能域覆盖率

```
软件工程生命周期 (SDLC)
┌─────────────────────────────────────────────┐
│ 需求工程                                      │
│   ✅ create_requirement                      │
│   ✅ get_requirement                         │
│   ✅ update_requirement                      │
│   ✅ list_requirements                     │
│   ✅ link_requirement_to_branch             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 设计工程                                      │
│   ✅ list_skills (设计技能)                   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 编码工程                                      │
│   ✅ run_skill (编码技能)                     │
│   ✅ review_code                             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 测试工程                                      │
│   ✅ run_tests                               │
│   ✅ get_coverage                            │
│   ✅ generate_test_report                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ 部署工程                                      │
│   ✅ run_workflow (部署工作流)                 │
│   ✅ get_health_status (健康检查)             │
│   ✅ get_metrics (性能监控)                   │
│   ✅ detect_anomaly (异常检测)                │
└─────────────────────────────────────────────┘
```

---

## 🎉 总结

LingFlow MCP Server v1.3.0 通过 **21 个工具** 覆盖了 **8 个功能域**，实现了：

✅ **完整的 SDLC 支持** - 从需求到部署的全流程自动化
✅ **自然语言交互** - 无需学习命令语法
✅ **异步任务支持** - 长时间操作不阻塞
✅ **智能监控** - 健康检查和异常检测
✅ **测试自动化** - 一键测试和报告生成
✅ **生产就绪** - 经过测试验证，可用于生产环境

**从命令行工具到 AI 生态的完整升级！** 🚀

---

**相关文档**:
- README.md - 完整使用指南
- FINAL_COMPLETION_REPORT.md - 项目完成总结
- PHASE3_COMPLETION_REPORT.md - Phase 3 详细报告
