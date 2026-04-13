"""Auto Mode 上下文预加载 - Pre-inlined Context 系统

参考 GSD 的 Fresh Context 设计：
- 每次状态转换时，预加载相关上下文文件
- 任务执行前注入已完成任务的摘要
- Slice/Milestone 级别的上下文累积
- 上下文大小控制（避免 token 溢出）

设计原则：
- 每个 task 执行时，知道自己在一个 slice/milestone 中的位置
- 已完成的 task 摘要作为上下文传递给下一个 task
- Roadmap/Plan 作为高层上下文始终可用
- 上下文大小有限制，超过时自动摘要
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, field

from lingflow.workflow.auto_mode import (
    AutoModeStateMachine,
    StateSnapshot,
)

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONTEXT_CHARS = 15000
SUMMARY_THRESHOLD_CHARS = 10000


@dataclass
class PreInlinedContext:
    """预加载的上下文包

    在每个 task 执行前构建，包含所有相关上下文。
    """

    # 高层上下文
    roadmap_summary: str = ""
    slice_plan: str = ""
    task_plan: str = ""

    # 累积上下文
    completed_tasks_summaries: List[Dict[str, str]] = field(default_factory=list)
    failed_tasks_info: List[Dict[str, str]] = field(default_factory=list)

    # 状态信息
    milestone_id: str = ""
    slice_id: str = ""
    task_id: str = ""
    current_task_index: int = 0
    total_tasks: int = 0
    completed_count: int = 0

    # 元数据
    total_chars: int = 0
    truncated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于注入 skill params）"""
        return {
            "milestone_id": self.milestone_id,
            "slice_id": self.slice_id,
            "task_id": self.task_id,
            "progress": f"{self.completed_count}/{self.total_tasks}",
            "roadmap_summary": self.roadmap_summary,
            "slice_plan": self.slice_plan,
            "task_plan": self.task_plan,
            "previous_results": self.completed_tasks_summaries,
            "failed_tasks": self.failed_tasks_info,
            "context_size_chars": self.total_chars,
            "context_truncated": self.truncated,
        }

    def to_prompt_prefix(self) -> str:
        """生成注入到 skill 执行前的上下文前缀"""
        lines = []

        if self.milestone_id:
            lines.append(f"[Milestone: {self.milestone_id}]")

        if self.slice_id:
            progress = f"({self.completed_count}/{self.total_tasks} tasks done)"
            lines.append(f"[Slice: {self.slice_id} {progress}]")

        if self.task_id:
            lines.append(f"[Current Task: {self.task_id}]")

        if self.roadmap_summary:
            roadmap_preview = self.roadmap_summary[:2000]
            if len(self.roadmap_summary) > 2000:
                roadmap_preview += "\n... (roadmap truncated)"
            lines.append(f"\n--- Roadmap ---\n{roadmap_preview}")

        if self.completed_tasks_summaries:
            lines.append("\n--- Previously Completed ---")
            for summary in self.completed_tasks_summaries[-5:]:
                tid = summary.get("task_id", "?")
                result = summary.get("summary", "")[:500]
                lines.append(f"  {tid}: {result}")

        if self.failed_tasks_info:
            lines.append("\n--- Failed Tasks ---")
            for info in self.failed_tasks_info[-3:]:
                tid = info.get("task_id", "?")
                error = info.get("error", "")[:300]
                lines.append(f"  {tid}: {error}")

        return "\n".join(lines)


