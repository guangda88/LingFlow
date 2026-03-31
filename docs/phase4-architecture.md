# LingFlow Phase 4: 参数优化架构设计

**版本**: v1.0
**日期**: 2026-03-31
**状态**: 架构设计

---

## 目录

1. [架构概述](#架构概述)
2. [设计目标](#设计目标)
3. [当前状态分析](#当前状态分析)
4. [核心架构](#核心架构)
5. [参数优化算法](#参数优化算法)
6. [参数管理系统](#参数管理系统)
7. [评估框架](#评估框架)
8. [技术栈选型](#技术栈选型)
9. [接口设计](#接口设计)
10. [集成策略](#集成策略)
11. [实施路线图](#实施路线图)
12. [性能约束](#性能约束)

---

## 架构概述

Phase 4参数优化架构旨在将LingFlow的自优化能力从简单的网格搜索升级到智能参数优化系统。通过引入贝叶斯优化、参数持久化和多目标优化策略，实现更高效、更智能的参数调优。

### 架构分层

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (CLI / Hooks)                      │
├─────────────────────────────────────────────────────────────┤
│                    优化协调层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 优化调度器   │  │  参数管理器  │  │  报告生成器  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    算法核心层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 贝叶斯优化器 │  │ 多目标优化器 │  │ 敏感性分析器 │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    评估层                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 结构评估器   │  │ 性能评估器   │  │ 简洁评估器   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
├─────────────────────────────────────────────────────────────┤
│                    持久化层                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 参数存储     │  │ 历史记录     │  │ 缓存管理     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 设计目标

### 主要目标

1. **智能优化**: 从网格搜索升级到贝叶斯优化，减少50%以上的评估次数
2. **参数持久化**: 实现参数版本管理和最佳参数缓存
3. **多目标优化**: 同时优化代码质量、性能、简洁性
4. **知识迁移**: 支持跨项目的参数知识迁移
5. **实时监控**: 提供优化进度可视化和收敛性检测

### 非目标

- 不改变现有的评估器接口
- 不修改现有的触发器系统
- 不影响核心LingFlow工作流

---

## 当前状态分析

### 现有系统架构

当前LingFlow自优化系统（v3.6.0）包含：

**优点**:
- 已实现结构、性能、简洁性三个评估器
- 支持LingMinOpt集成（带降级）
- 进程隔离的优化器设计
- 完善的配置管理系统

**限制**:
- 使用简单网格搜索或随机采样
- 无参数持久化机制
- 无参数版本管理
- 无多目标优化支持
- 无参数敏感性分析

### 关键性能指标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| 192类项目优化时间 | ~120秒 | <60秒 |
| 参数评估次数 | 20-50次 | <15次 |
| 内存占用 | ~150MB | <200MB |
| 参数命中率 | N/A | >60% |

---

## 核心架构

### 架构原则

1. **向后兼容**: 保持现有API不变
2. **渐进增强**: 可选启用新功能
3. **模块化**: 各组件独立可测试
4. **可扩展**: 支持新算法和评估器
5. **可观测**: 完整的日志和指标

### 核心组件关系图

```
┌─────────────────────────────────────────────────────────────┐
│                       OptimizationEngine                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              OptimizationCoordinator                  │   │
│  │  - 管理优化生命周期                                    │   │
│  │  - 协调各个组件                                        │   │
│  │  - 处理优化请求                                        │   │
│  └──────────┬──────────────────┬──────────────────┬─────┘   │
│             │                  │                  │         │
│  ┌──────────▼──────┐  ┌───────▼────────┐  ┌─────▼──────┐  │
│  │ BayesianOptimizer│  │ParameterManager│  │MultiObjective│  │
│  │                  │  │                 │  │ Optimizer   │  │
│  └──────────────────┘  └─────────────────┘  └─────────────┘  │
│             │                  │                  │         │
│  ┌──────────▼──────────────────▼──────────────────▼──────┐  │
│  │               ParameterStore                          │  │
│  │  - 参数版本管理                                        │  │
│  │  - 最佳参数缓存                                        │  │
│  │  - 知识迁移                                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 参数优化算法

### 贝叶斯优化器设计

贝叶斯优化通过构建代理模型（高斯过程或TPE）来建模目标函数，从而用更少的评估次数找到最优参数。

#### 核心算法选择

**推荐方案**: Optuna (TPE算法)

**选择理由**:
1. 成熟稳定，广泛使用
2. 支持并行优化
3. 内置剪枝和早停
4. 轻量级依赖
5. 活跃社区支持

**备选方案**:
- **Scikit-Optimize**: 基于高斯过程，适合小规模搜索空间
- **BoTorch**: 适合大规模并行优化，但依赖较重

#### 算法实现框架

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable
import numpy as np

@dataclass
class OptimizationTrial:
    """优化试验"""
    trial_id: str
    params: Dict[str, Any]
    score: float
    metrics: Dict[str, float]
    timestamp: float
    converged: bool = False

@dataclass
class OptimizationState:
    """优化状态"""
    current_trial: int
    best_trial: OptimizationTrial
    convergence_rate: float
    should_stop: bool = False

class BaseOptimizer(ABC):
    """优化器基类"""

    def __init__(
        self,
        search_space: Dict[str, Any],
        objective: Callable[[Dict[str, Any]], float],
        config: Dict[str, Any]
    ):
        self.search_space = search_space
        self.objective = objective
        self.config = config
        self.history: List[OptimizationTrial] = []

    @abstractmethod
    def suggest(self) -> Dict[str, Any]:
        """建议下一组参数"""
        pass

    @abstractmethod
    def observe(self, params: Dict[str, Any], score: float) -> None:
        """观察评估结果"""
        pass

    @abstractmethod
    def should_stop(self) -> bool:
        """判断是否应该停止"""
        pass

class BayesianOptimizer(BaseOptimizer):
    """贝叶斯优化器 (Optuna TPE)"""

    def __init__(
        self,
        search_space: Dict[str, Any],
        objective: Callable[[Dict[str, Any]], float],
        config: Dict[str, Any]
    ):
        super().__init__(search_space, objective, config)
        self.study = self._create_study()
        self.n_trials = config.get("n_trials", 50)
        self.timeout = config.get("timeout", 120)

    def _create_study(self):
        """创建Optuna研究"""
        try:
            import optuna

            study = optuna.create_study(
                direction="minimize",
                sampler=optuna.samplers.TPESampler(
                    seed=self.config.get("seed", 42),
                    multivariate=True,
                    group=True
                ),
                pruner=optuna.pruners.MedianPruner(
                    n_startup_trials=5,
                    n_warmup_steps=10
                )
            )

            return study
        except ImportError:
            raise ImportError("Optuna未安装，请运行: pip install optuna")

    def suggest(self) -> Dict[str, Any]:
        """建议下一组参数"""
        trial = self.study.ask()

        params = {}
        for name, space in self.search_space.items():
            if space["type"] == "categorical":
                params[name] = trial.suggest_categorical(
                    name, space["choices"]
                )
            elif space["type"] == "int":
                params[name] = trial.suggest_int(
                    name, space["min"], space["max"]
                )
            elif space["type"] == "float":
                params[name] = trial.suggest_float(
                    name, space["min"], space["max"]
                )

        return params

    def observe(self, params: Dict[str, Any], score: float) -> None:
        """观察评估结果"""
        self.study.tell(score)

        # 记录历史
        trial = OptimizationTrial(
            trial_id=f"trial_{len(self.history)}",
            params=params,
            score=score,
            metrics={},
            timestamp=time.time()
        )
        self.history.append(trial)

    def should_stop(self) -> bool:
        """判断是否应该停止"""
        # 收敛性检测
        if len(self.history) < 10:
            return False

        # 检查最近10次试验的改进
        recent_scores = [t.score for t in self.history[-10:]]
        improvement = (recent_scores[0] - recent_scores[-1]) / recent_scores[0]

        if improvement < self.config.get("min_improvement", 0.01):
            return True

        return len(self.history) >= self.n_trials

    def optimize(self) -> OptimizationTrial:
        """运行完整优化"""
        while not self.should_stop():
            params = self.suggest()
            score = self.objective(params)
            self.observe(params, score)

        return self.history[
            min(range(len(self.history)), key=lambda i: self.history[i].score)
        ]
```

#### 多目标优化器

```python
class MultiObjectiveOptimizer(BaseOptimizer):
    """多目标优化器 (Pareto前沿)"""

    def __init__(
        self,
        search_space: Dict[str, Any],
        objectives: List[Callable[[Dict[str, Any]], float]],
        weights: Optional[List[float]] = None,
        config: Dict[str, Any] = None
    ):
        super().__init__(search_space, lambda x: 0, config or {})
        self.objectives = objectives
        self.weights = weights or [1.0] * len(objectives)
        self.pareto_front: List[OptimizationTrial] = []

    def _weighted_score(self, params: Dict[str, Any]) -> float:
        """计算加权分数"""
        scores = [obj(params) for obj in self.objectives]
        return sum(s * w for s, w in zip(scores, self.weights))

    def _update_pareto_front(self, trial: OptimizationTrial) -> None:
        """更新Pareto前沿"""
        # 检查是否被支配
        dominated = False
        for existing in self.pareto_front:
            if all(
                existing.metrics.get(f"obj_{i}", float('inf')) <=
                trial.metrics.get(f"obj_{i}", float('inf'))
                for i in range(len(self.objectives))
            ):
                dominated = True
                break

        if not dominated:
            # 移除被新试验支配的
            self.pareto_front = [
                t for t in self.pareto_front
                if not all(
                    trial.metrics.get(f"obj_{i}", float('inf')) <=
                    t.metrics.get(f"obj_{i}", float('inf'))
                    for i in range(len(self.objectives))
                )
            ]
            self.pareto_front.append(trial)

    def get_pareto_front(self) -> List[OptimizationTrial]:
        """获取Pareto前沿"""
        return sorted(self.pareto_front, key=lambda t: t.score)
```

#### 敏感性分析器

```python
class SensitivityAnalyzer:
    """参数敏感性分析器"""

    def __init__(
        self,
        search_space: Dict[str, Any],
        objective: Callable[[Dict[str, Any]], float],
        base_params: Dict[str, Any]
    ):
        self.search_space = search_space
        self.objective = objective
        self.base_params = base_params

    def analyze(
        self,
        n_samples: int = 100,
        method: str = "sobol"
    ) -> Dict[str, float]:
        """分析参数敏感性

        Returns:
            参数名 -> 敏感性分数 (0-1)
        """
        sensitivities = {}

        base_score = self.objective(self.base_params)

        for param_name, space in self.search_space.items():
            # 单变量扰动分析
            perturbations = []

            if space["type"] == "categorical":
                # 测试所有类别
                for value in space["choices"]:
                    params = self.base_params.copy()
                    params[param_name] = value
                    score = self.objective(params)
                    perturbations.append(abs(score - base_score))

            elif space["type"] in ("int", "float"):
                # 在范围内采样
                values = np.linspace(space["min"], space["max"], min(10, n_samples))
                for value in values:
                    params = self.base_params.copy()
                    params[param_name] = value
                    score = self.objective(params)
                    perturbations.append(abs(score - base_score))

            # 计算敏感性（归一化）
            sensitivity = np.mean(perturbations) / (base_score + 1e-6)
            sensitivities[param_name] = min(1.0, sensitivity)

        return sensitivities
```

---

## 参数管理系统

### 参数持久化架构

```python
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json

class ParameterVersion:
    """参数版本"""

    def __init__(
        self,
        params: Dict[str, Any],
        metadata: Dict[str, Any],
        parent_version: Optional[str] = None
    ):
        self.version_id = self._generate_id(params)
        self.params = params
        self.metadata = metadata
        self.parent_version = parent_version
        self.created_at = datetime.now()
        self.checksum = self._calculate_checksum(params)

    def _generate_id(self, params: Dict[str, Any]) -> str:
        """生成版本ID"""
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.sha256(param_str.encode()).hexdigest()[:16]

    def _calculate_checksum(self, params: Dict[str, Any]) -> str:
        """计算校验和"""
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()

class ParameterStore:
    """参数存储（后端抽象）"""

    def save(self, version: ParameterVersion) -> bool:
        """保存参数版本"""
        raise NotImplementedError

    def load(self, version_id: str) -> Optional[ParameterVersion]:
        """加载参数版本"""
        raise NotImplementedError

    def list_versions(self, filter: Dict[str, Any] = None) -> List[ParameterVersion]:
        """列出参数版本"""
        raise NotImplementedError

    def delete(self, version_id: str) -> bool:
        """删除参数版本"""
        raise NotImplementedError

class FileSystemParameterStore(ParameterStore):
    """文件系统参数存储"""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_path / "index.json"
        self.versions_path = self.base_path / "versions"
        self.versions_path.mkdir(exist_ok=True)

        self._load_index()

    def _load_index(self):
        """加载索引"""
        if self.index_path.exists():
            with open(self.index_path, 'r') as f:
                self.index = json.load(f)
        else:
            self.index = {
                "versions": {},
                "by_project": {},
                "by_goal": {},
                "best": {}
            }

    def _save_index(self):
        """保存索引"""
        with open(self.index_path, 'w') as f:
            json.dump(self.index, f, indent=2, default=str)

    def save(self, version: ParameterVersion) -> bool:
        """保存参数版本"""
        # 保存版本文件
        version_file = self.versions_path / f"{version.version_id}.json"
        version_file.write_text(json.dumps({
            "params": version.params,
            "metadata": version.metadata,
            "parent_version": version.parent_version,
            "created_at": version.created_at.isoformat(),
            "checksum": version.checksum
        }, indent=2))

        # 更新索引
        project = version.metadata.get("project", "default")
        goal = version.metadata.get("goal", "unknown")

        self.index["versions"][version.version_id] = {
            "created_at": version.created_at.isoformat(),
            "checksum": version.checksum,
            "project": project,
            "goal": goal
        }

        if project not in self.index["by_project"]:
            self.index["by_project"][project] = []
        self.index["by_project"][project].append(version.version_id)

        if goal not in self.index["by_goal"]:
            self.index["by_goal"][goal] = []
        self.index["by_goal"][goal].append(version.version_id)

        # 更新最佳参数
        best_key = f"{project}:{goal}"
        if best_key not in self.index["best"]:
            self.index["best"][best_key] = version.version_id
        else:
            # 比较分数
            existing_version = self.load(self.index["best"][best_key])
            if existing_version and version.metadata.get("score", float('inf')) < existing_version.metadata.get("score", float('inf')):
                self.index["best"][best_key] = version.version_id

        self._save_index()
        return True

    def load(self, version_id: str) -> Optional[ParameterVersion]:
        """加载参数版本"""
        version_file = self.versions_path / f"{version_id}.json"
        if not version_file.exists():
            return None

        data = json.loads(version_file.read_text())
        return ParameterVersion(
            params=data["params"],
            metadata=data["metadata"],
            parent_version=data.get("parent_version")
        )

    def get_best_params(self, project: str, goal: str) -> Optional[Dict[str, Any]]:
        """获取最佳参数"""
        best_key = f"{project}:{goal}"
        version_id = self.index["best"].get(best_key)

        if version_id:
            version = self.load(version_id)
            return version.params if version else None

        return None
```

### 参数缓存管理

```python
from functools import lru_cache
from typing import Tuple

class ParameterCache:
    """参数缓存管理器"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache = {}

    def _make_key(self, params: Dict[str, Any], context: str) -> str:
        """生成缓存键"""
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(f"{context}:{param_str}".encode()).hexdigest()

    def get(self, params: Dict[str, Any], context: str) -> Optional[float]:
        """获取缓存结果"""
        key = self._make_key(params, context)
        return self._cache.get(key)

    def set(self, params: Dict[str, Any], context: str, result: float) -> None:
        """设置缓存"""
        if len(self._cache) >= self.max_size:
            # LRU淘汰
            oldest = next(iter(self._cache))
            del self._cache[oldest]

        key = self._make_key(params, context)
        self._cache[key] = result

    def invalidate(self, context: str = None) -> None:
        """失效缓存"""
        if context:
            keys_to_delete = [k for k in self._cache if k.startswith(context)]
            for key in keys_to_delete:
                del self._cache[key]
        else:
            self._cache.clear()
```

### 知识迁移

```python
class KnowledgeTransfer:
    """参数知识迁移"""

    def __init__(self, store: ParameterStore):
        self.store = store

    def transfer(
        self,
        source_project: str,
        target_project: str,
        goal: str,
        similarity_threshold: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """从源项目迁移参数到目标项目

        Args:
            source_project: 源项目名称
            target_project: 目标项目名称
            goal: 优化目标
            similarity_threshold: 相似度阈值

        Returns:
            迁移后的参数（如果相似度足够高）
        """
        # 获取源项目的最佳参数
        source_params = self.store.get_best_params(source_project, goal)
        if not source_params:
            return None

        # 计算项目相似度（简化版）
        similarity = self._calculate_similarity(
            source_project, target_project
        )

        if similarity >= similarity_threshold:
            # 应用迁移调整
            return self._adjust_parameters(
                source_params, source_project, target_project
            )

        return None

    def _calculate_similarity(self, project1: str, project2: str) -> float:
        """计算项目相似度"""
        # 简化版：基于项目元数据
        # 实际实现可以考虑：
        # - 代码结构相似度
        # - 技术栈相似度
        # - 规模相似度
        return 0.8  # 占位符

    def _adjust_parameters(
        self,
        params: Dict[str, Any],
        source_project: str,
        target_project: str
    ) -> Dict[str, Any]:
        """调整参数以适应目标项目"""
        # 根据项目规模等调整参数
        # 简化版：直接返回原参数
        return params.copy()
```

---

## 评估框架

### 评估指标设计

```python
from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum

class MetricType(Enum):
    """指标类型"""
    STRUCTURE = "structure"
    PERFORMANCE = "performance"
    SIMPLICITY = "simplicity"
    QUALITY = "quality"

@dataclass
class Metric:
    """评估指标"""
    name: str
    value: float
    type: MetricType
    weight: float = 1.0
    higher_is_better: bool = False

@dataclass
class EvaluationResult:
    """评估结果"""
    metrics: Dict[str, Metric]
    overall_score: float
    converged: bool
    metadata: Dict[str, Any]

class EvaluationFramework:
    """评估框架"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_weights = config.get("metrics_weights", {})
        self.convergence_threshold = config.get("convergence_threshold", 0.01)

    def evaluate(
        self,
        params: Dict[str, Any],
        evaluators: Dict[str, Any],
        goal: str
    ) -> EvaluationResult:
        """综合评估

        Args:
            params: 参数配置
            evaluators: 评估器字典
            goal: 优化目标

        Returns:
            评估结果
        """
        metrics = {}
        weighted_scores = []

        # 结构评估
        if "structure" in evaluators and goal in ("structure", "all"):
            structure_result = evaluators["structure"].evaluate(params)
            metrics["structure_violations"] = Metric(
                name="structure_violations",
                value=structure_result,
                type=MetricType.STRUCTURE,
                weight=self.metrics_weights.get("structure", 1.0)
            )
            weighted_scores.append(
                metrics["structure_violations"].value *
                metrics["structure_violations"].weight
            )

        # 性能评估
        if "performance" in evaluators and goal in ("performance", "all"):
            perf_result = evaluators["performance"].evaluate(params)
            metrics["execution_time"] = Metric(
                name="execution_time",
                value=perf_result,
                type=MetricType.PERFORMANCE,
                weight=self.metrics_weights.get("performance", 1.0)
            )
            weighted_scores.append(
                metrics["execution_time"].value *
                metrics["execution_time"].weight
            )

        # 简洁性评估
        if "simplicity" in evaluators and goal in ("simplicity", "all"):
            simplicity_result = evaluators["simplicity"].evaluate(params)
            metrics["complexity_score"] = Metric(
                name="complexity_score",
                value=simplicity_result,
                type=MetricType.SIMPLICITY,
                weight=self.metrics_weights.get("simplicity", 1.0)
            )
            weighted_scores.append(
                metrics["complexity_score"].value *
                metrics["complexity_score"].weight
            )

        # 计算总分
        overall_score = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0

        # 检测收敛
        converged = self._check_convergence(metrics)

        return EvaluationResult(
            metrics=metrics,
            overall_score=overall_score,
            converged=converged,
            metadata={"params": params}
        )

    def _check_convergence(self, metrics: Dict[str, Metric]) -> bool:
        """检测收敛"""
        # 简化版：基于指标变化率
        # 实际实现需要历史数据
        return False
```

### A/B测试框架

```python
class ABTestFramework:
    """A/B测试框架"""

    def __init__(
        self,
        evaluator: EvaluationFramework,
        min_samples: int = 5,
        confidence_level: float = 0.95
    ):
        self.evaluator = evaluator
        self.min_samples = min_samples
        self.confidence_level = confidence_level

    def compare(
        self,
        params_a: Dict[str, Any],
        params_b: Dict[str, Any],
        evaluators: Dict[str, Any],
        goal: str
    ) -> Dict[str, Any]:
        """比较两组参数

        Returns:
            比较结果，包含统计显著性
        """
        # 多次评估A
        scores_a = []
        for _ in range(self.min_samples):
            result = self.evaluator.evaluate(params_a, evaluators, goal)
            scores_a.append(result.overall_score)

        # 多次评估B
        scores_b = []
        for _ in range(self.min_samples):
            result = self.evaluator.evaluate(params_b, evaluators, goal)
            scores_b.append(result.overall_score)

        # 统计检验
        from scipy import stats

        t_stat, p_value = stats.ttest_ind(scores_a, scores_b)

        # 计算改善比例
        mean_a = np.mean(scores_a)
        mean_b = np.mean(scores_b)
        improvement = (mean_a - mean_b) / mean_a

        return {
            "params_a": params_a,
            "params_b": params_b,
            "mean_a": mean_a,
            "mean_b": mean_b,
            "improvement": improvement,
            "p_value": p_value,
            "significant": p_value < (1 - self.confidence_level),
            "winner": "a" if mean_a < mean_b else "b"
        }
```

### 收敛性检测

```python
class ConvergenceDetector:
    """收敛性检测器"""

    def __init__(
        self,
        window_size: int = 10,
        threshold: float = 0.01,
        min_trials: int = 20
    ):
        self.window_size = window_size
        self.threshold = threshold
        self.min_trials = min_trials
        self.history: List[float] = []

    def update(self, score: float) -> bool:
        """更新并检查收敛

        Returns:
            是否收敛
        """
        self.history.append(score)

        if len(self.history) < self.min_trials:
            return False

        # 检查最近window_size个分数的变化
        recent = self.history[-self.window_size:]

        # 计算标准差
        std = np.std(recent)

        # 计算相对变化
        mean = np.mean(recent)
        relative_change = std / (mean + 1e-6)

        return relative_change < self.threshold

    def get_convergence_rate(self) -> float:
        """获取收敛率"""
        if len(self.history) < self.window_size:
            return 0.0

        recent = self.history[-self.window_size:]
        mean = np.mean(recent)
        std = np.std(recent)

        return 1.0 - min(1.0, std / (mean + 1e-6))
```

---

## 技术栈选型

### 核心依赖

| 库名 | 版本 | 用途 | 优先级 |
|------|------|------|--------|
| optuna | >=3.0 | 贝叶斯优化 (TPE) | 必须 |
| scikit-optimize | >=0.9 | 备选优化算法 | 可选 |
| numpy | >=1.20 | 数值计算 | 必须 |
| scipy | >=1.7 | 统计检验 | 推荐 |
| pyyaml | >=5.4 | 配置文件 | 必须 |

### 可选依赖

| 库名 | 版本 | 用途 | 优先级 |
|------|------|------|--------|
| plotly | >=5.0 | 可视化 | 推荐 |
| rich | >=12.0 | 终端输出 | 可选 |
| sqlalchemy | >=1.4 | 数据库存储 | 可选 |

### 依赖安装

```bash
# 核心依赖
pip install optuna numpy scipy pyyaml

# 可选依赖
pip install scikit-optimize plotly rich

# 开发依赖
pip install pytest pytest-cov mypy black
```

---

## 接口设计

### 优化引擎主接口

```python
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

@dataclass
class OptimizationRequest:
    """优化请求"""
    # 目标配置
    target_path: str
    goal: str  # structure, performance, simplicity, all

    # 搜索空间
    search_space: Dict[str, Any]

    # 约束
    constraints: Dict[str, Any] = None

    # 配置
    max_time: float = 120  # 秒
    max_trials: int = 50
    early_stopping: bool = True
    enable_cache: bool = True
    enable_transfer: bool = True

    # 元数据
    project_name: str = "default"
    experiment_name: str = None

@dataclass
class OptimizationResult:
    """优化结果"""
    # 最佳参数
    best_params: Dict[str, Any]
    best_score: float

    # 统计
    n_trials: int
    total_time: float

    # 历史记录
    trials: List[Dict[str, Any]]

    # 收敛信息
    converged: bool
    convergence_rate: float

    # 敏感性分析
    sensitivities: Dict[str, float] = None

    # Pareto前沿（多目标）
    pareto_front: List[Dict[str, Any]] = None

    # 错误信息
    error: Optional[str] = None

class OptimizationEngine:
    """优化引擎主类"""

    def __init__(
        self,
        config: Dict[str, Any] = None,
        store: ParameterStore = None
    ):
        self.config = config or {}
        self.store = store or FileSystemParameterStore(
            Path.home() / ".lingflow" / "parameters"
        )

        # 初始化组件
        self.cache = ParameterCache()
        self.evaluator = EvaluationFramework(self.config)
        self.convergence_detector = ConvergenceDetector()
        self.transfer = KnowledgeTransfer(self.store)

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """执行优化

        Args:
            request: 优化请求

        Returns:
            优化结果
        """
        # 1. 尝试参数迁移
        if request.enable_transfer:
            transferred_params = self.transfer.transfer(
                source_project=None,  # 自动选择相似项目
                target_project=request.project_name,
                goal=request.goal
            )
            if transferred_params:
                # 使用迁移参数作为起点
                pass

        # 2. 选择优化器
        if request.goal == "all":
            optimizer = MultiObjectiveOptimizer(...)
        else:
            optimizer = BayesianOptimizer(...)

        # 3. 运行优化
        trials = []
        start_time = time.time()

        while not self._should_stop(request, trials, start_time):
            # 建议参数
            params = optimizer.suggest()

            # 检查缓存
            cache_key = self._make_cache_key(params, request)
            if request.enable_cache:
                cached_score = self.cache.get(params, cache_key)
                if cached_score is not None:
                    score = cached_score
                else:
                    score = self._evaluate(params, request)
                    self.cache.set(params, cache_key, score)
            else:
                score = self._evaluate(params, request)

            # 观察结果
            optimizer.observe(params, score)

            # 记录试验
            trials.append({
                "params": params,
                "score": score,
                "timestamp": time.time() - start_time
            })

            # 检查收敛
            if self.convergence_detector.update(score):
                break

        # 4. 敏感性分析
        sensitivities = self._analyze_sensitivity(
            optimizer, request
        )

        # 5. 保存结果
        self._save_result(request, trials)

        return OptimizationResult(
            best_params=optimizer.best_params,
            best_score=optimizer.best_score,
            n_trials=len(trials),
            total_time=time.time() - start_time,
            trials=trials,
            converged=self.convergence_detector.get_convergence_rate() > 0.9,
            convergence_rate=self.convergence_detector.get_convergence_rate(),
            sensitivities=sensitivities
        )

    def _evaluate(
        self,
        params: Dict[str, Any],
        request: OptimizationRequest
    ) -> float:
        """评估参数"""
        # 选择评估器
        evaluators = self._get_evaluators(request)

        # 综合评估
        result = self.evaluator.evaluate(
            params, evaluators, request.goal
        )

        return result.overall_score

    def _should_stop(
        self,
        request: OptimizationRequest,
        trials: List[Dict],
        start_time: float
    ) -> bool:
        """判断是否应该停止"""
        # 时间限制
        if time.time() - start_time >= request.max_time:
            return True

        # 试验次数限制
        if len(trials) >= request.max_trials:
            return True

        return False

    def _analyze_sensitivity(
        self,
        optimizer: BaseOptimizer,
        request: OptimizationRequest
    ) -> Dict[str, float]:
        """分析参数敏感性"""
        analyzer = SensitivityAnalyzer(
            search_space=request.search_space,
            objective=lambda p: self._evaluate(p, request),
            base_params=optimizer.best_params
        )

        return analyzer.analyze(n_samples=50)
```

### CLI接口

```python
import click

@click.group()
def optimize():
    """参数优化命令"""
    pass

@optimize.command()
@click.option("--target", "-t", default=".", help="目标路径")
@click.option("--goal", "-g", type=click.Choice(["structure", "performance", "simplicity", "all"]),
              default="structure", help="优化目标")
@click.option("--max-time", type=float, default=120, help="最大时间（秒）")
@click.option("--max-trials", type=int, default=50, help="最大试验次数")
@click.option("--output", "-o", help="输出报告路径")
@click.option("--cache/--no-cache", default=True, help="启用缓存")
@click.option("--transfer/--no-transfer", default=True, help="启用知识迁移")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def run(target, goal, max_time, max_trials, output, cache, transfer, verbose):
    """运行参数优化"""
    from lingflow.self_optimizer.phase4 import OptimizationEngine, OptimizationRequest

    # 创建请求
    request = OptimizationRequest(
        target_path=target,
        goal=goal,
        search_space=_get_default_search_space(goal),
        max_time=max_time,
        max_trials=max_trials,
        enable_cache=cache,
        enable_transfer=transfer
    )

    # 创建引擎
    engine = OptimizationEngine()

    # 运行优化
    with click.progressbar(length=100, label="优化进度") as bar:
        result = engine.optimize(request)
        bar.update(100)

    # 输出结果
    _print_result(result, verbose)

    # 保存报告
    if output:
        _save_report(result, output)

@optimize.command()
@click.option("--project", "-p", help="项目名称")
@click.option("--goal", "-g", help="优化目标")
def best(project, goal):
    """查看最佳参数"""
    from lingflow.self_optimizer.phase4 import FileSystemParameterStore

    store = FileSystemParameterStore(Path.home() / ".lingflow" / "parameters")
    params = store.get_best_params(project or "default", goal or "structure")

    if params:
        click.echo("最佳参数:")
        for key, value in sorted(params.items()):
            click.echo(f"  {key}: {value}")
    else:
        click.echo("未找到保存的参数")

@optimize.command()
@click.option("--format", type=click.Choice(["json", "yaml", "table"]), default="table")
def history(format):
    """查看优化历史"""
    pass

@optimize.command()
@click.option("--goal", "-g", required=True, help="优化目标")
@click.option("--output", "-o", required=True, help="输出路径")
def export(goal, output):
    """导出最佳参数配置"""
    pass
```

---

## 集成策略

### 与现有系统集成

#### 1. 保持向后兼容

```python
# lingflow/self_optimizer/__init__.py
from lingflow.self_optimizer.optimizer import (
    ProcessIsolatedOptimizer,
    SynchronousOptimizer,
    OptimizationRequest as LegacyRequest,
    OptimizationResult as LegacyResult
)

# 新的Phase 4接口
from lingflow.self_optimizer.phase4 import (
    OptimizationEngine,
    OptimizationRequest,
    OptimizationResult
)

# 适配器：将旧接口转换为新接口
class LegacyOptimizerAdapter:
    """旧版优化器适配器"""

    def __init__(self, use_phase4: bool = True):
        self.use_phase4 = use_phase4

        if use_phase4:
            self.engine = OptimizationEngine()
        else:
            self.optimizer = SynchronousOptimizer()

    def optimize(self, request: LegacyRequest) -> LegacyResult:
        """适配优化接口"""
        if self.use_phase4:
            # 转换请求
            new_request = OptimizationRequest(
                target_path=request.target,
                goal=request.goal,
                search_space=_convert_search_space(request.goal),
                config=request.config
            )

            # 运行新优化器
            new_result = self.engine.optimize(new_request)

            # 转换结果
            return LegacyResult(
                success=new_result.error is None,
                best_params=new_result.best_params,
                best_score=new_result.best_score,
                experiments=new_result.n_trials,
                duration=new_result.total_time,
                history=new_result.trials
            )
        else:
            # 使用旧优化器
            return self.optimizer.optimize(request)
```

#### 2. 配置文件扩展

```yaml
# ~/.lingflow/config.yaml
# 现有配置保持不变...

# Phase 4 新增配置
phase4:
  enabled: true
  optimizer:
    algorithm: "bayesian"  # bayesian, random, grid
    backend: "optuna"      # optuna, skopt

  search_spaces:
    structure:
      max_class_size:
        type: "int"
        min: 100
        max: 500
        step: 50
      max_method_count:
        type: "categorical"
        choices: [10, 15, 20, 25]

  cache:
    enabled: true
    max_size: 1000
    ttl: 86400  # 24小时

  transfer:
    enabled: true
    similarity_threshold: 0.7

  convergence:
    window_size: 10
    threshold: 0.01
    min_trials: 20
```

#### 3. Hook集成

```python
# 在现有hook中集成Phase 4优化
def post_review_hook(context):
    """代码审查后hook"""
    # 检查是否启用Phase 4
    config = get_global_config()
    if config.get("phase4.enabled", False):
        from lingflow.self_optimizer.phase4 import OptimizationEngine

        engine = OptimizationEngine()
        # ... 运行优化
    else:
        # 使用旧版优化器
        from lingflow.self_optimizer import quick_optimize
        quick_optimize(...)
```

---

## 实施路线图

### 阶段1: 基础架构 (Week 1-2)

**目标**: 建立核心架构和基础组件

**任务**:
1. 创建新模块结构 `lingflow/self_optimizer/phase4/`
2. 实现参数存储后端（文件系统）
3. 实现参数缓存机制
4. 编写单元测试

**交付物**:
- `lingflow/self_optimizer/phase4/__init__.py`
- `lingflow/self_optimizer/phase4/storage.py`
- `lingflow/self_optimizer/phase4/cache.py`
- 单元测试覆盖率 >80%

**验收标准**:
- 可以保存和加载参数版本
- 缓存命中率 >50%
- 所有测试通过

### 阶段2: 贝叶斯优化器 (Week 3-4)

**目标**: 集成Optuna，实现智能优化

**任务**:
1. 集成Optuna库
2. 实现BayesianOptimizer类
3. 实现搜索空间定义
4. 实现收敛性检测

**交付物**:
- `lingflow/self_optimizer/phase4/optimizer.py`
- `lingflow/self_optimizer/phase4/search_space.py`
- 集成测试

**验收标准**:
- 优化时间减少 >50%
- 参数质量提升 >20%
- 与现有评估器兼容

### 阶段3: 多目标与敏感性分析 (Week 5-6)

**目标**: 实现高级优化功能

**任务**:
1. 实现MultiObjectiveOptimizer
2. 实现SensitivityAnalyzer
3. 实现KnowledgeTransfer
4. 实现ABTestFramework

**交付物**:
- `lingflow/self_optimizer/phase4/multi_objective.py`
- `lingflow/self_optimizer/phase4/sensitivity.py`
- `lingflow/self_optimizer/phase4/transfer.py`
- `lingflow/self_optimizer/phase4/ab_test.py`

**验收标准**:
- Pareto前沿正确计算
- 敏感性分析准确
- 跨项目迁移可用

### 阶段4: 集成与CLI (Week 7-8)

**目标**: 完成集成和用户界面

**任务**:
1. 实现OptimizationEngine主类
2. 实现CLI命令
3. 实现报告生成
4. 编写文档

**交付物**:
- `lingflow/self_optimizer/phase4/engine.py`
- `lingflow/cli.py` (更新)
- `docs/phase4-user-guide.md`
- 集成测试

**验收标准**:
- CLI命令完整可用
- 向后兼容性100%
- 文档完整

### 阶段5: 优化与部署 (Week 9-10)

**目标**: 性能优化和生产部署

**任务**:
1. 性能优化
2. 内存优化
3. 生产环境测试
4. 发布准备

**交付物**:
- 性能测试报告
- 部署指南
- v3.7.0发布

**验收标准**:
- 192类项目优化 <60秒
- 内存占用 <200MB
- 零重大bug

---

## 性能约束

### 时间约束

| 项目规模 | 类数量 | 目标时间 | 当前时间 | 改进 |
|----------|--------|----------|----------|------|
| 小型 | <50 | <20秒 | ~30秒 | 33% |
| 中型 | 50-150 | <45秒 | ~90秒 | 50% |
| 大型 | 150-200 | <60秒 | ~120秒 | 50% |

### 内存约束

- 峰值内存: <200MB
- 缓存大小: <50MB
- 参数历史: <10MB

### 质量约束

- 参数命中率: >60%
- 收敛准确率: >85%
- 跨项目迁移成功率: >50%

---

## 附录

### A. 搜索空间示例

```python
DEFAULT_SEARCH_SPACES = {
    "structure": {
        "max_class_size": {
            "type": "int",
            "min": 100,
            "max": 500,
            "step": 50
        },
        "max_method_count": {
            "type": "categorical",
            "choices": [10, 15, 20, 25]
        },
        "max_complexity": {
            "type": "int",
            "min": 5,
            "max": 20,
            "step": 5
        },
        "coupling_limit": {
            "type": "float",
            "min": 5.0,
            "max": 15.0,
            "step": 1.0
        }
    },
    "performance": {
        "cache_size": {
            "type": "categorical",
            "choices": [10, 50, 100, 500]
        },
        "parallelism": {
            "type": "int",
            "min": 1,
            "max": 4,
            "step": 1
        },
        "timeout": {
            "type": "categorical",
            "choices": [5, 10, 30, 60]
        }
    },
    "simplicity": {
        "complexity_threshold": {
            "type": "int",
            "min": 5,
            "max": 15,
            "step": 5
        },
        "duplication_penalty": {
            "type": "float",
            "min": 0.5,
            "max": 2.0,
            "step": 0.25
        },
        "max_line_length": {
            "type": "categorical",
            "choices": [80, 100, 120]
        }
    }
}
```

### B. 配置文件示例

```yaml
# ~/.lingflow/phase4-config.yaml

# 优化器配置
optimizer:
  # 算法选择: bayesian, random, grid
  algorithm: bayesian

  # 后端选择: optuna, skopt
  backend: optuna

  # 并行配置
  n_jobs: 1
  timeout: 120
  n_trials: 50

  # 早停配置
  early_stopping: true
  patience: 10
  min_improvement: 0.01

# 搜索空间配置
search_spaces:
  structure:
    max_class_size: {min: 100, max: 500, step: 50}
    max_method_count: {choices: [10, 15, 20, 25]}
    max_complexity: {min: 5, max: 20, step: 5}

# 缓存配置
cache:
  enabled: true
  max_size: 1000
  ttl: 86400  # 24小时

# 知识迁移配置
transfer:
  enabled: true
  similarity_threshold: 0.7
  max_sources: 5

# 收敛检测配置
convergence:
  window_size: 10
  threshold: 0.01
  min_trials: 20

# 日志配置
logging:
  level: INFO
  file: ~/.lingflow/phase4.log
```

### C. API参考

```python
# 快速开始
from lingflow.self_optimizer.phase4 import OptimizationEngine, OptimizationRequest

engine = OptimizationEngine()

request = OptimizationRequest(
    target_path="./my_project",
    goal="structure",
    search_space={"max_class_size": {"type": "int", "min": 100, "max": 500}},
    max_time=60
)

result = engine.optimize(request)
print(f"最佳参数: {result.best_params}")
print(f"最佳分数: {result.best_score}")
```

---

**文档版本**: v1.0
**最后更新**: 2026-03-31
**维护者**: LingFlow团队
