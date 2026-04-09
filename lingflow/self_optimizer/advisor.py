"""
LingFlow 优化建议生成器
生成详细的优化建议报告
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from lingflow.self_optimizer.optimizer import OptimizationResult


class OptimizationAdvisor:
    """优化建议生成器"""

    def __init__(self):
        self.goal_names = {"structure": "结构优化", "performance": "性能优化", "simplicity": "简洁优化"}

    def generate_report(
        self, goal: str, target: str, current_metrics: Dict[str, Any], optimization_result: OptimizationResult
    ) -> str:
        """生成优化建议报告

        Args:
            goal: 优化目标
            target: 目标路径
            current_metrics: 当前指标
            optimization_result: 优化结果

        Returns:
            Markdown格式的报告
        """
        lines = [
            "# LingFlow 自优化建议报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"优化目标: {self._goal_name(goal)}",
            f"目标范围: {target}",
            "",
            "---",
            "",
            "## 当前状态分析",
            "",
        ]

        # 添加当前指标
        lines.extend(self._format_current_metrics(current_metrics, goal))

        # 添加主要问题
        lines.extend(self._format_issues(current_metrics, goal))

        # 添加优化建议
        lines.extend(self._format_recommendations(current_metrics, optimization_result, goal))

        # 添加详细对比
        lines.extend(self._format_comparison(current_metrics, optimization_result))

        # 添加实施步骤
        lines.extend(self._format_implementation_steps(optimization_result.best_params))

        # 添加优化历史
        if optimization_result.history:
            lines.extend(self._format_optimization_history(optimization_result))

        return "\n".join(lines)

    def _goal_name(self, goal: str) -> str:
        """获取目标名称"""
        return self.goal_names.get(goal, goal)

    def _format_current_metrics(self, metrics: Dict[str, Any], goal: str) -> list[str]:
        """格式化当前指标"""
        lines = ["### 质量指标", ""]

        # 通用指标
        if "review_score" in metrics:
            lines.append(f"- 整体得分: {metrics['review_score']}/100")

        # 结构相关指标
        if goal == "structure":
            if "structure_violations" in metrics:
                lines.append(f"- 结构违规: {metrics['structure_violations']}处")
            if "avg_class_size" in metrics:
                lines.append(f"- 平均类大小: {metrics['avg_class_size']:.0f}行")
            if "avg_method_count" in metrics:
                lines.append(f"- 平均方法数: {metrics['avg_method_count']:.1f}个")
            if "avg_complexity" in metrics:
                lines.append(f"- 圈复杂度: {metrics['avg_complexity']:.1f}")
            if "large_classes_count" in metrics:
                lines.append(f"- 大型类数量: {metrics['large_classes_count']}")

        # 性能相关指标
        elif goal == "performance":
            if "execution_time" in metrics:
                lines.append(f"- 执行时间: {metrics['execution_time']:.2f}秒")
            if "memory_usage_mb" in metrics:
                lines.append(f"- 内存使用: {metrics['memory_usage_mb']:.1f}MB")
            if "response_time_ms" in metrics:
                lines.append(f"- API响应时间: {metrics['response_time_ms']:.0f}ms")

        # 简洁相关指标
        elif goal == "simplicity":
            if "total_lines" in metrics:
                lines.append(f"- 代码总行数: {metrics['total_lines']}")
            if "duplication_rate" in metrics:
                rate_pct = metrics["duplication_rate"] * 100
                lines.append(f"- 重复率: {rate_pct:.1f}%")
            if "avg_line_length" in metrics:
                lines.append(f"- 平均行长度: {metrics['avg_line_length']:.0f}")

        lines.append("")
        return lines

    def _format_issues(self, metrics: Dict[str, Any], goal: str) -> list[str]:
        """格式化主要问题"""
        lines = ["### 主要问题", ""]

        issues = []

        # 结构相关问题
        if goal == "structure":
            if metrics.get("large_classes_count", 0) > 0:
                count = metrics["large_classes_count"]
                issues.append(f"- 发现 {count} 个大型类（超过建议阈值）")

            if metrics.get("complex_methods_count", 0) > 0:
                count = metrics["complex_methods_count"]
                issues.append(f"- 发现 {count} 个复杂方法（圈复杂度过高）")

            if metrics.get("structure_violations", 0) > 0:
                violations = metrics["structure_violations"]
                issues.append(f"- 结构违规: {violations} 处")

        # 性能相关问题
        elif goal == "performance":
            if metrics.get("execution_time", 0) > 1.0:
                t = metrics["execution_time"]
                issues.append(f"- 执行时间过长: {t:.2f}秒")

            if metrics.get("memory_usage_mb", 0) > 100:
                mem = metrics["memory_usage_mb"]
                issues.append(f"- 内存占用较高: {mem:.1f}MB")

        # 简洁相关问题
        elif goal == "simplicity":
            if metrics.get("duplication_rate", 0) > 0.05:
                rate = metrics["duplication_rate"] * 100
                issues.append(f"- 代码重复率较高: {rate:.1f}%")

            if metrics.get("avg_complexity", 0) > 10:
                comp = metrics["avg_complexity"]
                issues.append(f"- 平均复杂度较高: {comp:.1f}")

        if not issues:
            issues.append("- 未发现严重问题（建议定期检查）")

        lines.extend(issues)
        lines.append("")
        return lines

    def _format_recommendations(self, current_metrics: Dict[str, Any], result: OptimizationResult, goal: str) -> list[str]:
        """格式化优化建议"""
        lines = ["## 优化建议", "", "### 最佳参数配置", "", "```yaml", "# LingFlow 自优化参数配置", ""]

        # 格式化最佳参数
        for key, value in sorted(result.best_params.items()):
            if isinstance(value, float):
                lines.append(f"{key}: {value:.2f}")
            else:
                lines.append(f"{value}")

        lines.extend(
            [
                "```",
                "",
                "### 预期改进",
                "",
            ]
        )

        # 计算预期改进
        if goal == "structure":
            current_violations = current_metrics.get("structure_violations", 0)
            if current_violations > 0:
                improvement_ratio = 0.6  # 假设改进60%
                expected_violations = int(current_violations * (1 - improvement_ratio))
                lines.append(f"- 结构违规: {current_violations} → {expected_violations} ({improvement_ratio * 100:.0f}% 改进)")

            if "avg_class_size" in current_metrics:
                current_size = current_metrics["avg_class_size"]
                new_max = result.best_params.get("max_class_size", 200)
                expected_size = min(current_size, new_max * 0.9)
                improvement = (current_size - expected_size) / current_size * 100 if current_size > 0 else 0
                lines.append(f"- 平均类大小: {current_size:.0f} → {expected_size:.0f} ({improvement:.0f}% 改进)")

        elif goal == "performance":
            if "execution_time" in current_metrics:
                current_time = current_metrics["execution_time"]
                expected_improvement = 0.3  # 假设改进30%
                expected_time = current_time * (1 - expected_improvement)
                lines.append(
                    f"- 执行时间: {current_time:.2f}s → {expected_time:.2f}s ({expected_improvement * 100:.0f}% 改进)"
                )

        lines.extend(["", f"**优化实验**: 运行了 {result.experiments} 次实验", f"**优化耗时**: {result.duration:.1f} 秒", ""])

        return lines

    def _format_comparison(self, current_metrics: Dict[str, Any], result: OptimizationResult) -> list[str]:
        """格式化详细对比"""
        lines = [
            "### 参数对比",
            "",
            "| 参数 | 当前值 | 建议值 | 说明 |",
            "|------|--------|--------|------|",
        ]

        # 生成对比表格
        current_params = current_metrics.get("current_params", {})

        for key in sorted(result.best_params.keys()):
            current = current_params.get(key, "默认")
            recommended = result.best_params[key]

            # 格式化值
            if isinstance(recommended, float):
                recommended_str = f"{recommended:.2f}"
            else:
                recommended_str = str(recommended)

            if isinstance(current, float):
                current_str = f"{current:.2f}"
            elif isinstance(current, int):
                current_str = str(current)
            else:
                current_str = str(current)

            # 生成说明
            if current != recommended and current != "默认":
                change = "↓" if recommended < current else "↑"
                note = f"建议{change}"
            else:
                note = "保持"

            lines.append(f"| {key} | {current_str} | {recommended_str} | {note} |")

        lines.append("")
        return lines

    def _format_implementation_steps(self, best_params: Dict[str, Any]) -> list[str]:
        """格式化实施步骤"""
        lines = [
            "## 实施步骤",
            "",
            "### 选项 1: 自动应用",
            "",
            "```bash",
            "# 确认后自动应用优化",
            "lingflow optimize apply --report <报告文件>",
            "```",
            "",
            "### 选项 2: 手动应用",
            "",
            "1. 创建或编辑配置文件 `~/.lingflow/config.yaml`：",
            "",
            "```yaml",
            "# 自优化参数",
            "structure_optimization:",
            "",
        ]

        # 生成配置示例
        for key, value in sorted(best_params.items()):
            if isinstance(value, float):
                lines.append(f"  {key}: {value:.2f}")
            else:
                lines.append(f"  {key}: {value}")

        lines.extend(
            [
                "```",
                "",
                "2. 验证配置：",
                "   ```bash",
                "   lingflow review",
                "   ```",
                "",
                "3. 如果满意，提交更改：",
                "   ```bash",
                "   git add ~/.lingflow/config.yaml",
                "   git commit -m 'opt: 应用自优化建议'",
                "   ```",
                "",
                "### 选项 3: 生成配置文件",
                "",
                "```bash",
                "# 生成新的配置文件",
                "lingflow optimize generate-config --report <报告文件>",
                "",
                "# 审查后手动应用",
                "vi ~/.lingflow/config_optimized.yaml",
                "```",
                "",
                "---",
                "",
            ]
        )

        return lines

    def _format_optimization_history(self, result: OptimizationResult) -> list[str]:
        """格式化优化历史"""
        lines = [
            "## 优化历史",
            "",
            "### 实验记录（前10次）",
            "",
            "| 实验 | 参数 | 分数 |",
            "|------|------|------|",
        ]

        # 只显示前10次
        for i, entry in enumerate(result.history[:10]):
            exp_id = entry.get("experiment_id", i)
            params = entry.get("params", {})
            score = entry.get("score", 0)

            # 简化参数显示
            param_str = ", ".join([f"{k}={v}" for k, v in list(params.items())[:3]])
            if len(params) > 3:
                param_str += ", ..."

            lines.append(f"| {exp_id} | {param_str} | {score:.2f} |")

        if len(result.history) > 10:
            lines.append("| ... | ... | ... |")
            lines.append(f"| 共 {len(result.history)} 次实验 | | |")

        lines.extend(["", "---", "", "*报告由 LingFlow 自动生成*", ""])

        return lines

    def save_report(self, report: str, output_path: str = None) -> str:
        """保存报告到文件

        Args:
            report: 报告内容
            output_path: 输出路径（可选）

        Returns:
            保存的文件路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"LINGFLOW_OPTIMIZATION_REPORT_{timestamp}.md"

        Path(output_path).write_text(report, encoding="utf-8")
        return output_path

    def print_summary(self, result: OptimizationResult, current_metrics: Dict[str, Any]):
        """打印优化摘要到控制台"""
        print("\n" + "=" * 60)
        print("📊 优化完成".center(60))
        print("=" * 60)

        print(f"\n✓ 实验次数: {result.experiments}")
        print(f"✓ 优化耗时: {result.duration:.1f} 秒")
        print(f"✓ 最佳分数: {result.best_score:.2f}")

        print("\n🎯 最佳参数:")
        for key, value in sorted(result.best_params.items()):
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

        if current_metrics.get("structure_violations"):
            print("\n📈 预期改进:")
            violations = current_metrics["structure_violations"]
            print(f"  结构违规: {violations} → {int(violations * 0.4)} (约60%改进)")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":  # pragma: no cover
    # 测试
    from lingflow.self_optimizer.evaluator import StructureEvaluator

    evaluator = StructureEvaluator("/home/ai/LingFlow/lingflow")
    metrics = evaluator.get_current_metrics()

    result = OptimizationResult(
        success=True,
        best_params={"max_class_size": 200, "max_complexity": 10, "max_method_count": 15},
        best_score=5.0,
        experiments=20,
        duration=45.2,
    )

    advisor = OptimizationAdvisor()
    report = advisor.generate_report(
        goal="structure", target="/home/ai/LingFlow/lingflow", current_metrics=metrics, optimization_result=result
    )

    print(report)
