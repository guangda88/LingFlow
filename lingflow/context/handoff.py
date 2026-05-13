"""会话交接文档

当上下文接近 LLM 退化阈值时，生成结构化的交接文档，
使新会话能够无缝继承前一会话的关键信息。

设计依据:
- 保持交接文档在 40% 安全线内（< 72K tokens for 180K model）
- 优先保留不可重建的信息（决策、状态、约束）
- 可重建信息（代码、文件内容）仅保留引用
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class HandoffDocument:
    """会话交接文档

    当上下文接近退化阈值时，生成此文档以支持会话无缝切换。
    """

    version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: str = ""
    reason: str = ""

    # 工作状态
    current_task: str = ""
    tasks_completed: List[str] = field(default_factory=list)
    tasks_pending: List[str] = field(default_factory=list)
    tasks_in_progress: List[str] = field(default_factory=list)

    # 关键决策（不可丢失）
    key_decisions: List[Dict[str, str]] = field(default_factory=list)

    # 重要文件引用（不包含内容，仅路径和描述）
    important_files: Dict[str, str] = field(default_factory=dict)

    # 当前工作上下文
    active_files: List[str] = field(default_factory=list)
    active_branch: str = ""
    last_commit: str = ""

    # 约束和注意事项
    constraints: List[str] = field(default_factory=list)
    known_issues: List[str] = field(default_factory=list)
    failed_approaches: List[str] = field(default_factory=list)

    # 下一步
    next_steps: List[str] = field(default_factory=list)
    context_for_next_step: str = ""

    # 健康状态
    token_usage_at_handoff: int = 0
    degradation_detected: bool = False
    degradation_types: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the handoff document to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the handoff document.
        """
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert the handoff document to JSON string.

        Args:
            indent: JSON indentation level.

        Returns:
            str: JSON string representation of the handoff document.
        """
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_markdown(self) -> str:
        """生成交接文档的 Markdown 表示"""
        parts = [
            "# lingflow 会话交接文档",
            "",
            f"**版本**: {self.version}",
            f"**时间**: {self.timestamp}",
            f"**会话 ID**: {self.session_id}",
            f"**交接原因**: {self.reason}",
            "",
        ]

        if self.current_task:
            parts.extend(
                [
                    "## 当前任务",
                    "",
                    self.current_task,
                    "",
                ]
            )

        if self.tasks_in_progress:
            parts.extend(["## 进行中的任务", ""])
            for t in self.tasks_in_progress:
                parts.append(f"- 🔄 {t}")
            parts.append("")

        if self.tasks_completed:
            parts.extend([f"## 已完成任务 ({len(self.tasks_completed)})", ""])
            for t in self.tasks_completed:
                parts.append(f"- ✅ {t}")
            parts.append("")

        if self.tasks_pending:
            parts.extend([f"## 待完成任务 ({len(self.tasks_pending)})", ""])
            for t in self.tasks_pending:
                parts.append(f"- ◻ {t}")
            parts.append("")

        if self.key_decisions:
            parts.extend(["## 关键决策", ""])
            for d in self.key_decisions:
                decision_text = d.get("decision", "")
                rationale = d.get("rationale", "")
                parts.append(f"- **{decision_text}**")
                if rationale:
                    parts.append(f"  原因: {rationale}")
            parts.append("")

        if self.important_files:
            parts.extend(["## 重要文件", ""])
            for path, desc in self.important_files.items():
                parts.append(f"- `{path}`: {desc}")
            parts.append("")

        if self.constraints:
            parts.extend(["## 约束条件", ""])
            for c in self.constraints:
                parts.append(f"- ⚠️ {c}")
            parts.append("")

        if self.known_issues:
            parts.extend(["## 已知问题", ""])
            for issue in self.known_issues:
                parts.append(f"- 🐛 {issue}")
            parts.append("")

        if self.failed_approaches:
            parts.extend(["## 已失败的方案（避免重复）", ""])
            for approach in self.failed_approaches:
                parts.append(f"- ❌ {approach}")
            parts.append("")

        if self.next_steps:
            parts.extend(["## 下一步", ""])
            for i, step in enumerate(self.next_steps, 1):
                parts.append(f"{i}. {step}")
            parts.append("")

        if self.context_for_next_step:
            parts.extend(["## 下一步所需的上下文", ""])
            parts.append(self.context_for_next_step)
            parts.append("")

        if self.degradation_detected:
            parts.extend(
                [
                    "## 退化检测",
                    "",
                    f"- Token 使用量: {self.token_usage_at_handoff}",
                    f"- 检测到的退化类型: {', '.join(self.degradation_types) or '无'}",
                    "",
                ]
            )

        return "\n".join(parts)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HandoffDocument":
        """Create a HandoffDocument from a dictionary.

        Args:
            data: Dictionary containing handoff document data.

        Returns:
            HandoffDocument: New handoff document instance.
        """
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    @classmethod
    def from_json(cls, json_str: str) -> "HandoffDocument":
        """Create a HandoffDocument from a JSON string.

        Args:
            json_str: JSON string containing handoff document data.

        Returns:
            HandoffDocument: New handoff document instance.

        Raises:
            json.JSONDecodeError: If the JSON string is invalid.
        """
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_context_snapshot(cls, snapshot: Any, **kwargs: Any) -> "HandoffDocument":
        """从 ContextSnapshot 创建交接文档

        Args:
            snapshot: ContextSnapshot 实例
            **kwargs: 额外字段覆盖

        Returns:
            HandoffDocument 实例
        """
        doc = cls(
            session_id=getattr(snapshot, "session_id", ""),
            tasks_completed=getattr(snapshot, "tasks_completed", []),
            tasks_pending=getattr(snapshot, "tasks_pending", []),
            important_files=getattr(snapshot, "important_files", {}),
            next_steps=getattr(snapshot, "next_steps", []),
            **kwargs,
        )

        decisions = getattr(snapshot, "key_decisions", [])
        doc.key_decisions = [{"decision": d, "rationale": ""} for d in decisions]

        return doc
