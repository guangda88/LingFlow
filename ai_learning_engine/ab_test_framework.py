"""
A/B测试框架

用于对比优化前后的效果，确保优化措施的有效性。
"""

import json
import logging
import math
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class TestGroup:
    """测试组"""
    name: str
    group_type: str  # 'control' or 'treatment'
    file_paths: List[str]
    metrics: Dict[str, Any] = field(default_factory=dict)
    application_log: List[str] = field(default_factory=list)


@dataclass
class ABTestConfig:
    """A/B测试配置"""
    test_id: str
    name: str
    description: str
    control_ratio: float = 0.5  # 控制组比例
    treatment_ratio: float = 0.5  # 实验组比例
    min_sample_size: int = 100  # 最小样本量
    confidence_level: float = 0.95  # 置信度
    duration_hours: int = 24  # 测试持续时间
    random_seed: Optional[int] = None
    stratify_by: List[str] = field(default_factory=list)  # 分层变量
    metrics_to_track: List[str] = field(default_factory=list)


@dataclass
class TestMetric:
    """测试指标"""
    name: str
    value: float
    unit: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTestResult:
    """A/B测试结果"""
    test_id: str
    config: ABTestConfig
    start_time: datetime
    end_time: Optional[datetime] = None
    control_group: TestGroup = field(default_factory=TestGroup)
    treatment_group: TestGroup = field(default_factory=TestGroup)
    statistical_significance: float = 0.0
    p_value: float = 1.0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    improvement_rate: float = 0.0
    is_significant: bool = False
    recommendation: str = ""
    notes: List[str] = field(default_factory=list)


