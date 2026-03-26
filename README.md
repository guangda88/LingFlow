# LingFlow

[![version](https://img.shields.io/badge/version-3.5.2-blue)](https://github.com/guangda88/LingFlow)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![sdlc](https://img.shields.io/badge/SDLC%20Alignment-85%25-brightgreen)](https://github.com/guangda88/LingFlow)

LingFlow 是一个强大的工作流执行系统，支持多智能体协调、分层技能架构、智能上下文压缩和运维监控等功能。

## 核心特性

- **分层技能架构**：三层技能设计（L1 核心调度、L2 专业能力、L3 扩展能力）
- **工作流编排**：支持基于 YAML/JSON 的工作流定义，包括任务依赖、条件分支和循环执行
- **多智能体协调**：支持多个智能体的并行执行和协调
- **智能上下文压缩**：精确 Token 计数、消息重要性评分、分层压缩策略，防止会话中断
- **会话自动恢复**：支持跨会话上下文恢复，任务状态持久化
- **运维监控**：内置健康检查、告警规则和性能监控
- **代码审查**：8 维度代码审查框架（质量、架构、性能、安全、可维护性等）
- **测试框架**：完整的单元测试、集成测试和 E2E 测试支持

## 技能架构

LingFlow 采用三层技能架构设计：

```
L1: 核心调度层 (5 个) - 永不卸载
├── workflow-executor    工作流执行
├── task-runner          任务执行
├── conditional-branch   条件分支
├── loop-iterator        循环迭代
└── error-handler        错误处理

L2: 专业能力层 (12 个) - 常驻内存
├── 代码质量: code-review, code-refactor, code-review-js
├── 开发流程: brainstorming, systematic-debugging, verification
├── 测试验证: test-runner, test-driven-development
├── 版本控制: using-git-worktrees, finishing-branch
└── 通用服务: notification, skill-creator, writing-plans

L3: 扩展能力层 (11 个) - 按需加载
├── 设计工具: api-doc-generator, ui-mockup-generator, database-schema-designer
├── DevOps: ci-cd-orchestrator, deployment-automation, environment-manager
├── 数据处理: database-export
├── 工作流: dispatching-parallel-agents, subagent-driven-development
└── 管理: skill-analytics

总计: 28 个技能
```

## SDLC 流程对齐

| 阶段 | 对齐度 | 主要技能 |
|------|--------|----------|
| 需求分析 | 65% | brainstorming, writing-plans |
| 设计阶段 | 85% | api-doc, ui-mockup, db-schema |
| 编码实现 | 90% | code-review, code-refactor |
| 测试阶段 | 80% | test-runner, TDD, debugging |
| 部署发布 | 80% | ci-cd, deployment, environment |
| 监控运维 | 70% | operations-monitor, analytics |
| 维护迭代 | 75% | code-review, refactor |

**综合对齐度**: **85%**

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

# 安装 LingFlow
pip install -e .
```

## 使用方法

### 执行技能

```bash
# 代码审查
lingflow run code-review --params '{"target": "./lingflow/"}'

# 列出可用技能
lingflow list-skills
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

### 执行工作流

```bash
# 自优化工作流
lingflow workflow workflows/self_optimize.yaml
```

### 运维监控

```python
from lingflow.monitoring import get_operations_monitor, run_health_checks

# 运行健康检查
results = run_health_checks()

# 获取监控摘要
monitor = get_operations_monitor()
summary = monitor.get_monitoring_summary()
```

## 项目结构

```
LingFlow/
├── lingflow/
│   ├── core/              # 核心功能
│   │   ├── skill.py        # 技能系统
│   │   └── layered_skill_loader.py  # 分层技能加载器
│   ├── monitoring/         # 运维监控
│   │   ├── operations_monitor.py
│   │   └── default_checks.py
│   ├── workflow/          # 工作流编排
│   ├── code_review/       # 代码审查
│   ├── testing/           # 测试框架
│   └── utils/             # 工具模块
├── skills/                # 技能目录 (28 个)
├── tests/                 # 测试目录
├── docs/                  # 文档目录
│   └── reports/           # 审计和优化报告
├── cli.py                 # 命令行工具
├── setup.py
├── requirements.txt
└── VERSION                # 版本号
```

## 版本历史

### 3.5.2 (2026-03-27)

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
- 修复 `session.py` 中 `'task'` 键不存在的问题

**测试完善**
- 新增 `test_smart_compression.py` 完整测试套件
- 26 个测试用例全部通过

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

**技术债务清理**
- 项目文档结构整理
- 代码文档完善
- 根目录文件清理（61 → 3 个 MD 文件）

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
