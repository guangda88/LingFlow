"""情报分析器基类

定义分析器接口和通用功能。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..logging_config import get_logger
from ..models.common import (
    InfluenceScore,
    MentionData,
    SentimentResult,
    TopicCluster,
    TrendMetrics,
)

logger = get_logger(__name__)


@dataclass
class AnalyzerConfig:
    """分析器配置"""

    enabled: bool = True
    cache_results: bool = True
    output_dir: Path = Path(".lingflow/intelligence/analyzed")


class BaseAnalyzer(ABC):
    """分析器基类

    所有分析器必须继承此类并实现analyze方法。
    """

    NAME: str = "base"
    DESCRIPTION: str = ""

    def __init__(self, config: Optional[AnalyzerConfig] = None):
        """初始化分析器

        Args:
            config: 分析器配置
        """
        self.config = config or AnalyzerConfig()
        self.output_dir = self.config.output_dir / self.NAME
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def analyze(self, mentions: List[MentionData], **kwargs) -> Any:
        """分析数据

        Args:
            mentions: 提及数据列表
            **kwargs: 分析参数

        Returns:
            分析结果
        """
        pass


class AnalyzerPipeline:
    """分析器流水线

    按顺序执行多个分析器。
    """

    def __init__(self, analyzers: Optional[List[BaseAnalyzer]] = None):
        """初始化流水线

        Args:
            analyzers: 分析器列表
        """
        self.analyzers = analyzers or []

    def add(self, analyzer: BaseAnalyzer) -> "AnalyzerPipeline":
        """添加分析器

        Args:
            analyzer: 分析器实例

        Returns:
            自身（链式调用）
        """
        self.analyzers.append(analyzer)
        return self

    def remove(self, name: str) -> bool:
        """移除分析器

        Args:
            name: 分析器名称

        Returns:
            是否成功移除
        """
        for i, a in enumerate(self.analyzers):
            if a.NAME == name:
                self.analyzers.pop(i)
                return True
        return False

    def run(self, mentions: List[MentionData]) -> Dict[str, Any]:
        """运行所有分析器

        Args:
            mentions: 提及数据列表

        Returns:
            各分析器的结果
        """
        results = {}

        for analyzer in self.analyzers:
            if analyzer.config.enabled:
                try:
                    results[analyzer.NAME] = analyzer.analyze(mentions)
                except Exception as e:
                    logger.error(f"{analyzer.NAME} 分析失败: {e}")
                    results[analyzer.NAME] = None

        return results

    def list_analyzers(self) -> List[str]:
        """列出所有分析器

        Returns:
            分析器名称列表
        """
        return [a.NAME for a in self.analyzers]


def calculate_percentile(values: List[float], percentile: float) -> float:
    """计算百分位数

    Args:
        values: 数值列表
        percentile: 百分位数 (0-100)

    Returns:
        百分位数值
    """
    if not values:
        return 0.0

    sorted_values = sorted(values)
    n = len(sorted_values)
    index = max(0, min(n - 1, int(n * percentile / 100)))
    return sorted_values[index]


def calculate_moving_average(values: List[float], window: int = 7) -> List[float]:
    """计算移动平均

    Args:
        values: 数值列表
        window: 窗口大小

    Returns:
        移动平均值列表
    """
    if window >= len(values):
        return [sum(values) / len(values)] if values else []

    result = []
    for i in range(len(values) - window + 1):
        avg = sum(values[i : i + window]) / window
        result.append(avg)

    return result


def detect_outliers(values: List[float], threshold: float = 2.0) -> List[int]:
    """检测异常值

    使用标准差方法检测异常值。

    Args:
        values: 数值列表
        threshold: 标准差倍数阈值

    Returns:
        异常值索引列表
    """
    if len(values) < 3:
        return []

    import statistics

    mean = statistics.mean(values)
    stdev = statistics.stdev(values) if len(values) > 1 else 0

    if stdev == 0:
        return []

    outliers = []
    for i, value in enumerate(values):
        z_score = abs(value - mean) / stdev if stdev > 0 else 0
        if z_score > threshold:
            outliers.append(i)

    return outliers
