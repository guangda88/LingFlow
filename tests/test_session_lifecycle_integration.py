"""会话生命周期集成测试

验证 ContextManager 与 SessionLifecycleManager 的完整过渡闭环：
  检测(WARNING) → 预警(logging) → 过渡(transition) → 新会话加载(previous summary)
"""

import json
import logging

import pytest

from lingflow.context.manager import ContextManager


@pytest.fixture
def storage(tmp_path):
    """隔离的存储目录"""
    return tmp_path / "ctx"


class TestLifecycleTransition:
    """测试会话过渡的完整闭环"""

    def test_transition_resets_session_id(self, storage):
        """过渡后 session_id 变化"""
        mgr = ContextManager(storage_dir=str(storage))
        old_session_id = mgr.session_id

        mgr._cumulative_tokens = 350_000
        mgr._check_lifecycle()

        assert mgr.session_id != old_session_id

    def test_transition_resets_counters(self, storage):
        """过渡后所有计数器归零"""
        mgr = ContextManager(storage_dir=str(storage))
        mgr.message_count = 100
        mgr._cumulative_tokens = 350_000
        mgr.estimated_tokens = 50_000

        mgr._check_lifecycle()

        assert mgr.message_count == 0
        assert mgr._cumulative_tokens == 0
        assert mgr.estimated_tokens == 0

    def test_transition_preserves_pending_tasks(self, storage):
        """过渡后待完成任务保留到新快照"""
        mgr = ContextManager(storage_dir=str(storage))
        mgr.snapshot.tasks_pending = ["write tests", "deploy"]
        mgr.snapshot.key_decisions = ["use async"]
        mgr.snapshot.next_steps = ["review PR"]
        mgr._cumulative_tokens = 350_000

        mgr._check_lifecycle()

        assert mgr.snapshot.tasks_pending == ["write tests", "deploy"]
        assert mgr.snapshot.key_decisions == ["use async"]
        assert mgr.snapshot.next_steps == ["review PR"]

    def test_transition_clears_messages(self, storage):
        """过渡后消息列表清空"""
        mgr = ContextManager(storage_dir=str(storage))
        mgr._messages = [{"role": "user", "content": "hello"}] * 50
        mgr._cumulative_tokens = 350_000

        mgr._check_lifecycle()

        assert mgr._messages == []

    def test_transition_resets_lazy_managers(self, storage):
        """过渡后懒加载管理器重置为 None"""
        mgr = ContextManager(storage_dir=str(storage))
        # 先触发懒加载创建，然后验证过渡后重置
        mgr._budget_manager = object()
        mgr._cumulative_tokens = 350_000
        # _lifecycle_manager 由 _check_lifecycle 懒加载
        mgr._check_lifecycle()

        assert mgr._budget_manager is None
        assert mgr._lifecycle_manager is None

    def test_transition_creates_artifacts(self, storage):
        """过渡后创建所有磁盘文件"""
        mgr = ContextManager(storage_dir=str(storage))
        mgr.add_task("task A")
        mgr.complete_task("task A")
        mgr.add_task("task B")
        mgr.add_decision("use PostgreSQL")
        mgr.set_next_steps(["write migration"])
        mgr._cumulative_tokens = 350_000

        mgr._check_lifecycle()

        assert (storage / "SESSION_HANDOVER.md").exists()
        assert (storage / "SESSION_HANDOVER_INSTRUCTIONS.md").exists()
        assert (storage / "HANDOVER.md").exists()
        assert (storage / "handover.json").exists()

        lifecycle_files = list(storage.glob("lifecycle_*.json"))
        assert len(lifecycle_files) >= 1

    def test_transition_summary_content(self, storage):
        """过渡后摘要文件内容正确"""
        mgr = ContextManager(storage_dir=str(storage))
        mgr.add_task("pending task")
        mgr.add_decision("key decision X")
        mgr._cumulative_tokens = 350_000

        mgr._check_lifecycle()

        md = (storage / "SESSION_HANDOVER.md").read_text(encoding="utf-8")
        assert "pending task" in md
        assert "key decision X" in md

        instructions = (storage / "SESSION_HANDOVER_INSTRUCTIONS.md").read_text(encoding="utf-8")
        assert "pending task" in instructions
        assert "key decision X" in instructions

    def test_transition_context_summary_has_prefix(self, storage):
        """过渡后新快照的 context_summary 包含来源标记"""
        mgr = ContextManager(storage_dir=str(storage))
        old_id = mgr.session_id
        mgr._cumulative_tokens = 350_000

        mgr._check_lifecycle()

        assert old_id in mgr.snapshot.context_summary
        assert "从会话" in mgr.snapshot.context_summary

    def test_transition_does_not_retrigger(self, storage):
        """过渡后再次 check_lifecycle 不会无限循环"""
        mgr = ContextManager(storage_dir=str(storage))
        mgr._cumulative_tokens = 350_000
        mgr._check_lifecycle()

        session_after_first = mgr.session_id

        mgr._check_lifecycle()

        assert mgr.session_id == session_after_first

    def test_transition_new_session_can_record_messages(self, storage):
        """过渡后新会话可以正常记录消息"""
        mgr = ContextManager(storage_dir=str(storage))
        mgr._cumulative_tokens = 350_000
        mgr._check_lifecycle()

        mgr.record_message("user", "hello after transition")
        mgr.record_message("assistant", "response after transition")

        assert mgr.message_count == 2
        assert mgr._cumulative_tokens > 0
        assert len(mgr._messages) == 2


