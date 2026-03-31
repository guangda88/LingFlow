# LingFlow CLI 快速参考

常用命令速查表

## 命令树

```
lingflow
├── run                 # 执行单个技能
├── workflow            # 执行工作流文件
├── list-skills         # 列出所有技能
├── optimize            # 自优化系统
│   ├── run            # 运行优化
│   ├── status         # 查看状态
│   ├── wait           # 等待完成
│   ├── cancel         # 取消优化
│   ├── apply          # 应用优化
│   ├── generate-config # 生成配置
│   └── check          # 检查触发条件
├── learn               # AI工具学习 (Phase 5)
│   ├── run-learn      # 运行学习
│   ├── list-rules     # 列出规则
│   └── list-patterns  # 列出模式
├── analyze             # 代码分析
│   ├── run-analyze    # 运行分析
│   ├── complexity     # 复杂度分析
│   └── duplication    # 重复分析
├── test                # 测试系统
│   ├── run-test       # 运行测试
│   └── e2e            # E2E测试
└── feedback            # 反馈管理
    ├── submit         # 提交反馈
    ├── bug            # 快速报Bug
    ├── list           # 列出反馈
    ├── show           # 显示详情
    ├── resolve        # 解决反馈
    ├── export         # 导出报告
    └── stats          # 统计信息
```

## 常用命令

### 优化

```bash
# 快速优化
lingflow optimize run structure --target ./src

# 后台优化
lingflow optimize run structure --target ./src --async

# 查看进度
lingflow optimize status

# 等待完成
lingflow optimize wait
```

### 学习

```bash
# 自动学习
lingflow learn run-learn --target ./src

# 指定工具
lingflow learn run-learn --tools semgrep,ruff --target ./src

# 查看规则
lingflow learn list-rules --category security
```

### 分析

```bash
# 全面分析
lingflow analyze run-analyze --target ./src

# 特定指标
lingflow analyze run-analyze --target ./src --metrics complexity,duplication

# 复杂度分析
lingflow analyze complexity --target ./src
```

### 测试

```bash
# 运行测试
lingflow test run-test

# 覆盖率
lingflow test run-test --coverage

# 并行运行
lingflow test run-test --parallel
```

## 快速工作流

### 代码质量提升

```bash
# 1. 分析
lingflow analyze run-analyze --target ./src

# 2. 优化
lingflow optimize run structure --target ./src

# 3. 学习
lingflow learn run-learn --tools semgrep,ruff --target ./src

# 4. 测试
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

### 性能优化

```bash
# 1. 性能优化
lingflow optimize run performance --target ./src

# 2. 应用优化
lingflow optimize apply --report perf_report.md
```

## 选项速查

### 全局选项

- `--help, -h`: 显示帮助
- `--verbose, -v`: 详细输出
- `--target, -t`: 目标路径

### 优化选项

- `--async`: 后台运行
- `--experiments, -e`: 实验次数
- `--report, -r`: 报告路径
- `--timeout`: 超时时间

### 学习选项

- `--tools`: 工具列表
- `--apply`: 自动应用
- `--rules-only`: 仅规则
- `--output, -o`: 输出路径

### 分析选项

- `--metrics`: 指标列表
- `--format, -f`: 输出格式
- `--threshold`: 阈值

### 测试选项

- `--coverage`: 覆盖率
- `--parallel`: 并行运行

## 工具列表

- `semgrep`: 语义分析
- `ruff`: 快速检查
- `pylint`: 代码质量
- `bandit`: 安全检查
- `mypy`: 类型检查

## 指标列表

- `complexity`: 复杂度
- `duplication`: 重复度
- `security`: 安全性
- `maintainability`: 可维护性

## 输出格式

- `json`: JSON格式
- `markdown`: Markdown格式
- `html`: HTML格式

## 报告位置

默认报告保存在: `<project>/.lingflow/reports/`

## 配置文件

全局配置: `~/.lingflow/config.yaml`
项目配置: `<project>/.lingflow/config.yaml`

## 日志位置

日志文件: `~/.lingflow/logs/latest.log`

## 调试

```bash
# 启用调试
export LINGFLOW_DEBUG=1

# 详细输出
lingflow <command> --verbose
```

## 获取帮助

```bash
# 全局帮助
lingflow --help

# 命令帮助
lingflow optimize --help

# 子命令帮助
lingflow optimize run --help
```

## 常见组合

### 全面检查

```bash
lingflow analyze run-analyze --metrics all && \
lingflow optimize check && \
lingflow learn run-learn --tools all
```

### 快速修复

```bash
lingflow learn run-learn --tools ruff --apply && \
lingflow test run-test
```

### 深度优化

```bash
lingflow optimize run structure --experiments 100 && \
lingflow optimize run performance --experiments 100
```

---

**众智混元，万法灵通** 🚀
