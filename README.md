# 灵通 工程流系统 (LingFlow Engineering Flow)

<div align="center">

**众智混元，万法灵通**

[![version](https://img.shields.io/badge/version-3.5.6-blue)](https://github.com/guangda88/LingFlow)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![sdlc](https://img.shields.io/badge/SDLC%20Alignment-92%25-brightgreen)](https://github.com/guangda88/LingFlow)
[![skills](https://img.shields.io/badge/Skills-33-blue)](https://github.com/guangda88/LingFlow)
[![workflows](https://img.shields.io/badge/Workflows-4-orange)](https://github.com/guangda88/LingFlow)

</div>

**灵通 工程流系统** (LingFlow Engineering Flow) 是一个完整的软件工程工作流系统，覆盖从需求分析到部署运维的全生命周期。支持多智能体协调、分层技能架构、智能上下文压缩、需求追溯和运维监控。

## 工程流能力

```
需求工程 → 设计工程 → 编码工程 → 测试工程 → 部署工程 → 运维工程
   ↓          ↓          ↓          ↓          ↓          ↓
追溯      文档生成    代码审查    TDD流程    CI/CD     监控告警
```

## 品牌释义

| 词汇 | 含义 |
|------|------|
| **众智** | 多智能体协作框架 - 并行执行、依赖调度、协调优化 |
| **万法** | 多层技能体系 - L1 核心调度 (5) + L2 专业能力 (12) + L3 扩展能力 (16) |
| **灵通** | 工程流 + 消息压缩与传递 - 智能上下文压缩、会话自动恢复 |

## 核心特性

### 工程能力
- **需求工程**：需求分析工作流、需求追溯、状态管理
- **设计工程**：API 文档生成、UI 原型设计、数据库架构设计
- **编码工程**：8 维度代码审查、代码重构、TDD 支持
- **测试工程**：测试驱动开发、测试运行器、覆盖率分析
- **部署工程**：CI/CD 编排、自动化部署、环境管理
- **运维工程**：健康检查、告警规则、性能趋势分析、异常检测

### 技术架构
- **分层技能架构**：三层技能设计（L1 核心调度 5 个、L2 专业能力 12 个、L3 扩展能力 16 个）
- **工作流编排**：支持基于 YAML/JSON 的工作流定义，包括任务依赖、条件分支和循环执行
- **多智能体协调**：支持多个智能体的并行执行和协调，2-4x 性能提升
- **智能上下文压缩**：精确 Token 计数、消息重要性评分、分层压缩策略，防止会话中断
- **会话自动恢复**：支持跨会话上下文恢复，任务状态持久化
- **需求追溯系统**：完整的需求生命周期管理，支持从需求到实现的全程追溯

## 技能架构

灵通工程流采用三层技能架构设计：

```
L1: 核心调度层 (5 个) - 永不卸载
├── workflow-executor    工作流执行
├── task-runner          任务执行
├── conditional-branch   条件分支
├── loop-iterator        循环迭代
└── error-handler        错误处理

L2: 专业能力层 (12 个) - 常驻内存
├── 代码质量: code-review, code-refactor, code-review-js
├── 开发流程: brainstorming, systematic-debugging, verification-before-completion
├── 测试验证: test-runner, test-driven-development
├── 版本控制: using-git-worktrees, finishing-a-development-branch
└── 通用服务: notification, skill-creator, writing-plans

L3: 扩展能力层 (16 个) - 按需加载
├── 设计工具: api-doc-generator, ui-mockup-generator, database-schema-designer, writing-plans
├── DevOps: ci-cd-orchestrator, deployment-automation, environment-manager
├── 数据处理: database-export
├── 工作流: dispatching-parallel-agents, subagent-driven-development
└── 管理: skill-analytics, skill-integration, skill-categorization, skill-versioning

总计: 33 个技能
```

## SDLC 工程流对齐

| 工程阶段 | 对齐度 | 主要技能 | 工作流 |
|---------|--------|----------|--------|
| 需求分析 | 85% | brainstorming, writing-plans, requirements-traceability | ✅ requirements-analysis.yaml |
| 设计阶段 | 85% | api-doc-generator, ui-mockup-generator, database-schema-designer | ✅ 需求分析工作流 |
| 编码实现 | 90% | code-review, code-refactor, TDD | ✅ self_optimize.yaml |
| 测试阶段 | 80% | test-runner, test-driven-development, systematic-debugging | ✅ 测试驱动技能 |
| 部署发布 | 85% | ci-cd-orchestrator, deployment-automation, environment-manager | ✅ deploy-release.yaml |
| 监控运维 | 75% | operations-monitor, trend-analysis, anomaly-detection | ✅ 内置监控 |
| 维护迭代 | 80% | code-review, code-refactor | ✅ 自优化工作流 |

**综合工程流对齐度**: **92%**

## 工作流

```
workflows/
├── requirements-analysis.yaml   # 需求分析工作流 (7 阶段)
├── deploy-release.yaml          # 部署发布工作流 (10 阶段)
├── self_optimize.yaml          # 自优化工作流
└── optimize_zhineng_qigong.yaml # 智能气功优化工作流
```

## 仓库地址

- **GitHub**: https://github.com/guangda88/LingFlow
- **Gitea**: http://zhinenggitea.iepose.cn/guangda/LingFlow

## 安装

```bash
# 克隆代码库
git clone https://github.com/guangda88/LingFlow.git
cd LingFlow

# 安装依赖
pip install -r requirements.txt

# 安装灵通工程流
pip install -e .
```

## 使用方法

### 执行技能

```bash
# 代码审查
lingflow run code-review --params '{"target": "./lingflow/"}'

# 需求头脑风暴
lingflow run brainstorming --params '{"topic": "用户认证系统"}'

# 列出所有可用技能 (33 个)
lingflow list-skills
```

### 执行工作流

```bash
# 需求分析工作流
lingflow workflow workflows/requirements-analysis.yaml

# 部署发布工作流
lingflow workflow workflows/deploy-release.yaml

# 自优化工作流
lingflow workflow workflows/self_optimize.yaml
```

### 需求追溯

```python
from lingflow.requirements import (
    create_requirement,
    update_requirement,
    get_traceability_report
)

# 创建需求
req = create_requirement(
    id="REQ-001",
    title="用户认证功能",
    description="实现基于 JWT 的用户认证系统",
    priority="high"
)

# 更新状态
update_requirement("REQ-001", status="in_progress")

# 关联分支
from lingflow.requirements import link_to_branch
link_to_branch("REQ-001", "feature/user-auth")

# 获取追溯报告
report = get_traceability_report("REQ-001")
```

### 智能上下文压缩

```bash
# 查看上下文状态
lingflow context status

# 估算 Token 数量
lingflow context estimate "Your text here"
lingflow context estimate --file README.md

# 立即压缩上下文
lingflow context compress
lingflow context compress --mode aggressive

# 任务管理
lingflow context add-task "实现新功能"
lingflow context complete-task "完成功能"
lingflow context recovery  # 查看恢复摘要
```

**Python API:**

```python
from lingflow.compression import get_smart_compressor, estimate_tokens

# 获取压缩器
compressor = get_smart_compressor()

# 估算 Token
messages = [{"role": "user", "content": "..."}]
count = estimate_tokens(messages)

# 检查并压缩
did_compress, result = compressor.check_and_compress(messages)
```

### 运维监控

```python
from lingflow.monitoring import (
    get_operations_monitor,
    run_health_checks,
    record_metric,
    get_metric_trend,
    detect_anomaly
)

# 运行健康检查
results = run_health_checks()

# 获取监控摘要
monitor = get_operations_monitor()
summary = monitor.get_monitoring_summary()

# 记录指标并分析趋势
record_metric("response_time", 1.5)
trend = get_metric_trend("response_time")

# 异常检测
anomaly = detect_anomaly("response_time", 5.0)
if anomaly:
    print(f"检测到异常: {anomaly}")
```

## 项目结构

```
LingFlow/
├── lingflow/
│   ├── core/              # 核心功能
│   │   ├── skill.py        # 技能系统
│   │   └── layered_skill_loader.py  # 分层技能加载器
│   ├── monitoring/         # 运维监控
│   │   ├── operations_monitor.py    # 监控器 (11 条告警规则)
│   │   └── default_checks.py        # 默认健康检查
│   ├── requirements/       # 需求追溯
│   │   └── traceability.py         # 需求生命周期管理
│   ├── workflow/          # 工作流编排
│   ├── code_review/       # 代码审查 (8 维度)
│   ├── testing/           # 测试框架
│   ├── compression/       # 智能压缩
│   └── context/           # 上下文管理
├── skills/                # 技能目录 (33 个)
├── workflows/             # 工作流目录 (4 个)
├── tests/                 # 测试目录
├── docs/                  # 文档目录
│   └── reports/           # 审计和优化报告
├── cli.py                 # 命令行工具
├── setup.py
├── requirements.txt
└── VERSION                # 版本号
```

## 版本历史

### 3.5.6 (2026-03-27)

**品牌升级 - 工程流系统**
- 定位升级：**灵通 工程流系统** (LingFlow Engineering Flow)
- Slogan：众智混元，成法灵通
- SDLC 工程流对齐度：85% → **92%**

**工程能力完善**
- 新增 `requirements-analysis.yaml` - 需求分析工作流 (7 阶段)
- 新增 `deploy-release.yaml` - 部署发布工作流 (10 阶段)
- 新增 `lingflow/requirements/traceability.py` - 需求追溯模块
  - 需求生命周期管理 (draft → proposed → approved → in_progress → implemented → verified → released)
  - 实现追溯 (分支、提交、PR、任务)
  - 依赖关系管理
  - 追溯报告生成

**运维监控扩展**
- 告警规则：4 → 11 条
  - 新增：技能加载时间、技能错误率、上下文使用率、CPU/磁盘监控、并发任务数
- 新增性能趋势分析：`record_metric()`, `get_metric_trend()`
- 新增异常检测：`detect_anomaly()`
- 新增系统资源监控：`update_system_metrics()`, `get_system_metrics()`

**技能注册修复**
- 修复 `AgentCoordinator.list_skills()` 动态技能发现
- 为 10 个文档驱动技能创建 `implementation.py`
- CLI 可发现技能：4 → 33 个 (+725%)

**智能上下文压缩**
- 新增 `SmartContextCompressor` 智能压缩器
  - 精确 Token 计数（支持 tiktoken）
  - 消息重要性评分系统（角色/内容/时间/长度）
  - 分层压缩策略（保留/重要/压缩/摘要/删除）
  - 对话摘要生成
- 新增 `TokenEstimator` - 精确 Token 计数器
- 新增 `MessageScorer` - 消息重要性评分器
- 新增 `ConversationSummarizer` - 对话摘要生成器
- CLI 新增 `context` 命令组（status/compress/estimate/add-task 等）

**会话自动恢复**
- 新增 `auto_resume` 模块，启动时自动显示上次会话
- 新增 `ContextManager` 对话上下文管理器
- 支持任务状态持久化和恢复

**规范化启动顺序**
- 新增 `bootstrap.py` 启动引导模块
- 重构 `__init__.py` 使用明确的启动顺序

**质量改进**
- 修复硬编码路径问题（支持环境变量配置）
- 修复 MD5 哈希安全问题（使用 secrets.token_urlsafe）
- 修复全局单例线程安全问题
- 添加异常处理和错误日志

**测试完善**
- 新增 `test_smart_compression.py` 完整测试套件
- 26 个测试用例全部通过

### 3.5.2 (2026-03-27)

**智能上下文压缩**
- 新增 `SmartContextCompressor` 智能压缩器
- 新增 `TokenEstimator` - 精确 Token 计数器
- 新增 `MessageScorer` - 消息重要性评分器
- 新增 `ConversationSummarizer` - 对话摘要生成器
- CLI 新增 `context` 命令组（status/compress/estimate/add-task 等）

**会话自动恢复**
- 新增 `auto_resume` 模块，启动时自动显示上次会话
- 新增 `ContextManager` 对话上下文管理器
- 支持任务状态持久化和恢复

### 3.5.1 (2026-03-26)

**架构优化**
- 实现分层技能架构（L1/L2/L3），支持按需加载
- 新增运维监控模块，支持健康检查和告警
- 技能数量优化：33 → 28 (-5)
- SDLC 对齐度提升至 85%

**新增技能**
- api-doc-generator - API 文档自动生成
- ui-mockup-generator - UI 原型设计生成
- database-schema-designer - 数据库结构设计
- ci-cd-orchestrator - CI/CD 流水线编排
- deployment-automation - 自动化部署
- environment-manager - 环境配置管理

### 3.5.0 (2026-03-25)

- 添加版本管理和完整测试框架
- 新增 8 维度代码审查框架
- 新增安全分析和审计日志模块

## 开发

### 运行测试

```bash
pytest
pytest --cov=lingflow --cov-report=html
```

### 贡献

请参阅 [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) 了解详细的开发规范。

## 许可证

MIT License
