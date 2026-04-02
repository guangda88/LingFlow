"""LingFlow 用户反馈收集器

收集和管理用户反馈，包括问题报告、功能请求和使用体验。
"""

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict


logger = logging.getLogger(__name__)


class FeedbackCategory(str, Enum):
    """反馈类别"""
    BUG = "bug"                    # Bug 报告
    FEATURE = "feature"            # 功能请求
    IMPROVEMENT = "improvement"    # 改进建议
    PERFORMANCE = "performance"    # 性能问题
    DOCUMENTATION = "documentation" # 文档问题
    USABILITY = "usability"        # 易用性问题
    OTHER = "other"                # 其他


class FeedbackSeverity(str, Enum):
    """反馈严重性"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Feedback:
    """用户反馈"""
    id: str
    category: FeedbackCategory
    severity: FeedbackSeverity
    title: str
    description: str
    timestamp: str
    user: Optional[str] = None
    email: Optional[str] = None
    reproduction_steps: Optional[List[str]] = None
    environment: Optional[Dict[str, Any]] = None
    logs: Optional[str] = None
    stack_trace: Optional[str] = None
    status: str = "open"  # open, in_progress, resolved, closed
    resolution: Optional[str] = None
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["category"] = self.category.value
        data["severity"] = self.severity.value
        return data

    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class FeedbackCollector:
    """用户反馈收集器"""

    def __init__(
        self,
        storage_dir: Optional[str] = None,
        auto_report: bool = False,
        report_url: Optional[str] = None,
    ) -> None:
        """初始化反馈收集器

        Args:
            storage_dir: 反馈存储目录
            auto_report: 是否自动上报到远程
            report_url: 远程上报 URL
        """
        self.storage_dir = Path(storage_dir or ".lingflow/feedback")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.auto_report = auto_report
        self.report_url = report_url
        self._feedbacks: List[Feedback] = []
        self._load_feedbacks()

    def _load_feedbacks(self) -> None:
        """从存储加载反馈"""
        feedback_file = self.storage_dir / "feedbacks.json"
        if feedback_file.exists():
            try:
                with open(feedback_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data.get("feedbacks", []):
                        self._feedbacks.append(self._dict_to_feedback(item))
            except Exception as e:
                logger.warning("加载反馈失败: %s", e)

    def _dict_to_feedback(self, data: Dict[str, Any]) -> Feedback:
        """从字典创建反馈对象"""
        return Feedback(
            id=data["id"],
            category=FeedbackCategory(data["category"]),
            severity=FeedbackSeverity(data["severity"]),
            title=data["title"],
            description=data["description"],
            timestamp=data["timestamp"],
            user=data.get("user"),
            email=data.get("email"),
            reproduction_steps=data.get("reproduction_steps"),
            environment=data.get("environment"),
            logs=data.get("logs"),
            stack_trace=data.get("stack_trace"),
            status=data.get("status", "open"),
            resolution=data.get("resolution"),
            resolved_at=data.get("resolved_at"),
        )

    def _save_feedbacks(self) -> None:
        """保存反馈到存储"""
        feedback_file = self.storage_dir / "feedbacks.json"
        data = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "total_count": len(self._feedbacks),
            "feedbacks": [f.to_dict() for f in self._feedbacks],
        }
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def submit_feedback(
        self,
        category: FeedbackCategory,
        severity: FeedbackSeverity,
        title: str,
        description: str,
        user: Optional[str] = None,
        email: Optional[str] = None,
        reproduction_steps: Optional[List[str]] = None,
        environment: Optional[Dict[str, Any]] = None,
        logs: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> Feedback:
        """提交用户反馈

        Args:
            category: 反馈类别（Bug/Feature/Improvement等）
            severity: 严重性级别（Low/Medium/High/Critical）
            title: 简短的反馈标题
            description: 详细描述
            user: 用户标识
            email: 联系邮箱
            reproduction_steps: 复现问题的步骤列表
            environment: 环境信息字典
            logs: 相关日志文本
            stack_trace: 错误堆栈跟踪

        Returns:
            创建的 Feedback 对象

        Raises:
            ValueError: 如果必填参数为空

        Example:
            >>> collector.submit_feedback(
            ...     category=FeedbackCategory.BUG,
            ...     severity=FeedbackSeverity.HIGH,
            ...     title="登录失败",
            ...     description="用户无法登录系统"
            ... )
        """
        # 验证必填参数
        self._validate_feedback_input(title, description)

        # 创建反馈对象
        feedback = self._create_feedback(
            category=category,
            severity=severity,
            title=title,
            description=description,
            user=user,
            email=email,
            reproduction_steps=reproduction_steps,
            environment=environment,
            logs=logs,
            stack_trace=stack_trace,
        )

        # 存储并上报
        self._store_feedback(feedback)
        self._auto_report_if_enabled(feedback)

        logger.info(f"收到反馈: [{feedback.id}] {feedback.title}")
        return feedback

    def _validate_feedback_input(self, title: str, description: str) -> None:
        """验证反馈输入参数

        Args:
            title: 反馈标题
            description: 反馈描述

        Raises:
            ValueError: 如果必填参数为空
        """
        if not title or not title.strip():
            raise ValueError("反馈标题不能为空")
        if not description or not description.strip():
            raise ValueError("反馈描述不能为空")

    def _create_feedback(
        self,
        category: FeedbackCategory,
        severity: FeedbackSeverity,
        title: str,
        description: str,
        user: Optional[str] = None,
        email: Optional[str] = None,
        reproduction_steps: Optional[List[str]] = None,
        environment: Optional[Dict[str, Any]] = None,
        logs: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> Feedback:
        """创建反馈对象

        Args:
            与 submit_feedback 相同

        Returns:
            新创建的 Feedback 对象
        """
        import uuid

        return Feedback(
            id=str(uuid.uuid4())[:8],
            category=category,
            severity=severity,
            title=title.strip(),
            description=description.strip(),
            timestamp=datetime.now().isoformat(),
            user=user,
            email=email,
            reproduction_steps=reproduction_steps,
            environment=environment,
            logs=logs,
            stack_trace=stack_trace,
        )

    def _store_feedback(self, feedback: Feedback) -> None:
        """存储反馈到内存和持久化存储

        Args:
            feedback: 要存储的反馈对象
        """
        self._feedbacks.append(feedback)
        self._save_feedbacks()

    def _auto_report_if_enabled(self, feedback: Feedback) -> None:
        """如果启用了自动上报，则上报反馈

        Args:
            feedback: 要上报的反馈对象
        """
        if self.auto_report and self.report_url:
            self._report_to_remote(feedback)

    def submit_bug_report(
        self,
        title: str,
        description: str,
        reproduction_steps: Optional[List[str]] = None,
        stack_trace: Optional[str] = None,
        severity: FeedbackSeverity = FeedbackSeverity.MEDIUM,
    ) -> Feedback:
        """快捷提交 Bug 报告"""
        import platform
        import sys

        environment = {
            "os": platform.system(),
            "python_version": sys.version,
            "lingflow_version": self._get_lingflow_version(),
        }

        return self.submit_feedback(
            category=FeedbackCategory.BUG,
            severity=severity,
            title=title,
            description=description,
            reproduction_steps=reproduction_steps,
            environment=environment,
            stack_trace=stack_trace,
        )

    def _get_lingflow_version(self) -> str:
        """获取 LingFlow 版本"""
        try:
            from lingflow import __version__
            return __version__
        except:
            return "unknown"

    def _report_to_remote(self, feedback: Feedback) -> bool:
        """上报反馈到远程服务器"""
        if not self.report_url:
            return False

        try:
            import urllib.request

            data = json.dumps(feedback.to_dict()).encode("utf-8")
            req = urllib.request.Request(
                self.report_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"上报失败: {e}")
            return False

    def get_feedbacks(
        self,
        category: Optional[FeedbackCategory] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Feedback]:
        """获取反馈列表

        Args:
            category: 按类别过滤
            status: 按状态过滤
            limit: 返回数量限制

        Returns:
            反馈列表
        """
        feedbacks = self._feedbacks

        if category:
            feedbacks = [f for f in feedbacks if f.category == category]
        if status:
            feedbacks = [f for f in feedbacks if f.status == status]

        # 按时间倒序
        feedbacks.sort(key=lambda f: f.timestamp, reverse=True)

        if limit:
            feedbacks = feedbacks[:limit]

        return feedbacks

    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """获取单个反馈"""
        for f in self._feedbacks:
            if f.id == feedback_id:
                return f
        return None

    def update_status(
        self,
        feedback_id: str,
        status: str,
        resolution: Optional[str] = None,
    ) -> bool:
        """更新反馈状态

        Args:
            feedback_id: 反馈 ID
            status: 新状态
            resolution: 解决方案说明

        Returns:
            是否成功
        """
        feedback = self.get_feedback(feedback_id)
        if not feedback:
            return False

        feedback.status = status
        if resolution:
            feedback.resolution = resolution
        if status == "resolved":
            feedback.resolved_at = datetime.now().isoformat()

        self._save_feedbacks()
        logger.info(f"更新反馈状态: [{feedback_id}] -> {status}")
        return True

    def get_statistics(self) -> Dict[str, Any]:
        """获取反馈统计信息"""
        total = len(self._feedbacks)
        by_category: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        by_status: Dict[str, int] = {}

        for f in self._feedbacks:
            by_category[f.category.value] = by_category.get(f.category.value, 0) + 1
            by_severity[f.severity.value] = by_severity.get(f.severity.value, 0) + 1
            by_status[f.status] = by_status.get(f.status, 0) + 1

        return {
            "total": total,
            "by_category": by_category,
            "by_severity": by_severity,
            "by_status": by_status,
            "open": by_status.get("open", 0),
            "resolved": by_status.get("resolved", 0),
        }

    def export_markdown(self, output_path: Optional[str] = None) -> str:
        """导出反馈为 Markdown 格式

        Args:
            output_path: 输出文件路径

        Returns:
            Markdown 内容
        """
        lines = [
            "# 用户反馈报告",
            "",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**总反馈数**: {len(self._feedbacks)}",
            "",
        ]

        # 统计信息
        stats = self.get_statistics()
        lines.extend([
            "## 统计概览",
            "",
            f"- **总计**: {stats['total']}",
            f"- **待处理**: {stats['open']}",
            f"- **已解决**: {stats['resolved']}",
            "",
            "### 按类别",
            "",
        ])
        for cat, count in stats["by_category"].items():
            lines.append(f"- {cat}: {count}")

        lines.extend([
            "",
            "### 按严重性",
            "",
        ])
        for sev, count in stats["by_severity"].items():
            lines.append(f"- {sev}: {count}")

        # 详细列表
        lines.extend([
            "",
            "## 反馈详情",
            "",
        ])

        for f in self._feedbacks:
            if f.status != "closed":
                lines.extend([
                    f"### {f.id}: {f.title}",
                    "",
                    f"- **类别**: {f.category.value}",
                    f"- **严重性**: {f.severity.value}",
                    f"- **状态**: {f.status}",
                    f"- **时间**: {f.timestamp}",
                    "",
                    f"**描述**: {f.description}",
                    "",
                ])
                if f.reproduction_steps:
                    lines.extend([
                        "**复现步骤**:",
                        "",
                    ])
                    for i, step in enumerate(f.reproduction_steps, 1):
                        lines.append(f"{i}. {step}")
                    lines.append("")
                if f.resolution:
                    lines.extend([
                        f"**解决方案**: {f.resolution}",
                        "",
                    ])

        content = "\n".join(lines)

        if output_path:
            Path(output_path).write_text(content, encoding="utf-8")
            logger.info(f"反馈报告已导出到: {output_path}")

        return content


# 全局单例
_collector: Optional[FeedbackCollector] = None


def get_feedback_collector() -> FeedbackCollector:
    """获取全局反馈收集器实例"""
    global _collector
    if _collector is None:
        _collector = FeedbackCollector()
    return _collector


# 便捷函数
def submit_bug(
    title: str,
    description: str,
    reproduction_steps: Optional[List[str]] = None,
    stack_trace: Optional[str] = None,
) -> Feedback:
    """快捷提交 Bug"""
    return get_feedback_collector().submit_bug_report(
        title=title,
        description=description,
        reproduction_steps=reproduction_steps,
        stack_trace=stack_trace,
    )


def list_feedbacks(
    category: Optional[FeedbackCategory] = None,
    status: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Feedback]:
    """获取反馈列表"""
    return get_feedback_collector().get_feedbacks(
        category=category,
        status=status,
        limit=limit,
    )
