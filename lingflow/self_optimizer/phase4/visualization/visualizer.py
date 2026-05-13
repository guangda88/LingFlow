"""
lingflow Phase 4: 主可视化类

协调数据处理器和图表生成器，提供统一的可视化接口。
"""

import logging
from pathlib import Path
from typing import Any, Dict

from lingflow.self_optimizer.phase4.visualization.charts import ChartGenerator
from lingflow.self_optimizer.phase4.visualization.data_processor import DataProcessor

logger = logging.getLogger(__name__)


class OptimizationVisualizer:
    """优化可视化器

    生成优化过程和结果的可视化报告。
    """

    def __init__(self, output_dir: str = ".lingflow/reports"):
        """初始化可视化器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_processor = DataProcessor()
        self.chart_generator = ChartGenerator()

    def generate_html_report(self, optimization_state, search_space: Dict[str, Any], metadata: Dict[str, Any] = None) -> str:
        """生成HTML报告

        Args:
            optimization_state: 优化状态对象
            search_space: 搜索空间
            metadata: 元数据

        Returns:
            生成的HTML文件路径
        """
        # 提取数据
        history = optimization_state.history
        best_params = self.data_processor.extract_best_params(optimization_state)
        best_score = self.data_processor.extract_best_score(optimization_state)
        convergence_data = self.data_processor.extract_convergence_data(optimization_state)
        timestamp_readable = self.data_processor.get_timestamp_readable()

        # 生成HTML
        html = self.chart_generator.generate_optimization_html(
            history=history,
            best_params=best_params,
            best_score=best_score,
            convergence_rate=convergence_data["rate"],
            search_space=search_space,
            metadata=metadata or {},
            timestamp_readable=timestamp_readable,
        )

        # 保存文件
        timestamp = self.data_processor.get_timestamp()
        output_file = self.output_dir / f"optimization_report_{timestamp}.html"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"HTML报告已生成: {output_file}")
        return str(output_file)

    def generate_sensitivity_heatmap(self, sensitivity_results: Dict[str, Any], output_file: str = None) -> str:
        """生成敏感性热力图

        Args:
            sensitivity_results: 敏感性分析结果
            output_file: 输出文件名

        Returns:
            生成的HTML文件路径
        """
        if output_file is None:
            output_file = self.output_dir / f"sensitivity_heatmap_{self.data_processor.get_timestamp()}.html"

        # 提取数据
        sensitivity_data = self.data_processor.extract_sensitivity_data(sensitivity_results)

        # 生成HTML
        html = self.chart_generator.generate_sensitivity_html(
            parameters=sensitivity_data["parameters"], scores=sensitivity_data["scores"]
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"敏感性热力图已生成: {output_file}")
        return str(output_file)

    def generate_pareto_front_plot(self, pareto_result, output_file: str = None) -> str:
        """生成Pareto前沿图

        Args:
            pareto_result: 多目标优化结果
            output_file: 输出文件名

        Returns:
            生成的HTML文件路径
        """
        if output_file is None:
            output_file = self.output_dir / f"pareto_front_{self.data_processor.get_timestamp()}.html"

        # 提取Pareto前沿数据
        pareto_data = self.data_processor.extract_pareto_data(pareto_result)

        if not pareto_data["points"]:
            logger.warning("没有Pareto前沿数据")
            return ""

        # 生成HTML
        html = self.chart_generator.generate_pareto_html(
            pareto_points=pareto_data["points"],
            objective_names=pareto_data["objective_names"],
            all_evaluated=pareto_data["all_evaluated"],
        )

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Pareto前沿图已生成: {output_file}")
        return str(output_file)


# 便捷函数
def plot_optimization_progress(optimization_state, search_space: Dict[str, Any], output_dir: str = ".lingflow/reports") -> str:
    """绘制优化进度图（便捷函数）"""
    visualizer = OptimizationVisualizer(output_dir)
    return visualizer.generate_html_report(optimization_state, search_space)


def plot_sensitivity_heatmap(sensitivity_results: Dict[str, Any], output_dir: str = ".lingflow/reports") -> str:
    """绘制敏感性热力图（便捷函数）"""
    visualizer = OptimizationVisualizer(output_dir)
    return visualizer.generate_sensitivity_heatmap(sensitivity_results)


def plot_pareto_front(pareto_result, output_dir: str = ".lingflow/reports") -> str:
    """绘制Pareto前沿图（便捷函数）"""
    visualizer = OptimizationVisualizer(output_dir)
    return visualizer.generate_pareto_front_plot(pareto_result)
