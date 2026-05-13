"""
lingflow Phase 4: 多目标优化器实现

支持同时优化多个目标（代码质量、性能、简洁性），
使用Pareto前沿方法找到非支配解集。
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ParetoPoint:
    """Pareto前沿点"""

    params: Dict[str, Any]
    objectives: Dict[str, float]  # 目标名称 -> 值
    aggregated_score: float
    dominated: bool = False
    timestamp: float = field(default_factory=time.time)

    def dominates(self, other: "ParetoPoint") -> bool:
        """判断当前点是否支配另一个点

        当前点支配另一个点，当且仅当：
        - 所有目标都不比另一个点差
        - 至少有一个目标比另一个点好

        假设所有目标都是最小化（越小越好）
        """
        at_least_one_better = False

        for obj_name, obj_value in self.objectives.items():
            other_value = other.objectives.get(obj_name, float("inf"))

            if obj_value > other_value:
                return False  # 有一个目标更差，不支配
            elif obj_value < other_value:
                at_least_one_better = True  # 至少有一个更好

        return at_least_one_better

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "params": self.params,
            "objectives": self.objectives,
            "aggregated_score": self.aggregated_score,
            "dominated": self.dominated,
        }


@dataclass
class MultiObjectiveResult:
    """多目标优化结果"""

    pareto_front: List[ParetoPoint]
    all_evaluated: List[ParetoPoint]
    n_evaluations: int
    total_time: float
    converged: bool

    def get_pareto_front(self) -> List[ParetoPoint]:
        """获取Pareto前沿（非支配解）"""
        return [p for p in self.pareto_front if not p.dominated]

    def get_best_by_objective(self, objective_name: str) -> Optional[ParetoPoint]:
        """根据特定目标获取最佳解"""
        candidates = self.get_pareto_front()
        if not candidates:
            return None

        return min(candidates, key=lambda p: p.objectives.get(objective_name, float("inf")))

    def get_balanced_solution(self) -> Optional[ParetoPoint]:
        """获取平衡解（所有目标的加权和最小）"""
        candidates = self.get_pareto_front()
        if not candidates:
            return None

        return min(candidates, key=lambda p: p.aggregated_score)

    def get_summary(self) -> str:
        """获取摘要"""
        pareto_solutions = self.get_pareto_front()

        summary = f"""
多目标优化结果摘要:
  评估次数: {self.n_evaluations}
  耗时: {self.total_time:.2f}秒
  Pareto前沿解数: {len(pareto_solutions)}
  收敛状态: {'是' if self.converged else '否'}

