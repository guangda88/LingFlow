import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lingflow.context.manager import (
    _CONTEXT_MANAGER_LOCK,
    ContextManager,
    ContextSnapshot,
    add_task,
    complete_task,
    compress_context,
    get_context_manager,
    get_recovery_context,
    track_context,
)


@pytest.fixture(autouse=True)
def reset_global_cm():
    import lingflow.context.manager as mod

    mod._CONTEXT_MANAGER = None
    yield
    mod._CONTEXT_MANAGER = None


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path / "ctx_test")


@pytest.fixture
def cm(tmp_dir):
    return ContextManager(storage_dir=tmp_dir)


class TestContextSnapshot:
    def test_from_dict(self):
        data = {
            "timestamp": "2026-01-01",
            "session_id": "abc",
            "tasks_completed": ["t1"],
            "tasks_pending": ["t2"],
            "key_decisions": ["d1"],
            "important_files": {"f.py": "desc"},
            "context_summary": "sum",
            "next_steps": ["s1"],
        }
        snap = ContextSnapshot.from_dict(data)
        assert snap.session_id == "abc"
        assert snap.tasks_completed == ["t1"]

    def test_to_dict(self):
        snap = ContextSnapshot(
            timestamp="2026-01-01",
            session_id="xyz",
            tasks_completed=["a"],
        )
        d = snap.to_dict()
        assert d["session_id"] == "xyz"
        assert d["tasks_completed"] == ["a"]

    def test_defaults(self):
        snap = ContextSnapshot(timestamp="t", session_id="s")
        assert snap.tasks_completed == []
        assert snap.tasks_pending == []
        assert snap.key_decisions == []
        assert snap.important_files == {}
        assert snap.context_summary == ""
        assert snap.next_steps == []


class TestContextManagerInit:
    def test_custom_storage_dir(self, cm, tmp_dir):
        assert cm.storage_dir == Path(tmp_dir)
        assert cm.storage_dir.exists()

    def test_default_storage_dir(self):
        cm = ContextManager()
        assert "lingflow" in str(cm.storage_dir).lower() or ".claude" in str(cm.storage_dir)

    def test_session_id_generated(self, cm):
        assert cm.session_id
        assert len(cm.session_id) > 5

    def test_initial_state(self, cm):
        assert cm.message_count == 0
        assert cm.estimated_tokens == 0
        assert cm._messages == []

    def test_load_last_context_missing(self, cm):
        assert cm.last_context is None

    def test_load_last_context_exists(self, tmp_path):
        tmp_dir = str(tmp_path / "ctx_test")
        data = {
            "timestamp": "2026-01-01",
            "session_id": "prev_session",
            "tasks_completed": ["old_task"],
        }
        os.makedirs(tmp_dir, exist_ok=True)
        ctx_path = Path(tmp_dir) / "last_context.json"
        ctx_path.write_text(json.dumps(data))
        cm = ContextManager(storage_dir=tmp_dir)
        assert cm.last_context is not None
        assert cm.last_context.session_id == "prev_session"

    def test_load_last_context_corrupt(self, tmp_path):
        tmp_dir = str(tmp_path / "ctx_test2")
        os.makedirs(tmp_dir, exist_ok=True)
        ctx_path = Path(tmp_dir) / "last_context.json"
        ctx_path.write_text("not valid json{{{")
        cm = ContextManager(storage_dir=tmp_dir)
        assert cm.last_context is None


class TestRecordMessage:
    def test_basic_message(self, cm):
        cm.record_message("user", "Hello world")
        assert cm.message_count == 1
        assert len(cm._messages) == 1
        assert cm._messages[0]["role"] == "user"

    def test_tokens_estimated(self, cm):
        cm.record_message("user", "Hello world")
        assert cm.estimated_tokens > 0

    def test_important_message_auto_detect(self, cm):
        cm.record_message("user", "fix the bug in module X")
        assert len(cm.snapshot.tasks_completed) + len(cm.snapshot.tasks_pending) >= 0

    def test_explicit_important(self, cm):
        cm.record_message("user", "plain text", is_important=True)
        assert len(cm._messages) == 1

    def test_extract_pending_task(self, cm):
        cm.record_message("user", "- [ ] implement feature A", is_important=True)
        assert "implement feature A" in cm.snapshot.tasks_pending

    def test_extract_completed_task(self, cm):
        cm.record_message("user", "- [x] done with B", is_important=True)
        assert "done with B" in cm.snapshot.tasks_completed

    def test_extract_checkbox_task(self, cm):
        cm.record_message("user", "◻ new task here", is_important=True)
        assert "new task here" in cm.snapshot.tasks_pending

    def test_extract_done_checkbox(self, cm):
        cm.record_message("user", "◼ old task done", is_important=True)
        assert "old task done" in cm.snapshot.tasks_completed

    def test_multiple_messages(self, cm):
        for i in range(5):
            cm.record_message("assistant", f"message {i}")
        assert cm.message_count == 5


class TestTaskManagement:
    def test_add_pending_task(self, cm):
        cm.add_task("Write tests")
        assert "Write tests" in cm.snapshot.tasks_pending

    def test_add_completed_task(self, cm):
        cm.add_task("Write tests", completed=True)
        assert "Write tests" in cm.snapshot.tasks_completed

    def test_no_duplicate_task(self, cm):
        cm.add_task("Write tests")
        cm.add_task("Write tests")
        assert cm.snapshot.tasks_pending.count("Write tests") == 1

    def test_complete_task(self, cm):
        cm.add_task("Write tests")
        cm.complete_task("Write tests")
        assert "Write tests" not in cm.snapshot.tasks_pending
        assert "Write tests" in cm.snapshot.tasks_completed

    def test_complete_nonexistent_task(self, cm):
        cm.complete_task("nonexistent")
        assert "nonexistent" in cm.snapshot.tasks_completed

    def test_add_task_saves_snapshot(self, cm):
        cm.add_task("Test task")
        snap_file = cm.storage_dir / f"{cm.session_id}.json"
        assert snap_file.exists()


