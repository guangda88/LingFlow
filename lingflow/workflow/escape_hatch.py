"""Auto Mode 逃逸舱 - 交互式暂停和恢复机制

参考 GSD 的 Escape Hatch：Ctrl+C 暂停，交互式菜单，恢复执行
"""

import logging
from typing import Optional, Callable
from dataclasses import dataclass

from lingflow.workflow.auto_mode import (
    AutoModeState,
    AutoModeStateMachine,
)

logger = logging.getLogger(__name__)


@dataclass
class EscapeHatchAction:
    """逃逸舱操作"""
    key: str
    description: str
    action: Callable[[], Optional[bool]]  # 返回 True 表示继续暂停，False 表示恢复执行


class AutoModeEscapeHatch:
    """Auto Mode 逃逸舱

    提供 Ctrl+C 暂停后的交互式菜单。
    """

    def __init__(self, state_machine: AutoModeStateMachine):
        """初始化逃逸舱

        Args:
            state_machine: 状态机实例
        """
        self.state_machine = state_machine

        # 可用操作
        self.actions = [
            EscapeHatchAction("1", "查看当前状态", self._show_status),
            EscapeHatchAction("2", "查看进度", self._show_progress),
            EscapeHatchAction("3", "查看计划 (Milestone/Slice/Task)", self._show_plan),
            EscapeHatchAction("4", "查看日志", self._show_logs),
            EscapeHatchAction("5", "修改当前任务", self._modify_current_task),
            EscapeHatchAction("6", "跳过当前任务", self._skip_current_task),
            EscapeHatchAction("7", "标记任务完成", self._mark_task_complete),
            EscapeHatchAction("8", "回退到上一状态", self._revert_state),
            EscapeHatchAction("c", "继续执行 (resume)", self._resume_execution),
            EscapeHatchAction("s", "保存并退出", self._save_and_exit),
            EscapeHatchAction("q", "退出（不保存）", self._quit_without_saving),
            EscapeHatchAction("?", "帮助", self._show_help),
        ]

    def enter_escape_hatch(self) -> None:
        """进入逃逸舱交互菜单

        此方法在 Ctrl+C 被触发后调用。
        """
        self._print_header()

        while True:
            try:
                # 显示菜单
                self._print_menu()

                # 获取用户输入
                choice = input("\n请选择操作 [?] 帮助: ").strip().lower()

                # 查找并执行操作
                action = self._find_action(choice)
                if action:
                    should_pause = action.action()
                    if should_pause is False:
                        # 用户选择了继续执行
                        logger.info("用户选择继续执行")
                        break
                else:
                    print(f"无效选项: {choice}，请重新选择")

            except KeyboardInterrupt:
                print("\n\n检测到 Ctrl+C，再次按 Ctrl+C 退出逃逸舱")
                # 第一次 Ctrl+C 只是忽略，等待用户重新选择
            except EOFError:
                print("\n\n检测到 EOF，退出逃逸舱")
                break
            except Exception as e:
                logger.error(f"逃逸舱执行错误: {e}")
                print(f"\n错误: {e}")
                # 继续循环

    def _print_header(self) -> None:
        """打印逃逸舱头部"""
        print("\n" + "=" * 70)
        print("🚪 Auto Mode 逃逸舱")
        print("=" * 70)
        print("\nAuto Mode 已暂停。您可以在下方交互式菜单中：")
        print("  • 查看当前状态和进度")
        print("  • 修改计划或任务")
        print("  • 继续执行或退出")
        print()

    def _print_menu(self) -> None:
        """打印菜单"""
        print("\n" + "-" * 70)
        print("可用操作：")
        print("-" * 70)

        # 分组显示操作
        info_actions = self.actions[:4]  # 查看类操作
        modify_actions = self.actions[4:8]  # 修改类操作
        system_actions = self.actions[8:]  # 系统类操作

        print("📊 查看信息：")
        for action in info_actions:
            print(f"  {action.key:<2} - {action.description}")

        print("\n✏️  修改计划：")
        for action in modify_actions:
            print(f"  {action.key:<2} - {action.description}")

        print("\n⚙️  系统操作：")
        for action in system_actions:
            print(f"  {action.key:<2} - {action.description}")

    def _find_action(self, choice: str) -> Optional[EscapeHatchAction]:
        """查找操作

        Args:
            choice: 用户选择

        Returns:
            找到的操作，未找到则返回 None
        """
        for action in self.actions:
            if action.key == choice:
                return action
        return None

    # ========== 操作实现 ==========

    def _show_status(self) -> Optional[bool]:
        """查看当前状态"""
        state = self.state_machine.state

        print("\n" + "=" * 70)
        print("📊 当前状态")
        print("=" * 70)
        print(f"\nSession ID: {self.state_machine.session_id}")
        print(f"当前状态: {state.state}")
        print(f"开始时间: {state.started_at.strftime('%Y-%m-%d %H:%M:%S') if state.started_at else 'N/A'}")
        print(f"暂停原因: {state.paused_reason or 'N/A'}")

        # Milestone 信息
        if state.milestone:
            m = state.milestone
            print(f"\n📍 Milestone: {m.milestone_id} - {m.title}")
            print(f"  当前 Slice: {m.current_slice_index}/{len(m.slices)}")
            print(f"  Slices: {', '.join(m.slices)}")

        # Slice 信息
        if state.slice:
            s = state.slice
            print(f"\n📝 Slice: {s.slice_id}")
            print(f"  当前 Task: {s.current_task_index}/{len(s.tasks)}")
            print(f"  Tasks: {', '.join(s.tasks)}")
            print(f"  已完成: {len(s.completed_tasks)}")
            print(f"  失败: {len(s.failed_tasks)}")

        # Task 信息
        if state.task:
            t = state.task
            print(f"\n🔧 Task: {t.task_id}")
            print(f"  执行时间: {t.execution_time:.2f}s")
            print(f"  重试次数: {t.retry_count}")
            print(f"  Token 成本: {t.token_cost}")

        # 成本统计
        print("\n💰 成本统计:")
        print(f"  总 Tokens: {state.total_tokens}")
        print(f"  总成本: ${state.total_cost:.2f}")

        input("\n按 Enter 返回菜单...")
        return None  # 继续暂停

    def _show_progress(self) -> Optional[bool]:
        """查看进度"""
        state = self.state_machine.state

        print("\n" + "=" * 70)
        print("📈 执行进度")
        print("=" * 70)

        if state.milestone:
            m = state.milestone
            print(f"\nMilestone: {m.milestone_id}")
            print(f"  Progress: {m.current_slice_index}/{len(m.slices)} slices completed")

            # 显示每个 slice 的进度
            for i, slice_id in enumerate(m.slices):
                status = "✅" if i < m.current_slice_index else "⏳" if i == m.current_slice_index else "⬜"
                print(f"  {status} {slice_id}")

        if state.slice:
            s = state.slice
            print(f"\nSlice: {s.slice_id}")
            print(f"  Progress: {len(s.completed_tasks)}/{len(s.tasks)} tasks completed")

            # 显示每个 task 的进度
            for i, task_id in enumerate(s.tasks):
                if task_id in s.completed_tasks:
                    status = "✅"
                elif task_id in s.failed_tasks:
                    status = "❌"
                elif i < s.current_task_index:
                    status = "⚠️"
                else:
                    status = "⬜"
                print(f"  {status} {task_id}")

        input("\n按 Enter 返回菜单...")
        return None  # 继续暂停

    def _show_plan(self) -> Optional[bool]:
        """查看计划"""
        state = self.state_machine.state
        lingflow_dir = self.state_machine.workdir / ".lingflow"

        print("\n" + "=" * 70)
        print("📋 计划详情")
        print("=" * 70)

        # 显示 Milestone 计划
        if state.milestone:
            m = state.milestone
            roadmap_file = lingflow_dir / f"{m.milestone_id}-ROADMAP.md"

            print(f"\n📍 Milestone: {m.milestone_id} - {m.title}")
            print(f"  文件: {roadmap_file}")

            if roadmap_file.exists():
                print("\n" + "-" * 70)
                print(roadmap_file.read_text(encoding="utf-8")[:1000])
                if roadmap_file.stat().st_size > 1000:
                    print("\n... (内容过长，已截断)")
            else:
                print("  文件不存在")

        # 显示 Slice 计划
        if state.slice:
            s = state.slice
            plan_file = lingflow_dir / f"{s.slice_id}-PLAN.md"

            print(f"\n📝 Slice: {s.slice_id}")
            print(f"  文件: {plan_file}")

            if plan_file.exists():
                print("\n" + "-" * 70)
                print(plan_file.read_text(encoding="utf-8")[:1000])
                if plan_file.stat().st_size > 1000:
                    print("\n... (内容过长，已截断)")
            else:
                print("  文件不存在")

        # 显示 Task 计划
        if state.task:
            t = state.task
            plan_file = lingflow_dir / f"{t.task_id}-PLAN.md"

            print(f"\n🔧 Task: {t.task_id}")
            print(f"  文件: {plan_file}")

            if plan_file.exists():
                print("\n" + "-" * 70)
                content = plan_file.read_text(encoding="utf-8")
                print(content)
            else:
                print("  文件不存在")

        input("\n按 Enter 返回菜单...")
        return None  # 继续暂停

    def _show_logs(self) -> Optional[bool]:
        """查看日志"""
        print("\n" + "=" * 70)
        print("📜 日志（最近的 50 行）")
        print("=" * 70)

        # 尝试读取日志文件
        import os

        log_files = [
            "lingflow.log",
            "auto_mode.log",
        ]

        logs_found = False
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n📄 {log_file}:")
                print("-" * 70)

                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    # 显示最后 50 行
                    for line in lines[-50:]:
                        print(line.rstrip())

                logs_found = True

        if not logs_found:
            print("\n未找到日志文件")

        input("\n按 Enter 返回菜单...")
        return None  # 继续暂停

    def _modify_current_task(self) -> Optional[bool]:
        """修改当前任务"""
        state = self.state_machine.state

        if not state.slice or state.slice.current_task_index >= len(state.slice.tasks):
            print("\n没有当前任务可修改")
            input("\n按 Enter 返回菜单...")
            return None  # 继续暂停

        task_id = state.slice.tasks[state.slice.current_task_index]

        print(f"\n当前任务: {task_id}")

        # 显示当前任务计划
        plan_file = self.state_machine.workdir / ".lingflow" / f"{task_id}-PLAN.md"
        if plan_file.exists():
            print("\n当前计划:")
            print("-" * 70)
            print(plan_file.read_text(encoding="utf-8"))

        # 询问用户是否要修改
        choice = input("\n是否要修改此任务？ [y/N]: ").strip().lower()
        if choice != "y":
            print("取消修改")
            input("\n按 Enter 返回菜单...")
            return None  # 继续暂停

        # 获取新的计划内容
        print("\n请输入新的计划内容（按 Ctrl+D 结束输入）：")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass

        if lines:
            new_content = "\n".join(lines)
            plan_file.write_text(new_content, encoding="utf-8")
            print(f"\n✅ 任务计划已保存到: {plan_file}")
        else:
            print("\n取消修改（输入为空）")

        input("\n按 Enter 返回菜单...")
        return None  # 继续暂停

    def _skip_current_task(self) -> Optional[bool]:
        """跳过当前任务"""
        state = self.state_machine.state

        if not state.slice or state.slice.current_task_index >= len(state.slice.tasks):
            print("\n没有当前任务可跳过")
            input("\n按 Enter 返回菜单...")
            return None  # 继续暂停

        task_id = state.slice.tasks[state.slice.current_task_index]

        print(f"\n当前任务: {task_id}")
        choice = input(f"确定要跳过任务 {task_id} 吗？ [y/N]: ").strip().lower()

        if choice == "y":
            state.slice.failed_tasks.append(task_id)
            state.slice.current_task_index += 1
            print(f"✅ 已跳过任务 {task_id}")
        else:
            print("取消跳过")

        input("\n按 Enter 返回菜单...")
        return None  # 继续暂停

    def _mark_task_complete(self) -> Optional[bool]:
        """标记任务完成"""
        state = self.state_machine.state

        if not state.slice or state.slice.current_task_index >= len(state.slice.tasks):
            print("\n没有当前任务可标记")
            input("\n按 Enter 返回菜单...")
            return None  # 继续暂停

        task_id = state.slice.tasks[state.slice.current_task_index]

        print(f"\n当前任务: {task_id}")
        choice = input(f"确定要标记任务 {task_id} 为已完成吗？ [y/N]: ").strip().lower()

        if choice == "y":
            state.slice.completed_tasks.append(task_id)
            state.slice.current_task_index += 1
            print(f"✅ 已标记任务 {task_id} 为已完成")
        else:
            print("取消标记")

        input("\n按 Enter 返回菜单...")
        return None  # 继续暂停

    def _revert_state(self) -> Optional[bool]:
        """回退到上一状态"""
        state = self.state_machine.state

        print(f"\n当前状态: {state.state}")
        print("\n可用回退操作：")
        print("  1 - 回退到 Milestone 开始")
        print("  2 - 回退到 Slice 开始")
        print("  3 - 取消")

        choice = input("\n请选择: ").strip()

        if choice == "1":
            # 回退到 Milestone 开始
            if state.milestone:
                state.milestone.current_slice_index = 0
                state.slice = None
                state.task = None
                self.state_machine.transition_to(AutoModeState.PLAN, reason="用户回退到 Milestone 开始")
                print("✅ 已回退到 Milestone 开始")
        elif choice == "2":
            # 回退到 Slice 开始
            if state.slice:
                state.slice.current_task_index = 0
                state.slice.completed_tasks = []
                state.slice.failed_tasks = []
                state.task = None
                self.state_machine.transition_to(AutoModeState.EXECUTE, reason="用户回退到 Slice 开始")
                print("✅ 已回退到 Slice 开始")
        else:
            print("取消回退")

        input("\n按 Enter 返回菜单...")
        return None  # 继续暂停

    def _resume_execution(self) -> Optional[bool]:
        """继续执行"""
        print("\n正在恢复 Auto Mode 执行...")
        return False  # 退出逃逸舱，继续执行

    def _save_and_exit(self) -> Optional[bool]:
        """保存并退出"""
        print("\n正在保存状态...")
        self.state_machine.save_state()
        print("✅ 状态已保存")
        print("\nAuto Mode 已退出。下次启动时会从此状态恢复。")
        raise SystemExit(0)  # 退出程序

    def _quit_without_saving(self) -> Optional[bool]:
        """退出（不保存）"""
        print("\n正在退出...")
        choice = input("确定要退出吗？未保存的更改将丢失 [y/N]: ").strip().lower()
        if choice == "y":
            print("Auto Mode 已退出。")
            raise SystemExit(0)  # 退出程序
        else:
            print("取消退出")
            input("\n按 Enter 返回菜单...")
            return None  # 继续暂停

    def _show_help(self) -> Optional[bool]:
        """显示帮助"""
        print("\n" + "=" * 70)
        print("❓ 帮助")
        print("=" * 70)
        print("""
逃逸舱允许您在 Auto Mode 执行过程中暂停并交互。

快捷键：
  Ctrl+C    - 暂停 Auto Mode，进入逃逸舱
  Ctrl+D    - 在多行输入中结束输入

菜单操作：
  查看信息    - 查看当前状态、进度、计划、日志
  修改计划    - 修改当前任务、跳过任务、标记完成
  系统操作    - 继续执行、保存退出、退出

工作流程：
  1. Auto Mode 执行过程中按 Ctrl+C 暂停
  2. 在逃逸舱中查看/修改信息
  3. 选择 "继续执行" (c) 恢复 Auto Mode

注意事项：
  - 所有修改会立即生效
  - 状态会定期自动保存
  - 可随时选择 "保存并退出" (s)
""")

        input("\n按 Enter 返回菜单...")
        return None  # 继续暂停
