# LingFlow CLI 使用指南

众智混元，万法灵通

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [核心命令](#核心命令)
- [自优化系统](#自优化系统)
- [AI工具学习](#ai工具学习-phase-5)
- [代码分析](#代码分析)
- [测试系统](#测试系统)
- [反馈管理](#反馈管理)
- [最佳实践](#最佳实践)
- [故障排除](#故障排除)

---

## 安装

确保已安装 LingFlow:

```bash
pip install -e .
```

验证安装:

```bash
lingflow --help
```

---

## 快速开始

### 1. 参数优化

优化项目结构参数:

```bash
lingflow optimize run structure --target ./my_project
```

### 2. AI工具学习

从 Semgrep 和 Ruff 学习规则:

```bash
lingflow learn run-learn --tools semgrep,ruff --target ./my_project
```

### 3. 代码分析

分析代码复杂度和重复度:

```bash
lingflow analyze run-analyze --target ./my_project --metrics complexity,duplication
```

### 4. 运行测试

运行测试套件并生成覆盖率报告:

```bash
lingflow test run-test --coverage
```

---

## 核心命令

### 执行技能

```bash
# 执行单个技能
lingflow run <skill_name> --params '{"key": "value"}'

# 示例: 执行代码审查
lingflow run code_review --params '{"target": "./src", "strict": true}'
```

### 工作流

```bash
# 执行工作流文件
lingflow workflow ./workflows/my_workflow.yaml
```

### 列出技能

```bash
# 查看所有可用技能
lingflow list-skills
```

---

## 自优化系统

### 运行优化

```bash
# 结构优化
lingflow optimize run structure --target ./my_project

# 性能优化
lingflow optimize run performance --target ./my_project

# 简洁性优化
lingflow optimize run simplicity --target ./my_project
```

**选项:**

- `--target, -t`: 目标路径 (默认: 当前目录)
- `--async`: 异步执行（后台运行）
- `--experiments, -e`: 最大实验次数 (默认: 20)
- `--report, -r`: 保存报告到文件

**示例:**

```bash
# 后台运行优化
lingflow optimize run structure --target ./src --async

# 指定实验次数并保存报告
lingflow optimize run structure --target ./src --experiments 50 --report opt_report.md
```

### 查看优化状态

```bash
# 查看运行中的优化
lingflow optimize status

# 等待优化完成
lingflow optimize wait --timeout 600

# 取消优化
lingflow optimize cancel
```

### 应用优化结果

```bash
# 从报告生成配置文件
lingflow optimize generate-config --report opt_report.md --output config.yaml

# 应用优化建议（修改配置）
lingflow optimize apply --report opt_report.md
```

### 检查优化触发条件

```bash
# 检查当前项目是否需要优化
lingflow optimize check --target ./src
```

---

## AI工具学习 (Phase 5)

### 运行学习

```bash
# 自动检测可用工具并学习
lingflow learn run-learn --target ./my_project

# 指定工具
lingflow learn run-learn --tools semgrep,ruff --target ./my_project

# 自动应用学习到的改进
lingflow learn run-learn --tools semgrep --target ./my_project --apply

# 仅提取规则
lingflow learn run-learn --tools semgrep --target ./my_project --rules-only
```

**选项:**

- `--tools, -t`: 工具列表 (逗号分隔)
  - 可用工具: `semgrep`, `ruff`, `pylint`, `bandit`, `mypy`
- `--target`: 目标路径 (默认: 当前目录)
- `--output, -o`: 输出报告路径
- `--apply`: 自动应用学习到的改进
- `--rules-only`: 仅提取规则，不运行模式检测
- `--verbose, -v`: 详细输出

**示例:**

```bash
# 学习并保存报告
lingflow learn run-learn \
  --tools semgrep,ruff,pylint \
  --target ./src \
  --output learning_report.md

# 详细输出模式
lingflow learn run-learn \
  --tools semgrep \
  --target ./src \
  --verbose
```

### 查看学习结果

```bash
# 列出所有学习到的规则
lingflow learn list-rules

# 按类别过滤
lingflow learn list-rules --category security

# 按严重性过滤
lingflow learn list-rules --severity high

# 限制返回数量
lingflow learn list-rules --limit 20
```

### 查看识别的模式

```bash
# 列出所有模式
lingflow learn list-patterns

# 按类型过滤
lingflow learn list-patterns --type long_method

# 限制返回数量
lingflow learn list-patterns --limit 20
```

---

## 代码分析

### 运行分析

```bash
# 分析所有指标
lingflow analyze run-analyze --target ./my_project

# 分析特定指标
lingflow analyze run-analyze \
  --target ./my_project \
  --metrics complexity,duplication,security

# 生成JSON格式报告
lingflow analyze run-analyze \
  --target ./my_project \
  --format json \
  --output analysis.json

# 生成HTML报告
lingflow analyze run-analyze \
  --target ./my_project \
  --format html \
  --output report.html
```

**选项:**

- `--target, -t`: 目标路径 (默认: 当前目录)
- `--metrics, -m`: 指标列表 (逗号分隔)
  - 可用指标: `complexity`, `duplication`, `security`, `maintainability`
- `--output, -o`: 输出报告路径
- `--format, -f`: 输出格式 (默认: markdown)
  - 可用格式: `json`, `markdown`, `html`
- `--verbose, -v`: 详细输出

### 复杂度分析

```bash
# 分析代码复杂度
lingflow analyze complexity --target ./src

# 设置自定义阈值
lingflow analyze complexity --target ./src --threshold 15
```

### 重复代码分析

```bash
# 分析代码重复
lingflow analyze duplication --target ./src

# 设置最小重复行数
lingflow analyze duplication --target ./src --min-lines 15
```

---

## 测试系统

### 运行测试

```bash
# 运行所有测试
lingflow test run-test

# 运行测试并生成覆盖率报告
lingflow test run-test --coverage

# 详细输出
lingflow test run-test --verbose

# 并行运行测试
lingflow test run-test --parallel

# 运行特定测试
lingflow test run-test --target tests/test_phase4.py
```

**选项:**

- `--coverage`: 生成覆盖率报告
- `--verbose, -v`: 详细输出
- `--parallel`: 并行运行测试
- `--target`: 目标测试路径

### E2E测试

```bash
# 运行所有E2E测试
lingflow test e2e

# 运行特定场景
lingflow test e2e --scenario optimization_flow

# 详细输出
lingflow test e2e --verbose
```

---

## 反馈管理

### 提交反馈

```bash
# 提交一般反馈
lingflow feedback submit \
  --title "标题" \
  --description "详细描述" \
  --category bug \
  --severity high

# 快速提交Bug报告
lingflow feedback bug \
  --title "Bug标题" \
  --description "Bug描述" \
  --severity critical
```

**类别选项:**
- `bug`: Bug报告
- `feature`: 功能请求
- `improvement`: 改进建议
- `performance`: 性能问题
- `documentation`: 文档问题
- `usability`: 可用性问题
- `other`: 其他

**严重性选项:**
- `low`: 低
- `medium`: 中
- `high`: 高
- `critical`: 严重

### 查看反馈

```bash
# 列出所有反馈
lingflow feedback list

# 按类别过滤
lingflow feedback list --category bug

# 按状态过滤
lingflow feedback list --status open

# 限制返回数量
lingflow feedback list --limit 50
```

### 反馈详情

```bash
# 查看反馈详情
lingflow feedback show <feedback_id>
```

### 解决反馈

```bash
# 标记反馈为已解决
lingflow feedback resolve <feedback_id> --resolution "解决方案说明"
```

### 导出报告

```bash
# 导出反馈报告
lingflow feedback export --output feedback_report.md
```

### 查看统计

```bash
# 显示反馈统计信息
lingflow feedback stats
```

---

## 最佳实践

### 1. 开发工作流

```bash
# 1. 分析当前代码
lingflow analyze run-analyze --target ./src --metrics complexity,duplication

# 2. 运行优化
lingflow optimize run structure --target ./src

# 3. 从AI工具学习
lingflow learn run-learn --tools semgrep,ruff --target ./src

# 4. 应用改进
lingflow learn run-learn --tools semgrep --target ./src --apply

# 5. 运行测试
lingflow test run-test --coverage

# 6. 检查是否需要再次优化
lingflow optimize check --target ./src
```

### 2. CI/CD集成

```yaml
# .github/workflows/lingflow.yml
name: LingFlow Analysis

on: [push, pull_request]

jobs:
  analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install LingFlow
        run: pip install -e .

      - name: Run Analysis
        run: |
          lingflow analyze run-analyze \
            --target ./src \
            --metrics complexity,duplication,security \
            --format json \
            --output analysis.json

      - name: Run Tests
        run: |
          lingflow test run-test --coverage

      - name: Learn from Tools
        run: |
          lingflow learn run-learn \
            --tools semgrep,ruff \
            --target ./src \
            --output learning_report.md
```

### 3. 定期维护

```bash
# 每周运行一次全面检查
lingflow analyze run-analyze --target ./src --metrics all
lingflow optimize check --target ./src
lingflow learn run-learn --target ./src

# 每月运行一次深度优化
lingflow optimize run structure --target ./src --experiments 100
lingflow learn run-learn --tools all --target ./src
```

### 4. 性能优化

```bash
# 1. 性能分析
lingflow optimize run performance --target ./src

# 2. 敏感性分析
lingflow optimize sensitivity --target ./src

# 3. 应用最佳参数
lingflow optimize apply --report performance_report.md
```

---

## 故障排除

### 常见问题

#### 1. 命令未找到

```bash
# 确保已正确安装
pip install -e .

# 或使用完整路径
python -m lingflow.cli <command>
```

#### 2. AI工具不可用

```bash
# 检查工具是否安装
which semgrep
which ruff

# 安装缺失的工具
pip install semgrep ruff pylint bandit mypy

# 或手动指定可用工具
lingflow learn run-learn --tools ruff --target ./src
```

#### 3. 优化失败

```bash
# 查看详细错误
lingflow optimize run structure --target ./src --verbose

# 检查是否有运行中的优化
lingflow optimize status

# 取消卡住的优化
lingflow optimize cancel
```

#### 4. 测试失败

```bash
# 运行特定测试查看详细输出
lingflow test run-test --target tests/test_specific.py --verbose

# 检查测试覆盖率
lingflow test run-test --coverage
```

### 调试模式

```bash
# 启用详细输出
export LINGFLOW_DEBUG=1
lingflow <command> --verbose
```

### 日志文件

日志位置: `~/.lingflow/logs/`

```bash
# 查看最新日志
tail -f ~/.lingflow/logs/latest.log
```

---

## 高级用法

### 批处理模式

```bash
# 创建批处理脚本
#!/bin/bash
for project in project1 project2 project3; do
  lingflow analyze run-analyze --target ./$project
  lingflow optimize run structure --target ./$project
  lingflow learn run-learn --target ./$project
done
```

### 并行优化

```bash
# 后台运行多个优化任务
lingflow optimize run structure --target ./src1 --async
lingflow optimize run structure --target ./src2 --async

# 查看所有任务状态
lingflow optimize status
```

### 自定义配置

创建 `~/.lingflow/config.yaml`:

```yaml
optimization:
  max_experiments: 100
  timeout: 600

learning:
  min_frequency: 3
  min_confidence: 0.7
  max_rules: 1000

analysis:
  default_metrics:
    - complexity
    - duplication
    - security
```

---

## 更多资源

- [GitHub仓库](https://github.com/guangda88/LingFlow)
- [API文档](./API_REFERENCE.md)
- [架构文档](./ARCHITECTURE.md)
- [Phase 4文档](./phase4-implementation.md)
- [Phase 5文档](./phase5-design.md)

---

## 更新日志

### v3.6.0 (2026-03-31)

- 新增 `lingflow learn` 命令组 (Phase 5)
- 新增 `lingflow analyze` 命令组
- 新增 `lingflow test` 命令组
- 改进 `lingflow optimize` 命令组
- 完善错误处理和用户反馈

---

**众智混元，万法灵通** 🚀
