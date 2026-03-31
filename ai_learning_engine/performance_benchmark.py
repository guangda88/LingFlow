"""
性能基准测试系统

用于评估和监控系统的性能指标，确保优化措施不会引入性能问题。
"""

import ast
import gc
import logging
import multiprocessing
import os
import time
import tracemalloc
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple
import psutil
import numpy as np
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float = 0.0        # 执行时间（秒）
    memory_peak: float = 0.0          # 内存峰值（MB）
    memory_current: float = 0.0       # 当前内存（MB）
    cpu_percent: float = 0.0          # CPU使用率（%）
    disk_io_read: float = 0.0         # 磁盘读取（MB）
    disk_io_write: float = 0.0        # 磁盘写入（MB）
    context_switches: int = 0         # 上下文切换次数
    thread_count: int = 0             # 线程数
    gc_count: int = 0                 # 垃圾回收次数
    throughput: float = 0.0           # 吞吐量（操作/秒）
    response_time_avg: float = 0.0     # 平均响应时间（ms）
    response_time_p95: float = 0.0    # P95响应时间（ms）
    response_time_p99: float = 0.0    # P99响应时间（ms）
    error_rate: float = 0.0           # 错误率（%）
    cpu_user: float = 0.0             # 用户态CPU时间
    cpu_system: float = 0.0           # 系统态CPU时间

    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_time': self.execution_time,
            'memory_peak': self.memory_peak,
            'memory_current': self.memory_current,
            'cpu_percent': self.cpu_percent,
            'disk_io_read': self.disk_io_read,
            'disk_io_write': self.disk_io_write,
            'context_switches': self.context_switches,
            'thread_count': self.thread_count,
            'gc_count': self.gc_count,
            'throughput': self.throughput,
            'response_time_avg': self.response_time_avg,
            'response_time_p95': self.response_time_p95,
            'response_time_p99': self.response_time_p99,
            'error_rate': self.error_rate,
            'cpu_user': self.cpu_user,
            'cpu_system': self.cpu_system
        }


@dataclass
class BenchmarkConfig:
    """基准测试配置"""
    name: str
    description: str
    iterations: int = 10
    warmup_iterations: int = 3
    timeout_seconds: int = 300
    threads: int = 1
    processes: int = 0
    memory_limit_mb: int = 0
    cpu_limit_percent: int = 0
    enable_profiling: bool = False
    collect_gc_stats: bool = True
    collect_memory_profile: bool = True


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    config: BenchmarkConfig
    metrics: PerformanceMetrics
    timestamp: datetime
    status: str = "completed"  # completed, failed, timeout
    error_message: Optional[str] = None
    raw_data: List[Dict[str, Any]] = field(default_factory=list)
    comparison: Optional[Dict[str, Any]] = None


class PerformanceProfiler:
    """性能分析器"""

    def __init__(self):
        self.process = psutil.Process()

    def start_profiling(self):
        """开始性能分析"""
        tracemalloc.start()
        self.process.cpu_percent(interval=None)
        gc.enable()
        gc.set_threshold(700, 10, 10)

    def stop_profiling(self) -> Dict[str, Any]:
        """停止性能分析并返回结果"""
        memory_current = tracemalloc.get_traced_memory()[1] / (1024 * 1024)  # MB
        tracemalloc.stop()

        # 获取进程信息
        memory_info = self.process.memory_info()
        cpu_percent = self.process.cpu_percent(interval=0.1)
        io_counters = self.process.io_counters()
        num_threads = self.process.num_threads()
        num_ctx_switches = self.process.num_ctx_switches()

        return {
            'memory_current': memory_current,
            'memory_peak': memory_info.rss / (1024 * 1024),
            'cpu_percent': cpu_percent,
            'disk_io_read': io_counters.read_bytes / (1024 * 1024),
            'disk_io_write': io_counters.write_bytes / (1024 * 1024),
            'thread_count': num_threads,
            'context_switches': num_ctx_switches,
            'gc_count': gc.get_count()
        }


