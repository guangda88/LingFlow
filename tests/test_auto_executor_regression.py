"""回归测试：验证 auto_executor.py 的 6 个 bug 修复

每个测试对应一个修复：
  1. _print_final_report 使用 state.total_cost（非 state.total.total_cost）
  2. 状态文件路径使用 self.lingflow_dir / "STATE.md"（非 self.state_machine.state_file）
  3. 任务失败后 current_task_index 递增（防止无限循环）
  4. _read_slice_plan 从文件名提取 milestone_id（非硬编码 "M001"）
  5. import time 在模块顶层（非循环内部）
  6. 状态文件路径一致性（无重复计算）

设计原则：
  - 不 mock 被测逻辑本身
  - 用真实 dataclass、真实文件系统、真实字符串操作
  - 每个测试验证修复后的行为，并在注释中说明修复前的失败模式
"""

import pytest
import tempfile
import shutil
import io
from pathlib import Path
from unittest.mock import patch

from lingflow.workflow.auto_executor import AutoModeExecutor
from lingflow.workflow.auto_mode import (
    StateSnapshot,
    SliceContext,
)
from lingflow.coordination.coordinator import AgentCoordinator


@pytest.fixture
def temp_workdir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def coordinator():
    return AgentCoordinator()


@pytest.fixture
def executor(coordinator, temp_workdir):
    return AutoModeExecutor(coordinator, str(temp_workdir))


# ============================================================
# Fix #1 (CRITICAL): _print_final_report 访问 state.total_cost
# 修复前：state.total.total_cost → AttributeError: 'StateSnapshot' has no 'total'
# 修复后：state.total_cost → 正确访问顶层字段
# ============================================================

class TestFix1FinalReportTotalCost:
    """修复 #1: _print_final_report 中的 total_cost 访问路径"""

    def test_print_final_report_uses_top_level_total_cost(self, executor):
        """_print_final_report 应该访问 state.total_cost 而非 state.total.total_cost

        修复前行为：AttributeError: 'StateSnapshot' object has no attribute 'total'
        修复后行为：正常打印，total_cost 值正确显示
        """
        executor.state_machine.state.total_cost = 42.50
        executor.state_machine.state.total_tokens = 15000
        executor._execution_stats["tasks_completed"] = 5
        executor._execution_stats["tasks_failed"] = 1
        executor._execution_stats["total_execution_time"] = 123.45

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            executor._print_final_report()

        output = captured.getvalue()

        assert "$42.50" in output, f"总成本未正确显示，输出: {output}"
        assert "15000" in output, f"总 tokens 未正确显示，输出: {output}"
        assert "5" in output, "完成的 tasks 数未正确显示"
        assert "1" in output, "失败的 tasks 数未正确显示"

    def test_print_final_report_zero_cost(self, executor):
        """total_cost=0 时不应崩溃"""
        executor.state_machine.state.total_cost = 0.0
        executor.state_machine.state.total_tokens = 0

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            executor._print_final_report()

        assert "$0.00" in captured.getvalue()

    def test_state_snapshot_has_no_total_attribute(self):
        """StateSnapshot 没有 .total 属性——这是 bug #1 的根因

        如果有人添加了 .total 属性，这个测试会失败，
        提醒维护者 _print_final_report 的访问路径需要相应更新。
        """
        snapshot = StateSnapshot()
        assert not hasattr(snapshot, "total"), (
            "StateSnapshot 不应该有 .total 属性。"
            "_print_final_report 直接访问 state.total_cost。"
            "如果添加了 .total 属性，请检查 _print_final_report 中的访问路径。"
        )
        assert hasattr(snapshot, "total_cost"), "StateSnapshot 必须有 total_cost 字段"
        assert hasattr(snapshot, "total_tokens"), "StateSnapshot 必须有 total_tokens 字段"

    def test_state_snapshot_serialization_round_trip_preserves_cost(self):
        """StateSnapshot 的 total_cost 在 to_dict/from_dict 往返后保持一致"""
        original = StateSnapshot(total_cost=99.99, total_tokens=50000)
        restored = StateSnapshot.from_dict(original.to_dict())

        assert restored.total_cost == 99.99
        assert restored.total_tokens == 50000


