"""LingFlow 对话上下文管理器

自动跟踪对话进度，在 token 限制时压缩上下文到持久化存储。
"""

import json
import logging
import os
import secrets
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .auto_resume import save_resume_markdown
from lingflow.compression.token_estimator import TokenEstimator
from .session_lifecycle import SessionLifecycleManager, LifecyclePhase  # noqa: F401

logger = logging.getLogger(__name__)

_SHARED_TOKEN_ESTIMATOR: Optional[TokenEstimator] = None


def _get_token_estimator() -> TokenEstimator:
    global _SHARED_TOKEN_ESTIMATOR
    if _SHARED_TOKEN_ESTIMATOR is None:
        _SHARED_TOKEN_ESTIMATOR = TokenEstimator()
    return _SHARED_TOKEN_ESTIMATOR


DEFAULT_CONTEXT_DIR = Path(os.getenv("LINGFLOW_CONTEXT_DIR", Path.home() / ".claude" / "projects" / "lingflow" / "context"))


@dataclass
class ContextSnapshot:
    """上下文快照"""

    timestamp: str
    session_id: str
    tasks_completed: List[str] = field(default_factory=list)
    tasks_pending: List[str] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)
    important_files: Dict[str, str] = field(default_factory=dict)
    context_summary: str = ""
    next_steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextSnapshot":
        return cls(**data)


