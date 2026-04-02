# LingFlow 自优化系统 - 快速使用指南

## 5分钟上手

### 1️⃣ 检查是否需要优化

```bash
$ lingflow optimize check --target ./your-project

✓ 需要优化
  原因: 代码审查得分 (65) 低于阈值 (70)
  优先级: medium
```

### 2️⃣ 运行优化

```bash
# 同步模式（等待完成）
$ lingflow optimize structure --target ./your-project

# 异步模式（后台运行）
$ lingflow optimize structure --async --target ./your-project
```

### 3️⃣ 查看结果

```bash
# 查看报告
$ cat LINGFLOW_OPTIMIZATION_REPORT_*.md

# 应用优化建议
$ lingflow optimize apply --report LINGFLOW_OPTIMIZATION_REPORT_*.md
```

---

## 常用命令

```bash
# 运行不同类型的优化
lingflow optimize structure    # 结构优化
lingflow optimize performance  # 性能优化
lingflow optimize simplicity   # 简洁优化

# 异步优化
lingflow optimize structure --async
lingflow optimize status       # 查看进度
lingflow optimize wait         # 等待完成
lingflow optimize cancel       # 取消优化

# 处理报告
lingflow optimize apply -r REPORT.md              # 自动应用
lingflow optimize generate-config -r REPORT.md   # 生成配置文件

# 检查和诊断
lingflow optimize check        # 检查是否需要优化
```

---

## 钩子自动触发

```python
from lingflow.hooks import get_global_hook

hook = get_global_hook()

# 代码审查后自动检查
review_result = {"overall_score": 65}
hook.on_code_review_complete(review_result)

# 如果满足条件，会提示是否启动优化
```

---

## 配置优化阈值

编辑 `~/.lingflow/config.yaml`:

```yaml
# 自优化配置
triggers:
  quality:
    review_score_below: 70  # 审查得分阈值
  structure:
    complexity_above: 15     # 复杂度阈值

optimization:
  max_experiments: 20       # 最大实验次数
  time_budget: 300          # 时间预算（秒）

hooks:
  enable_on_review: true    # 审查后启用
  enable_on_test: true      # 测试后启用
  require_confirmation: true # 需要用户确认
```

---

## 优化目标对比

| 目标 | 优化内容 | 适用场景 |
|------|---------|---------|
| **structure** | 类大小、复杂度、方法数 | 代码结构问题多 |
| **performance** | 缓存、并行、超时 | 性能瓶颈 |
| **simplicity** | 重复率、行长度、复杂度 | 代码冗余 |

---

## 实际案例

### 案例1: 降低代码复杂度

```bash
$ lingflow optimize structure --experiments 30

✓ 实验次数: 30
✓ 优化耗时: 65秒

🎯 最佳参数:
  max_class_size: 200
  max_complexity: 10

📈 预期改进:
  结构违规: 15 → 6 (60%改进)
  平均复杂度: 14.5 → 9.8
```

### 案例2: 异步优化

```bash
# 启动优化
$ lingflow optimize structure --async

✓ 优化已启动（后台运行）

# 继续其他工作...
$ git commit -m "refactor: cleanup"

# 稍后查看结果
$ lingflow optimize wait

✓ 优化完成
```

---

## 故障排除

### Q: 提示"没有运行中的优化"
A: 异步优化已完成或未启动，使用 `lingflow optimize structure` 运行同步模式。

### Q: 优化时间过长
A: 减少实验次数: `lingflow optimize structure --experiments 10`

### Q: 找不到LingMinOpt
A: 系统会自动降级到简单搜索，或安装: `pip install lingminopt`

### Q: 报告太长
A: 使用 `less` 查看: `less LINGFLOW_OPTIMIZATION_REPORT_*.md`

---

## 下一步

- 阅读完整报告: `cat SELFOPTIMIZATION_PHASE1_IMPLEMENTATION_REPORT.md`
- 查看测试: `pytest tests/test_self_optimizer/ -v`
- 自定义配置: `vi ~/.lingflow/config.yaml`

---

**LingFlow 自优化系统** - 让代码自动优化变得简单