# ============================================================
# Fix #2 (MAJOR): 状态文件路径使用正确属性
# 修复前：self.state_machine.state_file.exists()
#         → AttributeError: 'AutoModeStateMachine' has no attribute 'state_file'
# 修复后：state_file = self.lingflow_dir / "STATE.md"
# ============================================================

class TestFix2StateFilePath:
    """修复 #2: 状态文件路径构造"""

    def test_state_machine_has_no_state_file_attribute(self):
        """AutoModeStateMachine 没有 .state_file 属性——这是 bug #2 的根因"""
        from lingflow.workflow.auto_mode import AutoModeStateMachine

        with tempfile.TemporaryDirectory() as td:
            sm = AutoModeStateMachine(td)
            assert not hasattr(sm, "state_file"), (
                "AutoModeStateMachine 不应该有 state_file 属性。"
                "run_auto_mode 中应该使用 self.lingflow_dir / 'STATE.md'。"
            )

    def test_executor_uses_lingflow_dir_for_state_path(self, executor, temp_workdir):
        """执行器应该通过 lingflow_dir 构造状态文件路径"""
        executor.state_machine.start()

        state_file = temp_workdir / ".lingflow" / "STATE.md"
        assert state_file.exists(), "状态文件应该通过 lingflow_dir 路径创建"

    def test_first_run_creates_state_when_no_file(self, executor, temp_workdir):
        """首次运行（无 STATE.md）时不应崩溃

        修复前：如果 state_file 属性不存在，启动时直接 AttributeError
        修复后：手动构造 state_file = self.lingflow_dir / "STATE.md"
        """
        state_file = temp_workdir / ".lingflow" / "STATE.md"
        assert not state_file.exists()

        executor.state_machine.start()

        assert state_file.exists()


# ============================================================
# Fix #3 (MAJOR): 任务失败后 current_task_index 递增
# 修复前：任务失败时不递增 current_task_index → 无限循环
# 修复后：所有三条路径（成功/验证失败/执行失败）都递增 index
# ============================================================

class TestFix3TaskFailureIndexIncrement:
    """修复 #3: 任务失败后 current_task_index 必须递增"""

    def _setup_executor_with_slice(self, executor, task_count=3):
        """创建有 N 个任务的 slice，返回可操作的 slice 对象"""
        executor.state_machine.state.slice = SliceContext(
            slice_id="S01",
            milestone_id="M001",
            tasks=[f"T{i:02d}" for i in range(1, task_count + 1)],
            current_task_index=0,
            completed_tasks=[],
            failed_tasks=[],
        )
        return executor.state_machine.state.slice

    def test_execute_failure_increments_index(self, executor, temp_workdir):
        """任务执行失败时，current_task_index 必须递增

        修复前：index 不变 → 下次迭代还是同一个 task → 无限循环
        修复后：index += 1 → 跳到下一个 task
        """
        s = self._setup_executor_with_slice(executor, task_count=3)
        assert s.current_task_index == 0

        executor._execute_task()

        assert s.current_task_index == 1, (
            f"任务失败后 index 未递增，当前值: {s.current_task_index}，预期: 1"
        )

    def test_verification_failure_increments_index(self, executor, temp_workdir):
        """验证失败（must_haves 检查不通过）时，index 也必须递增"""
        s = self._setup_executor_with_slice(executor, task_count=3)

        with patch.object(executor, "_execute_task_impl") as mock_impl:
            from lingflow.common.models import TaskResult

            mock_impl.return_value = TaskResult(
                task_id="T01",
                success=True,
                output="done",
                execution_time=1.0,
            )

            with patch.object(executor, "_verify_task", return_value=False):
                executor._execute_task()

        assert s.current_task_index == 1, "验证失败后 index 未递增"
        assert "T01" in s.failed_tasks, "验证失败的 task 应在 failed_tasks 中"

    def test_three_failures_dont_loop(self, executor, temp_workdir):
        """连续 3 个失败任务不会无限循环——index 每次都递增"""
        s = self._setup_executor_with_slice(executor, task_count=3)

        for _ in range(3):
            executor._execute_task()

        assert s.current_task_index == 3, (
            f"3 个失败后 index={s.current_task_index}，应该=3"
        )
        assert len(s.failed_tasks) == 3
        assert s.current_task_index >= len(s.tasks), "应该已经超出 task 列表范围"

    def test_success_also_increments_index(self, executor, temp_workdir):
        """任务成功时 index 也递增（验证原代码的正确路径没被破坏）"""
        s = self._setup_executor_with_slice(executor, task_count=3)

        with patch.object(executor, "_execute_task_impl") as mock_impl:
            from lingflow.common.models import TaskResult

            mock_impl.return_value = TaskResult(
                task_id="T01",
                success=True,
                output="done",
                execution_time=1.0,
            )

            with patch.object(executor, "_verify_task", return_value=True):
                executor._execute_task()

        assert s.current_task_index == 1
        assert "T01" in s.completed_tasks


