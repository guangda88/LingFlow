#!/usr/bin/env python3
"""性能基准测试

测量优化前后的性能差异。
"""

import time
import sys
import os

# Add lingflow to path
sys.path.insert(0, '/home/ai/LingFlow')

from lingflow.common.config import ConfigManager, get_config


def benchmark_config_lookup(iterations=10000):
    """测试配置查找性能"""
    print("\n" + "="*60)
    print("配置查找性能测试")
    print("="*60)

    config = ConfigManager()

    # Warm up
    for _ in range(100):
        config.get("workflow.max_iterations")

    # Benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        config.get("workflow.max_iterations")
        config.get("skills.default_timeout")
        config.get("agents.default_agents")
        config.get("compression.enabled")
        config.get("workflow.sleep_interval")
    end = time.perf_counter()

    total_time = end - start
    avg_time = (total_time / iterations) * 1000000  # microseconds
    ops_per_second = iterations / total_time

    print(f"\n测试迭代次数: {iterations:,}")
    print(f"总耗时: {total_time:.4f} 秒")
    print(f"平均单次查找: {avg_time:.2f} 微秒")
    print(f"吞吐量: {ops_per_second:,.0f} 操作/秒")

    # Test cache effectiveness
    print("\n缓存效果测试:")
    print(f"缓存键数量: {len(config._cache)}")
    cached_keys = list(config._cache.keys())
    print(f"缓存键示例: {cached_keys[:5]}")

    # Test with different default values
    start = time.perf_counter()
    for _ in range(1000):
        config.get("nonexistent.key", default=1)
        config.get("nonexistent.key", default=2)
        config.get("nonexistent.key", default=3)
    end = time.perf_counter()

    print(f"\n默认值测试 (1000次×3个不同默认值): {end-start:.4f} 秒")
    print(f"  验证: 缓存不会缓存默认值，避免冲突")


def benchmark_config_set(iterations=1000):
    """测试配置设置性能（包括缓存失效）"""
    print("\n" + "="*60)
    print("配置设置性能测试（含缓存失效）")
    print("="*60)

    config = ConfigManager()

    # Benchmark
    start = time.perf_counter()
    for i in range(iterations):
        config.set("workflow.max_iterations", 100 + i % 50)
        config.set("skills.default_timeout", 30 + i % 10)
        config.set("compression.max_length", 10000 + i % 5000)
    end = time.perf_counter()

    total_time = end - start
    avg_time = (total_time / iterations) * 1000000  # microseconds

    print(f"\n测试迭代次数: {iterations:,}")
    print(f"总耗时: {total_time:.4f} 秒")
    print(f"平均单次设置: {avg_time:.2f} 微秒")
    print(f"  包含缓存失效操作")

    # Test cache invalidation
    print(f"\n缓存无效化测试:")
    print(f"  设置后缓存键数量: {len(config._cache)}")
    config.get("workflow.max_iterations")
    print(f"  重新获取后缓存键数量: {len(config._cache)} (应不为空)")


def benchmark_memory_usage():
    """测试内存使用情况"""
    print("\n" + "="*60)
    print("内存使用情况")
    print("="*60)

    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Measure after imports
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Create config and populate cache
        from lingflow.common.config import ConfigManager
        config = ConfigManager()

        # Populate cache
        for i in range(100):
            config.get(f"workflow.{i}", default=i)
            config.get(f"skills.{i}", default=i)
            config.get(f"agents.{i}", default=i)

        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before

        print(f"\n初始内存: {memory_before:.2f} MB")
        print(f"缓存后内存: {memory_after:.2f} MB")
        print(f"内存增加: {memory_increase:.2f} MB")
        print(f"缓存项数: {len(config._cache)}")
        print(f"  平均每项: {(memory_increase/len(config._cache))*1024:.2f} KB" if config._cache else "  无缓存")

    except ImportError:
        print("\npsutil 未安装，跳过内存测试")


def benchmark_test_suite():
    """运行完整测试套件"""
    print("\n" + "="*60)
    print("测试套件性能")
    print("="*60)

    import subprocess

    print("\n运行 pytest (仅测量，不输出详细结果)...")
    start = time.perf_counter()
    result = subprocess.run(
        ["python", "-m", "pytest", "-q", "--tb=no"],
        cwd="/home/ai/LingFlow",
        capture_output=True,
        text=True
    )
    end = time.perf_counter()

    total_time = end - start

    # Parse results
    output_lines = result.stdout.strip().split('\n')
    result_line = output_lines[-1] if output_lines else ""

    print(f"\n总耗时: {total_time:.2f} 秒")
    print(f"测试结果: {result_line}")
    print(f"退出码: {result.returncode}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("LingFlow 性能基准测试")
    print("版本: 3.5.7 (优化后)")
    print("="*60)

    # Run benchmarks
    benchmark_config_lookup(10000)
    benchmark_config_set(1000)
    benchmark_memory_usage()

    # Optional: Run full test suite (commented out by default)
    # benchmark_test_suite()

    print("\n" + "="*60)
    print("性能测试完成")
    print("="*60)
