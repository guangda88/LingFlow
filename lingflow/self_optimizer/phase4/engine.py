"""
LingFlow Phase 4: 优化引擎核心实现

整合贝叶斯优化、多目标优化、敏感性分析和可视化，
提供统一的优化接口。
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# 导入Phase 4模块
from lingflow.self_optimizer.phase4.bayesian_optimizer import create_optimizer, get_default_search_space
from lingflow.self_optimizer.phase4.multi_objective import optimize_multiple_objectives
from lingflow.self_optimizer.phase4.sensitivity import (
    analyze_sensitivity,
)
from lingflow.self_optimizer.phase4.visualization import (
    OptimizationVisualizer,
)

# 导入现有评估器
from lingflow.self_optimizer.evaluator import StructureEvaluator
from lingflow.self_optimizer.performance_evaluator import PerformanceEvaluator
from lingflow.self_optimizer.simplicity_evaluator import SimplicityEvaluator


class OptimizationEngine:
    """Phase 4 优化引擎

    统一的参数优化接口，整合所有Phase 4功能。
    """

    def __init__(self, config: Dict[str, Any] = None):
        """初始化优化引擎

        Args:
            config: 配置字典
        """
        self.config = config or {}

        # 初始化可视化器
        output_dir = self.config.get("output_dir", ".lingflow/reports")
        self.visualizer = OptimizationVisualizer(output_dir)

        # 优化历史
        self.optimization_history: List[Dict[str, Any]] = []

    def optimize_single_objective(
        self, target_path: str, goal: str = "structure", search_space: Dict[str, Any] = None, config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """单目标优化

        Args:
            target_path: 目标代码路径
            goal: 优化目标 (structure, performance, simplicity)
            search_space: 搜索空间（None使用默认）
            config: 优化配置

        Returns:
            优化结果字典
        """
        # 使用默认搜索空间
        if search_space is None:
            search_space = get_default_search_space(goal)

        # 创建评估器
        evaluator = self._create_evaluator(target_path, goal)

        # 创建目标函数
        def objective(params):
            return evaluator.evaluate(params)

        # 合并配置
        opt_config = {**self.config, **(config or {})}

        # 创建优化器
        optimizer = create_optimizer(search_space, objective, opt_config)

        # 运行优化
        logger.info(f"开始{goal}优化...")
        state = optimizer.optimize()

        # 记录历史
        result = {
            "goal": goal,
            "target_path": target_path,
            "best_params": state.get_best_params(),
            "best_score": state.get_best_score(),
            "n_trials": state.current_trial,
            "convergence_rate": state.convergence_rate,
            "total_time": optimizer.get_total_time(),
            "search_space": search_space,
            "timestamp": datetime.now().isoformat(),
        }

        self.optimization_history.append(result)

        # 生成可视化报告
        if self.config.get("generate_reports", True):
            report_path = self.visualizer.generate_html_report(state, search_space, {"goal": goal, "target_path": target_path})
            result["report_path"] = report_path

        logger.info(f"优化完成: {result['best_score']:.4f}")

        return result

    def optimize_multi_objective(
        self,
        target_path: str,
        goals: List[str] = None,
        weights: Dict[str, float] = None,
        search_space: Dict[str, Any] = None,
        config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """多目标优化

        Args:
            target_path: 目标代码路径
            goals: 目标列表 (默认: ["structure", "performance", "simplicity"])
            weights: 目标权重
            search_space: 搜索空间
            config: 配置

        Returns:
            多目标优化结果
        """
        if goals is None:
            goals = ["structure", "performance", "simplicity"]

        if weights is None:
            weights = {goal: 1.0 for goal in goals}

        # 构建搜索空间（合并所有目标的搜索空间）
        if search_space is None:
            search_space = {}
            for goal in goals:
                goal_space = get_default_search_space(goal)
                search_space.update(goal_space)

        # 创建目标函数
        objectives = {}
        for goal in goals:
            evaluator = self._create_evaluator(target_path, goal)
            objectives[goal] = lambda p, e=evaluator: e.evaluate(p)

        # 合并配置
        opt_config = {
            "max_evaluations": self.config.get("max_evaluations", 200),
            "timeout": self.config.get("timeout", 300),
            **(config or {}),
        }

        # 运行多目标优化
        logger.info(f"开始多目标优化: {goals}")
        result = optimize_multiple_objectives(
            search_space=search_space, objectives=objectives, weights=weights, config=opt_config
        )

        # 记录历史
        summary = {
            "type": "multi_objective",
            "goals": goals,
            "weights": weights,
            "target_path": target_path,
            "n_evaluations": result.n_evaluations,
            "total_time": result.total_time,
            "converged": result.converged,
            "pareto_front_size": len(result.get_pareto_front()),
            "timestamp": datetime.now().isoformat(),
        }

        self.optimization_history.append(summary)

        # 生成Pareto前沿可视化
        if self.config.get("generate_reports", True):
            try:
                report_path = self.visualizer.generate_pareto_front_plot(result)
                summary["report_path"] = report_path
            except Exception as e:
                logger.error(f"生成Pareto前沿图失败: {e}")

        # 获取平衡解
        balanced = result.get_balanced_solution()
        if balanced:
            summary["balanced_solution"] = {
                "params": balanced.params,
                "objectives": balanced.objectives,
                "aggregated_score": balanced.aggregated_score,
            }

        logger.info(f"多目标优化完成，找到 {len(result.get_pareto_front())} 个Pareto解")

        return summary

    def analyze_sensitivity(
        self,
        target_path: str,
        goal: str = "structure",
        base_params: Dict[str, Any] = None,
        method: str = "local",
        n_samples: int = 50,
    ) -> Dict[str, Any]:
        """参数敏感性分析

        Args:
            target_path: 目标代码路径
            goal: 优化目标
            base_params: 基线参数
            method: 分析方法 (local, sobol, morris)
            n_samples: 样本数

        Returns:
            敏感性分析结果
        """
        # 获取搜索空间
        search_space = get_default_search_space(goal)

        # 创建评估器
        evaluator = self._create_evaluator(target_path, goal)

        # 创建目标函数
        def objective(params):
            return evaluator.evaluate(params)

        # 运行敏感性分析
        logger.info(f"开始参数敏感性分析 ({method})...")
        sensitivity_result = analyze_sensitivity(
            search_space=search_space, objective=objective, base_params=base_params, method=method, n_samples=n_samples
        )

        # 处理结果
        if method == "local":
            # 局部敏感性
            summary = {"method": method, "goal": goal, "target_path": target_path, "parameters": {}}

            for param_name, result in sensitivity_result.items():
                summary["parameters"][param_name] = {
                    "sensitivity_score": result.sensitivity_score,
                    "baseline_value": result.baseline_value,
                }

            # 生成可视化
            if self.config.get("generate_reports", True):
                try:
                    report_path = self.visualizer.generate_sensitivity_heatmap(sensitivity_result)
                    summary["report_path"] = report_path
                except Exception as e:
                    logger.error(f"生成敏感性图失败: {e}")

        elif method == "sobol":
            # Sobol全局敏感性
            summary = {
                "method": method,
                "goal": goal,
                "target_path": target_path,
                "first_order": sensitivity_result.first_order,
                "total_order": sensitivity_result.total_order,
                "most_sensitive": sensitivity_result.get_most_sensitive(5),
            }

        else:
            summary = {"method": method, "result": sensitivity_result}

        logger.info("敏感性分析完成")

        return summary

    def _create_evaluator(self, target_path: str, goal: str):
        """创建评估器

        Args:
            target_path: 目标路径
            goal: 优化目标

        Returns:
            评估器实例
        """
        if goal == "structure":
            return StructureEvaluator(target_path)
        elif goal == "performance":
            return PerformanceEvaluator(target_path)
        elif goal == "simplicity":
            return SimplicityEvaluator(target_path)
        else:
            raise ValueError(f"未知的优化目标: {goal}")

    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """获取优化历史"""
        return self.optimization_history.copy()

    def clear_history(self) -> None:
        """清空优化历史"""
        self.optimization_history.clear()


# 便捷函数
def quick_optimize(
    target_path: str = ".", goal: str = "structure", use_bayesian: bool = True, generate_report: bool = True
) -> Dict[str, Any]:
    """快速优化（便捷函数）

    Args:
        target_path: 目标路径
        goal: 优化目标
        use_bayesian: 是否使用贝叶斯优化
        generate_report: 是否生成报告

    Returns:
        优化结果
    """
    config = {"generate_reports": generate_report, "n_trials": 50, "timeout": 120}

    engine = OptimizationEngine(config)
    return engine.optimize_single_objective(target_path, goal)


def quick_multi_optimize(target_path: str = ".", goals: List[str] = None, weights: Dict[str, float] = None) -> Dict[str, Any]:
    """快速多目标优化（便捷函数）

    Args:
        target_path: 目标路径
        goals: 目标列表
        weights: 权重

    Returns:
        多目标优化结果
    """
    config = {"generate_reports": True}

    engine = OptimizationEngine(config)
    return engine.optimize_multi_objective(target_path, goals, weights)


def quick_sensitivity_analysis(target_path: str = ".", goal: str = "structure", method: str = "local") -> Dict[str, Any]:
    """快速敏感性分析（便捷函数）

    Args:
        target_path: 目标路径
        goal: 优化目标
        method: 分析方法

    Returns:
        敏感性分析结果
    """
    config = {"generate_reports": True}

    engine = OptimizationEngine(config)
    return engine.analyze_sensitivity(target_path, goal, method=method)


if __name__ == "__main__":
    # 测试
    import sys

    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = "."

    goal = sys.argv[2] if len(sys.argv) > 2 else "structure"

    print(f"开始优化: {target_path} (目标: {goal})")

    result = quick_optimize(target_path, goal)

    print(f"""
优化结果:
  最佳分数: {result['best_score']:.4f}
  试验次数: {result['n_trials']}
  收敛率: {result['convergence_rate']:.2%}
  耗时: {result['total_time']:.2f}秒

最佳参数:
""")
    for param, value in result["best_params"].items():
        print(f"  {param}: {value}")

    if result.get("report_path"):
        print(f"\n报告已生成: {result['report_path']}")
