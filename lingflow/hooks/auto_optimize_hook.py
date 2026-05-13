"""
lingflow 自优化钩子
在特定事件触发时检查是否需要自优化
"""

from datetime import datetime
from typing import Any, Dict

from lingflow.self_optimizer.optimizer import OptimizationRequest, ProcessIsolatedOptimizer
from lingflow.self_optimizer.trigger import OptimizationTrigger, TriggerInfo


class AutoOptimizeHook:
    """自优化触发钩子"""

    def __init__(self):
        self.trigger = OptimizationTrigger()
        self.optimizer = ProcessIsolatedOptimizer()
        self.last_check_time = None
        self.optimization_suggested = False

    def on_code_review_complete(self, review_result: Dict[str, Any]):
        """代码审查完成时检查

        Args:
            review_result: 审查结果，包含：
                - overall_score: 整体得分
                - dimensions: 各维度得分
        """
        context = {
            "review_score": review_result.get("overall_score", 100),
            "coverage_drop": 0,
            "execution_time": 0,
        }

        self._check_and_prompt(context, review_result)

    def on_test_complete(self, test_result: Dict[str, Any]):
        """测试完成时检查

        Args:
            test_result: 测试结果，包含：
                - coverage: 测试覆盖率
                - duration: 执行时间
                - failed: 失败数
                - total: 总数
        """
        # 计算覆盖率下降（简化版）
        coverage = test_result.get("coverage", 100)
        coverage_drop = max(0, self.last_check.get("coverage", 100) - coverage)

        context = {
            "review_score": 100,
            "coverage_drop": coverage_drop,
            "execution_time": test_result.get("duration", 0),
            "test_failure_rate": (
                test_result.get("failed", 0) / test_result.get("total", 1) * 100 if test_result.get("total", 0) > 0 else 0
            ),
        }

        # 更新last_check
        self.last_check["coverage"] = coverage

        self._check_and_prompt(context, test_result)

    def on_git_commit(self, commit_info: Dict[str, Any]):
        """Git提交时检查

        Args:
            commit_info: 提交信息，包含：
                - new_lines: 新增行数
                - deleted_lines: 删除行数
                - new_files: 新增文件数
        """
        context = {
            "review_score": 100,
            "new_lines": commit_info.get("new_lines", 0),
            "deleted_lines": commit_info.get("deleted_lines", 0),
            "new_files": commit_info.get("new_files", 0),
        }

        self._check_and_prompt(context, commit_info)

    def on_performance_measure(self, metrics: Dict[str, Any]):
        """性能测量时检查

        Args:
            metrics: 性能指标，包含：
                - execution_time: 执行时间
                - memory_usage_mb: 内存使用
                - response_time_ms: 响应时间
        """
        context = {
            "review_score": 100,
            "execution_time": metrics.get("execution_time", 0),
            "memory_usage_mb": metrics.get("memory_usage_mb", 0),
            "response_time_ms": metrics.get("response_time_ms", 0),
        }

        self._check_and_prompt(context, metrics)

    def _check_and_prompt(self, context: Dict[str, Any], event_data: Dict[str, Any]):
        """检查条件并提示用户"""
        # 更新last_check_time
        self.last_check_time = datetime.now()

        # 检查是否已有优化在运行
        if self.optimizer.is_running():
            return  # 已有优化在运行，跳过

        # 检查触发条件
        should_trigger, trigger_info = self.trigger.check_all_conditions(context)

        if not should_trigger:
            return  # 不满足触发条件

        # 检查是否需要用户确认
        if not self.trigger.requires_confirmation():
            # 自动启动优化
            self._start_optimization(trigger_info)
            return

        # 提示用户
        self._prompt_user(trigger_info, event_data)

    def _prompt_user(self, trigger_info: TriggerInfo, event_data: Dict[str, Any]):
        """提示用户是否启动优化"""
        if self.optimization_suggested:
            return  # 已建议过，避免重复提示

        print("\n" + "=" * 60)
        print("🔍 检测到需要优化的问题".center(60))
        print("=" * 60)
        print(f"\n原因: {trigger_info.reason}")
        print(f"优先级: {trigger_info.priority}")

        if trigger_info.current_value is not None:
            print(f"\n当前值: {trigger_info.current_value}")
            if trigger_info.threshold is not None:
                print(f"阈值: {trigger_info.threshold}")

        print("\n" + "-" * 60)

        response = input("\n是否启动自优化? [y/N] ")

        if response.lower() == "y":
            self._start_optimization(trigger_info)
        else:
            print("跳过优化。")

        self.optimization_suggested = True

    def _start_optimization(self, trigger_info: TriggerInfo):
        """启动优化"""
        # 确定优化目标
        goal = self._determine_goal_from_trigger(trigger_info)

        # 创建优化请求
        from lingflow.self_optimizer.config import get_global_config

        config = get_global_config()

        request = OptimizationRequest(
            target=".", goal=goal, params={}, config=config.get_optimization_config()  # 默认当前目录
        )

        # 启动优化
        success = self.optimizer.start_optimization(request)

        if success:
            print("\n✓ 自优化已启动（后台运行）")
            print(f"  进程ID: {self.optimizer.process.pid}")
            print("  使用 'lingflow optimize status' 查看进度")
        else:
            print("\n⚠️  优化启动失败（可能已有优化在运行）")

    def _determine_goal_from_trigger(self, trigger_info: TriggerInfo) -> str:
        """根据触发器类型确定优化目标"""
        trigger_type = trigger_info.type

        # 映射触发器类型到优化目标
        type_to_goal = {
            "structure": "structure",
            "quality": "structure",  # 质量问题优先优化结构
            "performance": "performance",
            "tech_debt": "simplicity",  # 技术债务优先优化简洁性
            "scale": "structure",
            "time": "structure",
            "user": "structure",  # 用户默认优化结构
        }

        return type_to_goal.get(trigger_type, "structure")

    def is_optimization_running(self) -> bool:
        """检查是否有优化在运行"""
        return self.optimizer.is_running()

    def get_optimization_result(self):
        """获取优化结果（如果完成）"""
        return self.optimizer.get_result()

    def cancel_optimization(self):
        """取消当前优化"""
        self.optimizer.cancel()


# 全局钩子实例
_global_hook: AutoOptimizeHook = None


def get_global_hook() -> AutoOptimizeHook:
    """获取全局钩子实例"""
    global _global_hook
    if _global_hook is None:
        _global_hook = AutoOptimizeHook()
    return _global_hook
