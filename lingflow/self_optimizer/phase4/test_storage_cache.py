#!/usr/bin/env python
"""
lingflow Phase 4: 参数存储和缓存测试

验证参数持久化存储和缓存机制的功能。
"""

import logging
import shutil
import sys
import tempfile

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_storage_save_and_load():
    """测试存储的保存和加载功能"""
    print("\n" + "=" * 60)
    print("测试存储保存和加载")
    print("=" * 60)

    from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore

    # 创建临时目录
    temp_dir = tempfile.mkdtemp()

    try:
        # 创建存储实例
        store = FileSystemParameterStore(base_path=temp_dir)

        # 测试数据
        params = {"learning_rate": 0.001, "batch_size": 32, "optimizer": "adam"}
        metadata = {"description": "Test parameters", "author": "test"}

        # 保存参数
        version = store.save(params=params, metadata=metadata, project="test_project", parent=None)

        print("\n保存的版本:")
        print(f"  版本ID: {version.version_id}")
        print(f"  校验和: {version.checksum}")
        print(f"  参数: {version.params}")

        # 加载参数
        loaded_version = store.load(version.version_id)

        assert loaded_version is not None, "加载的版本不应为None"
        assert loaded_version.version_id == version.version_id, "版本ID应该匹配"
        assert loaded_version.params == params, "参数应该匹配"
        assert loaded_version.metadata == metadata, "元数据应该匹配"
        assert loaded_version.checksum == version.checksum, "校验和应该匹配"

        print("\n✓ 存储保存和加载测试通过")
        return True

    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_storage_version_history():
    """测试版本历史链功能"""
    print("\n" + "=" * 60)
    print("测试版本历史链")
    print("=" * 60)

    from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore

    temp_dir = tempfile.mkdtemp()

    try:
        store = FileSystemParameterStore(base_path=temp_dir)

        # 创建版本链: v1 -> v2 -> v3
        v1 = store.save(params={"x": 1}, metadata={"version": 1}, project="test_history")

        v2 = store.save(params={"x": 2}, metadata={"version": 2}, project="test_history", parent=v1.version_id)

        v3 = store.save(params={"x": 3}, metadata={"version": 3}, project="test_history", parent=v2.version_id)

        # 获取历史链
        history = store.get_history(v3.version_id)

        assert len(history) == 3, f"历史链应该有3个版本，实际有{len(history)}个"
        assert history[0].version_id == v3.version_id, "第一个应该是v3"
        assert history[1].version_id == v2.version_id, "第二个应该是v2"
        assert history[2].version_id == v1.version_id, "第三个应该是v1"

        print("\n版本历史链:")
        for i, version in enumerate(history):
            print(f"  {i + 1}. {version.version_id}: x={version.params['x']}")

        print("\n✓ 版本历史链测试通过")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_storage_list_and_filter():
    """测试列出版本和过滤功能"""
    print("\n" + "=" * 60)
    print("测试列出版本和过滤")
    print("=" * 60)

    from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore

    temp_dir = tempfile.mkdtemp()

    try:
        store = FileSystemParameterStore(base_path=temp_dir)

        # 保存多个版本
        versions = []
        for i in range(5):
            version = store.save(
                params={"value": i}, metadata={"index": i}, project=f"project_{i % 2}"  # 交替使用project_0和project_1
            )
            versions.append(version)

        # 列出所有版本
        all_versions = store.list_versions(limit=10)
        assert len(all_versions) == 5, f"应该有5个版本，实际有{len(all_versions)}个"

        # 按项目过滤
        project_0_versions = store.list_versions(project="project_0")
        assert len(project_0_versions) == 3, "project_0应该有3个版本"

        # 获取最新版本
        latest = store.get_latest(project="project_0")
        assert latest is not None, "应该有最新版本"

        print("\n版本列表:")
        for version in all_versions:
            print(f"  {version.version_id}: value={version.params['value']}")

        print(f"\nproject_0的版本数: {len(project_0_versions)}")
        print(f"最新版本: {latest.version_id if latest else 'None'}")

        print("\n✓ 列出版本和过滤测试通过")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_storage_delete():
    """测试删除功能"""
    print("\n" + "=" * 60)
    print("测试删除功能")
    print("=" * 60)

    from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore

    temp_dir = tempfile.mkdtemp()

    try:
        store = FileSystemParameterStore(base_path=temp_dir)

        # 保存版本
        version = store.save(params={"test": 1}, project="test_delete")

        # 确认存在
        loaded = store.load(version.version_id)
        assert loaded is not None, "版本应该存在"

        # 删除版本
        result = store.delete(version.version_id)
        assert result is True, "删除应该成功"

        # 确认已删除
        loaded = store.load(version.version_id)
        assert loaded is None, "版本应该已删除"

        print("\n✓ 删除功能测试通过")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_storage_checkpoints():
    """测试检查点功能（使用版本作为检查点）"""
    print("\n" + "=" * 60)
    print("测试检查点功能（使用版本作为检查点）")
    print("=" * 60)

    from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore

    temp_dir = tempfile.mkdtemp()

    try:
        store = FileSystemParameterStore(base_path=temp_dir)

        # 使用save方法保存检查点
        checkpoint_version = store.save(
            params={"epoch": 100, "loss": 0.01}, metadata={"status": "completed", "type": "checkpoint"}, project="checkpoints"
        )

        print(f"\n保存的检查点版本: {checkpoint_version.version_id}")

        # 加载检查点
        checkpoint = store.load(checkpoint_version.version_id)
        assert checkpoint is not None, "检查点应该存在"
        assert checkpoint.params["epoch"] == 100, "参数应该匹配"
        assert checkpoint.metadata["status"] == "completed", "元数据应该匹配"

        print(f"检查点数据: epoch={checkpoint.params['epoch']}, loss={checkpoint.params['loss']}")

        # 删除检查点
        result = store.delete(checkpoint_version.version_id)
        assert result is True, "删除检查点应该成功"

        # 确认已删除
        checkpoint = store.load(checkpoint_version.version_id)
        assert checkpoint is None, "检查点应该已删除"

        print("\n✓ 检查点功能测试通过")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_storage_stats():
    """测试统计信息功能"""
    print("\n" + "=" * 60)
    print("测试统计信息")
    print("=" * 60)

    from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore

    temp_dir = tempfile.mkdtemp()

    try:
        store = FileSystemParameterStore(base_path=temp_dir)

        # 保存一些版本
        for i in range(10):
            store.save(params={"index": i}, project="test_stats")

        # 获取统计信息
        stats = store.get_stats()

        print("\n存储统计:")
        print(f"  总版本数: {stats['total_versions']}")
        print(f"  项目列表: {stats['projects']}")
        print(f"  存储路径: {stats['storage_path']}")

        assert stats["total_versions"] == 10, "应该有10个版本"
        assert "test_stats" in stats["projects"], "test_stats项目应该存在"

        print("\n✓ 统计信息测试通过")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_cache_basic_operations():
    """测试缓存基本操作"""
    print("\n" + "=" * 60)
    print("测试缓存基本操作")
    print("=" * 60)

    from datetime import datetime

    from lingflow.self_optimizer.phase4.cache import ParameterCache
    from lingflow.self_optimizer.phase4.data_types import ParameterVersion

    # 创建缓存
    cache = ParameterCache(max_size=3, ttl_seconds=60)

    # 创建测试版本
    version1 = ParameterVersion(version_id="v1", params={"x": 1}, metadata={}, created_at=datetime.now())

    version2 = ParameterVersion(version_id="v2", params={"x": 2}, metadata={}, created_at=datetime.now())

    # 测试put和get
    cache.put("key1", version1)
    cache.put("key2", version2)

    loaded1 = cache.get("key1")
    assert loaded1 is not None, "应该能获取到key1"
    assert loaded1.version_id == "v1", "版本ID应该匹配"

    # 测试miss
    loaded3 = cache.get("key3")
    assert loaded3 is None, "key3不应该存在"

    # 测试统计
    stats = cache.get_stats()
    print("\n缓存统计:")
    print(f"  大小: {stats['size']}")
    print(f"  命中次数: {stats['hits']}")
    print(f"  未命中次数: {stats['misses']}")
    print(f"  命中率: {stats['hit_rate']:.2%}")

    assert stats["size"] == 2, "缓存大小应该是2"
    assert stats["hits"] == 1, "应该有1次命中"
    assert stats["misses"] == 1, "应该有1次未命中"

    print("\n✓ 缓存基本操作测试通过")
    return True


