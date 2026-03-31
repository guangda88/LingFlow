"""
参数存储和缓存测试

YOLO测试：快速验证核心功能
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from lingflow.self_optimizer.phase4.storage import (
    FileSystemParameterStore,
    get_default_store,
    save_params,
    load_params,
    get_latest_params
)
from lingflow.self_optimizer.phase4.cache import (
    ParameterCache,
    CachedParameterStore
)
from lingflow.self_optimizer.phase4.data_types import ParameterVersion


class TestFileSystemParameterStore:
    """测试文件系统存储"""

    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.store = FileSystemParameterStore(self.temp_dir)

    def teardown_method(self):
        """清理测试环境"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_save_and_load(self):
        """测试保存和加载"""
        params = {"temperature": 0.7, "top_p": 0.9, "max_tokens": 100}
        metadata = {"score": 0.85, "project": "test"}

        # 保存
        version = self.store.save(params, metadata, project="test")
        assert version is not None
        assert version.params == params
        assert version.checksum is not None

        # 加载
        loaded = self.store.load(version.version_id)
        assert loaded is not None
        assert loaded.params == params
        assert loaded.metadata == metadata
        assert loaded.version_id == version.version_id

    def test_find_by_params(self):
        """测试根据参数查找"""
        params = {"temperature": 0.7, "top_p": 0.9}
        version = self.store.save(params, project="test")

        # 查找
        found = self.store.find_by_params(params)
        assert found is not None
        assert found.version_id == version.version_id

        # 不同参数应该找不到
        not_found = self.store.find_by_params({"temperature": 0.5})
        assert not_found is None

    def test_list_versions(self):
        """测试列出版本"""
        for i in range(3):
            params = {"value": i}
            self.store.save(params, project="test")

        versions = self.store.list_versions(project="test")
        assert len(versions) == 3
        # 应该按时间倒序
        assert versions[0].params["value"] > versions[-1].params["value"]

    def test_get_latest(self):
        """测试获取最新版本"""
        self.store.save({"value": 1}, project="test")
        self.store.save({"value": 2}, project="test")

        latest = self.store.get_latest("test")
        assert latest is not None
        assert latest.params["value"] == 2

    def test_delete(self):
        """测试删除"""
        version = self.store.save({"value": 1}, project="test")
        assert self.store.load(version.version_id) is not None

        # 删除
        assert self.store.delete(version.version_id) is True
        assert self.store.load(version.version_id) is None

    def test_cleanup_old_versions(self):
        """测试清理旧版本"""
        for i in range(5):
            self.store.save({"value": i}, project="test")

        # 保留2个
        count = self.store.cleanup_old_versions("test", keep=2)
        assert count == 3

        # 只剩2个
        versions = self.store.list_versions(project="test")
        assert len(versions) == 2

    def test_get_stats(self):
        """测试获取统计"""
        self.store.save({"value": 1}, project="proj1")
        self.store.save({"value": 2}, project="proj2")

        stats = self.store.get_stats()
        assert stats["total_versions"] == 2
        assert "proj1" in stats["projects"]
        assert "proj2" in stats["projects"]


class TestParameterCache:
    """测试参数缓存"""

    def test_put_and_get(self):
        """测试放入和获取"""
        cache = ParameterCache(max_size=10)
        version = ParameterVersion(
            version_id="test_1",
            params={"temp": 0.7},
            metadata={}
        )

        cache.put("key1", version)
        assert cache.get("key1") == version
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self):
        """测试LRU淘汰"""
        cache = ParameterCache(max_size=3)

        for i in range(4):
            version = ParameterVersion(
                version_id=f"v{i}",
                params={"value": i},
                metadata={}
            )
            cache.put(f"key{i}", version)

        # 应该只有3个，第一个被淘汰
        assert len(cache) == 3
        assert cache.get("key0") is None
        assert cache.get("key1") is not None

    def test_hit_rate(self):
        """测试命中率"""
        cache = ParameterCache()
        version = ParameterVersion(
            version_id="test",
            params={"x": 1},
            metadata={}
        )

        cache.put("key", version)

        # 命中
        cache.get("key")
        # 未命中
        cache.get("miss")

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestCachedParameterStore:
    """测试带缓存的存储"""

    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        store = FileSystemParameterStore(self.temp_dir)
        self.cached_store = CachedParameterStore(store, cache_size=10)

    def teardown_method(self):
        """清理测试环境"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_cache_hit(self):
        """测试缓存命中"""
        params = {"temp": 0.7}
        version = self.cached_store.save(params, project="test")

        # 第一次加载，从存储
        v1 = self.cached_store.load(version.version_id, "test")
        # 第二次加载，从缓存
        v2 = self.cached_store.load(version.version_id, "test")

        assert v1.version_id == v2.version_id

        stats = self.cached_store.get_cache_stats()
        # 应该有缓存
        assert stats["size"] >= 1

    def test_cache_invalidation(self):
        """测试缓存失效"""
        params = {"temp": 0.7}
        version = self.cached_store.save(params, project="test")

        # 加载进缓存
        self.cached_store.load(version.version_id, "test")
        assert self.cached_store.get_cache_stats()["size"] >= 1

        # 使缓存失效
        self.cached_store.invalidate(version.version_id, "test")

        # 清理后应该减少
        self.cached_store.cleanup_cache()


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_save_and_load(self):
        """测试保存和加载"""
        params = {"test": 1}
        version = save_params(params, project="test")
        assert version is not None

        loaded = load_params(version.version_id)
        assert loaded is not None
        assert loaded.params == params

    def test_get_latest(self):
        """测试获取最新"""
        save_params({"v": 1}, project="test")
        save_params({"v": 2}, project="test")

        latest = get_latest_params("test")
        assert latest is not None
        assert latest.params["v"] == 2


if __name__ == "__main__":
    # 快速运行测试
    pytest.main([__file__, "-v", "-x"])
