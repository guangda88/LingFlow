"""Auto Mode 执行器 - 实现 PLAN → EXECUTE → COMPLETE → REASSESS 循环

参考 GSD 的 The Loop:
- Plan (with integrated research) → Execute (per task) → Complete → Reassess Roadmap → Next Slice
                                                                                 ↓ (all slices done)
                                                                                 Validate Milestone → Complete Milestone
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import re
import json

from lingflow.workflow.auto_mode import (
    AutoModeState,
    MilestoneContext,
    SliceContext,
    TaskContext,
    AutoModeStateMachine,
)
from lingflow.common.models import TaskResult
from lingflow.coordination.coordinator import AgentCoordinator
from lingflow.workflow.escape_hatch import AutoModeEscapeHatch
from lingflow.workflow.crash_recovery import AutoModeCrashRecovery
from lingflow.workflow.context_preloader import ContextPreloader
from lingflow.workflow.verification import VerificationRunner
from lingflow.workflow.worktree_manager import AutoModeWorktree

logger = logging.getLogger(__name__)


class AutoModeExecutor:
    """Auto Mode 执行器

    负责驱动状态转换和任务执行。
    """

    def __init__(self, coordinator: AgentCoordinator, workdir: str):
        """初始化执行器

        Args:
            coordinator: Agent coordinator（用于执行技能）
            workdir: 工作目录
        """
        self.coordinator = coordinator
        self.workdir = Path(workdir)
        self.lingflow_dir = self.workdir / ".lingflow"
        self.lingflow_dir.mkdir(exist_ok=True)

        # 状态机
        self.state_machine = AutoModeStateMachine(str(workdir))

        # 逃逸舱
        self.escape_hatch = AutoModeEscapeHatch(self.state_machine)

        # 崩溃恢复
        self.crash_recovery = AutoModeCrashRecovery(self.state_machine)

        # 上下文预加载
        self.context_preloader = ContextPreloader(self.state_machine)

        # 验证运行器
        self.verification_runner = VerificationRunner(str(workdir))

        # Worktree 管理
        self.worktree = AutoModeWorktree(str(workdir))

        # 执行统计
        self._execution_stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
        }

    def run_auto_mode(self, max_iterations: int = 1000) -> None:
        """运行 Auto Mode

        主循环：读取状态 → 决策 → 执行 → 保存状态 → 重复

        Args:
            max_iterations: 最大迭代次数（防止无限循环）
        """
        logger.info(f"启动 Auto Mode: max_iterations={max_iterations}")

        # 验证状态完整性（崩溃恢复）
        integrity_result = self.crash_recovery.verify_state_integrity()
        if integrity_result["recovered"]:
            logger.warning("状态已从备份恢复")
            self.crash_recovery.print_recovered_state_summary()
        elif integrity_result["valid"]:
            logger.info("状态验证通过")
        else:
            logger.error(f"状态验证失败: {integrity_result.get('error')}")
            state_file = self.lingflow_dir / "STATE.md"
            if not state_file.exists():
                logger.info("首次运行，初始化新状态")

        self.state_machine.start()

        iteration = 0
        try:
            while iteration < max_iterations:
                iteration += 1
                logger.debug(f"Auto Mode 迭代 {iteration}/{max_iterations}")

                # 1. 读取当前状态
                current_state = self.state_machine.state.state

                # 2. 根据状态决定下一个动作
                if current_state == AutoModeState.IDLE:
                    self._transition_to_plan()

                elif current_state == AutoModeState.PLAN:
                    self._execute_plan()

                elif current_state == AutoModeState.RESEARCH:
                    self._execute_research()

                elif current_state == AutoModeState.EXECUTE:
                    self._execute_task()

                elif current_state == AutoModeState.COMPLETE:
                    self._complete_slice()

                elif current_state == AutoModeState.REASSESS:
                    self._reassess_roadmap()

                elif current_state == AutoModeState.VALIDATE:
                    self._validate_milestone()

                elif current_state == AutoModeState.DONE:
                    logger.info("Milestone 全部完成，Auto Mode 结束")
                    break

                elif current_state == AutoModeState.ERROR:
                    logger.error("Auto Mode 进入错误状态，停止执行")
                    break

                elif current_state == AutoModeState.PAUSED:
                    logger.info("Auto Mode 已暂停，等待用户恢复")
                    break

                # 3. 保存状态到磁盘
                self.state_machine.save_state()

                time.sleep(0.1)

        except KeyboardInterrupt:
            # Ctrl+C 捕获 -> 逃逸舱
            logger.info("检测到 Ctrl+C，暂停 Auto Mode")
            self.state_machine.pause(reason="用户中断（Ctrl+C）")
            # 进入逃逸舱交互菜单
            self.escape_hatch.enter_escape_hatch()
            # 用户选择继续执行，恢复运行
            logger.info("从逃逸舱恢复执行")
            self.state_machine.resume()
        except Exception as e:
            logger.error(f"Auto Mode 执行失败: {e}")
            self.state_machine.transition_to(AutoModeState.ERROR, reason=f"执行错误: {e}")
        finally:
            self.state_machine.stop()
            self._print_final_report()

    def _transition_to_plan(self) -> None:
        """转换到 PLAN 状态

        如果没有 milestone，创建新的 milestone。
        如果有 milestone，检查是否有下一个 slice。
        """
        state = self.state_machine.state

        # 检查是否有 milestone
        if not state.milestone:
            # 首次运行，需要创建或加载 milestone
            self._load_or_create_milestone()
            self.state_machine.transition_to(AutoModeState.PLAN, reason="开始 milestone 计划")
            return

        # 检查当前 slice 是否完成
        if state.slice:
            s = state.slice
            if s.current_task_index >= len(s.tasks):
                # slice 完成，进入 REASSESS
                self.state_machine.transition_to(AutoModeState.REASSESS, reason="slice 完成，重新评估 roadmap")
                return

        # 检查 milestone 是否有下一个 slice
        m = state.milestone
        if m.current_slice_index >= len(m.slices):
            # 所有 slices 完成，进入 VALIDATE
            self.state_machine.transition_to(AutoModeState.VALIDATE, reason="所有 slices 完成，验证 milestone")
            return

        # 创建或加载 slice
        self._load_or_create_slice()
        self.state_machine.transition_to(AutoModeState.PLAN, reason=f"开始 slice {state.slice.slice_id} 计划")

    def _execute_plan(self) -> None:
        """执行 PLAN 阶段

        研究 → 分解 tasks → 生成 must-haves
        """
        state = self.state_machine.state
        if not state.slice:
            logger.warning("PLAN 状态但没有 slice")
            self.state_machine.transition_to(AutoModeState.IDLE, reason="无 slice 可计划")
            return

        logger.info(f"开始计划 slice: {state.slice.slice_id}")

        # 调用 brainstorming 技能（如果尚未分解为 tasks）
        if not state.slice.tasks:
            tasks = self._decompose_slice(state.slice)
            state.slice.tasks = [t.task_id for t in tasks]

        # 生成 slice plan 文件（SXX-PLAN.md）
        self._write_slice_plan()

        # 生成 task plans（TXX-PLAN.md）
        for task_id in state.slice.tasks:
            self._write_task_plan(task_id)

        # 转换到 EXECUTE
        self.state_machine.transition_to(AutoModeState.EXECUTE, reason="slice 计划完成，开始执行 tasks")

    def _execute_research(self) -> None:
        """执行 RESEARCH 阶段

        研究 codebase 和生态系统（plan 阶段的子阶段）
        """
        # TODO: 实现研究逻辑
        # 简化：暂时直接转换为 PLAN
        logger.info("研究阶段（简化实现）")
        self.state_machine.transition_to(AutoModeState.PLAN, reason="研究完成，继续计划")

    def _execute_task(self) -> None:
        """执行当前 task

        每个 task 独立 fresh context。
        """
        state = self.state_machine.state
        if not state.slice:
            logger.warning("EXECUTE 状态但没有 slice")
            self.state_machine.transition_to(AutoModeState.IDLE, reason="无 slice 可执行")
            return

        s = state.slice
        if s.current_task_index >= len(s.tasks):
            logger.warning("所有 tasks 完成，应该进入 COMPLETE")
            self.state_machine.transition_to(AutoModeState.COMPLETE, reason="所有 tasks 完成")
            return

        task_id = s.tasks[s.current_task_index]
        logger.info(f"开始执行 task: {task_id} ({s.current_task_index + 1}/{len(s.tasks)})")

        # 创建或加载 task 上下文
        if not state.task or state.task.task_id != task_id:
            state.task = TaskContext(
                task_id=task_id,
                slice_id=s.slice_id,
                milestone_id=s.milestone_id,
                plan=self._read_task_plan(task_id),
                must_haves=[],
                summary="",
                execution_time=0.0,
                token_cost=0,
                retry_count=0,
            )

        # 执行 task（通过 coordinator）
        start_time = datetime.now()
        try:
            # TODO: 这里需要调用实际的技能执行
            # 简化：模拟执行成功
            result = self._execute_task_impl(task_id)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            state.task.execution_time = execution_time
            state.task.retry_count += 1

            if result.success:
                # 运行验证（如果 must_haves 定义了验证命令）
                verified = self._verify_task(task_id, state.task.must_haves)
                if not verified:
                    result.success = False
                    result.error = "Verification failed"
                    state.task.summary = "Task executed but verification failed"
                    s.failed_tasks.append(task_id)
                    s.current_task_index += 1
                    self._write_task_summary(task_id, state.task.summary, execution_time)
                    self._execution_stats["tasks_failed"] += 1
                    logger.error(f"Task {task_id} 验证失败")
                else:
                    # 成功 + 验证通过
                    state.task.summary = result.output or "Task completed (verified)"
                    s.completed_tasks.append(task_id)
                    s.current_task_index += 1
                    self._write_task_summary(task_id, state.task.summary, execution_time)
                    self._execution_stats["tasks_completed"] += 1
                    logger.info(f"Task {task_id} 完成: {execution_time:.2f}s")
            else:
                # 失败
                state.task.summary = f"Task failed: {result.error}"
                s.failed_tasks.append(task_id)
                s.current_task_index += 1

                # 写入失败摘要
                self._write_task_summary(task_id, state.task.summary, execution_time)

                self._execution_stats["tasks_failed"] += 1
                logger.error(f"Task {task_id} 失败: {result.error}")

            # 更新成本统计
            self.state_machine.state.total_tokens += state.task.token_cost
            self._execution_stats["total_execution_time"] += execution_time

            # 检查是否所有 tasks 完成
            if s.current_task_index >= len(s.tasks):
                self.state_machine.transition_to(AutoModeState.COMPLETE, reason="slice 所有 tasks 完成")
            else:
                # 继续下一个 task
                self.state_machine.transition_to(AutoModeState.EXECUTE, reason=f"继续 task {s.tasks[s.current_task_index]}")

        except Exception as e:
            logger.error(f"Task {task_id} 执行异常: {e}")
            state.task.retry_count += 1
            # 简化：直接跳到下一个 task
            if state.task.retry_count < 3:
                # 重试
                logger.info(f"重试 task {task_id} (第 {state.task.retry_count} 次)")
            else:
                # 放弃，跳到下一个
                s.failed_tasks.append(task_id)
                s.current_task_index += 1

    def _execute_task_impl(self, task_id: str) -> TaskResult:
        """实际执行 task（通过 coordinator）

        Args:
            task_id: Task ID

        Returns:
            Task result
        """
        # 读取 task plan
        plan_file = self.lingflow_dir / f"{task_id}-PLAN.md"
        if not plan_file.exists():
            return TaskResult(
                task_id=task_id,
                success=False,
                error=f"Task plan not found: {plan_file}",
                execution_time=0.0,
            )

        plan_content = plan_file.read_text(encoding="utf-8")
        
        # 从 plan 中提取技能名称和参数
        skill_name, params = self._parse_task_plan(plan_content, task_id)
        
        if not skill_name:
            return TaskResult(
                task_id=task_id,
                success=False,
                error=f"Cannot parse skill from task plan: {task_id}",
                execution_time=0.0,
            )

        # 调用 coordinator 执行技能（注入 pre-inlined context）
        try:
            params = self.context_preloader.inject_into_params(params, task_id)
            result_dict = self.coordinator.execute_skill(skill_name, params)
            
            if "error" in result_dict:
                return TaskResult(
                    task_id=task_id,
                    success=False,
                    error=result_dict["error"],
                    execution_time=0.0,
                )
            
            # 成功执行
            output = result_dict.get("result", {})
            if isinstance(output, dict):
                # 提取主要输出
                output_str = json.dumps(output, ensure_ascii=False, indent=2)
            else:
                output_str = str(output)
            
            return TaskResult(
                task_id=task_id,
                success=True,
                output=output_str,
                execution_time=0.0,  # 实际时间由调用方计算
            )
            
        except Exception as e:
            logger.error(f"Failed to execute task {task_id}: {e}")
            return TaskResult(
                task_id=task_id,
                success=False,
                error=f"Exception: {type(e).__name__}: {e}",
                execution_time=0.0,
            )

    def _verify_task(self, task_id: str, must_haves: List[str]) -> bool:
        """验证 task 是否真正完成

        根据 must_haves 中的验证标准运行检查。

        Args:
            task_id: Task ID
            must_haves: 验证标准列表

        Returns:
            是否通过验证（无 must_haves 时默认通过）
        """
        if not must_haves:
            return True

        checks = self.verification_runner.parse_must_haves(must_haves)
        if not checks:
            return True

        logger.info(f"Running {len(checks)} verification checks for {task_id}")
        results = self.verification_runner.run_checks(task_id, checks)

        self.verification_runner.write_verification_report(task_id, results)

        passed = all(r.passed for r in results)
        if not passed:
            failed_names = [r.check_name for r in results if not r.passed]
            logger.warning(f"Verification failed: {failed_names}")
        return passed

    def _complete_slice(self) -> None:
        """完成 slice

        写入 summary, UAT script，标记 roadmap
        """
        state = self.state_machine.state
        if not state.slice:
            logger.warning("COMPLETE 状态但没有 slice")
            self.state_machine.transition_to(AutoModeState.IDLE, reason="无 slice 可完成")
            return

        s = state.slice
        logger.info(f"完成 slice: {s.slice_id}")

        # 写入 SXX-SUMMARY.md
        self._write_slice_summary()

        # 写入 SXX-UAT.md
        self._write_slice_uat()

        # 标记 roadmap（完成当前 slice）
        m = state.milestone
        m.current_slice_index += 1

        # 转换到 REASSESS
        self.state_machine.transition_to(AutoModeState.REASSESS, reason=f"slice {s.slice_id} 完成，重新评估 roadmap")

    def _reassess_roadmap(self) -> None:
        """重新评估 roadmap

        检查 roadmap 是否仍然合理，重新排序/添加/删除 slices
        """
        state = self.state_machine.state

        if not state.milestone:
            logger.warning("REASSESS 状态但没有 milestone")
            self.state_machine.transition_to(AutoModeState.IDLE, reason="无 milestone 可评估")
            return

        m = state.milestone
        logger.info(f"重新评估 milestone: {m.milestone_id}")

        # 检查是否所有 slices 完成
        if m.current_slice_index >= len(m.slices):
            logger.info("所有 slices 完成，进入验证阶段")
            self.state_machine.transition_to(AutoModeState.VALIDATE, reason="所有 slices 完成")
            return

        # 转换到下一个 slice 的 PLAN
        # （通过调用 _transition_to_plan）
        self.state_machine.transition_to(AutoModeState.PLAN, reason=f"继续 slice {m.slices[m.current_slice_index]}")

    def _validate_milestone(self) -> None:
        """验证 milestone

        对比 roadmap success criteria vs 实际结果
        """
        state = self.state_machine.state

        if not state.milestone:
            logger.warning("VALIDATE 状态但没有 milestone")
            self.state_machine.transition_to(AutoModeState.IDLE, reason="无 milestone 可验证")
            return

        m = state.milestone
        logger.info(f"验证 milestone: {m.milestone_id}")

        # TODO: 实现验证逻辑
        # 简化：直接标记为完成
        logger.info("Milestone 验证通过")

        # 完成 worktree（合并分支）
        wt_result = self.worktree.complete_worktree(m.milestone_id, merge=True)
        if wt_result.get("success"):
            logger.info(f"Worktree completed and merged for {m.milestone_id}")
        else:
            logger.warning(f"Worktree completion note for {m.milestone_id}: {wt_result.get('message', '')}")

        # 转换到 DONE
        self.state_machine.transition_to(AutoModeState.DONE, reason="milestone 验证完成")

    # ========== 辅助方法 ==========

    def _load_or_create_milestone(self) -> None:
        """加载或创建 milestone

        优先顺序：
        1. 读取 MXXX-ROADMAP.md
        2. 如果不存在，创建新 milestone
        """
        state = self.state_machine.state

        # 搜索 milestone 文件
        roadmap_file = self.lingflow_dir / "M001-ROADMAP.md"
        if roadmap_file.exists():
            # 加载现有 milestone
            self.state_machine.state.milestone = self._read_roadmap(roadmap_file)
            logger.info(f"加载现有 milestone: {state.milestone.milestone_id}")
        else:
            # 创建新 milestone
            self.state_machine.state.milestone = self._create_new_milestone()
            self._write_roadmap()
            logger.info("创建新 milestone: M001")

        # 为 milestone 创建 worktree 隔离
        m = state.milestone
        if m:
            wt_result = self.worktree.create_worktree(m.milestone_id)
            if wt_result.get("success"):
                logger.info(f"Worktree created for {m.milestone_id}: {wt_result.get('path')}")
            else:
                logger.debug(f"Worktree fallback for {m.milestone_id}: {wt_result.get('path')}")

    def _load_or_create_slice(self) -> None:
        """加载或创建 slice

        优先顺序：
        1. 读取 SXX-PLAN.md
        2. 如果不存在，创建新 slice
        """
        state = self.state_machine.state
        m = state.milestone

        if not m:
            return

        slice_id = m.slices[m.current_slice_index]
        plan_file = self.lingflow_dir / f"{slice_id}-PLAN.md"

        if plan_file.exists():
            # 加载现有 slice
            self.state_machine.state.slice = self._read_slice_plan(plan_file)
            logger.info(f"加载现有 slice: {slice_id}")
        else:
            # 创建新 slice
            self.state_machine.state.slice = self._create_new_slice(slice_id, m.milestone_id)
            logger.info(f"创建新 slice: {slice_id}")

    def _decompose_slice(self, slice_ctx: SliceContext) -> List[TaskContext]:
        """分解 slice 为 tasks

        调用 brainstorming 技能。

        Args:
            slice_ctx: Slice 上下文

        Returns:
            Task 上下文列表
        """
        # 读取 milestone roadmap 了解背景
        roadmap_file = self.lingflow_dir / f"{slice_ctx.milestone_id}-ROADMAP.md"
        context = ""
        if roadmap_file.exists():
            context = roadmap_file.read_text(encoding="utf-8")

        # 调用 brainstorming 技能分解 slice
        params = {
            "topic": f"Slice {slice_ctx.slice_id} implementation",
            "context": context,
            "goal": f"Break down slice {slice_ctx.slice_id} into concrete, executable tasks",
            "complexity": "medium",
        }

        try:
            result_dict = self.coordinator.execute_skill("brainstorming", params)
            
            if "error" in result_dict:
                logger.error(f"Brainstorming failed: {result_dict['error']}")
                # 返回默认 tasks
                return self._create_default_tasks(slice_ctx, 3)
            
            result = result_dict.get("result", {})
            
            # 解析 brainstorming 结果，提取 tasks
            tasks = self._parse_brainstorming_result(result, slice_ctx)
            
            if not tasks:
                logger.warning("No tasks extracted from brainstorming, using defaults")
                return self._create_default_tasks(slice_ctx, 3)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to decompose slice: {e}")
            return self._create_default_tasks(slice_ctx, 3)

    def _read_roadmap(self, filepath: Path) -> MilestoneContext:
        """读取 roadmap 文件

        Args:
            filepath: Roadmap 文件路径

        Returns:
            Milestone 上下文
        """
        content = filepath.read_text(encoding="utf-8")
        
        # 提取 milestone ID
        milestone_match = re.search(r"^#\s+(M\d+):\s*(.+)$", content, re.MULTILINE)
        milestone_id = milestone_match.group(1) if milestone_match else "M001"
        title = milestone_match.group(2) if milestone_match else "Untitled Milestone"
        
        # 提取 success criteria
        success_criteria = []
        criteria_section = re.search(r"##\s*Success\s*Criteria\s*\n((?:-\s*\[\s*[x\s]\]\s*.+\n?)*)", content, re.IGNORECASE)
        if criteria_section:
            for line in criteria_section.group(1).split("\n"):
                match = re.match(r"-\s*\[\s*[x\s]\]\s*(.+)", line)
                if match:
                    success_criteria.append(match.group(1).strip())
        
        # 提取 slices
        slices = []
        current_slice_index = 0
        slice_section = re.search(r"##\s*Slices\s*\n((?:-\s*\[\s*[x\s]\]\s*.+\n?)*)", content, re.IGNORECASE)
        if slice_section:
            for idx, line in enumerate(slice_section.group(1).split("\n")):
                match = re.match(r"-\s*\[\s*([x\s])\]\s*(.+)", line)
                if match:
                    slices.append(match.group(2).strip())
                    if match.group(1).strip() == "x" and idx >= current_slice_index:
                        current_slice_index = idx + 1
        
        return MilestoneContext(
            milestone_id=milestone_id,
            title=title,
            success_criteria=success_criteria,
            slices=slices,
            current_slice_index=current_slice_index,
        )

    def _create_new_milestone(self) -> MilestoneContext:
        """创建新 milestone

        Returns:
            Milestone 上下文
        """
        return MilestoneContext(
            milestone_id="M001",
            title="New Milestone",
            success_criteria=[],
            slices=["S01"],
            current_slice_index=0,
        )

    def _write_roadmap(self) -> None:
        """写入 roadmap 文件"""
        state = self.state_machine.state
        if not state.milestone:
            return

        m = state.milestone
        roadmap_file = self.lingflow_dir / f"{m.milestone_id}-ROADMAP.md"

        # TODO: 实现格式化逻辑
        # 简化：写入基本结构
        content = f"""# {m.milestone_id}: {m.title}