class ContextManager:
    """对话上下文管理器

    自动跟踪对话状态，提供上下文压缩和恢复功能。
    """

    # 估计的 token 限制（保守估计）
    ESTIMATED_TOKEN_LIMIT = 180000
    WARNING_THRESHOLD = 0.85  # 85% 时警告
    COMPRESS_THRESHOLD = 0.90  # 90% 时压缩

    def __init__(self, storage_dir: Optional[str] = None):
        """初始化上下文管理器

        Args:
            storage_dir: 上下文存储目录 (默认使用用户主目录下的 .claude/projects/lingflow/context)
        """
        if storage_dir is None:
            self.storage_dir = DEFAULT_CONTEXT_DIR
        else:
            self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 当前会话状态
        self.session_id = self._generate_session_id()
        self.message_count = 0
        self.estimated_tokens = 0
        self._cumulative_tokens = 0

        # 对话消息列表（用于实际压缩）
        self._messages: List[Dict[str, str]] = []

        # 上下文数据
        self.snapshot = ContextSnapshot(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
        )

        # 关键词跟踪（用于识别重要消息）
        self._important_keywords: Set[str] = {
            "fix",
            "bug",
            "implement",
            "create",
            "refactor",
            "critical",
            "important",
            "must",
            "should",
            "todo",
            "task",
            "完成",
            "修复",
            "实现",
        }

        # 智能压缩器（懒加载）
        self._smart_compressor = None

        # 预算管理器
        self._budget_manager = None

        # 退化检测器
        self._degradation_detector = None

        # 会话生命周期管理器（灵依任务：20万警戒/30万阈值）
        self._lifecycle_manager: Optional[SessionLifecycleManager] = None

        # 加载之前的上下文
        self._load_last_context()

    def _generate_session_id(self) -> str:
        """生成会话 ID (使用加密安全的随机生成器)"""
        return secrets.token_urlsafe(12)

    def _load_last_context(self) -> Optional[ContextSnapshot]:
        """加载上次的上下文"""
        last_file = self.storage_dir / "last_context.json"
        if last_file.exists():
            try:
                with open(last_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.last_context = ContextSnapshot.from_dict(data)
                    logger.info("已加载上次上下文: %s", self.last_context.session_id)
                    return self.last_context
            except Exception as e:
                logger.warning("加载上次上下文失败: %s", e)
        self.last_context = None
        return None

    def record_message(self, role: str, content: str, is_important: bool = False) -> None:
        """记录一条消息

        Args:
            role: 角色 (user/assistant/system)
            content: 消息内容
            is_important: 是否为重要消息
        """
        self.message_count += 1
        new_tokens = _get_token_estimator().count_tokens(content)
        self.estimated_tokens += new_tokens
        self._cumulative_tokens += new_tokens

        # 保存消息到列表
        self._messages.append({"role": role, "content": content})

        # 自动检测重要内容
        if not is_important:
            is_important = self._is_important_message(content)

        if is_important:
            self._extract_important_info(content)

        # 检查是否需要压缩（模型退化预算）
        self._check_and_warn()

        # 检查会话生命周期（灵依任务）
        self._check_lifecycle()

    def _is_important_message(self, content: str) -> bool:
        """检测是否为重要消息"""
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in self._important_keywords)

    def _extract_important_info(self, content: str) -> None:
        """从消息中提取重要信息"""
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            # 提取任务相关信息
            if line.startswith("◻") or line.startswith("- [ ]"):
                task = line.lstrip("◻- [ ]").strip()
                if task and task not in self.snapshot.tasks_pending:
                    self.snapshot.tasks_pending.append(task)
            elif line.startswith("◼") or line.startswith("- [x]"):
                task = line.lstrip("◼- [x]").strip()
                if task and task not in self.snapshot.tasks_completed:
                    self.snapshot.tasks_completed.append(task)

    def add_task(self, task: str, completed: bool = False) -> None:
        """添加任务

        Args:
            task: 任务描述
            completed: 是否已完成
        """
        task_list = self.snapshot.tasks_completed if completed else self.snapshot.tasks_pending
        if task not in task_list:
            task_list.append(task)
            self._save_snapshot()

    def complete_task(self, task: str) -> None:
        """标记任务完成"""
        if task in self.snapshot.tasks_pending:
            self.snapshot.tasks_pending.remove(task)
        if task not in self.snapshot.tasks_completed:
            self.snapshot.tasks_completed.append(task)
        self._save_snapshot()

    def add_decision(self, decision: str) -> None:
        """记录关键决策"""
        if decision not in self.snapshot.key_decisions:
            self.snapshot.key_decisions.append(decision)
            self._save_snapshot()

    def add_file(self, path: str, description: str) -> None:
        """记录重要文件"""
        self.snapshot.important_files[path] = description
        self._save_snapshot()

    def set_next_steps(self, steps: List[str]) -> None:
        """设置下一步计划"""
        self.snapshot.next_steps = steps
        self._save_snapshot()

    def _check_and_warn(self) -> None:
        """检查 token 使用情况并警告"""
        if self._budget_manager is None:
            from .budget import ContextBudgetManager

            self._budget_manager = ContextBudgetManager(
                max_tokens=self.ESTIMATED_TOKEN_LIMIT,
            )

        budget_status = self._budget_manager.check_budget(self.estimated_tokens)

        if budget_status.level.value == "emergency":
            logger.warning("Token 使用率 %s，紧急交接", budget_status.usage_ratio)
            self.compress_now()
            self.generate_handoff(reason="emergency_token_limit")
        elif budget_status.level.value == "critical":
            logger.warning("Token 使用率 %s，严重退化，立即压缩", budget_status.usage_ratio)
            self.compress_now()
        elif budget_status.level.value == "warning":
            logger.warning("Token 使用率 %s，建议压缩上下文", budget_status.usage_ratio)
            self.compress_now()
        elif budget_status.level.value == "moderate":
            logger.info("Token 使用率 %s，接近安全阈值", budget_status.usage_ratio)

    def _check_lifecycle(self) -> None:
        """检查会话生命周期状态（灵依任务）"""
        if self._lifecycle_manager is None:
            self._lifecycle_manager = SessionLifecycleManager(
                storage_dir=self.storage_dir,
            )

        status = self._lifecycle_manager.check(self._cumulative_tokens)

        if status.phase == LifecyclePhase.WARNING:
            logger.warning(
                "会话生命周期预警: %s (%s / %s tokens)",
                status.message,
                f"{self._cumulative_tokens:,}",
                f"{self._lifecycle_manager.critical_threshold:,}",
            )
        elif status.phase == LifecyclePhase.EXPIRED:
            logger.warning("会话已过期，建议开始新会话")
            summary = self._lifecycle_manager.create_session_summary(
                session_id=self.session_id,
                total_tokens=self._cumulative_tokens,
                total_messages=self.message_count,
                tasks_completed=self.snapshot.tasks_completed,
                tasks_pending=self.snapshot.tasks_pending,
                key_decisions=self.snapshot.key_decisions,
                important_files=self.snapshot.important_files,
                next_steps=self.snapshot.next_steps,
                handoff_reason="lifecycle_expired",
            )
            self._lifecycle_manager.save_session_summary(summary)

    def _save_snapshot(self) -> None:
        """保存当前快照"""
        self.snapshot.timestamp = datetime.now().isoformat()
        snapshot_file = self.storage_dir / f"{self.session_id}.json"
        last_file = self.storage_dir / "last_context.json"

        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(self.snapshot.to_dict(), f, ensure_ascii=False, indent=2)

        with open(last_file, "w", encoding="utf-8") as f:
            json.dump(self.snapshot.to_dict(), f, ensure_ascii=False, indent=2)

        # 保存到会话文件（用于快速恢复）
        session_file = self.storage_dir / "session.json"
        session_data = {
            "timestamp": self.snapshot.timestamp,
            "summary": self._get_brief_summary(),
            "tasks": [{"name": t, "done": True} for t in self.snapshot.tasks_completed]
            + [{"name": t, "done": False} for t in self.snapshot.tasks_pending],
            "next_steps": self.snapshot.next_steps,
            "session_id": self.session_id,
        }
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        # 保存 Markdown 格式（用于自动恢复显示）
        tasks = [{"name": t, "done": True} for t in self.snapshot.tasks_completed] + [
            {"name": t, "done": False} for t in self.snapshot.tasks_pending
        ]
        save_resume_markdown(tasks=tasks, next_steps=self.snapshot.next_steps, summary=self._get_brief_summary())

    def _get_brief_summary(self) -> str:
        """获取简短摘要"""
        parts = []
        if self.snapshot.tasks_completed:
            parts.append(f"已完成 {len(self.snapshot.tasks_completed)} 个任务")
        if self.snapshot.tasks_pending:
            parts.append(f"待完成 {len(self.snapshot.tasks_pending)} 个任务")
        if self.snapshot.key_decisions:
            parts.append(f"做出 {len(self.snapshot.key_decisions)} 个关键决策")
        return "; ".join(parts) if parts else "进行中"

    def _get_smart_compressor(self):
        """懒加载 SmartContextCompressor"""
        if self._smart_compressor is None:
            from lingflow.compression.smart_compressor import (
                SmartContextCompressor,
                CompressionConfig as SmartCompressionConfig,
            )

            config = SmartCompressionConfig(
                max_tokens=self.ESTIMATED_TOKEN_LIMIT,
                warning_threshold=self.WARNING_THRESHOLD,
            )
            self._smart_compressor = SmartContextCompressor(config=config)
        return self._smart_compressor

    def compress_now(self) -> str:
        """立即压缩当前上下文

        使用 SmartContextCompressor 实际压缩内存中的消息列表，
        同时生成 Markdown 摘要持久化到磁盘。

        Returns:
            压缩后的上下文摘要，可用于新会话
        """
        # 使用 SmartContextCompressor 压缩内存中的消息
        if self._messages:
            compressor = self._get_smart_compressor()
            result = compressor.compress(
                self._messages,
                target_tokens=int(self.ESTIMATED_TOKEN_LIMIT * 0.4),
            )
            self._messages = result.compressed_messages
            self.estimated_tokens = result.compressed_tokens
            logger.info(
                f"SmartContextCompressor: {result.original_tokens} -> "
                f"{result.compressed_tokens} tokens "
                f"({result.compression_ratio:.1%} reduction)"
            )

        # 生成摘要
        summary_parts = [
            "# LingFlow 对话上下文摘要",
            "",
            f"**会话 ID**: {self.session_id}",
            f"**时间**: {self.snapshot.timestamp}",
            f"**消息数**: {self.message_count}",
            f"**估计 Token**: {self.estimated_tokens}",
            "",
        ]

        if self.snapshot.tasks_completed:
            summary_parts.extend(
                [
                    f"## 已完成任务 ({len(self.snapshot.tasks_completed)})",
                    "",
                ]
            )
            for task in self.snapshot.tasks_completed:
                summary_parts.append(f"- ✅ {task}")
            summary_parts.append("")

        if self.snapshot.tasks_pending:
            summary_parts.extend(
                [
                    f"## 待完成任务 ({len(self.snapshot.tasks_pending)})",
                    "",
                ]
            )
            for task in self.snapshot.tasks_pending:
                summary_parts.append(f"- ◻ {task}")
            summary_parts.append("")

        if self.snapshot.key_decisions:
            summary_parts.extend(
                [
                    "## 关键决策",
                    "",
                ]
            )
            for decision in self.snapshot.key_decisions:
                summary_parts.append(f"- {decision}")
            summary_parts.append("")

        if self.snapshot.important_files:
            summary_parts.extend(
                [
                    "## 重要文件",
                    "",
                ]
            )
            for path, desc in self.snapshot.important_files.items():
                summary_parts.append(f"- `{path}`: {desc}")
            summary_parts.append("")

        if self.snapshot.next_steps:
            summary_parts.extend(
                [
                    "## 下一步计划",
                    "",
                ]
            )
            for i, step in enumerate(self.snapshot.next_steps, 1):
                summary_parts.append(f"{i}. {step}")
            summary_parts.append("")

        summary = "\n".join(summary_parts)
        self.snapshot.context_summary = summary
        self._save_snapshot()

        # 同时保存到专门的恢复文件
        recovery_file = self.storage_dir / "RECOVERY_CONTEXT.md"
        recovery_file.write_text(summary, encoding="utf-8")

        logger.info("上下文已压缩，保存到: %s", recovery_file)
        return summary

    def get_recovery_summary(self) -> str:
        """获取恢复摘要（用于新会话）"""
        recovery_file = self.storage_dir / "RECOVERY_CONTEXT.md"
        if recovery_file.exists():
            return recovery_file.read_text(encoding="utf-8")

        # 如果没有恢复文件，生成当前摘要
        return self.compress_now()

    def generate_handoff(self, reason: str = "token_limit") -> "HandoffDocument":  # noqa: F821
        """生成交接文档

        当上下文接近退化阈值时调用，生成结构化的交接文档。

        Args:
            reason: 交接原因

        Returns:
            HandoffDocument 实例
        """
        from .handoff import HandoffDocument

        degradation_types = []
        if self._messages:
            if self._degradation_detector is None:
                from .degradation import DegradationDetector

                self._degradation_detector = DegradationDetector()
            report = self._degradation_detector.get_health_score(self._messages)
            if report.health.value != "healthy":
                degradation_types = [t.value for t in report.detected_types]

        doc = HandoffDocument.from_context_snapshot(
            self.snapshot,
            reason=reason,
            tasks_in_progress=[
                t for t in self.snapshot.tasks_pending if any(kw in t.lower() for kw in ["wip", "in progress", "进行中"])
            ],
            degradation_detected=len(degradation_types) > 0,
            degradation_types=degradation_types,
            token_usage_at_handoff=self.estimated_tokens,
        )

        handoff_file = self.storage_dir / "HANDOFF.md"
        handoff_file.write_text(doc.to_markdown(), encoding="utf-8")

        handoff_json = self.storage_dir / "handoff.json"
        handoff_json.write_text(doc.to_json(), encoding="utf-8")

        logger.info("交接文档已生成: %s", handoff_file)
        return doc

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        status = {
            "session_id": self.session_id,
            "message_count": self.message_count,
            "estimated_tokens": self.estimated_tokens,
            "cumulative_tokens": self._cumulative_tokens,
            "token_usage_ratio": self.estimated_tokens / self.ESTIMATED_TOKEN_LIMIT,
            "tasks_completed": len(self.snapshot.tasks_completed),
            "tasks_pending": len(self.snapshot.tasks_pending),
        }

        if self._budget_manager:
            budget_status = self._budget_manager.check_budget(self.estimated_tokens)
            status["budget"] = budget_status.to_dict()

        if self._messages and self._degradation_detector:
            health_report = self._degradation_detector.get_health_score(self._messages)
            status["health"] = health_report.to_dict()

        if self._lifecycle_manager:
            lifecycle_status = self._lifecycle_manager.check(self._cumulative_tokens)
            status["lifecycle"] = lifecycle_status.to_dict()

        return status