class ContextPreloader:
    """上下文预加载器

    在每个 task 执行前，收集所有相关上下文：
    1. Roadmap 摘要
    2. Slice plan
    3. 已完成 task 的摘要
    4. 失败 task 的信息
    5. 当前 task plan

    所有上下文打包为 PreInlinedContext，注入到 skill params 中。
    """

    def __init__(self, state_machine: AutoModeStateMachine, max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS):
        """初始化上下文预加载器

        Args:
            state_machine: 状态机实例
            max_context_chars: 最大上下文字符数
        """
        self.state_machine = state_machine
        self.workdir = Path(state_machine.workdir)
        self.lingflow_dir = self.workdir / ".lingflow"
        self.max_context_chars = max_context_chars

    def preload_for_task(self, task_id: str) -> PreInlinedContext:
        """为 task 执行预加载上下文

        Args:
            task_id: Task ID

        Returns:
            预加载的上下文包
        """
        state = self.state_machine.state
        ctx = PreInlinedContext()

        # 1. 基本状态信息
        if state.milestone:
            ctx.milestone_id = state.milestone.milestone_id
        if state.slice:
            ctx.slice_id = state.slice.slice_id
            ctx.current_task_index = state.slice.current_task_index
            ctx.total_tasks = len(state.slice.tasks)
            ctx.completed_count = len(state.slice.completed_tasks)
        ctx.task_id = task_id

        # 2. Roadmap 摘要
        ctx.roadmap_summary = self._load_roadmap_summary(state)

        # 3. Slice plan
        ctx.slice_plan = self._load_slice_plan(state)

        # 4. 已完成 task 的摘要
        ctx.completed_tasks_summaries = self._load_completed_summaries(state)

        # 5. 失败 task 信息
        ctx.failed_tasks_info = self._load_failed_info(state)

        # 6. 当前 task plan
        ctx.task_plan = self._load_task_plan(task_id)

        # 7. 计算总大小并检查截断
        ctx.total_chars = self._calculate_total_chars(ctx)
        if ctx.total_chars > self.max_context_chars:
            ctx = self._truncate_context(ctx)

        logger.debug(f"Pre-inlined context for {task_id}: {ctx.total_chars} chars")
        return ctx

    def inject_into_params(self, params: Dict[str, Any], task_id: str) -> Dict[str, Any]:
        """将预加载的上下文注入到 skill 参数中

        Args:
            params: 原始 skill 参数
            task_id: Task ID

        Returns:
            注入上下文后的参数
        """
        ctx = self.preload_for_task(task_id)

        # 合并到 params（不覆盖已有值）
        enriched = dict(params)
        enriched.setdefault("context", ctx.to_prompt_prefix())
        enriched.setdefault("auto_mode", ctx.to_dict())
        enriched.setdefault("task_id", task_id)

        return enriched

    def _load_roadmap_summary(self, state: StateSnapshot) -> str:
        """加载 roadmap 摘要"""
        if not state.milestone:
            return ""

        roadmap_file = self.lingflow_dir / f"{state.milestone.milestone_id}-ROADMAP.md"
        if not roadmap_file.exists():
            return ""

        content = roadmap_file.read_text(encoding="utf-8")
        return self._extract_summary_section(content) or content[:3000]

    def _load_slice_plan(self, state: StateSnapshot) -> str:
        """加载 slice plan"""
        if not state.slice:
            return ""

        plan_file = self.lingflow_dir / f"{state.slice.slice_id}-PLAN.md"
        if not plan_file.exists():
            return ""

        return plan_file.read_text(encoding="utf-8")[:5000]

    def _load_completed_summaries(self, state: StateSnapshot) -> List[Dict[str, str]]:
        """加载已完成 task 的摘要"""
        if not state.slice:
            return []

        summaries = []
        for task_id in state.slice.completed_tasks:
            summary_file = self.lingflow_dir / f"{task_id}-SUMMARY.md"
            if summary_file.exists():
                content = summary_file.read_text(encoding="utf-8")
                summaries.append({
                    "task_id": task_id,
                    "summary": content[:1000],
                })
            else:
                summaries.append({
                    "task_id": task_id,
                    "summary": "(completed, no summary file)",
                })

        return summaries

    def _load_failed_info(self, state: StateSnapshot) -> List[Dict[str, str]]:
        """加载失败 task 的信息"""
        if not state.slice:
            return []

        failed = []
        for task_id in state.slice.failed_tasks:
            summary_file = self.lingflow_dir / f"{task_id}-SUMMARY.md"
            if summary_file.exists():
                content = summary_file.read_text(encoding="utf-8")
                failed.append({
                    "task_id": task_id,
                    "error": content[:500],
                })
            else:
                failed.append({
                    "task_id": task_id,
                    "error": "(failed, no details)",
                })

        return failed

    def _load_task_plan(self, task_id: str) -> str:
        """加载当前 task plan"""
        plan_file = self.lingflow_dir / f"{task_id}-PLAN.md"
        if not plan_file.exists():
            return ""

        return plan_file.read_text(encoding="utf-8")[:5000]

    def _extract_summary_section(self, content: str) -> str:
        """从 markdown 中提取 Summary/概述 部分"""
        import re

        patterns = [
            r"##\s*(?:Summary|概述|摘要)\s*\n(.*?)(?=\n##|\Z)",
            r"#\s*(?:Summary|概述|摘要)\s*\n(.*?)(?=\n#|\Z)",
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()[:2000]

        return ""

    def _calculate_total_chars(self, ctx: PreInlinedContext) -> int:
        """计算上下文总字符数"""
        total = 0
        total += len(ctx.roadmap_summary)
        total += len(ctx.slice_plan)
        total += len(ctx.task_plan)
        for s in ctx.completed_tasks_summaries:
            total += len(s.get("summary", ""))
        for f in ctx.failed_tasks_info:
            total += len(f.get("error", ""))
        return total

    def _truncate_context(self, ctx: PreInlinedContext) -> PreInlinedContext:
        """截断上下文到最大大小

        优先保留：task_plan > slice_plan > 最近完成的 summaries > roadmap > 更早的 summaries
        """
        ctx.truncated = True
        budget = self.max_context_chars

        # 1. 保留 task plan（最高优先级）
        task_budget = min(len(ctx.task_plan), budget // 3)
        ctx.task_plan = ctx.task_plan[:task_budget]
        budget -= task_budget

        # 2. 保留 slice plan
        slice_budget = min(len(ctx.slice_plan), budget // 3)
        ctx.slice_plan = ctx.slice_plan[:slice_budget]
        budget -= slice_budget

        # 3. 保留最近的 completed summaries（最多5个）
        if ctx.completed_tasks_summaries:
            kept = []
            for s in reversed(ctx.completed_tasks_summaries):
                if budget <= 0:
                    break
                summary_text = s.get("summary", "")
                trunc = summary_text[:500]
                budget -= len(trunc)
                kept.insert(0, {"task_id": s["task_id"], "summary": trunc})
            ctx.completed_tasks_summaries = kept[-5:]

        # 4. roadmap 摘要（剩余预算）
        ctx.roadmap_summary = ctx.roadmap_summary[:max(0, budget)]

        # 5. 失败信息只保留最近2个
        ctx.failed_tasks_info = ctx.failed_tasks_info[-2:]
        for f in ctx.failed_tasks_info:
            f["error"] = f.get("error", "")[:200]

        ctx.total_chars = self._calculate_total_chars(ctx)
        return ctx
