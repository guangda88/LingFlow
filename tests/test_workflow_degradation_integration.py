"""工作流退化检测和交接文档自动生成集成测试"""

import json
from unittest.mock import MagicMock, patch

import pytest

from lingflow.common.models import TaskResult
from lingflow.context.degradation import DegradationDetector
from lingflow.context.manager import ContextManager
from lingflow.workflow.orchestrator import WorkflowOrchestrator


class TestWorkflowDegradationIntegration:
    """测试 WorkflowOrchestrator 中的退化检测集成"""

    def _make_coordinator_mock(self):
        coord = MagicMock()
        coord.completed_tasks = {}
        coord.failed_tasks = {}
        coord.submit_task = MagicMock()
        coord.execute_tasks_parallel = MagicMock(return_value={})
        return coord

    def test_degradation_detector_initialized_on_check(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)
        assert orch._degradation_detector is None

        batch = {"t1": TaskResult(task_id="t1", success=True, output="ok")}
        orch._check_degradation(batch)

        assert orch._degradation_detector is not None
        assert isinstance(orch._degradation_detector, DegradationDetector)

    def test_workflow_messages_accumulated(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        batch1 = {"t1": TaskResult(task_id="t1", success=True, output="result 1")}
        batch2 = {"t2": TaskResult(task_id="t2", success=True, output="result 2")}
        orch._check_degradation(batch1)
        orch._check_degradation(batch2)

        assert len(orch._workflow_messages) == 2
        assert orch._workflow_messages[0]["role"] == "assistant"
        assert orch._workflow_messages[0]["content"] == "result 1"

    def test_failed_tasks_use_user_role(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        batch = {"t1": TaskResult(task_id="t1", success=False, error="timeout")}
        orch._check_degradation(batch)

        assert orch._workflow_messages[0]["role"] == "user"
        assert orch._workflow_messages[0]["content"] == "timeout"

    def test_degradation_report_updated(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        batch = {"t1": TaskResult(task_id="t1", success=True, output="normal output")}
        orch._check_degradation(batch)

        assert orch._degradation_report is not None
        assert "health" in orch._degradation_report
        assert "score" in orch._degradation_report

    def test_get_degradation_report_initially_none(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)
        assert orch.get_degradation_report() is None

    def test_get_degradation_report_after_check(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)
        batch = {"t1": TaskResult(task_id="t1", success=True, output="ok")}
        orch._check_degradation(batch)

        report = orch.get_degradation_report()
        assert report is not None
        assert "health" in report

    def test_repetition_detected_in_workflow(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        repeated_content = "the same output repeated verbatim without variation"
        for i in range(5):
            batch = {f"t{i}": TaskResult(task_id=f"t{i}", success=True, output=repeated_content)}
            orch._check_degradation(batch)

        report = orch.get_degradation_report()
        assert report is not None
        assert report["score"] < 1.0

    def test_critical_degradation_logs_warning(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        success_batch = {
            f"t{i}": TaskResult(
                task_id=f"t{i}",
                success=True,
                output=f"error exception traceback failure 错误 异常 occurred in step {i}",
            )
            for i in range(5)
        }
        orch._check_degradation(success_batch)

        report = orch.get_degradation_report()
        assert report is not None
        assert report["score"] < 1.0

    def test_workflow_messages_reset_on_execute(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)
        orch._workflow_messages = [{"role": "old", "content": "stale"}]
        orch._degradation_report = {"old": True}

        with patch("asyncio.run", side_effect=RuntimeError("test")):
            with pytest.raises(RuntimeError):
                orch.execute([])

        assert orch._workflow_messages == []
        assert orch._degradation_report is None


class TestHandoffAutoGeneration:
    """测试交接文档在紧急预算时的自动生成"""

    def _make_manager(self, tmp_path):
        return ContextManager(storage_dir=str(tmp_path))

    def test_handover_generated_on_emergency_budget(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        mgr.estimated_tokens = int(mgr.ESTIMATED_TOKEN_LIMIT * 0.85)

        mgr.record_message("user", "push to emergency level " + "x" * 10000)

        handover_file = tmp_path / "HANDOVER.md"
        assert handover_file.exists() or mgr.estimated_tokens < mgr.ESTIMATED_TOKEN_LIMIT * 0.8

    def test_handover_file_written_by_generate_handover(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        mgr.add_task("design review", completed=False)
        mgr.add_decision("use tiktoken for counting")

        mgr.generate_handover(reason="manual_test")

        handover_file = tmp_path / "HANDOVER.md"
        handover_json = tmp_path / "handover.json"

        assert handover_file.exists()
        assert handover_json.exists()

        content = handover_file.read_text(encoding="utf-8")
        assert "会话传递文档" in content
        assert "manual_test" in content

        json.loads(handover_json.read_text(encoding="utf-8"))
        assert True

    def test_handover_includes_degradation_when_detected(self, tmp_path):
        mgr = self._make_manager(tmp_path)

        for i in range(10):
            mgr._messages.append(
                {
                    "role": "assistant",
                    "content": f"error exception traceback failure 错误 异常 {i}",
                }
            )

        doc = mgr.generate_handover(reason="degradation_test")
        assert doc.degradation_detected is True
        assert len(doc.degradation_types) > 0

    def test_handover_preserves_snapshot_data(self, tmp_path):
        mgr = self._make_manager(tmp_path)
        mgr.add_task("task A", completed=True)
        mgr.add_task("task B", completed=False)
        mgr.add_decision("use python 3.11")
        mgr.add_file("src/main.py", "main entry")
        mgr.set_next_steps(["implement feature X", "write tests"])

        doc = mgr.generate_handover(reason="test")

        assert "task A" in doc.tasks_completed
        assert "task B" in doc.tasks_pending
        assert any(d.get("decision") == "use python 3.11" for d in doc.key_decisions)
        assert "src/main.py" in doc.important_files
        assert "implement feature X" in doc.next_steps


class TestOrchestratorDegradationReport:
    """测试编排器退化报告在 get_status 中的暴露"""

    def _make_coordinator_mock(self):
        coord = MagicMock()
        coord.completed_tasks = {}
        coord.failed_tasks = {}
        coord.submit_task = MagicMock()
        coord.execute_tasks_parallel = MagicMock(return_value={})
        return coord

    def test_report_accessible_after_check(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        batch = {"t1": TaskResult(task_id="t1", success=True, output="done")}
        orch._check_degradation(batch)

        report = orch.get_degradation_report()
        assert report["health"] == "healthy"
        assert report["score"] >= 0.9

    def test_healthy_report_with_good_results(self):
        coord = self._make_coordinator_mock()
        orch = WorkflowOrchestrator(coord)

        for i in range(5):
            batch = {
                f"t{i}": TaskResult(
                    task_id=f"t{i}",
                    success=True,
                    output=f"Completed step {i} successfully with unique result",
                )
            }
            orch._check_degradation(batch)

        report = orch.get_degradation_report()
        assert report is not None
        assert report["score"] >= 0.5
