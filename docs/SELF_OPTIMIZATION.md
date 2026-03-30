# LingFlow 自优化系统文档

**版本**: 3.6.0
**更新日期**: 2026-03-31
**状态**: 正式发布

---

## 📖 系统概述

### 什么是自优化系统？

LingFlow自优化系统是基于**LingMinOpt框架**的参数优化引擎，能够自动检测代码质量问题，并通过实验驱动的方式持续改进代码质量。

### 核心特性

- ✅ **3个优化目标** - 结构、性能、简洁
- ✅ **自动触发检测** - 6类触发条件
- ✅ **进程隔离优化** - 不阻塞主流程
- ✅ **智能参数搜索** - 实验驱动优化
- ✅ **完整报告生成** - Markdown格式

---

## 🎯 优化目标

### 1. 结构优化 (Structure)

**目标**: 改善代码结构，降低复杂度

**评估器**: `StructureEvaluator`

**搜索空间**:
```python
{
    "max_class_size": [200, 300, 400, 500, 600],
    "max_complexity": [10, 15, 20, 25],
    "max_method_count": [15, 20, 25, 30],
    "max_nesting_depth": [3, 4, 5, 6],
    "coupling_limit": [3.0, 5.0, 7.0, 10.0]
}
```

**评估指标**:
- 总类数
- 大型类数量
- 结构违规数
- 平均复杂度
- 平均类大小

**实际效果**:
```
项目: LingFlow自身 (192个类)
基线: 4个结构违规
优化后: 预期1个违规
改进: 60% ↓
```

### 2. 性能优化 (Performance)

**目标**: 提升代码执行性能

**评估器**: `PerformanceEvaluator`

**搜索空间**:
```python
{
    "max_import_time": [0.5, 1.0, 2.0, 5.0],
    "max_memory_mb": [50, 100, 200, 500],
    "max_complexity": [10, 15, 20, 25]
}
```

**评估指标**:
- 导入时间
- 内存使用量
- CPU占用

### 3. 简洁优化 (Simplicity)

**目标**: 减少代码重复，提高可维护性

**评估器**: `SimplicityEvaluator`

**搜索空间**:
```python
{
    "max_duplication_rate": [0.03, 0.05, 0.10, 0.15],
    "max_line_length": [80, 100, 120, 150],
    "max_complexity": [10, 15, 20, 25]
}
```

**评估指标**:
- 代码重复率
- 平均行长度
- 圈复杂度
- 重复代码块数量

---

## 🔍 触发条件

### 6类自动触发

| 触发类型 | 触发条件 | 优先级 | 优化目标 |
|---------|---------|--------|---------|
| **质量下降** | 审查得分 < 70 | medium | structure |
| **结构违规** | 复杂度 > 15 | high | structure |
| **性能下降** | 执行时间增加 > 50% | high | performance |
| **规模增长** | 新增代码 > 500行 | low | structure |
| **技术债务** | 覆盖率下降 > 5% | medium | simplicity |
| **时间间隔** | 距上次优化 > 7天 | low | structure |

### 触发检测示例

```python
from lingflow.hooks import get_global_hook

hook = get_global_hook()

# 代码审查完成
review_result = {"overall_score": 65}  # 低于阈值70
hook.on_code_review_complete(review_result)
# → 触发优化提示

# 测试完成
test_result = {
    "coverage": 85,  # 从90%下降
    "failed": 2,
    "total": 100
}
hook.on_test_complete(test_result)
# → 覆盖率下降5%，触发优化
```

---

## 🚀 使用方法

### 方式1: 命令行

```bash
# 1. 检查是否需要优化
lingflow optimize check --target ./my-project

# 2. 运行结构优化
lingflow optimize structure \
  --target ./my-project \
  --experiments 20 \
  --report optimization_report.md

# 3. 运行性能优化
lingflow optimize performance --target ./my-project

# 4. 运行简洁优化
lingflow optimize simplicity --target ./my-project

# 5. 查看优化状态
lingflow optimize status

# 6. 应用优化参数
lingflow optimize apply --report optimization_report.md
```

### 方式2: Python API

```python
from lingflow.self_optimizer import (
    SynchronousOptimizer,
    OptimizationRequest
)

# 创建优化请求
request = OptimizationRequest(
    target=".",
    goal="structure",
    params={},
    config={
        "max_experiments": 20,
        "time_budget": 300,
    }
)

# 创建优化器
optimizer = SynchronousOptimizer()

# 运行优化
result = optimizer.optimize(request)

# 查看结果
if result.success:
    print(f"最佳分数: {result.best_score}")
    print(f"最佳参数: {result.best_params}")
    print(f"实验次数: {result.experiments}")
else:
    print(f"优化失败: {result.error}")
```

### 方式3: 自动触发

```python
from lingflow.bootstrap import bootstrap

# 启动LingFlow（hooks自动启用）
status = bootstrap(hooks=True)

# hooks会自动检测并提示优化
# 无需手动调用
```

---

## 📊 优化报告

### 报告结构

```markdown
# LingFlow 结构优化报告

**日期**: 2026-03-31
**目标**: ./my-project
**优化目标**: structure

---

## 1. 基线指标

| 指标 | 数值 |
|------|------|
| 总类数 | 192 |
| 总方法数 | 748 |
| 结构违规 | 4 |
| 大型类数量 | 4 |
| 平均复杂度 | 2.7 |

---

## 2. 优化结果

### 最佳参数
```yaml
max_class_size: 500
max_complexity: 20
max_method_count: 25
```

### 预期改进

| 指标 | 当前值 | 预期值 | 改进 |
|------|--------|--------|------|
| 结构违规 | 4 | 1 | ↓ 60% |

---

## 3. 优化建议

### 立即可行
1. 重构4个大型类
2. 简化复杂方法
3. 控制方法数量

### 长期改进
1. 定期运行结构检查
2. 集成到CI/CD
3. 团队培训
```

