#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试 - 快照测试系统
"""

import tempfile
from pathlib import Path

import pytest

from lingflow.testing import SnapshotMetadata, SnapshotTest


class TestSnapshotTest:
    """测试 SnapshotTest"""

    @pytest.fixture
    def snapshot_dir(self):
        """创建临时快照目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def snapshot(self, snapshot_dir):
        """创建快照测试实例"""
        return SnapshotTest(snapshot_dir)

    def test_init_creates_directory(self, snapshot_dir):
        """测试初始化创建目录"""
        snapshot = SnapshotTest(snapshot_dir / "snapshots")
        assert snapshot.snapshot_dir.exists()
        assert snapshot.snapshot_dir.is_dir()

    def test_normalize_value_dict(self, snapshot):
        """测试规范化字典值"""
        value = {"z": 1, "a": 2, "m": 3}
        normalized = snapshot._normalize_value(value)

        assert list(normalized.keys()) == ["a", "m", "z"]  # 已排序

    def test_normalize_value_list(self, snapshot):
        """测试规范化列表值"""
        value = [3, 1, 2]
        normalized = snapshot._normalize_value(value)

        # 列表保持原始顺序
        assert normalized == [3, 1, 2]

    def test_normalize_value_nested(self, snapshot):
        """测试规范化嵌套值"""
        value = {"outer": {"z_inner": 1, "a_inner": 2}}
        normalized = snapshot._normalize_value(value)

        assert list(normalized["outer"].keys()) == ["a_inner", "z_inner"]

    def test_assert_match_create_new_snapshot(self, snapshot):
        """测试创建新快照"""
        test_name = "test_create"
        data = {"value": 42, "text": "hello"}

        result = snapshot.assert_match(test_name, data, update=True)

        assert result is True
        snapshot_path = snapshot._get_snapshot_path(test_name)
        assert snapshot_path.exists()

    def test_assert_match_existing_snapshot(self, snapshot):
        """测试匹配现有快照"""
        test_name = "test_match"
        data = {"value": 100, "key": "test"}

        # 创建快照
        snapshot.assert_match(test_name, data, update=True)

        # 验证匹配
        result = snapshot.assert_match(test_name, data)

        assert result is True

    def test_assert_match_mismatch(self, snapshot):
        """测试不匹配快照"""
        test_name = "test_mismatch"

        # 创建快照
        original_data = {"value": 42}
        snapshot.assert_match(test_name, original_data, update=True)

        # 测试不同数据
        different_data = {"value": 99}

        with pytest.raises(AssertionError, match="快照不匹配"):
            snapshot.assert_match(test_name, different_data)

    def test_assert_match_with_metadata(self, snapshot):
        """测试带元数据的快照"""
        test_name = "test_metadata"
        data = {"result": "success"}

        metadata = SnapshotMetadata(test_name=test_name, created_at="2024-01-01", version="1.0.0", description="测试元数据")

        snapshot.assert_match(test_name, data, update=True, metadata=metadata)

        # 验证快照包含元数据
        snapshot_data = snapshot._load_snapshot(snapshot._get_snapshot_path(test_name))
        assert snapshot_data["metadata"]["version"] == "1.0.0"
        assert snapshot_data["metadata"]["description"] == "测试元数据"

    def test_update_snapshots_batch(self, snapshot):
        """测试批量更新快照"""
        batch_data = {"test1": {"value": 1}, "test2": {"value": 2}, "test3": {"value": 3}}

        snapshot.update_snapshots(batch_data)

        assert snapshot._get_snapshot_path("test1").exists()
        assert snapshot._get_snapshot_path("test2").exists()
        assert snapshot._get_snapshot_path("test3").exists()

    def test_list_snapshots(self, snapshot):
        """测试列出快照"""
        # 创建几个快照
        for i in range(3):
            snapshot.assert_match(f"test_{i}", {"value": i}, update=True)

        snapshots = snapshot.list_snapshots()

        assert len(snapshots) == 3
        assert "test_0" in snapshots
        assert "test_1" in snapshots
        assert "test_2" in snapshots

    def test_remove_snapshot(self, snapshot):
        """测试移除快照"""
        test_name = "test_remove"

        # 创建快照
        snapshot.assert_match(test_name, {"value": 1}, update=True)
        assert snapshot._get_snapshot_path(test_name).exists()

        # 移除快照
        result = snapshot.remove_snapshot(test_name)

        assert result is True
        assert not snapshot._get_snapshot_path(test_name).exists()

    def test_remove_nonexistent_snapshot(self, snapshot):
        """测试移除不存在的快照"""
        result = snapshot.remove_snapshot("nonexistent")
        assert result is False

    def test_clear_snapshots(self, snapshot):
        """测试清除所有快照"""
        # 创建多个快照
        for i in range(5):
            snapshot.assert_match(f"test_{i}", {"value": i}, update=True)

        assert len(snapshot.list_snapshots()) == 5

        # 清除所有快照
        snapshot.clear_snapshots()

        assert len(snapshot.list_snapshots()) == 0


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__, "-v"])