class TestPreviousSessionLoading:
    """测试新 ContextManager 加载上一会话摘要"""

    def _create_transitioned_session(self, storage):
        """辅助：创建一个已完成过渡的会话"""
        mgr = ContextManager(storage_dir=str(storage))
        mgr.add_task("carry-over task")
        mgr.add_decision("carry-over decision")
        mgr.set_next_steps(["step 1", "step 2"])
        mgr._cumulative_tokens = 350_000
        mgr._check_lifecycle()
        return mgr

    def test_new_manager_loads_previous_summary(self, storage):
        """新 ContextManager 创建时自动加载上一会话摘要"""
        self._create_transitioned_session(storage)

        new_mgr = ContextManager(storage_dir=str(storage))

        assert new_mgr._previous_session is not None
        assert new_mgr._previous_session.handover_reason == "lifecycle_expired"

    def test_new_manager_injects_pending_tasks(self, storage):
        """上一会话的待完成任务被注入到新会话"""
        self._create_transitioned_session(storage)

        new_mgr = ContextManager(storage_dir=str(storage))

        assert "carry-over task" in new_mgr.snapshot.tasks_pending

    def test_new_manager_injects_decisions(self, storage):
        """上一会话的关键决策被注入到新会话"""
        self._create_transitioned_session(storage)

        new_mgr = ContextManager(storage_dir=str(storage))

        assert "carry-over decision" in new_mgr.snapshot.key_decisions

    def test_new_manager_injects_next_steps(self, storage):
        """上一会话的下一步被注入到新会话"""
        self._create_transitioned_session(storage)

        new_mgr = ContextManager(storage_dir=str(storage))

        assert new_mgr.snapshot.next_steps == ["step 1", "step 2"]

    def test_new_manager_context_summary_has_prefix(self, storage):
        """新会话的 context_summary 包含接续标记"""
        self._create_transitioned_session(storage)

        new_mgr = ContextManager(storage_dir=str(storage))

        assert "从会话" in new_mgr.snapshot.context_summary

    def test_no_previous_summary_returns_none(self, storage):
        """没有上一会话摘要时返回 None"""
        mgr = ContextManager(storage_dir=str(storage))

        assert mgr._previous_session is None

    def test_new_manager_cumulative_starts_at_zero(self, storage):
        """新会话的累积 token 从零开始"""
        self._create_transitioned_session(storage)

        new_mgr = ContextManager(storage_dir=str(storage))

        assert new_mgr._cumulative_tokens == 0


