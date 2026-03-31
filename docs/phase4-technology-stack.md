# Phase 4 技术选型详细分析

**版本**: v1.0
**日期**: 2026-03-31

---

## 1. 贝叶斯优化库对比

### Optuna (推荐)

**优点**:
- 成熟稳定，50k+ GitHub stars
- 支持TPE、CMA-ES、Random、Grid等多种采样器
- 内置剪枝（MedianPruner、Hyperband、SuccessiveHalving）
- 支持并行优化和分布式执行
- 轻量级依赖（仅依赖numpy、packaging）
- 活跃社区，文档完善
- Python 3.8+支持

**缺点**:
- TPE算法对于非常高维搜索空间可能不如高斯过程
- 默认配置可能需要调优

**依赖**:
```
optuna>=3.0.0
numpy>=1.20.0
packaging>=21.0
```

**代码示例**:
```python
import optuna

def objective(trial):
    x = trial.suggest_float("x", -10, 10)
    return (x - 2) ** 2

study = optuna.create_study(
    direction="minimize",
    sampler=optuna.samplers.TPESampler(seed=42)
)
study.optimize(objective, n_trials=100)

print(f"Best value: {study.best_value}")
print(f"Best params: {study.best_params}")
```

### Scikit-Optimize (备选)

**优点**:
- 基于高斯过程，适合小规模搜索空间
- 与scikit-learn生态系统集成良好
- 支持贝叶斯优化、随机优化、森林优化

**缺点**:
- 依赖较重（需要scikit-learn）
- 不如Optuna活跃
- 性能可能不如TPE

**依赖**:
```
scikit-optimize>=0.9.0
scikit-learn>=1.0.0
scipy>=1.7.0
```

**代码示例**:
```python
from skopt import gp_minimize
from skopt.space import Real

def objective(params):
    x = params[0]
    return (x - 2) ** 2

space = [Real(-10, 10, name="x")]
result = gp_minimize(objective, space, n_calls=100)

print(f"Best value: {result.fun}")
print(f"Best params: {result.x}")
```

### 选型建议

| 场景 | 推荐方案 |
|------|----------|
| 通用场景 | Optuna (TPE) |
| 小规模搜索空间(<10维) | Scikit-Optimize (GP) |
| 需要分布式优化 | Optuna |
| 依赖最小化 | Optuna |

---

## 2. 存储方案对比

### 文件系统存储 (推荐用于初期)

**优点**:
- 零额外依赖
- 简单直观
- 易于备份和迁移
- 适合单机场景

**缺点**:
- 不支持并发写入
- 大规模数据性能较差
- 缺少事务支持

**存储结构**:
```
~/.lingflow/
├── parameters/
│   ├── index.json           # 索引文件
│   ├── versions/            # 参数版本
│   │   ├── abc123.json
│   │   └── def456.json
│   └── cache/               # 缓存
│       └── *.cache
```

### SQLite存储 (推荐用于生产)

**优点**:
- 内置Python支持
- 支持事务和并发
- 查询能力强
- 轻量级但可靠

**缺点**:
- 需要数据库设计
- 略微增加复杂度

**Schema设计**:
```sql
CREATE TABLE parameter_versions (
    version_id TEXT PRIMARY KEY,
    params_json TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    parent_version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum TEXT NOT NULL,
    FOREIGN KEY (parent_version) REFERENCES parameter_versions(version_id)
);

CREATE INDEX idx_versions_project ON parameter_versions(
    json_extract(metadata_json, '$.project')
);

CREATE TABLE optimization_history (
    trial_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id TEXT NOT NULL,
    params_json TEXT NOT NULL,
    score REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (version_id) REFERENCES parameter_versions(version_id)
);
```

### Redis存储 (可选，用于多机场景)

**优点**:
- 高性能
- 支持分布式
- 丰富的数据结构

**缺点**:
- 需要额外服务
- 增加部署复杂度

### 选型建议

| 场景 | 推荐方案 |
|------|----------|
| 开发/测试 | 文件系统 |
| 单机生产 | SQLite |
| 多机分布式 | Redis |
| 云原生 | PostgreSQL |

---

## 3. 可视化方案

### Plotly (推荐)

**优点**:
- 交互式图表
- 支持导出HTML
- 丰富的图表类型
- 与Optuna集成良好

**依赖**:
```
plotly>=5.0.0
```

**代码示例**:
```python
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[t["trial"] for t in history],
    y=[t["score"] for t in history],
    mode="lines+markers",
    name="优化历史"
))
fig.update_layout(
    title="参数优化进度",
    xaxis_title="试验次数",
    yaxis_title="分数"
)
fig.write_html("optimization_progress.html")
```

### Rich (用于终端输出)

**优点**:
- 美化终端输出
- 进度条、表格、语法高亮
- 轻量级