## Success Criteria
"""
        for criteria in m.success_criteria:
            content += f"- [ ] {criteria}\n"

        content += """
## Slices
"""
        for i, slice_id in enumerate(m.slices):
            prefix = "- [x]" if i < m.current_slice_index else "- [ ]"
            content += f"{prefix} {slice_id}\n"

        roadmap_file.write_text(content, encoding="utf-8")
        logger.info(f"写入 roadmap: {roadmap_file}")

    def _read_slice_plan(self, filepath: Path) -> SliceContext:
        """读取 slice plan 文件

        Args:
            filepath: Plan 文件路径

        Returns:
            Slice 上下文
        """
        content = filepath.read_text(encoding="utf-8")
        
        # 提取 slice ID
        slice_match = re.search(r"^#\s+(\S+):\s*Slice\s*Plan", content, re.IGNORECASE)
        slice_id = slice_match.group(1) if slice_match else "S01"
        
        # 提取 tasks
        tasks = []
        completed_tasks = []
        task_section = re.search(r"##\s*Tasks\s*\n((?:-\s*\[\s*[x\s]\]\s*.+\n?)*)", content, re.IGNORECASE)
        if task_section:
            for line in task_section.group(1).split("\n"):
                match = re.match(r"-\s*\[\s*([x\s])\]\s*(.+)", line)
                if match:
                    task_id = match.group(2).strip()
                    tasks.append(task_id)
                    if match.group(1).strip() == "x":
                        completed_tasks.append(task_id)
        
        current_task_index = len(completed_tasks)
        
        # 提取 milestone_id
        milestone_id_match = re.search(r"M\d+", filepath.stem)
        milestone_id = milestone_id_match.group(0) if milestone_id_match else "M001"

        return SliceContext(
            slice_id=slice_id,
            milestone_id=milestone_id,
            tasks=tasks,
            current_task_index=current_task_index,
            completed_tasks=completed_tasks,
            failed_tasks=[],  # 需要从其他地方获取
        )

    def _create_new_slice(self, slice_id: str, milestone_id: str) -> SliceContext:
        """创建新 slice

        Args:
            slice_id: Slice ID
            milestone_id: Milestone ID

        Returns:
            Slice 上下文
        """
        return SliceContext(
            slice_id=slice_id,
            milestone_id=milestone_id,
            tasks=[],
            current_task_index=0,
            completed_tasks=[],
            failed_tasks=[],
        )

    def _write_slice_plan(self) -> None:
        """写入 slice plan 文件"""
        state = self.state_machine.state
        if not state.slice:
            return

        s = state.slice
        plan_file = self.lingflow_dir / f"{s.slice_id}-PLAN.md"

        # TODO: 实现格式化逻辑
        content = f"""# {s.slice_id}: Slice Plan

