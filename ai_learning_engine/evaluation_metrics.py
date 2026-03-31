"""
评估指标模块

定义Phase 4-5系统的各种评估指标，用于量化优化效果和系统性能。
"""

import ast
import time
import psutil
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指标类型"""
    CODE_QUALITY = "code_quality"        # 代码质量
    PERFORMANCE = "performance"          # 性能
    RELIABILITY = "reliability"          # 可靠性
    MAINTAINABILITY = "maintainability"  # 可维护性
    SECURITY = "security"                # 安全性
    USER_EXPERIENCE = "user_experience" # 用户体验


@dataclass
class CodeQualityMetrics:
    """代码质量指标"""
    cyclomatic_complexity: float = 0.0      # 平均圈复杂度
    cognitive_complexity: float = 0.0      # 认知复杂度
    lines_of_code: int = 0                  # 代码行数
    comment_ratio: float = 0.0             # 注释率
    function_count: int = 0                 # 函数数量
    class_count: int = 0                   # 类数量
    average_function_length: float = 0.0    # 平均函数长度
    coupling_degree: float = 0.0           # 耦合度
    cohesion_degree: float = 0.0           # 内聚度
    technical_debt_ratio: float = 0.0      # 技术债务比例

    def calculate_overall_score(self) -> float:
        """计算总体质量分数"""
        weights = {
            'cyclomatic_complexity': 0.2,
            'cognitive_complexity': 0.15,
            'comment_ratio': 0.1,
            'average_function_length': 0.15,
            'coupling_degree': 0.2,
            'cohesion_degree': 0.1,
            'technical_debt_ratio': 0.1
        }

        # 标准化指标（假设理想值）
        normalized = {
            'cyclomatic_complexity': max(0, (10 - self.cyclomatic_complexity) / 10),
            'cognitive_complexity': max(0, (15 - self.cognitive_complexity) / 15),
            'comment_ratio': min(self.comment_ratio / 0.3, 1.0),  # 30%注释率为理想
            'average_function_length': max(0, (50 - self.average_function_length) / 50),
            'coupling_degree': max(0, (5 - self.coupling_degree) / 5),
            'cohesion_degree': min(self.cohesion_degree, 1.0),
            'technical_debt_ratio': max(0, (1 - self.technical_debt_ratio))
        }

        score = sum(
            normalized[key] * weight
            for key, weight in weights.items()
        )

        return round(score * 100, 2)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    execution_time: float = 0.0              # 执行时间
    memory_usage: float = 0.0               # 内存使用
    cpu_usage: float = 0.0                  # CPU使用率
    response_time: float = 0.0              # 响应时间
    throughput: float = 0.0                 # 吞吐量
    error_rate: float = 0.0                 # 错误率
    cache_hit_ratio: float = 0.0           # 缓存命中率
    garbage_collections: int = 0           # 垃圾回收次数
    thread_count: int = 0                   # 线程数
    disk_io: float = 0.0                    # 磁盘IO

    def calculate_overall_score(self) -> float:
        """计算总体性能分数"""
        # 标准化指标
        normalized = {
            'execution_time': max(0, 1 - (self.execution_time / 1000)),  # 假设1秒为基准
            'memory_usage': max(0, 1 - (self.memory_usage / (1024 * 1024 * 1024))),  # 1GB为基准
            'cpu_usage': max(0, 1 - (self.cpu_usage / 100)),
            'response_time': max(0, 1 - (self.response_time / 1000)),  # 1秒为基准
            'throughput': min(self.throughput / 100, 1.0),  # 100 QPS为基准
            'error_rate': max(0, 1 - self.error_rate),
            'cache_hit_ratio': self.cache_hit_ratio,
            'garbage_collections': max(0, 1 - (self.garbage_collections / 100)),
            'disk_io': max(0, 1 - (self.disk_io / (1024 * 1024)))  # 1MB为基准
        }

        # 不同指标权重
        weights = {
            'execution_time': 0.2,
            'memory_usage': 0.15,
            'cpu_usage': 0.15,
            'response_time': 0.15,
            'throughput': 0.15,
            'error_rate': 0.1,
            'cache_hit_ratio': 0.05,
            'garbage_collections': 0.03,
            'disk_io': 0.02
        }

        score = sum(
            normalized[key] * weight
            for key, weight in weights.items()
        )

        return round(score * 100, 2)


@dataclass
class RuleApplicationMetrics:
    """规则应用指标"""
    total_applied: int = 0                   # 总应用次数
    successful_applications: int = 0         # 成功应用次数
    failed_applications: int = 0            # 失败应用次数
    average_application_time: float = 0.0   # 平均应用时间
    rules_count: int = 0                     # 规则数量
    coverage_rate: float = 0.0               # 覆盖率
    rollback_rate: float = 0.0               # 回滚率
    manual_review_rate: float = 0.0          # 人工审核率
    rule_quality_score: float = 0.0          # 规则质量分数
    user_satisfaction_score: float = 0.0     # 用户满意度

    def calculate_overall_score(self) -> float:
        """计算总体应用分数"""
        success_rate = self.successful_applications / max(self.total_applied, 1)
        coverage_quality = min(self.coverage_rate, 1.0)
        quality_score = self.rule_quality_score / 100 if self.rule_quality_score <= 100 else 1.0

        weights = {
            'success_rate': 0.3,
            'coverage_rate': 0.2,
            'rule_quality': 0.25,
            'rollback_rate': 0.15,  # 越低越好
            'manual_review_rate': 0.1  # 越低越好（自动化程度）
        }

        score = (
            success_rate * weights['success_rate'] +
            coverage_quality * weights['coverage_rate'] +
            quality_score * weights['rule_quality'] +
            (1 - self.rollback_rate) * weights['rollback_rate'] +
            (1 - self.manual_review_rate) * weights['manual_review_rate']
        )

        return round(score * 100, 2)


@dataclass
class IntegrationMetrics:
    """工具集成指标"""
    tools_connected: int = 0                # 已连接工具数
    tools_total: int = 0                    # 总工具数
    average_response_time: float = 0.0      # 平均响应时间
    data_sync_success_rate: float = 0.0     # 数据同步成功率
    api_error_rate: float = 0.0            # API错误率
    tool_reliability: Dict[str, float] = field(default_factory=dict)  # 工具可靠性
    data_quality_score: float = 0.0         # 数据质量分数
    integration_complexity: float = 0.0     # 集成复杂度

    def calculate_overall_score(self) -> float:
        """计算总体集成分数"""
        connection_rate = self.tools_connected / max(self.tools_total, 1)
        reliability = sum(self.tool_reliability.values()) / len(self.tool_reliability) if self.tool_reliability else 0
        sync_quality = min(self.data_sync_success_rate, 1.0)
        data_quality = self.data_quality_score / 100 if self.data_quality_score <= 100 else 1.0

        weights = {
            'connection_rate': 0.2,
            'reliability': 0.3,
            'sync_success': 0.25,
            'data_quality': 0.2,
            'error_rate': 0.05  # 越低越好
        }

        score = (
            connection_rate * weights['connection_rate'] +
            reliability * weights['reliability'] +
            sync_quality * weights['sync_success'] +
            data_quality * weights['data_quality'] +
            (1 - self.api_error_rate) * weights['error_rate']
        )

        return round(score * 100, 2)


@dataclass
class EvaluationReport:
    """评估报告"""
    timestamp: datetime = field(default_factory=datetime.now)
    code_quality: CodeQualityMetrics = field(default_factory=CodeQualityMetrics)
    performance: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    rule_application: RuleApplicationMetrics = field(default_factory=RuleApplicationMetrics)
    integration: IntegrationMetrics = field(default_factory=IntegrationMetrics)
    overall_score: float = 0.0
    improvement_rate: float = 0.0
    baseline_metrics: Optional[Dict] = None
    recommendations: List[str] = field(default_factory=list)

    def calculate_overall_score(self) -> float:
        """计算总体分数"""
        weights = {
            'code_quality': 0.3,
            'performance': 0.25,
            'rule_application': 0.3,
            'integration': 0.15
        }

        scores = {
            'code_quality': self.code_quality.calculate_overall_score(),
            'performance': self.performance.calculate_overall_score(),
            'rule_application': self.rule_application.calculate_overall_score(),
            'integration': self.integration.calculate_overall_score()
        }

        self.overall_score = sum(
            scores[key] * weight
            for key, weight in weights.items()
        )

        return round(self.overall_score, 2)

    def calculate_improvement_rate(self, baseline: 'EvaluationReport') -> float:
        """计算改善率"""
        baseline_score = baseline.calculate_overall_score()
        current_score = self.calculate_overall_score()

        if baseline_score == 0:
            self.improvement_rate = 0
            return 0

        self.improvement_rate = (current_score - baseline_score) / baseline_score
        return round(self.improvement_rate, 2)


class MetricsCollector:
    """指标收集器"""

    def __init__(self, target_path: str = "."):
        self.target_path = Path(target_path)
        self.collected_metrics = {}

    def collect_code_quality_metrics(self) -> CodeQualityMetrics:
        """收集代码质量指标"""
        metrics = CodeQualityMetrics()

        # 遍历Python文件
        python_files = list(self.target_path.rglob("*.py"))
        if not python_files:
            return metrics

        total_complexity = 0
        total_cognitive = 0
        total_lines = 0
        total_comment_lines = 0
        total_functions = 0
        total_classes = 0
        total_function_length = 0
        coupling_count = 0
        cohesion_count = 0

        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    source = f.read()

                tree = ast.parse(source)

                # 分析AST
                file_lines = len(source.split('\n'))
                total_lines += file_lines

                # 统计注释
                comment_lines = sum(1 for line in source.split('\n') if line.strip().startswith('#'))
                total_comment_lines += comment_lines

                # 分析复杂度
                file_complexity, file_cognitive = self._analyze_complexity(tree)
                total_complexity += file_complexity
                total_cognitive += file_cognitive

                # 统计函数和类
                file_functions = 0
                file_classes = 0
                file_function_lengths = []

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        file_functions += 1
                        if hasattr(node, 'end_lineno') and node.end_lineno:
                            length = node.end_lineno - node.lineno + 1
                            file_function_lengths.append(length)
                    elif isinstance(node, ast.ClassDef):
                        file_classes += 1

                total_functions += file_functions
                total_classes += file_classes
                total_function_length += sum(file_function_lengths)

                # 简化的耦合度和内聚度计算
                coupling_count += len([n for n in ast.walk(tree) if isinstance(n, ast.Import or ast.ImportFrom)])
                cohesion_count += file_functions  # 简化：函数越多，内聚度越高

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")

        # 计算平均值
        if python_files:
            metrics.cyclomatic_complexity = total_complexity / len(python_files)
            metrics.cognitive_complexity = total_cognitive / len(python_files)
            metrics.lines_of_code = total_lines
            metrics.comment_ratio = total_comment_lines / total_lines if total_lines > 0 else 0
            metrics.function_count = total_functions
            metrics.class_count = total_classes
            metrics.average_function_length = total_function_length / total_functions if total_functions > 0 else 0
            metrics.coupling_degree = coupling_count / len(python_files)
            metrics.cohesion_degree = min(cohesion_count / len(python_files), 1.0)
            metrics.technical_debt_ratio = metrics.cyclomatic_complexity / 20  # 假设20为技术债务阈值

        return metrics

    def _analyze_complexity(self, tree: ast.AST) -> Tuple[float, float]:
        """分析代码复杂度"""
        cyclomatic = 1  # 基础复杂度
        cognitive = 0

        for node in ast.walk(tree):
            # 圈复杂度
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                cyclomatic += 1
            elif isinstance(node, ast.BoolOp):
                cyclomatic += len(node.values) - 1

            # 认知复杂度（简化版本）
            if isinstance(node, ast.If):
                cognitive += 1
            elif isinstance(node, ast.For):
                cognitive += 1
            elif isinstance(node, ast.While):
                cognitive += 2
            elif isinstance(node, ast.Try):
                cognitive += 2

        return cyclomatic, cognitive

    def collect_performance_metrics(self) -> PerformanceMetrics:
        """收集性能指标"""
        metrics = PerformanceMetrics()

        # 获取当前进程信息
        process = psutil.Process()

        # CPU使用率
        metrics.cpu_usage = process.cpu_percent()

        # 内存使用
        memory_info = process.memory_info()
        metrics.memory_usage = memory_info.rss / (1024 * 1024)  # MB

        # 磁盘IO（简化）
        disk_io = process.io_counters()
        metrics.disk_io = disk_io.read_bytes + disk_io.write_bytes

        # 这里可以添加更多的性能收集逻辑

        return metrics

    def create_evaluation_report(self, baseline: Optional[EvaluationReport] = None) -> EvaluationReport:
        """创建评估报告"""
        report = EvaluationReport(
            code_quality=self.collect_code_quality_metrics(),
            performance=self.collect_performance_metrics(),
            # 其他指标需要外部数据填充
        )

        # 计算总体分数
        report.calculate_overall_score()

        # 计算改善率（如果有基线）
        if baseline:
            report.calculate_improvement_rate(baseline)
            report.baseline_metrics = {
                'overall_score': baseline.overall_score,
                'code_quality': baseline.code_quality.calculate_overall_score(),
                'performance': baseline.performance.calculate_overall_score()
            }

        # 生成建议
        report.recommendations = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: EvaluationReport) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 代码质量建议
        if report.code_quality.cyclomatic_complexity > 10:
            recommendations.append("平均圈复杂度过高，建议重构复杂的函数")

        if report.code_quality.comment_ratio < 0.1:
            recommendations.append("注释率较低，建议增加必要的文档")

        # 性能建议
        if report.performance.memory_usage > 500:  # 500MB
            recommendations.append("内存使用较高，建议检查内存泄漏")

        if report.performance.cpu_usage > 80:  # 80%
            recommendations.append("CPU使用率过高，建议优化算法")

        return recommendations


def main():
    """测试评估指标系统"""
    collector = MetricsCollector(target_path="/home/ai/LingFlow")
    baseline = EvaluationReport()  # 假设有基线数据

    # 创建评估报告
    report = collector.create_evaluation_report(baseline)

    # 输出结果
    print("=== 评估报告 ===")
    print(f"总体分数: {report.overall_score:.2f}")
    print(f"改善率: {report.improvement_rate:.2%}")

    print(f"\n代码质量分数: {report.code_quality.calculate_overall_score():.2f}")
    print(f"性能分数: {report.performance.calculate_overall_score():.2f}")

    print("\n建议:")
    for rec in report.recommendations:
        print(f"- {rec}")


if __name__ == '__main__':
    main()