class TestWarningPhase:
    """测试 WARNING 阶段的预警"""

    def test_warning_logged(self, storage, caplog):
        """到达 20 万 token 时记录 WARNING 日志"""
        mgr = ContextManager(storage_dir=str(storage))

        with caplog.at_level(logging.WARNING, logger="lingflow.context.manager"):
            mgr._cumulative_tokens = 210_000
            mgr._check_lifecycle()

        assert any("生命周期预警" in r.message for r in caplog.records)

    def test_warning_does_not_trigger_transition(self, storage):
        """WARNING 阶段不触发过渡"""
        mgr = ContextManager(storage_dir=str(storage))
        old_session = mgr.session_id

        mgr._cumulative_tokens = 210_000
        mgr._check_lifecycle()

        assert mgr.session_id == old_session

    def test_warning_count_in_get_status(self, storage):
        """WARNING 后 get_status 包含 lifecycle 信息"""
        mgr = ContextManager(storage_dir=str(storage))
        mgr._cumulative_tokens = 210_000
        mgr._check_lifecycle()

        status = mgr.get_status()
        assert "cumulative_tokens" in status
        assert status["cumulative_tokens"] == 210_000


class TestFullCycleIntegration:
    """端到端：创建 → 积累 → 过渡 → 新会话 → 继续工作"""

    def test_full_lifecycle_cycle(self, storage):
        """完整的生命周期闭环"""
        # 1. 初始会话
        mgr = ContextManager(storage_dir=str(storage))
        first_session_id = mgr.session_id

        mgr.add_task("task alpha")
        mgr.add_task("task beta")
        mgr.complete_task("task alpha")
        mgr.add_decision("use SQLite")
        mgr.set_next_steps(["write tests", "deploy"])

        # 2. 强制过渡
        mgr._cumulative_tokens = 350_000
        mgr._check_lifecycle()

        second_session_id = mgr.session_id
        assert second_session_id != first_session_id
        assert mgr._cumulative_tokens == 0
        assert mgr.message_count == 0

        # 3. 过渡后状态保留
        assert "task beta" in mgr.snapshot.tasks_pending
        assert "task alpha" not in mgr.snapshot.tasks_pending
        assert "use SQLite" in mgr.snapshot.key_decisions
        assert mgr.snapshot.next_steps == ["write tests", "deploy"]

        # 4. 新会话可以正常工作
        mgr.record_message("user", "continue working")
        mgr.complete_task("task beta")

        assert mgr.message_count == 1
        assert "task beta" not in mgr.snapshot.tasks_pending
        assert "task beta" in mgr.snapshot.tasks_completed

        # 5. 保存新快照
        mgr._save_snapshot()
        snapshot_file = storage / f"{mgr.session_id}.json"
        assert snapshot_file.exists()

        data = json.loads(snapshot_file.read_text(encoding="utf-8"))
        assert "task beta" in data["tasks_completed"]

    def test_two_transitions_preserve_chain(self, storage):
        """连续两次过渡：信息链不断裂"""
        # 第一次过渡
        mgr = ContextManager(storage_dir=str(storage))
        mgr.add_task("original task")
        mgr.add_decision("original decision")
        mgr._cumulative_tokens = 350_000
        mgr._check_lifecycle()
        second_id = mgr.session_id

        # 第二次过渡
        mgr.add_task("second task")
        mgr._cumulative_tokens = 350_000
        mgr._check_lifecycle()
        third_id = mgr.session_id

        assert third_id != second_id

        # 第二次过渡后：两次的任务都在
        assert "original task" in mgr.snapshot.tasks_pending
        assert "second task" in mgr.snapshot.tasks_pending
        assert "original decision" in mgr.snapshot.key_decisions

    def test_new_context_manager_continues_chain(self, storage):
        """过渡后创建全新 ContextManager 能接续工作"""
        # 原始会话
        mgr = ContextManager(storage_dir=str(storage))
        mgr.add_task("persistent task")
        mgr.add_decision("persistent decision")
        mgr._cumulative_tokens = 350_000
        mgr._check_lifecycle()
        mgr._save_snapshot()

        # 全新的 ContextManager
        mgr2 = ContextManager(storage_dir=str(storage))

        assert mgr2._previous_session is not None
        assert "persistent task" in mgr2.snapshot.tasks_pending
        assert "persistent decision" in mgr2.snapshot.key_decisions

        mgr2.record_message("user", "resuming work")
        assert mgr2.message_count == 1
        assert mgr2._cumulative_tokens > 0
