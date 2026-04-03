"""
LingFlow 进程隔离的优化器
使用独立进程运行优化，不影响主流程
"""

import multiprocessing as mp
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class OptimizationRequest:
    """优化请求"""

    target: str  # 目标路径
    goal: str  # 优化目标: "structure", "performance", "simplicity"
    params: Dict[str, Any]  # 当前参数
    config: Dict[str, Any]  # 优化配置


@dataclass
class OptimizationResult:
    """优化结果"""

    success: bool
    best_params: Dict[str, Any]
    best_score: float
    experiments: int
    duration: float
    error: str = ""
    history: list = field(default_factory=list)


def _optimization_worker(request: OptimizationRequest, result_queue: mp.Queue):
    """优化工作进程（运行在独立进程中）"""
    try:
        # 尝试导入LingMinOpt
        try:
            from lingminopt import MinimalOptimizer, ExperimentConfig

            HAS_LINGMINOPT = True
        except ImportError:
            HAS_LINGMINOPT = False

        # 创建搜索空间
        search_space = _create_search_space(request.goal)

        if HAS_LINGMINOPT:
            # 使用LingMinOpt
            # 根据目标选择评估器
            if request.goal == "structure":
                from lingflow.self_optimizer.evaluator import StructureEvaluator

                evaluator = StructureEvaluator(request.target)
            elif request.goal == "performance":
                from lingflow.self_optimizer.performance_evaluator import PerformanceEvaluator

                evaluator = PerformanceEvaluator(request.target)
            elif request.goal == "simplicity":
                from lingflow.self_optimizer.simplicity_evaluator import SimplicityEvaluator

                evaluator = SimplicityEvaluator(request.target)
            else:
                # 默认使用结构评估器
                from lingflow.self_optimizer.evaluator import StructureEvaluator

                evaluator = StructureEvaluator(request.target)

            def evaluate(params):
                return evaluator.evaluate(params)

            # 创建优化器配置
            config = ExperimentConfig(
                max_experiments=request.config.get("max_experiments", 20),
                time_budget=request.config.get("time_budget", 300),
                early_stopping_patience=request.config.get("early_stopping_patience", 10),
                direction="minimize",
            )

            optimizer = MinimalOptimizer(evaluate=evaluate, search_space=search_space, config=config)

            # 运行优化
            result = optimizer.run()

            # 将结果放入队列
            result_queue.put(
                OptimizationResult(
                    success=True,
                    best_params=result.best_params,
                    best_score=result.best_score,
                    experiments=result.total_experiments,
                    duration=result.total_time,
                    history=result.history,
                )
            )

        else:
            # 降级到简单网格搜索
            result = _grid_search(search_space, request.target, request.config.get("max_experiments", 20))

            result_queue.put(result)

    except Exception as e:
        import traceback

        result_queue.put(
            OptimizationResult(
                success=False,
                best_params={},
                best_score=0,
                experiments=0,
                duration=0,
                error=str(e) + "\n" + traceback.format_exc(),
            )
        )


def _create_search_space(goal: str):
    """创建搜索空间"""
    try:
        from lingminopt import SearchSpace

        search_space = SearchSpace()
    except ImportError:
        # 降级到简单实现
        search_space = SimpleSearchSpace()

    if goal == "structure":
        search_space.add_discrete("max_class_size", [100, 200, 300, 500])
        search_space.add_discrete("max_method_count", [10, 15, 20, 25])
        search_space.add_discrete("max_complexity", [5, 10, 15, 20])
        search_space.add_discrete("max_nesting_depth", [3, 4, 5, 6])
        search_space.add_continuous("coupling_limit", 5.0, 15.0)

    elif goal == "performance":
        search_space.add_discrete("cache_size", [10, 50, 100, 500])
        search_space.add_discrete("parallelism", [1, 2, 4])
        search_space.add_discrete("timeout", [5, 10, 30, 60])

    elif goal == "simplicity":
        search_space.add_discrete("complexity_threshold", [5, 10, 15])
        search_space.add_discrete("duplication_penalty", [0.5, 1.0, 2.0])
        search_space.add_discrete("max_line_length", [80, 100, 120])

    return search_space


def _grid_search(search_space, target_path: str, max_experiments: int) -> OptimizationResult:
    """简单网格搜索（降级方案）"""
    from lingflow.self_optimizer.evaluator import StructureEvaluator

    evaluator = StructureEvaluator(target_path)
    best_score = float("inf")
    best_params = {}

    # 生成网格搜索点（简化版：随机采样）
    import random

    random.seed(42)

    for i in range(max_experiments):
        params = search_space.sample()
        score = evaluator.evaluate(params)

        if score < best_score:
            best_score = score
            best_params = params

    return OptimizationResult(
        success=True, best_params=best_params, best_score=best_score, experiments=max_experiments, duration=0, history=[]
    )


