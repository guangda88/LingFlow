"""
LingFlow 自优化触发器
检测何时应该启动自优化
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from lingflow.self_optimizer.config import get_global_config


@dataclass
class TriggerInfo:
    """触发器信息"""

    type: str  # 触发器类型
    reason: str  # 触发原因
    priority: str  # 优先级: high/medium/low
    current_value: Any  # 当前值
    threshold: Any  # 阈值
    metrics: Dict[str, Any]  # 相关指标


class OptimizationTrigger:
    """自优化触发器"""

    def __init__(self, config=None):
        """
        Args:
            config: 配置管理器（可选，默认使用全局配置）
        """
        self.config = config or get_global_config()
        self.last_check = {}

    def check_all_conditions(self, context: Dict[str, Any]) -> Tuple[bool, Optional[TriggerInfo]]:
        """检查所有触发条件

        Args:
            context: 上下文信息，包含：
                - review_score: 代码审查得分
                - coverage: 测试覆盖率
                - execution_time: 执行时间
                - baseline_time: 基线执行时间
                - memory_usage_mb: 内存使用
                - avg_complexity: 平均复杂度
                - large_classes_count: 大型类数量
                - new_lines: 新增代码行数
                - todo_count: TODO数量
                - last_optimization_time: 上次优化时间
                - user_triggered: 用户主动触发

        Returns:
            (should_trigger, trigger_info)
        """
        triggers_found = []

        # 1. 用户主动触发（最高优先级）
        if context.get("user_triggered"):
            return True, TriggerInfo(
                type="user", reason="用户主动触发", priority="high", current_value=None, threshold=None, metrics={}
            )

        # 2. 质量检查
        quality_trigger = self._check_quality(context)
        if quality_trigger:
            triggers_found.append(quality_trigger)

        # 3. 结构检查
        structure_trigger = self._check_structure(context)
        if structure_trigger:
            triggers_found.append(structure_trigger)

        # 4. 性能检查
        perf_trigger = self._check_performance(context)
        if perf_trigger:
            triggers_found.append(perf_trigger)

        # 5. 规模检查
        scale_trigger = self._check_scale(context)
        if scale_trigger:
            triggers_found.append(scale_trigger)

        # 6. 技术债务检查
        debt_trigger = self._check_tech_debt(context)
        if debt_trigger:
            triggers_found.append(debt_trigger)

        # 7. 时间检查
        time_trigger = self._check_time(context)
        if time_trigger:
            triggers_found.append(time_trigger)

        # 选择优先级最高的触发器
        if triggers_found:
            priority_order = {"high": 3, "medium": 2, "low": 1}
            triggers_found.sort(key=lambda x: priority_order.get(x.priority, 0), reverse=True)
            return True, triggers_found[0]

        return False, None

    def _check_quality(self, context: Dict[str, Any]) -> Optional[TriggerInfo]:
        """检查质量相关触发条件"""
        config = self.config.get_trigger_config("quality")

        # 代码审查得分
        score = context.get("review_score", 100)
        threshold = config.get("review_score_below", 70)

        if score < threshold:
            return TriggerInfo(
                type="quality",
                reason=f"代码审查得分 ({score}) 低于阈值 ({threshold})",
                priority="high" if score < 50 else "medium",
                current_value=score,
                threshold=threshold,
                metrics={"review_score": score},
            )

        # 测试覆盖率下降
        coverage_drop = context.get("coverage_drop", 0)
        threshold = config.get("coverage_drop_above", 5)

        if coverage_drop > threshold:
            return TriggerInfo(
                type="quality",
                reason=f"测试覆盖率下降 ({coverage_drop}%) 超过阈值 ({threshold}%)",
                priority="medium",
                current_value=coverage_drop,
                threshold=threshold,
                metrics={"coverage_drop": coverage_drop},
            )

        # 测试失败率
        failure_rate = context.get("test_failure_rate", 0)
        threshold = config.get("test_failure_rate_above", 10)

        if failure_rate > threshold:
            return TriggerInfo(
                type="quality",
                reason=f"测试失败率 ({failure_rate}%) 超过阈值 ({threshold}%)",
                priority="high",
                current_value=failure_rate,
                threshold=threshold,
                metrics={"test_failure_rate": failure_rate},
            )

        return None

    def _check_structure(self, context: Dict[str, Any]) -> Optional[TriggerInfo]:
        """检查结构相关触发条件"""
        config = self.config.get_trigger_config("structure")

        # 圈复杂度
        complexity = context.get("avg_complexity", 0)
        threshold = config.get("complexity_above", 15)

        if complexity > threshold:
            return TriggerInfo(
                type="structure",
                reason=f"平均圈复杂度 ({complexity}) 超过阈值 ({threshold})",
                priority="medium",
                current_value=complexity,
                threshold=threshold,
                metrics={"avg_complexity": complexity},
            )

        # 大型类数量
        large_classes = context.get("large_classes_count", 0)
        threshold = config.get("large_classes_count_above", 5)

        if large_classes > threshold:
            return TriggerInfo(
                type="structure",
                reason=f"大型类数量 ({large_classes}) 超过阈值 ({threshold})",
                priority="medium",
                current_value=large_classes,
                threshold=threshold,
                metrics={"large_classes_count": large_classes},
            )

        # 重复代码率
        duplication_rate = context.get("duplication_rate", 0)
        threshold = config.get("duplication_rate_above", 0.05)

        if duplication_rate > threshold:
            rate_pct = duplication_rate * 100
            threshold_pct = threshold * 100
            return TriggerInfo(
                type="structure",
                reason=f"代码重复率 ({rate_pct:.1f}%) 超过阈值 ({threshold_pct:.1f}%)",
                priority="low",
                current_value=duplication_rate,
                threshold=threshold,
                metrics={"duplication_rate": duplication_rate},
            )

        # 耦合度
        coupling = context.get("avg_coupling", 0)
        threshold = config.get("coupling_above", 10)

        if coupling > threshold:
            return TriggerInfo(
                type="structure",
                reason=f"平均耦合度 ({coupling}) 超过阈值 ({threshold})",
                priority="medium",
                current_value=coupling,
                threshold=threshold,
                metrics={"avg_coupling": coupling},
            )

        return None

    def _check_performance(self, context: Dict[str, Any]) -> Optional[TriggerInfo]:
        """检查性能相关触发条件"""
        config = self.config.get_trigger_config("performance")

        # 执行时间
        exec_time = context.get("execution_time", 0)
        baseline = context.get("baseline_time", exec_time)
        ratio = config.get("execution_time_increase_ratio", 1.5)

        if baseline > 0 and exec_time > baseline * ratio:
            increase_pct = (exec_time / baseline - 1) * 100
            return TriggerInfo(
                type="performance",
                reason=f"执行时间 ({exec_time:.2f}s) 比基线增加 {increase_pct:.0f}%",
                priority="high",
                current_value=exec_time,
                threshold=baseline * ratio,
                metrics={"execution_time": exec_time, "baseline_time": baseline},
            )

        # 内存使用
        memory_mb = context.get("memory_usage_mb", 0)
        threshold = config.get("memory_usage_above_mb", 500)

        if memory_mb > threshold:
            return TriggerInfo(
                type="performance",
                reason=f"内存使用 ({memory_mb:.1f}MB) 超过阈值 ({threshold}MB)",
                priority="high",
                current_value=memory_mb,
                threshold=threshold,
                metrics={"memory_usage_mb": memory_mb},
            )

        # API响应时间
        response_time = context.get("response_time_ms", 0)
        threshold = config.get("response_time_above_ms", 100)

        if response_time > threshold:
            return TriggerInfo(
                type="performance",
                reason=f"API响应时间 ({response_time}ms) 超过阈值 ({threshold}ms)",
                priority="medium",
                current_value=response_time,
                threshold=threshold,
                metrics={"response_time_ms": response_time},
            )

        return None

    def _check_scale(self, context: Dict[str, Any]) -> Optional[TriggerInfo]:
        """检查规模变化"""
        config = self.config.get_trigger_config("scale")

        # 新增代码行数
        new_lines = context.get("new_lines", 0)
        threshold = config.get("new_lines_above", 500)

        if new_lines > threshold:
            return TriggerInfo(
                type="scale",
                reason=f"新增代码 ({new_lines}行) 超过阈值 ({threshold}行)",
                priority="low",
                current_value=new_lines,
                threshold=threshold,
                metrics={"new_lines": new_lines},
            )

        # 新增文件数
        new_files = context.get("new_files", 0)
        threshold = config.get("new_files_above", 10)

        if new_files > threshold:
            return TriggerInfo(
                type="scale",
                reason=f"新增文件 ({new_files}个) 超过阈值 ({threshold}个)",
                priority="low",
                current_value=new_files,
                threshold=threshold,
                metrics={"new_files": new_files},
            )

        return None

    def _check_tech_debt(self, context: Dict[str, Any]) -> Optional[TriggerInfo]:
        """检查技术债务"""
        config = self.config.get_trigger_config("tech_debt")

        # TODO数量
        todo_count = context.get("todo_count", 0)
        threshold = config.get("todo_count_above", 20)

        if todo_count > threshold:
            return TriggerInfo(
                type="tech_debt",
                reason=f"TODO 注释数量 ({todo_count}) 超过阈值 ({threshold})",
                priority="low",
                current_value=todo_count,
                threshold=threshold,
                metrics={"todo_count": todo_count},
            )

        # HACK标记
        hack_count = context.get("hack_comments", 0)
        threshold = config.get("hack_comments_above", 3)

        if hack_count > threshold:
            return TriggerInfo(
                type="tech_debt",
                reason=f"HACK 标记数量 ({hack_count}) 超过阈值 ({threshold})",
                priority="medium",
                current_value=hack_count,
                threshold=threshold,
                metrics={"hack_comments": hack_count},
            )

        return None

    def _check_time(self, context: Dict[str, Any]) -> Optional[TriggerInfo]:
        """检查时间相关触发条件"""
        config = self.config.get_trigger_config("time")

        # 距上次优化时间
        last_opt_time = context.get("last_optimization_time")
        if last_opt_time:
            if isinstance(last_opt_time, str):
                last_opt_time = datetime.fromisoformat(last_opt_time)

            days_since = (datetime.now() - last_opt_time).days
            threshold = config.get("days_since_last_optimization", 7)

            if days_since >= threshold:
                return TriggerInfo(
                    type="time",
                    reason=f"距离上次优化已超过 {days_since} 天（阈值：{threshold}天）",
                    priority="low",
                    current_value=days_since,
                    threshold=threshold,
                    metrics={"days_since_last_optimization": days_since},
                )

        # 距上次检查的提交次数
        commits_since = context.get("commits_since_last_check", 0)
        threshold = config.get("commits_since_last_check", 20)

        if commits_since >= threshold:
            return TriggerInfo(
                type="time",
                reason=f"距离上次检查已超过 {commits_since} 次提交（阈值：{threshold}次）",
                priority="low",
                current_value=commits_since,
                threshold=threshold,
                metrics={"commits_since_last_check": commits_since},
            )

        return None

    def should_auto_trigger(self) -> bool:
        """检查是否应该自动触发（根据钩子配置）"""
        hooks_config = self.config.get_hooks_config()
        return (
            hooks_config.get("enable_on_review", False)
            or hooks_config.get("enable_on_test", False)
            or hooks_config.get("enable_on_commit", False)
        )

    def requires_confirmation(self) -> bool:
        """检查是否需要用户确认"""
        hooks_config = self.config.get_hooks_config()
        return hooks_config.get("require_confirmation", True)
