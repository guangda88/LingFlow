"""Extended snapshot tests for additional coverage."""

import json
import pytest
from pathlib import Path
from lingflow.testing.snapshot import SnapshotTest, SnapshotMetadata


class TestSnapshotTest:
    @pytest.fixture
    def snapshot_dir(self, tmp_path):
        return tmp_path / "snapshots"

    @pytest.fixture
    def snapshot(self, snapshot_dir):
        return SnapshotTest(snapshot_dir)

    def test_init_creates_directory(self, snapshot_dir):
        assert not snapshot_dir.exists()
        s = SnapshotTest(snapshot_dir)
        assert snapshot_dir.exists()

    def test_assert_match_creates_snapshot(self, snapshot):
        result = {"value": 42}
        assert snapshot.assert_match("test_create", result) is True
        path = snapshot._get_snapshot_path("test_create")
        assert path.exists()

    def test_assert_match_matches_existing(self, snapshot):
        result = {"value": 42}
        snapshot.assert_match("test_match", result)
        assert snapshot.assert_match("test_match", result) is True

    def test_assert_match_mismatch_raises(self, snapshot):
        snapshot.assert_match("test_mismatch", {"value": 1})
        with pytest.raises(AssertionError, match="快照不匹配"):
            snapshot.assert_match("test_mismatch", {"value": 2})

    def test_assert_match_update_overwrites(self, snapshot):
        snapshot.assert_match("test_update", {"value": 1})
        assert snapshot.assert_match("test_update", {"value": 2}, update=True) is True
        assert snapshot.assert_match("test_update", {"value": 2}) is True

    def test_assert_match_with_metadata(self, snapshot):
        meta = SnapshotMetadata(test_name="test_meta", created_at="2025-01-01")
        snapshot.assert_match("test_meta", {"x": 1}, metadata=meta)
        path = snapshot._get_snapshot_path("test_meta")
        data = json.loads(path.read_text())
        assert data["metadata"]["test_name"] == "test_meta"

    def test_normalize_dict_sorted(self, snapshot):
        val = {"b": 2, "a": 1}
        result = snapshot._normalize_value(val)
        assert list(result.keys()) == ["a", "b"]

    def test_normalize_list(self, snapshot):
        val = [{"b": 2, "a": 1}]
        result = snapshot._normalize_value(val)
        assert result == [{"a": 1, "b": 2}]

    def test_normalize_scalar_types(self, snapshot):
        assert snapshot._normalize_value(42) == 42
        assert snapshot._normalize_value(3.14) == 3.14
        assert snapshot._normalize_value("hello") == "hello"
        assert snapshot._normalize_value(True) is True
        assert snapshot._normalize_value(None) is None

    def test_normalize_unknown_type(self, snapshot):
        class Custom:
            def __str__(self):
                return "custom"
        assert snapshot._normalize_value(Custom()) == "custom"

    def test_compute_diff_missing_keys(self, snapshot):
        diff = snapshot._compute_diff({"a": 1, "b": 2}, {"a": 1})
        assert "缺失键" in diff

    def test_compute_diff_added_keys(self, snapshot):
        diff = snapshot._compute_diff({"a": 1}, {"a": 1, "b": 2})
        assert "新增键" in diff

    def test_compute_diff_value_mismatch(self, snapshot):
        diff = snapshot._compute_diff({"a": 1}, {"a": 2})
        assert "差异" in diff
        assert "'a'" in diff

    def test_compute_diff_no_diff(self, snapshot):
        diff = snapshot._compute_diff({"a": 1}, {"a": 1})
        assert diff == "无明显差异"

    def test_list_snapshots(self, snapshot):
        snapshot.assert_match("test_list_1", {"v": 1})
        snapshot.assert_match("test_list_2", {"v": 2})
        names = snapshot.list_snapshots()
        assert "test_list_1" in names
        assert "test_list_2" in names

    def test_remove_snapshot(self, snapshot):
        snapshot.assert_match("test_remove", {"v": 1})
        assert snapshot.remove_snapshot("test_remove") is True
        assert not snapshot._get_snapshot_path("test_remove").exists()

    def test_remove_nonexistent_snapshot(self, snapshot):
        assert snapshot.remove_snapshot("nonexistent") is False

    def test_clear_snapshots(self, snapshot):
        snapshot.assert_match("test_clear_1", {"v": 1})
        snapshot.assert_match("test_clear_2", {"v": 2})
        snapshot.clear_snapshots()
        assert snapshot.list_snapshots() == []

    def test_load_snapshot(self, snapshot):
        snapshot.assert_match("test_load", {"key": "value"})
        path = snapshot._get_snapshot_path("test_load")
        data = snapshot._load_snapshot(path)
        assert data["data"] == {"key": "value"}

    def test_save_snapshot(self, snapshot):
        path = snapshot._get_snapshot_path("test_save")
        meta = SnapshotMetadata(test_name="test_save", created_at="2025-01-01")
        snapshot._save_snapshot(path, {"x": 1}, meta)
        data = json.loads(path.read_text())
        assert data["data"] == {"x": 1}
        assert data["metadata"]["test_name"] == "test_save"

    def test_update_snapshots_batch(self, snapshot):
        batch = {
            "batch_1": {"v": 1},
            "batch_2": {"v": 2},
        }
        snapshot.update_snapshots(batch)
        names = snapshot.list_snapshots()
        assert "batch_1" in names
        assert "batch_2" in names

    def test_snapshot_exists_no_update(self, snapshot):
        snapshot.assert_match("test_noexist", {"v": 1})
        assert snapshot._get_snapshot_path("test_noexist").exists()

    def test_snapshot_doesnt_exist_no_update_creates(self, snapshot):
        assert not snapshot._get_snapshot_path("test_new").exists()
        result = snapshot.assert_match("test_new", {"v": 1}, update=False)
        assert result is True
        assert snapshot._get_snapshot_path("test_new").exists()
