"""Auto Mode 逃逸舱测试

测试逃逸舱的基本功能
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from lingflow.workflow.escape_hatch import AutoModeEscapeHatch
from lingflow.workflow.auto_mode import (
    AutoModeStateMachine,
    MilestoneContext,
    SliceContext,
    TaskContext,
    AutoModeState,
)


@pytest.fixture
def temp_workdir():
    """创建临时工作目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def state_machine(temp_workdir):
    """创建状态机实例"""
    return AutoModeStateMachine(str(temp_workdir))


@pytest.fixture
def escape_hatch(state_machine):
    """创建逃逸舱实例"""
    return AutoModeEscapeHatch(state_machine)


def test_escape_hatch_init(escape_hatch, state_machine):
    """测试逃逸舱初始化"""
    assert escape_hatch.state_machine == state_machine
    assert len(escape_hatch.actions) == 12


def test_find_action(escape_hatch):
    """测试查找操作"""
    # 测试查找存在的操作
    action = escape_hatch._find_action("1")
    assert action is not None
    assert action.key == "1"
    assert "查看当前状态" in action.description

    # 测试查找不存在的操作
    action = escape_hatch._find_action("99")
    assert action is None


def test_show_status(escape_hatch, state_machine):
    """测试显示状态"""
    # 设置一些状态
    state_machine.state.milestone = MilestoneContext(
        milestone_id="M001",
        title="Test Milestone",
        success_criteria=["A", "B"],
        slices=["S01", "S02"],
        current_slice_index=1,
    )

    state_machine.state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=["T01", "T02"],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    state_machine.state.task = TaskContext(
        task_id="T01",
        slice_id="S01",
        milestone_id="M001",
        plan="Test task",
        must_haves=["A"],
        summary="",
        execution_time=1.0,
        token_cost=100,
        retry_count=0,
    )

    # 使用 mock 来捕获 print 输出
    with patch('builtins.print') as mock_print:
        with patch('builtins.input', return_value=''):
            result = escape_hatch._show_status()

        # 检查是否调用了 print
        assert mock_print.called
        # 检查是否返回 None（继续暂停）
        assert result is None


def test_show_progress(escape_hatch, state_machine):
    """测试显示进度"""
    state_machine.state.milestone = MilestoneContext(
        milestone_id="M001",
        title="Test",
        success_criteria=[],
        slices=["S01", "S02"],
        current_slice_index=1,
    )

    state_machine.state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=["T01", "T02"],
        current_task_index=1,
        completed_tasks=["T01"],
        failed_tasks=[],
    )

    with patch('builtins.print') as mock_print:
        with patch('builtins.input', return_value=''):
            result = escape_hatch._show_progress()

        assert mock_print.called
        assert result is None


def test_show_plan(escape_hatch, state_machine, temp_workdir):
    """测试显示计划"""
    state_machine.state.milestone = MilestoneContext(
        milestone_id="M001",
        title="Test",
        success_criteria=[],
        slices=["S01"],
        current_slice_index=0,
    )

    state_machine.state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=[],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    state_machine.state.task = TaskContext(
        task_id="T01",
        slice_id="S01",
        milestone_id="M001",
        plan="Test",
        must_haves=[],
        summary="",
        execution_time=0,
        token_cost=0,
        retry_count=0,
    )

    # 创建计划文件
    lingflow_dir = temp_workdir / ".lingflow"
    lingflow_dir.mkdir(exist_ok=True)

    roadmap_file = lingflow_dir / "M001-ROADMAP.md"
    roadmap_file.write_text("# M001: Test Milestone\n\n## Success Criteria\n- Test")

    plan_file = lingflow_dir / "S01-PLAN.md"
    plan_file.write_text("# S01: Slice Plan\n\n## Tasks\n- T01")

    task_plan_file = lingflow_dir / "T01-PLAN.md"
    task_plan_file.write_text("# T01: Task Plan\n\n## Must-Haves\n- A")

    with patch('builtins.print') as mock_print:
        with patch('builtins.input', return_value=''):
            result = escape_hatch._show_plan()

        assert mock_print.called
        assert result is None


def test_resume_execution(escape_hatch):
    """测试继续执行"""
    result = escape_hatch._resume_execution()
    assert result is False  # False 表示退出逃逸舱，继续执行


def test_mark_task_complete(escape_hatch, state_machine):
    """测试标记任务完成"""
    state_machine.state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=["T01", "T02"],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    # 模拟用户确认
    with patch('builtins.input', return_value='y'):
        with patch('builtins.print'):
            result = escape_hatch._mark_task_complete()

    # 检查任务是否被标记为完成
    assert "T01" in state_machine.state.slice.completed_tasks
    assert state_machine.state.slice.current_task_index == 1
    assert result is None


def test_skip_current_task(escape_hatch, state_machine):
    """测试跳过任务"""
    state_machine.state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=["T01", "T02"],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    # 模拟用户确认
    with patch('builtins.input', return_value='y'):
        with patch('builtins.print'):
            result = escape_hatch._skip_current_task()

    # 检查任务是否被添加到失败列表
    assert "T01" in state_machine.state.slice.failed_tasks
    assert state_machine.state.slice.current_task_index == 1
    assert result is None


def test_revert_state_to_slice(escape_hatch, state_machine):
    """测试回退到 Slice 开始"""
    state_machine.state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=["T01", "T02"],
        current_task_index=2,
        completed_tasks=["T01"],
        failed_tasks=[],
    )

    state_machine.state.task = TaskContext(
        task_id="T02",
        slice_id="S01",
        milestone_id="M001",
        plan="Test",
        must_haves=[],
        summary="",
        execution_time=0,
        token_cost=0,
        retry_count=0,
    )

    # 模拟用户选择回退到 Slice 开始
    with patch('builtins.input', return_value='2'):
        result = escape_hatch._revert_state()

    # 检查状态是否重置
    assert state_machine.state.slice.current_task_index == 0
    assert len(state_machine.state.slice.completed_tasks) == 0
    assert state_machine.state.task is None
    assert state_machine.state.state == AutoModeState.EXECUTE
    assert result is None


def test_revert_state_cancel(escape_hatch, state_machine):
    """测试取消回退"""
    state_machine.state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=["T01"],
        current_task_index=1,
        completed_tasks=[],
        failed_tasks=[],
    )

    # 模拟用户选择取消
    with patch('builtins.input', return_value='3'):
        result = escape_hatch._revert_state()

    # 检查状态是否未改变
    assert state_machine.state.slice.current_task_index == 1
    assert result is None


def test_show_help(escape_hatch):
    """测试显示帮助"""
    with patch('builtins.print'):
        with patch('builtins.input', return_value=''):
            result = escape_hatch._show_help()

        assert result is None


def test_menu_display(escape_hatch):
    """测试菜单显示"""
    with patch('builtins.print') as mock_print:
        escape_hatch._print_menu()

        # 检查是否打印了菜单标题
        printed_texts = [str(call) for call in mock_print.call_args_list]
        menu_displayed = any("查看信息" in text for text in printed_texts)
        assert menu_displayed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
