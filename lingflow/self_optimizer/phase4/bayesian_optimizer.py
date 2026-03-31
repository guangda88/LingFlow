"""
LingFlow Phase 4: 贝叶斯优化器实现

使用Optuna的TPE (Tree-structured Parzen Estimator) 算法
实现高效的参数搜索，相比网格搜索可减少50%以上的评估次数。
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class OptimizationTrial:
    """优化试验记录"""
    trial_id: str
    params: Dict[str, Any]
    score: float
    metrics: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    converged: bool = False
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trial_id": self.trial_id,
            "params": self.params,
            "score": self.score,
            "metrics": self.metrics,
            "timestamp": self.timestamp,
            "converged": self.converged,
            "duration": self.duration
        }


@dataclass
class OptimizationState:
    """优化状态"""
    current_trial: int
    best_trial: OptimizationTrial
    convergence_rate: float
    should_stop: bool = False
    history: List[OptimizationTrial] = field(default_factory=list)

    def get_best_score(self) -> float:
        """获取最佳分数"""
        return self.best_trial.score

    def get_best_params(self) -> Dict[str, Any]:
        """获取最佳参数"""
        return self.best_trial.params


class BayesianOptimizer:
    """贝叶斯优化器

    使用Optuna的TPE算法进行高效的参数搜索。
    """

    def __init__(
        self,
        search_space: Dict[str, Any],
        objective: Callable[[Dict[str, Any]], float],
        config: Dict[str, Any] = None
    ):
        """初始化贝叶斯优化器

        Args:
            search_space: 搜索空间定义
                例如: {
                    "max_class_size": {"type": "int", "min": 100, "max": 500},
                    "max_method_count": {"type": "categorical", "choices": [10, 15, 20]}
                }
            objective: 目标函数，接收参数字典，返回分数（越小越好）
            config: 配置字典
        """
        self.search_space = search_space
        self.objective = objective
        self.config = config or {}

        # 优化配置
        self.n_trials = self.config.get("n_trials", 50)
        self.timeout = self.config.get("timeout", 120)
        self.early_stopping_patience = self.config.get("early_stopping_patience", 10)
        self.min_improvement = self.config.get("min_improvement", 0.01)
        self.seed = self.config.get("seed", 42)

        # 内部状态
        self.study = None
        self.history: List[OptimizationTrial] = []
        self.best_score = float('inf')
        self.best_params: Dict[str, Any] = {}
        self.start_time = None
        self.trial_count = 0

        # 尝试创建Optuna study
        self._create_study()

    def _create_study(self):
        """创建Optuna Study"""
        try:
            import optuna

            # 创建采样器
            sampler = optuna.samplers.TPESampler(
                seed=self.seed,
                multivariate=True,
                group=True
            )

            # 创建剪枝器（可选）
            pruner = optuna.pruners.MedianPruner(
                n_startup_trials=5,
                n_warmup_steps=10,
                interval_steps=1
            )

            # 创建study
            self.study = optuna.create_study(
                direction="minimize",
                sampler=sampler,
                pruner=pruner
            )

            logger.info("成功创建Optuna Study")

        except ImportError:
            logger.warning("Optuna未安装，将使用随机采样降级方案")
            self.study = None
        except Exception as e:
            logger.error(f"创建Optuna Study失败: {e}")
            self.study = None

    def suggest(self) -> Dict[str, Any]:
        """建议下一组参数

        Returns:
            参数字典
        """
        if self.study is not None:
            # 使用Optuna建议参数
            trial = self.study.ask()
            params = self._get_params_from_trial(trial)
            # 存储trial以便后续observe
            self._current_trial = trial
            return params
        else:
            # 降级到随机采样
            return self._random_sample()

    def _get_params_from_trial(self, trial) -> Dict[str, Any]:
        """从Optuna trial获取参数"""
        params = {}

        for name, space in self.search_space.items():
            space_type = space.get("type")

            if space_type == "categorical":
                params[name] = trial.suggest_categorical(
                    name, space["choices"]
                )
            elif space_type == "int":
                params[name] = trial.suggest_int(
                    name, space["min"], space["max"]
                )
            elif space_type == "float":
                params[name] = trial.suggest_float(
                    name, space["min"], space["max"]
                )
            elif space_type == "log":
                # 对数尺度
                import math
                log_min = math.log(space["min"])
                log_max = math.log(space["max"])
                log_value = trial.suggest_float(name, log_min, log_max)
                params[name] = math.exp(log_value)
            else:
                logger.warning(f"未知的参数类型: {space_type}")

        return params

    def _random_sample(self) -> Dict[str, Any]:
        """随机采样（降级方案）"""
        import random

        random.seed(self.seed + self.trial_count)
        params = {}

        for name, space in self.search_space.items():
            space_type = space.get("type")

            if space_type == "categorical":
                params[name] = random.choice(space["choices"])
            elif space_type == "int":
                params[name] = random.randint(space["min"], space["max"])
            elif space_type == "float":
                params[name] = random.uniform(space["min"], space["max"])
            elif space_type == "log":
                import math
                log_min = math.log(space["min"])
                log_max = math.log(space["max"])
                log_value = random.uniform(log_min, log_max)
                params[name] = math.exp(log_value)

        return params

    def observe(self, params: Dict[str, Any], score: float, **kwargs) -> None:
        """观察评估结果

        Args:
            params: 参数字典
            score: 目标函数值
            **kwargs: 额外的指标
        """
        self.trial_count += 1

        # 记录试验
        trial = OptimizationTrial(
            trial_id=self._generate_trial_id(params),
            params=params.copy(),
            score=score,
            metrics=kwargs.copy()
        )
        self.history.append(trial)

        # 更新最佳结果
        if score < self.best_score:
            self.best_score = score
            self.best_params = params.copy()

        # 如果使用Optuna，通知结果
        if self.study is not None and hasattr(self, '_current_trial'):
            try:
                self.study.tell(score)
            except Exception as e:
                logger.error(f"通知Optuna结果失败: {e}")
            finally:
                delattr(self, '_current_trial')

    def _generate_trial_id(self, params: Dict[str, Any]) -> str:
        """生成试验ID"""
        param_str = str(sorted(params.items()))
        hash_val = hashlib.md5(param_str.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"trial_{self.trial_count}_{hash_val}"

    def should_stop(self) -> bool:
        """判断是否应该停止优化

        检查：
        1. 是否达到最大试验次数
        2. 是否超时
        3. 是否收敛
        """
        # 检查试验次数
        if self.trial_count >= self.n_trials:
            return True

        # 检查超时
        if self.start_time and (time.time() - self.start_time) > self.timeout:
            return True

        # 检查收敛
        if len(self.history) >= self.early_stopping_patience + 10:
            recent_scores = [t.score for t in self.history[-self.early_stopping_patience:]]
            if len(recent_scores) > 0:
                improvement = (recent_scores[0] - recent_scores[-1]) / (recent_scores[0] + 1e-6)
                if improvement < self.min_improvement:
                    return True

        return False

    def optimize(self) -> OptimizationState:
        """运行完整优化

        Returns:
            优化状态
        """
        self.start_time = time.time()

        while not self.should_stop():
            # 建议参数
            params = self.suggest()

            # 评估目标函数
            trial_start = time.time()
            try:
                score = self.objective(params)
                trial_duration = time.time() - trial_start

                # 观察结果
                self.observe(params, score, duration=trial_duration)

            except Exception as e:
                logger.error(f"评估失败: {e}")
                continue

        # 创建优化状态
        best_trial = OptimizationTrial(
            trial_id="best",
            params=self.best_params,
            score=self.best_score,
            timestamp=time.time()
        )

        # 计算收敛率
        convergence_rate = self._calculate_convergence_rate()

        state = OptimizationState(
            current_trial=self.trial_count,
            best_trial=best_trial,
            convergence_rate=convergence_rate,
            should_stop=True,
            history=self.history.copy()
        )

        return state

    def _calculate_convergence_rate(self) -> float:
        """计算收敛率"""
        if len(self.history) < 10:
            return 0.0

        # 使用最近10次试验的标准差
        recent_scores = [t.score for t in self.history[-10:]]
        import statistics
        mean_score = statistics.mean(recent_scores)
        std_score = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0

        if mean_score == 0:
            return 0.0

        # 收敛率 = 1 - (标准差 / 均值)
        convergence = max(0.0, 1.0 - (std_score / (abs(mean_score) + 1e-6)))
        return convergence

    def get_best_params(self) -> Dict[str, Any]:
        """获取最佳参数"""
        return self.best_params.copy()

    def get_best_score(self) -> float:
        """获取最佳分数"""
        return self.best_score

    def get_history(self) -> List[OptimizationTrial]:
        """获取优化历史"""
        return self.history.copy()

    def get_n_trials(self) -> int:
        """获取试验次数"""
        return self.trial_count

    def get_total_time(self) -> float:
        """获取总耗时"""
        if self.start_time:
            return time.time() - self.start_time
        elif self.history:
            # 使用历史记录计算总耗时
            return sum(t.duration for t in self.history)
        return 0.0

    def get_n_trials(self) -> int:
        """获取试验次数（兼容方法）"""
        return self.trial_count

    def get_history(self) -> List[OptimizationTrial]:
        """获取历史记录（兼容方法）"""
        return self.history.copy()


class GridSearchOptimizer:
    """网格搜索优化器（降级方案）

    当Optuna不可用时使用。
    """

    def __init__(
        self,
        search_space: Dict[str, Any],
        objective: Callable[[Dict[str, Any]], float],
        config: Dict[str, Any] = None
    ):
        """初始化网格搜索优化器"""
        self.search_space = search_space
        self.objective = objective
        self.config = config or {}

        self.max_experiments = self.config.get("max_experiments", 50)
        self.timeout = self.config.get("timeout", 120)

        self.history: List[OptimizationTrial] = []
        self.best_score = float('inf')
        self.best_params: Dict[str, Any] = {}
        self.trial_count = 0
        self.start_time = None

    def _generate_grid_points(self) -> List[Dict[str, Any]]:
        """生成网格搜索点"""
        import random
        random.seed(42)

        points = []
        for _ in range(self.max_experiments):
            point = {}
            for name, space in self.search_space.items():
                space_type = space.get("type")

                if space_type == "categorical":
                    point[name] = random.choice(space["choices"])
                elif space_type == "int":
                    point[name] = random.randint(space["min"], space["max"])
                elif space_type == "float":
                    point[name] = random.uniform(space["min"], space["max"])

            points.append(point)

        return points

    def optimize(self) -> OptimizationState:
        """运行网格搜索优化"""
        self.start_time = time.time()

        # 生成搜索点
        grid_points = self._generate_grid_points()

        for params in grid_points:
            # 检查超时
            if time.time() - self.start_time > self.timeout:
                break

            # 评估
            try:
                trial_start = time.time()
                score = self.objective(params)
                trial_duration = time.time() - trial_start

                # 记录
                trial = OptimizationTrial(
                    trial_id=self._generate_trial_id(params),
                    params=params,
                    score=score,
                    duration=trial_duration
                )
                self.history.append(trial)
                self.trial_count += 1

                # 更新最佳
                if score < self.best_score:
                    self.best_score = score
                    self.best_params = params

            except Exception as e:
                logger.error(f"评估失败: {e}")
                continue

        # 创建状态
        best_trial = OptimizationTrial(
            trial_id="best",
            params=self.best_params,
            score=self.best_score
        )

        convergence_rate = self._calculate_convergence_rate()

        state = OptimizationState(
            current_trial=self.trial_count,
            best_trial=best_trial,
            convergence_rate=convergence_rate,
            should_stop=True,
            history=self.history
        )

        # 兼容方法
        state.get_best_params = lambda: self.best_params.copy()
        state.get_best_score = lambda: self.best_score
        state.get_total_time = lambda: (time.time() - self.start_time) if self.start_time else 0.0

        return state

    def _generate_trial_id(self, params: Dict[str, Any]) -> str:
        """生成试验ID"""
        import hashlib
        param_str = str(sorted(params.items()))
        hash_val = hashlib.md5(param_str.encode(), usedforsecurity=False).hexdigest()[:8]
        return f"grid_{self.trial_count}_{hash_val}"

    def _calculate_convergence_rate(self) -> float:
        """计算收敛率"""
        if len(self.history) < 10:
            return 0.0

        recent_scores = [t.score for t in self.history[-10:]]
        import statistics
        mean_score = statistics.mean(recent_scores)
        std_score = statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0

        if mean_score == 0:
            return 0.0

        convergence = max(0.0, 1.0 - (std_score / (abs(mean_score) + 1e-6)))
        return convergence


def create_optimizer(
    search_space: Dict[str, Any],
    objective: Callable[[Dict[str, Any]], float],
    config: Dict[str, Any] = None,
    prefer_bayesian: bool = True
) -> 'BayesianOptimizer':
    """创建优化器工厂函数

    Args:
        search_space: 搜索空间
        objective: 目标函数
        config: 配置
        prefer_bayesian: 是否优先使用贝叶斯优化

    Returns:
        优化器实例
    """
    config = config or {}

    if prefer_bayesian:
        try:
            import optuna
            logger.info("使用贝叶斯优化器（Optuna）")
            return BayesianOptimizer(search_space, objective, config)
        except ImportError:
            logger.warning("Optuna不可用，降级到网格搜索")

    logger.info("使用网格搜索优化器")
    return GridSearchOptimizer(search_space, objective, config)


# 预定义的搜索空间
DEFAULT_SEARCH_SPACES = {
    "structure": {
        "max_class_size": {"type": "int", "min": 100, "max": 500},
        "max_method_count": {"type": "categorical", "choices": [10, 15, 20, 25]},
        "max_complexity": {"type": "int", "min": 5, "max": 20},
        "max_nesting_depth": {"type": "int", "min": 3, "max": 6},
        "coupling_limit": {"type": "float", "min": 5.0, "max": 15.0},
    },
    "performance": {
        "cache_size": {"type": "categorical", "choices": [10, 50, 100, 500]},
        "parallelism": {"type": "int", "min": 1, "max": 4},
        "timeout": {"type": "categorical", "choices": [5, 10, 30, 60]},
    },
    "simplicity": {
        "complexity_threshold": {"type": "int", "min": 5, "max": 15},
        "duplication_penalty": {"type": "float", "min": 0.5, "max": 2.0},
        "max_line_length": {"type": "categorical", "choices": [80, 100, 120]},
    }
}


def get_default_search_space(goal: str) -> Dict[str, Any]:
    """获取默认搜索空间"""
    return DEFAULT_SEARCH_SPACES.get(goal, {}).copy()


if __name__ == "__main__":
    # 测试
    def test_objective(params):
        """测试目标函数：简单的二次函数"""
        x = params.get("x", 0)
        y = params.get("y", 0)
        return (x - 2) ** 2 + (y - 3) ** 2

    search_space = {
        "x": {"type": "float", "min": -10, "max": 10},
        "y": {"type": "float", "min": -10, "max": 10}
    }

    config = {
        "n_trials": 50,
        "timeout": 30,
        "seed": 42
    }

    optimizer = create_optimizer(search_space, test_objective, config)
    state = optimizer.optimize()

    print(f"最佳参数: {state.get_best_params()}")
    print(f"最佳分数: {state.get_best_score():.4f}")
    print(f"试验次数: {state.current_trial}")
    print(f"收敛率: {state.convergence_rate:.2%}")
