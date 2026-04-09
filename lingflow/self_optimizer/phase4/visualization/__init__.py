"""
LingFlow Phase 4: 参数优化可视化工具

提供参数优化过程和结果的可视化功能。

模块结构:
- visualizer: 主可视化类和便捷函数
- data_processor: 数据处理器
- charts: 图表生成器
"""

from lingflow.self_optimizer.phase4.visualization.charts import ChartGenerator
from lingflow.self_optimizer.phase4.visualization.data_processor import DataProcessor
from lingflow.self_optimizer.phase4.visualization.visualizer import (
    OptimizationVisualizer,
    plot_optimization_progress,
    plot_pareto_front,
    plot_sensitivity_heatmap,
)

__all__ = [
    # 主类
    "OptimizationVisualizer",
    # 便捷函数
    "plot_optimization_progress",
    "plot_sensitivity_heatmap",
    "plot_pareto_front",
    # 组件
    "DataProcessor",
    "ChartGenerator",
]