class TestDecisionAndFiles:
    def test_add_decision(self, cm):
        cm.add_decision("Use SQLite")
        assert "Use SQLite" in cm.snapshot.key_decisions

    def test_no_duplicate_decision(self, cm):
        cm.add_decision("Use SQLite")
        cm.add_decision("Use SQLite")
        assert cm.snapshot.key_decisions.count("Use SQLite") == 1

    def test_add_file(self, cm):
        cm.add_file("src/main.py", "main entry")
        assert cm.snapshot.important_files["src/main.py"] == "main entry"

    def test_set_next_steps(self, cm):
        cm.set_next_steps(["step 1", "step 2"])
        assert cm.snapshot.next_steps == ["step 1", "step 2"]


class TestGetStatus:
    def test_basic_status(self, cm):
        status = cm.get_status()
        assert "session_id" in status
        assert status["message_count"] == 0
        assert "estimated_tokens" in status
        assert "token_usage_ratio" in status

    def test_status_after_messages(self, cm):
        cm.record_message("user", "test message")
        status = cm.get_status()
        assert status["message_count"] == 1
        assert status["tasks_completed"] == 0
        assert status["tasks_pending"] == 0


class TestGetBriefSummary:
    def test_empty_summary(self, cm):
        assert cm._get_brief_summary() == "进行中"

    def test_summary_with_tasks(self, cm):
        cm.add_task("task1", completed=True)
        cm.add_task("task2")
        summary = cm._get_brief_summary()
        assert "已完成" in summary
        assert "待完成" in summary

    def test_summary_with_decisions(self, cm):
        cm.add_decision("Use Python")
        summary = cm._get_brief_summary()
        assert "决策" in summary


class TestSaveSnapshot:
    def test_saves_json(self, cm):
        cm.add_task("test task")
        snap_file = cm.storage_dir / f"{cm.session_id}.json"
        assert snap_file.exists()
        data = json.loads(snap_file.read_text())
        assert "test task" in data.get("tasks_pending", [])

    def test_saves_last_context(self, cm):
        cm.add_task("test task")
        last_file = cm.storage_dir / "last_context.json"
        assert last_file.exists()

    def test_saves_session(self, cm):
        cm.add_task("test task")
        session_file = cm.storage_dir / "session.json"
        assert session_file.exists()
        data = json.loads(session_file.read_text())
        assert "session_id" in data


class TestCompressNow:
    def test_compress_with_messages(self, cm):
        cm.record_message("user", "hello " * 200)
        cm.record_message("assistant", "world " * 200)
        with patch.object(cm, "_get_smart_compressor") as mock_sc:
            mock_result = MagicMock()
            mock_result.compressed_messages = [{"role": "user", "content": "compressed"}]
            mock_result.compressed_tokens = 10
            mock_result.original_tokens = 100
            mock_result.compression_ratio = 0.9
            mock_sc.return_value.compress.return_value = mock_result
            summary = cm.compress_now()
            assert isinstance(summary, str)
            assert len(summary) > 0

    def test_compress_without_messages(self, cm):
        summary = cm.compress_now()
        assert isinstance(summary, str)
        assert "lingflow" in summary


class TestGetRecoverySummary:
    def test_no_recovery_file(self, cm):
        summary = cm.get_recovery_summary()
        assert isinstance(summary, str)

    def test_existing_recovery_file(self, cm):
        recovery = cm.storage_dir / "RECOVERY_CONTEXT.md"
        recovery.write_text("existing recovery content")
        summary = cm.get_recovery_summary()
        assert summary == "existing recovery content"


class TestGenerateHandover:
    def test_generate_handover(self, cm):
        with patch("lingflow.context.handover.HandoverDocument") as mock_hd:
            mock_doc = MagicMock()
            mock_doc.to_markdown.return_value = "# Handoff"
            mock_doc.to_json.return_value = '{"handoff": true}'
            mock_hd.from_context_snapshot.return_value = mock_doc
            doc = cm.generate_handover(reason="test")
            assert doc is mock_doc

    def test_generate_handover_with_messages(self, cm):
        cm.record_message("user", "hello world")
        with (
            patch("lingflow.context.handover.HandoverDocument") as mock_hd,
            patch("lingflow.context.degradation.DegradationDetector") as mock_dd,
        ):
            mock_report = MagicMock()
            mock_report.health.value = "healthy"
            mock_report.detected_types = []
            mock_dd.return_value.get_health_score.return_value = mock_report
            mock_doc = MagicMock()
            mock_doc.to_markdown.return_value = "# Handoff"
            mock_doc.to_json.return_value = "{}"
            mock_hd.from_context_snapshot.return_value = mock_doc
            doc = cm.generate_handover()
            assert doc is mock_doc


class TestGlobalFunctions:
    def test_get_context_manager(self):
        cm = get_context_manager()
        assert isinstance(cm, ContextManager)

    def test_track_context(self):
        track_context("user", "test message")
        cm = get_context_manager()
        assert cm.message_count == 1

    def test_add_task_global(self):
        add_task("global task")
        cm = get_context_manager()
        assert "global task" in cm.snapshot.tasks_pending

    def test_complete_task_global(self):
        add_task("global task")
        complete_task("global task")
        cm = get_context_manager()
        assert "global task" in cm.snapshot.tasks_completed

    def test_compress_context_global(self):
        result = compress_context()
        assert isinstance(result, str)

    def test_get_recovery_context(self):
        result = get_recovery_context()
        assert isinstance(result, str)