def test_cache_lru_eviction():
    """测试LRU淘汰策略"""
    print("\n" + "=" * 60)
    print("测试LRU淘汰策略")
    print("=" * 60)

    from datetime import datetime

    from lingflow.self_optimizer.phase4.cache import ParameterCache
    from lingflow.self_optimizer.phase4.data_types import ParameterVersion

    # 创建小缓存
    cache = ParameterCache(max_size=2, ttl_seconds=60)

    # 添加3个版本
    for i in range(3):
        version = ParameterVersion(version_id=f"v{i}", params={"x": i}, metadata={}, created_at=datetime.now())
        cache.put(f"key{i}", version)

    # 第一个应该被淘汰
    v0 = cache.get("key0")
    assert v0 is None, "key0应该被LRU淘汰"

    # 后两个应该还在
    v1 = cache.get("key1")
    v2 = cache.get("key2")
    assert v1 is not None, "key1应该还存在"
    assert v2 is not None, "key2应该还存在"

    print(f"\n缓存大小: {len(cache)}")
    print(f"缓存键: {cache.keys()}")

    assert len(cache) == 2, "缓存大小应该是2"

    print("\n✓ LRU淘汰策略测试通过")
    return True


def test_cache_expiration():
    """测试缓存过期"""
    print("\n" + "=" * 60)
    print("测试缓存过期")
    print("=" * 60)

    import time
    from datetime import datetime

    from lingflow.self_optimizer.phase4.cache import ParameterCache
    from lingflow.self_optimizer.phase4.data_types import ParameterVersion

    # 创建短TTL缓存
    cache = ParameterCache(max_size=10, ttl_seconds=1)

    version = ParameterVersion(version_id="v1", params={"x": 1}, metadata={}, created_at=datetime.now())

    cache.put("key1", version)

    # 立即获取应该成功
    loaded = cache.get("key1")
    assert loaded is not None, "应该能立即获取到"

    # 等待过期
    time.sleep(1.5)

    # 过期后应该获取不到
    loaded = cache.get("key1")
    assert loaded is None, "过期后应该获取不到"

    # 清理过期条目
    expired_count = cache.cleanup_expired()
    print(f"\n清理的过期条目数: {expired_count}")

    print("\n✓ 缓存过期测试通过")
    return True