class BenchmarkRunner:
    """基准测试运行器"""

    def __init__(self, results_dir: str = "./benchmark_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.profiler = PerformanceProfiler()

    def run_benchmark(self, config: BenchmarkConfig, benchmark_func: Callable,
                     *args, **kwargs) -> BenchmarkResult:
        """运行基准测试"""
        logger.info(f"Starting benchmark: {config.name}")

        # 准备结果
        metrics = PerformanceMetrics()
        raw_data = []
        start_time = time.time()

        try:
            # 预热
            for i in range(config.warmup_iterations):
                benchmark_func(*args, **kwargs)

            # 正式运行
            execution_times = []
            memory_samples = []

            for i in range(config.iterations):
                iteration_start = time.time()

                # 开始分析
                self.profiler.start_profiling()

                # 执行测试函数
                try:
                    result = benchmark_func(*args, **kwargs)
                    execution_times.append(time.time() - iteration_start)
                except Exception as e:
                    logger.error(f"Iteration {i} failed: {e}")
                    execution_times.append(config.timeout_seconds)
                    continue
                finally:
                    # 停止分析
                    profile_data = self.profiler.stop_profiling()
                    memory_samples.append(profile_data['memory_current'])

                    # 收集数据
                    raw_data.append({
                        'iteration': i + 1,
                        'execution_time': execution_times[-1],
                        'memory': profile_data
                    })

            # 计算最终指标
            self._calculate_metrics(metrics, execution_times, memory_samples, config)

            status = "completed"

        except Exception as e:
            status = "failed"
            metrics.execution_time = time.time() - start_time
            logger.error(f"Benchmark failed: {e}")

        result = BenchmarkResult(
            config=config,
            metrics=metrics,
            timestamp=datetime.now(),
            status=status,
            error_message=str(e) if status == "failed" else None,
            raw_data=raw_data
        )

        # 保存结果
        self._save_result(result)

        logger.info(f"Benchmark completed: {config.name}")
        return result

    def _calculate_metrics(self, metrics: PerformanceMetrics, execution_times: List[float],
                          memory_samples: List[float], config: BenchmarkConfig):
        """计算性能指标"""
        # 执行时间
        metrics.execution_time = np.mean(execution_times)
        metrics.throughput = 1.0 / metrics.execution_time if metrics.execution_time > 0 else 0

        # 内存
        metrics.memory_peak = max(memory_samples) if memory_samples else 0
        metrics.memory_current = memory_samples[-1] if memory_samples else 0

        # CPU (基于执行时间和线程数估算)
        total_cpu_time = metrics.execution_time * config.threads * 100  # 百分秒
        metrics.cpu_percent = (total_cpu_time / config.iterations) / 100

        # 响应时间
        if len(execution_times) > 0:
            metrics.response_time_avg = np.mean(execution_times) * 1000  # ms
            sorted_times = sorted(execution_times)
            metrics.response_time_p95 = sorted_times[int(len(sorted_times) * 0.95)] * 1000
            metrics.response_time_p99 = sorted_times[int(len(sorted_times) * 0.99)] * 1000

    def _save_result(self, result: BenchmarkResult):
        """保存测试结果"""
        timestamp = result.timestamp.strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"benchmark_{result.config.name}_{timestamp}.json"

        with open(result_file, 'w') as f:
            json.dump({
                'name': result.config.name,
                'description': result.config.description,
                'timestamp': result.timestamp.isoformat(),
                'status': result.status,
                'error_message': result.error_message,
                'metrics': result.metrics.to_dict(),
                'raw_data': result.raw_data,
                'comparison': result.comparison
            }, f, indent=2)


class BenchmarkSuite:
    """基准测试套件"""

    def __init__(self, runner: BenchmarkRunner):
        self.runner = runner
        self.test_cases = []
        self.baseline_results = {}

    def add_test_case(self, name: str, description: str, func: Callable, config: BenchmarkConfig):
        """添加测试用例"""
        self.test_cases.append({
            'name': name,
            'description': description,
            'func': func,
            'config': config
        })

    def run_all_tests(self) -> List[BenchmarkResult]:
        """运行所有测试"""
        results = []
        for test_case in self.test_cases:
            result = self.runner.run_benchmark(test_case['config'], test_case['func'])
            results.append(result)

        # 生成比较报告
        self._generate_comparison_report(results)

        return results

    def create_baseline(self, test_name: str, result: BenchmarkResult):
        """创建基线"""
        self.baseline_results[test_name] = result
        logger.info(f"Created baseline for {test_name}")

    def compare_with_baseline(self, test_name: str, current_result: BenchmarkResult) -> Dict[str, Any]:
        """与基线比较"""
        if test_name not in self.baseline_results:
            return {'error': 'Baseline not found'}

        baseline = self.baseline_results[test_name]
        return self._compare_results(baseline, current_result)

    def _compare_results(self, baseline: BenchmarkResult, current: BenchmarkResult) -> Dict[str, Any]:
        """比较两个结果"""
        comparison = {
            'test_name': baseline.config.name,
            'baseline_metrics': baseline.metrics.to_dict(),
            'current_metrics': current.metrics.to_dict(),
            'differences': {},
            'regressions': [],
            'improvements': []
        }

        baseline_metrics = baseline.metrics.to_dict()
        current_metrics = current.metrics.to_dict()

        # 比较每个指标
        for key in baseline_metrics:
            baseline_val = baseline_metrics[key]
            current_val = current_metrics[key]
            difference = current_val - baseline_val

            # 计算百分比变化
            if baseline_val != 0:
                percent_change = (difference / baseline_val) * 100
            else:
                percent_change = 0 if difference == 0 else 100

            comparison['differences'][key] = {
                'baseline': baseline_val,
                'current': current_val,
                'difference': difference,
                'percent_change': percent_change
            }

            # 检测回归（性能下降超过10%）
            if key in ['execution_time', 'memory_peak', 'cpu_percent', 'response_time_p95']:
                if percent_change > 10:
                    comparison['regressions'].append({
                        'metric': key,
                        'change': percent_change,
                        'severity': 'HIGH' if percent_change > 30 else 'MEDIUM'
                    })

            # 检测改进（性能提升超过10%）
            elif key in ['throughput'] and percent_change < -10:
                comparison['improvements'].append({
                    'metric': key,
                    'change': percent_change,
                    'severity': 'HIGH' if percent_change < -30 else 'MEDIUM'
                })

        return comparison

    def _generate_comparison_report(self, results: List[BenchmarkResult]):
        """生成比较报告"""
        for result in results:
            if result.config.name in self.baseline_results:
                comparison = self.compare_with_baseline(result.config.name, result)
                result.comparison = comparison


class PerformanceBenchmarkSuite:
    """性能基准测试套件"""

    def __init__(self):
        self.runner = BenchmarkRunner()
        self.suite = BenchmarkSuite(self.runner)

    def create_default_benchmarks(self):
        """创建默认基准测试"""
        # 代码分析性能测试
        self.add_code_analysis_benchmark()

        # AI学习引擎性能测试
        self.add_learning_engine_benchmark()

        # 规则应用性能测试
        self.add_rule_application_benchmark()

        # 系统资源使用测试
        self.add_resource_usage_benchmark()

    def add_code_analysis_benchmark(self):
        """添加代码分析基准测试"""
        def analyze_large_file():
            """模拟分析大文件"""
            # 创建一个大的Python文件
            large_code = []
            for i in range(1000):
                large_code.append(f"def function_{i}():")
                large_code.append(f"    # Comment {i}")
                large_code.append(f"    return {i}")
            large_code.append("")

            # 模拟AST分析
            code = '\n'.join(large_code)
            try:
                ast.parse(code)
            except:
                pass

        config = BenchmarkConfig(
            name="code_analysis",
            description="Test code analysis performance",
            iterations=10,
            warmup_iterations=3
        )

        self.suite.add_test_case(
            "Code Analysis Performance",
            "Measure time to parse and analyze large Python files",
            analyze_large_file,
            config
        )

    def add_learning_engine_benchmark(self):
        """添加学习引擎基准测试"""
        def simulate_learning_process():
            """模拟学习过程"""
            # 模拟从反馈中学习
            feedback_data = []
            for i in range(100):
                feedback_data.append({
                    'tool': 'SonarQube',
                    'rule_id': f'S{i:04d}',
                    'message': f'Issue {i}',
                    'file': f'file_{i}.py'
                })

            # 模拟规则提取
            rules = []
            for item in feedback_data:
                rules.append({
                    'id': item['rule_id'],
                    'name': f'Rule {item["rule_id"]}',
                    'score': 0.8
                })

            # 模拟规则验证
            for rule in rules:
                if rule['score'] > 0.7:
                    rule['validated'] = True

        config = BenchmarkConfig(
            name="learning_engine",
            description="Test AI learning engine performance",
            iterations=5,
            warmup_iterations=2
        )

        self.suite.add_test_case(
            "Learning Engine Performance",
            "Measure time for rule extraction and validation",
            simulate_learning_process,
            config
        )

    def add_rule_application_benchmark(self):
        """添加规则应用基准测试"""
        def apply_rules_to_files():
            """模拟规则应用到多个文件"""
            files = []
            for i in range(50):
                files.append(f"temp_file_{i}.py")

            # 模拟规则应用
            for file_path in files:
                # 模拟文件操作
                with open(file_path, 'w') as f:
                    f.write("# Test file\n")
                    f.write("def test_function():\n")
                    f.write("    return 'test'\n")

                # 模拟文件处理
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    # 模拟应用规则
                    modified = content.replace('test', 'optimized')
                    with open(file_path, 'w') as f:
                        f.write(modified)
                except:
                    pass

                # 清理临时文件
                try:
                    os.remove(file_path)
                except:
                    pass

        config = BenchmarkConfig(
            name="rule_application",
            description="Test rule application performance",
            iterations=5,
            warmup_iterations=2
        )

        self.suite.add_test_case(
            "Rule Application Performance",
            "Measure time to apply optimization rules to multiple files",
            apply_rules_to_files,
            config
        )

    def add_resource_usage_benchmark(self):
        """添加资源使用基准测试"""
        def intensive_task():
            """执行密集型任务"""
            # 模拟CPU密集型任务
            result = 0
            for i in range(1000000):
                result += i * i
            return result

        config = BenchmarkConfig(
            name="resource_usage",
            description="Test system resource usage",
            iterations=5,
            warmup_iterations=2,
            enable_profiling=True
        )

        self.suite.add_test_case(
            "Resource Usage",
            "Measure CPU and memory usage for intensive operations",
            intensive_task,
            config
        )

    def add_test_case(self, name: str, description: str, func: Callable, config: BenchmarkConfig):
        """添加测试用例"""
        self.suite.add_test_case(name, description, func, config)

    def run_benchmarks(self) -> List[BenchmarkResult]:
        """运行所有基准测试"""
        print("Running performance benchmarks...")
        results = self.suite.run_all_tests()

        # 打印结果摘要
        print("\n=== Benchmark Results ===")
        for result in results:
            metrics = result.metrics
            print(f"\n{result.config.name}:")
            print(f"  Execution Time: {metrics.execution_time:.2f}s")
            print(f"  Memory Peak: {metrics.memory_peak:.2f}MB")
            print(f"  Throughput: {metrics.throughput:.2f} ops/s")

            if result.comparison:
                regressions = len(result.comparison.get('regressions', []))
                improvements = len(result.comparison.get('improvements', []))
                print(f"  Regressions: {regressions}")
                print(f"  Improvements: {improvements}")

        return results

    def create_performance_report(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """创建性能报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(results),
            'average_execution_time': np.mean([r.metrics.execution_time for r in results]),
            'average_memory_usage': np.mean([r.metrics.memory_peak for r in results]),
            'total_throughput': sum([r.metrics.throughput for r in results]),
            'test_results': []
        }

        for result in results:
            test_data = {
                'name': result.config.name,
                'metrics': result.metrics.to_dict(),
                'status': result.status,
                'comparison': result.comparison
            }
            report['test_results'].append(test_data)

        # 保存报告
        report_file = self.runner.results_dir / "performance_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def detect_performance_regression(self, test_name: str, current_result: BenchmarkResult) -> Dict[str, Any]:
        """检测性能回归"""
        if test_name not in self.suite.baseline_results:
            return {'error': 'No baseline found'}

        baseline = self.suite.baseline_results[test_name]
        comparison = self.suite._compare_results(baseline, current_result)

        # 生成回归报告
        regression_report = {
            'test_name': test_name,
            'baseline_timestamp': baseline.timestamp.isoformat(),
            'current_timestamp': current_result.timestamp.isoformat(),
            'regressions': comparison['regressions'],
            'improvements': comparison['improvements'],
            'recommendations': self._generate_regression_recommendations(comparison)
        }

        return regression_report

    def _generate_regression_recommendations(self, comparison: Dict[str, Any]) -> List[str]:
        """生成回归建议"""
        recommendations = []

        regressions = comparison['regressions']
        if regressions:
            for regression in regressions:
                if regression['severity'] == 'HIGH':
                    recommendations.append(f"严重性能回归检测到: {regression['metric']} 恶化了 {regression['change']:.1f}%")
                else:
                    recommendations.append(f"性能回归: {regression['metric']} 恶化了 {regression['change']:.1f}%")

        improvements = comparison['improvements']
        if improvements:
            recommendations.append(f"发现 {len(improvements)} 个性能改进")

        if not regressions and not improvements:
            recommendations.append("性能指标与基线一致")

        return recommendations


def create_visualization(results: List[BenchmarkResult]):
    """创建性能可视化"""
    # 创建图表目录
    viz_dir = Path("./visualizations")
    viz_dir.mkdir(exist_ok=True)

    # 准备数据
    test_names = [r.config.name for r in results]
    execution_times = [r.metrics.execution_time for r in results]
    memory_usage = [r.metrics.memory_peak for r in results]

    # 执行时间对比图
    plt.figure(figsize=(10, 6))
    bars = plt.bar(test_names, execution_times)
    plt.title('Execution Time Comparison')
    plt.ylabel('Time (seconds)')
    plt.xticks(rotation=45, ha='right')

    # 在柱状图上添加数值
    for bar, time in zip(bars, execution_times):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{time:.2f}s',
                ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(viz_dir / 'execution_time.png')
    plt.close()

    # 内存使用对比图
    plt.figure(figsize=(10, 6))
    bars = plt.bar(test_names, memory_usage)
    plt.title('Memory Usage Comparison')
    plt.ylabel('Memory (MB)')
    plt.xticks(rotation=45, ha='right')

    for bar, mem in zip(bars, memory_usage):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{mem:.1f}MB',
                ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig(viz_dir / 'memory_usage.png')
    plt.close()

    logger.info(f"Visualizations saved to {viz_dir}")


if __name__ == '__main__':
    # 创建性能基准测试套件
    benchmark_suite = PerformanceBenchmarkSuite()

    # 添加默认基准测试
    benchmark_suite.create_default_benchmarks()

    # 运行基准测试
    results = benchmark_suite.run_benchmarks()

    # 创建性能报告
    report = benchmark_suite.create_performance_report(results)

    # 生成可视化
    create_visualization(results)

    # 创建基线（如果需要）
    if not benchmark_suite.suite.baseline_results:
        for result in results:
            benchmark_suite.suite.create_baseline(result.config.name, result)

    print("\nPerformance benchmark completed successfully!")
    print(f"Report saved to: {benchmark_suite.runner.results_dir}")