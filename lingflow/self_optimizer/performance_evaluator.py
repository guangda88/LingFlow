"""
LingFlow 性能评估器
评估代码性能指标
"""

import time
import psutil
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float      # 执行时间（秒）
    memory_usage_mb: float     # 内存使用（MB）
    cpu_percent: float         # CPU使用率
    io_operations: int         # IO操作次数
    cache_hit_rate: float      # 缓存命中率


class PerformanceEvaluator:
    """性能评估器"""

    def __init__(self, target_path: str = "."):
        """
        Args:
            target_path: 目标代码路径
        """
        self.target_path = Path(target_path)
        self.process = psutil.Process()

    def evaluate(self, params: Dict[str, Any]) -> float:
        """评估性能质量（用于LingMinOpt）

        Args:
            params: 优化参数
                - cache_size: 缓存大小
                - parallelism: 并行度
                - timeout: 超时时间

        Returns:
            性能分数（越低越好）
        """
        # 1. 测量导入时间
        import_time = self._measure_import_time()

        # 2. 测量内存使用
        memory_mb = self._measure_memory_usage()

        # 3. 计算分数
        # 执行时间权重更高
        score = (
            import_time * 10.0 +  # 执行时间
            memory_mb * 0.1       # 内存使用
        )

        return float(score)

    def _measure_import_time(self) -> float:
        """测量导入时间"""
        start_time = time.time()

        # 尝试导入目标模块
        try:
            # 如果是包，尝试导入
            if (self.target_path / "__init__.py").exists():
                # 动态导入
                import sys
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "target_module",
                    self.target_path / "__init__.py"
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
        except Exception:
            pass

        return time.time() - start_time

    def _measure_memory_usage(self) -> float:
        """测量内存使用"""
        try:
            # 获取当前进程内存
            mem_info = self.process.memory_info()
            return mem_info.rss / (1024 * 1024)  # 转换为MB
        except Exception:
            return 0.0

    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        # 测量导入时间
        execution_time = self._measure_import_time()

        # 测量内存
        memory_mb = self._measure_memory_usage()

        # CPU使用率
        cpu_percent = self._get_cpu_percent()

        # 文件数量（作为IO复杂度代理）
        file_count = len(list(self.target_path.rglob("*.py")))

        return {
            "execution_time": execution_time,
            "memory_usage_mb": memory_mb,
            "cpu_percent": cpu_percent,
            "python_files": file_count,
        }

    def _get_cpu_percent(self) -> float:
        """获取CPU使用率"""
        try:
            return self.process.cpu_percent(interval=0.1)
        except Exception:
            return 0.0

    def benchmark_function(self, func: callable, *args, **kwargs) -> Dict[str, Any]:
        """基准测试函数性能

        Args:
            func: 要测试的函数
            *args, **kwargs: 函数参数

        Returns:
            性能指标字典
        """
        # 预热
        for _ in range(3):
            try:
                func(*args, **kwargs)
            except:
                pass

        # 多次运行
        times = []
        memory_samples = []

        for _ in range(10):
            # 测量时间
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                result = e
            elapsed = time.time() - start_time
            times.append(elapsed)

            # 测量内存
            memory_mb = self._measure_memory_usage()
            memory_samples.append(memory_mb)

        # 统计
        import statistics

        return {
            "execution_time_mean": statistics.mean(times),
            "execution_time_median": statistics.median(times),
            "execution_time_std": statistics.stdev(times) if len(times) > 1 else 0,
            "memory_usage_mb_mean": statistics.mean(memory_samples),
            "memory_usage_mb_max": max(memory_samples),
            "samples": len(times),
        }


def fallback_evaluate(params: Dict[str, Any], target_path: str = ".") -> float:
    """降级评估函数（无LingMinOpt时）

    Args:
        params: 优化参数
        target_path: 目标路径

    Returns:
        评分（越低越好）
    """
    evaluator = PerformanceEvaluator(target_path)
    return evaluator.evaluate(params)


if __name__ == "__main__":
    # 测试
    evaluator = PerformanceEvaluator("/home/ai/LingFlow/lingflow")

    params = {
        "cache_size": 100,
        "parallelism": 2,
        "timeout": 30
    }

    score = evaluator.evaluate(params)
    print(f"性能评分: {score:.2f}")

    metrics = evaluator.get_current_metrics()
    print(f"当前指标: {metrics}")