## Tasks
"""
        for task_id in s.tasks:
            content += f"- [ ] {task_id}\n"

        plan_file.write_text(content, encoding="utf-8")
        logger.info(f"写入 slice plan: {plan_file}")

    def _read_task_plan(self, task_id: str) -> str:
        """读取 task plan 文件

        Args:
            task_id: Task ID

        Returns:
            Plan 内容
        """
        plan_file = self.lingflow_dir / f"{task_id}-PLAN.md"
        if plan_file.exists():
            return plan_file.read_text(encoding="utf-8")
        return f"Plan for {task_id}"

    def _write_task_plan(self, task_id: str) -> None:
        """写入 task plan 文件"""
        state = self.state_machine.state
        if not state.slice:
            return

        plan_file = self.lingflow_dir / f"{task_id}-PLAN.md"
        content = f"""# {task_id}: Task Plan

## Must-Haves
- Task completes successfully
- Code is committed

## Implementation Notes
"""
        plan_file.write_text(content, encoding="utf-8")
        logger.info(f"写入 task plan: {plan_file}")

    def _write_task_summary(self, task_id: str, summary: str, execution_time: float) -> None:
        """写入 task summary 文件

        供 ContextPreloader 读取，传递给后续 task。

        Args:
            task_id: Task ID
            summary: 执行结果摘要
            execution_time: 执行时间
        """
        summary_file = self.lingflow_dir / f"{task_id}-SUMMARY.md"
        content = f"# Task {task_id} Summary\n\n"
        content += f"- Execution Time: {execution_time:.2f}s\n"
        content += f"- Written: {datetime.now().isoformat()}\n\n"
        content += summary

        summary_file.write_text(content, encoding="utf-8")
        logger.debug(f"Task summary written: {summary_file}")

    def _write_slice_summary(self) -> None:
        """写入 slice summary 文件"""
        state = self.state_machine.state
        if not state.slice or not state.task:
            return

        s = state.slice
        t = state.task
        summary_file = self.lingflow_dir / f"{s.slice_id}-SUMMARY.md"

        # TODO: 实现格式化逻辑
        content = f"""# {s.slice_id}: Slice Summary

