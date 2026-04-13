"""Auto Mode 上下文预加载器测试

测试覆盖：
- PreInlinedContext 数据类
- 上下文收集（roadmap, slice, task summaries）
- 上下文注入到 skill params
- 上下文截断（大小控制）
- 集成流程
"""

import pytest
from pathlib import Path

from lingflow.workflow.auto_mode import (
    AutoModeStateMachine,
    MilestoneContext,
    SliceContext,
)
from lingflow.workflow.context_preloader import (
    ContextPreloader,
    PreInlinedContext,
    DEFAULT_MAX_CONTEXT_CHARS,
)


@pytest.fixture
def temp_workdir(tmp_path: Path):
    """临时工作目录"""
    yield tmp_path


@pytest.fixture
def state_machine(temp_workdir: Path):
    """状态机实例"""
    sm = AutoModeStateMachine(str(temp_workdir))
    sm.start()
    return sm


@pytest.fixture
def preloader(state_machine: AutoModeStateMachine):
    """上下文预加载器实例"""
    return ContextPreloader(state_machine)


def _setup_full_state(state_machine: AutoModeStateMachine, temp_workdir: Path):
    """设置完整的 milestone/slice/task 状态"""
    state = state_machine.state
    lingflow_dir = temp_workdir / ".lingflow"

    # 设置 milestone
    state.milestone = MilestoneContext(
        milestone_id="M001",
        title="Test Milestone",
        success_criteria=["Feature works"],
        slices=["S01", "S02"],
        current_slice_index=0,
    )

    # 设置 slice
    state.slice = SliceContext(
        slice_id="S01",
        milestone_id="M001",
        tasks=["T01", "T02", "T03"],
        current_task_index=1,
        completed_tasks=["T01"],
        failed_tasks=[],
    )

    # 写入 roadmap 文件
    roadmap = lingflow_dir / "M001-ROADMAP.md"
    roadmap.write_text("# M001 Roadmap\n\n## Summary\n\nBuild feature X\n", encoding="utf-8")

    # 写入 slice plan
    slice_plan = lingflow_dir / "S01-PLAN.md"
    slice_plan.write_text("# S01 Plan\n\nImplement slice 1\n", encoding="utf-8")

    # 写入已完成 task 的 summary
    t01_summary = lingflow_dir / "T01-SUMMARY.md"
    t01_summary.write_text("T01 completed successfully with output X", encoding="utf-8")

    # 写入当前 task plan
    t02_plan = lingflow_dir / "T02-PLAN.md"
    t02_plan.write_text("# T02 Plan\n\nSkill: code-review\n\nReview the code\n", encoding="utf-8")


class TestPreInlinedContext:
    """测试 PreInlinedContext 数据类"""

    def test_default_values(self):
        """测试默认值"""
        ctx = PreInlinedContext()
        assert ctx.roadmap_summary == ""
        assert ctx.slice_plan == ""
        assert ctx.task_plan == ""
        assert ctx.completed_tasks_summaries == []
        assert ctx.failed_tasks_info == []
        assert ctx.total_chars == 0
        assert ctx.truncated is False

    def test_to_dict(self):
        """测试转换为字典"""
        ctx = PreInlinedContext(
            milestone_id="M001",
            slice_id="S01",
            task_id="T02",
            current_task_index=1,
            total_tasks=3,
            completed_count=1,
            roadmap_summary="Build feature",
        )
        d = ctx.to_dict()

        assert d["milestone_id"] == "M001"
        assert d["slice_id"] == "S01"
        assert d["task_id"] == "T02"
        assert d["progress"] == "1/3"
        assert d["roadmap_summary"] == "Build feature"

    def test_to_prompt_prefix_basic(self):
        """测试生成上下文前缀"""
        ctx = PreInlinedContext(
            milestone_id="M001",
            slice_id="S01",
            task_id="T02",
            current_task_index=1,
            total_tasks=3,
            completed_count=1,
        )
        prefix = ctx.to_prompt_prefix()

        assert "[Milestone: M001]" in prefix
        assert "[Slice: S01" in prefix
        assert "[Current Task: T02]" in prefix

    def test_to_prompt_prefix_with_summaries(self):
        """测试包含已完成摘要的前缀"""
        ctx = PreInlinedContext(
            milestone_id="M001",
            slice_id="S01",
            task_id="T02",
            completed_tasks_summaries=[
                {"task_id": "T01", "summary": "Completed feature X"},
            ],
        )
        prefix = ctx.to_prompt_prefix()

        assert "Previously Completed" in prefix
        assert "T01" in prefix
        assert "Completed feature X" in prefix

    def test_to_prompt_prefix_with_failed(self):
        """测试包含失败信息的前缀"""
        ctx = PreInlinedContext(
            milestone_id="M001",
            failed_tasks_info=[
                {"task_id": "T01", "error": "ImportError: missing module"},
            ],
        )
        prefix = ctx.to_prompt_prefix()

        assert "Failed Tasks" in prefix
        assert "T01" in prefix

    def test_to_prompt_prefix_truncates_roadmap(self):
        """测试 roadmap 截断"""
        ctx = PreInlinedContext(
            roadmap_summary="x" * 3000,
        )
        prefix = ctx.to_prompt_prefix()

        assert len(ctx.roadmap_summary) == 3000
        # Should contain roadmap but truncated in prefix
        assert "roadmap truncated" in prefix


