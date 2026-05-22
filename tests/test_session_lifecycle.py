"""会话生命周期管理器单元测试"""

import json

import pytest

from lingflow.context.session_lifecycle import (
    LifecyclePhase,
    LifecycleStatus,
    SessionLifecycleManager,
    SessionSummary,
)


class TestLifecyclePhase:
    def test_phase_values(self):
        assert LifecyclePhase.HEALTHY.value == "healthy"
        assert LifecyclePhase.WARNING.value == "warning"
        assert LifecyclePhase.CRITICAL.value == "critical"
        assert LifecyclePhase.EXPIRED.value == "expired"


class TestSessionLifecycleManager:
    def test_check_returns_healthy_below_warning(self):
        mgr = SessionLifecycleManager()
        status = mgr.check(100_000)
        assert status.phase == LifecyclePhase.HEALTHY

    def test_check_returns_warning_at_200k(self):
        mgr = SessionLifecycleManager()
        status = mgr.check(200_000)
        assert status.phase == LifecyclePhase.WARNING

    def test_check_returns_warning_above_200k(self):
        mgr = SessionLifecycleManager()
        status = mgr.check(250_000)
        assert status.phase == LifecyclePhase.WARNING

    def test_check_returns_expired_at_300k(self):
        mgr = SessionLifecycleManager()
        status = mgr.check(300_000)
        assert status.phase == LifecyclePhase.EXPIRED

    def test_check_returns_expired_above_300k(self):
        mgr = SessionLifecycleManager()
        status = mgr.check(500_000)
        assert status.phase == LifecyclePhase.EXPIRED

    def test_custom_thresholds(self):
        mgr = SessionLifecycleManager(warning_threshold=50_000, critical_threshold=100_000)
        assert mgr.check(30_000).phase == LifecyclePhase.HEALTHY
        assert mgr.check(60_000).phase == LifecyclePhase.WARNING
        assert mgr.check(120_000).phase == LifecyclePhase.EXPIRED

    def test_status_fields(self):
        mgr = SessionLifecycleManager()
        status = mgr.check(200_000)
        assert isinstance(status, LifecycleStatus)
        assert status.current_tokens == 200_000
        assert status.warning_threshold == 200_000
        assert status.critical_threshold == 300_000
        assert status.recommended_action == "prepare_handover"

    def test_expired_recommended_action(self):
        mgr = SessionLifecycleManager()
        status = mgr.check(300_000)
        assert status.recommended_action == "new_session"

    def test_status_to_dict(self):
        mgr = SessionLifecycleManager()
        status = mgr.check(200_000)
        d = status.to_dict()
        assert d["phase"] == "warning"
        assert d["current_tokens"] == 200_000
        assert "usage_percentage" in d

    def test_callback_triggers_on_phase_change(self):
        mgr = SessionLifecycleManager()
        triggered = []
        mgr.on_phase_change(LifecyclePhase.WARNING, lambda s: triggered.append(s.phase))
        mgr.check(200_000)
        assert len(triggered) == 1
        assert triggered[0] == LifecyclePhase.WARNING

    def test_callback_does_not_retrigger_same_phase(self):
        mgr = SessionLifecycleManager()
        triggered = []
        mgr.on_phase_change(LifecyclePhase.WARNING, lambda s: triggered.append(s.phase))
        mgr.check(200_000)
        mgr.check(210_000)
        assert len(triggered) == 1

    def test_callback_triggers_for_different_phases(self):
        mgr = SessionLifecycleManager()
        triggered = []
        mgr.on_phase_change(LifecyclePhase.WARNING, lambda s: triggered.append("warning"))
        mgr.on_phase_change(LifecyclePhase.EXPIRED, lambda s: triggered.append("expired"))
        mgr.check(200_000)
        mgr.check(300_000)
        assert triggered == ["warning", "expired"]

    def test_warnings_issued_count(self):
        mgr = SessionLifecycleManager()
        mgr.check(200_000)
        mgr.check(250_000)
        mgr.check(100_000)
        mgr.check(200_000)
        info = mgr.get_status()
        assert info["warnings_issued"] == 2