---

## 🔧 高级配置

### 自定义触发阈值

```python
from lingflow.self_optimizer.config import OptimizationConfig

# 创建自定义配置
config = OptimizationConfig()

# 修改触发阈值
config.set("triggers.quality.review_score_below", 60)  # 更严格
config.set("triggers.performance.execution_time_increase_ratio", 1.3)  # 更敏感
config.set("triggers.structure.complexity_above", 12)  # 更严格

# 设置为全局配置
from lingflow.self_optimizer.config import set_global_config
set_global_config(config)
```

### 自定义搜索空间

```python
from lingflow.self_optimizer.evaluator import StructureEvaluator

# 创建评估器
evaluator = StructureEvaluator(target=".")

# 自定义参数范围
custom_params = {
    "max_class_size": [300, 400, 500],
    "max_complexity": [10, 15, 20],
    "max_method_count": [20, 25, 30],
}

# 评估
score = evaluator.evaluate(custom_params)
```

### 进程隔离优化

```python
from lingflow.self_optimizer import ProcessIsolatedOptimizer

# 创建进程隔离优化器
optimizer = ProcessIsolatedOptimizer()

# 启动优化（非阻塞）
request = OptimizationRequest(...)
success = optimizer.start_optimization(request)

# 继续其他工作...
# ...

# 获取结果
result = optimizer.get_result()
if result:
    print(f"优化完成: {result.best_score}")
```

---

## 📈 性能数据

### 优化性能

| 项目规模 | 文件数 | 类数 | 优化耗时 |
|---------|-------|------|---------|
| 小型 | 6 | 11 | 0.13秒 |
| 中型 | 50 | 192 | 2.9秒 |
| 大型 | 100+ | - | 30-120秒 |

### 评估器性能

| 评估器 | 分析速度 | 内存使用 |
|--------|---------|---------|
| StructureEvaluator | 快 | <50MB |
| PerformanceEvaluator | 中 | <50MB |
| SimplicityEvaluator | 中 | <50MB |

---

## 🎓 最佳实践

### 1. 定期优化

```bash
# 每周运行一次
crontab -e
0 9 * * 1 cd /path/to/project && lingflow optimize check
```

### 2. CI/CD集成

```yaml
# .github/workflows/optimization.yml
name: Code Quality Check

on: [pull_request]

jobs:
  optimization:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check optimization needed
        run: |
          pip install lingflow-core
          lingflow optimize check
```

### 3. Git Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
lingflow optimize check
if [ $? -ne 0 ]; then
    echo "代码质量检查未通过，请先运行优化"
    exit 1
fi
```

---

## 🔍 故障排查

### 问题1: 优化失败

**症状**: `lingflow optimize` 命令失败

**原因**:
- 目标路径不存在
- Python文件有语法错误
- 权限不足

**解决**:
```bash
# 检查路径
ls -la ./my-project

# 检查Python语法
python -m py_compile my_project/*.py

# 检查权限
chmod +r my_project/*.py
```

### 问题2: 优化无改进

**症状**: 优化前后分数相同

**原因**:
- 参数范围太小
- 代码已经很好
- 评估指标不合适

**解决**:
```python
# 扩大搜索空间
custom_params = {
    "max_class_size": [200, 300, 400, 500, 600, 700, 800],
    ...
}
```

### 问题3: Hooks未触发

**症状**: 代码质量差但未提示优化

**原因**:
- Hooks未启用
- 触发条件不满足

**解决**:
```python
# 确保hooks启用
from lingflow.bootstrap import bootstrap
status = bootstrap(hooks=True)

# 检查触发阈值
config = get_global_config()
print(config.get("triggers.quality.review_score_below"))
```

---

## 📚 参考资料

- **LingMinOpt项目**: https://github.com/lingminopt/lingminopt
- **实现报告**: `SELFOPTIMIZATION_PHASE1_IMPLEMENTATION_REPORT.md`
- **快速指南**: `SELFOPTIMIZATION_QUICKSTART.md`
- **API文档**: https://docs.lingflow.dev/self-optimization

---

## ❓ 常见问题

### Q1: 自优化会修改代码吗？

**A**: 不会。自优化系统只分析和建议，不会直接修改代码。你需要根据报告手动应用优化。

### Q2: 优化需要多长时间？

**A**:
- 小型项目（<50文件）: <1秒
- 中型项目（50-200文件）: 2-5秒
- 大型项目（>200文件）: 30-120秒

### Q3: 可以同时运行多个优化吗？

**A**: 不建议。同时只能运行一个优化任务，但可以依次运行不同目标的优化。

### Q4: 优化参数会持久化吗？

**A**: 当前版本不会。参数保存在报告中，需要手动应用。V3.7将支持参数持久化。

### Q5: 支持自定义评估器吗？

**A**: 支持。你可以继承基类并实现自己的评估器。

```python
from lingflow.self_optimizer.evaluator import BaseEvaluator

class MyEvaluator(BaseEvaluator):
    def evaluate(self, params):
        # 自定义评估逻辑
        return score
```

---

**LingFlow 自优化系统** - 让代码质量持续改进 🚀

---

*最后更新: 2026-03-31*
*版本: 3.6.0*
