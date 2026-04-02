"""Workflow cache tests"""

import os
import time
import tempfile
import pytest
import yaml

from lingflow.workflow.cache import (
    CacheConfig,
    CachedWorkflow,
    WorkflowCache,
    get_workflow_cache,
)


@pytest.fixture
def tmp_yaml():
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        yaml.dump({"tasks": [{"name": "test"}]}, f)
        path = f.name
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def tmp_yaml_dir():
    with tempfile.TemporaryDirectory() as d:
        for name in ["a.yaml", "b.yaml"]:
            path = os.path.join(d, name)
            with open(path, "w") as f:
                yaml.dump({"tasks": [{"name": name}]}, f)
        yield d


class TestCachedWorkflow:
    def test_defaults(self):
        cw = CachedWorkflow(
            definition={"tasks": []},
            file_path="/tmp/test.yaml",
            mtime=1.0,
            cached_at=1.0,
            checksum="abc",
        )
        assert cw.access_count == 0


class TestCacheConfig:
    def test_defaults(self):
        cfg = CacheConfig()
        assert cfg.ttl_seconds == 300
        assert cfg.max_size == 100
        assert cfg.enable_file_watching is True
        assert cfg.checksum_enabled is True


class TestWorkflowCacheGetSet:
    def test_miss(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        result = cache.get(tmp_yaml)
        assert result is None

    def test_set_and_get(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        defn = {"tasks": [{"name": "test"}]}
        cache.set(tmp_yaml, defn)
        result = cache.get(tmp_yaml)
        assert result == defn

    def test_invalidate_specific(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        cache.set(tmp_yaml, {"tasks": []})
        cache.invalidate(tmp_yaml)
        assert cache.get(tmp_yaml) is None

    def test_invalidate_all(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        cache.set(tmp_yaml, {"tasks": []})
        cache.invalidate()
        assert cache.get(tmp_yaml) is None

    def test_ttl_expiry(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=0))
        cache.set(tmp_yaml, {"tasks": []})
        time.sleep(0.1)
        result = cache.get(tmp_yaml)
        assert result is None

    def test_file_modification_invalidates(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300, checksum_enabled=False))
        cache.set(tmp_yaml, {"tasks": []})
        time.sleep(0.05)
        with open(tmp_yaml, "w") as f:
            yaml.dump({"tasks": [{"name": "modified"}]}, f)
        result = cache.get(tmp_yaml)
        assert result is None

    def test_deleted_file_invalidates(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        cache.set(tmp_yaml, {"tasks": []})
        os.unlink(tmp_yaml)
        result = cache.get(tmp_yaml)
        assert result is None


class TestWorkflowCacheLoad:
    def test_load_from_file(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        result = cache.load(tmp_yaml)
        assert result is not None
        assert "tasks" in result

    def test_load_from_cache(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        cache.load(tmp_yaml)
        result = cache.load(tmp_yaml)
        assert result is not None

    def test_load_nonexistent(self):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        result = cache.load("/nonexistent/file.yaml")
        assert result is None


class TestWorkflowCacheStats:
    def test_stats_after_operations(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        cache.get(tmp_yaml)
        cache.set(tmp_yaml, {"tasks": []})
        cache.get(tmp_yaml)
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


class TestWorkflowCachePreload:
    def test_preload(self, tmp_yaml_dir):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        cache.preload(tmp_yaml_dir)
        stats = cache.get_stats()
        assert stats["size"] == 2

    def test_preload_nonexistent_dir(self):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300))
        cache.preload("/nonexistent/dir")
        stats = cache.get_stats()
        assert stats["size"] == 0


class TestWorkflowCacheSizeLimit:
    def test_eviction(self, tmp_yaml_dir):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300, max_size=1))
        file_a = os.path.join(tmp_yaml_dir, "a.yaml")
        file_b = os.path.join(tmp_yaml_dir, "b.yaml")
        cache.set(file_a, {"tasks": []})
        cache.set(file_b, {"tasks": []})
        stats = cache.get_stats()
        assert stats["size"] <= 1


class TestWorkflowCacheChecksum:
    def test_checksum_disabled(self, tmp_yaml):
        cache = WorkflowCache(CacheConfig(ttl_seconds=300, checksum_enabled=False))
        cache.set(tmp_yaml, {"tasks": []})
        result = cache.get(tmp_yaml)
        assert result is not None


class TestGetWorkflowCache:
    def test_singleton(self):
        c1 = get_workflow_cache()
        c2 = get_workflow_cache()
        assert c1 is c2
