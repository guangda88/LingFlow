# LingFlow 自优化钩子系统 - 使用指南

**集成日期**: 2026-03-31
**状态**: ✅ 已启用

---

## 🎯 系统概述

自优化钩子系统已成功集成到LingFlow启动流程中。该系统会在特定事件自动触发，检查代码质量，并在必要时提示用户运行优化。

### 集成验证

```bash
$ python test_hooks_integration.py
🎉 所有测试通过！Hooks系统已成功集成。
```

---

## 🚀 自动启动

Hooks系统现在在LingFlow启动时自动初始化：

```python
from lingflow.bootstrap import bootstrap

# 启动LingFlow（hooks默认启用）
status = bootstrap()
# status['hooks'] 包含钩子实例
```

### 启动顺序

1. 版本信息加载
2. 日志系统初始化
3. 智能压缩器初始化
4. 上下文管理器初始化
5. **钩子系统初始化** ← 新增
6. 会话恢复显示

---

## 📋 触发场景

### 场景1: 代码审查得分低

**触发条件**: 代码审查得分 < 70

```python
from lingflow.hooks import get_global_hook

hook = get_global_hook()

# 模拟代码审查完成
review_result = {
    "overall_score": 65,  # 低于阈值70
    "dimensions": {
        "structure": 70,
        "naming": 60,
        "complexity": 65,
    }
}

# 触发检查
hook.on_code_review_complete(review_result)
# 如果得分低，会提示用户是否启动优化
```

**输出示例**:
```
============================================================
             🔍 检测到需要优化的问题
============================================================

原因: 代码审查得分 (65) 低于阈值 (70)
优先级: medium

当前值: 65
阈值: 70

------------------------------------------------------------

是否启动自优化? [y/N]
```

---

### 场景2: 测试覆盖率下降

**触发条件**: 测试覆盖率下降 > 5%

```python
# 模拟测试完成
test_result = {
    "coverage": 85,  # 从90%下降到85%
    "duration": 10,
    "failed": 2,
    "total": 100,
}

hook.on_test_complete(test_result)
```

---

### 场景3: 性能下降

**触发条件**: 执行时间增加 > 50%

```python
# 模拟性能测量
metrics = {
    "execution_time": 15,  # 比基线10秒增加了50%
    "memory_usage_mb": 250,
    "response_time_ms": 500,
}

hook.on_performance_measure(metrics)
```

---

### 场景4: 代码规模增长

**触发条件**: 新增代码行数 > 500

```python
# 模拟Git提交
commit_info = {
    "new_lines": 600,
    "deleted_lines": 100,
    "new_files": 3,
}

hook.on_git_commit(commit_info)
```

---

## 🔧 手动控制

### 获取全局钩子

```python
from lingflow.hooks import get_global_hook

hook = get_global_hook()
```

### 检查优化状态

```python
# 检查是否有优化在运行
is_running = hook.is_optimization_running()
print(f"优化运行中: {is_running}")

# 获取优化结果（如果完成）
result = hook.get_optimization_result()
if result:
    print(f"优化分数: {result.best_score}")
    print(f"最佳参数: {result.best_params}")
```

### 取消优化

```python
# 取消当前正在运行的优化
hook.cancel_optimization()
```

---

## 🎨 集成到工作流

### 集成到代码审查流程

```python
from lingflow.hooks import get_global_hook

def run_code_review():
    """运行代码审查"""
    # ... 运行审查逻辑
    review_result = {
        "overall_score": calculate_score(),
        "dimensions": get_dimensions(),
    }

    # 自动触发优化检查
    hook = get_global_hook()
    hook.on_code_review_complete(review_result)

    return review_result
```

### 集成到测试流程

```python
from lingflow.hooks import get_global_hook

def run_tests():
    """运行测试套件"""
    # ... 运行测试
    test_result = {
        "coverage": get_coverage(),
        "duration": get_duration(),
        "failed": get_failed_count(),
        "total": get_total_count(),
    }

    # 自动触发优化检查
    hook = get_global_hook()
    hook.on_test_complete(test_result)

    return test_result
```

### 集成到Git Hooks