class ABTestFramework:
    """A/B测试框架"""

    def __init__(self, data_dir: str = "./ab_test_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.active_tests = {}
        self.test_history = []

    def create_ab_test(self, config: ABTestConfig) -> str:
        """创建A/B测试"""
        # 验证配置
        if not self._validate_config(config):
            raise ValueError("Invalid A/B test configuration")

        # 设置随机种子
        if config.random_seed:
            random.seed(config.random_seed)
            np.random.seed(config.random_seed)

        # 生成测试ID
        if not config.test_id:
            config.test_id = f"ab_{int(time.time())}"

        # 保存配置
        config_file = self.data_dir / f"{config.test_id}_config.json"
        with open(config_file, 'w') as f:
            json.dump({
                'test_id': config.test_id,
                'config': config.__dict__,
                'created_at': datetime.now().isoformat()
            }, f, indent=2)

        # 注册测试
        self.active_tests[config.test_id] = config

        logger.info(f"Created A/B test: {config.test_id} - {config.name}")
        return config.test_id

    def _validate_config(self, config: ABTestConfig) -> bool:
        """验证配置"""
        if config.control_ratio + config.treatment_ratio != 1.0:
            return False
        if config.min_sample_size < 10:
            return False
        if not 0 < config.confidence_level < 1:
            return False
        if config.duration_hours <= 0:
            return False
        return True

    def assign_groups(self, test_id: str, file_paths: List[str],
                     metadata: Dict[str, Any] = None) -> Dict[str, List[str]]:
        """分配文件到测试组"""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")

        config = self.active_tests[test_id]
        metadata = metadata or {}

        # 如果需要分层，先按分层变量分组
        if config.stratify_by:
            stratified_groups = self._stratify_files(file_paths, config.stratify_by, metadata)
            assignments = {}

            for stratum, stratum_files in stratified_groups.items():
                stratum_assignment = self._random_assignment(stratum_files, config)
                for group_name, files in stratum_assignment.items():
                    if group_name not in assignments:
                        assignments[group_name] = []
                    assignments[group_name].extend(files)

        else:
            # 随机分配
            assignments = self._random_assignment(file_paths, config)

        # 记录分配结果
        assignment_file = self.data_dir / f"{test_id}_assignment.json"
        with open(assignment_file, 'w') as f:
            json.dump({
                'test_id': test_id,
                'assignment': assignments,
                'metadata': metadata,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)

        logger.info(f"Assigned {len(file_paths)} files to test {test_id}")
        return assignments

    def _stratify_files(self, file_paths: List[str], stratify_by: List[str],
                       metadata: Dict[str, Any]) -> Dict[str, List[str]]:
        """按分层变量分组文件"""
        stratified = defaultdict(list)

        for file_path in file_paths:
            # 获取分层键
            stratification_key = []
            for key in stratify_by:
                if key in metadata:
                    stratification_key.append(str(metadata[key][file_path]))
                else:
                    # 如果没有指定分层变量，使用文件特征
                    file_size = Path(file_path).stat().st_size
                    stratification_key.append(f"size_{file_size // 1024}KB")

            strat_key = "|".join(stratification_key)
            stratified[strat_key].append(file_path)

        return dict(stratified)

    def _random_assignment(self, file_paths: List[str], config: ABTestConfig) -> Dict[str, List[str]]:
        """随机分配文件到组"""
        # 随机打乱文件列表
        shuffled_files = file_paths.copy()
        random.shuffle(shuffled_files)

        # 计算各组大小
        total_files = len(shuffled_files)
        control_size = int(total_files * config.control_ratio)
        treatment_size = total_files - control_size

        # 分配文件
        assignments = {
            'control': shuffled_files[:control_size],
            'treatment': shuffled_files[control_size:]
        }

        return assignments

    def apply_treatment(self, test_id: str, treatment_func: Callable):
        """对实验组应用处理"""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")

        # 获取分配文件
        assignment_file = self.data_dir / f"{test_id}_assignment.json"
        if not assignment_file.exists():
            raise ValueError(f"No assignment found for test {test_id}")

        with open(assignment_file, 'r') as f:
            assignment_data = json.load(f)
            treatment_files = assignment_data['assignment']['treatment']

        # 应用处理
        logger.info(f"Applying treatment to {len(treatment_files)} files")

        results = []
        for file_path in treatment_files:
            try:
                result = treatment_func(file_path)
                results.append({
                    'file': file_path,
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'file': file_path,
                    'success': False,
                    'error': str(e)
                })

        # 保存应用结果
        treatment_file = self.data_dir / f"{test_id}_treatment_results.json"
        with open(treatment_file, 'w') as f:
            json.dump({
                'test_id': test_id,
                'results': results,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)

    def collect_metrics(self, test_id: str, metric_func: Callable,
                       group: str = 'both') -> Dict[str, List[TestMetric]]:
        """收集指标数据"""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")

        metrics = {'control': [], 'treatment': []}

        # 获取分配文件
        assignment_file = self.data_dir / f"{test_id}_assignment.json"
        with open(assignment_file, 'r') as f:
            assignment_data = json.load(f)

        # 收集控制组指标
        if group in ['control', 'both']:
            for file_path in assignment_data['assignment']['control']:
                try:
                    metric_value = metric_func(file_path)
                    metrics['control'].append(TestMetric(
                        name='quality_score',
                        value=metric_value,
                        file_path=file_path
                    ))
                except Exception as e:
                    logger.warning(f"Failed to collect metric for {file_path}: {e}")

        # 收集实验组指标
        if group in ['treatment', 'both']:
            for file_path in assignment_data['assignment']['treatment']:
                try:
                    metric_value = metric_func(file_path)
                    metrics['treatment'].append(TestMetric(
                        name='quality_score',
                        value=metric_value,
                        file_path=file_path
                    ))
                except Exception as e:
                    logger.warning(f"Failed to collect metric for {file_path}: {e}")

        # 保存指标数据
        metrics_file = self.data_dir / f"{test_id}_metrics.json"
        with open(metrics_file, 'w') as f:
            metrics_data = {
                'test_id': test_id,
                'control_metrics': [
                    {
                        'value': m.value,
                        'timestamp': m.timestamp.isoformat(),
                        'file_path': m.file_path
                    } for m in metrics['control']
                ],
                'treatment_metrics': [
                    {
                        'value': m.value,
                        'timestamp': m.timestamp.isoformat(),
                        'file_path': m.file_path
                    } for m in metrics['treatment']
                ],
                'timestamp': datetime.now().isoformat()
            }
            json.dump(metrics_data, f, indent=2)

        return metrics

    def analyze_results(self, test_id: str) -> ABTestResult:
        """分析A/B测试结果"""
        if test_id not in self.active_tests:
            raise ValueError(f"Test {test_id} not found")

        config = self.active_tests[test_id]

        # 加载指标数据
        metrics_file = self.data_dir / f"{test_id}_metrics.json"
        if not metrics_file.exists():
            raise ValueError(f"No metrics found for test {test_id}")

        with open(metrics_file, 'r') as f:
            metrics_data = json.load(f)

        # 提取指标值
        control_values = [m['value'] for m in metrics_data['control_metrics']]
        treatment_values = [m['value'] for m in metrics_data['treatment_metrics']]

        # 检查样本量
        if len(control_values) < config.min_sample_size or len(treatment_values) < config.min_sample_size:
            raise ValueError(f"Sample size too small. Control: {len(control_values)}, Treatment: {len(treatment_values)}")

        # 计算统计指标
        control_mean = np.mean(control_values)
        treatment_mean = np.mean(treatment_values)
        improvement_rate = (treatment_mean - control_mean) / control_mean if control_mean != 0 else 0

        # 执行统计检验
        statistic, p_value = stats.ttest_ind(control_values, treatment_values)
        is_significant = p_value < (1 - config.confidence_level)

        # 计算置信区间
        pooled_std = np.sqrt((np.var(control_values) + np.var(treatment_values)) / 2)
        margin_of_error = stats.t.ppf(config.confidence_level, len(control_values) + len(treatment_values) - 2) * pooled_std * np.sqrt(1/len(control_values) + 1/len(treatment_values))
        ci_lower = improvement_rate - margin_of_error
        ci_upper = improvement_rate + margin_of_error

        # 生成推荐
        recommendation = self._generate_recommendation(is_significant, improvement_rate, p_value)

        # 创建结果对象
        result = ABTestResult(
            test_id=test_id,
            config=config,
            start_time=datetime.fromisoformat(metrics_data.get('timestamp', datetime.now().isoformat()).split('Z')[0]),
            end_time=datetime.now(),
            statistical_significance=config.confidence_level,
            p_value=p_value,
            confidence_interval=(ci_lower, ci_upper),
            improvement_rate=improvement_rate,
            is_significant=is_significant,
            recommendation=recommendation,
            notes=[
                f"Control mean: {control_mean:.3f}",
                f"Treatment mean: {treatment_mean:.3f}",
                f"Sample sizes: {len(control_values)}, {len(treatment_values)}"
            ]
        )

        # 保存结果
        result_file = self.data_dir / f"{test_id}_result.json"
        with open(result_file, 'w') as f:
            json.dump(result.__dict__, f, indent=2, default=str)

        # 添加到历史记录
        self.test_history.append(result)

        logger.info(f"A/B test {test_id} completed")
        logger.info(f"Improvement: {improvement_rate:.2%}, p-value: {p_value:.4f}")
        logger.info(f"Recommendation: {recommendation}")

        return result

    def _generate_recommendation(self, is_significant: bool, improvement_rate: float, p_value: float) -> str:
        """生成测试建议"""
        if not is_significant:
            return "测试结果不显著，需要更多数据或重新设计实验"

        if improvement_rate > 0.1:  # 10%以上改善
            if p_value < 0.01:
                return "强烈建议采用该优化措施，效果显著且改善明显"
            else:
                return "建议采用该优化措施，有一定改善效果"
        elif improvement_rate > 0.05:  # 5-10%改善
            return "可以考虑采用该优化措施，有一定改善效果"
        elif improvement_rate > 0:  # 0-5%改善
            return "优化措施有轻微改善，可根据成本考虑是否采用"
        else:
            return "优化措施没有带来改善，不建议采用"

    def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """获取测试状态"""
        if test_id not in self.active_tests:
            return {'status': 'not_found'}

        config = self.active_tests[test_id]

        # 检查是否有结果
        result_file = self.data_dir / f"{test_id}_result.json"
        if result_file.exists():
            with open(result_file, 'r') as f:
                result_data = json.load(f)
                return {
                    'status': 'completed',
                    'config': config.__dict__,
                    'result': result_data
                }

        # 检查是否超时
        start_time = datetime.now() - timedelta(hours=config.duration_hours)
        if datetime.now() > start_time:
            return {
                'status': 'timeout',
                'config': config.__dict__
            }

        return {
            'status': 'running',
            'config': config.__dict__
        }

    def get_test_history(self, limit: int = 10) -> List[ABTestResult]:
        """获取测试历史"""
        return self.test_history[-limit:]

    def run_predefined_experiment(self, file_paths: List[str], treatment_func: Callable,
                               metric_func: Callable) -> ABTestResult:
        """运行预定义实验"""
        # 创建测试配置
        config = ABTestConfig(
            test_id=f"experiment_{int(time.time())}",
            name="Optimization Experiment",
            description="Test optimization effectiveness",
            control_ratio=0.5,
            treatment_ratio=0.5,
            min_sample_size=50,
            confidence_level=0.95
        )

        # 创建测试
        test_id = self.create_ab_test(config)

        # 分组
        assignments = self.assign_groups(test_id, file_paths)

        # 应用处理
        self.apply_treatment(test_id, treatment_func)

        # 收集指标
        metrics = self.collect_metrics(test_id, metric_func)

        # 分析结果
        result = self.analyze_results(test_id)

        return result


class MetricsCalculator:
    """指标计算器"""

    @staticmethod
    def calculate_code_quality_metrics(file_path: str) -> float:
        """计算代码质量分数"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # 简化的质量计算
            lines = content.split('\n')
            total_lines = len(lines)
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            empty_lines = sum(1 for line in lines if not line.strip())

            # 计算函数数量
            function_count = content.count('def ')
            class_count = content.count('class ')

            # 计算复杂度（简化）
            complexity = 1
            for line in lines:
                if any(keyword in line for keyword in ['if ', 'for ', 'while ', 'try:']):
                    complexity += 1

            # 质量分数计算
            if total_lines == 0:
                return 0.0

            comment_ratio = comment_lines / total_lines
            empty_ratio = empty_lines / total_lines
            complexity_ratio = complexity / total_lines

            score = (
                comment_ratio * 0.3 +          # 注释权重
                (1 - empty_ratio) * 0.2 +      # 空行权重
                min(function_count / 10, 1) * 0.2 +  # 函数数量权重
                min(class_count / 5, 1) * 0.2 +      # 类数量权重
                (1 - complexity_ratio) * 0.1   # 复杂度权重
            )

            return min(score * 100, 100.0)

        except Exception as e:
            logger.warning(f"Failed to calculate metrics for {file_path}: {e}")
            return 0.0

    @staticmethod
    def calculate_performance_metrics(file_path: str) -> float:
        """计算性能指标"""
        # 这里可以添加具体的性能计算逻辑
        # 例如：执行时间、内存使用等
        return 50.0  # 简化实现


if __name__ == '__main__':
    # 示例使用
    framework = ABTestFramework()

    # 创建测试
    config = ABTestConfig(
        test_id="test_optimization",
        name="Code Optimization Test",
        description="Test the effectiveness of code optimization rules",
        control_ratio=0.5,
        treatment_ratio=0.5,
        min_sample_size=20,
        confidence_level=0.95
    )

    test_id = framework.create_ab_test(config)

    # 模拟文件列表
    test_files = [f"test_file_{i}.py" for i in range(40)]

    # 定义处理函数
    def optimize_file(file_path):
        """模拟文件优化"""
        # 这里可以实际的优化逻辑
        return f"Optimized {file_path}"

    def calculate_metrics(file_path):
        """模拟指标计算"""
        import random
        return random.uniform(60, 100)  # 模拟质量分数

    # 分组
    assignments = framework.assign_groups(test_id, test_files)

    # 应用处理
    framework.apply_treatment(test_id, optimize_file)

    # 收集指标
    metrics = framework.collect_metrics(test_id, calculate_metrics)

    # 分析结果
    result = framework.analyze_results(test_id)

    print(f"\nA/B测试结果:")
    print(f"测试ID: {result.test_id}")
    print(f"改善率: {result.improvement_rate:.2%}")
    print(f"P值: {result.p_value:.4f}")
    print(f"是否显著: {result.is_significant}")
    print(f"置信区间: {result.confidence_interval}")
    print(f"建议: {result.recommendation}")