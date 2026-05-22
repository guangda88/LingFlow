"""会话生命周期管理器

基于灵依提出的上下文生命周期管理原则，实现会话级别的 token 监控、预警和过渡机制。

核心规则（议事厅 #灵通工作流）：
- 警戒线：20万 token 时提示用户
- 阈值：30万 token 时主动建议新会话
- 动作：保存会话摘要，启动新会话，无缝衔接

设计原则：
- 与 budget.py（模型退化预算）并行，而非替代
- budget.py 关注「模型性能退化」（相对阈值）
- 本模块关注「会话生命周期」（绝对 token 阈值）
- 两者独立触发，不互相干扰
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class LifecyclePhase(Enum):
    """会话生命周期阶段"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EXPIRED = "expired"


@dataclass
class LifecycleStatus:
    """会话生命周期状态"""

    phase: LifecyclePhase
    current_tokens: int
    warning_threshold: int
    critical_threshold: int
    usage_percentage: float
    recommended_action: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "current_tokens": self.current_tokens,
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "usage_percentage": f"{self.usage_percentage:.1%}",
            "recommended_action": self.recommended_action,
            "message": self.message,
        }


@dataclass
class SessionSummary:
    """会话摘要（用于跨会话交接）"""

    session_id: str
    created_at: str
    ended_at: str
    total_tokens: int
    total_messages: int
    tasks_completed: List[str] = field(default_factory=list)
    tasks_pending: List[str] = field(default_factory=list)
    key_decisions: List[str] = field(default_factory=list)
    important_files: Dict[str, str] = field(default_factory=dict)
    next_steps: List[str] = field(default_factory=list)
    context_summary: str = ""
    handover_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_markdown(self) -> str:
        parts = [
            "# 会话交接摘要",
            "",
            f"- **会话 ID**: {self.session_id}",
            f"- **时间**: {self.created_at} → {self.ended_at}",
            f"- **Token 使用**: {self.total_tokens:,}",
            f"- **消息数**: {self.total_messages}",
            f"- **传递原因**: {self.handover_reason}",
            "",
        ]
        if self.tasks_completed:
            parts.append(f"## 已完成任务 ({len(self.tasks_completed)})")
            parts.append("")
            for t in self.tasks_completed:
                parts.append(f"- ✅ {t}")
            parts.append("")
        if self.tasks_pending:
            parts.append(f"## 待完成任务 ({len(self.tasks_pending)})")
            parts.append("")
            for t in self.tasks_pending:
                parts.append(f"- ◻ {t}")
            parts.append("")
        if self.key_decisions:
            parts.append("## 关键决策")
            parts.append("")
            for d in self.key_decisions:
                parts.append(f"- {d}")
            parts.append("")
        if self.important_files:
            parts.append("## 重要文件")
            parts.append("")
            for p, desc in self.important_files.items():
                parts.append(f"- `{p}`: {desc}")
            parts.append("")
        if self.next_steps:
            parts.append("## 下一步")
            parts.append("")
            for i, s in enumerate(self.next_steps, 1):
                parts.append(f"{i}. {s}")
            parts.append("")
        return "\n".join(parts)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionSummary":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class SessionLifecycleManager:
    """会话生命周期管理器

    管理 AI 会话的完整生命周期，在 token 使用量达到警戒线时
    提前预警，在达到阈值时建议新会话，并负责会话交接。

    与 ContextBudgetManager（budget.py）的关系：
    - BudgetManager 关注模型性能退化（相对阈值，基于退化研究）
    - LifecycleManager 关注会话生命周期（绝对阈值，基于使用经验）
    - 两者独立运行，可同时触发
    """

    DEFAULT_WARNING_THRESHOLD = 200_000
    DEFAULT_CRITICAL_THRESHOLD = 300_000

    def __init__(
        self,
        warning_threshold: int = DEFAULT_WARNING_THRESHOLD,
        critical_threshold: int = DEFAULT_CRITICAL_THRESHOLD,
        storage_dir: Optional[Path] = None,
    ):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.storage_dir = storage_dir

        self._callbacks: Dict[str, List[Callable]] = {
            LifecyclePhase.WARNING: [],
            LifecyclePhase.CRITICAL: [],
            LifecyclePhase.EXPIRED: [],
        }
        self._warnings_issued = 0
        self._last_phase = LifecyclePhase.HEALTHY

    def check(self, current_tokens: int) -> LifecycleStatus:
        """检查当前会话生命周期状态

        Args:
            current_tokens: 当前 token 使用量

        Returns:
            生命周期状态
        """
        pct = current_tokens / self.critical_threshold if self.critical_threshold > 0 else 0.0

        if current_tokens >= self.critical_threshold:
            phase = LifecyclePhase.EXPIRED
            action = "new_session"
            message = (
                f"会话已达 {current_tokens:,} tokens（阈值 {self.critical_threshold:,}），"
                f"建议立即开始新会话。当前会话摘要将自动保存。"
            )
        elif current_tokens >= self.warning_threshold:
            phase = LifecyclePhase.WARNING
            action = "prepare_handover"
            message = (
                f"会话已达 {current_tokens:,} tokens（警戒线 {self.warning_threshold:,}），"
                f"建议准备会话传递。阈值 {self.critical_threshold:,} tokens。"
            )
        else:
            phase = LifecyclePhase.HEALTHY
            action = "none"
            pct_of_warning = current_tokens / self.warning_threshold * 100 if self.warning_threshold > 0 else 0
            message = f"会话健康（{pct_of_warning:.0f}% 警戒线）"

        status = LifecycleStatus(
            phase=phase,
            current_tokens=current_tokens,
            warning_threshold=self.warning_threshold,
            critical_threshold=self.critical_threshold,
            usage_percentage=pct,
            recommended_action=action,
            message=message,
        )

        self._trigger_if_phase_changed(phase, status)

        return status

    def on_phase_change(self, phase: LifecyclePhase, callback: Callable[["LifecycleStatus"], None]) -> None:
        """注册阶段变更回调

        Args:
            phase: 监听的生命周期阶段
            callback: 回调函数，接收 LifecycleStatus
        """
        if phase in self._callbacks:
            self._callbacks[phase].append(callback)

    def create_session_summary(
        self,
        session_id: str,
        total_tokens: int,
        total_messages: int,
        tasks_completed: Optional[List[str]] = None,
        tasks_pending: Optional[List[str]] = None,
        key_decisions: Optional[List[str]] = None,
        important_files: Optional[Dict[str, str]] = None,
        next_steps: Optional[List[str]] = None,
        context_summary: str = "",
        handover_reason: str = "lifecycle_threshold",
    ) -> SessionSummary:
        """创建会话摘要

        Args:
            session_id: 会话 ID
            total_tokens: 总 token 使用量
            total_messages: 总消息数
            tasks_completed: 已完成任务
            tasks_pending: 待完成任务
            key_decisions: 关键决策
            important_files: 重要文件
            next_steps: 下一步计划
            context_summary: 上下文摘要
            handover_reason: 传递原因

        Returns:
            会话摘要
        """
        now = datetime.now().isoformat()
        return SessionSummary(
            session_id=session_id,
            created_at="",
            ended_at=now,
            total_tokens=total_tokens,
            total_messages=total_messages,
            tasks_completed=tasks_completed or [],
            tasks_pending=tasks_pending or [],
            key_decisions=key_decisions or [],
            important_files=important_files or {},
            next_steps=next_steps or [],
            context_summary=context_summary,
            handover_reason=handover_reason,
        )

    def save_session_summary(self, summary: SessionSummary) -> Path:
        """保存会话摘要到磁盘

        Args:
            summary: 会话摘要

        Returns:
            保存路径
        """
        if self.storage_dir is None:
            raise ValueError("storage_dir not configured")

        self.storage_dir.mkdir(parents=True, exist_ok=True)

        json_path = self.storage_dir / f"lifecycle_{summary.session_id}.json"
        json_path.write_text(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

        md_path = self.storage_dir / "SESSION_HANDOVER.md"
        md_path.write_text(summary.to_markdown(), encoding="utf-8")

        logger.info("会话摘要已保存: %s", json_path)
        return json_path

    def load_last_session_summary(self) -> Optional[SessionSummary]:
        """加载上一次会话摘要

        Returns:
            上一次会话摘要，如果不存在返回 None
        """
        if self.storage_dir is None:
            return None

        md_path = self.storage_dir / "SESSION_HANDOVER.md"
        if not md_path.exists():
            return None

        summaries = sorted(self.storage_dir.glob("lifecycle_*.json"), reverse=True)
        if not summaries:
            return None

        try:
            data = json.loads(summaries[0].read_text(encoding="utf-8"))
            return SessionSummary.from_dict(data)
        except Exception as e:
            logger.warning("加载会话摘要失败: %s", e)
            return None

    def get_handover_instructions(self, summary: SessionSummary) -> str:
        """生成新会话的传递指令

        Args:
            summary: 上一会话的摘要

        Returns:
            传递指令文本
        """
        parts = [
            "## 会话传递指令",
            "",
            f"上一会话（{summary.session_id}）因 token 限制（{summary.total_tokens:,}）而结束。",
            "",
        ]
        if summary.tasks_pending:
            parts.append("### 待完成任务")
            for t in summary.tasks_pending:
                parts.append(f"- {t}")
            parts.append("")
        if summary.next_steps:
            parts.append("### 建议下一步")
            for i, s in enumerate(summary.next_steps, 1):
                parts.append(f"{i}. {s}")
            parts.append("")
        if summary.key_decisions:
            parts.append("### 已做出的关键决策（请遵守）")
            for d in summary.key_decisions:
                parts.append(f"- {d}")
            parts.append("")
        return "\n".join(parts)

    def _trigger_if_phase_changed(self, new_phase: LifecyclePhase, status: LifecycleStatus) -> None:
        """在阶段变更时触发回调"""
        if new_phase == self._last_phase:
            return

        if new_phase == LifecyclePhase.WARNING:
            self._warnings_issued += 1

        callbacks = self._callbacks.get(new_phase, [])
        for cb in callbacks:
            try:
                cb(status)
            except Exception as e:
                logger.error("生命周期回调失败: %s", e)

        self._last_phase = new_phase

    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "current_phase": self._last_phase.value,
            "warnings_issued": self._warnings_issued,
        }