**依赖**:
```
rich>=12.0.0
```

**代码示例**:
```python
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

# 表格
table = Table(title="参数优化结果")
table.add_column("参数", style="cyan")
table.add_column("值", style="magenta")

for param, value in best_params.items():
    table.add_row(param, str(value))

console.print(table)

# 进度条
for i in track(range(100), description="优化中..."):
    time.sleep(0.01)
```

---

## 4. 统计分析方案

### SciPy (推荐)

**优点**:
- 成熟的统计库
- 包含t检验、ANOVA等
- 与numpy集成良好

**依赖**:
```
scipy>=1.7.0
```

**A/B测试示例**:
```python
from scipy import stats

# t检验
t_stat, p_value = stats.ttest_ind(scores_a, scores_b)

# 判断显著性
alpha = 0.05
if p_value < alpha:
    print(f"显著差异 (p={p_value:.4f})")
else:
    print(f"无显著差异 (p={p_value:.4f})")
```

### Statsmodels (可选，用于高级分析)

**优点**:
- 更丰富的统计模型
- 回归分析、时间序列等

**依赖**:
```
statsmodels>=0.13.0
```

---

## 5. 依赖兼容性矩阵

| Python版本 | Optuna | Scikit-Optimize | Plotly | Rich | SciPy |
|------------|--------|-----------------|--------|------|-------|
| 3.8 | >=3.0.0 | >=0.9.0 | >=5.0.0 | >=12.0.0 | >=1.7.0 |
| 3.9 | >=3.0.0 | >=0.9.0 | >=5.0.0 | >=12.0.0 | >=1.7.0 |
| 3.10 | >=3.0.0 | >=0.9.0 | >=5.0.0 | >=12.0.0 | >=1.7.0 |
| 3.11 | >=3.1.0 | >=0.9.0 | >=5.11.0 | >=13.0.0 | >=1.10.0 |

---

## 6. 性能基准

### Optuna性能

| 搜索空间维度 | TPE (秒/100次) | GP (秒/100次) | Random (秒/100次) |
|--------------|----------------|---------------|-------------------|
| 5 | 2.5 | 8.3 | 1.2 |
| 10 | 4.1 | 25.6 | 1.5 |
| 20 | 7.8 | 85.2 | 2.1 |

### 存储性能

| 方案 | 写入 (ms) | 读取 (ms) | 查询 (ms) |
|------|-----------|-----------|-----------|
| 文件系统 | 5-10 | 2-5 | 100-500 |
| SQLite | 1-3 | 0.5-2 | 10-50 |
| Redis | 0.5-1 | 0.1-0.5 | 1-5 |

---

## 7. 推荐技术栈

### 核心依赖 (必须)

```
# requirements.txt
optuna>=3.0.0
numpy>=1.20.0
scipy>=1.7.0
pyyaml>=5.4.0
```

### 推荐依赖 (强烈推荐)

```
# requirements-recommended.txt
plotly>=5.0.0
rich>=12.0.0
```

### 可选依赖

```
# requirements-optional.txt
scikit-optimize>=0.9.0
statsmodels>=0.13.0
sqlalchemy>=1.4.0
redis>=4.0.0
```

### 开发依赖

```
# requirements-dev.txt
pytest>=7.0.0
pytest-cov>=3.0.0
pytest-mock>=3.0.0
mypy>=0.950
black>=22.0.0
isort>=5.0.0
```

---

## 8. 安装命令

```bash
# 最小安装
pip install -e .

# 标准安装（推荐）
pip install -e ".[recommended]"

# 完整安装
pip install -e ".[all]"

# 开发安装
pip install -e ".[dev]"
```

### setup.py配置

```python
setup(
    name="lingflow",
    # ...
    extras_require={
        "recommended": [
            "optuna>=3.0.0",
            "plotly>=5.0.0",
            "rich>=12.0.0",
        ],
        "all": [
            "optuna>=3.0.0",
            "scikit-optimize>=0.9.0",
            "plotly>=5.0.0",
            "rich>=12.0.0",
            "statsmodels>=0.13.0",
            "sqlalchemy>=1.4.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=3.0.0",
            "mypy>=0.950",
            "black>=22.0.0",
        ],
    },
)
```

---

## 9. 版本策略

### 依赖版本锁定

```
# requirements-lock.txt (生成于2026-03-31)
optuna==3.3.0
numpy==1.24.3
scipy==1.10.1
plotly==5.14.1
rich==13.3.5
pyyaml==6.0
```

### 兼容性测试

在CI中测试以下组合：
- Python 3.8 + Optuna 3.0
- Python 3.9 + Optuna 3.1
- Python 3.10 + Optuna 3.2
- Python 3.11 + Optuna 3.3

---

**文档版本**: v1.0
**最后更新**: 2026-03-31
