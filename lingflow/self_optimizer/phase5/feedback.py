"""
反馈循环系统

收集规则应用的效果，形成完整的学习闭环。
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter


class FeedbackCollector:
    """反馈收集器 - 收集规则应用的效果反馈"""

    def __init__(self, storage_path: Optional[str] = None):
        """初始化反馈收集器

        Args:
            storage_path: 反馈数据存储路径
        """
        if storage_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            storage_path = project_root / ".lingflow" / "feedback.json"

        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self._feedback_data: Dict[str, List[Dict]] = self._load_feedback()

    def _load_feedback(self) -> Dict[str, List[Dict]]:
        """加载反馈数据"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"rule_feedback": [], "application_feedback": []}

    def _save_feedback(self) -> None:
        """保存反馈数据"""
        with open(self.storage_path, 'w') as f:
            json.dump(self._feedback_data, f, indent=2)

    def record_rule_application(
        self,
        rule_id: str,
        file_path: str,
        line: int,
        accepted: bool,
        user_feedback: Optional[str] = None
    ) -> None:
        """记录规则应用反馈

        Args:
            rule_id: 规则ID
            file_path: 文件路径
            line: 行号
            accepted: 用户是否接受建议
            user_feedback: 用户额外反馈
        """
        feedback = {
            "rule_id": rule_id,
            "file_path": file_path,
            "line": line,
            "accepted": accepted,
            "user_feedback": user_feedback,
            "timestamp": datetime.now().isoformat(),
        }

        self._feedback_data["rule_feedback"].append(feedback)
        self._save_feedback()

    def record_application_stats(
        self,
        scan_id: str,
        total_files: int,
        total_issues: int,
        fixed_issues: int,
        duration_seconds: float
    ) -> None:
        """记录应用统计

        Args:
            scan_id: 扫描ID
            total_files: 扫描的文件总数
            total_issues: 发现的问题总数
            fixed_issues: 修复的问题数
            duration_seconds: 扫描耗时
        """
        stats = {
            "scan_id": scan_id,
            "total_files": total_files,
            "total_issues": total_issues,
            "fixed_issues": fixed_issues,
            "fix_rate": fixed_issues / total_issues if total_issues > 0 else 0,
            "duration_seconds": duration_seconds,
            "timestamp": datetime.now().isoformat(),
        }

        self._feedback_data["application_feedback"].append(stats)
        self._save_feedback()

    def get_rule_effectiveness(self, rule_id: str, days: int = 30) -> Dict[str, Any]:
        """获取规则效果统计

        Args:
            rule_id: 规则ID
            days: 统计天数

        Returns:
            效果统计
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        rule_feedbacks = [
            f for f in self._feedback_data["rule_feedback"]
            if f["rule_id"] == rule_id
            and datetime.fromisoformat(f["timestamp"]) > cutoff_time
        ]

        if not rule_feedbacks:
            return {
                "rule_id": rule_id,
                "total_applications": 0,
                "acceptance_rate": 0,
                "avg_confidence": 0,
            }

        total = len(rule_feedbacks)
        accepted = sum(1 for f in rule_feedbacks if f["accepted"])

        return {
            "rule_id": rule_id,
            "total_applications": total,
            "accepted_count": accepted,
            "acceptance_rate": accepted / total,
            "recent_feedback": rule_feedbacks[-10:],  # 最近10条
        }

    def get_all_feedback(
        self,
        days: int = 30
    ) -> Dict[str, Any]:
        """获取所有反馈统计

        Args:
            days: 统计天数

        Returns:
            反馈统计
        """
        cutoff_time = datetime.now() - timedelta(days=days)

        recent_rule_feedback = [
            f for f in self._feedback_data["rule_feedback"]
            if datetime.fromisoformat(f["timestamp"]) > cutoff_time
        ]

        recent_app_feedback = [
            f for f in self._feedback_data["application_feedback"]
            if datetime.fromisoformat(f["timestamp"]) > cutoff_time
        ]

        # 按规则ID统计
        rule_stats = Counter(f["rule_id"] for f in recent_rule_feedback)

        # 接受率统计
        acceptance_by_rule = {}
        for rule_id in rule_stats.keys():
            rule_feedbacks = [f for f in recent_rule_feedback if f["rule_id"] == rule_id]
            accepted = sum(1 for f in rule_feedbacks if f["accepted"])
            acceptance_by_rule[rule_id] = {
                "total": len(rule_feedbacks),
                "accepted": accepted,
                "rate": accepted / len(rule_feedbacks)
            }

        return {
            "period_days": days,
            "total_rule_feedback": len(recent_rule_feedback),
            "total_application_feedback": len(recent_app_feedback),
            "top_rules": dict(rule_stats.most_common(10)),
            "acceptance_by_rule": acceptance_by_rule,
            "avg_fix_rate": (
                sum(f.get("fix_rate", 0) for f in recent_app_feedback) / len(recent_app_feedback)
                if recent_app_feedback
                else 0
            ),
        }


class RuleQualityAdjuster:
    """规则质量调整器 - 根据反馈调整规则质量"""

    def __init__(self, knowledge_base, feedback_collector: FeedbackCollector):
        """初始化质量调整器

        Args:
            knowledge_base: 知识库实例
            feedback_collector: 反馈收集器实例
        """
        self.knowledge_base = knowledge_base
        self.feedback_collector = feedback_collector

    def adjust_rule_scores(self, days: int = 30) -> Dict[str, Any]:
        """根据反馈调整规则质量分数

        Args:
            days: 统计天数

        Returns:
            调整结果
        """
        all_rules = self.knowledge_base.get_all_rules(limit=1000)
        adjustments = []

        for rule in all_rules:
            effectiveness = self.feedback_collector.get_rule_effectiveness(
                rule.id, days
            )

            if effectiveness["total_applications"] >= 5:  # 至少5次应用
                new_score = self._calculate_adjusted_score(
                    rule.quality_score,
                    effectiveness["acceptance_rate"]
                )

                if new_score != rule.quality_score:
                    # 更新规则
                    rule.quality_score = new_score

                    # 根据新分数调整状态
                    if new_score >= 0.8 and rule.status == "draft":
                        rule.status = "approved"
                    elif new_score < 0.4 and rule.status == "approved":
                        rule.status = "draft"

                    self.knowledge_base.add_rule(rule)
                    adjustments.append({
                        "rule_id": rule.id,
                        "old_score": rule.quality_score,
                        "new_score": new_score,
                        "applications": effectiveness["total_applications"],
                        "acceptance_rate": effectiveness["acceptance_rate"],
                    })

        return {
            "total_adjustments": len(adjustments),
            "adjustments": adjustments,
        }

    def _calculate_adjusted_score(
        self,
        current_score: float,
        acceptance_rate: float
    ) -> float:
        """计算调整后的质量分数

        Args:
            current_score: 当前质量分数
            acceptance_rate: 接受率

        Returns:
            调整后的质量分数
        """
        # 接受率权重 40%，原始分数权重 60%
        adjusted = (current_score * 0.6) + (acceptance_rate * 0.4)

        # 限制在 0-1 范围内
        return max(0.0, min(1.0, adjusted))


class FeedbackLoop:
    """反馈循环 - 整合收集、分析和调整"""

    def __init__(self, knowledge_base):
        """初始化反馈循环

        Args:
            knowledge_base: 知识库实例
        """
        self.knowledge_base = knowledge_base
        self.collector = FeedbackCollector()
        self.adjuster = RuleQualityAdjuster(knowledge_base, self.collector)

    def run_cycle(
        self,
        scan_id: str,
        scan_results: Dict[str, List[Dict]],
        duration_seconds: float
    ) -> Dict[str, Any]:
        """运行完整的反馈循环

        Args:
            scan_id: 扫描ID
            scan_results: 扫描结果
            duration_seconds: 扫描耗时

        Returns:
            循环结果
        """
        # 1. 记录应用统计
        total_files = len(scan_results)
        total_issues = sum(len(issues) for issues in scan_results.values())
        fixed_issues = sum(
            1
            for issues in scan_results.values()
            for issue in issues
            if isinstance(issue, dict) and issue.get("fixed", False)
        )

        self.collector.record_application_stats(
            scan_id=scan_id,
            total_files=total_files,
            total_issues=total_issues,
            fixed_issues=fixed_issues,
            duration_seconds=duration_seconds
        )

        # 2. 调整规则质量分数
        adjustments = self.adjuster.adjust_rule_scores()

        # 3. 生成反馈报告
        feedback_summary = self.collector.get_all_feedback()

        # 4. 获取知识库统计
        kb_stats = self.knowledge_base.get_statistics()

        return {
            "scan_id": scan_id,
            "application_stats": {
                "total_files": total_files,
                "total_issues": total_issues,
                "fixed_issues": fixed_issues,
                "duration_seconds": duration_seconds,
            },
            "quality_adjustments": adjustments,
            "feedback_summary": feedback_summary,
            "knowledge_base_stats": kb_stats,
        }

    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """获取改进建议

        Returns:
            改进建议列表
        """
        suggestions = []

        # 1. 低接受率规则
        all_rules = self.knowledge_base.get_all_rules(limit=1000)
        for rule in all_rules:
            effectiveness = self.collector.get_rule_effectiveness(rule.id)
            if effectiveness["total_applications"] >= 5:
                if effectiveness["acceptance_rate"] < 0.5:
                    suggestions.append({
                        "type": "low_acceptance",
                        "rule_id": rule.id,
                        "acceptance_rate": effectiveness["acceptance_rate"],
                        "suggestion": f"Consider reviewing or disabling rule '{rule.name}' due to low acceptance rate",
                    })

        # 2. 高误报规则
        feedback_summary = self.collector.get_all_feedback()
        for rule_id, stats in feedback_summary.get("acceptance_by_rule", {}).items():
            if stats["total"] >= 10 and stats["rate"] < 0.3:
                suggestions.append({
                    "type": "high_false_positive",
                    "rule_id": rule_id,
                    "acceptance_rate": stats["rate"],
                    "suggestion": f"Rule '{rule_id}' may have high false positive rate. Consider refining the pattern.",
                })

        return suggestions


__all__ = [
    "FeedbackCollector",
    "RuleQualityAdjuster",
    "FeedbackLoop",
]
