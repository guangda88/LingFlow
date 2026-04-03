"""Extended tests for lingflow.requirements.traceability - module functions and edge cases"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from lingflow.requirements.traceability import (
    RequirementStatus,
    RequirementPriority,
    Requirement,
    TraceEvent,
    RequirementsTraceability,
    get_traceability,
    create_requirement as mod_create,
    get_requirement as mod_get,
    update_requirement as mod_update,
    list_requirements as mod_list,
    link_to_branch as mod_link,
    add_commit as mod_add_commit,
    get_traceability_report as mod_report,
)


@pytest.fixture
def storage_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def tracker(storage_dir):
    path = os.path.join(storage_dir, "ext_reqs.json")
    return RequirementsTraceability(storage_path=path)


class TestModuleSingleton:
    def test_get_traceability_returns_instance(self):
        t = get_traceability()
        assert isinstance(t, RequirementsTraceability)

    def test_get_traceability_singleton(self):
        t1 = get_traceability()
        t2 = get_traceability()
        assert t1 is t2


class TestModuleConvenienceFunctions:
    @patch("lingflow.requirements.traceability.get_traceability")
    def test_create_requirement(self, mock_get):
        mock_tracker = MagicMock()
        mock_get.return_value = mock_tracker
        mod_create("r1", "Title", "Desc")
        mock_tracker.create_requirement.assert_called_once_with("r1", "Title", "Desc")

    @patch("lingflow.requirements.traceability.get_traceability")
    def test_get_requirement(self, mock_get):
        mock_tracker = MagicMock()
        mock_get.return_value = mock_tracker
        mod_get("r1")
        mock_tracker.get_requirement.assert_called_once_with("r1")

    @patch("lingflow.requirements.traceability.get_traceability")
    def test_update_requirement(self, mock_get):
        mock_tracker = MagicMock()
        mock_get.return_value = mock_tracker
        mod_update("r1", title="new")
        mock_tracker.update_requirement.assert_called_once_with("r1", title="new")

    @patch("lingflow.requirements.traceability.get_traceability")
    def test_list_requirements(self, mock_get):
        mock_tracker = MagicMock()
        mock_get.return_value = mock_tracker
        mod_list(status="draft")
        mock_tracker.list_requirements.assert_called_once_with(status="draft")

    @patch("lingflow.requirements.traceability.get_traceability")
    def test_link_to_branch(self, mock_get):
        mock_tracker = MagicMock()
        mock_get.return_value = mock_tracker
        mod_link("r1", "feature/r1")
        mock_tracker.link_to_branch.assert_called_once_with("r1", "feature/r1")

    @patch("lingflow.requirements.traceability.get_traceability")
    def test_add_commit(self, mock_get):
        mock_tracker = MagicMock()
        mock_get.return_value = mock_tracker
        mod_add_commit("r1", "abc123")
        mock_tracker.add_commit.assert_called_once_with("r1", "abc123")

    @patch("lingflow.requirements.traceability.get_traceability")
    def test_get_report(self, mock_get):
        mock_tracker = MagicMock()
        mock_get.return_value = mock_tracker
        mod_report("r1")
        mock_tracker.get_traceability_report.assert_called_once_with("r1")


class TestUpdateStatusString:
    def test_update_with_string_status(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        updated = tracker.update_requirement("r1", status="approved")
        assert updated.status == "approved"

    def test_update_with_enum_status(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        updated = tracker.update_requirement("r1", status=RequirementStatus.APPROVED)
        assert updated.status == RequirementStatus.APPROVED

    def test_status_change_records_event(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.update_requirement("r1", status=RequirementStatus.IN_PROGRESS)
        events = [e for e in tracker._events if e.requirement_id == "r1" and e.event_type == "status_change"]
        assert len(events) == 1
        assert "draft" in events[0].description
        assert "in_progress" in events[0].description

    def test_same_status_no_event(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        before = len(tracker._events)
        tracker.update_requirement("r1", status=RequirementStatus.DRAFT)
        after = len(tracker._events)
        assert after == before


class TestGetStatusSummary:
    def test_all_zero_initially(self, tracker):
        summary = tracker.get_status_summary()
        for status in RequirementStatus:
            assert summary[status.value] == 0

    def test_counts_across_statuses(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.create_requirement("r2", "T", "D")
        tracker.update_requirement("r2", status=RequirementStatus.APPROVED)
        summary = tracker.get_status_summary()
        assert summary["draft"] == 1
        assert summary["approved"] == 1


class TestListWithFilters:
    def test_list_combined_filters(self, tracker):
        tracker.create_requirement("r1", "T", "D", category="cat1", epic="ep1")
        tracker.create_requirement("r2", "T", "D", category="cat1", epic="ep2")
        tracker.create_requirement("r3", "T", "D", category="cat2", epic="ep1")
        result = tracker.list_requirements(category="cat1", epic="ep1")
        assert len(result) == 1
        assert result[0].id == "r1"

    def test_list_by_status(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.create_requirement("r2", "T", "D")
        tracker.update_requirement("r2", status=RequirementStatus.IN_PROGRESS)
        in_progress = tracker.list_requirements(status=RequirementStatus.IN_PROGRESS)
        assert len(in_progress) == 1


class TestPersistence:
    def test_persistence_with_events(self, storage_dir):
        path = os.path.join(storage_dir, "persist.json")
        t1 = RequirementsTraceability(storage_path=path)
        t1.create_requirement("r1", "T", "D")
        t1.add_commit("r1", "abc123")
        t2 = RequirementsTraceability(storage_path=path)
        assert t2.get_requirement("r1") is not None
        assert len(t2._events) > 0

    def test_load_corrupt_file(self, storage_dir):
        path = os.path.join(storage_dir, "bad.json")
        with open(path, "w") as f:
            f.write("not valid json{{{")
        tracker = RequirementsTraceability(storage_path=path)
        assert len(tracker._requirements) == 0


class TestDefaultStoragePath:
    def test_default_path(self):
        tracker = RequirementsTraceability()
        assert tracker.storage_path == Path(".lingflow/requirements.json")


class TestRequirementToDict:
    def test_all_fields(self):
        r = Requirement(
            id="r1", title="Title", description="Desc",
            status=RequirementStatus.IMPLEMENTED,
            priority=RequirementPriority.HIGH,
            category="cat", epic="epic",
            tags=["t1"], commits=["c1"],
            pull_requests=["p1"], tasks=["task1"],
            test_cases=["tc1"], child_ids=["child"],
            depends_on=["dep"], blocks=["block"],
            metadata={"key": "val"}
        )
        d = r.to_dict()
        assert d["status"] == "implemented"
        assert d["priority"] == "high"
        assert d["category"] == "cat"
        assert d["tags"] == ["t1"]
        assert d["commits"] == ["c1"]
        assert d["metadata"] == {"key": "val"}


class TestRequirementFromDictEdge:
    def test_missing_status_defaults_to_draft(self):
        d = {"id": "r1", "title": "t", "description": "d"}
        r = Requirement.from_dict(d)
        assert r.status == RequirementStatus.DRAFT

    def test_missing_priority_defaults_to_medium(self):
        d = {"id": "r1", "title": "t", "description": "d"}
        r = Requirement.from_dict(d)
        assert r.priority == RequirementPriority.MEDIUM

    def test_datetime_string_conversion(self):
        r = Requirement(id="r1", title="t", description="d")
        d = r.to_dict()
        r2 = Requirement.from_dict(d)
        assert r2.created_at is not None
        assert r2.updated_at is not None


class TestTraceEventInit:
    def test_with_metadata(self):
        e = TraceEvent(
            id="e1", requirement_id="r1", event_type="test",
            description="desc", metadata={"key": "val"}
        )
        assert e.metadata == {"key": "val"}

    def test_auto_timestamp(self):
        e = TraceEvent(id="e1", requirement_id="r1", event_type="test")
        assert e.timestamp is not None


class TestAddPullRequestDuplicate:
    def test_duplicate_pr_not_added(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.add_pull_request("r1", "pr-1")
        tracker.add_pull_request("r1", "pr-1")
        assert len(tracker.get_requirement("r1").pull_requests) == 1


class TestAddTaskDuplicate:
    def test_duplicate_task_not_added(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.add_task("r1", "task-1")
        tracker.add_task("r1", "task-1")
        assert len(tracker.get_requirement("r1").tasks) == 1


class TestAddTestCaseDuplicate:
    def test_duplicate_test_not_added(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.add_test_case("r1", "tc-1")
        tracker.add_test_case("r1", "tc-1")
        assert len(tracker.get_requirement("r1").test_cases) == 1


class TestAddDependencyDuplicate:
    def test_duplicate_dep_not_added(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.create_requirement("r2", "T", "D")
        tracker.add_dependency("r2", "r1")
        tracker.add_dependency("r2", "r1")
        assert len(tracker.get_requirement("r2").depends_on) == 1

    def test_dependency_updates_blocks(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.create_requirement("r2", "T", "D")
        tracker.add_dependency("r2", "r1")
        assert "r2" in tracker.get_requirement("r1").blocks

    def test_dependency_missing_target(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.add_dependency("r1", "nonexistent")
        assert "nonexistent" in tracker.get_requirement("r1").depends_on


class TestGetTraceabilityReport:
    def test_report_has_all_fields(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.add_commit("r1", "abc")
        tracker.add_pull_request("r1", "pr-1")
        tracker.add_task("r1", "task-1")
        tracker.add_test_case("r1", "tc-1")
        tracker.add_dependency("r1", "nonexistent")
        report = tracker.get_traceability_report("r1")
        assert report["summary"]["commits_count"] == 1
        assert report["summary"]["pull_requests_count"] == 1
        assert report["summary"]["tasks_count"] == 1
        assert report["summary"]["test_cases_count"] == 1
        assert report["summary"]["dependencies_count"] == 1
        assert len(report["events"]) > 0
