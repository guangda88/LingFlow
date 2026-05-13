"""
lingflow Phase 4: 核心数据类型定义

包含所有优化相关的数据类和枚举类型。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class OptimizationGoal(Enum):
    """优化目标类型"""

    STRUCTURE = "structure"
    PERFORMANCE = "performance"
    SIMPLICITY = "simplicity"
    ALL = "all"


class MetricType(Enum):
    """评估指标类型"""

    STRUCTURE = "structure"
    PERFORMANCE = "performance"
    SIMPLICITY = "simplicity"
    QUALITY = "quality"


class ParameterType(Enum):
    """参数类型"""

    CATEGORICAL = "categorical"  # 离散类别
    INT = "int"  # 整数范围
    FLOAT = "float"  # 浮点范围
    LOG = "log"  # 对数尺度


@dataclass
class SearchSpace:
    """搜索空间定义"""

    name: str
    type: ParameterType
    # 对于categorical: choices
    # 对于int/float: min, max, step (可选)
    # 对于log: base, min, max
    choices: Optional[List[Any]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    base: Optional[float] = None

    def validate(self) -> bool:
        """验证搜索空间定义"""
        if self.type == ParameterType.CATEGORICAL:
            return self.choices is not None and len(self.choices) > 0
        elif self.type in (ParameterType.INT, ParameterType.FLOAT):
            return self.min is not None and self.max is not None and self.min < self.max
        elif self.type == ParameterType.LOG:
            return self.min is not None and self.max is not None and self.base is not None
        return False


@dataclass
class OptimizationRequest:
    """优化请求"""

    # 目标配置
    target_path: str
    goal: str  # structure, performance, simplicity, all

    # 搜索空间
    search_space: Dict[str, Dict[str, Any]]

    # 约束
    constraints: Dict[str, Any] = field(default_factory=dict)

    # 配置
    max_time: float = 120  # 秒
    max_trials: int = 50
    early_stopping: bool = True
    enable_cache: bool = True
    enable_transfer: bool = True

    # 元数据
    project_name: str = "default"
    experiment_name: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.experiment_name is None:
            self.experiment_name = f"{self.project_name}_{self.goal}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@dataclass
class OptimizationTrial:
    """优化试验记录"""

    trial_id: str
    params: Dict[str, Any]
    score: float
    metrics: Dict[str, float]
    timestamp: float
    converged: bool = False
    duration: float = 0.0


@dataclass
class OptimizationResult:
    """优化结果"""

    # 最佳参数
    best_params: Dict[str, Any]
    best_score: float

    # 统计
    n_trials: int
    total_time: float

    # 历史记录
    trials: List[Dict[str, Any]]

    # 收敛信息
    converged: bool
    convergence_rate: float

    # 敏感性分析
    sensitivities: Optional[Dict[str, float]] = None

    # Pareto前沿（多目标）
    pareto_front: Optional[List[Dict[str, Any]]] = None

    # 错误信息
    error: Optional[str] = None

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_improvement(self, baseline_score: float) -> float:
        """计算相对于基线的改进"""
        if baseline_score == 0:
            return 0.0
        return (baseline_score - self.best_score) / baseline_score

    def get_summary(self) -> str:
        """获取结果摘要"""
        lines = [
            "优化结果摘要",
            "=" * 40,
            f"最佳分数: {self.best_score:.4f}",
            f"试验次数: {self.n_trials}",
            f"总耗时: {self.total_time:.2f}秒",
            f"收敛状态: {'是' if self.converged else '否'}",
            f"收敛率: {self.convergence_rate:.2%}",
            "",
            "最佳参数:",
        ]
        for key, value in sorted(self.best_params.items()):
            lines.append(f"  {key}: {value}")

        if self.sensitivities:
            lines.extend(["", "参数敏感性:"])
            for param, sensitivity in sorted(self.sensitivities.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {param}: {sensitivity:.3f}")

        return "\n".join(lines)


@dataclass
class Metric:
    """评估指标"""

    name: str
    value: float
    type: MetricType
    weight: float = 1.0
    higher_is_better: bool = False

    def get_weighted_value(self) -> float:
        """获取加权值"""
        if not self.higher_is_better:
            return self.value * self.weight
        return -self.value * self.weight  # 负值用于最小化


@dataclass
class EvaluationResult:
    """评估结果"""

    metrics: Dict[str, Metric]
    overall_score: float
    converged: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_metric(self, name: str) -> Optional[Metric]:
        """获取特定指标"""
        return self.metrics.get(name)

    def get_metrics_by_type(self, metric_type: MetricType) -> List[Metric]:
        """按类型获取指标"""
        return [m for m in self.metrics.values() if m.type == metric_type]


@dataclass
class ParameterVersion:
    """参数版本"""

    version_id: str
    params: Dict[str, Any]
    metadata: Dict[str, Any]
    parent_version: Optional[str] = None
    created_at: Optional[datetime] = None
    checksum: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ConvergenceInfo:
    """收敛信息"""

    converged: bool
    convergence_rate: float
    window_size: int
    threshold: float
    n_trials: int

    def get_status_message(self) -> str:
        """获取状态消息"""
        if self.converged:
            return f"已收敛 (收敛率: {self.convergence_rate:.2%})"
        return f"优化中... (收敛率: {self.convergence_rate:.2%})"


@dataclass
class SensitivityResult:
    """敏感性分析结果"""

    sensitivities: Dict[str, float]
    method: str
    n_samples: int
    base_params: Dict[str, Any]

    def get_ranking(self) -> List[tuple]:
        """获取敏感性排名"""
        return sorted(self.sensitivities.items(), key=lambda x: x[1], reverse=True)

    def get_top_sensitive(self, n: int = 5) -> List[tuple]:
        """获取最敏感的前N个参数"""
        return self.get_ranking()[:n]


@dataclass
class TransferResult:
    """知识迁移结果"""

    transferred: bool
    source_project: Optional[str]
    target_project: str
    params: Optional[Dict[str, Any]]
    similarity: float
    confidence: float

    def get_summary(self) -> str:
        """获取摘要"""
        if self.transferred:
            return (
                f"参数迁移成功\n"
                f"  源项目: {self.source_project}\n"
                f"  相似度: {self.similarity:.2%}\n"
                f"  置信度: {self.confidence:.2%}"
            )
        return "参数迁移失败：未找到足够相似的项目"


@dataclass
class ComparisonResult:
    """A/B测试比较结果"""

    params_a: Dict[str, Any]
    params_b: Dict[str, Any]
    mean_a: float
    mean_b: float
    improvement: float
    p_value: float
    significant: bool
    winner: str
    confidence_level: float

    def get_summary(self) -> str:
        """获取摘要"""
        sig_marker = "***" if self.significant else "ns"
        return (
            f"A/B测试结果\n"
            f"{'=' * 40}\n"
            f"方案A平均分: {self.mean_a:.4f}\n"
            f"方案B平均分: {self.mean_b:.4f}\n"
            f"改进幅度: {self.improvement:.2%}\n"
            f"P值: {self.p_value:.4f} {sig_marker}\n"
            f"显著差异: {'是' if self.significant else '否'}\n"
            f"推荐方案: {self.winner.upper()}"
        )
