"""Auto Mode 执行器集成测试

测试状态机和执行器的基本功能
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from lingflow.workflow.auto_executor import AutoModeExecutor
from lingflow.coordination.coordinator import AgentCoordinator


@pytest.fixture
def temp_workdir():
    """创建临时工作目录"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def coordinator():
    """创建 coordinator 实例"""
    return AgentCoordinator()


@pytest.fixture
def executor(coordinator, temp_workdir):
    """创建 AutoModeExecutor 实例"""
    return AutoModeExecutor(coordinator, str(temp_workdir))


def test_executor_init(executor, temp_workdir):
    """测试 executor 初始化"""
    assert executor.workdir == temp_workdir
    assert executor.lingflow_dir == temp_workdir / ".lingflow"
    assert executor.lingflow_dir.exists()
    assert executor.state_machine is not None


def test_parse_task_plan(executor):
    """测试 task plan 解析"""
    plan_content = """# T01: Task Plan

Skill: workflow-executor

## Must-Haves
- Task completes successfully
- Code is committed

## Implementation Notes
Implement feature X with Y approach
"""

    skill_name, params = executor._parse_task_plan(plan_content, "T01")

    assert skill_name == "workflow-executor"
    assert params["task_id"] == "T01"
    assert "notes" in params
    assert "Implement feature X" in params["notes"]


def test_parse_task_plan_default_skill(executor):
    """测试默认技能解析"""
    plan_content = """# T02: Task Plan

## Must-Haves
- Task completes successfully

## Implementation Notes
Simple task
"""

    skill_name, params = executor._parse_task_plan(plan_content, "T02")

    assert skill_name == "workflow-executor"
    assert params["task_id"] == "T02"


def test_read_roadmap(executor, temp_workdir):
    """测试 roadmap 文件读取"""
    roadmap_file = temp_workdir / ".lingflow" / "M001-ROADMAP.md"
    roadmap_file.write_text("""# M001: Test Milestone

## Success Criteria
- [x] Feature A working
- [ ] Feature B working
- [ ] Feature C working

## Slices
- [x] S01
- [ ] S02
- [ ] S03
""")

    milestone = executor._read_roadmap(roadmap_file)

    assert milestone.milestone_id == "M001"
    assert milestone.title == "Test Milestone"
    assert len(milestone.success_criteria) == 3
    assert "Feature A working" in milestone.success_criteria
    assert len(milestone.slices) == 3
    assert "S01" in milestone.slices
    assert milestone.current_slice_index == 1  # S01 is marked complete


def test_read_slice_plan(executor, temp_workdir):
    """测试 slice plan 文件读取"""
    plan_file = temp_workdir / ".lingflow" / "S01-PLAN.md"
    plan_file.write_text("""# S01: Slice Plan

## Tasks
- [x] T01
- [ ] T02
- [ ] T03
""")

    slice_ctx = executor._read_slice_plan(plan_file)

    assert slice_ctx.slice_id == "S01"
    assert len(slice_ctx.tasks) == 3
    assert "T01" in slice_ctx.tasks
    assert "T02" in slice_ctx.tasks
    assert "T03" in slice_ctx.tasks
    assert len(slice_ctx.completed_tasks) == 1
    assert "T01" in slice_ctx.completed_tasks
    assert slice_ctx.current_task_index == 1


def test_create_default_tasks(executor):
    """测试默认 tasks 创建"""
    from lingflow.workflow.auto_mode import SliceContext

    slice_ctx = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=[],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    tasks = executor._create_default_tasks(slice_ctx, 3)

    assert len(tasks) == 3
    assert tasks[0].task_id == "T01"
    assert tasks[1].task_id == "T02"
    assert tasks[2].task_id == "T03"
    assert all(t.slice_id == "S01" for t in tasks)
    assert all(t.milestone_id == "M001" for t in tasks)


