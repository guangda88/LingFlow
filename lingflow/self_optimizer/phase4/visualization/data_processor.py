"""
LingFlow Phase 4: 可视化数据处理器

负责从优化状态和结果中提取和处理可视化数据。
"""

from datetime import datetime
from typing import Any, Dict, List


class DataProcessor:
    """可视化数据处理器

    从优化状态中提取和转换数据用于可视化。
    """

    @staticmethod
    def extract_trial_data(history: List) -> Dict[str, Any]:
        """提取试验数据

        Args:
            history: 优化历史记录

        Returns:
            包含试验ID和分数的字典
        """
        scores = [t.score for t in history]
        trial_ids = list(range(1, len(history) + 1))

        return {"trials": trial_ids, "scores": scores, "count": len(history)}

    @staticmethod
    def extract_best_params(optimization_state) -> Dict[str, Any]:
        """提取最佳参数

        Args:
            optimization_state: 优化状态对象

        Returns:
            最佳参数字典
        """
        return optimization_state.get_best_params()

    @staticmethod
    def extract_best_score(optimization_state) -> float:
        """提取最佳分数

        Args:
            optimization_state: 优化状态对象

        Returns:
            最佳分数
        """
        return optimization_state.get_best_score()

    @staticmethod
    def extract_convergence_data(optimization_state) -> Dict[str, Any]:
        """提取收敛数据

        Args:
            optimization_state: 优化状态对象

        Returns:
            收敛率字典
        """
        return {"rate": optimization_state.convergence_rate, "is_converged": optimization_state.convergence_rate > 0.9}

    @staticmethod
    def extract_sensitivity_data(sensitivity_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取敏感性分析数据

        Args:
            sensitivity_results: 敏感性分析结果

        Returns:
            敏感性数据字典
        """
        parameters = list(sensitivity_results.keys())
        scores = [sensitivity_results[p].sensitivity_score for p in parameters]

        return {"parameters": parameters, "scores": scores}

    @staticmethod
    def extract_pareto_data(pareto_result) -> Dict[str, Any]:
        """提取Pareto前沿数据

        Args:
            pareto_result: 多目标优化结果

        Returns:
            Pareto前沿数据字典
        """
        pareto_points = pareto_result.get_pareto_front()

        if not pareto_points:
            return {"points": [], "objective_names": []}

        objective_names = list(pareto_points[0].objectives.keys())

        return {"points": pareto_points, "objective_names": objective_names, "all_evaluated": pareto_result.all_evaluated}

    @staticmethod
    def get_timestamp() -> str:
        """获取时间戳字符串

        Returns:
            格式化的时间戳
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    @staticmethod
    def get_timestamp_readable() -> str:
        """获取可读时间戳

        Returns:
            可读格式的时间戳
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
