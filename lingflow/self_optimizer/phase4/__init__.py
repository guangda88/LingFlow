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

# 版本信息
__version__ = "4.0.0-alpha"
__author__ = "LingFlow Team"

# 核心引擎
from lingflow.self_optimizer.phase4.engine import (
    OptimizationEngine,
)

# 优化器
from lingflow.self_optimizer.phase4.bayesian_optimizer import (
    BayesianOptimizer,
    GridSearchOptimizer,
    create_optimizer,
    get_default_search_space,
)

from lingflow.self_optimizer.phase4.bayesian_optimizer import (
    OptimizationTrial,
    OptimizationState,
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

# 可视化
from lingflow.self_optimizer.phase4.visualization import (
    OptimizationVisualizer,
    plot_optimization_progress,
    plot_sensitivity_heatmap,
    plot_pareto_front,
)

# 存储和缓存
from lingflow.self_optimizer.phase4.storage import (
    FileSystemParameterStore,
    get_default_store,
    save_params,
    load_params,
    get_latest_params,
)

from lingflow.self_optimizer.phase4.cache import (
    ParameterCache,
    CachedParameterStore,
    get_default_cache,
)

# 便捷函数
from lingflow.self_optimizer.phase4.engine import (
    quick_optimize,
    quick_multi_optimize,
    quick_sensitivity_analysis,
)


__all__ = [
    # 版本信息
    "__version__",
    "__author__",

    # 核心引擎
    "OptimizationEngine",

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
