#!/usr/bin/env python3
"""会话交接文档测试

测试 HandoffDocument 的各项功能:
1. 创建与序列化
2. Markdown/JSON 生成
3. 从 ContextSnapshot 创建
4. 字段过滤
"""

import json

from lingflow.context.handoff import HandoffDocument
from lingflow.context.manager import ContextSnapshot


class TestHandoffCreation:
    """创建测试"""

    def test_default_creation(self):
        doc = HandoffDocument()
        assert doc.version == "1.0"
        assert doc.session_id == ""
        assert doc.tasks_completed == []
        assert doc.tasks_pending == []

    def test_full_creation(self):
        doc = HandoffDocument(
            session_id="test-abc",
            reason="token_limit",
            current_task="implement feature X",
            tasks_completed=["setup", "design"],
            tasks_pending=["testing", "docs"],
            tasks_in_progress=["coding"],
            key_decisions=[{"decision": "use Python", "rationale": "team expertise"}],
            important_files={"main.py": "entry point"},
            constraints=["must support Python 3.8+"],
            known_issues=["memory leak in module Y"],
            failed_approaches=["tried approach A, too slow"],
            next_steps=["write unit tests", "add logging"],
            context_for_next_step="Module X is at 80% completion",
        )
        assert doc.session_id == "test-abc"
        assert len(doc.tasks_completed) == 2
        assert len(doc.key_decisions) == 1
        assert doc.degradation_detected is False


class TestHandoffSerialization:
    """序列化测试"""

    def test_to_dict(self):
        doc = HandoffDocument(
            session_id="s1",
            tasks_completed=["task1"],
        )
        d = doc.to_dict()
        assert d["session_id"] == "s1"
        assert d["tasks_completed"] == ["task1"]
        assert "version" in d
        assert "timestamp" in d

    def test_to_json(self):
        doc = HandoffDocument(
            session_id="s2",
            reason="degradation",
        )
        j = doc.to_json()
        parsed = json.loads(j)
        assert parsed["session_id"] == "s2"
        assert parsed["reason"] == "degradation"

    def test_from_dict(self):
        data = {
            "session_id": "s3",
            "tasks_completed": ["a", "b"],
            "tasks_pending": ["c"],
            "version": "1.0",
        }
        doc = HandoffDocument.from_dict(data)
        assert doc.session_id == "s3"
        assert doc.tasks_completed == ["a", "b"]

    def test_from_dict_ignores_unknown_fields(self):
        data = {
            "session_id": "s4",
            "unknown_field": "should be ignored",
        }
        doc = HandoffDocument.from_dict(data)
        assert doc.session_id == "s4"

    def test_from_json(self):
        j = '{"session_id": "s5", "reason": "manual"}'
        doc = HandoffDocument.from_json(j)
        assert doc.session_id == "s5"
        assert doc.reason == "manual"

    def test_roundtrip(self):
        doc = HandoffDocument(
            session_id="roundtrip",
            reason="test",
            tasks_completed=["t1"],
            tasks_pending=["t2"],
            key_decisions=[{"decision": "d1", "rationale": "r1"}],
        )
        j = doc.to_json()
        doc2 = HandoffDocument.from_json(j)
        assert doc2.session_id == doc.session_id
        assert doc2.tasks_completed == doc.tasks_completed
        assert doc2.key_decisions == doc.key_decisions


