"""
LingFlow 自优化系统
基于 LingMinOpt 的自我优化能力
"""

from lingflow.self_optimizer.config import DEFAULT_CONFIG, OptimizationConfig, get_global_config

# 向后兼容：保留ConfigManager作为别名
ConfigManager = OptimizationConfig

from lingflow.self_optimizer.advisor import OptimizationAdvisor
from lingflow.self_optimizer.evaluator import StructureEvaluator, fallback_evaluate
from lingflow.self_optimizer.optimizer import (
    OptimizationRequest,
    OptimizationResult,
    ProcessIsolatedOptimizer,
    SynchronousOptimizer,
)
from lingflow.self_optimizer.performance_evaluator import PerformanceEvaluator as PerfEvaluator
from lingflow.self_optimizer.simplicity_evaluator import SimplicityEvaluator
from lingflow.self_optimizer.trigger import OptimizationTrigger, TriggerInfo

__all__ = [
    # Config
    "OptimizationConfig",
    "ConfigManager",  # 向后兼容的别名
    "get_global_config",
    "DEFAULT_CONFIG",
    # Trigger
    "OptimizationTrigger",
    "TriggerInfo",
    # Optimizer
    "ProcessIsolatedOptimizer",
    "SynchronousOptimizer",
    "OptimizationRequest",
    "OptimizationResult",
    # Evaluators
    "StructureEvaluator",
    "PerfEvaluator",
    "SimplicityEvaluator",
    "fallback_evaluate",
    # Advisor
    "OptimizationAdvisor",
]


# 便捷函数
def quick_optimize(target: str = ".", goal: str = "structure", async_mode: bool = False) -> OptimizationResult:
    """快速优化（便捷函数）

    Args:
        target: 目标路径
        goal: 优化目标 (structure/performance/simplicity)
        async_mode: 是否异步执行

    Returns:
        优化结果
    """
    config = get_global_config()
    opt_config = config.get_optimization_config()

    request = OptimizationRequest(target=target, goal=goal, params={}, config=opt_config)

    if async_mode:
        optimizer = ProcessIsolatedOptimizer()
        optimizer.start_optimization(request)
        # 返回None表示异步启动成功
        return None
    else:
        optimizer = SynchronousOptimizer()
        return optimizer.optimize(request)


def check_and_optimize(context: dict, target: str = ".", goal: str = "structure") -> tuple[bool, OptimizationResult]:
    """检查条件并优化

    Args:
        context: 上下文信息
        target: 目标路径
        goal: 优化目标

    Returns:
        (should_optimize, result)
    """
    # 1. 检查触发条件
    trigger = OptimizationTrigger()
    should_trigger, trigger_info = trigger.check_all_conditions(context)

    if not should_trigger:
        return False, None

    # 2. 打印触发信息
    print(f"\n🔍 {trigger_info.reason}")
    print(f"优先级: {trigger_info.priority}")

    # 3. 确认是否优化
    if trigger.requires_confirmation():
        response = input("\n是否启动优化? [y/N] ")
        if response.lower() != "y":
            return False, None

    # 4. 运行优化
    result = quick_optimize(target, goal)

    return True, result
