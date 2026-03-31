"""
LingFlow Phase 4 集成到现有 self_optimizer

提供向后兼容的适配器，将Phase 4的新功能集成到现有系统。
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class Phase4Integration:
    """Phase 4 集成适配器

    将Phase 4的贝叶斯优化、多目标优化和敏感性分析
    集成到现有的self_optimizer系统中。
    """

    @staticmethod
    def enhance_optimizer_request(request) -> Dict[str, Any]:
        """增强优化请求

        将现有的OptimizationRequest转换为Phase 4格式。

        Args:
            request: 现有的OptimizationRequest

        Returns:
            Phase 4兼容的配置字典
        """
        # 提取目标
        goal = request.goal if hasattr(request, 'goal') else "structure"

        # 提取路径
        target = request.target if hasattr(request, 'target') else "."

        # 提取配置
        config = request.config if hasattr(request, 'config') else {}

        # 转换为Phase 4配置
        phase4_config = {
            "n_trials": config.get("max_experiments", 50),
            "timeout": config.get("time_budget", 120),
            "early_stopping_patience": config.get("early_stopping_patience", 10),
            "generate_reports": True
        }

        return {
            "target_path": target,
            "goal": goal,
            "config": phase4_config
        }

    @staticmethod
    def convert_to_legacy_result(phase4_result: Dict[str, Any], request):
        """将Phase 4结果转换为现有格式

        Args:
            phase4_result: Phase 4优化结果
            request: 原始请求

        Returns:
            现有格式的OptimizationResult
        """
        from lingflow.self_optimizer.optimizer import OptimizationResult

        # 构建历史
        history = []
        for i in range(phase4_result.get("n_trials", 0)):
            history.append({
                "experiment_id": i,
                "params": phase4_result.get("best_params", {}),
                "score": phase4_result.get("best_score", float('inf'))
            })

        return OptimizationResult(
            success=True,
            best_params=phase4_result.get("best_params", {}),
            best_score=phase4_result.get("best_score", 0),
            experiments=phase4_result.get("n_trials", 0),
            duration=phase4_result.get("total_time", 0),
            history=history
        )


class EnhancedOptimizerAdapter:
    """增强的优化器适配器

    提供与现有SynchronousOptimizer兼容的接口，
    但内部使用Phase 4的贝叶斯优化。
    """

    def __init__(self, use_phase4: bool = True):
        """初始化适配器

        Args:
            use_phase4: 是否使用Phase 4优化器
        """
        self.use_phase4 = use_phase4

        if use_phase4:
            try:
                from lingflow.self_optimizer.phase4 import OptimizationEngine
                self.engine = OptimizationEngine()
                logger.info("使用Phase 4贝叶斯优化器")
            except ImportError as e:
                logger.warning(f"Phase 4不可用: {e}，降级到现有优化器")
                self.use_phase4 = False

        if not self.use_phase4:
            from lingflow.self_optimizer.optimizer import SynchronousOptimizer
            self.legacy_optimizer = SynchronousOptimizer()

    def optimize(self, request):
        """优化（兼容现有接口）

        Args:
            request: OptimizationRequest

        Returns:
            OptimizationResult
        """
        if self.use_phase4:
            # 使用Phase 4优化
            config = Phase4Integration.enhance_optimizer_request(request)
            result = self.engine.optimize_single_objective(
                target_path=config["target_path"],
                goal=config["goal"],
                config=config["config"]
            )

            # 转换结果格式
            return Phase4Integration.convert_to_legacy_result(result, request)
        else:
            # 使用现有优化器
            return self.legacy_optimizer.optimize(request)


def patch_self_optimizer():
    """动态补丁self_optimizer，启用Phase 4功能

    修改现有的optimizer模块，使用Phase 4优化器。
    """
    try:
        from lingflow import self_optimizer as optimizer_module

        # 保存原始类
        if not hasattr(optimizer_module, '_original_SynchronousOptimizer'):
            optimizer_module._original_SynchronousOptimizer = (
                optimizer_module.SynchronousOptimizer
            )

        # 替换为增强版本
        optimizer_module.SynchronousOptimizer = EnhancedOptimizerAdapter

        logger.info("已启用Phase 4优化器集成")

    except Exception as e:
        logger.error(f"补丁self_optimizer失败: {e}")


def enable_phase4_integration():
    """启用Phase 4集成（便捷函数）"""
    patch_self_optimizer()


# 可选：自动启用集成
# 取消下面的注释来自动启用Phase 4集成
# enable_phase4_integration()
