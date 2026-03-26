"""LingFlow 对话上下文管理器

自动跟踪对话进度，在 token 限制时压缩上下文到持久化存储。
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import hashlib

from .auto_resume import save_resume_markdown

logger = logging.getLogger(__name__)


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
            storage_dir: 上下文存储目录
        """
        self.storage_dir = Path(storage_dir or "/home/ai/.claude/projects/-home-ai-LingFlow/context")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 当前会话状态
        self.session_id = self._generate_session_id()
        self.message_count = 0
        self.estimated_tokens = 0

        # 上下文数据
        self.snapshot = ContextSnapshot(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
        )

        # 关键词跟踪（用于识别重要消息）
        self._important_keywords: Set[str] = {
            "fix", "bug", "implement", "create", "refactor",
            "critical", "important", "must", "should",
            "todo", "task", "完成", "修复", "实现"
        }

        # 加载之前的上下文
        self._load_last_context()

    def _generate_session_id(self) -> str:
        """生成会话 ID"""
        return hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:12]

    def _load_last_context(self) -> Optional[ContextSnapshot]:
        """加载上次的上下文"""
        last_file = self.storage_dir / "last_context.json"
        if last_file.exists():
            try:
                with open(last_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.last_context = ContextSnapshot.from_dict(data)
                    logger.info(f"已加载上次上下文: {self.last_context.session_id}")
                    return self.last_context
            except Exception as e:
                logger.warning(f"加载上次上下文失败: {e}")
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
        # 粗略估计 token 数量（约 4 字符 = 1 token）
        self.estimated_tokens += len(content) // 4

        # 自动检测重要内容
        if not is_important:
            is_important = self._is_important_message(content)

        if is_important:
            self._extract_important_info(content)

        # 检查是否需要压缩
        self._check_and_warn()

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
        ratio = self.estimated_tokens / self.ESTIMATED_TOKEN_LIMIT

        if ratio >= self.COMPRESS_THRESHOLD:
            logger.warning(f"Token 使用率 {ratio:.1%}，建议压缩上下文")
            self.compress_now()
        elif ratio >= self.WARNING_THRESHOLD:
            logger.warning(f"Token 使用率 {ratio:.1%}，接近限制")

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
            "tasks": [
                {"name": t, "done": True}
                for t in self.snapshot.tasks_completed
            ] + [
                {"name": t, "done": False}
                for t in self.snapshot.tasks_pending
            ],
            "next_steps": self.snapshot.next_steps,
            "session_id": self.session_id,
        }
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        # 保存 Markdown 格式（用于自动恢复显示）
        tasks = [
            {"name": t, "done": True}
            for t in self.snapshot.tasks_completed
        ] + [
            {"name": t, "done": False}
            for t in self.snapshot.tasks_pending
        ]
        save_resume_markdown(
            tasks=tasks,
            next_steps=self.snapshot.next_steps,
            summary=self._get_brief_summary()
        )

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

    def compress_now(self) -> str:
        """立即压缩当前上下文

        Returns:
            压缩后的上下文摘要，可用于新会话
        """
        # 生成摘要
        summary_parts = [
            f"# LingFlow 对话上下文摘要",
            f"",
            f"**会话 ID**: {self.session_id}",
            f"**时间**: {self.snapshot.timestamp}",
            f"**消息数**: {self.message_count}",
            f"**估计 Token**: {self.estimated_tokens}",
            f"",
        ]

        if self.snapshot.tasks_completed:
            summary_parts.extend([
                f"## 已完成任务 ({len(self.snapshot.tasks_completed)})",
                f""
            ])
            for task in self.snapshot.tasks_completed:
                summary_parts.append(f"- ✅ {task}")
            summary_parts.append("")

        if self.snapshot.tasks_pending:
            summary_parts.extend([
                f"## 待完成任务 ({len(self.snapshot.tasks_pending)})",
                f""
            ])
            for task in self.snapshot.tasks_pending:
                summary_parts.append(f"- ◻ {task}")
            summary_parts.append("")

        if self.snapshot.key_decisions:
            summary_parts.extend([
                f"## 关键决策",
                f""
            ])
            for decision in self.snapshot.key_decisions:
                summary_parts.append(f"- {decision}")
            summary_parts.append("")

        if self.snapshot.important_files:
            summary_parts.extend([
                f"## 重要文件",
                f""
            ])
            for path, desc in self.snapshot.important_files.items():
                summary_parts.append(f"- `{path}`: {desc}")
            summary_parts.append("")

        if self.snapshot.next_steps:
            summary_parts.extend([
                f"## 下一步计划",
                f""
            ])
            for i, step in enumerate(self.snapshot.next_steps, 1):
                summary_parts.append(f"{i}. {step}")
            summary_parts.append("")

        summary = "\n".join(summary_parts)
        self.snapshot.context_summary = summary
        self._save_snapshot()

        # 同时保存到专门的恢复文件
        recovery_file = self.storage_dir / "RECOVERY_CONTEXT.md"
        recovery_file.write_text(summary, encoding="utf-8")

        logger.info(f"上下文已压缩，保存到: {recovery_file}")
        return summary

    def get_recovery_summary(self) -> str:
        """获取恢复摘要（用于新会话）"""
        recovery_file = self.storage_dir / "RECOVERY_CONTEXT.md"
        if recovery_file.exists():
            return recovery_file.read_text(encoding="utf-8")

        # 如果没有恢复文件，生成当前摘要
        return self.compress_now()

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "session_id": self.session_id,
            "message_count": self.message_count,
            "estimated_tokens": self.estimated_tokens,
            "token_usage_ratio": self.estimated_tokens / self.ESTIMATED_TOKEN_LIMIT,
            "tasks_completed": len(self.snapshot.tasks_completed),
            "tasks_pending": len(self.snapshot.tasks_pending),
        }


# 全局单例
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """获取全局上下文管理器实例"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


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
