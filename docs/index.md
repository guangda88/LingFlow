# LingFlow API 文档

## 众智混元，万法灵通

LingFlow 是一个完整覆盖软件工程全生命周期的工程流系统。

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 核心特性

### 🎯 完整工程流程
- **需求工程** → 需求追踪、追溯性管理
- **设计工程** → 架构设计、模式选择
- **编码工程** → 代码审查、质量保证
- **测试工程** → 自动化测试、覆盖率分析
- **部署工程** → 部署流程、环境管理
- **运维工程** → 监控告警、性能优化

### 🤖 智能Agent系统
- **多Agent协调** - 智能任务分发和执行
- **工作流编排** - 灵活的YAML/JSON工作流定义
- **上下文管理** - 智能压缩和恢复机制
- **安全防护** - 内置guardrail和hooks系统

### 🔄 自优化系统
- **Phase 4: 参数优化** - Optuna驱动的参数调优
- **Phase 5: AI学习** - 持续学习和反馈改进
- **实时监控** - 性能指标和质量监控
- **自动调优** - 基于数据的智能决策

## 快速开始

### 安装

```bash
pip install lingflow
```

### 基础使用

```python
from lingflow import LingFlow

# 初始化系统
lf = LingFlow()

# 执行单个技能
result = lf.run_skill("code_review", {
    "file_path": "src/main.py",
    "focus_areas": ["security", "performance"]
})

# 执行工作流
result = lf.run_workflow_file("workflows/ci_cd.yaml")
```

## 文档导航

### 📘 [快速开始指南](quickstart.md)
5分钟上手LingFlow，了解基本概念和用法。

### 📚 [API 参考](api/lingflow.md)
完整的API文档，包含所有模块、类和方法的详细说明。

### 💡 [使用示例](examples/basic_usage.md)
实际应用场景的代码示例和最佳实践。

### 🎓 [深入指南](guides/architecture.md)
系统架构、高级特性和定制化指南。

## 系统架构

```
LingFlow
├── coordination/       # Agent协调系统
│   ├── Agent         # 智能Agent基类
│   ├── AgentCoordinator # 多Agent协调器
│   └── AgentRegistry   # Agent注册表
├── workflow/          # 工作流引擎
│   ├── WorkflowOrchestrator # 工作流编排器
│   └── cache/          # 执行缓存
├── context/           # 上下文管理
│   ├── ContextManager  # 上下文管理器
│   └── auto_resume/    # 自动恢复
├── compression/        # 智能压缩
│   └── SmartCompressor # Token压缩器
├── self_optimizer/     # 自优化系统
│   ├── phase4/         # 参数优化
│   └── phase5/         # AI学习
├── guardrail/          # 安全防护
├── requirements/       # 需求工程
└── monitoring/         # 监控系统
```

## 核心概念

### Agent（智能体）
Agent是LingFlow的基本执行单元，每个Agent具有：
- **技能（Skills）** - 可执行的专业任务
- **状态（State）** - 上下文和配置
- **通信（Communication）** - 与其他Agent协作

### 工作流（Workflow）
工作流定义了任务的执行流程：
```yaml
name: "代码审查工作流"
tasks:
  - name: "静态分析"
    agent: "code_reviewer"
    skill: "static_analysis"
  - name: "安全扫描"
    agent: "security_agent"
    skill: "security_scan"
    depends_on: ["静态分析"]
```

### 自优化（Self-Optimization）
LingFlow能够自我优化和进化：
- **参数调优** - 自动优化系统参数
- **学习改进** - 基于反馈持续学习
- **性能监控** - 实时跟踪关键指标

## 版本信息

当前版本: **v3.8.0**

更新日志请查看 [GitHub Releases](https://github.com/guangda88/LingFlow/releases)

## 社区

- **GitHub**: [guangda88/LingFlow](https://github.com/guangda88/LingFlow)
- **问题反馈**: [Issues](https://github.com/guangda88/LingFlow/issues)
- **贡献指南**: [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

**众智混元，万法灵通** - LingFlow让软件工程更智能、更高效。
