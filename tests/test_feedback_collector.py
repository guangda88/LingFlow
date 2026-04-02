"""Tests for lingflow.feedback.collector"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from lingflow.feedback.collector import (
    Feedback,
    FeedbackCategory,
    FeedbackCollector,
    FeedbackSeverity,
    get_feedback_collector,
    list_feedbacks,
    submit_bug,
)


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def collector(tmp_dir):
    return FeedbackCollector(storage_dir=os.path.join(tmp_dir, "fb"))


class TestFeedbackCategory:
    def test_values(self):
        assert FeedbackCategory.BUG.value == "bug"
        assert FeedbackCategory.FEATURE.value == "feature"
        assert FeedbackCategory.IMPROVEMENT.value == "improvement"
        assert FeedbackCategory.PERFORMANCE.value == "performance"
        assert FeedbackCategory.DOCUMENTATION.value == "documentation"
        assert FeedbackCategory.USABILITY.value == "usability"
        assert FeedbackCategory.OTHER.value == "other"

    def test_from_value(self):
        assert FeedbackCategory("bug") is FeedbackCategory.BUG


class TestFeedbackSeverity:
    def test_values(self):
        assert FeedbackSeverity.LOW.value == "low"
        assert FeedbackSeverity.MEDIUM.value == "medium"
        assert FeedbackSeverity.HIGH.value == "high"
        assert FeedbackSeverity.CRITICAL.value == "critical"


class TestFeedback:
    def test_to_dict(self):
        fb = Feedback(
            id="abc",
            category=FeedbackCategory.BUG,
            severity=FeedbackSeverity.HIGH,
            title="Test",
            description="Desc",
            timestamp="2026-01-01",
        )
        d = fb.to_dict()
        assert d["category"] == "bug"
        assert d["severity"] == "high"
        assert d["id"] == "abc"

    def test_to_json(self):
        fb = Feedback(
            id="abc",
            category=FeedbackCategory.BUG,
            severity=FeedbackSeverity.HIGH,
            title="Test",
            description="Desc",
            timestamp="2026-01-01",
        )
        j = fb.to_json()
        data = json.loads(j)
        assert data["category"] == "bug"

    def test_defaults(self):
        fb = Feedback(
            id="x",
            category=FeedbackCategory.OTHER,
            severity=FeedbackSeverity.LOW,
            title="T",
            description="D",
            timestamp="2026-01-01",
        )
        assert fb.status == "open"
        assert fb.user is None
        assert fb.resolution is None


class TestFeedbackCollector:
    def test_init_creates_dir(self, tmp_dir):
        path = os.path.join(tmp_dir, "new_fb")
        FeedbackCollector(storage_dir=path)
        assert Path(path).exists()

    def test_submit_feedback(self, collector):
        fb = collector.submit_feedback(
            category=FeedbackCategory.BUG,
            severity=FeedbackSeverity.HIGH,
            title="Login fails",
            description="Users can't log in",
        )
        assert fb.title == "Login fails"
        assert fb.category == FeedbackCategory.BUG
        assert fb.status == "open"
        assert len(fb.id) == 8

    def test_submit_feedback_strips_whitespace(self, collector):
        fb = collector.submit_feedback(
            category=FeedbackCategory.BUG,
            severity=FeedbackSeverity.LOW,
            title="  padded  ",
            description="  desc  ",
        )
        assert fb.title == "padded"
        assert fb.description == "desc"

    def test_submit_feedback_empty_title_raises(self, collector):
        with pytest.raises(ValueError, match="不能为空"):
            collector.submit_feedback(
                category=FeedbackCategory.BUG,
                severity=FeedbackSeverity.LOW,
                title="",
                description="desc",
            )

    def test_submit_feedback_whitespace_title_raises(self, collector):
        with pytest.raises(ValueError):
            collector.submit_feedback(
                category=FeedbackCategory.BUG,
                severity=FeedbackSeverity.LOW,
                title="   ",
                description="desc",
            )

    def test_submit_feedback_empty_description_raises(self, collector):
        with pytest.raises(ValueError, match="不能为空"):
            collector.submit_feedback(
                category=FeedbackCategory.BUG,
                severity=FeedbackSeverity.LOW,
                title="title",
                description="",
            )

    def test_submit_with_optional_fields(self, collector):
        fb = collector.submit_feedback(
            category=FeedbackCategory.BUG,
            severity=FeedbackSeverity.CRITICAL,
            title="Crash",
            description="App crashes",
            user="alice",
            email="alice@example.com",
            reproduction_steps=["step1", "step2"],
            environment={"os": "Linux"},
            logs="error log",
            stack_trace="traceback here",
        )
        assert fb.user == "alice"
        assert fb.email == "alice@example.com"
        assert fb.reproduction_steps == ["step1", "step2"]
        assert fb.environment == {"os": "Linux"}
        assert fb.logs == "error log"
        assert fb.stack_trace == "traceback here"

    def test_submit_bug_report(self, collector):
        fb = collector.submit_bug_report(
            title="Bug",
            description="Something broke",
            reproduction_steps=["do this"],
            stack_trace="tb",
            severity=FeedbackSeverity.HIGH,
        )
        assert fb.category == FeedbackCategory.BUG
        assert fb.environment is not None
        assert "os" in fb.environment
        assert "python_version" in fb.environment

    def test_submit_bug_report_default_severity(self, collector):
        fb = collector.submit_bug_report(
            title="Bug",
            description="Default sev",
        )
        assert fb.severity == FeedbackSeverity.MEDIUM

    def test_persistence(self, tmp_dir):
        path = os.path.join(tmp_dir, "persist_fb")
        c1 = FeedbackCollector(storage_dir=path)
        c1.submit_feedback(
            category=FeedbackCategory.FEATURE,
            severity=FeedbackSeverity.LOW,
            title="Feature request",
            description="Please add X",
        )
        fb_file = Path(path) / "feedbacks.json"
        assert fb_file.exists()
        data = json.loads(fb_file.read_text())
        assert data["total_count"] == 1

        c2 = FeedbackCollector(storage_dir=path)
        assert len(c2._feedbacks) == 1
        assert c2._feedbacks[0].title == "Feature request"

    def test_get_feedbacks_empty(self, collector):
        assert collector.get_feedbacks() == []

    def test_get_feedbacks_all(self, collector):
        collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.HIGH, "B1", "d1")
        collector.submit_feedback(FeedbackCategory.FEATURE, FeedbackSeverity.LOW, "F1", "d2")
        fbs = collector.get_feedbacks()
        assert len(fbs) == 2

    def test_get_feedbacks_filter_category(self, collector):
        collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.HIGH, "B1", "d1")
        collector.submit_feedback(FeedbackCategory.FEATURE, FeedbackSeverity.LOW, "F1", "d2")
        bugs = collector.get_feedbacks(category=FeedbackCategory.BUG)
        assert len(bugs) == 1
        assert bugs[0].title == "B1"

    def test_get_feedbacks_filter_status(self, collector):
        fb = collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.HIGH, "B1", "d1")
        collector.update_status(fb.id, "resolved")
        open_fbs = collector.get_feedbacks(status="open")
        assert len(open_fbs) == 0
        resolved_fbs = collector.get_feedbacks(status="resolved")
        assert len(resolved_fbs) == 1

    def test_get_feedbacks_limit(self, collector):
        for i in range(5):
            collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.LOW, f"T{i}", f"D{i}")
        limited = collector.get_feedbacks(limit=2)
        assert len(limited) == 2

    def test_get_feedback_found(self, collector):
        fb = collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.HIGH, "Find me", "d")
        found = collector.get_feedback(fb.id)
        assert found is not None
        assert found.title == "Find me"

    def test_get_feedback_not_found(self, collector):
        assert collector.get_feedback("nonexistent") is None

    def test_update_status(self, collector):
        fb = collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.HIGH, "B1", "d1")
        assert collector.update_status(fb.id, "in_progress") is True
        found = collector.get_feedback(fb.id)
        assert found.status == "in_progress"

    def test_update_status_with_resolution(self, collector):
        fb = collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.HIGH, "B1", "d1")
        collector.update_status(fb.id, "resolved", resolution="Fixed in v2")
        found = collector.get_feedback(fb.id)
        assert found.status == "resolved"
        assert found.resolution == "Fixed in v2"
        assert found.resolved_at is not None

    def test_update_status_nonexistent(self, collector):
        assert collector.update_status("nope", "resolved") is False

    def test_get_statistics_empty(self, collector):
        stats = collector.get_statistics()
        assert stats["total"] == 0
        assert stats["open"] == 0

    def test_get_statistics(self, collector):
        collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.HIGH, "B1", "d1")
        collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.LOW, "B2", "d2")
        fb3 = collector.submit_feedback(FeedbackCategory.FEATURE, FeedbackSeverity.MEDIUM, "F1", "d3")
        collector.update_status(fb3.id, "resolved")
        stats = collector.get_statistics()
        assert stats["total"] == 3
        assert stats["by_category"]["bug"] == 2
        assert stats["by_category"]["feature"] == 1
        assert stats["by_severity"]["high"] == 1
        assert stats["resolved"] == 1

    def test_export_markdown(self, collector):
        collector.submit_feedback(
            FeedbackCategory.BUG,
            FeedbackSeverity.HIGH,
            "Login bug",
            "Can't log in",
            reproduction_steps=["Open app", "Click login"],
        )
        md = collector.export_markdown()
        assert "# 用户反馈报告" in md
        assert "Login bug" in md
        assert "复现步骤" in md
        assert "Open app" in md

    def test_export_markdown_with_file(self, collector, tmp_dir):
        collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.LOW, "T1", "D1")
        out = os.path.join(tmp_dir, "report.md")
        md = collector.export_markdown(output_path=out)
        assert Path(out).exists()
        assert md == Path(out).read_text()

    def test_export_markdown_closed_excluded(self, collector):
        fb = collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.LOW, "Closed", "D")
        collector.update_status(fb.id, "closed")
        md = collector.export_markdown()
        assert "Closed" not in md

    def test_export_markdown_with_resolution(self, collector):
        fb = collector.submit_feedback(FeedbackCategory.BUG, FeedbackSeverity.HIGH, "B1", "D1")
        collector.update_status(fb.id, "resolved", resolution="Fixed")
        md = collector.export_markdown()
        assert "解决方案" in md
        assert "Fixed" in md


class TestModuleFunctions:
    def test_get_feedback_collector(self):
        c = get_feedback_collector()
        assert isinstance(c, FeedbackCollector)

    def test_submit_bug(self):
        fb = submit_bug(title="Test bug", description="Bug desc")
        assert fb.category == FeedbackCategory.BUG

    def test_list_feedbacks(self):
        fbs = list_feedbacks()
        assert isinstance(fbs, list)