class TestContextPreloader:
    """测试 ContextPreloader"""

    def test_initialization(self, preloader: ContextPreloader):
        """测试初始化"""
        assert preloader.max_context_chars == DEFAULT_MAX_CONTEXT_CHARS
        assert preloader.lingflow_dir.exists()

    def test_preload_no_state(self, preloader: ContextPreloader):
        """测试无状态时的预加载"""
        ctx = preloader.preload_for_task("T01")

        assert ctx.task_id == "T01"
        assert ctx.roadmap_summary == ""
        assert ctx.slice_plan == ""
        assert ctx.completed_tasks_summaries == []

    def test_preload_full_state(self, state_machine: AutoModeStateMachine, temp_workdir: Path):
        """测试完整状态的预加载"""
        _setup_full_state(state_machine, temp_workdir)
        preloader = ContextPreloader(state_machine)

        ctx = preloader.preload_for_task("T02")

        assert ctx.milestone_id == "M001"
        assert ctx.slice_id == "S01"
        assert ctx.task_id == "T02"
        assert ctx.current_task_index == 1
        assert ctx.total_tasks == 3
        assert ctx.completed_count == 1
        assert "Build feature X" in ctx.roadmap_summary
        assert "Implement slice 1" in ctx.slice_plan
        assert "code-review" in ctx.task_plan
        assert len(ctx.completed_tasks_summaries) == 1
        assert ctx.completed_tasks_summaries[0]["task_id"] == "T01"

    def test_preload_with_failed_tasks(self, state_machine: AutoModeStateMachine, temp_workdir: Path):
        """测试包含失败 task 的预加载"""
        state = state_machine.state
        lingflow_dir = temp_workdir / ".lingflow"

        state.slice = SliceContext(
            slice_id="S01",
            milestone_id="M001",
            tasks=["T01", "T02"],
            current_task_index=1,
            completed_tasks=[],
            failed_tasks=["T01"],
        )

        t01_summary = lingflow_dir / "T01-SUMMARY.md"
        t01_summary.write_text("Task failed: import error", encoding="utf-8")

        preloader = ContextPreloader(state_machine)
        ctx = preloader.preload_for_task("T02")

        assert len(ctx.failed_tasks_info) == 1
        assert ctx.failed_tasks_info[0]["task_id"] == "T01"

    def test_inject_into_params(self, state_machine: AutoModeStateMachine, temp_workdir: Path):
        """测试注入上下文到 skill 参数"""
        _setup_full_state(state_machine, temp_workdir)
        preloader = ContextPreloader(state_machine)

        original_params = {"topic": "review code"}
        enriched = preloader.inject_into_params(original_params, "T02")

        # 原始参数保留
        assert enriched["topic"] == "review code"
        # 新增上下文
        assert "context" in enriched
        assert "auto_mode" in enriched
        assert enriched["task_id"] == "T02"
        assert "M001" in enriched["context"]

    def test_inject_does_not_overwrite(self, state_machine: AutoModeStateMachine, temp_workdir: Path):
        """测试注入不覆盖已有值"""
        _setup_full_state(state_machine, temp_workdir)
        preloader = ContextPreloader(state_machine)

        params = {"topic": "test", "context": "existing context", "task_id": "CUSTOM"}
        enriched = preloader.inject_into_params(params, "T02")

        # 已有值不应被覆盖
        assert enriched["context"] == "existing context"
        assert enriched["task_id"] == "CUSTOM"

    def test_truncation(self, state_machine: AutoModeStateMachine, temp_workdir: Path):
        """测试上下文截断"""
        state = state_machine.state
        lingflow_dir = temp_workdir / ".lingflow"

        # 设置一个有很多已完成 task 的 slice
        state.milestone = MilestoneContext(
            milestone_id="M001",
            title="Big",
            slices=["S01"],
        )
        state.slice = SliceContext(
            slice_id="S01",
            milestone_id="M001",
            tasks=["T01", "T02"],
            current_task_index=1,
            completed_tasks=[f"T{i:02d}" for i in range(1, 20)],
        )

        # 写入大 summary 文件
        for i in range(1, 20):
            f = lingflow_dir / f"T{i:02d}-SUMMARY.md"
            f.write_text("x" * 2000, encoding="utf-8")

        # 写入大 roadmap
        roadmap = lingflow_dir / "M001-ROADMAP.md"
        roadmap.write_text("R" * 10000, encoding="utf-8")

        # 小 max context 触发截断
        preloader = ContextPreloader(state_machine, max_context_chars=2000)
        ctx = preloader.preload_for_task("T02")

        assert ctx.truncated is True
        assert ctx.total_chars <= 2500  # 允许一些余量

    def test_load_roadmap_summary_with_summary_section(self, state_machine: AutoModeStateMachine, temp_workdir: Path):
        """测试从 roadmap 中提取 Summary 部分"""
        lingflow_dir = temp_workdir / ".lingflow"
        state = state_machine.state
        state.milestone = MilestoneContext(
            milestone_id="M001",
            title="Test",
        )

        roadmap = lingflow_dir / "M001-ROADMAP.md"
        roadmap.write_text(
            "# M001 Roadmap\n\n## Summary\n\nThis is the summary section.\n\n## Details\n\nMore details here.\n",
            encoding="utf-8",
        )

        preloader = ContextPreloader(state_machine)
        summary = preloader._load_roadmap_summary(state)

        assert "This is the summary section" in summary
        assert "More details" not in summary

    def test_load_roadmap_summary_no_section(self, state_machine: AutoModeStateMachine, temp_workdir: Path):
        """测试 roadmap 没有 Summary 部分时返回前3000字"""
        lingflow_dir = temp_workdir / ".lingflow"
        state = state_machine.state
        state.milestone = MilestoneContext(
            milestone_id="M001",
            title="Test",
        )

        roadmap = lingflow_dir / "M001-ROADMAP.md"
        roadmap.write_text("Just a plain roadmap without sections", encoding="utf-8")

        preloader = ContextPreloader(state_machine)
        summary = preloader._load_roadmap_summary(state)

        assert "plain roadmap" in summary

    def test_load_completed_summaries_no_files(self, state_machine: AutoModeStateMachine):
        """测试已完成 task 没有 summary 文件"""
        state = state_machine.state
        state.slice = SliceContext(
            slice_id="S01",
            milestone_id="M001",
            tasks=["T01"],
            completed_tasks=["T01"],
        )

        preloader = ContextPreloader(state_machine)
        summaries = preloader._load_completed_summaries(state)

        assert len(summaries) == 1
        assert "no summary file" in summaries[0]["summary"]


class TestIntegration:
    """集成测试"""

    def test_full_preload_flow(self, state_machine: AutoModeStateMachine, temp_workdir: Path):
        """测试完整的预加载流程"""
        _setup_full_state(state_machine, temp_workdir)
        preloader = ContextPreloader(state_machine)

        # 为 T02 预加载上下文
        ctx = preloader.preload_for_task("T02")

        # 验证所有部分
        assert ctx.milestone_id == "M001"
        assert ctx.slice_id == "S01"
        assert ctx.task_id == "T02"
        assert ctx.roadmap_summary != ""
        assert ctx.slice_plan != ""
        assert ctx.task_plan != ""
        assert len(ctx.completed_tasks_summaries) == 1

        # 注入到 params
        params = {"skill": "code-review"}
        enriched = preloader.inject_into_params(params, "T02")

        assert enriched["skill"] == "code-review"
        assert "context" in enriched
        assert "auto_mode" in enriched
        assert enriched["auto_mode"]["progress"] == "1/3"
