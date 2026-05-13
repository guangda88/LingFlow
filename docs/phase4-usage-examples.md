# Phase 4 参数优化使用示例

本文档展示如何使用lingflow Phase 4的参数优化功能。

## 快速开始

### 1. 单目标优化

```python
from lingflow.self_optimizer.phase4 import quick_optimize

# 优化代码结构
result = quick_optimize(
    target_path="./my_project",
    goal="structure",
    generate_report=True
)

print(f"最佳参数: {result['best_params']}")
print(f"最佳分数: {result['best_score']:.4f}")
print(f"试验次数: {result['n_trials']}")
print(f"收敛率: {result['convergence_rate']:.2%}")

if result.get('report_path'):
    print(f"查看报告: {result['report_path']}")
```

### 2. 多目标优化

```python
from lingflow.self_optimizer.phase4 import quick_multi_optimize

# 同时优化多个目标
result = quick_multi_optimize(
    target_path="./my_project",
    goals=["structure", "performance", "simplicity"],
    weights={"structure": 0.4, "performance": 0.4, "simplicity": 0.2}
)

print(f"Pareto前沿解数: {result['pareto_front_size']}")
print(f"平衡解: {result['balanced_solution']}")
```

### 3. 敏感性分析

```python
from lingflow.self_optimizer.phase4 import quick_sensitivity_analysis

# 分析参数敏感性
result = quick_sensitivity_analysis(
    target_path="./my_project",
    goal="structure",
    method="local"  # 或 "sobol", "morris"
)

for param, sensitivity in result['parameters'].items():
    print(f"{param}: {sensitivity['sensitivity_score']:.4f}")
```

## 高级用法

### 自定义搜索空间

```python
from lingflow.self_optimizer.phase4 import OptimizationEngine

engine = OptimizationEngine()

custom_search_space = {
    "max_class_size": {"type": "int", "min": 100, "max": 500, "step": 50},
    "max_method_count": {"type": "categorical", "choices": [10, 15, 20, 25]},
    "max_complexity": {"type": "int", "min": 5, "max": 20},
    "coupling_limit": {"type": "float", "min": 5.0, "max": 15.0}
}

result = engine.optimize_single_objective(
    target_path="./my_project",
    goal="structure",
    search_space=custom_search_space,
    config={"n_trials": 100, "timeout": 300}
)
```

### 自定义目标函数

```python
from lingflow.self_optimizer.phase4 import BayesianOptimizer

def custom_objective(params):
    """自定义优化目标"""
    x = params.get("param1", 0)
    y = params.get("param2", 0)
    # 计算目标值（越小越好）
    return (x - target_x) ** 2 + (y - target_y) ** 2

search_space = {
    "param1": {"type": "float", "min": 0, "max": 10},
    "param2": {"type": "float", "min": 0, "max": 10}
}

optimizer = BayesianOptimizer(search_space, custom_objective)
state = optimizer.optimize()

print(f"最佳参数: {state.get_best_params()}")
print(f"最佳分数: {state.get_best_score()}")
```

### 多目标优化

```python
from lingflow.self_optimizer.phase4 import optimize_multiple_objectives

# 定义多个目标
def quality_metric(params):
    return params.get("complexity", 0) * 2

def performance_metric(params):
    return params.get("execution_time", 0)

def simplicity_metric(params):
    return params.get("code_lines", 0) / 1000

search_space = {
    "complexity": {"type": "int", "min": 1, "max": 20},
    "execution_time": {"type": "float", "min": 0.1, "max": 10.0},
    "code_lines": {"type": "int", "min": 100, "max": 1000}
}

objectives = {
    "quality": quality_metric,
    "performance": performance_metric,
    "simplicity": simplicity_metric
}

weights = {"quality": 0.4, "performance": 0.4, "simplicity": 0.2}

result = optimize_multiple_objectives(search_space, objectives, weights)

# 获取不同类型的最佳解
best_quality = result.get_best_by_objective("quality")
best_performance = result.get_best_by_objective("performance")
balanced = result.get_balanced_solution()

print(f"质量最优: {best_quality.params}")
print(f"性能最优: {best_performance.params}")
print(f"平衡解: {balanced.params}")
```

## 可视化

### 生成HTML报告

```python
from lingflow.self_optimizer.phase4 import OptimizationVisualizer

visualizer = OptimizationVisualizer(output_dir="./reports")

# 生成优化进度报告
report_path = visualizer.generate_html_report(
    optimization_state=state,
    search_space=search_space,
    metadata={"project": "my_project"}
)
```

### Pareto前沿图

```python
from lingflow.self_optimizer.phase4 import plot_pareto_front

report_path = plot_pareto_front(
    pareto_result=result,
    output_dir="./reports"
)
```

### 敏感性热力图

```python
from lingflow.self_optimizer.phase4 import plot_sensitivity_heatmap

report_path = plot_sensitivity_heatmap(
    sensitivity_results=sensitivity_results,
    output_dir="./reports"
)
```

## 集成到现有代码

### 替换现有优化器

```python
from lingflow.self_optimizer.phase4.integration import enable_phase4_integration

# 启用Phase 4集成
enable_phase4_integration()

# 现在self_optimizer将使用Phase 4的贝叶斯优化
from lingflow.self_optimizer import quick_optimize

result = quick_optimize(target=".", goal="structure")
```

### 使用适配器

```python
from lingflow.self_optimizer.phase4.integration import EnhancedOptimizerAdapter

# 创建适配器
adapter = EnhancedOptimizerAdapter(use_phase4=True)

# 使用现有接口
from lingflow.self_optimizer.optimizer import OptimizationRequest
request = OptimizationRequest(
    target=".",
    goal="structure",
    params={},
    config={"max_experiments": 50}
)

result = adapter.optimize(request)
```

## 配置选项

### 优化配置

```python
config = {
    # 优化器配置
    "n_trials": 50,              # 最大试验次数
    "timeout": 120,              # 超时时间（秒）
    "early_stopping_patience": 10,  # 早停耐心值
    "min_improvement": 0.01,      # 最小改进阈值
    "seed": 42,                  # 随机种子

    # 报告配置
    "generate_reports": True,     # 生成报告
    "output_dir": ".lingflow/reports"  # 输出目录
}
```

### 多目标配置

```python
multi_config = {
    "max_evaluations": 200,       # 最大评估次数
    "timeout": 300,               # 超时时间
    "pareto_epsilon": 0.01        # Pareto前沿精度
}
```

## 性能提示

1. **使用贝叶斯优化**: 相比网格搜索可减少50%以上评估次数
2. **启用缓存**: 相同参数会被缓存，避免重复计算
3. **调整试验次数**: 根据搜索空间大小调整
4. **使用多目标优化**: 找到平衡多个目标的最佳解

## 故障排除

### Optuna未安装

如果看到 "Optuna未安装" 警告，系统会自动降级到网格搜索。

安装Optuna：
```bash
pip install optuna
```

### 内存不足

减少试验次数或搜索空间大小：
```python
config = {"n_trials": 20}  # 减少试验次数
```

### 收敛缓慢

增加早停耐心值或调整搜索空间：
```python
config = {"early_stopping_patience": 20}
```