class SimpleSearchSpace:
    """简单搜索空间（降级实现）"""

    def __init__(self):
        import random

        self.parameters = {}
        self._rng = random.Random()

    def add_discrete(self, name, choices):
        self.parameters[name] = ("discrete", choices)

    def add_continuous(self, name, min_val, max_val):
        self.parameters[name] = ("continuous", min_val, max_val)

    def sample(self):
        sampled = {}
        for name, param in self.parameters.items():
            if param[0] == "discrete":
                sampled[name] = self._rng.choice(param[1])
            else:
                sampled[name] = self._rng.uniform(param[1], param[2])
        return sampled


class ProcessIsolatedOptimizer:
    """进程隔离的优化器"""

    def __init__(self):
        self.process: Optional[mp.Process] = None
        self.result_queue: Optional[mp.Queue] = None

    def start_optimization(self, request: OptimizationRequest) -> bool:
        """启动优化进程（非阻塞）

        Args:
            request: 优化请求

        Returns:
            是否成功启动
        """
        if self.is_running():
            return False  # 已有优化在运行

        # 创建结果队列
        self.result_queue = mp.Queue()

        # 启动进程
        self.process = mp.Process(target=_optimization_worker, args=(request, self.result_queue))
        self.process.start()

        return True

    def is_running(self) -> bool:
        """检查优化是否在运行"""
        return self.process is not None and self.process.is_alive()

    def get_progress(self) -> Optional[Dict[str, Any]]:
        """获取优化进度（非阻塞）"""
        if not self.is_running():
            return None

        return {
            "running": True,
            "pid": self.process.pid if self.process else None,
        }

    def get_result(self, timeout: float = 0.0) -> Optional[OptimizationResult]:
        """获取优化结果（如果完成）

        Args:
            timeout: 等待超时时间（秒），0表示非阻塞

        Returns:
            优化结果，如果未完成则返回None
        """
        if not self.result_queue:
            return None

        try:
            if timeout > 0:
                # 等待指定时间
                if not self.result_queue.empty():
                    return self.result_queue.get(timeout=timeout)
            else:
                # 非阻塞
                if not self.result_queue.empty():
                    return self.result_queue.get_nowait()
        except Exception:
            pass

        return None

    def wait_for_completion(self, timeout: float = 300.0) -> Optional[OptimizationResult]:
        """等待优化完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            优化结果
        """
        if self.process:
            self.process.join(timeout=timeout)

        return self.get_result(timeout=1.0)

    def cancel(self):
        """取消优化"""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=5)
            if self.process.is_alive():
                self.process.kill()


class SynchronousOptimizer:
    """同步优化器（用于测试或小型项目）"""

    def optimize(self, request: OptimizationRequest) -> OptimizationResult:
        """同步执行优化（阻塞）

        Args:
            request: 优化请求

        Returns:
            优化结果
        """
        try:
            from lingminopt import MinimalOptimizer, ExperimentConfig

            # 创建搜索空间
            search_space = _create_search_space(request.goal)

            # 根据目标选择评估器
            if request.goal == "structure":
                from lingflow.self_optimizer.evaluator import StructureEvaluator

                evaluator = StructureEvaluator(request.target)
            elif request.goal == "performance":
                from lingflow.self_optimizer.performance_evaluator import PerformanceEvaluator

                evaluator = PerformanceEvaluator(request.target)
            elif request.goal == "simplicity":
                from lingflow.self_optimizer.simplicity_evaluator import SimplicityEvaluator

                evaluator = SimplicityEvaluator(request.target)
            else:
                # 默认使用结构评估器
                from lingflow.self_optimizer.evaluator import StructureEvaluator

                evaluator = StructureEvaluator(request.target)

            def evaluate(params):
                return evaluator.evaluate(params)

            # 创建优化器
            config = ExperimentConfig(
                max_experiments=request.config.get("max_experiments", 20),
                time_budget=request.config.get("time_budget", 300),
                early_stopping_patience=request.config.get("early_stopping_patience", 10),
                direction="minimize",
            )

            optimizer = MinimalOptimizer(evaluate=evaluate, search_space=search_space, config=config)

            # 运行优化
            result = optimizer.run()

            return OptimizationResult(
                success=True,
                best_params=result.best_params,
                best_score=result.best_score,
                experiments=result.total_experiments,
                duration=result.total_time,
                history=result.history,
            )

        except ImportError:
            # 降级到简单搜索
            search_space = _create_search_space(request.goal)
            return _grid_search(search_space, request.target, request.config.get("max_experiments", 20))
        except Exception as e:
            import traceback

            return OptimizationResult(
                success=False,
                best_params={},
                best_score=0,
                experiments=0,
                duration=0,
                error=str(e) + "\n" + traceback.format_exc(),
            )


if __name__ == "__main__":  # pragma: no cover
    # 测试
    request = OptimizationRequest(
        target="/home/ai/LingFlow/lingflow", goal="structure", params={}, config={"max_experiments": 5}
    )

    # 同步测试
    optimizer = SynchronousOptimizer()
    result = optimizer.optimize(request)

    print(f"优化结果: {result.success}")
    print(f"最佳参数: {result.best_params}")
    print(f"最佳分数: {result.best_score}")
    print(f"实验次数: {result.experiments}")
    print(f"耗时: {result.duration:.2f}秒")
