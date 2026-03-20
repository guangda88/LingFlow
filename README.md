# LingFlow

LingFlow 是一个强大的工作流执行系统，支持多智能体协调、上下文压缩和代码优化等功能。

## 功能特性

- **工作流编排**：支持基于 YAML/JSON 的工作流定义，包括任务依赖、条件分支和循环执行
- **技能系统**：可扩展的技能系统，支持各种任务的执行
- **多智能体协调**：支持多个智能体的并行执行和协调
- **上下文压缩**：智能压缩上下文，节省 Token 消耗
- **代码优化**：支持代码分析、优化和重构
- **命令行界面**：提供简单易用的命令行工具

## 安装

### 从源码安装

1. 克隆代码库：
   ```bash
   git clone https://zhinenggitea.iepose.cn/guangda/LingFlow.git
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
# 执行代码分析技能
lingflow run code-analysis --params '{"target": "./lingflow/", "metrics": ["complexity", "duplication", "dead_code"]}'

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
- **code-review**：审查代码质量和安全性

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
│   └── __init__.py        # 统一入口
├── skills/                # 技能目录
│   ├── code-analysis/     # 代码分析技能
│   ├── code-optimizer/    # 代码优化器技能
│   ├── code-refactor/     # 代码重构器技能
│   ├── test-runner/       # 测试运行器技能
│   ├── code-review/       # 代码审查技能
│   └── notification/      # 通知技能
├── workflows/             # 工作流配置
│   └── self_optimize.yaml # 自优化工作流
├── cli.py                 # 命令行工具
├── setup.py               # 安装配置
├── requirements.txt       # 依赖列表
└── README.md              # 项目文档
```

## 版本历史

- **3.2.0**：实现自优化工作流，支持代码分析、优化和重构
- **3.1.0**：添加命令行界面和工作流编排功能
- **3.0.0**：重构项目结构，实现模块化设计

## 贡献

欢迎贡献代码和提出建议！请通过以下方式参与：

1. 提交 Issue 报告问题或建议
2. 提交 Pull Request 贡献代码
3. 参与讨论和文档改进

## 许可证

本项目采用 MIT 许可证。
