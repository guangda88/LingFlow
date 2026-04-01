# LingMinOpt 快速启动指南

## 🎯 立即开始使用 LingMinOpt

### 方式1：运行演示程序

```bash
cd /home/ai/LingFlow
python demo_lingminopt.py
```

演示程序会展示：
1. 搜索空间定义和使用
2. 贝叶斯优化（Rastrigin函数）
3. 多目标优化（Pareto前沿）
4. 实际代码结构优化

### 方式2：在你的项目中使用

#### 基础优化

```python
from lingflow.self_optimizer.phase4 import SearchSpace, OptimizationEngine, OptimizationConfig

# 1. 定义搜索空间
search_space = SearchSpace()
search_space.add_discrete("max_depth", [5, 10, 15, 20])
search_space.add_discrete("min_samples_split", [2, 5, 10])
search_space.add_continuous("min_weight_fraction_leaf", 0.0, 0.5)

# 2. 定义评估函数
def evaluate(params):
    # 你的模型训练和评估逻辑
    model = train_model(**params)
    score = model.evaluate(validation_data)
    return score  # 越小越好

# 3. 配置优化器
config = OptimizationConfig(
    max_experiments=30,
    time_budget=600,
    early_stopping_patience=10,
    acquisition_function="EI"
)

# 4. 运行优化
optimizer = OptimizationEngine(
    search_space=search_space,
    evaluate=evaluate,
    config=config
)

result = optimizer.run()

print(f"最佳参数: {result.best_params}")
print(f"最佳分数: {result.best_objective}")
```

#### 多目标优化

```python
from lingflow.self_optimizer.phase4 import MultiObjectiveOptimizer

# 1. 定义多目标评估
def multi_evaluate(params):
    model = train_model(**params)
    return {
        "accuracy": model.accuracy,      # 最大化
        "training_time": model.time,     # 最小化
        "model_size": model.size         # 最小化
    }

# 2. 创建多目标优化器
multi_opt = MultiObjectiveOptimizer(
    search_space=search_space,
    evaluate=multi_evaluate,
    objectives=["accuracy", "training_time", "model_size"],
    directions=["maximize", "minimize", "minimize"]
)

# 3. 运行优化
pareto_front = multi_opt.run(max_iterations=100)

# 4. 查看Pareto前沿
for point in pareto_front[:10]:
    print(f"参数: {point.params}")
    print(f"目标: {point.objectives}")
```

### 方式3：优化LingFlow代码结构

```python
from lingflow.self_optimizer import quick_optimize

# 快速优化
result = quick_optimize(
    target="/path/to/your/code",
    goal="structure",  # structure, performance, or simplicity
    async_mode=False
)

print(f"优化完成！")
print(f"最佳参数: {result.best_params}")
print(f"改进: {result.improvement_percentage:.1f}%")
```

## 📊 API 文档

### SearchSpace

搜索空间定义类。

**方法**:
- `add_discrete(name, choices)`: 添加离散参数
- `add_continuous(name, min_val, max_val)`: 添加连续参数
- `add_categorical(name, choices)`: 添加分类参数
- `sample()`: 随机采样
- `map_to_vector(params)`: 参数转向量
- `map_to_params(vector)`: 向量转参数

**示例**:
```python
space = SearchSpace()
space.add_discrete("n_estimators", [50, 100, 200])
space.add_continuous("learning_rate", 0.001, 0.1)
space.add_categorical("criterion", ["gini", "entropy"])

params = space.sample()
# {"n_estimators": 100, "learning_rate": 0.05, "criterion": "gini"}
```

### OptimizationEngine

优化引擎类。

**参数**:
- `search_space`: SearchSpace实例
- `evaluate`: 评估函数，接收参数字典，返回数值
- `config`: OptimizationConfig配置

**方法**:
- `run()`: 运行优化，返回OptimizationResult

**OptimizationResult属性**:
- `best_params`: 最佳参数字典
- `best_objective`: 最佳目标值
- `total_experiments`: 总实验次数
- `total_time`: 总耗时（秒）
- `improvement_percentage`: 改进百分比

### OptimizationConfig

优化配置类。

**参数**:
- `max_experiments`: 最大实验次数（默认50）
- `time_budget`: 时间预算，秒（默认300）
- `early_stopping_patience`: 早停耐心值（默认10）
- `direction`: "minimize"或"maximize"（默认"minimize"）
- `acquisition_function`: "EI", "UCB", "PI"（默认"EI"）
- `n_initial_points`: 初始采样点数（默认10）

## 🎓 高级用法

### 自定义采集函数

```python
from lingflow.self_optimizer.phase4 import OptimizationEngine

class CustomOptimizer(OptimizationEngine):
    def _suggest_next(self):
        # 实现你的采集函数
        # 例如：Thompson Sampling, Knowledge Gradient等
        pass

optimizer = CustomOptimizer(
    search_space=search_space,
    evaluate=evaluate,
    config=config
)
```

### 并行优化

```python
from concurrent.futures import ProcessPoolExecutor

def parallel_evaluate(params_list):
    with ProcessPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(evaluate, params_list))
    return results

# 在优化循环中使用并行评估
```

### 优化历史可视化

```python
import matplotlib.pyplot as plt

# 绘制收敛曲线
plt.plot(result.convergence_curve)
plt.xlabel('Iteration')
plt.ylabel('Objective')
plt.title('Optimization Progress')
plt.show()

# 绘制参数分布
import pandas as pd
df = pd.DataFrame([e.params for e in result.history])
df.boxplot()
plt.show()
```

## 🔧 故障排除

### 问题1：评估函数很慢

**解决方案**：
1. 使用异步优化：`async_mode=True`
2. 减少max_experiments
3. 设置合理的time_budget
4. 使用并行评估

### 问题2：优化结果不理想

**解决方案**：
1. 增加n_initial_points进行更好的初始探索
2. 扩大搜索空间范围
3. 尝试不同的acquisition_function
4. 检查评估函数是否正确

### 问题3：内存不足

**解决方案**：
1. 定期清理历史：`optimizer.history.clear()`
2. 使用参数缓存：`CachedParameterStore`
3. 分批优化，每次优化部分参数

## 📚 更多资源

- 完整文档：`LINGMINOPT_SELF_OPTIMIZATION_MASTER_PLAN.md`
- API文档：`docs/api/self_optimizer.md`
- 示例代码：`demo_lingminopt.py`
- 测试：`tests/test_self_optimizer/`

## 💬 获取帮助

- GitHub Issues: https://github.com/guangda88/LingFlow/issues
- 文档: https://lingflow.readthedocs.io/
- 社区讨论: https://github.com/guangda88/LingFlow/discussions
