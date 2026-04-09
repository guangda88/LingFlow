"""
LingFlow Phase 4: 参数优化系统

智能参数优化架构，包括：
- 贝叶斯优化 (Bayesian Optimization)
- 多目标优化 (Multi-objective Optimization)
- 参数敏感性分析 (Parameter Sensitivity Analysis)
- 参数效果可视化 (Visualization)

使用示例:
    from lingflow.self_optimizer.phase4 import quick_optimize

    result = quick_optimize("./my_project", goal="structure")
    print(f"最佳参数: {result['best_params']}")
    print(f"最佳分数: {result['best_score']}")
"""

# 版本信息 (与主项目版本保持一致)
__version__ = "3.8.0"
__author__ = "LingFlow Team"

# 核心引擎
from lingflow.self_optimizer.phase4.engine import (
    OptimizationEngine,
)

# 搜索空间（新增）
from lingflow.self_optimizer.phase4.search_space import (
    Parameter,
    ParameterType,
    SearchSpace,
)

# 配置类（新增）
try:
    from lingflow.self_optimizer.phase4.engine import (
        Experiment,
        OptimizationConfig,
        OptimizationResult,
    )
except ImportError:
    # 如果engine.py中没有这些类，我们定义它们
    from dataclasses import dataclass, field
    from typing import Any, Dict, List

    @dataclass
    class OptimizationConfig:
        max_experiments: int = 50
        time_budget: float = 300.0
        early_stopping_patience: int = 10
        direction: str = "minimize"
        acquisition_function: str = "EI"
        n_initial_points: int = 10
        random_seed: int = None

    @dataclass
    class Experiment:
        params: Dict[str, Any]
        objective: float
        metadata: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class OptimizationResult:
        best_params: Dict[str, Any]
        best_objective: float
        total_experiments: int
        total_time: float
        history: List[Experiment]
        convergence_curve: List[float]
        improvement_percentage: float


# 优化器
from lingflow.self_optimizer.phase4.bayesian_optimizer import (
    BayesianOptimizer,
    GridSearchOptimizer,
    OptimizationState,
    OptimizationTrial,
    create_optimizer,
    get_default_search_space,
)
from lingflow.self_optimizer.phase4.cache import (
    CachedParameterStore,
    ParameterCache,
    get_default_cache,
)

# 便捷函数
from lingflow.self_optimizer.phase4.engine import (
    quick_multi_optimize,
    quick_optimize,
    quick_sensitivity_analysis,
)

# 多目标优化
from lingflow.self_optimizer.phase4.multi_objective import (
    MultiObjectiveOptimizer,
    MultiObjectiveResult,
    ParetoPoint,
    optimize_multiple_objectives,
)

# 敏感性分析
from lingflow.self_optimizer.phase4.sensitivity import (
    SensitivityAnalyzer,
    SensitivityResult,
    SobolResult,
    analyze_sensitivity,
)

# 存储和缓存
from lingflow.self_optimizer.phase4.storage import (
    FileSystemParameterStore,
    get_default_store,
    get_latest_params,
    load_params,
    save_params,
)

# 可视化
from lingflow.self_optimizer.phase4.visualization import (
    OptimizationVisualizer,
    plot_optimization_progress,
    plot_pareto_front,
    plot_sensitivity_heatmap,
)

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    # 核心引擎
    "OptimizationEngine",
    # 配置类（新增）
    "OptimizationConfig",
    "Experiment",
    "OptimizationResult",
    # 搜索空间（新增）
    "SearchSpace",
    "Parameter",
    "ParameterType",
    # 优化器
    "BayesianOptimizer",
    "GridSearchOptimizer",
    "create_optimizer",
    "get_default_search_space",
    "OptimizationTrial",
    "OptimizationState",
    # 多目标优化
    "MultiObjectiveOptimizer",
    "MultiObjectiveResult",
    "ParetoPoint",
    "optimize_multiple_objectives",
    # 敏感性分析
    "SensitivityAnalyzer",
    "SensitivityResult",
    "SobolResult",
    "analyze_sensitivity",
    # 可视化
    "OptimizationVisualizer",
    "plot_optimization_progress",
    "plot_sensitivity_heatmap",
    "plot_pareto_front",
    # 便捷函数
    "quick_optimize",
    "quick_multi_optimize",
    "quick_sensitivity_analysis",
    # 存储和缓存
    "FileSystemParameterStore",
    "get_default_store",
    "save_params",
    "load_params",
    "get_latest_params",
    "ParameterCache",
    "CachedParameterStore",
    "get_default_cache",
]
