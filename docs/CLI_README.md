# LingFlow CLI 使用指南

## 快速开始

```bash
# 安装
pip install -e .

# 查看帮助
lingflow --help

# 分析代码
lingflow analyze run-analyze --target ./my_project

# 优化参数
lingflow optimize run structure --target ./my_project

# 从AI工具学习
lingflow learn run-learn --tools semgrep,ruff --target ./my_project

# 运行测试
lingflow test run-test --coverage
```

## 主要命令

### 1. 代码分析 (`lingflow analyze`)

```bash
# 全面分析
lingflow analyze run-analyze --target ./src

# 特定指标
lingflow analyze run-analyze --target ./src --metrics complexity,duplication

# 生成报告
lingflow analyze run-analyze --target ./src --format json --output report.json
```

### 2. 参数优化 (`lingflow optimize`)

```bash
# 运行优化
lingflow optimize run structure --target ./src

# 后台运行
lingflow optimize run structure --target ./src --async

# 查看状态
lingflow optimize status

# 等待完成
lingflow optimize wait
```

### 3. AI工具学习 (`lingflow learn`)

```bash
# 自动学习
lingflow learn run-learn --target ./src

# 指定工具
lingflow learn run-learn --tools semgrep,ruff --target ./src

# 查看规则
lingflow learn list-rules
```

### 4. 测试 (`lingflow test`)

```bash
# 运行测试
lingflow test run-test

# 覆盖率
lingflow test run-test --coverage

# 并行运行
lingflow test run-test --parallel
```

## 工作流示例

### 代码质量提升

```bash
# 1. 分析当前状态
lingflow analyze run-analyze --target ./src

# 2. 优化参数
lingflow optimize run structure --target ./src

# 3. 从工具学习
lingflow learn run-learn --tools semgrep,ruff --target ./src

# 4. 运行测试
lingflow test run-test --coverage
```

### 安全检查

```bash
# 1. 安全分析
lingflow analyze run-analyze --target ./src --metrics security

# 2. 安全工具学习
lingflow learn run-learn --tools semgrep,bandit --target ./src

# 3. 查看安全规则
lingflow learn list-rules --category security
```

## 支持的工具

- **semgrep**: 语义分析
- **ruff**: 快速检查
- **pylint**: 代码质量
- **bandit**: 安全检查
- **mypy**: 类型检查

## 更多信息

- [完整指南](./CLI_GUIDE.md)
- [快速参考](./CLI_EXAMPLES.md)
- [实现总结](./CLI_IMPLEMENTATION_SUMMARY.md)

## 问题反馈

```bash
# 提交Bug
lingflow feedback bug --title "问题标题" --description "详细描述"

# 查看反馈
lingflow feedback list
```

---

**众智混元，万法灵通** 🚀