Pareto前沿目标范围:
"""

        if pareto_solutions:
            # 计算每个目标的范围
            for obj_name in pareto_solutions[0].objectives.keys():
                values = [p.objectives[obj_name] for p in pareto_solutions]
                summary += f"  {obj_name}: [{min(values):.4f}, {max(values):.4f}]\n"

        return summary.strip()


class MultiObjectiveOptimizer:
    """多目标优化器

    使用加权聚合方法和Pareto前沿分析处理多个优化目标。
    """

    def __init__(
        self,
        search_space: Dict[str, Any],
        objectives: Dict[str, Callable[[Dict[str, Any]], float]],
        weights: Optional[Dict[str, float]] = None,
        config: Dict[str, Any] = None,
    ):
        """初始化多目标优化器

        Args:
            search_space: 搜索空间定义
            objectives: 目标函数字典
                例如: {
                    "quality": lambda p: quality_fn(p),
                    "performance": lambda p: perf_fn(p),
                    "simplicity": lambda p: simplicity_fn(p)
                }
            weights: 目标权重（可选）
            config: 配置字典
        """
        self.search_space = search_space
        self.objectives = objectives
        self.weights = weights or {name: 1.0 for name in objectives}
        self.config = config or {}

        # 优化配置
        self.max_evaluations = self.config.get("max_evaluations", 200)
        self.timeout = self.config.get("timeout", 300)
        self.pareto_epsilon = self.config.get("pareto_epsilon", 0.01)

        # 内部状态
        self.pareto_front: List[ParetoPoint] = []
        self.all_evaluated: List[ParetoPoint] = []
        self.evaluation_count = 0
        self.start_time = None

    def evaluate_all_objectives(self, params: Dict[str, Any]) -> Dict[str, float]:
        """评估所有目标

        Args:
            params: 参数字典

        Returns:
            所有目标的分数
        """
        results = {}
        for name, objective_fn in self.objectives.items():
            try:
                score = objective_fn(params)
                results[name] = score
            except Exception as e:
                logger.error(f"评估目标 {name} 失败: {e}")
                results[name] = float("inf")

        return results

    def calculate_aggregated_score(self, objectives: Dict[str, float]) -> float:
        """计算加权聚合分数

        Args:
            objectives: 目标分数字典

        Returns:
            加权分数
        """
        total = 0.0
        total_weight = 0.0

        for name, value in objectives.items():
            weight = self.weights.get(name, 1.0)
            total += value * weight
            total_weight += weight

        return total / total_weight if total_weight > 0 else 0.0

    def update_pareto_front(self, point: ParetoPoint) -> None:
        """更新Pareto前沿

        Args:
            point: 新评估的点
        """
        # 检查新点是否被现有点支配
        for existing in self.pareto_front:
            if existing.dominates(point):
                point.dominated = True
                break

        # 如果新点不被支配，移除被新点支配的现有点
        if not point.dominated:
            to_remove = []
            for existing in self.pareto_front:
                if point.dominates(existing):
                    to_remove.append(existing)

            for p in to_remove:
                self.pareto_front.remove(p)

            # 添加新点到前沿
            self.pareto_front.append(point)

    def optimize(self) -> MultiObjectiveResult:
        """运行多目标优化

        Returns:
            多目标优化结果
        """
        self.start_time = time.time()

        # 使用底层优化器进行搜索
        from lingflow.self_optimizer.phase4.bayesian_optimizer import create_optimizer

        # 创建聚合目标函数
        def aggregated_objective(params):
            objectives = self.evaluate_all_objectives(params)
            return self.calculate_aggregated_score(objectives)

        # 创建优化器
        optimizer_config = {"n_trials": self.max_evaluations, "timeout": self.timeout, "early_stopping_patience": 20}

        optimizer = create_optimizer(self.search_space, aggregated_objective, optimizer_config)

        # 运行优化
        state = optimizer.optimize()

        # 收集所有评估点
        for trial in state.history:
            # 重新评估所有目标
            all_objectives = self.evaluate_all_objectives(trial.params)
            aggregated = self.calculate_aggregated_score(all_objectives)

            point = ParetoPoint(
                params=trial.params.copy(), objectives=all_objectives, aggregated_score=aggregated, timestamp=trial.timestamp
            )

            self.all_evaluated.append(point)
            self.update_pareto_front(point)
            self.evaluation_count += 1

        # 判断收敛
        converged = state.convergence_rate > 0.9

        return MultiObjectiveResult(
            pareto_front=self.pareto_front.copy(),
            all_evaluated=self.all_evaluated.copy(),
            n_evaluations=self.evaluation_count,
            total_time=time.time() - self.start_time,
            converged=converged,
        )


class NSGA2Optimizer:
    """NSGA-II优化器实现

    NSGA-II (Non-dominated Sorting Genetic Algorithm II)
    是一种经典的多目标优化算法。

    这里提供一个简化实现。
    """

    def __init__(
        self,
        search_space: Dict[str, Any],
        objectives: Dict[str, Callable[[Dict[str, Any]], float]],
        config: Dict[str, Any] = None,
    ):
        """初始化NSGA-II优化器"""
        self.search_space = search_space
        self.objectives = objectives
        self.config = config or {}

        self.population_size = self.config.get("population_size", 50)
        self.max_generations = self.config.get("max_generations", 100)
        self.mutation_rate = self.config.get("mutation_rate", 0.1)

    def _fast_non_dominated_sort(self, population: List[ParetoPoint]) -> List[List[ParetoPoint]]:
        """快速非支配排序

        将种群分为多个前沿面
        """
        fronts = []
        current_front = []

        # 计算每个点的支配数和被支配集合
        for p in population:
            p.domination_count = 0
            p.dominated_solutions = []

            for q in population:
                if p.dominates(q):
                    p.dominated_solutions.append(q)
                elif q.dominates(p):
                    p.domination_count += 1

            if p.domination_count == 0:
                p.rank = 0
                current_front.append(p)

        fronts.append(current_front)

        # 构建后续前沿面
        while current_front:
            next_front = []

            for p in current_front:
                for q in p.dominated_solutions:
                    q.domination_count -= 1
                    if q.domination_count == 0:
                        q.rank = len(fronts)
                        next_front.append(q)

            if next_front:
                fronts.append(next_front)

            current_front = next_front

        return fronts

    def _calculate_crowding_distance(self, front: List[ParetoPoint]) -> None:
        """计算拥挤距离

        用于维护前沿面的多样性
        """
        if not front:
            return

        # 初始化拥挤距离
        for p in front:
            p.crowding_distance = 0.0

        # 对每个目标计算拥挤距离

        for obj_name in front[0].objectives.keys():
            # 按该目标排序
            sorted_front = sorted(front, key=lambda p: p.objectives[obj_name])

            # 边界点设为无穷大
            sorted_front[0].crowding_distance = float("inf")
            sorted_front[-1].crowding_distance = float("inf")

            # 计算中间点的拥挤距离
            obj_range = sorted_front[-1].objectives[obj_name] - sorted_front[0].objectives[obj_name]

            if obj_range == 0:
                continue

            for i in range(1, len(sorted_front) - 1):
                distance = (sorted_front[i + 1].objectives[obj_name] - sorted_front[i - 1].objectives[obj_name]) / obj_range
                sorted_front[i].crowding_distance += distance

    def optimize(self) -> MultiObjectiveResult:
        """运行NSGA-II优化"""
        # 简化实现：使用随机采样 + Pareto过滤

        pareto_front: List[ParetoPoint] = []
        all_evaluated: List[ParetoPoint] = []

        for _ in range(self.max_generations * self.population_size):
            # 随机采样参数
            params = self._random_sample()
            objectives = self.evaluate_all_objectives(params)
            aggregated = sum(objectives.values()) / len(objectives)

            point = ParetoPoint(params=params, objectives=objectives, aggregated_score=aggregated)

            all_evaluated.append(point)
            self.update_pareto_front(point, pareto_front)

        return MultiObjectiveResult(
            pareto_front=pareto_front,
            all_evaluated=all_evaluated,
            n_evaluations=len(all_evaluated),
            total_time=0.0,
            converged=False,
        )

    def _random_sample(self) -> Dict[str, Any]:
        """随机采样参数"""
        import random

        params = {}

        for name, space in self.search_space.items():
            space_type = space.get("type")

            if space_type == "categorical":
                params[name] = random.choice(space["choices"])
            elif space_type == "int":
                params[name] = random.randint(space["min"], space["max"])
            elif space_type == "float":
                params[name] = random.uniform(space["min"], space["max"])

        return params

    def evaluate_all_objectives(self, params: Dict[str, Any]) -> Dict[str, float]:
        """评估所有目标"""
        results = {}
        for name, objective_fn in self.objectives.items():
            try:
                score = objective_fn(params)
                results[name] = score
            except Exception as e:
                logger.error(f"评估目标 {name} 失败: {e}")
                results[name] = float("inf")

        return results

    def update_pareto_front(self, point: ParetoPoint, front: List[ParetoPoint]) -> None:
        """更新Pareto前沿"""
        for existing in front:
            if existing.dominates(point):
                point.dominated = True
                break

        if not point.dominated:
            to_remove = [p for p in front if point.dominates(p)]
            for p in to_remove:
                front.remove(p)
            front.append(point)


# 便捷函数
def optimize_multiple_objectives(
    search_space: Dict[str, Any],
    objectives: Dict[str, Callable],
    weights: Dict[str, float] = None,
    config: Dict[str, Any] = None,
) -> MultiObjectiveResult:
    """多目标优化便捷函数

    Args:
        search_space: 搜索空间
        objectives: 目标函数字典
        weights: 权重字典
        config: 配置

    Returns:
        多目标优化结果
    """
    optimizer = MultiObjectiveOptimizer(search_space=search_space, objectives=objectives, weights=weights, config=config)

    return optimizer.optimize()


if __name__ == "__main__":  # pragma: no cover
    # 测试
    def quality_obj(params):
        """质量目标：越小越好"""
        x = params.get("x", 0)
        return (x - 2) ** 2

    def performance_obj(params):
        """性能目标：越小越好"""
        y = params.get("y", 0)
        return (y - 3) ** 2

    search_space = {"x": {"type": "float", "min": 0, "max": 10}, "y": {"type": "float", "min": 0, "max": 10}}

    objectives = {"quality": quality_obj, "performance": performance_obj}

    weights = {"quality": 0.6, "performance": 0.4}

    config = {"max_evaluations": 100, "timeout": 30}

    result = optimize_multiple_objectives(search_space, objectives, weights, config)

    print(result.get_summary())

    # 获取平衡解
    balanced = result.get_balanced_solution()
    if balanced:
        print(f"\n平衡解: {balanced.params}")
        print(f"目标值: {balanced.objectives}")