# ============================================================
# Fix #4 (MAJOR): _read_slice_plan 从文件名提取 milestone_id
# 修复前：硬编码 milestone_id="M001"
# 修复后：re.search(r"M\d+", filepath.stem) 提取，fallback 到 "M001"
# ============================================================

class TestFix4MilestoneIdExtraction:
    """修复 #4: _read_slice_plan 中的 milestone_id 提取"""

    def test_extracts_milestone_from_filename_with_m_prefix(self, executor, temp_workdir):
        """文件名 M002-S01-PLAN.md 应提取出 milestone_id='M002'"""
        plan_file = temp_workdir / ".lingflow" / "M002-S01-PLAN.md"
        plan_file.write_text("""# S01: Slice Plan

## Tasks
- [ ] T01
- [ ] T02
""")
        result = executor._read_slice_plan(plan_file)
        assert result.milestone_id == "M002", (
            f"从 'M002-S01-PLAN.md' 提取的 milestone_id='{result.milestone_id}'，预期 'M002'"
        )

    def test_extracts_milestone_from_m003_variant(self, executor, temp_workdir):
        """文件名 M003-S02-PLAN.md → milestone_id='M003'"""
        plan_file = temp_workdir / ".lingflow" / "M003-S02-PLAN.md"
        plan_file.write_text("""# S02: Slice Plan

## Tasks
- [ ] T01
""")
        result = executor._read_slice_plan(plan_file)
        assert result.milestone_id == "M003"

    def test_fallback_to_m001_when_no_m_prefix(self, executor, temp_workdir):
        """文件名 S01-PLAN.md（无 M 前缀）→ fallback 到 'M001'"""
        plan_file = temp_workdir / ".lingflow" / "S01-PLAN.md"
        plan_file.write_text("""# S01: Slice Plan

## Tasks
- [ ] T01
""")
        result = executor._read_slice_plan(plan_file)
        assert result.milestone_id == "M001", (
            f"无 M 前缀时 fallback 值='{result.milestone_id}'，预期 'M001'"
        )

    def test_m999_large_number(self, executor, temp_workdir):
        """文件名 M999-S01-PLAN.md → milestone_id='M999'"""
        plan_file = temp_workdir / ".lingflow" / "M999-S01-PLAN.md"
        plan_file.write_text("""# S01: Slice Plan

## Tasks
- [ ] T01
""")
        result = executor._read_slice_plan(plan_file)
        assert result.milestone_id == "M999"

    def test_first_match_wins_when_multiple_m_numbers(self, executor, temp_workdir):
        """文件名 M003-S01-M001-PLAN.md → 应该取第一个 'M003'"""
        plan_file = temp_workdir / ".lingflow" / "M003-S01-M001-PLAN.md"
        plan_file.write_text("""# S01: Slice Plan

## Tasks
- [ ] T01
""")
        result = executor._read_slice_plan(plan_file)
        assert result.milestone_id == "M003"