class TestHandoffMarkdown:
    """Markdown 生成测试"""

    def test_basic_markdown(self):
        doc = HandoffDocument(
            session_id="md-test",
            reason="token_limit",
        )
        md = doc.to_markdown()
        assert "# LingFlow 会话交接文档" in md
        assert "md-test" in md
        assert "token_limit" in md

    def test_markdown_with_tasks(self):
        doc = HandoffDocument(
            tasks_completed=["task A", "task B"],
            tasks_pending=["task C"],
            tasks_in_progress=["task D"],
        )
        md = doc.to_markdown()
        assert "已完成任务" in md
        assert "待完成任务" in md
        assert "进行中的任务" in md
        assert "task A" in md
        assert "task C" in md

    def test_markdown_with_decisions(self):
        doc = HandoffDocument(
            key_decisions=[
                {"decision": "use PostgreSQL", "rationale": "better JSON support"},
                {"decision": "adopt TDD", "rationale": ""},
            ]
        )
        md = doc.to_markdown()
        assert "关键决策" in md
        assert "use PostgreSQL" in md
        assert "better JSON support" in md

    def test_markdown_with_constraints(self):
        doc = HandoffDocument(
            constraints=["Python 3.8+"],
            known_issues=["memory leak"],
            failed_approaches=["approach X"],
        )
        md = doc.to_markdown()
        assert "约束条件" in md
        assert "已知问题" in md
        assert "已失败的方案" in md

    def test_markdown_with_next_steps(self):
        doc = HandoffDocument(
            next_steps=["step 1", "step 2"],
            context_for_next_step="Module at 80%",
        )
        md = doc.to_markdown()
        assert "下一步" in md
        assert "step 1" in md
        assert "Module at 80%" in md

    def test_markdown_with_degradation(self):
        doc = HandoffDocument(
            degradation_detected=True,
            degradation_types=["repetition_collapse", "instruction_drift"],
            token_usage_at_handoff=150000,
        )
        md = doc.to_markdown()
        assert "退化检测" in md
        assert "repetition_collapse" in md
        assert "150000" in md

    def test_empty_sections_omitted(self):
        doc = HandoffDocument()
        md = doc.to_markdown()
        assert "已完成任务" not in md
        assert "待完成任务" not in md
        assert "关键决策" not in md


class TestHandoffFromSnapshot:
    """从 ContextSnapshot 创建测试"""

    def test_basic_from_snapshot(self):
        snap = ContextSnapshot(
            timestamp="2026-01-01T00:00:00",
            session_id="snap-123",
            tasks_completed=["task1"],
            tasks_pending=["task2"],
            key_decisions=["decision1"],
        )
        doc = HandoffDocument.from_context_snapshot(snap)
        assert doc.session_id == "snap-123"
        assert doc.tasks_completed == ["task1"]
        assert doc.tasks_pending == ["task2"]

    def test_decisions_converted_to_dicts(self):
        snap = ContextSnapshot(
            timestamp="2026-01-01",
            session_id="snap-456",
            key_decisions=["use Python", "use pytest"],
        )
        doc = HandoffDocument.from_context_snapshot(snap)
        assert len(doc.key_decisions) == 2
        assert doc.key_decisions[0]["decision"] == "use Python"
        assert doc.key_decisions[1]["decision"] == "use pytest"

    def test_from_snapshot_with_overrides(self):
        snap = ContextSnapshot(
            timestamp="2026-01-01",
            session_id="snap-789",
        )
        doc = HandoffDocument.from_context_snapshot(
            snap,
            reason="manual",
            current_task="testing",
        )
        assert doc.reason == "manual"
        assert doc.current_task == "testing"

    def test_from_snapshot_with_important_files(self):
        snap = ContextSnapshot(
            timestamp="2026-01-01",
            session_id="snap-files",
            important_files={"main.py": "entry", "config.yaml": "config"},
        )
        doc = HandoffDocument.from_context_snapshot(snap)
        assert doc.important_files == {"main.py": "entry", "config.yaml": "config"}


class TestHandoffDegradationFields:
    """退化相关字段测试"""

    def test_no_degradation_by_default(self):
        doc = HandoffDocument()
        assert doc.degradation_detected is False
        assert doc.degradation_types == []

    def test_degradation_with_types(self):
        doc = HandoffDocument(
            degradation_detected=True,
            degradation_types=["repetition_collapse", "attention_dilution"],
            token_usage_at_handoff=120000,
        )
        assert doc.degradation_detected is True
        assert len(doc.degradation_types) == 2