在 `.git/hooks/post-commit`:

```bash
#!/bin/bash
# 获取本次提交的统计信息
new_lines=$(git diff --shortstat HEAD~1 HEAD | grep -oP '\d+(?= insertion)')
new_files=$(git diff --name-only --diff-filter=A HEAD~1 HEAD | wc -l)

# 调用Python脚本
python - <<EOF
from lingflow.hooks import get_global_hook

hook = get_global_hook()
hook.on_git_commit({
    "new_lines": $new_lines,
    "new_files": $new_files,
})
EOF
```

---

## 📊 触发阈值配置

默认阈值（可在 `lingflow/self_optimizer/config.py` 中修改）：

| 触发类型 | 阈值 | 说明 |
|---------|------|------|
| 质量下降 | review_score < 70 | 代码审查得分低于70 |
| 结构违规 | complexity > 15 | 圈复杂度超过15 |
| 性能下降 | 执行时间增加 > 50% | 性能下降超过50% |
| 规模增长 | 新增行数 > 500 | 单次新增代码超过500行 |
| 技术债务 | 覆盖率下降 > 5% | 测试覆盖率下降超过5% |
| 时间间隔 | 距上次优化 > 7天 | 超过7天未优化 |

---

## 🔍 调试和监控

### 查看启动状态

```python
from lingflow.bootstrap import bootstrap

status = bootstrap(hooks=True, verbose=True)

print(f"版本: {status['version']}")
print(f"Hooks: {status['hooks']}")
print(f"错误: {status['errors']}")
```

### 测试触发器

```python
from lingflow.hooks import get_global_hook

hook = get_global_hook()

# 测试触发条件
context = {
    "review_score": 65,
    "coverage_drop": 0,
    "execution_time": 0,
}

should_trigger, info = hook.trigger.check_all_conditions(context)

print(f"应该触发: {should_trigger}")
print(f"原因: {info.reason}")
print(f"优先级: {info.priority}")
```

---

## ⚙️ 高级配置

### 禁用自动启动

如果不想在启动时自动初始化hooks：

```python
from lingflow.bootstrap import bootstrap

status = bootstrap(hooks=False)  # 禁用hooks
```

### 自定义触发器

```python
from lingflow.hooks import get_global_hook
from lingflow.self_optimizer.config import OptimizationConfig

hook = get_global_hook()

# 自定义配置
custom_config = OptimizationConfig(
    triggers={
        "quality": {"review_score_below": 60},  # 更严格
    }
)

hook.trigger.config = custom_config
```

---

## 🧪 测试

运行集成测试：

```bash
# 完整集成测试
python test_hooks_integration.py

# 单独测试bootstrap
python -c "from lingflow.bootstrap import bootstrap; print(bootstrap(hooks=True))"

# 测试触发检测
python -c "
from lingflow.hooks import get_global_hook
hook = get_global_hook()
should, info = hook.trigger.check_all_conditions({'review_score': 65})
print(f'Trigger: {should}, Reason: {info.reason}')
"
```

---

## ✅ 验收清单

- [x] Bootstrap集成（hooks自动初始化）
- [x] 全局钩子可访问
- [x] 触发检测工作正常
- [x] 事件处理器工作正常
- [x] 优化状态查询工作
- [x] 测试全部通过（5/5）

---

## 📝 注意事项

1. **用户交互**: 默认情况下，触发优化会询问用户确认
2. **后台运行**: 优化在独立进程运行，不阻塞主流程
3. **并发控制**: 同时只能运行一个优化任务
4. **结果持久化**: 优化结果保存为Markdown报告

---

## 🎉 总结

LingFlow自优化钩子系统现已完全集成并可正常工作。

**关键特性**:
- ✅ 自动检测代码质量问题
- ✅ 智能触发优化流程
- ✅ 无侵入式集成
- ✅ 可配置的触发阈值
- ✅ 完整的测试覆盖

**下一步**:
1. 根据实际使用调整触发阈值
2. 添加更多触发类型
3. 集成到CI/CD流程

---

*LingFlow 自优化系统 - 让代码质量持续改进* 🚀