# ============================================================
# Fix #5 (MINOR): import time 在模块顶层
# 修复前：import time 在 while 循环内部（每次迭代都执行）
# 修复后：import time 在文件顶部
# ============================================================

class TestFix5TimeImportAtModuleLevel:
    """修复 #5: import time 必须在模块顶层"""

    def test_time_is_module_level_import(self):
        """time 模块应该在 auto_executor 的顶层导入中"""
        import lingflow.workflow.auto_executor as mod

        assert hasattr(mod, "time"), "time 模块未在 auto_executor 顶层导入"
        assert mod.time is __import__("time"), "time 应该是标准库 time 模块"

    def test_no_import_inside_loop(self, temp_workdir):
        """检查源码中 while 循环内没有 import time"""
        import inspect
        source = inspect.getsource(AutoModeExecutor.run_auto_mode)

        lines = source.split("\n")
        in_while = False
        for line in lines:
            if "while" in line and ":" in line:
                in_while = True
            if in_while and "import time" in line and not line.strip().startswith("#"):
                pytest.fail(
                    "在 while 循环内发现 'import time'。"
                    "import 应该在模块顶层，不应在循环内部。"
                )


# ============================================================
# Fix #6 (MINOR): 状态文件路径无重复计算
# 与 Fix #2 相关：使用统一的 self.lingflow_dir / "STATE.md"
# ============================================================

class TestFix6StateFilePathConsistency:
    """修复 #6: 状态文件路径计算一致性"""

    def test_lingflow_dir_matches_state_machine(self, executor, temp_workdir):
        """executor.lingflow_dir 和 state_machine.lingflow_dir 应该指向同一位置"""
        assert executor.lingflow_dir == executor.state_machine.lingflow_dir

    def test_state_file_path_construction(self, executor, temp_workdir):
        """状态文件路径应该是 .lingflow/STATE.md"""
        expected = temp_workdir / ".lingflow" / "STATE.md"
        actual = executor.lingflow_dir / "STATE.md"
        assert actual == expected

    def test_state_machine_save_uses_correct_path(self, executor, temp_workdir):
        """AutoModeStateMachine.save_state() 创建的文件在 lingflow_dir/STATE.md"""
        executor.state_machine.start()

        state_file = temp_workdir / ".lingflow" / "STATE.md"
        assert state_file.exists(), "save_state() 应该在 lingflow_dir/STATE.md 创建文件"

        content = state_file.read_text()
        assert "```json" in content
        assert "session_id" in content


# ============================================================
# 集成验证：多修复联合测试
# ============================================================

class TestMultipleFixesIntegration:
    """验证多个修复在一起工作时不会互相干扰"""

    def test_full_execution_flow_with_failures(self, executor, temp_workdir):
        """完整执行流：包含任务失败 + 验证失败 + 最终报告

        验证 Fix #1（报告）、Fix #3（index 递增）的联合行为。
        """
        executor.state_machine.state.slice = SliceContext(
            slice_id="S01",
            milestone_id="M001",
            tasks=["T01", "T02"],
            current_task_index=0,
            completed_tasks=[],
            failed_tasks=[],
        )
        executor.state_machine.state.total_cost = 12.34
        executor.state_machine.state.total_tokens = 8000

        with patch.object(executor, "_execute_task_impl") as mock_impl:
            from lingflow.common.models import TaskResult

            mock_impl.return_value = TaskResult(
                task_id="T01", success=False, error="boom", execution_time=1.0
            )
            executor._execute_task()

        s = executor.state_machine.state.slice
        assert s.current_task_index == 1, "Fix #3: 失败后 index 应递增"
        assert "T01" in s.failed_tasks

        captured = io.StringIO()
        with patch("sys.stdout", captured):
            executor._print_final_report()

        assert "$12.34" in captured.getvalue(), "Fix #1: 报告应包含正确的 total_cost"