def test_parse_brainstorming_result_dict(executor):
    """测试解析 brainstorming 字典结果"""
    from lingflow.workflow.auto_mode import SliceContext

    slice_ctx = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=[],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    result = {
        "tasks": [
            {"title": "Task 1", "description": "Implement feature A", "must_haves": ["A works"]},
            {"title": "Task 2", "description": "Implement feature B", "must_haves": ["B works"]},
        ]
    }

    tasks = executor._parse_brainstorming_result(result, slice_ctx)

    assert len(tasks) == 2
    assert tasks[0].task_id == "T01"
    assert tasks[1].task_id == "T02"
    assert "feature A" in tasks[0].plan
    assert "A works" in tasks[0].must_haves


def test_parse_brainstorming_result_list(executor):
    """测试解析 brainstorming 列表结果"""
    from lingflow.workflow.auto_mode import SliceContext

    slice_ctx = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=[],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    result = [
        "Implement feature A",
        "Implement feature B",
        "Implement feature C",
    ]

    tasks = executor._parse_brainstorming_result(result, slice_ctx)

    assert len(tasks) == 3
    assert tasks[0].task_id == "T01"
    assert "feature A" in tasks[0].plan


def test_parse_brainstorming_result_empty(executor):
    """测试解析空 brainstorming 结果"""
    from lingflow.workflow.auto_mode import SliceContext

    slice_ctx = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=[],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    tasks = executor._parse_brainstorming_result({}, slice_ctx)
    assert len(tasks) == 0

    tasks = executor._parse_brainstorming_result([], slice_ctx)
    assert len(tasks) == 0


def test_write_roadmap(executor, temp_workdir):
    """测试写入 roadmap 文件"""
    from lingflow.workflow.auto_mode import MilestoneContext

    # 设置 milestone
    executor.state_machine.state.milestone = MilestoneContext(
        milestone_id="M001",
        title="Test Milestone",
        success_criteria=["Feature A", "Feature B"],
        slices=["S01", "S02", "S03"],
        current_slice_index=1,
    )

    executor._write_roadmap()

    roadmap_file = temp_workdir / ".lingflow" / "M001-ROADMAP.md"
    assert roadmap_file.exists()

    content = roadmap_file.read_text(encoding="utf-8")
    assert "# M001: Test Milestone" in content
    assert "## Success Criteria" in content
    assert "## Slices" in content
    assert "- [x] S01" in content  # current_slice_index=1，所以 S01 应该标记为完成
    assert "- [ ] S02" in content


def test_write_slice_plan(executor, temp_workdir):
    """测试写入 slice plan 文件"""
    from lingflow.workflow.auto_mode import SliceContext

    # 设置 slice
    executor.state_machine.state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=["T01", "T02", "T03"],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    executor._write_slice_plan()

    plan_file = temp_workdir / ".lingflow" / "S01-PLAN.md"
    assert plan_file.exists()

    content = plan_file.read_text(encoding="utf-8")
    assert "# S01: Slice Plan" in content
    assert "## Tasks" in content
    assert "- [ ] T01" in content


def test_write_task_plan(executor, temp_workdir):
    """测试写入 task plan 文件"""
    from lingflow.workflow.auto_mode import SliceContext

    # 设置 slice
    executor.state_machine.state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=["T01", "T02"],
        current_task_index=0,
        completed_tasks=[],
        failed_tasks=[],
    )

    executor._write_task_plan("T01")

    plan_file = temp_workdir / ".lingflow" / "T01-PLAN.md"
    assert plan_file.exists()

    content = plan_file.read_text(encoding="utf-8")
    assert "# T01: Task Plan" in content
    assert "## Must-Haves" in content
    assert "## Implementation Notes" in content


def test_execute_task_impl_missing_plan(executor, temp_workdir):
    """测试执行任务时 plan 文件不存在"""
    result = executor._execute_task_impl("T99")

    assert result.success is False
    assert "Task plan not found" in result.error


def test_state_persistence(executor, temp_workdir):
    """测试状态持久化"""
    # 手动启动状态机
    executor.state_machine.start()

    # 检查 STATE.md 文件是否创建
    state_file = temp_workdir / ".lingflow" / "STATE.md"
    assert state_file.exists()

    content = state_file.read_text(encoding="utf-8")
    assert "session_id" in content
    assert "state" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
