"""Auto Mode 状态机 - 基于 GSD 的状态驱动架构

设计目标：
- 磁盘状态驱动（所有状态可从 .lingflow/STATE.md 读取）
- 可中断恢复（Ctrl+C + 交互后继续）
- 每个状态独立（fresh context）
- 状态转换显式（无隐藏逻辑）

状态循环（参考 GSD 的 The Loop）：
Plan (with integrated research) → Execute (per task) → Complete → Reassess Roadmap → Next Slice
                                                                               ↓ (all slices done)
                                                                             Validate Milestone → Complete Milestone
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class AutoModeState(Enum):
    """Auto Mode 状态定义

    对应 GSD 的状态机：
    - IDLE: 初始状态，等待启动
    - PLAN: 计划下一个 slice
    - RESEARCH: 研究（plan 阶段的子阶段）
    - EXECUTE: 执行单个 task
    - COMPLETE: 完成 slice，写入 summary
    - REASSESS: 重新评估 roadmap
    - VALIDATE: 验证 milestone
    - PAUSED: 用户暂停（逃逸舱）
    - DONE: 全部完成
    - ERROR: 错误状态
    """

    IDLE = auto()
    PLAN = auto()
    RESEARCH = auto()
    EXECUTE = auto()
    COMPLETE = auto()
    REASSESS = auto()
    VALIDATE = auto()
    PAUSED = auto()
    DONE = auto()
    ERROR = auto()

    def __str__(self) -> str:
        return self.name

    def is_terminal(self) -> bool:
        """是否是终端状态（DONE 或 ERROR）"""
        return self in (AutoModeState.DONE, AutoModeState.ERROR)

    def is_paused(self) -> bool:
        """是否是暂停状态"""
        return self == AutoModeState.PAUSED

    def is_active(self) -> bool:
        """是否是活跃状态（非 IDLE/PAUSED/DONE/ERROR）"""
        return self not in (AutoModeState.IDLE, AutoModeState.PAUSED, AutoModeState.DONE, AutoModeState.ERROR)


@dataclass
class MilestoneContext:
    """Milestone 上下文

    对应 GSD 的 M001-ROADMAP.md, M001-CONTEXT.md, M001-RESEARCH.md
    """

    milestone_id: str  # 例如: "M001"
    title: str
    success_criteria: List[str] = field(default_factory=list)
    slices: List[str] = field(default_factory=list)  # slice IDs，例如: ["S01", "S02"]
    current_slice_index: int = 0


@dataclass
class SliceContext:
    """Slice 上下文

    对应 GSD 的 S01-PLAN.md, S01-UAT.md
    """

    slice_id: str  # 例如: "S01"
    milestone_id: str  # 例如: "M001"
    tasks: List[str] = field(default_factory=list)  # task IDs，例如: ["T01", "T02"]
    current_task_index: int = 0
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)


@dataclass
class TaskContext:
    """Task 上下文

    对应 GSD 的 T01-PLAN.md, T01-SUMMARY.md
    """

    task_id: str  # 例如: "T01"
    slice_id: str  # 例如: "S01"
    milestone_id: str  # 例如: "M001"
    plan: str = ""  # T01-PLAN.md 内容
    must_haves: List[str] = field(default_factory=list)  # 验证标准
    summary: str = ""  # T01-SUMMARY.md 内容（完成后写入）
    execution_time: float = 0.0  # 执行时间（秒）
    token_cost: int = 0  # Token 消耗
    retry_count: int = 0  # 重试次数


@dataclass
class StateSnapshot:
    """状态快照

    对应 GSD 的 .gsd/STATE.md
    这是 Auto Mode 的"磁盘状态"，所有决策基于此文件。
    """

    # 当前状态
    state: AutoModeState = AutoModeState.IDLE

    # Milestone 层级
    milestone: Optional[MilestoneContext] = None

    # Slice 层级
    slice: Optional[SliceContext] = None

    # Task 层级
    task: Optional[TaskContext] = None

    # 元数据
    started_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    session_id: str = ""  # 唯一 session ID，用于崩溃恢复

    # 成本跟踪
    total_tokens: int = 0
    total_cost: float = 0.0

    # 逃逸舱
    paused_reason: str = ""  # 暂停原因
    pause_stacktrace: str = ""  # 暂停时的调用栈（用于恢复）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于 JSON 序列化）"""
        return {
            "state": self.state.name,
            "milestone": {
                "id": self.milestone.milestone_id if self.milestone else None,
                "title": self.milestone.title if self.milestone else None,
                "success_criteria": self.milestone.success_criteria if self.milestone else [],
                "slices": self.milestone.slices if self.milestone else [],
                "current_slice_index": self.milestone.current_slice_index if self.milestone else 0,
            } if self.milestone else None,
            "slice": {
                "id": self.slice.slice_id if self.slice else None,
                "milestone_id": self.slice.milestone_id if self.slice else None,
                "tasks": self.slice.tasks if self.slice else [],
                "current_task_index": self.slice.current_task_index if self.slice else 0,
                "completed_tasks": self.slice.completed_tasks if self.slice else [],
                "failed_tasks": self.slice.failed_tasks if self.slice else [],
            } if self.slice else None,
            "task": {
                "id": self.task.task_id if self.task else None,
                "slice_id": self.task.slice_id if self.task else None,
                "milestone_id": self.task.milestone_id if self.task else None,
                "plan": self.task.plan if self.task else "",
                "must_haves": self.task.must_haves if self.task else [],
                "summary": self.task.summary if self.task else "",
                "execution_time": self.task.execution_time,
                "token_cost": self.task.token_cost,
                "retry_count": self.task.retry_count,
            } if self.task else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_updated": self.last_updated.isoformat(),
            "session_id": self.session_id,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "paused_reason": self.paused_reason,
            "pause_stacktrace": self.pause_stacktrace,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateSnapshot":
        """从字典创建（用于 JSON 反序列化）"""
        state = AutoModeState[data.get("state", "IDLE")]

        milestone_data = data.get("milestone")
        milestone = None
        if milestone_data:
            milestone = MilestoneContext(
                milestone_id=milestone_data.get("id", ""),
                title=milestone_data.get("title", ""),
                success_criteria=milestone_data.get("success_criteria", []),
                slices=milestone_data.get("slices", []),
                current_slice_index=milestone_data.get("current_slice_index", 0),
            )

        slice_data = data.get("slice")
        slice_ctx = None
        if slice_data:
            slice_ctx = SliceContext(
                slice_id=slice_data.get("id", ""),
                milestone_id=slice_data.get("milestone_id", ""),
                tasks=slice_data.get("tasks", []),
                current_task_index=slice_data.get("current_task_index", 0),
                completed_tasks=slice_data.get("completed_tasks", []),
                failed_tasks=slice_data.get("failed_tasks", []),
            )

        task_data = data.get("task")
        task_ctx = None
        if task_data:
            task_ctx = TaskContext(
                task_id=task_data.get("id", ""),
                slice_id=task_data.get("slice_id", ""),
                milestone_id=task_data.get("milestone_id", ""),
                plan=task_data.get("plan", ""),
                must_haves=task_data.get("must_haves", []),
                summary=task_data.get("summary", ""),
                execution_time=task_data.get("execution_time", 0.0),
                token_cost=task_data.get("token_cost", 0),
                retry_count=task_data.get("retry_count", 0),
            )

        started_at_str = data.get("started_at")
        started_at = datetime.fromisoformat(started_at_str) if started_at_str else None

        last_updated_str = data.get("last_updated")
        last_updated = datetime.fromisoformat(last_updated_str) if last_updated_str else datetime.now()

        return cls(
            state=state,
            milestone=milestone,
            slice=slice_ctx,
            task=task_ctx,
            started_at=started_at,
            last_updated=last_updated,
            session_id=data.get("session_id", ""),
            total_tokens=data.get("total_tokens", 0),
            total_cost=data.get("total_cost", 0.0),
            paused_reason=data.get("paused_reason", ""),
            pause_stacktrace=data.get("pause_stacktrace", ""),
        )


class AutoModeStateMachine:
    """Auto Mode 状态机

    核心设计原则（参考 GSD）：
    1. 状态驱动：所有决策基于磁盘上的 STATE.md
    2. 可中断：随时暂停，保存完整上下文
    3. 可恢复：从保存的快照继续
    4. 显式转换：状态转换逻辑清晰可见
    5. fresh context：每个 task 独立会话
    """

    def __init__(self, workdir: str):
        """初始化状态机

        Args:
            workdir: 工作目录（.lingflow/ 所在位置）
        """
        self.workdir = Path(workdir)
        self.lingflow_dir = self.workdir / ".lingflow"
        self.lingflow_dir.mkdir(exist_ok=True)

        # 状态快照（内存中，每次操作后持久化）
        self.state: StateSnapshot = StateSnapshot()

        # 锁文件（防止并发运行）
        self.lock_file = self.lingflow_dir / "auto.lock"
        self.lock_fd = None

        # session ID（用于唯一标识）
        self.session_id = self._generate_session_id()

        # 回调函数
        self._on_state_change = None

        logger.info(f"Auto Mode 状态机初始化: workdir={workdir}, session_id={self.session_id}")

    def _generate_session_id(self) -> str:
        """生成唯一 session ID"""
        import uuid
        return f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"

    def load_state(self) -> bool:
        """从磁盘加载状态

        如果存在 STATE.md，反序列化并恢复快照。

        Returns:
            是否成功加载
        """
        state_file = self.lingflow_dir / "STATE.md"
        if not state_file.exists():
            logger.info("STATE.md 不存在，使用初始状态")
            return False

        try:
            # STATE.md 是 JSON 块
            with open(state_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 提取 JSON 部分
                if "```json" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_str = content[json_start:json_end]
                else:
                    json_str = content

                data = json.loads(json_str)
                self.state = StateSnapshot.from_dict(data)

            logger.info(f"从 STATE.md 恢复状态: state={self.state.state}, session_id={self.state.session_id}")
            return True

        except Exception as e:
            logger.error(f"加载 STATE.md 失败: {e}")
            return False

    def save_state(self) -> None:
        """保存状态到磁盘（STATE.md）

        对应 GSD 的磁盘状态持久化。
        """
        self.state.last_updated = datetime.now()

        state_file = self.lingflow_dir / "STATE.md"

        # 生成 STATE.md 内容（Markdown + JSON 块）
        json_data = self.state.to_dict()
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)

        content = f"""# Auto Mode State

Last updated: {self.state.last_updated.isoformat()}
Session ID: {self.state.session_id}
Current State: **{self.state.state}**

```json
{json_str}
```
"""

        with open(state_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"状态已保存: {self.state.state}")

    def acquire_lock(self) -> bool:
        """获取锁文件

        防止多个 Auto Mode 实例同时运行。

        Returns:
            是否成功获取锁
        """
        try:
            self.lock_fd = open(self.lock_file, "x")
            self.lock_fd.write(str(self.session_id))
            self.lock_fd.flush()
            logger.info(f"锁文件获取成功: {self.lock_file}")
            return True
        except (IOError, OSError) as e:
            logger.warning(f"锁文件获取失败: {e}")
            return False

    def release_lock(self) -> None:
        """释放锁文件"""
        if self.lock_fd is not None:
            try:
                self.lock_fd.close()
                self.lock_file.unlink(missing_ok=True)
                logger.info("锁文件已释放")
            except Exception as e:
                logger.error(f"释放锁文件失败: {e}")
            finally:
                self.lock_fd = None

    def transition_to(self, new_state: AutoModeState, reason: str = "") -> None:
        """转换状态

        Args:
            new_state: 新状态
            reason: 转换原因（用于日志）
        """
        old_state = self.state.state
        if old_state == new_state:
            logger.debug(f"状态无变化: {new_state}")
            return

        logger.info(f"状态转换: {old_state} → {new_state} ({reason})")
        self.state.state = new_state
        self.save_state()

        # 触发回调
        if self._on_state_change:
            self._on_state_change(old_state, new_state, reason)

    def start(self) -> None:
        """启动 Auto Mode

        1. 获取锁
        2. 加载或初始化状态
        3. 设置 started_at
        4. 转换到 IDLE → PLAN
        """
        if not self.acquire_lock():
            raise RuntimeError("Auto Mode 已在运行（锁文件存在）")

        if not self.load_state():
            # 首次运行，初始化状态
            self.state = StateSnapshot(session_id=self.session_id)
            logger.info("初始化新 Auto Mode session")

        self.state.started_at = datetime.now()
        self.save_state()

        logger.info("Auto Mode 已启动")
        self.transition_to(AutoModeState.IDLE, "Auto Mode 启动")

    def pause(self, reason: str = "User paused") -> None:
        """暂停 Auto Mode（逃逸舱）

        Args:
            reason: 暂停原因
        """
        import traceback

        old_state = self.state.state

        # 保存调用栈（用于 forensics）
        self.state.paused_reason = reason
        self.state.pause_stacktrace = "".join(traceback.format_stack())

        # 转换到 PAUSED
        self.transition_to(AutoModeState.PAUSED, reason)

        logger.info(f"Auto Mode 已暂停: {reason}")
        logger.info(f"原状态: {old_state}，使用 /auto continue 恢复")

    def resume(self) -> None:
        """恢复 Auto Mode

        从 PAUSED 状态转换回之前的状态（或继续到下一个逻辑状态）
        """
        if self.state.state != AutoModeState.PAUSED:
            logger.warning(f"当前状态不是 PAUSED: {self.state.state}")
            return

        # 从暂停原因推断应该回到的状态
        # 简单实现：根据上下文决定
        if self.state.task and self.state.task.retry_count > 0:
            # 重试中，回到 EXECUTE
            next_state = AutoModeState.EXECUTE
            reason = "重试任务"
        elif self.state.slice:
            # slice 进行中，回到 EXECUTE
            next_state = AutoModeState.EXECUTE
            reason = "继续 slice 执行"
        elif self.state.milestone:
            # milestone 进行中，回到 PLAN
            next_state = AutoModeState.PLAN
            reason = "继续 milestone 计划"
        else:
            # 没有上下文，回到 IDLE
            next_state = AutoModeState.IDLE
            reason = "从 IDLE 开始"

        # 清除暂停信息
        self.state.paused_reason = ""
        self.state.pause_stacktrace = ""

        self.transition_to(next_state, reason)
        logger.info(f"Auto Mode 已恢复: {next_state}")

    def stop(self) -> None:
        """停止 Auto Mode

        释放锁，保存最终状态
        """
        self.release_lock()
        logger.info("Auto Mode 已停止")

    def get_current_context_summary(self) -> str:
        """获取当前上下文摘要（用于显示）

        Returns:
            当前状态的 Markdown 摘要
        """
        lines = [
            "# Auto Mode 状态摘要",
            "",
            f"当前状态: {self.state.state}",
            f"Session ID: {self.state.session_id}",
            f"开始时间: {self.state.started_at.isoformat() if self.state.started_at else 'N/A'}",
            f"最后更新: {self.state.last_updated.isoformat()}",
            "",
        ]

        if self.state.milestone:
            m = self.state.milestone
            lines.extend([
                "## Milestone",
                f"- **ID**: `{m.milestone_id}`",
                f"- **标题**: {m.title}",
                f"- **当前 Slice**: `{m.slices[m.current_slice_index] if m.current_slice_index < len(m.slices) else 'N/A'}`",
                f"- **进度**: {m.current_slice_index}/{len(m.slices)} slices",
                "",
            ])

        if self.state.slice:
            s = self.state.slice
            lines.extend([
                "## Slice",
                f"- **ID**: `{s.slice_id}`",
                f"- **当前 Task**: `{s.tasks[s.current_task_index] if s.current_task_index < len(s.tasks) else 'N/A'}`",
                f"- **进度**: {s.current_task_index}/{len(s.tasks)} tasks",
                f"- **已完成**: {', '.join(s.completed_tasks)}",
                f"- **失败**: {', '.join(s.failed_tasks)}",
                "",
            ])

        if self.state.task:
            t = self.state.task
            lines.extend([
                "## Task",
                f"- **ID**: `{t.task_id}`",
                f"- **重试次数**: {t.retry_count}",
                f"- **执行时间**: {t.execution_time}s",
                f"- **Token 成本**: {t.token_cost}",
                "",
            ])

        lines.extend([
            "## 成本统计",
            f"- **总 Tokens**: `{self.state.total_tokens}`",
            f"- **总成本**: `${self.state.total_cost:.2f}`",
            "",
        ])

        if self.state.paused_reason:
            lines.extend([
                "## 暂停信息",
                f"- **原因**: {self.state.paused_reason}",
                "",
            ])

        return "\n".join(lines)