# 全局单例（线程安全）
_CONTEXT_MANAGER: Optional[ContextManager] = None
_CONTEXT_MANAGER_LOCK = threading.Lock()


def get_context_manager() -> ContextManager:
    """获取全局上下文管理器实例（线程安全）"""
    global _CONTEXT_MANAGER
    if _CONTEXT_MANAGER is None:
        with _CONTEXT_MANAGER_LOCK:
            if _CONTEXT_MANAGER is None:  # 双重检查锁定
                _CONTEXT_MANAGER = ContextManager()
    return _CONTEXT_MANAGER


def track_context(role: str, content: str, is_important: bool = False) -> None:
    """追踪上下文（便捷函数）

    Args:
        role: 角色 (user/assistant/system)
        content: 消息内容
        is_important: 是否为重要消息
    """
    manager = get_context_manager()
    manager.record_message(role, content, is_important)


def compress_context() -> str:
    """压缩上下文（便捷函数）

    Returns:
        压缩后的上下文摘要
    """
    manager = get_context_manager()
    return manager.compress_now()


def get_recovery_context() -> str:
    """获取恢复上下文（便捷函数）

    Returns:
        上下文恢复摘要
    """
    manager = get_context_manager()
    return manager.get_recovery_summary()


def add_task(task: str, completed: bool = False) -> None:
    """添加任务（便捷函数）"""
    manager = get_context_manager()
    manager.add_task(task, completed)


def complete_task(task: str) -> None:
    """完成任务（便捷函数）"""
    manager = get_context_manager()
    manager.complete_task(task)