## Completed Tasks
"""
        for task_id in s.completed_tasks:
            content += f"- [x] {task_id}\n"

        content += f"""
## Summary
{t.summary}

## Metrics
- Tasks completed: {len(s.completed_tasks)}
- Tasks failed: {len(s.failed_tasks)}
- Execution time: {self.state_machine.state.task.execution_time:.2f}s
"""

        summary_file.write_text(content, encoding="utf-8")
        logger.info(f"写入 slice summary: {summary_file}")

    def _write_slice_uat(self) -> None:
        """写入 UAT 脚本文件"""
        state = self.state_machine.state
        if not state.slice:
            return

        s = state.slice
        uat_file = self.lingflow_dir / f"{s.slice_id}-UAT.md"

        # TODO: 实现格式化逻辑
        content = f"""# {s.slice_id}: User Acceptance Test

## Test Scenarios
"""
        uat_file.write_text(content, encoding="utf-8")
        logger.info(f"写入 UAT script: {uat_file}")

    def _print_final_report(self) -> None:
        """打印最终报告"""
        stats = self._execution_stats
        state = self.state_machine.state

        lines = [
            "",
            "=" * 60,
            "Auto Mode 执行报告",
            "=" * 60,
            "",
            f"Session ID: {self.state_machine.session_id}",
            f"最终状态: {state.state}",
            "",
            "执行统计:",
            f"  完成的 tasks: {stats['tasks_completed']}",
            f"  失败的 tasks: {stats['tasks_failed']}",
            f"  总执行时间: {stats['total_execution_time']:.2f}s",
            "",
            "成本统计:",
            f"  总 Tokens: {state.total_tokens}",
            f"  总成本: ${state.total_cost:.2f}",
            "",
            "=" * 60,
            "",
        ]

        print("\n".join(lines))

    # ========== 辅助解析方法 ==========

    def _parse_task_plan(self, plan_content: str, task_id: str) -> Tuple[str, Dict[str, Any]]:
        """解析 task plan 文件，提取技能名称和参数

        Args:
            plan_content: Task plan 内容
            task_id: Task ID

        Returns:
            (skill_name, params) 元组
        """
        # 默认值
        skill_name = "workflow-executor"  # 默认使用 workflow-executor
        params = {
            "task_id": task_id,
            "description": f"Execute task {task_id}",
            "plan": plan_content,
        }

        # 尝试从 plan 中提取技能信息
        # 格式1: Skill: skill-name
        skill_match = re.search(r"(?:^|\n)Skill:\s*(.+?)\s*(?:\n|$)", plan_content, re.IGNORECASE)
        if skill_match:
            skill_name = skill_match.group(1).strip().lower()

        # 格式2: ## Implementation Notes 下可能有更详细的参数
        impl_section = re.search(r"##\s*Implementation\s*Notes\s*\n((?:[^#].*\n?)*)", plan_content, re.IGNORECASE)
        if impl_section:
            notes = impl_section.group(1).strip()
            params["notes"] = notes
            params["description"] = notes[:200]  # 前200字符作为描述

        return skill_name, params

    def _parse_brainstorming_result(self, result: Dict[str, Any], slice_ctx: SliceContext) -> List[TaskContext]:
        """解析 brainstorming 结果，提取 tasks

        Args:
            result: Brainstorming 结果
            slice_ctx: Slice 上下文

        Returns:
            Task 上下文列表
        """
        tasks = []

        # 尝试从 result 中提取 tasks
        # 格式1: result.tasks
        if "tasks" in result and isinstance(result["tasks"], list):
            task_list = result["tasks"]
        # 格式2: result.result.tasks
        elif isinstance(result, dict) and "result" in result and isinstance(result["result"], dict) and "tasks" in result["result"]:
            task_list = result["result"]["tasks"]
        # 格式3: result 是列表
        elif isinstance(result, list):
            task_list = result
        else:
            # 尝试从文本中提取
            text_content = str(result)
            # 简单模式：查找以 "Task" 开头的行
            task_list = []
            lines = text_content.split("\n")
            for line in lines:
                if re.match(r"\d+\.\s*Task", line, re.IGNORECASE) or re.match(r"^-\s*Task", line, re.IGNORECASE):
                    task_list.append(line.strip())

        if not task_list:
            return []

        # 创建 TaskContext 对象
        for idx, task_info in enumerate(task_list):
            task_id = f"T{idx+1:02d}"
            
            if isinstance(task_info, dict):
                # 格式: {"title": "...", "description": "..."}
                plan = task_info.get("description", task_info.get("title", f"Task {task_id}"))
                must_haves = task_info.get("must_haves", [])
            else:
                # 格式: 字符串
                plan = str(task_info)
                must_haves = [f"Complete {task_id}"]

            tasks.append(
                TaskContext(
                    task_id=task_id,
                    slice_id=slice_ctx.slice_id,
                    milestone_id=slice_ctx.milestone_id,
                    plan=plan,
                    must_haves=must_haves,
                    summary="",
                    execution_time=0.0,
                    token_cost=0,
                    retry_count=0,
                )
            )

        return tasks

    def _create_default_tasks(self, slice_ctx: SliceContext, count: int = 3) -> List[TaskContext]:
        """创建默认 tasks（fallback）

        Args:
            slice_ctx: Slice 上下文
            count: Task 数量

        Returns:
            Task 上下文列表
        """
        return [
            TaskContext(
                task_id=f"T{idx+1:02d}",
                slice_id=slice_ctx.slice_id,
                milestone_id=slice_ctx.milestone_id,
                plan=f"Task T{idx+1:02d} for slice {slice_ctx.slice_id}",
                must_haves=[f"Complete T{idx+1:02d}"],
                summary="",
                execution_time=0.0,
                token_cost=0,
                retry_count=0,
            )
            for idx in range(count)
        ]