class TestSessionSummary:
    def test_create_summary(self):
        summary = SessionSummary(
            session_id="test-123",
            created_at="2026-01-01T00:00:00",
            ended_at="2026-01-01T01:00:00",
            total_tokens=250_000,
            total_messages=100,
            tasks_completed=["task1", "task2"],
            tasks_pending=["task3"],
            key_decisions=["decide X"],
            important_files={"/tmp/f.py": "test file"},
            next_steps=["do Y"],
            handover_reason="lifecycle_expired",
        )
        assert summary.session_id == "test-123"
        assert summary.total_tokens == 250_000
        assert len(summary.tasks_completed) == 2
        assert len(summary.tasks_pending) == 1

    def test_to_markdown(self):
        summary = SessionSummary(
            session_id="test-123",
            created_at="2026-01-01T00:00:00",
            ended_at="2026-01-01T01:00:00",
            total_tokens=250_000,
            total_messages=100,
            tasks_completed=["task1"],
            tasks_pending=["task2"],
            handover_reason="test",
        )
        md = summary.to_markdown()
        assert "# 会话交接摘要" in md
        assert "test-123" in md
        assert "✅ task1" in md
        assert "◻ task2" in md

    def test_to_dict_and_from_dict_roundtrip(self):
        summary = SessionSummary(
            session_id="test-456",
            created_at="2026-01-01T00:00:00",
            ended_at="2026-01-01T01:00:00",
            total_tokens=300_000,
            total_messages=200,
            tasks_completed=["a"],
            tasks_pending=["b"],
            key_decisions=["c"],
            important_files={"/f.py": "desc"},
            next_steps=["d"],
            handover_reason="expired",
        )
        d = summary.to_dict()
        restored = SessionSummary.from_dict(d)
        assert restored.session_id == summary.session_id
        assert restored.total_tokens == summary.total_tokens
        assert restored.tasks_completed == summary.tasks_completed
        assert restored.tasks_pending == summary.tasks_pending

    def test_from_dict_ignores_extra_keys(self):
        d = {
            "session_id": "x",
            "extra_field": "ignore",
            "total_tokens": 0,
            "total_messages": 0,
            "created_at": "",
            "ended_at": "",
        }
        summary = SessionSummary.from_dict(d)
        assert summary.session_id == "x"


class TestSaveAndLoad:
    def test_save_session_summary(self, tmp_path):
        mgr = SessionLifecycleManager(storage_dir=tmp_path)
        summary = SessionSummary(
            session_id="save-test",
            created_at="2026-01-01T00:00:00",
            ended_at="2026-01-01T01:00:00",
            total_tokens=300_000,
            total_messages=150,
            tasks_completed=["task1"],
            tasks_pending=["task2"],
            handover_reason="lifecycle_expired",
        )
        path = mgr.save_session_summary(summary)
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["session_id"] == "save-test"

        md_path = tmp_path / "SESSION_HANDOVER.md"
        assert md_path.exists()
        assert "save-test" in md_path.read_text(encoding="utf-8")

    def test_load_last_session_summary(self, tmp_path):
        mgr = SessionLifecycleManager(storage_dir=tmp_path)
        summary = SessionSummary(
            session_id="load-test",
            created_at="2026-01-01T00:00:00",
            ended_at="2026-01-01T01:00:00",
            total_tokens=300_000,
            total_messages=100,
            handover_reason="test",
        )
        mgr.save_session_summary(summary)
        loaded = mgr.load_last_session_summary()
        assert loaded is not None
        assert loaded.session_id == "load-test"
        assert loaded.total_tokens == 300_000

    def test_load_returns_none_when_no_summary(self, tmp_path):
        mgr = SessionLifecycleManager(storage_dir=tmp_path)
        assert mgr.load_last_session_summary() is None

    def test_save_without_storage_dir_raises(self):
        mgr = SessionLifecycleManager(storage_dir=None)
        summary = SessionSummary(
            session_id="err",
            created_at="",
            ended_at="",
            total_tokens=0,
            total_messages=0,
        )
        with pytest.raises(ValueError, match="storage_dir"):
            mgr.save_session_summary(summary)

    def test_load_without_storage_dir_returns_none(self):
        mgr = SessionLifecycleManager(storage_dir=None)
        assert mgr.load_last_session_summary() is None


class TestHandoffInstructions:
    def test_generate_handover_instructions(self):
        mgr = SessionLifecycleManager()
        summary = SessionSummary(
            session_id="handover-test",
            created_at="2026-01-01T00:00:00",
            ended_at="2026-01-01T01:00:00",
            total_tokens=300_000,
            total_messages=100,
            tasks_pending=["finish feature"],
            next_steps=["write tests", "deploy"],
            key_decisions=["use async"],
            handover_reason="expired",
        )
        instructions = mgr.get_handover_instructions(summary)
        assert "handover-test" in instructions
        assert "finish feature" in instructions
        assert "write tests" in instructions
        assert "use async" in instructions


class TestManagerViaCreateSessionSummary:
    def test_create_session_summary_method(self):
        mgr = SessionLifecycleManager()
        summary = mgr.create_session_summary(
            session_id="create-test",
            total_tokens=250_000,
            total_messages=120,
            tasks_completed=["task A"],
            tasks_pending=["task B"],
            key_decisions=["decided X"],
            important_files={"/path/to/file.py": "main module"},
            next_steps=["do next"],
            handover_reason="lifecycle_expired",
        )
        assert summary.session_id == "create-test"
        assert summary.total_tokens == 250_000
        assert summary.tasks_completed == ["task A"]
        assert summary.tasks_pending == ["task B"]
        assert summary.ended_at  # should be set


class TestManagerStatus:
    def test_get_status(self):
        mgr = SessionLifecycleManager()
        status = mgr.get_status()
        assert status["warning_threshold"] == 200_000
        assert status["critical_threshold"] == 300_000
        assert status["current_phase"] == "healthy"
        assert status["warnings_issued"] == 0
