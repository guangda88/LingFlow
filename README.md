# LingFlow

[![version](https://img.shields.io/badge/version-3.5.0-blue)](https://github.com/guangda88/LingFlow)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

LingFlow 是一个强大的工作流执行系统，支持多智能体协调、上下文压缩和代码优化等功能。

## 功能特性

- **工作流编排**：支持基于 YAML/JSON 的工作流定义，包括任务依赖、条件分支和循环执行
- **技能系统**：可扩展的技能系统，支持各种任务的执行
- **多智能体协调**：支持多个智能体的并行执行和协调
- **上下文压缩**：智能压缩上下文，节省 Token 消耗
- **代码优化**：支持代码分析、优化和重构
- **性能监控**：内置性能监控和缓存系统，支持执行时间追踪和瓶颈分析
- **安全框架**：宪法级别保护和合规性检查
- **代码审查**：8 维度代码审查框架（质量、架构、性能、安全、可维护性等）
- **测试框架**：完整的单元测试、集成测试和 E2E 测试支持
- **命令行界面**：提供简单易用的命令行工具

## 仓库地址

- **GitHub**: https://github.com/guangda88/LingFlow
- **Gitea**: http://zhinenggitea.iepose.cn/guangda/LingFlow

## 安装

### 从源码安装

1. 克隆代码库：
   ```bash
   # GitHub
   git clone https://github.com/guangda88/LingFlow.git
   cd LingFlow

   # 或 Gitea
   git clone http://zhinenggitea.iepose.cn/guangda/LingFlow.git
   cd LingFlow
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 安装 LingFlow：
   ```bash
   pip install -e .
   ```

## 使用方法

### 执行单个技能

```bash
# 执行代码审查技能
lingflow run code-review --params '{"target": "./skills/"}'

# 执行通知技能
lingflow run notification --params '{"message": "测试通知", "level": "info"}'
```

### 执行工作流

```bash
# 执行自优化工作流
lingflow workflow workflows/self_optimize.yaml

# 执行其他工作流
lingflow workflow path/to/workflow.yaml
```

### 列出可用技能

```bash
lingflow list-skills
```

### 性能监控

查看性能统计信息：

```bash
# 查看所有函数的执行时间统计
python -c "from lingflow.utils.performance import performance_monitor; print(performance_monitor.get_all_stats())"

# 查看缓存命中率
python -c "from lingflow.utils.performance import get_cache_stats; print(get_cache_stats())"
```

## 性能监控

LingFlow v3.5.0 引入了完整的性能监控和缓存系统：

### 性能追踪

使用装饰器追踪函数执行时间：

```python
from lingflow.utils.performance import track_performance

@track_performance()
def your_function():
    # 你的代码
    pass
```

### 缓存优化

使用带监控的LRU缓存：

```python
from lingflow.utils.performance import cached_with_monitor

@cached_with_monitor(maxsize=128)
def expensive_function(param):
    # 昂贵的计算
    return result
```

## 自优化工作流

LingFlow 提供了一个自优化工作流，可以自动分析、优化和验证自己的代码：

1. **代码分析**：分析代码的复杂度、重复率和死代码
2. **问题识别**：识别代码中的问题
3. **生成优化方案**：基于分析结果生成优化方案
4. **执行优化**：执行代码重构
5. **验证结果**：运行测试验证优化效果
6. **生成报告**：生成优化报告

## 技能列表

### 核心技能

- **workflow-executor**：执行 YAML/JSON 定义的工作流
- **task-runner**：执行单个任务（技能调用）
- **conditional-branch**：工作流中的条件判断
- **loop-iterator**：工作流中的循环执行
- **error-handler**：任务失败时的重试和降级

### 代码优化技能

- **code-analysis**：分析代码的复杂度、重复率和死代码
- **code-optimizer**：基于分析结果生成优化方案
- **code-refactor**：执行代码重构操作
- **test-runner**：运行测试并返回结果
- **code-review**：8 维度代码审查（质量、架构、性能、安全、可维护性、最佳实践、一致性、Bug分析）

### 支持性技能

- **notification**：发送各种类型的通知
- **skill-creator**：创建新的技能

## 工作流配置示例

### 自优化工作流

```yaml
name: LingFlow 自我优化
description: 用 LingFlow 分析并优化自己的代码

tasks:
  # 阶段1：代码分析
  - id: analyze_codebase
    skill: code-analysis
    params:
      target: ./lingflow/
      metrics:
        - complexity
        - duplication
        - dead_code

  # 阶段2：识别问题
  - id: identify_issues
    skill: conditional-branch
    params:
      condition: "{{tasks.analyze_codebase.output.duplication_rate}} > 0.1"
      branches:
        true:
          - id: flag_duplication
            skill: code-review
            params:
              focus: "duplicate_code"
              files: "{{tasks.analyze_codebase.output.duplicate_files}}"
        false:
          - id: skip_duplication
            skill: notification
            params:
              message: "无重复代码问题"

  # 阶段3：生成优化方案
  - id: generate_optimization
    skill: task-runner
    params:
      skill: code-optimizer
      params:
        issues: "{{tasks.identify_issues.output}}"
        strategy: "refactor_duplicates"
    depends_on: [identify_issues]

  # 阶段4：执行优化（需要确认）
  - id: apply_optimizations
    skill: conditional-branch
    params:
      condition: "{{tasks.generate_optimization.output.is_safe}}"
      branches:
        true:
          - id: execute_refactor
            skill: code-refactor
            params:
              changes: "{{tasks.generate_optimization.output.changes}}"
              backup: true
        false:
          - id: report_unsafe
            skill: notification
            params:
              message: "优化方案不安全，需要人工审查"
    depends_on: [generate_optimization]

  # 阶段5：验证优化结果
  - id: verify_optimization
    skill: loop-iterator
    params:
      items: "{{tasks.apply_optimizations.output.modified_files}}"
      task:
        skill: test-runner
        params:
          file: "{{item}}"
          test_type: unit
    depends_on: [apply_optimizations]

  # 阶段6：生成报告
  - id: generate_report
    skill: report-generator
    params:
      data:
        before: "{{tasks.analyze_codebase.output}}"
        after: "{{tasks.verify_optimization.output}}"
        changes: "{{tasks.apply_optimizations.output.changes}}"
      format: markdown
    depends_on: [verify_optimization]
```

## 项目结构

```
LingFlow/
├── lingflow/              # 核心代码
│   ├── common/            # 公共模块
│   ├── compression/       # 上下文压缩
│   ├── coordination/      # 多智能体协调
│   ├── workflow/          # 工作流编排
│   ├── core/              # 核心功能（宪法、合规矩阵）
│   ├── guardrail/         # 安全框架
│   ├── code_review/       # 代码审查模块
│   ├── testing/           # 测试框架
│   └── utils/             # 工具模块（性能监控、错误处理）
├── skills/                # 技能目录
│   ├── code-analysis/     # 代码分析技能
│   ├── code-optimizer/    # 代码优化器技能
│   ├── code-refactor/     # 代码重构器技能
│   ├── code-review/       # 代码审查技能
│   ├── code-review-js/    # JavaScript 代码审查技能
│   └── notification/      # 通知技能
├── workflows/             # 工作流配置
│   └── self_optimize.yaml # 自优化工作流
├── tests/                 # 测试目录
│   ├── test_*.py          # 单元测试
│   ├── test_code_review/  # 代码审查测试
│   └── test_compliance_matrix.py
├── docs/                  # 文档目录
├── cli.py                 # 命令行工具
├── setup.py               # 安装配置
├── requirements.txt       # 依赖列表
├── VERSION                # 版本号
├── CHANGELOG.md           # 变更日志
└── README.md              # 项目文档
```

## 版本历史

### 3.5.0 (2026-03-25)

- 添加版本管理（VERSION 文件、`__version__` 导出）
- 新增完整测试框架（单元测试、集成测试、E2E 测试）
- 新增代码审查模块（8 维度审查框架）
- 新增安全分析和审计日志模块
- 新增沙箱执行环境
- 优化项目结构和代码质量
- 更新文档和开发规则

### 3.3.0 (2026-03-22)

- 实现真实工作流执行逻辑（替换模拟数据）
- 统一日志系统（替换13个print语句）
- 添加性能监控模块，支持装饰器追踪
- 添加LRU缓存，支持命中率统计
- 消除魔法值，添加常量定义
- 添加宪法级别保护和合规性检查
- 完善文档和用户指南

### 3.2.0

- 实现自优化工作流，支持代码分析、优化和重构

### 3.1.0

- 添加命令行界面和工作流编排功能

### 3.0.0

- 重构项目结构，实现模块化设计

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_code_review/

# 生成覆盖率报告
pytest --cov=lingflow --cov-report=html
```

### 代码审查

```bash
# 运行代码审查
python -m lingflow.code_review.core.base_reviewer
```

## 贡献

欢迎贡献代码和提出建议！请通过以下方式参与：

1. 提交 Issue 报告问题或建议
2. 提交 Pull Request 贡献代码
3. 参与讨论和文档改进

### 开发规则

请参阅 [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) 了解详细的开发规范。

## 许可证

本项目采用 MIT 许可证。