def test_cached_store():
    """测试带缓存的存储"""
    print("\n" + "=" * 60)
    print("测试带缓存的存储")
    print("=" * 60)

    from lingflow.self_optimizer.phase4.cache import CachedParameterStore
    from lingflow.self_optimizer.phase4.storage import FileSystemParameterStore

    temp_dir = tempfile.mkdtemp()

    try:
        # 创建底层存储
        store = FileSystemParameterStore(base_path=temp_dir)

        # 创建带缓存的存储
        cached_store = CachedParameterStore(store=store, cache_size=10, cache_ttl=60)

        # 保存参数
        version = cached_store.save(params={"cached": True}, project="test_project")

        print(f"\n保存的版本: {version.version_id}")

        # 第一次加载（缓存未命中）
        loaded1 = cached_store.load(version.version_id, "test_project")
        assert loaded1 is not None, "应该能加载到"

        # 第二次加载（缓存命中）
        loaded2 = cached_store.load(version.version_id, "test_project")
        assert loaded2 is not None, "应该能加载到"

        # 检查缓存统计
        cache_stats = cached_store.get_cache_stats()
        print("\n缓存统计:")
        print(f"  命中次数: {cache_stats['hits']}")
        print(f"  未命中次数: {cache_stats['misses']}")
        print(f"  命中率: {cache_stats['hit_rate']:.2%}")

        # 第一次从缓存加载（save时已添加到缓存），第二次也是从缓存
        assert cache_stats["hits"] >= 1, "至少应该有1次缓存命中"
        assert cache_stats["hit_rate"] > 0, "命中率应该大于0"

        # 使缓存失效
        cached_store.invalidate(version.version_id, "test_project")

        # 再次加载应该从存储加载
        loaded3 = cached_store.load(version.version_id, "test_project")
        assert loaded3 is not None, "应该能从存储重新加载"

        print("\n✓ 带缓存的存储测试通过")
        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("lingflow Phase 4: 存储和缓存测试套件")
    print("=" * 60)

    tests = [
        ("存储保存和加载", test_storage_save_and_load),
        ("版本历史链", test_storage_version_history),
        ("列出版本和过滤", test_storage_list_and_filter),
        ("删除功能", test_storage_delete),
        ("检查点功能", test_storage_checkpoints),
        ("统计信息", test_storage_stats),
        ("缓存基本操作", test_cache_basic_operations),
        ("LRU淘汰策略", test_cache_lru_eviction),
        ("缓存过期", test_cache_expiration),
        ("带缓存的存储", test_cached_store),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"{test_name} 测试失败: {e}", exc_info=True)
            results.append((test_name, False))

    # 输出测试摘要
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
