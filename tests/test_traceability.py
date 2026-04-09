"""Requirements traceability tests"""

import os
import tempfile

import pytest

from lingflow.requirements.traceability import (
    Requirement,
    RequirementPriority,
    RequirementStatus,
    RequirementsTraceability,
    TraceEvent,
)


@pytest.fixture
def storage_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def tracker(storage_dir):
    path = os.path.join(storage_dir, "reqs.json")
    return RequirementsTraceability(storage_path=path)


class TestRequirementStatus:
    def test_values(self):
        assert RequirementStatus.DRAFT.value == "draft"
        assert RequirementStatus.APPROVED.value == "approved"
        assert RequirementStatus.IMPLEMENTED.value == "implemented"
        assert RequirementStatus.CANCELLED.value == "cancelled"


class TestRequirementPriority:
    def test_values(self):
        assert RequirementPriority.CRITICAL.value == "critical"
        assert RequirementPriority.HIGH.value == "high"
        assert RequirementPriority.MEDIUM.value == "medium"
        assert RequirementPriority.LOW.value == "low"


class TestRequirement:
    def test_defaults(self):
        r = Requirement(id="r1", title="t", description="d")
        assert r.status == RequirementStatus.DRAFT
        assert r.priority == RequirementPriority.MEDIUM
        assert r.parent_id is None
        assert r.child_ids == []
        assert r.tags == []

    def test_to_dict(self):
        r = Requirement(id="r1", title="t", description="d")
        d = r.to_dict()
        assert d["id"] == "r1"
        assert d["status"] == "draft"
        assert d["priority"] == "medium"
        assert "created_at" in d

    def test_from_dict(self):
        d = {"id": "r1", "title": "t", "description": "d", "status": "approved", "priority": "high"}
        r = Requirement.from_dict(d)
        assert r.status == RequirementStatus.APPROVED
        assert r.priority == RequirementPriority.HIGH

    def test_roundtrip(self):
        r = Requirement(id="r1", title="t", description="d", category="cat1", epic="epic1")
        d = r.to_dict()
        r2 = Requirement.from_dict(d)
        assert r2.id == r.id
        assert r2.category == "cat1"
        assert r2.epic == "epic1"


class TestTraceEvent:
    def test_defaults(self):
        e = TraceEvent(id="e1", requirement_id="r1", event_type="created")
        assert e.description == ""
        assert e.metadata == {}


class TestRequirementsTraceability:
    def test_create_requirement(self, tracker):
        req = tracker.create_requirement("r1", "Title", "Desc")
        assert req.id == "r1"
        assert req.title == "Title"

    def test_create_duplicate_fails(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        with pytest.raises(ValueError, match="已存在"):
            tracker.create_requirement("r1", "T2", "D2")

    def test_get_requirement(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        assert tracker.get_requirement("r1") is not None
        assert tracker.get_requirement("missing") is None

    def test_update_requirement(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        updated = tracker.update_requirement("r1", title="New Title")
        assert updated.title == "New Title"

    def test_update_nonexistent(self, tracker):
        assert tracker.update_requirement("missing", title="x") is None

    def test_update_status_records_event(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.update_requirement("r1", status=RequirementStatus.APPROVED)
        events = [e for e in tracker._events if e.requirement_id == "r1" and e.event_type == "status_change"]
        assert len(events) == 1

    def test_delete_requirement(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        assert tracker.delete_requirement("r1") is True
        assert tracker.get_requirement("r1") is None

    def test_delete_nonexistent(self, tracker):
        assert tracker.delete_requirement("missing") is False

    def test_list_requirements(self, tracker):
        tracker.create_requirement("r1", "T", "D", priority=RequirementPriority.HIGH)
        tracker.create_requirement("r2", "T", "D", priority=RequirementPriority.LOW)
        assert len(tracker.list_requirements()) == 2
        assert len(tracker.list_requirements(priority=RequirementPriority.HIGH)) == 1

    def test_list_by_category(self, tracker):
        tracker.create_requirement("r1", "T", "D", category="backend")
        tracker.create_requirement("r2", "T", "D", category="frontend")
        assert len(tracker.list_requirements(category="backend")) == 1

    def test_list_by_epic(self, tracker):
        tracker.create_requirement("r1", "T", "D", epic="epic1")
        tracker.create_requirement("r2", "T", "D", epic="epic2")
        assert len(tracker.list_requirements(epic="epic1")) == 1

    def test_link_to_branch(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        assert tracker.link_to_branch("r1", "feature/r1") is True
        assert tracker.get_requirement("r1").feature_branch == "feature/r1"

    def test_link_to_branch_nonexistent(self, tracker):
        assert tracker.link_to_branch("missing", "feature/x") is False

    def test_add_commit(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        assert tracker.add_commit("r1", "abc123") is True
        assert "abc123" in tracker.get_requirement("r1").commits

    def test_add_commit_duplicate(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.add_commit("r1", "abc123")
        tracker.add_commit("r1", "abc123")
        assert len(tracker.get_requirement("r1").commits) == 1

    def test_add_commit_nonexistent(self, tracker):
        assert tracker.add_commit("missing", "abc") is False

    def test_add_pull_request(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        assert tracker.add_pull_request("r1", "pr-42") is True
        assert "pr-42" in tracker.get_requirement("r1").pull_requests

    def test_add_pull_request_nonexistent(self, tracker):
        assert tracker.add_pull_request("missing", "pr-1") is False

    def test_add_task(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        assert tracker.add_task("r1", "task-1") is True
        assert "task-1" in tracker.get_requirement("r1").tasks

    def test_add_task_nonexistent(self, tracker):
        assert tracker.add_task("missing", "task-1") is False

    def test_add_test_case(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        assert tracker.add_test_case("r1", "tc-1") is True
        assert "tc-1" in tracker.get_requirement("r1").test_cases

    def test_add_test_case_nonexistent(self, tracker):
        assert tracker.add_test_case("missing", "tc-1") is False

    def test_add_dependency(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.create_requirement("r2", "T", "D")
        tracker.add_dependency("r2", "r1")
        assert "r1" in tracker.get_requirement("r2").depends_on
        assert "r2" in tracker.get_requirement("r1").blocks

    def test_add_dependency_nonexistent(self, tracker):
        assert tracker.add_dependency("missing", "r1") is False

    def test_get_traceability_report(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        tracker.add_commit("r1", "abc123")
        report = tracker.get_traceability_report("r1")
        assert report["requirement"]["id"] == "r1"
        assert report["summary"]["commits_count"] == 1

    def test_get_traceability_report_nonexistent(self, tracker):
        report = tracker.get_traceability_report("missing")
        assert "error" in report

    def test_get_status_summary(self, tracker):
        tracker.create_requirement("r1", "T", "D")
        summary = tracker.get_status_summary()
        assert summary["draft"] == 1

    def test_persistence(self, storage_dir):
        path = os.path.join(storage_dir, "persist.json")
        t1 = RequirementsTraceability(storage_path=path)
        t1.create_requirement("r1", "T", "D")
        t2 = RequirementsTraceability(storage_path=path)
        assert t2.get_requirement("r1") is not None
        assert t2.get_requirement("r1").title == "T"
